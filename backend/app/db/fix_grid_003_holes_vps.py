"""
Script Perbaikan Poligon Bolong & Celah Kosong di Grid 003_2025 (Rizky)
Serta Grid Lainnya di VPS.

Fitur:
1. Menutup bolongan poligon yang di dalamnya terdapat poligon dari kelas yang sama (Same-Class Hole Dissolve).
2. Menghilangkan overlap tumpang tindih antara poligon background besar dengan poligon-poligon detail di atasnya (Background Subtraction).
3. Menutup seluruh celah kosong (gaps) yang bolong / belum tercakup poligon dengan menyatukannya ke poligon tetangga batas terpanjang secara cepat & efisien.
4. Otomatis membuat snapshot cadangan (backup) sebelum melakukan modifikasi.

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
from collections import defaultdict
from shapely.geometry import shape, mapping, Polygon, box, MultiPolygon
from shapely.ops import unary_union
from shapely.strtree import STRtree
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

        # Gunakan batas polygon asli dari geom_geojson jika ada, atau fallback ke bounding box
        if tg.geom_geojson:
            grid_boundary = shape(json.loads(tg.geom_geojson))
            if not grid_boundary.is_valid:
                grid_boundary = grid_boundary.buffer(0)
            logger.info(f"Batas Grid menggunakan geom_geojson asli (Area: {grid_boundary.area * (111320.0**2)/1e6:.2f} km²)")
        else:
            grid_boundary = box(tg.min_lon, tg.min_lat, tg.max_lon, tg.max_lat)
            logger.info(f"Batas Grid menggunakan bounding box (Area: {grid_boundary.area * (111320.0**2)/1e6:.2f} km²)")

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
        same_class_merges = []  # list of (outer_id, inner_id, hole_area)
        absorbed_inner_ids = set()

        id_list = list(parsed_dict.keys())
        geoms_list = [parsed_dict[aid]["geom"] for aid in id_list]
        geom_tree = STRtree(geoms_list)

        for idx, a_id in enumerate(id_list):
            data = parsed_dict[a_id]
            g = data["geom"]
            if not hasattr(g, "interiors") or len(g.interiors) == 0:
                continue

            for h in g.interiors:
                hole_poly = Polygon(h)
                hole_area_sqm = hole_poly.area * (111320.0 ** 2)
                if hole_area_sqm < 1.0:
                    continue

                candidate_indices = geom_tree.query(hole_poly)
                for c_idx in candidate_indices:
                    o_id = id_list[c_idx]
                    if o_id == a_id or o_id in absorbed_inner_ids:
                        continue
                    o_data = parsed_dict[o_id]
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
            logger.info(f"  • Poligon #{outer_id} ({cname}) berlubang {h_area:.1f} m² -> Diisi oleh #{inner_id} ({cname}) [Disatukan]")
        if len(same_class_merges) > 15:
            logger.info(f"  ... dan {len(same_class_merges) - 15} lainnya.")

        # Simulasi merge same-class
        sim_parsed = {}
        for aid, d in parsed_dict.items():
            if aid not in absorbed_inner_ids:
                sim_parsed[aid] = {
                    "geom": d["geom"],
                    "class_id": d["class_id"],
                    "class_name": d["class_name"]
                }

        outer_to_inners = defaultdict(list)
        for outer_id, inner_id, _, _ in same_class_merges:
            outer_to_inners[outer_id].append(inner_id)

        for outer_id, inners in outer_to_inners.items():
            if outer_id in sim_parsed:
                geoms_to_merge = [sim_parsed[outer_id]["geom"]] + [parsed_dict[iid]["geom"] for iid in inners]
                m_geom = unary_union(geoms_to_merge)
                if not m_geom.is_valid:
                    m_geom = m_geom.buffer(0)
                sim_parsed[outer_id]["geom"] = m_geom

        # ─────────────────────────────────────────────────────────────────────
        # 2. SUBTRACT OVERLAPPING BACKGROUND DARI POLIGON-POLIGON DETAIL
        # ─────────────────────────────────────────────────────────────────────
        logger.info("\n--- 2. Memeriksa Subtraksi Poligon Background yang Menimpa Poligon Detail ---")
        # A. Clip any sample polygon overlapping 'Di Luar Wilayah Sampel' (#10782501)
        dlw_id = 10782501
        if dlw_id in sim_parsed:
            dlw_geom = sim_parsed[dlw_id]["geom"]
            for aid, d in sim_parsed.items():
                if aid != dlw_id and d["geom"].intersects(dlw_geom):
                    inter = d["geom"].intersection(dlw_geom)
                    if inter.area * (111320.0 ** 2) > 0.05:
                        diff = d["geom"].difference(dlw_geom)
                        if not diff.is_valid:
                            diff = diff.buffer(0)
                        d["geom"] = diff
                        logger.info(f"  • Memotong {inter.area*(111320.0**2):.1f} m² tumpang tindih dari #{aid} dengan Di Luar Wilayah Sampel")

        # B. Subtract smaller polygons from larger background polygons (area > 500,000 m²)
        large_poly_ids = sorted(
            [aid for aid, d in sim_parsed.items() if aid != dlw_id and d["geom"].area * (111320.0**2) > 500000.0],
            key=lambda x: sim_parsed[x]["geom"].area,
            reverse=True
        )
        logger.info(f"Poligon latar belakang besar (> 0.5 km²): {len(large_poly_ids)}")
        background_cut_records = {}

        for lp_id in large_poly_ids:
            lg = sim_parsed[lp_id]["geom"]
            other_geoms = [
                d["geom"] for aid, d in sim_parsed.items()
                if aid != lp_id and aid != dlw_id and aid not in large_poly_ids and d["geom"].intersects(lg)
            ]
            if other_geoms:
                u_other = unary_union(other_geoms)
                inter = lg.intersection(u_other)
                inter_sqm = inter.area * (111320.0 ** 2)
                if inter_sqm > 5.0:
                    diff_geom = lg.difference(u_other)
                    if not diff_geom.is_valid:
                        diff_geom = diff_geom.buffer(0)
                    background_cut_records[lp_id] = diff_geom
                    sim_parsed[lp_id]["geom"] = diff_geom
                    logger.info(f"  • Memotong {inter_sqm/1e6:.2f} km² ({inter_sqm:.1f} m²) tumpang tindih dari latar belakang #{lp_id} ({sim_parsed[lp_id]['class_name']})")

        # C. Pairwise clipping for remaining sliver overlaps > 0.1 m²
        id_list = list(sim_parsed.keys())
        geoms_for_tree = [sim_parsed[aid]["geom"] for aid in id_list]
        ov_tree = STRtree(geoms_for_tree)
        pairwise_clipped = 0

        for i, aid1 in enumerate(id_list):
            g1 = sim_parsed[aid1]["geom"]
            for j in ov_tree.query(g1):
                if j > i:
                    aid2 = id_list[j]
                    g2 = sim_parsed[aid2]["geom"]
                    if g1.intersects(g2):
                        inter = g1.intersection(g2)
                        inter_sqm = inter.area * (111320.0 ** 2)
                        if inter_sqm > 0.05:
                            # Clip larger by smaller
                            a1_sqm = g1.area * (111320.0 ** 2)
                            a2_sqm = g2.area * (111320.0 ** 2)
                            if a1_sqm >= a2_sqm:
                                new_g1 = g1.difference(g2)
                                if not new_g1.is_valid:
                                    new_g1 = new_g1.buffer(0)
                                sim_parsed[aid1]["geom"] = new_g1
                                g1 = new_g1
                            else:
                                new_g2 = g2.difference(g1)
                                if not new_g2.is_valid:
                                    new_g2 = new_g2.buffer(0)
                                sim_parsed[aid2]["geom"] = new_g2
                            pairwise_clipped += 1

        if pairwise_clipped > 0:
            logger.info(f"  • Berhasil merapikan {pairwise_clipped} sliver tumpang tindih antar batas poligon.")

        # ─────────────────────────────────────────────────────────────────────
        # 3. DETEKSI & ABSORPSI CELAH KOSONG (EMPTY GAPS) PADA GRID
        # ─────────────────────────────────────────────────────────────────────
        logger.info("\n--- 3. Memeriksa Celah Kosong (Gaps) pada Grid ---")
        current_geoms_list = [d["geom"] for d in sim_parsed.values()]
        union_all = unary_union(current_geoms_list)
        uncovered = grid_boundary.difference(union_all)

        gap_pieces = []
        if uncovered.geom_type == "Polygon" and uncovered.area * (111320.0**2) >= 0.01:
            gap_pieces = [uncovered]
        elif hasattr(uncovered, "geoms"):
            for g in uncovered.geoms:
                if g.geom_type in ("Polygon", "MultiPolygon") and g.area * (111320.0**2) >= 0.01:
                    gap_pieces.append(g)

        gap_pieces.sort(key=lambda x: x.area, reverse=True)
        total_gap_area = sum(g.area * (111320.0**2) for g in gap_pieces)
        logger.info(f"Ditemukan {len(gap_pieces)} celah kosong (>= 0.01 m²), total area kosong: {total_gap_area:.2f} m² ({total_gap_area/1e6:.4f} km²)")
        for i, g in enumerate(gap_pieces[:10]):
            logger.info(f"  • Celah #{i+1}: {g.area * (111320.0**2):.1f} m² di koordinat ({g.centroid.x:.6f}, {g.centroid.y:.6f})")

        # Kelompokkan gap ke poligon tetangga dengan batas perbatasan terpanjang
        gap_assignments = defaultdict(list)
        if fill_gaps and gap_pieces:
            logger.info("Mencocokkan celah kosong ke poligon tetangga dengan perbatasan terpanjang...")
            active_ids = list(sim_parsed.keys())
            active_geoms = [sim_parsed[aid]["geom"] for aid in active_ids]
            active_tree = STRtree(active_geoms)

            for g in gap_pieces:
                cand_indices = active_tree.query(g)
                best_aid = None
                max_shared = 0.0
                g_boundary = g.boundary
                for c_idx in cand_indices:
                    poly = active_geoms[c_idx]
                    if poly.intersects(g):
                        try:
                            shared_len = poly.intersection(g_boundary).length
                            if shared_len > max_shared:
                                max_shared = shared_len
                                best_aid = active_ids[c_idx]
                        except Exception:
                            pass
                if best_aid:
                    gap_assignments[best_aid].append(g)

            logger.info(f"Celah kosong berhasil dialokasikan ke {len(gap_assignments)} poligon tetangga.")

        # ─────────────────────────────────────────────────────────────────────
        # 4. EKSEKUSI PENERAPAN PERBAIKAN KE DATABASE (JIKA --apply)
        # ─────────────────────────────────────────────────────────────────────
        if apply_changes:
            logger.info("\n--- MEMULAI PENERAPAN PERBAIKAN KE DATABASE ---")

            # Step A: Buat snapshot backup otomatis
            snap = create_grid_snapshot_from_db(
                db=db,
                task_grid_id=task_grid_id,
                user_id=tg.assigned_user_id or 1,
                note="Backup Sebelum Perbaikan Poligon Bolong & Celah Kosong (Maintenance Script)"
            )
            logger.info(f"✓ Snapshot backup berhasil dibuat (Snapshot ID: {snap.id}, Versi: v{snap.version_number}).")

            # Step B: Alihkan pin review dari poligon yang diserap ke outer_id
            for outer_id, inners in outer_to_inners.items():
                for iid in inners:
                    db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == iid).update(
                        {"annotation_id": outer_id}, synchronize_session=False
                    )

            if absorbed_inner_ids:
                for iid in absorbed_inner_ids:
                    if iid in parsed_dict and parsed_dict[iid].get("ann"):
                        db.delete(parsed_dict[iid]["ann"])
                logger.info(f"✓ Berhasil menyatukan dan menutup {len(same_class_merges)} lubang kelas yang sama (menghapus {len(absorbed_inner_ids)} poligon inner ganda).")

            # Step C: Absorpsi Celah Kosong ke sim_parsed
            if fill_gaps and gap_assignments:
                for target_id, g_list in gap_assignments.items():
                    if target_id in sim_parsed:
                        cur_g = sim_parsed[target_id]["geom"]
                        new_g = unary_union([cur_g] + g_list)
                        if not new_g.is_valid:
                            new_g = new_g.buffer(0)
                        sim_parsed[target_id]["geom"] = new_g
                logger.info(f"✓ Berhasil menyerap seluruh celah kosong ke {len(gap_assignments)} poligon tetangga.")

            # Step D: Tuliskan seluruh geometri bersih yang sudah disempurnakan ke Database
            for aid, s_data in sim_parsed.items():
                if aid in parsed_dict and parsed_dict[aid].get("ann"):
                    target_ann = parsed_dict[aid]["ann"]
                    final_g = s_data["geom"]
                    if not final_g.is_valid:
                        final_g = final_g.buffer(0)
                    if final_g.geom_type == "MultiPolygon":
                        final_g = max(final_g.geoms, key=lambda x: x.area)

                    target_ann.geom_geojson = json.dumps(mapping(final_g))
                    target_ann.area_sqm = final_g.area * (111320.0 ** 2)

            tg.updated_at = datetime.utcnow()
            db.commit()

            # Verifikasi akhir
            remaining_anns = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).all()
            final_geoms = []
            for ra in remaining_anns:
                try:
                    fg = shape(json.loads(ra.geom_geojson))
                    if not fg.is_valid:
                        fg = fg.buffer(0)
                    final_geoms.append(fg)
                except Exception:
                    pass

            final_union = unary_union(final_geoms)
            final_uncovered = grid_boundary.difference(final_union)
            final_uncovered_sqm = final_uncovered.area * (111320.0 ** 2)
            final_cov = (final_union.intersection(grid_boundary).area / grid_boundary.area) * 100.0

            logger.info(f"\n=======================================================")
            logger.info(f"✓ PERBAIKAN SELESAI PADA GRID {tg.grid_code} (ID: {task_grid_id})!")
            logger.info(f"✓ Jumlah poligon aktif akhir: {len(remaining_anns)}")
            logger.info(f"✓ Coverage batas grid: {final_cov:.4f}%")
            logger.info(f"✓ Sisa celah kosong: {final_uncovered_sqm:.2f} m²")
            logger.info(f"=======================================================")
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
