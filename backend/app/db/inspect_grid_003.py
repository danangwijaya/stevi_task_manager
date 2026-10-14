import json
from shapely.geometry import shape, box, Polygon
from shapely.ops import unary_union
from app.db.session import SessionLocal
from app.db.models import TaskGrid, Annotation, GridSnapshot

db = SessionLocal()
tg = db.query(TaskGrid).filter(TaskGrid.id == 3).first()
anns = db.query(Annotation).filter(Annotation.task_grid_id == 3).order_by(Annotation.id.asc()).all()

print(f"=== GRID {tg.grid_code} (ID: 3) ===")
print(f"Total Annotations: {len(anns)}")

polys_with_holes = []
class_counts = {}
geoms = []
parsed_list = []

for a in anns:
    try:
        g = shape(json.loads(a.geom_geojson))
        if not g.is_valid:
            g = g.buffer(0)
        geoms.append(g)
        parsed_list.append((a, g))
        cname = a.class_name
        class_counts[cname] = class_counts.get(cname, 0) + 1
        
        num_holes = len(g.interiors) if hasattr(g, 'interiors') else 0
        if num_holes > 0:
            polys_with_holes.append({
                'id': a.id,
                'class_id': a.class_id,
                'class_name': a.class_name,
                'area_sqm': a.area_sqm or (g.area * (111320.0 ** 2)),
                'num_holes': num_holes,
                'geom': g,
                'created_at': a.created_at,
                'updated_at': a.updated_at
            })
    except Exception as e:
        print(f"Error parsing {a.id}: {e}")

print("\nClass distribution:")
for c, cnt in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {c}: {cnt}")

print(f"\nPolygons with interior holes: {len(polys_with_holes)}")
for p in sorted(polys_with_holes, key=lambda x: x['num_holes'], reverse=True):
    print(f"  • Poly #{p['id']} ({p['class_name']}) -> {p['num_holes']} HOLES | Area: {p['area_sqm']/1e6:.4f} km² ({p['area_sqm']:.1f} m²) | Created: {p['created_at']}")

# Now let's inspect the holes in the largest polygon with holes!
if polys_with_holes:
    largest = max(polys_with_holes, key=lambda x: x['num_holes'])
    print(f"\nAnalyzing holes of Poly #{largest['id']} ({largest['class_name']}):")
    hole_areas = []
    for h in largest['geom'].interiors:
        hole_poly = Polygon(h)
        hole_areas.append(hole_poly.area * (111320.0 ** 2))
    hole_areas.sort(reverse=True)
    print(f"  Total holes: {len(hole_areas)}")
    print(f"  Largest hole area: {hole_areas[0]:.1f} m² ({hole_areas[0]/1e6:.4f} km²)")
    print(f"  Smallest hole area: {hole_areas[-1]:.1f} m²")
    print(f"  Top 10 hole sizes (m²): {[round(x, 1) for x in hole_areas[:10]]}")

    # Check: are these holes filled by other polygons, or are they empty/void?
    other_geoms = [g for a, g in parsed_list if a.id != largest['id']]
    other_union = unary_union(other_geoms)
    
    empty_holes = []
    filled_holes = []
    for idx, h in enumerate(largest['geom'].interiors):
        hp = Polygon(h)
        inter = hp.intersection(other_union)
        fill_ratio = inter.area / (hp.area + 1e-12)
        if fill_ratio < 0.5:
            empty_holes.append((idx, hp.area * (111320.0**2), fill_ratio))
        else:
            filled_holes.append((idx, hp.area * (111320.0**2), fill_ratio))
            
    print(f"\nHoles in #{largest['id']} filled by other polygons: {len(filled_holes)}")
    print(f"Holes in #{largest['id']} that are COMPLETELY EMPTY (BOLONG): {len(empty_holes)}")
    for idx, area_sqm, fr in empty_holes[:15]:
        print(f"   - Empty Hole #{idx}: Area = {area_sqm:.1f} m² (filled only {fr*100:.1f}%)")

# Check Grid Coverage / Uncovered Gaps overall
grid_box = box(tg.min_lon, tg.min_lat, tg.max_lon, tg.max_lat)
grid_area = grid_box.area
union_all = unary_union(geoms)
covered_area = union_all.intersection(grid_box).area
coverage_pct = (covered_area / grid_area) * 100
uncovered = grid_box.difference(union_all)
uncovered_area_sqm = uncovered.area * (111320.0 ** 2)

print(f"\nGrid BBox Coverage: {coverage_pct:.4f}% covered")
print(f"Total Uncovered / Empty gap area across entire grid: {uncovered_area_sqm:.1f} m² ({uncovered_area_sqm/1e6:.4f} km²)")

if hasattr(uncovered, 'geoms'):
    unc_count = len(uncovered.geoms)
    print(f"Number of disjoint empty gap patches: {unc_count}")
    large_gaps = [g for g in uncovered.geoms if g.area * (111320.0**2) > 1.0]
    print(f"Empty gaps > 1 m²: {len(large_gaps)}")
    for i, lg in enumerate(sorted(large_gaps, key=lambda x: x.area, reverse=True)[:10]):
        bounds = lg.bounds
        print(f"   Gap #{i+1}: {lg.area * (111320.0**2):.1f} m² at coords ({bounds[0]:.6f}, {bounds[1]:.6f})")
else:
    print(f"Empty gap geometry type: {uncovered.geom_type}, area: {uncovered_area_sqm:.1f} m²")

# Check recent snapshots for Grid 3
print("\nRecent Snapshots for Grid 3:")
snaps = db.query(GridSnapshot).filter(GridSnapshot.task_grid_id == 3).order_by(GridSnapshot.created_at.desc()).limit(5).all()
for s in snaps:
    print(f"  Snap #{s.id} (v{s.version_number}) | {s.features_count} feats | Note: {s.note} | At: {s.created_at}")

db.close()
