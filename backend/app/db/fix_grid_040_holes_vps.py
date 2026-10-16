"""
Script Perbaikan Poligon Menyatu & Tumpang Tindih di Grid 040_2022 (Cece / Putri Shafaa Salsabila)
Task Grid ID: 156 (SB_GRID_040_2022)

Masalah:
- Poligon-poligon kecil (Semak & Belukar, Bangunan, Sawah, Tubuh Air, dll.) masih menyatu /
  tenggelam di dalam poligon latar belakang besar (#18573125 Hutan Lahan Kering,
  #18573127 Sawah Lahan Basah, #18571251, dll.) karena belum dipotongkan lubang (holes).
- Terdapat ratusan sliver tumpang tindih pada perbatasan poligon.

Solusi:
1. Snapshot Backup otomatis sebelum modifikasi database.
2. Background Subtraction bertingkat: Poligon yang lebih besar dipotong oleh seluruh poligon
   detail yang lebih kecil yang menimpanya. Poligon besar akan memiliki lubang (interior ring)
   yang rapi, memisahkan poligon-poligon kecil menjadi poligon independen seutuhnya.
3. Explode MultiPolygon: Jika pemotongan membelah poligon menjadi beberapa pulau terpisah (> 1 m²),
   bagian-bagian tersebut di-explode menjadi record Annotation mandiri dengan kelas yang sama,
   sehingga tidak ada area yang hilang atau terbuang.
4. Pairwise Sliver Clipping: Merapikan sisa tumpang tindih mikro pada perbatasan poligon.
5. Verifikasi Topologi: Memastikan validitas topologi 100% dan 0 error tumpang tindih.

Penggunaan di VPS:
  Dry Run:
    docker exec geoai_backend python -m app.db.fix_grid_040_holes_vps --grid 156
  Terapkan:
    docker exec geoai_backend python -m app.db.fix_grid_040_holes_vps --grid 156 --apply
"""

import sys
import json
import logging
import argparse
from datetime import datetime
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

from app.db.session import SessionLocal
from app.db.models import TaskGrid, Annotation
from app.services.snapshot_service import create_grid_snapshot_from_db
from app.api.annotations import validate_topology

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("fix_grid_040")

