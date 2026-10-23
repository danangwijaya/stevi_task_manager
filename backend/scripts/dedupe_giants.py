"""Remove stale copies of very large polygons that were stacked on top of each other in one grid.
A cluster = giants (>= MIN_HA) that overlap by IoU >= MIN_IOU; the newest row (highest id) is kept, the older ones are deleted.
usage: python - <grid> [--apply] [--idle-min=N] [--min-ha=10000] [--min-iou=0.98]   (default = dry run: nothing is written)"""
import json, sys
from datetime import datetime, timedelta
from shapely.geometry import shape
from shapely.strtree import STRtree
from sqlalchemy import text
from app.db.session import SessionLocal
from app.db.models import User, TaskGrid, Annotation, TaskReviewPin
from app.services.snapshot_service import create_grid_snapshot_from_db, log_audit

GRID = int(sys.argv[1]); APPLY = "--apply" in sys.argv
IDLE_MIN = next((int(a.split('=')[1]) for a in sys.argv if a.startswith('--idle-min=')), 30)
MIN_HA = next((float(a.split('=')[1]) for a in sys.argv if a.startswith('--min-ha=')), 10000.0)
MIN_IOU = next((float(a.split('=')[1]) for a in sys.argv if a.startswith('--min-iou=')), 0.98)
k = 111320.0 ** 2
db = SessionLocal()
admin = db.query(User).filter(User.role == "admin").order_by(User.id).first()
task = db.query(TaskGrid).filter(TaskGrid.id == GRID).first()
last = db.execute(text("select max(created_at) from audit_logs where task_grid_id=:g and action='SAVE_ANNOTATIONS'"), {"g": GRID}).scalar()
idle = (datetime.utcnow() - last) if last else timedelta(days=99)
print(f"grid {GRID} {task.grid_code} | last mapper save {last} (idle {idle}) | mode {'APPLY' if APPLY else 'DRY RUN'}", flush=True)
if APPLY and idle < timedelta(minutes=IDLE_MIN):
    print("ABORT: the mapper saved this grid less than %d min ago" % IDLE_MIN, flush=True); sys.exit(2)

rows = db.query(Annotation).filter(Annotation.task_grid_id == GRID).order_by(Annotation.id).all()
giants = [r for r in rows if (r.area_sqm or 0) / 1e4 >= MIN_HA]
geoms = {}
for r in giants:
    g = shape(json.loads(r.geom_geojson)); geoms[r.id] = g if g.is_valid else g.buffer(0)
ids = list(geoms); tree = STRtree([geoms[i] for i in ids])
parent = {i: i for i in ids}
def find(x):
    while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
    return x
for a_i, a in enumerate(ids):
    for b_i in tree.query(geoms[a]):
        b = ids[int(b_i)]
        if b <= a: continue
        inter = geoms[a].intersection(geoms[b]).area; iou = inter / (geoms[a].area + geoms[b].area - inter)
        if iou >= MIN_IOU: parent[find(a)] = find(b)
clusters = {}
for i in ids: clusters.setdefault(find(i), []).append(i)
by_id = {r.id: r for r in rows}
to_delete = []
for members in clusters.values():
    if len(members) < 2: continue
    members.sort(); keep = members[-1]
    print(f"cluster of {len(members)}: keep #{keep} (class {by_id[keep].class_id}, {geoms[keep].area*k/1e4:.0f} ha, created {by_id[keep].created_at}); delete " +
          ", ".join(f"#{m}(class {by_id[m].class_id}, created {by_id[m].created_at.strftime('%H:%M:%S')})" for m in members[:-1]), flush=True)
    to_delete += members[:-1]
print(f"polygons in grid: {len(rows)} | large polygons (>= {MIN_HA:.0f} ha): {len(giants)} | stale copies to delete: {len(to_delete)}", flush=True)
if not APPLY or not to_delete:
    print("dry run: nothing written" if not APPLY else "nothing to delete"); sys.exit(0)
create_grid_snapshot_from_db(db=db, task_grid_id=GRID, user_id=admin.id, note="Sebelum hapus salinan poligon usang")
db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id.in_(to_delete)).update({"annotation_id": None}, synchronize_session=False)
db.query(Annotation).filter(Annotation.id.in_(to_delete)).delete(synchronize_session=False)
log_audit(db=db, user_id=admin.id, action="DEDUPE_GIANTS", entity_type="task_grid", entity_id=GRID, task_grid_id=GRID, details=json.dumps({"deleted_ids": to_delete}))
db.commit()
print(f"APPLIED: {len(to_delete)} stale giant copies deleted", flush=True)
