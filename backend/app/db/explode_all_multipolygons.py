import json
import logging
from shapely.geometry import shape, mapping
from app.db.session import SessionLocal
from app.db.models import Annotation, TaskReviewPin, TaskGrid
from app.api.annotations import _extract_polygons

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("explode_multipolygons")

def explode_all_multipolygons(db=None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        all_anns = db.query(Annotation).all()
        multi_anns = []
        for ann in all_anns:
            try:
                g = json.loads(ann.geom_geojson)
                if g.get("type") in ["MultiPolygon", "GeometryCollection"]:
                    multi_anns.append(ann)
            except Exception:
                pass

        logger.info(f"Ditemukan {len(multi_anns)} poligon multi-part dari total {len(all_anns)} anotasi.")
        
        converted_grids = set()
        new_annotations_count = 0
        deleted_count = 0

        for ann in multi_anns:
            try:
                g = json.loads(ann.geom_geojson)
                s_geom = shape(g)
                pieces = _extract_polygons(s_geom, min_area_sqm=0.1)
                
                if not pieces:
                    continue

                tg = db.query(TaskGrid).filter(TaskGrid.id == ann.task_grid_id).first()
                grid_info = f"Grid {tg.grid_code if tg else ann.task_grid_id} (Tahun: {tg.year if tg else '?'})"
                converted_grids.add(grid_info)

                logger.info(
                    f"Exploding Annotation ID {ann.id} [{grid_info}, Class {ann.class_id}: {ann.class_name}] "
                    f"menjadi {len(pieces)} poligon tunggal (singlepart)..."
                )

                # Reassign or safeguard pins linked to this annotation
                # Create the first piece reusing the same concept, and rest as new annotations
                new_anns_for_this = []
                for idx, p in enumerate(pieces):
                    area_sqm = p.area * (111320.0 ** 2)
                    new_a = Annotation(
                        task_grid_id=ann.task_grid_id,
                        user_id=ann.user_id,
                        class_id=ann.class_id,
                        class_name=ann.class_name,
                        geom_geojson=json.dumps(mapping(p)),
                        area_sqm=area_sqm,
                        created_at=ann.created_at
                    )
                    db.add(new_a)
                    new_anns_for_this.append(new_a)
                    new_annotations_count += 1

                db.flush() # get new IDs

                # Point review pins to the largest piece
                largest_new_a = max(new_anns_for_this, key=lambda a: a.area_sqm or 0)
                db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann.id).update(
                    {"annotation_id": largest_new_a.id}, synchronize_session=False
                )

                # Delete the old multi-part annotation
                db.delete(ann)
                deleted_count += 1

            except Exception as e:
                logger.error(f"Error exploding annotation {ann.id}: {e}")

        db.commit()
        logger.info(
            f"SELESAI! Berhasil memecah {deleted_count} multi-part poligon menjadi "
            f"{new_annotations_count} poligon tunggal (singlepart) di {len(converted_grids)} grid."
        )
        return {
            "deleted_multipart_count": deleted_count,
            "created_singlepart_count": new_annotations_count,
            "affected_grids": list(converted_grids)
        }

    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    explode_all_multipolygons()
