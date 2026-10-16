"""
Script untuk mengimpor data dump PostgreSQL dari VPS ke database lokal SQLite (geoai_landcover.db).
Dapat digunakan untuk file dump pg_dump (custom format .dump) apa pun dari VPS.
"""

import os
import sys
import sqlite3
import subprocess
import time
import re

def clean_val(v, is_bool=False, is_int=False, is_float=False):
    if v == r"\N" or v == "":
        return None
    if is_bool:
        return True if v in ["t", "true", "1", "TRUE"] else False
    if is_int:
        try:
            return int(v)
        except Exception:
            return None
    if is_float:
        try:
            return float(v)
        except Exception:
            return None
    return v

def import_table(dump_path, table_name, columns, types, con):
    print(f"\n--- Mengimpor tabel: {table_name} ---")
    start_t = time.time()
    
    cmd = ["pg_restore", "-a", "-t", table_name, "-f", "-", dump_path]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    copy_started = False
    batch = []
    total_count = 0
    cur = con.cursor()
    
    placeholders = ",".join(["?"] * len(columns))
    col_names = ",".join(columns)
    sql_insert = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
    
    for line in p.stdout:
        if line.startswith(f"COPY public.{table_name}") or line.startswith(f"COPY {table_name}"):
            copy_started = True
            continue
        if copy_started:
            if line.startswith(r"\."):
                break
            raw_parts = line.rstrip("\r\n").split("\t")
            if len(raw_parts) < len(columns):
                continue
            
            row = []
            for idx, col in enumerate(columns):
                val = raw_parts[idx]
                t = types.get(col, "str")
                row.append(clean_val(val, is_bool=(t == "bool"), is_int=(t == "int"), is_float=(t == "float")))
            
            batch.append(tuple(row))
            if len(batch) >= 2000:
                cur.executemany(sql_insert, batch)
                total_count += len(batch)
                batch = []
                print(f"  Sudah diimpor {total_count} baris...", end="\r", flush=True)

    if batch:
        cur.executemany(sql_insert, batch)
        total_count += len(batch)

    try:
        p.stdout.close()
        p.stderr.close()
    except Exception:
        pass
    p.terminate()
    cur.close()
    con.commit()
    elapsed = time.time() - start_t
    print(f"✓ Tabel {table_name}: Berhasil mengimpor {total_count} baris dalam {elapsed:.2f} detik.")
    return total_count

def run_import(dump_path="backups/geoai_core.dump", db_path="geoai_landcover.db"):
    if not os.path.exists(dump_path):
        print(f"Error: File dump tidak ditemukan di {dump_path}")
        return

    print(f"=== MEMULAI IMPORT DUMP VPS KE SQLITE LOKAL ===")
    print(f"Source Dump: {dump_path}")
    print(f"Target SQLite: {db_path}")

    # Pastikan skema tabel sudah siap di SQLite
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = OFF;")
    cur.execute("PRAGMA synchronous = OFF;")
    cur.execute("PRAGMA journal_mode = MEMORY;").fetchall()
    cur.close()

    # 1. users
    users_cols = ["id", "username", "email", "full_name", "hashed_password", "role", "is_active", "created_at", "phone", "institution", "department", "nim_nip", "address", "gender"]
    users_types = {"id": "int", "is_active": "bool"}
    import_table(dump_path, "users", users_cols, users_types, con)

    # 2. study_areas
    sa_cols = ["id", "name", "description", "center_lat", "center_lon", "default_zoom", "bounds_geojson", "created_at", "priority", "difficulty"]
    sa_types = {"id": "int", "center_lat": "float", "center_lon": "float", "default_zoom": "int"}
    import_table(dump_path, "study_areas", sa_cols, sa_types, con)

    # 3. land_cover_classes
    lcc_cols = ["id", "class_id", "name", "color_hex", "description", "is_active"]
    lcc_types = {"id": "int", "class_id": "int", "is_active": "bool"}
    import_table(dump_path, "land_cover_classes", lcc_cols, lcc_types, con)

    # 4. task_grids
    tg_cols = ["id", "grid_code", "study_area_id", "year", "min_lon", "min_lat", "max_lon", "max_lat", "geom_geojson", "tile_key", "raster_file_2022", "raster_file_2025", "assigned_user_id", "status", "reviewer_notes", "created_at", "updated_at", "completed_at", "qc1_approved", "qc2_approved", "finishing_approved"]
    tg_types = {
        "id": "int", "study_area_id": "int", "year": "int",
        "min_lon": "float", "min_lat": "float", "max_lon": "float", "max_lat": "float",
        "assigned_user_id": "int", "qc1_approved": "bool", "qc2_approved": "bool", "finishing_approved": "bool"
    }
    import_table(dump_path, "task_grids", tg_cols, tg_types, con)

    # 5. annotations
    ann_cols = ["id", "task_grid_id", "user_id", "class_id", "class_name", "geom_geojson", "area_sqm", "created_at", "updated_at"]
    ann_types = {"id": "int", "task_grid_id": "int", "user_id": "int", "class_id": "int", "area_sqm": "float"}
    import_table(dump_path, "annotations", ann_cols, ann_types, con)

    # 6. task_review_pins
    trp_cols = ["id", "task_grid_id", "annotation_id", "lat", "lon", "note", "status", "reviewer_id", "resolved_by_id", "resolved_at", "created_at", "updated_at"]
    trp_types = {"id": "int", "task_grid_id": "int", "annotation_id": "int", "lat": "float", "lon": "float", "reviewer_id": "int", "resolved_by_id": "int"}
    import_table(dump_path, "task_review_pins", trp_cols, trp_types, con)

    # Pastikan indeks dibuat
    print("\n--- Membangun Indeks B-Tree Lokal ---")
    idx_cur = con.cursor()
    indexes = [
        "CREATE INDEX IF NOT EXISTS ix_annotations_task_grid_id ON annotations (task_grid_id);",
        "CREATE INDEX IF NOT EXISTS ix_annotations_user_id ON annotations (user_id);",
        "CREATE INDEX IF NOT EXISTS ix_annotations_class_id ON annotations (class_id);",
        "CREATE INDEX IF NOT EXISTS ix_task_grids_study_area_id ON task_grids (study_area_id);",
        "CREATE INDEX IF NOT EXISTS ix_task_grids_year ON task_grids (year);",
        "CREATE INDEX IF NOT EXISTS ix_task_grids_assigned_user_id ON task_grids (assigned_user_id);",
        "CREATE INDEX IF NOT EXISTS ix_task_grids_status ON task_grids (status);"
    ]
    for idx_sql in indexes:
        idx_cur.execute(idx_sql)
    idx_cur.close()
    con.commit()
    con.close()

    print("\n🎉 SELURUH DATA VPS BERHASIL DIIMPOR KE DATABASE LOKAL!")

if __name__ == "__main__":
    dump_file = sys.argv[1] if len(sys.argv) > 1 else "backups/geoai_core.dump"
    run_import(dump_file)
