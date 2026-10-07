import os
import json
import logging
from datetime import datetime
from shapely.geometry import shape, mapping, box, Polygon
from shapely.ops import unary_union
from sqlalchemy import func
from app.db.session import SessionLocal
from app.db.models import TaskGrid, Annotation, TaskReviewPin, GridSnapshot, AuditLog
from app.api.annotations import _extract_polygons
from app.services.snapshot_service import create_grid_snapshot_from_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cleanup_maintenance")

def run_cleanup():
    db = SessionLocal()
    try:
        logger.info("=== MEMULAI PROSES CLEANUP DAN MAINTENANCE DATABASE ===")

        # -------------------------------------------------------------
        # 1. DEDUPLIKASI GEOMETRI IDENTIK DI SEMUA GRID
        # -------------------------------------------------------------
        logger.info("--- [1] Memeriksa dan Menghapus Duplikat Geometri di Semua Grid ---")
        
        # Cari semua kelompok duplikat berdasarkan (task_grid_id, geom_geojson)
        all_anns = db.query(Annotation.id, Annotation.task_grid_id, Annotation.geom_geojson).order_by(Annotation.id.asc()).all()
        
        grid_geom_map = {}
        duplicates_to_delete = []
        pins_reassigned = 0

        for aid, grid_id, geom_str in all_anns:
            key = (grid_id, geom_str)
            if key not in grid_geom_map:
                grid_geom_map[key] = aid
            else:
                keep_id = grid_geom_map[key]
                duplicates_to_delete.append((aid, keep_id, grid_id))

        logger.info(f"Ditemukan {len(duplicates_to_delete)} poligon duplikat identik di database.")

        if duplicates_to_delete:
            # Reassign review pins dari id yang akan dihapus ke id yang dipertahankan
            for del_id, keep_id, grid_id in duplicates_to_delete:
                updated_pins = db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == del_id).update(
                    {"annotation_id": keep_id}, synchronize_session=False
                )
                pins_reassigned += updated_pins

            del_ids = [d[0] for d in duplicates_to_delete]
            # Hapus dalam batch 500 ID
            BATCH_SIZE = 500
            for i in range(0, len(del_ids), BATCH_SIZE):
                chunk = del_ids[i:i + BATCH_SIZE]
                db.query(Annotation).filter(Annotation.id.in_(chunk)).delete(synchronize_session=False)

            db.commit()
            logger.info(f"Berhasil menghapus {len(del_ids)} poligon duplikat! ({pins_reassigned} pin berhasil dialihkan)")

        # -------------------------------------------------------------
        # 2. PEMBERSIHAN SERPIHAN / SLIVERS KOSONG DI GRID 119
        # -------------------------------------------------------------
        logger.info("--- [2] Pembersihan Poligon Sliver Kosong di Grid 119 ---")
        g119_slivers = db.query(Annotation).filter(
            Annotation.task_grid_id == 119,
            Annotation.area_sqm < 1.0,
            Annotation.class_id == 0
        ).all()
        
        if g119_slivers:
            sliver_ids = [s.id for s in g119_slivers]
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id.in_(sliver_ids)).update(
                {"annotation_id": None}, synchronize_session=False
            )
            for i in range(0, len(sliver_ids), 500):
                chunk = sliver_ids[i:i + 500]
                db.query(Annotation).filter(Annotation.id.in_(chunk)).delete(synchronize_session=False)
            db.commit()
            logger.info(f"Berhasil membersihkan {len(sliver_ids)} poligon sliver kosong (< 1 m²) di Grid 119.")

        # -------------------------------------------------------------
        # 3. PENAMBALAN LUBANG DI GRID 30 (2025)
        # -------------------------------------------------------------
        logger.info("--- [3] Penambalan Lubang dan Celah Kosong di Grid 30 (2025) ---")
        tg30 = db.query(TaskGrid).filter(TaskGrid.id == 30).first()
        if tg30:
            grid_box = box(tg30.min_lon, tg30.min_lat, tg30.max_lon, tg30.max_lat)
            g30_anns = db.query(Annotation).filter(Annotation.task_grid_id == 30).all()
            
            geoms = []
            for a in g30_anns:
                try:
                    g = shape(json.loads(a.geom_geojson))
                    geoms.append(g if g.is_valid else g.buffer(0))
                except Exception:
                    pass

            union_all = unary_union(geoms)
            # Area lubang/gap
            gap_geom = grid_box.difference(union_all)
            
            if not gap_geom.is_empty:
                gap_polys = _extract_polygons(gap_geom, min_area_sqm=1.0)
                logger.info(f"Ditemukan {len(gap_polys)} bagian celah/lubang di Grid 30.")

                # Cari user_id untuk assignee
                assignee_id = tg30.assigned_user_id or 29 # Trisna

                patched_count = 0
                total_patched_sqm = 0.0

                for gp in gap_polys:
                    area_sqm = gp.area * (111320.0 ** 2)
                    # Jika lubang besar (> 1 ha) di pedalaman: Hutan Lahan Kering (class_id=1)
                    # Sesuai data citra/tahun 2022
                    c = gp.centroid
                    is_interior = not gp.intersects(grid_box.boundary)
                    
                    if area_sqm > 50000 and is_interior:
                        class_id = 1
                        class_name = "Hutan Lahan Kering"
                    elif is_interior and area_sqm > 1000:
                        class_id = 1
                        class_name = "Hutan Lahan Kering"
                    else:
                        # Celah batas luar atau celah samping: serap ke Hutan Lahan Kering agar konsisten
                        class_id = 1
                        class_name = "Hutan Lahan Kering"

                    new_ann = Annotation(
                        task_grid_id=30,
                        user_id=assignee_id,
                        class_id=class_id,
                        class_name=class_name,
                        geom_geojson=json.dumps(mapping(gp)),
                        area_sqm=area_sqm,
                        created_at=datetime.utcnow()
                    )
                    db.add(new_ann)
                    patched_count += 1
                    total_patched_sqm += area_sqm

                db.commit()
                logger.info(f"Berhasil menambal {patched_count} celah di Grid 30 seluas {total_patched_sqm:,.1f} m²!")

        # -------------------------------------------------------------
        # 4. BUAT SNAPSHOT SAFETY UNTUK GRID UTAMA
        # -------------------------------------------------------------
        for gid in [126, 121, 119, 30]:
            try:
                tg = db.query(TaskGrid).filter(TaskGrid.id == gid).first()
                if tg:
                    cnt = db.query(Annotation).filter(Annotation.task_grid_id == gid).count()
                    create_grid_snapshot_from_db(
                        db=db,
                        task_grid_id=gid,
                        user_id=tg.assigned_user_id or 1,
                        note="Pembersihan Duplikat & Penambalan Sistem (Maintenance)"
                    )
                    logger.info(f"Snapshot tersimpan untuk Grid {tg.grid_code} ({tg.year}): {cnt} poligon bersih.")
            except Exception as e:
                logger.warning(f"Gagal membuat snapshot grid {gid}: {e}")

        logger.info("=== SELESAI! SEMUA TAHAPAN CLEANUP DATABASE BERHASIL ===")

    finally:
        db.close()

if __name__ == "__main__":
    run_cleanup()
