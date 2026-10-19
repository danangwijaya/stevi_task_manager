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


# ─── Shapefile round trip (grid_transfer) ───────────────────────────────────

def _grid_with_polys(db):
    owner = _user(db, "own", "annotator")
    g = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    g.min_lon, g.min_lat, g.max_lon, g.max_lat = 100.0, 0.0, 100.01, 0.01
    from app.db.models import Annotation
    a = Annotation(task_grid_id=g.id, user_id=owner.id, class_id=1, class_name="x",
                   geom_geojson=json.dumps({"type": "Polygon", "coordinates": [[[100.0, 0.0], [100.005, 0.0], [100.005, 0.01], [100.0, 0.01], [100.0, 0.0]]]}),
                   area_sqm=1.0)
    b = Annotation(task_grid_id=g.id, user_id=owner.id, class_id=2, class_name="y",
                   geom_geojson=json.dumps({"type": "Polygon", "coordinates": [[[100.005, 0.0], [100.01, 0.0], [100.01, 0.01], [100.005, 0.01], [100.005, 0.0]]]}),
                   area_sqm=1.0)
    db.add_all([a, b])
    db.commit()
    return owner, g


def _zip_gdf(gdf, tmp_path):
    import zipfile, os
    shp = tmp_path / "t.shp"
    gdf.to_file(shp, driver="ESRI Shapefile")
    zp = tmp_path / "t.zip"
    with zipfile.ZipFile(zp, "w") as zf:
        for ext in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
            f = tmp_path / ("t" + ext)
            if f.exists():
                zf.write(f, "t" + ext)
    return zp


def _upload(zp):
    from fastapi import UploadFile
    return UploadFile(file=open(zp, "rb"), filename="t.zip")


def test_shapefile_export_import_roundtrip(db, tmp_path):
    import geopandas as gpd
    from fastapi import BackgroundTasks
    from app.api.grid_transfer import export_grid_shapefile, import_grid_shapefile
    from app.db.models import Annotation

    owner, g = _grid_with_polys(db)
    resp = export_grid_shapefile(g.id, BackgroundTasks(), db, owner)
    import zipfile
    zf = zipfile.ZipFile(resp.path)
    zf.extractall(tmp_path / "ex")
    shp = next((tmp_path / "ex").glob("*.shp"))
    gdf = gpd.read_file(shp)
    assert set(gdf["KODE_PL"]) == {1, 2} and len(gdf) == 2

    # edit offline: reclassify one polygon, keep ids
    gdf.loc[gdf["KODE_PL"] == 2, "KODE_PL"] = 3
    zp = _zip_gdf(gdf, tmp_path)

    preview = import_grid_shapefile(g.id, _upload(zp), True, False, db, owner)
    assert preview["dry_run"] and preview["file_polygons"] == 2 and preview["kept_ids"] == 2
    assert {a.class_id for a in db.query(Annotation).filter(Annotation.task_grid_id == g.id)} == {1, 2}  # untouched

    done = import_grid_shapefile(g.id, _upload(zp), False, False, db, owner)
    assert not done["dry_run"] and done["saved_count"] == 2
    anns = db.query(Annotation).filter(Annotation.task_grid_id == g.id).all()
    assert {a.class_id for a in anns} == {1, 3}


def test_import_rejects_unknown_class_and_foreign_user(db, tmp_path):
    import geopandas as gpd
    from app.api.grid_transfer import import_grid_shapefile
    from shapely.geometry import box as sbox

    owner, g = _grid_with_polys(db)
    bad = gpd.GeoDataFrame({"KODE_PL": [999]}, geometry=[sbox(100.0, 0.0, 100.005, 0.005)], crs="EPSG:4326")
    zp = _zip_gdf(bad, tmp_path)
    with pytest.raises(HTTPException) as e:
        import_grid_shapefile(g.id, _upload(zp), True, False, db, owner)
    assert e.value.status_code == 400

    other = _user(db, "oth", "annotator")
    with pytest.raises(HTTPException) as e:
        import_grid_shapefile(g.id, _upload(zp), True, False, db, other)
    assert e.value.status_code == 403


def test_import_matches_grid_identity(db, tmp_path):
    import geopandas as gpd
    from app.api.grid_transfer import import_grid_shapefile, _base_code
    from shapely.geometry import box as sbox

    owner, g = _grid_with_polys(db)           # grid_code "G1"
    g.grid_code = "SB_R00_C00_2025"
    db.commit()
    geom = [sbox(100.0, 0.0, 100.005, 0.005)]

    def up(code):
        gdf = gpd.GeoDataFrame({"KODE_PL": [1], "GRID_CODE": [code]}, geometry=geom, crs="EPSG:4326")
        return _upload(_zip_gdf(gdf, tmp_path))

    assert _base_code("SB_R00_C00_2025") == "SB_R00_C00" and _base_code("G1") == "G1"
    assert import_grid_shapefile(g.id, up("SB_R00_C00_2025"), True, False, db, owner)["match"] == "exact"
    assert import_grid_shapefile(g.id, up("SB_R00_C00_2022"), True, False, db, owner)["match"] == "other_year"
    with pytest.raises(HTTPException) as e:                      # other cell: always rejected
        import_grid_shapefile(g.id, up("SB_R09_C09_2025"), True, False, db, owner)
    assert e.value.status_code == 400
    with pytest.raises(HTTPException) as e:                      # other year needs explicit consent
        import_grid_shapefile(g.id, up("SB_R00_C00_2022"), False, False, db, owner)
    assert e.value.status_code == 409
    done = import_grid_shapefile(g.id, up("SB_R00_C00_2022"), False, True, db, owner)
    assert done["saved_count"] == 1


def test_import_rejects_file_mostly_outside_grid(db, tmp_path):
    import geopandas as gpd
    from app.api.grid_transfer import import_grid_shapefile
    from shapely.geometry import box as sbox

    owner, g = _grid_with_polys(db)
    far = [sbox(110, 5, 110.001, 5.001), sbox(111, 5, 111.001, 5.001), sbox(100.0, 0.0, 100.001, 0.001)]
    gdf = gpd.GeoDataFrame({"KODE_PL": [1, 1, 1]}, geometry=far, crs="EPSG:4326")
    with pytest.raises(HTTPException) as e:
        import_grid_shapefile(g.id, _upload(_zip_gdf(gdf, tmp_path)), True, False, db, owner)
    assert e.value.status_code == 400
