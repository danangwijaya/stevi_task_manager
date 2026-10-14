"""
Script Pembersihan & Penyelamatan Poligon Menumpuk (Stacking / Overlap Parah)
Khusus Grid 013_2025 (Tasya), Grid 003_2025 (Rizki), Grid 011_2025, atau Grid Lainnya di VPS.

Cara Penggunaan di VPS:
1. Dry Run (Hanya Memeriksa tanpa mengubah database):
   docker exec geoai_backend python -m app.db.fix_grid_013_stacked_vps --grid 13
   docker exec geoai_backend python -m app.db.fix_grid_013_stacked_vps --grid 3
   docker exec geoai_backend python -m app.db.fix_grid_013_stacked_vps --grid 11

2. Eksekusi Perbaikan (Dengan otomatis backup snapshot dan hapus duplikat menumpuk):
   docker exec geoai_backend python -m app.db.fix_grid_013_stacked_vps --grid 13 --apply
   docker exec geoai_backend python -m app.db.fix_grid_013_stacked_vps --grid 3 --apply
   docker exec geoai_backend python -m app.db.fix_grid_013_stacked_vps --grid 11 --apply
"""

import sys
import json
import logging
import argparse
from datetime import datetime
from shapely.geometry import shape, mapping
from shapely.strtree import STRtree
from sqlalchemy import func
from app.db.session import SessionLocal
from app.db.models import TaskGrid, Annotation, TaskReviewPin, User
from app.services.snapshot_service import create_grid_snapshot_from_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fix_stacked_polygons")

