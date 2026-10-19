import json
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.db.models import User, TaskGrid, StudyArea
from app.api.annotations import _require_grid_edit_access, _ensure_single_merged_part
from shapely.geometry import box


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _user(db, name, role):
    u = User(username=name, email=f"{name}@x.id", full_name=name, role=role, hashed_password="x", is_active=True)
    db.add(u)
    db.flush()
    return u


def _grid(db, **kw):
    sa = StudyArea(name="sa", center_lat=0, center_lon=0)
    db.add(sa)
    db.flush()
    g = TaskGrid(grid_code="G1", study_area_id=sa.id, year=2025, min_lon=0, min_lat=0, max_lon=1, max_lat=1,
                 geom_geojson="{}", **kw)
    db.add(g)
    db.flush()
    return g


def test_owner_can_edit_others_cannot(db):
    owner, other = _user(db, "a", "annotator"), _user(db, "b", "annotator")
    g = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    assert _require_grid_edit_access(db, g.id, owner) is g
    with pytest.raises(HTTPException) as e:
        _require_grid_edit_access(db, g.id, other)
    assert e.value.status_code == 403


def test_submitted_grid_locked_for_annotator_not_reviewer(db):
    owner, rev = _user(db, "a", "annotator"), _user(db, "r", "reviewer")
    g = _grid(db, assigned_user_id=owner.id, status="SUBMITTED")
    with pytest.raises(HTTPException) as e:
        _require_grid_edit_access(db, g.id, owner)
    assert e.value.status_code == 403
    assert _require_grid_edit_access(db, g.id, rev) is g


def test_missing_grid_404(db):
    u = _user(db, "a", "annotator")
    with pytest.raises(HTTPException) as e:
        _require_grid_edit_access(db, 999, u)
    assert e.value.status_code == 404


def test_merge_rejects_disjoint_parts_but_ignores_noise():
    big = box(0, 0, 0.001, 0.001)
    far = box(0.01, 0.01, 0.0101, 0.0101)       # ~1.2 ha, well above 5 sqm
    speck = box(0.02, 0.02, 0.0200001, 0.0200001)  # ~0.01 sqm
    with pytest.raises(HTTPException):
        _ensure_single_merged_part([big, far], "x")
    assert _ensure_single_merged_part([speck, big], "x") is big


def test_save_keeps_rows_modified_after_client_sync(db):
    from datetime import datetime, timedelta
    from app.api.annotations import save_grid_annotations, AnnotationSaveRequest, GeoJSONFeature
    from app.db.models import Annotation

    owner = _user(db, "a", "annotator")
    g = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    square = {"type": "Polygon", "coordinates": [[[0, 0], [0.001, 0], [0.001, 0.001], [0, 0.001], [0, 0]]]}
    other = {"type": "Polygon", "coordinates": [[[0.002, 0], [0.003, 0], [0.003, 0.001], [0.002, 0.001], [0.002, 0]]]}
    known = Annotation(task_grid_id=g.id, user_id=owner.id, class_id=1, class_name="x",
                       geom_geojson=json.dumps(square), area_sqm=1.0, updated_at=datetime(2026, 1, 1))
    foreign = Annotation(task_grid_id=g.id, user_id=owner.id, class_id=1, class_name="x",
                         geom_geojson=json.dumps(other), area_sqm=1.0, updated_at=datetime(2026, 1, 3))
    old_deleted = Annotation(task_grid_id=g.id, user_id=owner.id, class_id=1, class_name="x",
                             geom_geojson=json.dumps(other), area_sqm=1.0, updated_at=datetime(2026, 1, 1))
    db.add_all([known, foreign, old_deleted])
    db.commit()
    known_id, foreign_id, old_id = known.id, foreign.id, old_deleted.id

    req = AnnotationSaveRequest(
        task_grid_id=g.id,
        synced_at="2026-01-02T00:00:00Z",
        features=[GeoJSONFeature(id=known_id, geometry=square, properties={"class_id": 1, "class_name": "x"})],
    )
    res = save_grid_annotations(g.id, req, db, owner)
    ids = {a.id for a in db.query(Annotation).filter(Annotation.task_grid_id == g.id)}
    assert foreign_id in ids            # unseen by client -> preserved
    assert old_id not in ids            # seen and removed by client -> deleted
    assert res["preserved_ids"] == [foreign_id]
    assert res["server_time"].endswith("Z")
