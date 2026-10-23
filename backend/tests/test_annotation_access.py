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


def _detail(exc):
    d = exc.value.detail
    assert isinstance(d, dict) and d["message"] and d["solution"]
    return d


def test_import_errors_explain_cause_and_solution(db, tmp_path):
    import zipfile
    import geopandas as gpd
    from fastapi import UploadFile
    from app.api.grid_transfer import import_grid_shapefile
    from shapely.geometry import box as sbox

    owner, g = _grid_with_polys(db)

    def zip_of(names, name="x.zip"):
        zp = tmp_path / name
        with zipfile.ZipFile(zp, "w") as zf:
            for n in names:
                zf.writestr(n, "x")
        return UploadFile(file=open(zp, "rb"), filename=name)

    with pytest.raises(HTTPException) as e:
        import_grid_shapefile(g.id, zip_of(["data.gpkg"]), True, False, db, owner)
    assert _detail(e)["code"] == "UNSUPPORTED_FORMAT"
    with pytest.raises(HTTPException) as e:
        import_grid_shapefile(g.id, zip_of(["a.shp", "a.prj"], "m.zip"), True, False, db, owner)
    assert _detail(e)["code"] == "MISSING_PARTS"
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not a zip")
    with pytest.raises(HTTPException) as e:
        import_grid_shapefile(g.id, UploadFile(file=open(bad, "rb"), filename="bad.zip"), True, False, db, owner)
    assert _detail(e)["code"] == "NOT_ZIP"

    gdf = gpd.GeoDataFrame({"KODE_PL": [999]}, geometry=[sbox(100.0, 0.0, 100.005, 0.005)], crs="EPSG:4326")
    with pytest.raises(HTTPException) as e:
        import_grid_shapefile(g.id, _upload(_zip_gdf(gdf, tmp_path)), True, False, db, owner)
    d = _detail(e)
    assert d["code"] == "BAD_CLASS" and "0 = " in d["solution"]  # lists the valid codes


def test_import_null_class_becomes_zero_with_warning_and_drops_z(db, tmp_path):
    import geopandas as gpd
    from shapely.geometry import Polygon as P
    from app.api.grid_transfer import import_grid_shapefile
    from app.db.models import Annotation

    owner, g = _grid_with_polys(db)
    poly_z = P([(100.0, 0.0, 5), (100.005, 0.0, 5), (100.005, 0.005, 5), (100.0, 0.005, 5)])
    gdf = gpd.GeoDataFrame({"KODE_PL": [None]}, geometry=[poly_z], crs="EPSG:4326")
    zp = _zip_gdf(gdf, tmp_path)

    preview = import_grid_shapefile(g.id, _upload(zp), True, False, db, owner)
    codes = {w["code"] for w in preview["warnings"]}
    assert "NULL_CLASS" in codes and all(w["solution"] for w in preview["warnings"])

    import_grid_shapefile(g.id, _upload(zp), False, False, db, owner)
    ann = db.query(Annotation).filter(Annotation.task_grid_id == g.id).one()
    assert ann.class_id == 0
    assert all(len(c) == 2 for c in json.loads(ann.geom_geojson)["coordinates"][0])  # no Z


# ─── merge: seam slivers must close, real islands must stay ──────────────────

def _merge(*geoms):
    from app.api.annotations import _merge_polygons_robust
    return _merge_polygons_robust(list(geoms))


def test_merge_closes_sliver_between_polygon_and_neighbour_hole():
    """A polygon sitting in another polygon's hole leaves a ~1 m seam sliver: the merge must weld it."""
    from shapely.geometry import box as sbox, Polygon as P
    w = 1.0 / 111320.0  # 1 m in degrees
    ring_hole = sbox(0.0010, 0.0010, 0.0030, 0.0030)
    outer = P(sbox(0, 0, 0.004, 0.004).exterior.coords, [ring_hole.exterior.coords])
    inner = sbox(0.0010 + w, 0.0010 + w, 0.0030, 0.0030)  # leaves a 1 m sliver on two sides of the hole
    merged = _merge(outer, inner)
    assert merged.geom_type == "Polygon"
    assert len(merged.interiors) == 0, "seam sliver was kept as a hole"


def test_merge_keeps_hole_that_other_polygon_occupies():
    """An island of a non-selected polygon inside the hole must not be covered by the merged polygon."""
    from shapely.geometry import box as sbox, Polygon as P
    hole = sbox(0.0010, 0.0010, 0.0020, 0.0020)
    outer = P(sbox(0, 0, 0.004, 0.004).exterior.coords, [hole.exterior.coords])
    neighbour = sbox(0.004, 0, 0.006, 0.004)
    merged = _merge(outer, neighbour)
    assert merged.geom_type == "Polygon" and len(merged.interiors) == 1
    assert P(merged.interiors[0]).area > 0.9 * hole.area


