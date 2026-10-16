import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import Base, get_db
from app.db.models import User, StudyArea, TaskGrid, Annotation
from app.api.deps import get_current_user

# In-memory SQLite for testing without external postgres dependency
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock mock contributor user
mock_user = User(
    id=1,
    email="contributor@geostevia.id",
    full_name="Mapper Sumatera Barat",
    role="contributor",
    is_active=True
)

def override_get_current_user():
    return mock_user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

def setup_test_data():
    db = TestingSessionLocal()
    # Check if study area exists
    sa = db.query(StudyArea).first()
    if not sa:
        sa = StudyArea(id=1, name="Sumatera Barat", center_lat=-0.5, center_lon=100.0, bounds_geojson="{}")
        db.add(sa)
    
    # Create task grid (0.01 deg x 0.01 deg ~ 1.1km x 1.1km)
    tg = db.query(TaskGrid).filter(TaskGrid.id == 100).first()
    if not tg:
        grid_poly = {
            "type": "Polygon",
            "coordinates": [[
                [100.0, -0.5], [100.01, -0.5], [100.01, -0.49], [100.0, -0.49], [100.0, -0.5]
            ]]
        }
        tg = TaskGrid(
            id=100,
            study_area_id=1,
            grid_code="TEST_SB_001",
            year=2025,
            status="ASSIGNED",
            assigned_user_id=mock_user.id,
            min_lat=-0.5,
            max_lat=-0.49,
            min_lon=100.0,
            max_lon=100.01,
            geom_geojson=json.dumps(grid_poly)
        )
        db.add(tg)
    db.commit()
    db.close()

def test_coastal_grid_gap_warning_not_blocking():
    print("Testing API: Coastal grid coverage gap validation...")
    setup_test_data()
    db = TestingSessionLocal()
    # Add a polygon that only covers 70% of the grid (30% empty ocean/gap)
    # Covering from lon 100.0 to 100.007
    covered_geom = {
        "type": "Polygon",
        "coordinates": [[
            [100.0, -0.5], [100.007, -0.5], [100.007, -0.49], [100.0, -0.49], [100.0, -0.5]
        ]]
    }
    db.query(Annotation).filter(Annotation.task_grid_id == 100).delete()
    ann = Annotation(
        task_grid_id=100,
        user_id=mock_user.id,
        class_id=1,
        class_name="Hutan Lahan Kering",
        geom_geojson=json.dumps(covered_geom),
        area_sqm=700000.0
    )
    db.add(ann)
    db.commit()
    db.close()

    res = client.post("/api/v1/annotations/grid/100/validate-topology")
    assert res.status_code == 200, res.text
    data = res.json()
    print("  Topology result:", json.dumps({k: data[k] for k in ["valid", "coverage_percent", "total_errors"]}, indent=2))
    
    # CRITICAL: valid MUST be True because GAP is now a warning, not a blocking error!
    assert data["valid"] is True, f"Expected valid=True for coastal grid with gap, got valid={data['valid']}"
    assert data["total_errors"] == 0, f"Expected 0 errors, got {data['total_errors']}"
    assert any(w["type"] == "GAP" for w in data["warnings"]), "Expected GAP warning in warnings list"
    print("  ✓ Coastal ocean grid gap correctly recorded as warning, topology is VALID and submission allowed!")

def test_save_grid_annotations_id_map():
    print("Testing API: save_grid_annotations with _uiId tracking and id_map return...")
    payload = {
        "task_grid_id": 100,
        "features": [
            {
                "type": "Feature",
                "_uiId": "f_tmp_1001",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [100.0, -0.5], [100.005, -0.5], [100.005, -0.495], [100.0, -0.495], [100.0, -0.5]
                    ]]
                },
                "properties": {
                    "_uiId": "f_tmp_1001",
                    "class_id": 2,
                    "class_name": "Hutan Rawa"
                }
            },
            {
                "type": "Feature",
                "_uiId": "f_tmp_1002",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [100.005, -0.5], [100.01, -0.5], [100.01, -0.495], [100.005, -0.495], [100.005, -0.5]
                    ]]
                },
                "properties": {
                    "_uiId": "f_tmp_1002",
                    "class_id": 3,
                    "class_name": "Hutan Mangrove"
                }
            }
        ]
    }
    res = client.post("/api/v1/annotations/grid/100", json=payload)
    assert res.status_code == 200, res.text
    data = res.json()
    print("  Save response:", json.dumps(data, indent=2))
    assert "id_map" in data, "Expected 'id_map' in save_grid_annotations response"
    assert "f_tmp_1001" in data["id_map"], "Expected f_tmp_1001 in id_map"
    assert "f_tmp_1002" in data["id_map"], "Expected f_tmp_1002 in id_map"
    assert isinstance(data["id_map"]["f_tmp_1001"], int), "Expected integer DB ID"
    print("  ✓ save_grid_annotations returned accurate id_map mapping temporary UI IDs to real database IDs!")

def test_task_status_transition_by_contributor():
    print("Testing API: update_task_status permission transitions...")
    db = TestingSessionLocal()
    tg = db.query(TaskGrid).filter(TaskGrid.id == 100).first()
    tg.status = "ASSIGNED"
    db.commit()
    db.close()

    res = client.post("/api/v1/tasks/100/status", json={"status": "SUBMITTED"})
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "SUBMITTED"
    print("  ✓ Contributor successfully submitted task from ASSIGNED to SUBMITTED!")

if __name__ == "__main__":
    print("==================================================")
    print("RUNNING API ENDPOINT VERIFICATION")
    print("==================================================")
    test_coastal_grid_gap_warning_not_blocking()
    test_save_grid_annotations_id_map()
    test_task_status_transition_by_contributor()
    print("==================================================")
    print("ALL API ENDPOINT TESTS PASSED SUCCESSFULLY!")
    print("==================================================")
