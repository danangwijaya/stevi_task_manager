"""
Script Perbaikan Poligon Bolong & Celah Kosong di Grid 003_2025 (Rizky)
Serta Grid Lainnya di VPS.

Fitur:
1. Menutup bolongan poligon yang di dalamnya terdapat poligon dari kelas yang sama (Same-Class Hole Dissolve).
   Misal: Poligon Semak & Belukar berlubang yang di dalam lubangnya adalah Semak & Belukar juga.
2. Menutup celah kosong (gaps) yang bolong / belum tercakup poligon dengan menyatukannya ke poligon tetangga terpanjang.
3. Otomatis membuat snapshot cadangan (backup) sebelum melakukan modifikasi.

Cara Penggunaan di VPS:
1. Dry Run (Analisis saja tanpa simpan):
   docker exec geoai_backend python -m app.db.fix_grid_003_holes_vps --grid 3

2. Eksekusi Perbaikan:
   docker exec geoai_backend python -m app.db.fix_grid_003_holes_vps --grid 3 --apply
"""

import sys
import json
import logging
import argparse
from datetime import datetime
from shapely.geometry import shape, mapping, Polygon, box
from shapely.ops import unary_union
from app.db.session import SessionLocal
from app.db.models import TaskGrid, Annotation, TaskReviewPin
from app.services.snapshot_service import create_grid_snapshot_from_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fix_holes_and_gaps")

