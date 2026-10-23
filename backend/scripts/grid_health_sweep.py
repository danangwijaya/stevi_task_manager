"""Read-only health sweep of production polygons (a local copy; nothing here writes to any server).
usage: python -I grid_health_sweep.py <folder with grids.txt and polys.txt>   (see README.md for the two COPY exports)"""
import json, sys, csv, collections
from multiprocessing import Pool
from shapely.geometry import shape, box, LineString, MultiLineString, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

D = (sys.argv[1] if len(sys.argv) > 1 else '.').rstrip('/') + '/'      # folder with grids.txt and polys.txt; health.csv is written there
K = 111320.0 ** 2
M = 111320.0
# the 21 h window in which the quadrant auto-subdivision was live (commits 77cdb9b..0ea2e8e, +07:00 -> UTC)
WIN_A, WIN_B = '2026-10-16 18:04:05', '2026-10-17 15:11:29'

grids = {}
for l in open(D + 'grids.txt'):
    gid, code, year, status, user, x0, y0, x1, y1 = l.rstrip('\n').split('|')
    grids[int(gid)] = dict(code=code, year=int(year), status=status, user=int(user), bbox=(float(x0), float(y0), float(x1), float(y1)))

by_grid = collections.defaultdict(list)
for l in open(D + 'polys.txt'):
    aid, gid, cid, uid, cr, up, geo = l.rstrip('\n').split('|', 6)
    by_grid[int(gid)].append((int(aid), int(cid), int(uid), cr, up, geo))


def nverts(g):
    return sum(len(p.exterior.coords) + sum(len(r.coords) for r in p.interiors) for p in (g.geoms if hasattr(g, 'geoms') else [g]))


def axis_len(shared):
    """metres of `shared` that run exactly along a parallel/meridian (dx==0 or dy==0)."""
    lines = []
    if shared.is_empty:
        return 0.0, 0.0
    for part in (shared.geoms if hasattr(shared, 'geoms') else [shared]):
        if isinstance(part, LineString):
            lines.append(part)
        elif hasattr(part, 'geoms'):
            lines.extend(p for p in part.geoms if isinstance(p, LineString))
    tot = ax = 0.0
    for ln in lines:
        c = list(ln.coords)
        for (x0, y0), (x1, y1) in zip(c, c[1:]):
            L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 * M
            tot += L
            if abs(x1 - x0) < 1e-9 or abs(y1 - y0) < 1e-9:
                ax += L
    return tot, ax


def sweep(gid):
    g = grids[gid]
    rows = by_grid[gid]
    ids = [r[0] for r in rows]; cls = [r[1] for r in rows]
    geoms = [shape(json.loads(r[5])) for r in rows]
    gb = box(*g['bbox'])
    invalid = sum(1 for x in geoms if not x.is_valid)
    multi = sum(1 for x in geoms if x.geom_type != 'Polygon')
    holes = sum(len(p.interiors) for x in geoms for p in (x.geoms if hasattr(x, 'geoms') else [x]))
    verts = [nverts(x) for x in geoms]
    in_win = sum(1 for r in rows if WIN_A <= r[4][:19] <= WIN_B or WIN_A <= r[3][:19] <= WIN_B)
    fixed = [x if x.is_valid else x.buffer(0) for x in geoms]
    u = unary_union(fixed)
    gap = gb.difference(u)
    parts = [p for p in (gap.geoms if hasattr(gap, 'geoms') else [gap]) if not p.is_empty]
    gap_ge1 = sum(1 for p in parts if p.area * K >= 1)
    gap_big = sum(1 for p in parts if p.area * K >= 1000)
    tree = STRtree(fixed)
    ov = ovA = dup = 0
    iou_dup = 0
    open_holes = 0; open_hole_m2 = 0.0
    for i, a in enumerate(fixed):
        for q in (a.geoms if hasattr(a, 'geoms') else [a]):
            for ring in q.interiors:
                h = Polygon(ring)
                oth = [fixed[j] for j in tree.query(h, predicate='intersects') if j != i]
                unc = (h.difference(unary_union(oth)).area if oth else h.area) * K
                if unc >= 10:
                    open_holes += 1; open_hole_m2 += unc
    axis_pairs = 0; axis_m = 0.0; same_adj = 0
    for i, a in enumerate(fixed):
        for j in tree.query(a):
            if j <= i:
                continue
            b = fixed[j]
            x = a.intersection(b).area * K
            if x > 1:
                ov += 1; ovA += x
                if x > 0.9 * min(a.area, b.area) * K:
                    dup += 1
                if x / ((a.area + b.area) * K - x) >= 0.9:
                    iou_dup += 1
            if cls[i] == cls[j]:
                try:
                    sh = a.boundary.intersection(b.boundary)
                except Exception:
                    continue
                tot, ax = axis_len(sh)
                if tot >= 20:
                    same_adj += 1
                    if ax >= 50 and ax >= 0.5 * tot:
                        axis_pairs += 1; axis_m += ax
    return dict(grid=g['code'], year=g['year'], status=g['status'], polys=len(geoms), verts=sum(verts), max_verts=max(verts),
                holes=holes, invalid=invalid, multipart=multi, class0=sum(1 for c in cls if c == 0),
                coverage=round(100 * u.intersection(gb).area / gb.area, 4), gap_ge1m2=gap_ge1, gap_ge1000m2=gap_big,
                overlap_pairs=ov, overlap_ha=round(ovA / 1e4, 2), contained_pairs=dup, dup_iou90=iou_dup, open_holes_ge10m2=open_holes, open_hole_ha=round(open_hole_m2 / 1e4, 2),
                same_class_adjacent=same_adj, axis_aligned_pairs=axis_pairs, axis_aligned_m=round(axis_m),
                saved_in_window=in_win)


if __name__ == '__main__':
    gids = sorted(by_grid)
    with Pool(6) as pool, open(D + 'health.csv', 'w', newline='') as f:
        w = None
        for n, r in enumerate(pool.imap_unordered(sweep, gids), 1):
            if w is None:
                w = csv.DictWriter(f, fieldnames=list(r)); w.writeheader()
            w.writerow(r); f.flush()
            print(n, r['grid'], r['polys'], flush=True)
