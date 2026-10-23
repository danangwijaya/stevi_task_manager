"""Close gaps inside a grid without creating thousands of polygons.
 - gap pieces that are small (<100 m2) or thin (<5 m thick) are absorbed by the neighbour sharing the most boundary
 - larger voids become one class-0 polygon each (Belum Teridentifikasi) for the mapper to classify
usage: python - <grid> [--apply]   (default = dry run: nothing is written)"""
import json, sys, time
from collections import defaultdict
from datetime import datetime, timedelta
from shapely.geometry import shape, box, mapping, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
from sqlalchemy import text
from app.db.session import SessionLocal
from app.db.models import User, TaskGrid, Annotation
from app.services.snapshot_service import create_grid_snapshot_from_db
from app.api.annotations import _extract_polygons

GRID = int(sys.argv[1]); APPLY = "--apply" in sys.argv
SMALL_M2, THIN_M = 100.0, 5.0
IDLE_MIN = next((int(a.split('=')[1]) for a in sys.argv if a.startswith('--idle-min=')), 30)
k = 111320.0 ** 2
db = SessionLocal()
admin = db.query(User).filter(User.role == "admin").order_by(User.id).first()
task = db.query(TaskGrid).filter(TaskGrid.id == GRID).first()
last = db.execute(text("select max(created_at) from audit_logs where task_grid_id=:g and action='SAVE_ANNOTATIONS'"), {"g": GRID}).scalar()
idle = (datetime.utcnow() - last) if last else timedelta(days=99)
print(f"grid {GRID} {task.grid_code} | last mapper save {last} (idle {idle}) | mode {'APPLY' if APPLY else 'DRY RUN'}", flush=True)
if APPLY and idle < timedelta(minutes=IDLE_MIN):
    print("ABORT: the mapper saved this grid less than %d min ago" % IDLE_MIN + "", flush=True); sys.exit(2)

rows = db.query(Annotation).filter(Annotation.task_grid_id == GRID).order_by(Annotation.id).all()
ids = [a.id for a in rows]; geoms = [shape(json.loads(a.geom_geojson)) for a in rows]
gb = box(task.min_lon, task.min_lat, task.max_lon, task.max_lat)
def stats(gs, label):
    u = unary_union(gs); gap = gb.difference(u)
    parts = [p for p in (gap.geoms if hasattr(gap, "geoms") else [gap]) if not p.is_empty]
    tree = STRtree(gs); ov = 0
    for i, g in enumerate(gs):
        for j in tree.query(g):
            if j > i and g.intersection(gs[j]).area * k > 1: ov += 1
    print(f"[{label}] polygons {len(gs)} | coverage {100*u.intersection(gb).area/gb.area:.4f}% | gap pieces >=1 m2: {sum(1 for p in parts if p.area*k>=1)} | overlapping pairs >1 m2: {ov} | invalid {sum(1 for g in gs if not g.is_valid)}", flush=True)
    return parts
t0 = time.time(); pieces = stats(geoms, "BEFORE")
thick = lambda p: 2 * p.area * k / (p.length * 111320.0)
absorb = [p for p in pieces if p.area * k < SMALL_M2 or thick(p) < THIN_M]
fill = [p for p in pieces if not (p.area * k < SMALL_M2 or thick(p) < THIN_M)]
tree = STRtree(geoms); adds = defaultdict(list); orphan = []
for p in absorb:
    best, bestc = None, 0.0
    probe = p.buffer(3e-7)
    for j in tree.query(probe):
        c = probe.intersection(geoms[j]).area
        if c > bestc: best, bestc = j, c
    (adds[best].append(p) if best is not None else orphan.append(p))
new_geoms = list(geoms); changed = set(); refused = 0
def same_kind(m, g): return m.is_valid and m.geom_type == g.geom_type
for j, ps in adds.items():
    merged = unary_union([geoms[j]] + ps)
    if same_kind(merged, geoms[j]):
        new_geoms[j] = merged; changed.add(j); continue
    refused += 1                      # retry piece by piece, keep only the pieces that keep the polygon in one part
    cur = geoms[j]
    for p in ps:
        m = unary_union([cur, p])
        if same_kind(m, geoms[j]): cur = m
        else: orphan.append(p)
    if cur is not geoms[j]: new_geoms[j] = cur; changed.add(j)
changed = sorted(changed)
voids = []
for p in fill:                        # real voids only: big and not ribbon-like
    for poly in (p.geoms if hasattr(p, "geoms") else [p]):
        if poly.area * k >= SMALL_M2: voids.append(poly)
print(f"plan: {len(absorb)} small/thin gaps -> absorbed into {len(changed)} neighbours ({refused} neighbours refused: would turn MultiPolygon/invalid) | {len(voids)} larger voids -> class-0 polygons | thin pieces left as they are: {len(orphan)}", flush=True)
stats(new_geoms + voids, "AFTER (simulated)" if not APPLY else "AFTER")
print(f"computed in {time.time()-t0:.0f}s", flush=True)
if not APPLY:
    print("dry run: nothing written"); sys.exit(0)
create_grid_snapshot_from_db(db=db, task_grid_id=GRID, user_id=admin.id, note="Sebelum penutupan celah (serap ke tetangga)")
for j in changed:
    rows[j].geom_geojson = json.dumps(mapping(new_geoms[j])); rows[j].area_sqm = new_geoms[j].area * k
owner = task.assigned_user_id or admin.id
for poly in voids:
    db.add(Annotation(task_grid_id=GRID, user_id=owner, class_id=0, class_name="Belum Teridentifikasi", geom_geojson=json.dumps(mapping(poly)), area_sqm=poly.area * k))
db.commit()
print(f"APPLIED: {len(changed)} polygons extended, {len(voids)} class-0 polygons added", flush=True)
