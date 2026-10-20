import json
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.grid_changes import ChangeFeature, DeleteRef, GridChangesRequest, save_grid_changes
from app.db.models import Annotation, StudyArea, TaskGrid, User
from app.db.session import Base


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


def _user(db, name, role="annotator"):
    u = User(username=name, email=f"{name}@x.id", full_name=name, role=role, hashed_password="x", is_active=True)
    db.add(u)
    db.flush()
    return u


def _grid(db, owner, status="IN_PROGRESS"):
    sa = StudyArea(name="sa", center_lat=0, center_lon=0)
    db.add(sa)
    db.flush()
    g = TaskGrid(grid_code="G1", study_area_id=sa.id, year=2025, min_lon=0, min_lat=0, max_lon=1, max_lat=1,
                 geom_geojson="{}", assigned_user_id=owner.id, status=status)
    db.add(g)
    db.flush()
    return g


def sq(x, size=0.002):
    return {"type": "Polygon", "coordinates": [[[x, 0], [x + size, 0], [x + size, size], [x, size], [x, 0]]]}


def feat(x, uid=None, id=None, version=None, cls=1):
    return ChangeFeature(id=id, client_uid=uid, version=version, geometry=sq(x), properties={"class_id": cls})


def rows(db, g):
    return db.query(Annotation).filter(Annotation.task_grid_id == g.id).order_by(Annotation.id).all()


def test_insert_is_idempotent_and_returns_ids(db):
    owner = _user(db, "own")
    g = _grid(db, owner)
    req = GridChangesRequest(upserts=[feat(0.0, "u-1"), feat(0.01, "u-2", cls=2)])
    first = save_grid_changes(g.id, req, db, owner)
    assert set(first["id_map"]) == {"u-1", "u-2"} and len(rows(db, g)) == 2
    again = save_grid_changes(g.id, req, db, owner)          # the response was lost: the client sends it again
    assert again["id_map"] == first["id_map"] and len(rows(db, g)) == 2


def test_rows_not_mentioned_are_never_touched(db):
    """The point of the delta save: a stale tab cannot delete what it does not know about."""
    owner = _user(db, "own")
    g = _grid(db, owner)
    saved = save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, "a"), feat(0.01, "b"), feat(0.02, "c")]), db, owner)
    ids = saved["id_map"]
    # a client that only knows polygon "a" saves a change to it
    save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, None, ids["a"], saved["versions"][str(ids["a"])], cls=3)]), db, owner)
    assert {r.id for r in rows(db, g)} == set(ids.values())


def test_update_with_current_version_applies_and_keeps_author(db):
    owner, reviewer = _user(db, "own"), _user(db, "rev", "reviewer")
    g = _grid(db, owner)
    saved = save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, "a")]), db, owner)
    rid = saved["id_map"]["a"]
    out = save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, None, rid, saved["versions"][str(rid)], cls=4)]), db, reviewer)
    row = db.query(Annotation).get(rid)
    assert row.class_id == 4 and row.user_id == owner.id and not out["conflicts"]


def test_stale_version_conflicts_and_server_wins(db):
    owner, reviewer = _user(db, "own"), _user(db, "rev", "reviewer")
    g = _grid(db, owner)
    saved = save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, "a")]), db, owner)
    rid, v0 = saved["id_map"]["a"], saved["versions"][str(saved["id_map"]["a"])]
    save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, None, rid, v0, cls=5)]), db, reviewer)   # someone else edits
    out = save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, None, rid, v0, cls=2)]), db, owner)  # stale tab, old version
    assert db.query(Annotation).get(rid).class_id == 5                      # the server's value stays
    assert [c["id"] for c in out["conflicts"]] == [rid]
    assert out["conflicts"][0]["server_feature"]["properties"]["class_id"] == 5


def test_delete_needs_current_version(db):
    owner, reviewer = _user(db, "own"), _user(db, "rev", "reviewer")
    g = _grid(db, owner)
    saved = save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, "a"), feat(0.01, "b")]), db, owner)
    a, b = saved["id_map"]["a"], saved["id_map"]["b"]
    va, vb = saved["versions"][str(a)], saved["versions"][str(b)]
    save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.01, None, b, vb, cls=3)]), db, reviewer)   # b changed meanwhile
    out = save_grid_changes(g.id, GridChangesRequest(deletes=[DeleteRef(id=a, version=va), DeleteRef(id=b, version=vb)]), db, owner)
    assert out["deleted"] == [a] and [c["id"] for c in out["conflicts"]] == [b]
    assert {r.id for r in rows(db, g)} == {b}


def test_access_rules_match_the_full_save(db):
    owner, other = _user(db, "own"), _user(db, "oth")
    g = _grid(db, owner)
    with pytest.raises(HTTPException) as e:
        save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, "a")]), db, other)
    assert e.value.status_code == 403
    g.status = "SUBMITTED"
    db.commit()
    with pytest.raises(HTTPException) as e:
        save_grid_changes(g.id, GridChangesRequest(upserts=[feat(0.0, "a")]), db, owner)
    assert e.value.status_code == 403


def test_bad_geometry_is_reported_not_dropped_silently(db):
    owner = _user(db, "own")
    g = _grid(db, owner)
    flat = ChangeFeature(client_uid="t", properties={"class_id": 1},     # collapsed ring: no area at all
                         geometry={"type": "Polygon", "coordinates": [[[0, 0], [0.002, 0], [0.004, 0], [0, 0]]]})
    out = save_grid_changes(g.id, GridChangesRequest(upserts=[flat, feat(0.01, "ok")]), db, owner)
    assert [r["client_uid"] for r in out["rejected"]] == ["t"] and set(out["id_map"]) == {"ok"}
