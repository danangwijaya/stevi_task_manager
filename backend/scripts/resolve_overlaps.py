"""Remove overlaps inside one grid: where two polygons overlap by more than MIN_M2, the overlapping part is cut out of the LARGER
polygon (the smaller one wins, like an island inside a bigger polygon). A polygon that would turn into several parts, become
invalid or vanish is left alone and reported. Nothing else is touched.
usage: python - <grid> [--apply] [--idle-min=N] [--min-m2=1]   (default = dry run: nothing is written)"""
import json, sys
from collections import defaultdict
from datetime import datetime, timedelta
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree
from sqlalchemy import text
from app.db.session import SessionLocal
from app.db.models import User, TaskGrid, Annotation
from app.services.snapshot_service import create_grid_snapshot_from_db, log_audit

GRID = int(sys.argv[1]); APPLY = "--apply" in sys.argv
IDLE_MIN = next((int(a.split('=')[1]) for a in sys.argv if a.startswith('--idle-min=')), 30)
MIN_M2 = next((float(a.split('=')[1]) for a in sys.argv if a.startswith('--min-m2=')), 1.0)
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
geoms = []
for r in rows:
    g = shape(json.loads(r.geom_geojson)); geoms.append(g if g.is_valid else g.buffer(0))
area = [g.area for g in geoms]
tree = STRtree(geoms)
cut_from = defaultdict(list)          # larger polygon index -> overlapping parts to remove
pairs = 0
for i, a in enumerate(geoms):
    for j in tree.query(a):
        j = int(j)
        if j <= i: continue
        inter = a.intersection(geoms[j])
        if inter.area * k <= MIN_M2: continue
        pairs += 1
        big = i if (area[i], rows[i].id) >= (area[j], rows[j].id) else j
        cut_from[big].append(inter)
print(f"overlapping pairs > {MIN_M2} m2: {pairs} | larger polygons to cut: {len(cut_from)}", flush=True)

def parts(g): return list(g.geoms) if hasattr(g, "geoms") else [g]
new_geom, skipped = {}, []
for idx, inters in cut_from.items():
    cut = unary_union(inters)
    res = geoms[idx].difference(cut)
    polys = [p for p in parts(res) if p.geom_type == "Polygon" and p.area * k >= 0.1]
    if len(polys) != 1 or not polys[0].is_valid or polys[0].is_empty:
        skipped.append((rows[idx].id, len(polys))); continue
    new_geom[idx] = polys[0]
print(f"cuttable: {len(new_geom)} | skipped (would split, invalidate or vanish): {len(skipped)} {skipped[:8]}", flush=True)

after = list(geoms)
for idx, g in new_geom.items(): after[idx] = g
t2 = STRtree(after); left = 0; left_m2 = 0.0
for i, a in enumerate(after):
    for j in t2.query(a):
        j = int(j)
        if j > i:
            x = a.intersection(after[j]).area * k
            if x > MIN_M2: left += 1; left_m2 += x
print(f"[AFTER (simulated)] overlapping pairs > {MIN_M2} m2: {left} ({left_m2/1e4:.2f} ha) | polygons: {len(rows)} (none added or removed)", flush=True)
lost = sum((geoms[i].area - g.area) * k for i, g in new_geom.items()) / 1e4
print(f"area removed from the larger polygons: {lost:.2f} ha (all of it stays covered by the smaller polygon)", flush=True)
if not APPLY:
    print("dry run: nothing written"); sys.exit(0)
create_grid_snapshot_from_db(db=db, task_grid_id=GRID, user_id=admin.id, note="Sebelum selesaikan tumpang tindih (poligon lebih kecil menang)")
for idx, g in new_geom.items():
    rows[idx].geom_geojson = json.dumps(mapping(g)); rows[idx].area_sqm = g.area * k
log_audit(db=db, user_id=admin.id, action="RESOLVE_OVERLAPS", entity_type="task_grid", entity_id=GRID, task_grid_id=GRID,
          details=json.dumps({"cut": len(new_geom), "skipped": len(skipped), "pairs_before": pairs, "pairs_after": left}))
db.commit()
print(f"APPLIED: {len(new_geom)} polygons trimmed", flush=True)