def _rough_disc(cx, cy, r_m, n=3000, jitter_m=1.5, seed=7):
    import math, random
    from shapely.geometry import Polygon as P
    rnd = random.Random(seed)
    deg = 1.0 / 111320.0
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = (r_m + rnd.uniform(-jitter_m, jitter_m)) * deg
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return P(pts).buffer(0)


def test_merge_does_not_rewrite_large_polygon_away_from_the_seam(merge=None):
    """Merging a large, detailed polygon with a small neighbour must only touch the area around their seam."""
    from shapely.geometry import box as sbox
    merge = merge or _merge
    big = _rough_disc(0.0, 0.0, 500.0)
    deg = 1.0 / 111320.0
    nb = sbox(500 * deg - 1e-5, -50 * deg, 500 * deg + 80 * deg, 50 * deg)   # touches the east edge
    merged = merge(big, nb)
    union = big.union(nb)
    far = sbox(-600 * deg, -600 * deg, 400 * deg, 600 * deg)                  # everything >100 m from the seam
    changed = merged.symmetric_difference(union).intersection(far).area * (111320.0 ** 2)
    assert changed < 1.0, f"{changed:.1f} m2 of the polygon was rewritten far from the seam"


def test_hole_occupancy_separates_empty_holes_from_islands(db):
    from shapely.geometry import box as sbox, Polygon as P, mapping
    from app.api.annotations import hole_occupancy, HoleOccupancyRequest
    from app.db.models import Annotation

    owner = _user(db, "own", "annotator")
    g = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    outer = P(sbox(0, 0, 0.01, 0.01).exterior.coords,
              [sbox(0.001, 0.001, 0.003, 0.003).exterior.coords,     # hole 1: an island polygon sits in it
               sbox(0.006, 0.006, 0.008, 0.008).exterior.coords])    # hole 2: nothing in it
    island = sbox(0.0012, 0.0012, 0.0028, 0.0028)
    db.add(Annotation(task_grid_id=g.id, user_id=owner.id, class_id=2, class_name="island",
                      geom_geojson=json.dumps(mapping(island)), area_sqm=1.0))
    own = Annotation(task_grid_id=g.id, user_id=owner.id, class_id=1, class_name="outer",
                     geom_geojson=json.dumps(mapping(outer)), area_sqm=1.0)
    db.add(own)
    db.commit()

    res = hole_occupancy(HoleOccupancyRequest(task_grid_id=g.id, geometry=mapping(outer), exclude_annotation_id=own.id), db, owner)
    by_ring = {h["ring"]: h["occupied"] for h in res["holes"]}
    assert by_ring == {1: True, 2: False}
    assert res["empty_count"] == 1 and res["occupied_count"] == 1


def test_resending_unsaved_features_without_ids_does_not_duplicate(db):
    """A client that never learned the ids of rows it created (lost response, two overlapping saves)
    resends the same polygons without ids. The server must not keep both copies."""
    from datetime import datetime, timedelta
    from app.api.annotations import save_grid_annotations, AnnotationSaveRequest, GeoJSONFeature
    from app.db.models import Annotation

    owner = _user(db, "own", "annotator")
    g = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    square = {"type": "Polygon", "coordinates": [[[0, 0], [0.002, 0], [0.002, 0.002], [0, 0.002], [0, 0]]]}
    other = {"type": "Polygon", "coordinates": [[[0.01, 0], [0.012, 0], [0.012, 0.002], [0.01, 0.002], [0.01, 0]]]}
    synced = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z"   # the client's last sync, before both saves

    def payload():
        return AnnotationSaveRequest(task_grid_id=g.id, synced_at=synced, features=[
            GeoJSONFeature(geometry=square, properties={"class_id": 1, "class_name": "x"}),
            GeoJSONFeature(geometry=other, properties={"class_id": 2, "class_name": "y"}),
        ])

    save_grid_annotations(g.id, payload(), db, owner)     # first save: rows are created, client does not learn their ids
    save_grid_annotations(g.id, payload(), db, owner)     # the client sends the same polygons again, still without ids
    n = db.query(Annotation).filter(Annotation.task_grid_id == g.id).count()
    assert n == 2, f"{n} rows in the grid: the same two polygons were stored twice"


