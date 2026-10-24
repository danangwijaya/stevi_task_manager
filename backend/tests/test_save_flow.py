"""Save flows as the map really drives them: a client that keeps its polygons, applies the ids the server returns and sends
the rest back on the next autosave. These guard the bugs of 22-24 October 2026 (ids lost, polygons deleted and re-inserted at
every autosave, stale tabs, cuts that left their target behind)."""
from tests.test_annotation_access import db, _user, _grid          # noqa: F401  (fixtures and helpers of the existing tests)

from app.api.annotations import AnnotationSaveRequest, save_grid_annotations
from app.api.grid_changes import ChangeFeature, DeleteRef, GridChangesRequest, save_grid_changes
from app.db.models import Annotation


def sq(x, size=0.002):
    return {"type": "Polygon", "coordinates": [[[x, 0], [x + size, 0], [x + size, size], [x, size], [x, 0]]]}


class FullSaveMap:
    """The mapper's browser on the full-save path. Polygons made on the map carry `_uiId` beside `properties`, as the
    cut and merge handlers set it, and no id until a save returns one."""

    def __init__(self, db, owner, grid):
        self.db, self.owner, self.grid = db, owner, grid
        self.features = {}                  # uid -> feature as sent on the wire
        self.synced_at = None

    def draw(self, uid, x, cls=1):
        self.features[uid] = {"type": "Feature", "geometry": sq(x), "properties": {"class_id": cls, "class_name": "x"}, "_uiId": uid}

    def erase(self, uid):
        del self.features[uid]

    def ids(self):
        return {uid: f.get("id") for uid, f in self.features.items()}

    def save(self):
        out = save_grid_annotations(self.grid.id, AnnotationSaveRequest(**{
            "task_grid_id": self.grid.id, "synced_at": self.synced_at, "features": list(self.features.values())}), self.db, self.owner)
        for uid, row_id in out["id_map"].items():       # what the view does with the response
            if uid in self.features:
                self.features[uid]["id"] = row_id
        if not out["preserved_ids"]:
            self.synced_at = out["server_time"]
        return out


def rows(db, grid):
    return db.query(Annotation).filter(Annotation.task_grid_id == grid.id).order_by(Annotation.id).all()


def test_consecutive_autosaves_keep_the_ids_of_polygons_made_on_the_map(db):
    owner = _user(db, "own", "annotator")
    grid = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    client = FullSaveMap(db, owner, grid)
    seen = {}
    for n in range(5):
        client.draw(f"f_tmp_{n}", n * 0.01)
        out = client.save()
        assert out["preserved_ids"] == [] and out["dropped_duplicates"] == 0
        assert all(client.ids().values()), "a polygon is still without a database id after the save"
        for uid, row_id in client.ids().items():
            assert seen.setdefault(uid, row_id) == row_id, f"{uid} got a new id: it was deleted and inserted again"
        assert [r.id for r in rows(db, grid)] == sorted(client.ids().values())


def test_a_cut_replaces_its_target_and_leaves_no_twin(db):
    owner = _user(db, "own", "annotator")
    grid = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    client = FullSaveMap(db, owner, grid)
    client.draw("whole", 0.0)
    client.draw("other", 0.05)
    client.save()
    other_id = client.ids()["other"]
    client.erase("whole")                                # the cut removes its target on the map ...
    client.draw("piece_a", 0.0)                          # ... and adds the two pieces
    client.draw("piece_b", 0.001)
    client.save()
    assert [r.id for r in rows(db, grid)] == sorted(client.ids().values())
    assert len(rows(db, grid)) == 3 and client.ids()["other"] == other_id


def test_a_stale_tab_cannot_delete_what_another_tab_saved_meanwhile(db):
    owner = _user(db, "own", "annotator")
    grid = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    tab_a, tab_b = FullSaveMap(db, owner, grid), FullSaveMap(db, owner, grid)
    tab_a.draw("a1", 0.0)
    tab_a.save()
    tab_b.synced_at = tab_a.synced_at                    # tab B loaded the grid with a1 ...
    tab_b.features["a1"] = dict(tab_a.features["a1"])
    tab_a.draw("a2", 0.05)                               # ... then tab A adds a2 and saves
    tab_a.save()
    tab_b.draw("b1", 0.1)                                # tab B never saw a2
    out = tab_b.save()
    ids = {r.id for r in rows(db, grid)}
    assert tab_a.ids()["a2"] in ids and tab_a.ids()["a2"] in out["preserved_ids"]


class DeltaMap:
    """The same for the delta save: inserts keyed by client_uid, deletes and updates carrying the version last seen."""

    def __init__(self, db, owner, grid):
        self.db, self.owner, self.grid = db, owner, grid
        self.rows = {}                      # uid -> {"id", "version"}

    def save(self, upserts=(), deletes=()):
        req = GridChangesRequest(
            upserts=[ChangeFeature(client_uid=uid, geometry=sq(x), properties={"class_id": 1}) for uid, x in upserts],
            deletes=[DeleteRef(id=self.rows[uid]["id"], version=self.rows[uid]["version"]) for uid in deletes])
        out = save_grid_changes(self.grid.id, req, self.db, self.owner)
        for uid in deletes:
            self.rows.pop(uid)
        for uid, row_id in out["id_map"].items():
            self.rows[uid] = {"id": row_id, "version": out["versions"][str(row_id)]}
        return out


def test_delta_cuts_one_after_another_leave_exactly_the_latest_pieces(db):
    owner = _user(db, "own", "annotator")
    grid = _grid(db, assigned_user_id=owner.id, status="IN_PROGRESS")
    client = DeltaMap(db, owner, grid)
    client.save(upserts=[("whole", 0.0)])
    client.save(upserts=[("p1", 0.0), ("p2", 0.001)], deletes=["whole"])         # first cut
    out = client.save(upserts=[("p3", 0.0), ("p4", 0.0005)], deletes=["p1"])      # cut the first piece again
    assert out["conflicts"] == [] and out["rejected"] == []
    assert {r.id for r in rows(db, grid)} == {v["id"] for v in client.rows.values()} and len(rows(db, grid)) == 3
