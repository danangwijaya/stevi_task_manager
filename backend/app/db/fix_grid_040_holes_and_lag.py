import json
from shapely.geometry import shape, mapping, Polygon, MultiPolygon, box
from shapely.validation import make_valid
from shapely.ops import unary_union
from app.db.session import SessionLocal
from app.db.models import Annotation, TaskGrid, TaskReviewPin
from app.services.snapshot_service import create_grid_snapshot_from_db
from app.api.annotations import validate_topology, _extract_polygons

def subdivide_multihole_polygon(poly, max_holes=15):
    if poly.geom_type != 'Polygon' or len(poly.interiors) <= max_holes:
        return [poly]
    minx, miny, maxx, maxy = poly.bounds
    midx = (minx + maxx) / 2.0
    midy = (miny + maxy) / 2.0
    quads = [
        box(minx, miny, midx, midy),
        box(midx, miny, maxx, midy),
        box(minx, midy, midx, maxy),
        box(midx, midy, maxx, maxy),
    ]
    pieces = []
    for q in quads:
        if poly.intersects(q):
            try:
                part = poly.intersection(q)
                part = make_valid(part)
                extracted = _extract_polygons(part, min_area_sqm=5.0)
                for p in extracted:
                    if len(p.interiors) > max_holes:
                        pieces.extend(subdivide_multihole_polygon(p, max_holes))
                    else:
                        pieces.append(p)
            except Exception as e:
                print(f"Error subdividing quad: {e}")
    return pieces if pieces else [poly]

def fix_task_156():
    db = SessionLocal()
    task_id = 156
    task = db.query(TaskGrid).filter(TaskGrid.id == task_id).first()
    if not task:
        print("Task 156 not found!")
        return

    print(f"=== Starting Lag & Duplicate Cleanup for Task 156 ({task.grid_code}) ===")

    # 1. Create safety snapshot
    snap = create_grid_snapshot_from_db(
        db=db,
        task_grid_id=task_id,
        user_id=task.assigned_user_id or 1,
        note="Sebelum Optimasi Lubang dan Lag Grid 040"
    )
    print(f"Snapshot created: ID {snap.id}, Version {snap.version_number}")

    # 2. Remove duplicate polygon #18571254 (95% overlap with #18571251)
    dup_ann = db.query(Annotation).filter(Annotation.id == 18571254).first()
    if dup_ann:
        print("Removing duplicate stacked polygon #18571254...")
        db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == 18571254).update({"annotation_id": None}, synchronize_session=False)
        db.delete(dup_ann)
        db.flush()

    # 3. Load all remaining annotations
    anns = db.query(Annotation).filter(Annotation.task_grid_id == task_id).all()
    print(f"Loaded {len(anns)} annotations.")

    # Target the giant multi-hole background polygons: #18574020, #7608100, #7607721, #18505380
    heavy_ids = {18574020, 7608100, 7607721, 18505380, 18574021}
    heavy_anns = [a for a in anns if a.id in heavy_ids]
    fg_anns = [a for a in anns if a.id not in heavy_ids]

    print(f"Identified {len(heavy_anns)} heavy background polygons and {len(fg_anns)} foreground polygons.")

    # Collect foreground geometries
    fg_geoms = []
    for a in fg_anns:
        try:
            g = shape(json.loads(a.geom_geojson))
            if not g.is_valid:
                g = make_valid(g)
            if not g.is_empty:
                fg_geoms.append(g)
        except Exception as e:
            print(f"Error parsing fg ann {a.id}: {e}")

    print("Computing unary union of foreground polygons for clean boundary cutting...")
    fg_union = unary_union(fg_geoms)

    # Process each heavy polygon
    new_anns_to_add = []
    clip_thresh = 1.0 / (111320.0 ** 2)

    for h_ann in heavy_anns:
        try:
            h_geom = shape(json.loads(h_ann.geom_geojson))
            if not h_geom.is_valid:
                h_geom = make_valid(h_geom)
            
            orig_holes = len(h_geom.interiors) if h_geom.geom_type == 'Polygon' else 0
            print(f"Processing #{h_ann.id} ({h_ann.class_name}) with {orig_holes} holes...")

            # Subtract foreground union to eliminate all micro-overlaps at hole boundaries
            if h_geom.intersects(fg_union):
                h_geom = h_geom.difference(fg_union)
                h_geom = make_valid(h_geom)

            extracted = _extract_polygons(h_geom, min_area_sqm=5.0)
            if not extracted:
                continue

            # Subdivide any extracted polygon that still has > 15 holes
            final_sub_polys = []
            for p in extracted:
                sub_parts = subdivide_multihole_polygon(p, max_holes=15)
                final_sub_polys.extend(sub_parts)

            print(f"#{h_ann.id} converted into {len(final_sub_polys)} sub-polygons (max holes <= 15).")

            # First piece retains the original ID
            p0 = final_sub_polys[0]
            h_ann.geom_geojson = json.dumps(mapping(p0))
            h_ann.area_sqm = p0.area * (111320.0 ** 2)

            # Additional pieces become new annotations of same class
            for extra_p in final_sub_polys[1:]:
                extra_sqm = extra_p.area * (111320.0 ** 2)
                if extra_sqm >= 5.0:
                    new_ann = Annotation(
                        task_grid_id=task_id,
                        user_id=h_ann.user_id,
                        class_id=h_ann.class_id,
                        class_name=h_ann.class_name,
                        geom_geojson=json.dumps(mapping(extra_p)),
                        area_sqm=extra_sqm
                    )
                    db.add(new_ann)
                    db.flush()
        except Exception as e:
            print(f"Error processing heavy polygon #{h_ann.id}: {e}")

    db.commit()
    print("Database committed. Checking topology validation...")

    val = validate_topology(task_id, db)
    print(f"=== Task 156 Validation Result: Valid={val['valid']}, Total Errors={len(val['errors'])} ===")
    for e in val["errors"][:10]:
        print(f"  - {e.get('type')}: {e.get('message')}")

if __name__ == "__main__":
    fix_task_156()