def test_topology_separates_open_holes_from_holes_filled_by_other_polygons(db):
    import json
    from shapely.geometry import Polygon, mapping
    from app.db.models import Annotation
    from app.api.annotations import validate_topology

    u = _user(db, "rv", "reviewer")
    g = _grid(db, assigned_user_id=u.id, status="IN_PROGRESS")
    island, open_hole = box(0.2, 0.2, 0.3, 0.3), box(0.6, 0.6, 0.62, 0.62)
    donut = Polygon(box(0.1, 0.1, 0.9, 0.9).exterior.coords, [island.exterior.coords, open_hole.exterior.coords])

    def add(geom, cid):
        db.add(Annotation(task_grid_id=g.id, user_id=u.id, class_id=cid, class_name="c", geom_geojson=json.dumps(mapping(geom)), area_sqm=1))

    add(donut, 1)
    add(island, 2)                     # sits exactly in the first hole
    db.commit()

    out = validate_topology(g.id, db, u)
    assert out["hole_summary"] == {"polygons_with_holes": 1, "holes": 2, "filled": 1, "open": 1,
                                   "open_area_sqm": pytest.approx(open_hole.area * 111320.0 ** 2, rel=1e-6)}
    empty = [w for w in out["warnings"] if w["type"] == "EMPTY_HOLE"]
    assert len(empty) == 1 and empty[0]["annotation_id"] == 1
    assert shape_area(empty[0]["geometry"]) == pytest.approx(open_hole.area, rel=1e-6)


def shape_area(geojson):
    from shapely.geometry import shape
    return shape(geojson).area


def test_full_save_reports_a_new_polygon_that_duplicates_a_preserved_row(db):
    """The full save already drops duplicates inside one payload; a duplicate of a row it had to keep is only reported."""
    from datetime import datetime, timedelta
    from app.api.annotations import save_grid_annotations, AnnotationSaveRequest, GeoJSONFeature
    from app.db.models import Annotation, AuditLog

    owner = _user(db, "own", "annotator")
    g = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    a = {"type": "Polygon", "coordinates": [[[0, 0], [0.002, 0], [0.002, 0.002], [0, 0.002], [0, 0]]]}
    b = {"type": "Polygon", "coordinates": [[[0.0001, 0], [0.0021, 0], [0.0021, 0.002], [0.0001, 0.002], [0.0001, 0]]]}   # 5% shifted, IoU 0.905
    save_grid_annotations(g.id, AnnotationSaveRequest(task_grid_id=g.id, features=[
        GeoJSONFeature(geometry=a, properties={"class_id": 1, "class_name": "x"})]), db, owner)
    stale = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z"          # this client never saw the first row
    out = save_grid_annotations(g.id, AnnotationSaveRequest(task_grid_id=g.id, synced_at=stale, features=[
        GeoJSONFeature(geometry=b, properties={"class_id": 2, "class_name": "y"})]), db, owner)
    assert len(out["preserved_ids"]) == 1
    assert len(out["duplicate_warnings"]) == 1 and out["duplicate_warnings"][0]["iou"] >= 0.9
    assert db.query(Annotation).filter(Annotation.task_grid_id == g.id).count() == 2      # both kept
    assert db.query(AuditLog).filter(AuditLog.task_grid_id == g.id, AuditLog.action == "DUPLICATE_SUSPECT").count() == 1


def test_full_save_adopts_an_edited_copy_of_a_preserved_row_of_the_same_class(db):
    """The client lost the ids of rows it saved earlier and then edited them a little: the rows are updated in place."""
    from datetime import datetime, timedelta
    from app.api.annotations import save_grid_annotations, AnnotationSaveRequest, GeoJSONFeature
    from app.db.models import Annotation

    owner = _user(db, "own", "annotator")
    g = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    a = {"type": "Polygon", "coordinates": [[[0, 0], [0.002, 0], [0.002, 0.002], [0, 0.002], [0, 0]]]}
    b = {"type": "Polygon", "coordinates": [[[0.0001, 0], [0.0021, 0], [0.0021, 0.002], [0.0001, 0.002], [0.0001, 0]]]}   # IoU 0.905
    save_grid_annotations(g.id, AnnotationSaveRequest(task_grid_id=g.id, features=[
        GeoJSONFeature(geometry=a, properties={"class_id": 1, "class_name": "x"})]), db, owner)
    first = db.query(Annotation).filter(Annotation.task_grid_id == g.id).one().id
    stale = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z"
    out = save_grid_annotations(g.id, AnnotationSaveRequest(task_grid_id=g.id, synced_at=stale, features=[
        GeoJSONFeature(geometry=b, properties={"class_id": 1, "class_name": "x"})]), db, owner)
    rows = db.query(Annotation).filter(Annotation.task_grid_id == g.id).all()
    assert [r.id for r in rows] == [first] and out["preserved_ids"] == [] and out["duplicate_warnings"] == []
    assert json.loads(rows[0].geom_geojson)["coordinates"][0][0][0] == 0.0001           # the edited geometry won
