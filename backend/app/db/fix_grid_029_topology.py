import json
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.validation import make_valid
from shapely.ops import unary_union
from app.db.session import SessionLocal
from app.db.models import Annotation, TaskGrid, TaskReviewPin
from app.services.snapshot_service import create_grid_snapshot_from_db
from app.api.annotations import validate_topology, _extract_polygons

def fix_task_29():
    db = SessionLocal()
    task_id = 29
    task = db.query(TaskGrid).filter(TaskGrid.id == task_id).first()
    if not task:
        print("Task 29 not found!")
        return

    print(f"=== Starting Topology Fix for Task 29 ({task.grid_code}) ===")
    
    # 1. Create safety snapshot
    snap = create_grid_snapshot_from_db(
        db=db,
        task_grid_id=task_id,
        user_id=task.assigned_user_id or 1,
        note="Sebelum Pembersihan Background & Topologi Grid 29"
    )
    print(f"Snapshot created: ID {snap.id}, Version {snap.version_number}")

    # 2. Fetch all annotations
    anns = db.query(Annotation).filter(Annotation.task_grid_id == task_id).all()
    print(f"Total annotations in DB: {len(anns)}")

    bg_id = 18558351
    bg_ann = None
    fg_anns = []

    for a in anns:
        if a.id == bg_id:
            bg_ann = a
        else:
            fg_anns.append(a)

    print(f"Found background polygon #{bg_id} and {len(fg_anns)} foreground polygons.")

    # 3. Clean and collect foreground polygons
    fg_items = []
    fg_geoms = []

    for a in fg_anns:
        try:
            g = shape(json.loads(a.geom_geojson))
            if not g.is_valid:
                g = make_valid(g)
            polys = _extract_polygons(g, min_area_sqm=3.0)
            if polys:
                p0 = polys[0]
                area_sqm = p0.area * (111320.0 ** 2)
                fg_items.append({
                    "ann": a,
                    "geom": p0,
                    "area_sqm": area_sqm,
                    "class_id": a.class_id,
                    "class_name": a.class_name
                })
                fg_geoms.append(p0)
        except Exception as e:
            print(f"Error parsing foreground ann {a.id}: {e}")

    # 4. Pairwise clip overlaps among foreground polygons
    # Sort: real classes before class 0, smaller first (detailed objects clip larger ones)
    fg_items.sort(key=lambda x: (1 if x["class_id"] == 0 else 0, x["area_sqm"]))
    
    accepted_fg = []
    clip_thresh = 1.0 / (111320.0 ** 2) # ~1 sqm
    clipped_count = 0

    for item in fg_items:
        cur_geom = item["geom"]
        cur_ann = item["ann"]
        was_clipped = False

        for acc in accepted_fg:
            if not cur_geom.is_empty and cur_geom.intersects(acc["geom"]):
                try:
                    inter = cur_geom.intersection(acc["geom"])
                    if inter.area > clip_thresh:
                        cur_geom = cur_geom.difference(acc["geom"])
                        cur_geom = make_valid(cur_geom)
                        was_clipped = True
                        clipped_count += 1
                except Exception:
                    pass

        extracted = _extract_polygons(cur_geom, min_area_sqm=3.0)
        if extracted:
            p0 = extracted[0]
            accepted_fg.append({
                "ann": cur_ann,
                "geom": p0,
                "area_sqm": p0.area * (111320.0 ** 2),
                "class_id": item["class_id"],
                "class_name": item["class_name"]
            })
            for extra_p in extracted[1:]:
                extra_sqm = extra_p.area * (111320.0 ** 2)
                if extra_sqm >= 3.0:
                    new_ann = Annotation(
                        task_grid_id=task_id,
                        user_id=cur_ann.user_id,
                        class_id=cur_ann.class_id,
                        class_name=cur_ann.class_name,
                        geom_geojson=json.dumps(mapping(extra_p)),
                        area_sqm=extra_sqm
                    )
                    db.add(new_ann)
                    db.flush()
                    accepted_fg.append({
                        "ann": new_ann,
                        "geom": extra_p,
                        "area_sqm": extra_sqm,
                        "class_id": cur_ann.class_id,
                        "class_name": cur_ann.class_name
                    })

    print(f"Foreground cleaned: {clipped_count} overlaps clipped. Accepted {len(accepted_fg)} foreground features.")

    # 5. Background subtraction
    bg_polys = []
    if bg_ann:
        try:
            bg_geom = shape(json.loads(bg_ann.geom_geojson))
            if not bg_geom.is_valid:
                bg_geom = make_valid(bg_geom)
            
            print("Computing unary union of all foreground polygons...")
            all_fg_geoms = [it["geom"] for it in accepted_fg if not it["geom"].is_empty and it["geom"].is_valid]
            fg_union = unary_union(all_fg_geoms)
            print("Subtracting foreground union from background polygon #18558351...")
            bg_diff = bg_geom.difference(fg_union)
            bg_diff = make_valid(bg_diff)
            bg_polys = _extract_polygons(bg_diff, min_area_sqm=5.0)
            print(f"Background subtracted into {len(bg_polys)} clean singlepart polygons.")
        except Exception as e:
            print(f"Error subtracting background: {e}")

    # 6. Apply updates to DB
    print("Writing updates to database...")
    fg_ann_ids = set()
    for item in accepted_fg:
        ann = item["ann"]
        ann.geom_geojson = json.dumps(mapping(item["geom"]))
        ann.area_sqm = item["area_sqm"]
        fg_ann_ids.add(ann.id)

    # If background produced polygons:
    if bg_ann and bg_polys:
        # First piece retains original bg_ann ID
        p0 = bg_polys[0]
        bg_ann.geom_geojson = json.dumps(mapping(p0))
        bg_ann.area_sqm = p0.area * (111320.0 ** 2)
        fg_ann_ids.add(bg_ann.id)

        # Additional pieces
        for extra_bg in bg_polys[1:]:
            extra_sqm = extra_bg.area * (111320.0 ** 2)
            new_bg = Annotation(
                task_grid_id=task_id,
                user_id=bg_ann.user_id,
                class_id=bg_ann.class_id,
                class_name=bg_ann.class_name,
                geom_geojson=json.dumps(mapping(extra_bg)),
                area_sqm=extra_sqm
            )
            db.add(new_bg)
            db.flush()
            fg_ann_ids.add(new_bg.id)

    # Delete any foreground annotations that were completely covered / eliminated
    all_old_ids = {a.id for a in anns}
    deleted_ids = list(all_old_ids - fg_ann_ids)
    if deleted_ids:
        print(f"Deleting {len(deleted_ids)} obsolete/absorbed sliver annotations...")
        for i in range(0, len(deleted_ids), 500):
            chunk = deleted_ids[i:i + 500]
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id.in_(chunk)).update({"annotation_id": None}, synchronize_session=False)
            db.query(Annotation).filter(Annotation.id.in_(chunk)).delete(synchronize_session=False)

    db.commit()
    print("Database committed successfully.")

    # 7. Validate topology
    val = validate_topology(task_id, db)
    print(f"=== Task 29 Validation Result: Valid={val['valid']}, Total Errors={len(val['errors'])} ===")
    for e in val["errors"][:5]:
        print(f"  - {e.get('type')}: {e.get('message')}")

if __name__ == "__main__":
    fix_task_29()