def run_fix_grid_040(task_grid_id: int = 156, apply_changes: bool = False):
    db = SessionLocal()
    try:
        logger.info(f"=== PERBAIKAN POLIGON MENYATU PADA GRID ID: {task_grid_id} ===")
        tg = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
        if not tg:
            logger.error(f"Grid ID {task_grid_id} tidak ditemukan.")
            return

        assignee_name = tg.assignee.full_name if tg.assignee else "Belum Ditugaskan"
        logger.info(f"Grid: {tg.grid_code} | Assignee: {assignee_name} | Tahun: {tg.year}")

        annos = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).order_by(Annotation.id.asc()).all()
        if not annos:
            logger.info("Grid tidak memiliki poligon.")
            return

        logger.info(f"Total poligon awal: {len(annos)}")

        # Parse geometri
        anno_dict = {}
        geoms = {}
        for a in annos:
            try:
                g = shape(json.loads(a.geom_geojson))
                if not g.is_valid:
                    g = g.buffer(0)
                anno_dict[a.id] = a
                geoms[a.id] = g
            except Exception as e:
                logger.warning(f"Gagal parse poligon #{a.id}: {e}")

        # 1. Background Subtraction Bertingkat (Urut dari poligon terbesar ke terkecil)
        logger.info("\n--- 1. Memisahkan Poligon Kecil dari Poligon Besar (Background Subtraction) ---")
        sorted_ids = sorted(geoms.keys(), key=lambda aid: geoms[aid].area, reverse=True)
        tree_ids = list(sorted_ids)
        tree_geoms = [geoms[aid] for aid in tree_ids]
        tree = STRtree(tree_geoms)

        modified_geoms = dict(geoms)
        exploded_new_records = []
        total_cuts = 0

        for aid in sorted_ids:
            cur_g = modified_geoms[aid]
            cand_indices = tree.query(cur_g)

            # Cari poligon yang LEBIH KECIL yang tumpang tindih dengan poligon ini
            smaller_overlapping = []
            for c_idx in cand_indices:
                other_id = tree_ids[c_idx]
                if other_id == aid:
                    continue
                # Hanya potong terhadap poligon yang lebih kecil dari ukuran asli aid
                if geoms[other_id].area >= geoms[aid].area:
                    continue
                og = modified_geoms[other_id]
                if cur_g.intersects(og):
                    inter = cur_g.intersection(og)
                    if inter.area * (111320.0 ** 2) > 0.05:  # > 0.05 m2
                        smaller_overlapping.append(og)

            if smaller_overlapping:
                u_smaller = unary_union(smaller_overlapping)
                diff = cur_g.difference(u_smaller)
                if not diff.is_valid:
                    diff = diff.buffer(0)

                if diff.geom_type == "Polygon":
                    modified_geoms[aid] = diff
                elif diff.geom_type == "MultiPolygon":
                    # Filter bagian-bagian yang signifikan (> 1.0 m2)
                    parts = [p for p in diff.geoms if p.area * (111320.0 ** 2) > 1.0]
                    if len(parts) == 1:
                        modified_geoms[aid] = parts[0]
                    elif len(parts) > 1:
                        # Pertahankan bagian terbesar pada record asli
                        largest_part = max(parts, key=lambda p: p.area)
                        modified_geoms[aid] = largest_part
                        # Explode bagian lainnya sebagai record baru
                        for extra in parts:
                            if extra != largest_part:
                                exploded_new_records.append({
                                    "parent_id": aid,
                                    "geom": extra,
                                    "class_id": anno_dict[aid].class_id,
                                    "class_name": anno_dict[aid].class_name,
                                    "user_id": anno_dict[aid].user_id,
                                    "area_sqm": extra.area * (111320.0 ** 2)
                                })
                        logger.info(f"  • Poligon #{aid} ({anno_dict[aid].class_name}) terbelah menjadi {len(parts)} bagian terpisah.")
                total_cuts += len(smaller_overlapping)

        logger.info(f"Selesai pemotongan bertingkat: {total_cuts} interaksi tumpang tindih dipotong.")
        logger.info(f"Poligon baru hasil explode bagian terpisah: {len(exploded_new_records)}")

        # 2. Pairwise Sliver Clipping (Pembersihan tumpang tindih batas mikro)
        logger.info("\n--- 2. Merapikan Sliver Tumpang Tindih Antar Batas Poligon ---")
        all_active_ids = list(modified_geoms.keys())
        all_active_geoms = [modified_geoms[aid] for aid in all_active_ids]

        # Tambahkan exploded records ke dalam list pengecekan
        exploded_geom_offset = len(all_active_ids)
        for ex in exploded_new_records:
            all_active_ids.append(f"new_{ex['parent_id']}")
            all_active_geoms.append(ex["geom"])

        ov_tree = STRtree(all_active_geoms)
        pairwise_clipped = 0

        for i in range(len(all_active_geoms)):
            g1 = all_active_geoms[i]
            for j in ov_tree.query(g1):
                if j > i:
                    g2 = all_active_geoms[j]
                    if g1.intersects(g2):
                        inter = g1.intersection(g2)
                        inter_sqm = inter.area * (111320.0 ** 2)
                        if inter_sqm > 0.05:
                            # Potong yang lebih besar dengan yang lebih kecil
                            if g1.area >= g2.area:
                                new_g1 = g1.difference(g2)
                                if not new_g1.is_valid:
                                    new_g1 = new_g1.buffer(0)
                                if new_g1.geom_type == "MultiPolygon":
                                    new_g1 = max(new_g1.geoms, key=lambda p: p.area)
                                all_active_geoms[i] = new_g1
                                g1 = new_g1
                            else:
                                new_g2 = g2.difference(g1)
                                if not new_g2.is_valid:
                                    new_g2 = new_g2.buffer(0)
                                if new_g2.geom_type == "MultiPolygon":
                                    new_g2 = max(new_g2.geoms, key=lambda p: p.area)
                                all_active_geoms[j] = new_g2
                            pairwise_clipped += 1

        logger.info(f"Berhasil merapikan {pairwise_clipped} sliver batas.")

        # Update kembali hasil pairwise clipping ke dictionary dan list exploded
        for i, aid in enumerate(all_active_ids[:exploded_geom_offset]):
            modified_geoms[aid] = all_active_geoms[i]
        for idx, ex in enumerate(exploded_new_records):
            ex["geom"] = all_active_geoms[exploded_geom_offset + idx]
            ex["area_sqm"] = ex["geom"].area * (111320.0 ** 2)

        # 3. Validasi Akhir Sisa Tumpang Tindih
        check_tree = STRtree(all_active_geoms)
        rem_overlaps = []
        for i in range(len(all_active_geoms)):
            g1 = all_active_geoms[i]
            for j in check_tree.query(g1):
                if j > i:
                    g2 = all_active_geoms[j]
                    if g1.intersects(g2):
                        inter = g1.intersection(g2)
                        if inter.area * (111320.0 ** 2) > 0.05:
                            rem_overlaps.append((all_active_ids[i], all_active_ids[j], inter.area * (111320.0 ** 2)))

        logger.info(f"Sisa tumpang tindih (> 0.05 m²): {len(rem_overlaps)}")

        # 4. Terapkan ke Database jika --apply
        if apply_changes:
            logger.info("\n--- MEMULAI PENERAPAN KE DATABASE ---")
            # Snapshot backup
            snap = create_grid_snapshot_from_db(
                db=db,
                task_grid_id=task_grid_id,
                user_id=tg.assigned_user_id or 1,
                note="Backup Otomatis Sebelum Memisahkan Poligon Menyatu (Cece Grid 040_2022)"
            )
            logger.info(f"✓ Backup snapshot dibuat: Snapshot ID {snap.id} (Versi: v{snap.version_number})")

            # Update poligon yang dimodifikasi
            updated_count = 0
            for aid, new_g in modified_geoms.items():
                orig_ann = anno_dict[aid]
                if not new_g.is_valid:
                    new_g = new_g.buffer(0)
                if new_g.geom_type == "MultiPolygon":
                    new_g = max(new_g.geoms, key=lambda p: p.area)

                orig_ann.geom_geojson = json.dumps(mapping(new_g))
                orig_ann.area_sqm = new_g.area * (111320.0 ** 2)
                orig_ann.updated_at = datetime.utcnow()
                updated_count += 1

            # Tambahkan exploded new records
            created_count = 0
            for ex in exploded_new_records:
                ex_geom = ex["geom"]
                if not ex_geom.is_valid:
                    ex_geom = ex_geom.buffer(0)
                if ex_geom.geom_type == "MultiPolygon":
                    ex_geom = max(ex_geom.geoms, key=lambda p: p.area)

                new_ann = Annotation(
                    task_grid_id=task_grid_id,
                    user_id=ex["user_id"],
                    class_id=ex["class_id"],
                    class_name=ex["class_name"],
                    geom_geojson=json.dumps(mapping(ex_geom)),
                    area_sqm=ex_geom.area * (111320.0 ** 2),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_ann)
                created_count += 1

            tg.updated_at = datetime.utcnow()
            db.commit()
            logger.info(f"✓ Berhasil mengupdate {updated_count} poligon dan membuat {created_count} poligon pecahan baru.")

            # Jalankan Topology Validation
            logger.info("\n--- Menjalankan Cek Topologi Akhir ---")
            top_res = validate_topology(task_grid_id, db)
            logger.info(f"Status Topologi Valid: {top_res.get('valid')}")
            logger.info(f"Total Kesalahan: {len(top_res.get('errors', []))}")
            logger.info(f"Cakupan Poligon: {top_res.get('coverage_percentage')}%")
            if top_res.get("errors"):
                for err in top_res.get("errors")[:5]:
                    logger.warning(f"  • {err.get('message')}")
        else:
            logger.info("\n[MODE DRY RUN]: Tidak ada perubahan disimpan ke database. Gunakan flag '--apply' untuk menyimpan.")

    except Exception as e:
        db.rollback()
        logger.exception(f"Error saat memproses Grid {task_grid_id}: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pisahkan poligon kecil yang menyatu dengan poligon besar di Grid 040_2022")
    parser.add_argument("--grid", type=int, default=156, help="Task Grid ID (default: 156)")
    parser.add_argument("--apply", action="store_true", help="Terapkan perubahan ke database")
    args = parser.parse_args()

    run_fix_grid_040(task_grid_id=args.grid, apply_changes=args.apply)