def analyze_and_fix_grid(grid_query_str: str, apply_changes: bool = False):
    db = SessionLocal()
    try:
        logger.info(f"=== ANALISIS POLIGON MENUMPUK UNTUK QUERY: '{grid_query_str}' ===")

        tasks = []
        if grid_query_str.isdigit():
            t = db.query(TaskGrid).filter(TaskGrid.id == int(grid_query_str)).first()
            if t:
                tasks.append(t)
        elif grid_query_str.lower() == "all-stacked":
            # Periksa grid 13, 3, 11 secara langsung
            tasks = db.query(TaskGrid).filter(TaskGrid.id.in_([13, 3, 11])).all()
        else:
            tasks = db.query(TaskGrid).filter(TaskGrid.grid_code.ilike(f"%{grid_query_str}%")).all()

        if not tasks:
            # Cari juga berdasarkan assignee (Tasya / Rizki)
            users = db.query(User).filter(
                (User.username.ilike(f"%{grid_query_str}%")) |
                (User.full_name.ilike(f"%{grid_query_str}%"))
            ).all()
            for u in users:
                user_tasks = db.query(TaskGrid).filter(TaskGrid.assigned_user_id == u.id, TaskGrid.year == 2025).all()
                tasks.extend(user_tasks)

        if not tasks:
            logger.error(f"Tidak ditemukan task grid dengan pencarian: '{grid_query_str}'")
            return

        logger.info(f"Ditemukan {len(tasks)} grid untuk dianalisis:")
        for t in tasks:
            assignee_name = t.assignee.full_name if t.assignee else "Belum Ditugaskan"
            ann_count = db.query(Annotation).filter(Annotation.task_grid_id == t.id).count()
            logger.info(f"  • ID {t.id} | {t.grid_code} ({t.year}) | Assignee: {assignee_name} | Poligon: {ann_count}")

        for task in tasks:
            logger.info(f"\n=======================================================")
            logger.info(f"MEMERIKSA GRID ID {task.id} ({task.grid_code})")
            logger.info(f"=======================================================")

            anns = db.query(Annotation).filter(Annotation.task_grid_id == task.id).order_by(Annotation.id.asc()).all()
            if not anns:
                logger.info("Grid tidak memiliki poligon anotasi.")
                continue

            parsed_polys = []
            geoms = []
            for a in anns:
                try:
                    g = shape(json.loads(a.geom_geojson))
                    if not g.is_valid:
                        g = g.buffer(0)
                    holes = len(g.interiors) if hasattr(g, 'interiors') else 0
                    parsed_polys.append({
                        "id": a.id,
                        "class_id": a.class_id,
                        "class_name": a.class_name,
                        "area_sqm": a.area_sqm or (g.area * (111320.0 ** 2)),
                        "geom": g,
                        "wkb": g.wkb,
                        "holes": holes,
                        "created_at": a.created_at,
                        "raw": a
                    })
                    geoms.append(g)
                except Exception as e:
                    logger.warning(f"Gagal parse poligon #{a.id}: {e}")

            logger.info(f"Total poligon valid terbaca: {len(parsed_polys)}")

            # STRtree Fast Pairwise Collision Detection
            tree = STRtree(geoms)
            to_delete_map = {}  # del_id -> { 'del': p, 'keep': p, 'reason': str }
            checked_pairs = set()

            for i, p1 in enumerate(parsed_polys):
                for j in tree.query(p1["geom"]):
                    if i >= j:
                        continue
                    pair = (i, j)
                    if pair in checked_pairs:
                        continue
                    checked_pairs.add(pair)

                    p2 = parsed_polys[j]
                    if not p1["geom"].intersects(p2["geom"]):
                        continue

                    try:
                        inter = p1["geom"].intersection(p2["geom"])
                        if inter.is_empty or inter.area <= 0:
                            continue
                        r1 = inter.area / (p1["geom"].area + 1e-12)
                        r2 = inter.area / (p2["geom"].area + 1e-12)

                        # MUTUAL STACK (> 85% overlap pada kedua poligon)
                        if r1 > 0.85 and r2 > 0.85:
                            # Tentukan mana yang disimpan dan mana yang dihapus:
                            # Prioritas simpan:
                            # 1. Jika beda tanggal pembuatan, simpan yang lebih baru (latest user edit)
                            # 2. Jika sama/hampir sama waktu, simpan yang memiliki lubang (holes) lebih lengkap
                            # 3. Jika lubang sama, simpan ID yang lebih baru
                            if p1["created_at"] < p2["created_at"]:
                                del_p, keep_p = p1, p2
                            elif p1["created_at"] > p2["created_at"]:
                                del_p, keep_p = p2, p1
                            else:
                                if p1["holes"] < p2["holes"]:
                                    del_p, keep_p = p1, p2
                                elif p1["holes"] > p2["holes"]:
                                    del_p, keep_p = p2, p1
                                else:
                                    del_p = p1 if p1["id"] < p2["id"] else p2
                                    keep_p = p2 if p1["id"] < p2["id"] else p1

                            reason = f"Mutual Overlap {max(r1, r2)*100:.1f}% (del: #{del_p['id']} [{del_p['class_name']}], keep: #{keep_p['id']} [{keep_p['class_name']}])"
                            to_delete_map[del_p["id"]] = {
                                "del": del_p,
                                "keep": keep_p,
                                "reason": reason
                            }
                    except Exception:
                        pass

            logger.info(f"\nDitemukan {len(to_delete_map)} poligon duplikat menumpuk parah:")
            for del_id, info in list(to_delete_map.items())[:20]:
                d = info["del"]
                k = info["keep"]
                logger.info(f"  ❌ Hapus #{d['id']} ({d['class_name']}, {d['area_sqm']/1e6:.2f} km², {d['holes']} holes)")
                logger.info(f"     -> Dipertahankan: #{k['id']} ({k['class_name']}, {k['area_sqm']/1e6:.2f} km², {k['holes']} holes)")
                logger.info(f"     -> Info: {info['reason']}")

            if len(to_delete_map) > 20:
                logger.info(f"  ... dan {len(to_delete_map) - 20} poligon lainnya.")

            # Eksekusi Pembersihan
            if apply_changes:
                if not to_delete_map:
                    logger.info(f"Tidak ada poligon menumpuk yang perlu dihapus pada Grid {task.id}.")
                else:
                    # 1. Simpan Snapshot Cadangan
                    snap = create_grid_snapshot_from_db(
                        db=db,
                        task_grid_id=task.id,
                        user_id=task.assigned_user_id or 1,
                        note="Backup Sebelum Pembersihan Poligon Menumpuk (Maintenance Script)"
                    )
                    logger.info(f"✓ Snapshot backup berhasil dibuat (Snapshot ID: {snap.id}).")

                    del_ids = list(to_delete_map.keys())

                    # 2. Alihkan pin review jika ada yang menunjuk ke poligon yang dihapus
                    for del_id, info in to_delete_map.items():
                        db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == del_id).update(
                            {"annotation_id": info["keep"]["id"]}, synchronize_session=False
                        )

                    # 3. Hapus poligon duplikat menumpuk
                    for i in range(0, len(del_ids), 500):
                        chunk = del_ids[i:i + 500]
                        db.query(Annotation).filter(Annotation.id.in_(chunk)).delete(synchronize_session=False)

                    # 4. Update task timestamp
                    task.updated_at = datetime.utcnow()
                    db.commit()

                    remaining = db.query(Annotation).filter(Annotation.task_grid_id == task.id).count()
                    logger.info(f"✓ BERHASIL MENGHAPUS {len(del_ids)} POLIGON DUPLIKAT MENUMPUK DI GRID {task.grid_code}!")
                    logger.info(f"✓ Jumlah poligon tersisa yang bersih: {remaining}")
            else:
                logger.info("\n[MODE DRY RUN]: Tidak ada perubahan disimpan ke database.")
                logger.info("Jalankan dengan flag '--apply' untuk mengeksekusi pembersihan.")

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pembersihan Poligon Menumpuk di VPS")
    parser.add_argument("--grid", type=str, default="13", help="ID Grid, kode grid, atau 'all-stacked' (default: 13)")
    parser.add_argument("--apply", action="store_true", help="Terapkan pembersihan ke database")
    args = parser.parse_args()

    analyze_and_fix_grid(args.grid, apply_changes=args.apply)