def fix_grid_holes(task_grid_id: int, apply_changes: bool = False, fill_gaps: bool = True):
    db = SessionLocal()
    try:
        logger.info(f"=== ANALISIS POLIGON BOLONG & CELAH KOSONG PADA GRID ID: {task_grid_id} ===")
        tg = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
        if not tg:
            logger.error(f"Grid ID {task_grid_id} tidak ditemukan.")
            return

        anns = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).order_by(Annotation.id.asc()).all()
        if not anns:
            logger.info("Grid tidak memiliki poligon.")
            return

        assignee_name = tg.assignee.full_name if tg.assignee else "Belum Ditugaskan"
        logger.info(f"Grid: {tg.grid_code} | Assignee: {assignee_name} | Total Poligon: {len(anns)}")

        # Parse semua geometri
        parsed_dict = {}
        for a in anns:
            try:
                g = shape(json.loads(a.geom_geojson))
                if not g.is_valid:
                    g = g.buffer(0)
                parsed_dict[a.id] = {
                    "ann": a,
                    "geom": g,
                    "class_id": a.class_id,
                    "class_name": a.class_name
                }
            except Exception as e:
                logger.warning(f"Gagal parse poligon #{a.id}: {e}")

        # ─────────────────────────────────────────────────────────────────────
        # 1. DETEKSI & DISSOLVE LUBANG DENGAN KELAS SAMA (SAME-CLASS HOLE MERGE)
        # ─────────────────────────────────────────────────────────────────────
        logger.info("\n--- 1. Memeriksa Lubang Poligon yang Diisi Kelas yang Sama ---")
        same_class_merges = [] # list of (outer_id, inner_id, hole_area)
        absorbed_inner_ids = set()

        for a_id, data in list(parsed_dict.items()):
            g = data["geom"]
            if not hasattr(g, "interiors") or len(g.interiors) == 0:
                continue

            for h in g.interiors:
                hole_poly = Polygon(h)
                hole_area_sqm = hole_poly.area * (111320.0 ** 2)
                if hole_area_sqm < 5.0:
                    continue

                for o_id, o_data in list(parsed_dict.items()):
                    if o_id == a_id or o_id in absorbed_inner_ids:
                        continue
                    if o_data["class_id"] != data["class_id"]:
                        continue

                    og = o_data["geom"]
                    if og.intersects(hole_poly):
                        inter_area = og.intersection(hole_poly).area
                        # Jika poligon dalam berada > 80% di dalam lubang poligon luar
                        if inter_area > 0.80 * og.area:
                            same_class_merges.append((a_id, o_id, hole_area_sqm, data["class_name"]))
                            absorbed_inner_ids.add(o_id)

        logger.info(f"Ditemukan {len(same_class_merges)} kasus lubang poligon yang diisi oleh poligon kelas yang sama:")
        for outer_id, inner_id, h_area, cname in same_class_merges[:15]:
            logger.info(f"  • Poligon #{outer_id} ({cname}) berlubang {h_area:.1f} m² -> Diisi oleh #{inner_id} ({cname}) [Akan disatukan agar lubang tertutup]")
        if len(same_class_merges) > 15:
            logger.info(f"  ... dan {len(same_class_merges) - 15} lainnya.")

        # ─────────────────────────────────────────────────────────────────────
        # 2. DETEKSI CELAH KOSONG (EMPTY GAPS) PADA GRID
        # ─────────────────────────────────────────────────────────────────────
        logger.info("\n--- 2. Memeriksa Celah Kosong (Gaps) pada Grid ---")
        grid_box = box(tg.min_lon, tg.min_lat, tg.max_lon, tg.max_lat)
        
        # Buat union geometri sementara setelah simulasi merge
        temp_geoms = []
        for aid, d in parsed_dict.items():
            if aid not in absorbed_inner_ids:
                temp_geoms.append(d["geom"])
        
        union_all = unary_union(temp_geoms)
        uncovered = grid_box.difference(union_all)
        
        significant_gaps = []
        if uncovered.geom_type == "Polygon" and uncovered.area * (111320.0**2) >= 10.0:
            significant_gaps = [uncovered]
        elif hasattr(uncovered, "geoms"):
            for g in uncovered.geoms:
                if g.geom_type == "Polygon" and g.area * (111320.0**2) >= 10.0:
                    significant_gaps.append(g)

        significant_gaps.sort(key=lambda x: x.area, reverse=True)
        total_gap_area = sum(g.area * (111320.0**2) for g in significant_gaps)
        logger.info(f"Ditemukan {len(significant_gaps)} celah kosong signifikan (>= 10 m²), total area kosong: {total_gap_area:.1f} m² ({total_gap_area/1e6:.3f} km²)")
        for i, g in enumerate(significant_gaps[:10]):
            logger.info(f"  • Celah #{i+1}: {g.area * (111320.0**2):.1f} m² di koordinat ({g.centroid.x:.6f}, {g.centroid.y:.6f})")

        # ─────────────────────────────────────────────────────────────────────
        # 3. EKSEKUSI PERBAIKAN KE DATABASE (JIKA --apply)
        # ─────────────────────────────────────────────────────────────────────
        if apply_changes:
            logger.info("\n--- MEMULAI PENERAPAN PERBAIKAN KE DATABASE ---")
            
            # Step A: Buat snapshot backup
            snap = create_grid_snapshot_from_db(
                db=db,
                task_grid_id=task_grid_id,
                user_id=tg.assigned_user_id or 1,
                note="Backup Sebelum Perbaikan Poligon Bolong & Celah Kosong (Maintenance Script)"
            )
            logger.info(f"✓ Snapshot backup berhasil dibuat (Snapshot ID: {snap.id}).")

            # Step B: Eksekusi Same-Class Hole Merge
            # Kelompokkan per outer_id
            outer_to_inners = {}
            for outer_id, inner_id, _, _ in same_class_merges:
                outer_to_inners.setdefault(outer_id, []).append(inner_id)

            for outer_id, inners in outer_to_inners.items():
                outer_ann = parsed_dict[outer_id]["ann"]
                outer_geom = parsed_dict[outer_id]["geom"]
                inner_geoms = [parsed_dict[iid]["geom"] for iid in inners]

                merged_geom = unary_union([outer_geom] + inner_geoms)
                if merged_geom.geom_type == "MultiPolygon":
                    # Simpan poligon terbesar jika pecah
                    merged_geom = max(merged_geom.geoms, key=lambda x: x.area)

                outer_ann.geom_geojson = json.dumps(mapping(merged_geom))
                outer_ann.area_sqm = merged_geom.area * (111320.0 ** 2)
                parsed_dict[outer_id]["geom"] = merged_geom

                # Alihkan pin review dari poligon yang diserap ke outer_ann
                for iid in inners:
                    db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == iid).update(
                        {"annotation_id": outer_id}, synchronize_session=False
                    )

            # Hapus poligon dalam yang sudah diserap
            if absorbed_inner_ids:
                db.query(Annotation).filter(Annotation.id.in_(list(absorbed_inner_ids))).delete(synchronize_session=False)
                logger.info(f"✓ Berhasil menyatukan dan menutup {len(same_class_merges)} lubang kelas yang sama (menghapus {len(absorbed_inner_ids)} poligon ganda).")

            # Step C: Tutup Celah Kosong (Absorb Gaps to Neighbor with Longest Shared Boundary)
            if fill_gaps and significant_gaps:
                absorbed_gaps_count = 0
                for g in significant_gaps:
                    best_id = None
                    max_shared = 0.0
                    for a_id, d in parsed_dict.items():
                        if a_id in absorbed_inner_ids:
                            continue
                        poly = d["geom"]
                        if poly.intersects(g):
                            try:
                                inter = poly.intersection(g.boundary)
                                shared = inter.length
                                if shared > max_shared:
                                    max_shared = shared
                                    best_id = a_id
                            except Exception:
                                pass

                    if best_id:
                        target_ann = parsed_dict[best_id]["ann"]
                        new_geom = unary_union([parsed_dict[best_id]["geom"], g])
                        if new_geom.geom_type == "MultiPolygon":
                            new_geom = max(new_geom.geoms, key=lambda x: x.area)
                        
                        target_ann.geom_geojson = json.dumps(mapping(new_geom))
                        target_ann.area_sqm = new_geom.area * (111320.0 ** 2)
                        parsed_dict[best_id]["geom"] = new_geom
                        absorbed_gaps_count += 1

                logger.info(f"✓ Berhasil menyerap {absorbed_gaps_count} celah kosong ke poligon tetangga batas terpanjang.")

            tg.updated_at = datetime.utcnow()
            db.commit()

            remaining_count = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).count()
            logger.info(f"✓ PERBAIKAN SELESAI! Poligon aktif di Grid {tg.grid_code}: {remaining_count} poligon.")
        else:
            logger.info("\n[MODE DRY RUN]: Tidak ada perubahan yang disimpan ke database.")
            logger.info("Jalankan dengan argumen '--apply' untuk menerapkan perbaikan.")

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Perbaikan Poligon Bolong & Celah Kosong di VPS")
    parser.add_argument("--grid", type=int, default=3, help="ID Task Grid (default: 3)")
    parser.add_argument("--apply", action="store_true", help="Terapkan perbaikan ke database")
    parser.add_argument("--no-fill-gaps", action="store_true", help="Jangan serap celah kosong, hanya satukan lubang kelas sama")
    args = parser.parse_args()

    fix_grid_holes(args.grid, apply_changes=args.apply, fill_gaps=not args.no_fill_gaps)
