"""Per-grid data transfer for offline work (QGIS/ArcGIS):
export land-cover polygons as shapefile, export the Sentinel-2 raster clipped to the grid,
and import an edited shapefile back (preview first, then overwrite)."""
import json
import logging
import math
import os
import re
import shutil
import tempfile
import zipfile
from typing import Any, Dict, List, Optional

import geopandas as gpd
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from shapely import force_2d
from shapely.geometry import MultiPolygon, Polygon, box, mapping, shape
from shapely.validation import make_valid
from sqlalchemy.orm import Session

from app.api.annotations import (
    PRIVILEGED_ROLES,
    AnnotationSaveRequest,
    GeoJSONFeature,
    _require_grid_edit_access,
    save_grid_annotations,
)
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import Annotation, TaskGrid, User
from app.db.session import get_db
from app.services.snapshot_service import create_grid_snapshot_from_db, log_audit

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_RASTER_PIXELS = 4096 * 4096
SHP_PARTS = (".shp", ".shx", ".dbf", ".prj", ".cpg")
# Tolerance (deg, ~1 m) so polygons drawn exactly on the grid edge are not flagged as outside
GRID_EDGE_TOL = 1e-5


def _require_grid_read_access(db: Session, task_grid_id: int, user: User) -> TaskGrid:
    """Owner of the grid or staff. Unlike edit access, SUBMITTED/APPROVED grids stay downloadable."""
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")
    role = (user.role or "").strip().lower()
    if role not in PRIVILEGED_ROLES and task.assigned_user_id != user.id:
        raise HTTPException(status_code=403, detail="Grid ini bukan milik Anda.")
    return task


def _base_code(grid_code: str) -> str:
    """`SB_R00_C00_2025` -> `SB_R00_C00` (same spatial cell across years)."""
    parts = (grid_code or "").rsplit("_", 1)
    return parts[0] if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 4 else (grid_code or "")


def _classify_source(gdf: gpd.GeoDataFrame, task: TaskGrid) -> Dict[str, Any]:
    """Compares the GRID_CODE written by our export with the target grid.
    exact      same grid and year
    other_year same spatial cell, different year (allowed only when explicitly confirmed)
    other_grid a different cell (always rejected)
    unknown    no GRID_CODE column (hand-made shapefile): only the spatial check applies"""
    codes: List[str] = []
    if "GRID_CODE" in gdf.columns:
        codes = sorted({str(c).strip() for c in gdf["GRID_CODE"].dropna() if str(c).strip()})
    if not codes:
        return {"match": "unknown", "source_grid_code": None}
    if codes == [task.grid_code]:
        return {"match": "exact", "source_grid_code": task.grid_code}
    if all(_base_code(c) == _base_code(task.grid_code) for c in codes):
        return {"match": "other_year", "source_grid_code": ", ".join(codes)}
    return {"match": "other_grid", "source_grid_code": ", ".join(codes)}


def _cleanup(path: str) -> None:
    shutil.rmtree(path, ignore_errors=True)


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value or "grid").strip("_") or "grid"


# ─── SHAPEFILE EXPORT ────────────────────────────────────────────────────────

@router.get("/grid/{task_grid_id}/export/shp")
def export_grid_shapefile(
    task_grid_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    task = _require_grid_read_access(db, task_grid_id, current_user)
    anns = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).order_by(Annotation.id).all()
    if not anns:
        raise HTTPException(status_code=404, detail="Grid ini belum memiliki poligon untuk diunduh.")

    authors = {u.id: u.full_name for u in db.query(User).filter(User.id.in_({a.user_id for a in anns})).all()}
    records: List[Dict[str, Any]] = []
    geoms: List[Polygon] = []
    for a in anns:
        try:
            g = shape(json.loads(a.geom_geojson))
        except Exception:
            continue
        if g.is_empty:
            continue
        parts = list(g.geoms) if isinstance(g, MultiPolygon) else [g]
        for idx, part in enumerate(p for p in parts if isinstance(p, Polygon) and not p.is_empty):
            records.append({
                "ID": int(a.id) if idx == 0 else 0,  # extra parts of a legacy multipart get ID 0 (new on import)
                "KODE_PL": int(a.class_id),
                "NAMA_PL": str(a.class_name or "")[:50],
                "GRID_CODE": str(task.grid_code or "")[:20],
                "TAHUN": int(task.year or 0),
                "STATUS": str(task.status or "")[:20],
                "MAPPER": str(authors.get(a.user_id) or "")[:50],
                "LUAS_HA": round((a.area_sqm or 0) / 10000.0, 4),
            })
            geoms.append(part)
    if not records:
        raise HTTPException(status_code=400, detail="Tidak ada geometri valid yang dapat diekspor.")

    base = f"{_safe_name(task.grid_code)}_{task.year}_penutupan_lahan"
    temp_dir = tempfile.mkdtemp(prefix="grid_shp_")
    try:
        gpd.GeoDataFrame(records, geometry=geoms, crs="EPSG:4326").to_file(
            os.path.join(temp_dir, f"{base}.shp"), driver="ESRI Shapefile", encoding="utf-8"
        )
        zip_path = os.path.join(temp_dir, f"{base}_shp.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for ext in SHP_PARTS:
                p = os.path.join(temp_dir, base + ext)
                if os.path.exists(p):
                    zf.write(p, arcname=base + ext)
    except Exception as e:
        _cleanup(temp_dir)
        logger.exception("Grid shapefile export failed")
        raise HTTPException(status_code=500, detail=f"Gagal membuat Shapefile: {e}")

    log_audit(db=db, user_id=current_user.id, action="EXPORT_SHP", entity_type="task_grid",
              entity_id=task_grid_id, task_grid_id=task_grid_id)
    background_tasks.add_task(_cleanup, temp_dir)
    return FileResponse(zip_path, filename=f"{base}_shp.zip", media_type="application/zip")


# ─── RASTER (SENTINEL-2 COG) EXPORT ──────────────────────────────────────────

@router.get("/grid/{task_grid_id}/export/raster")
def export_grid_raster(
    task_grid_id: int,
    background_tasks: BackgroundTasks,
    year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Sentinel-2 raster clipped to the grid bounding box, returned as a Cloud Optimized GeoTIFF."""
    import rasterio
    import rasterio.shutil
    from rasterio.enums import Resampling
    from rasterio.warp import transform_bounds
    from rasterio.windows import Window, from_bounds

    from app.api.raster import get_year_raster_index

    task = _require_grid_read_access(db, task_grid_id, current_user)
    target_year = year or task.year
    match = next((i for i in get_year_raster_index(target_year) if i["tile_key"] == task.tile_key), None)
    if not match or not os.path.exists(match["path"]):
        raise HTTPException(status_code=404, detail=f"Citra tahun {target_year} tidak tersedia untuk grid ini.")

    base = f"{_safe_name(task.grid_code)}_{target_year}_sentinel2"
    temp_dir = tempfile.mkdtemp(prefix="grid_raster_")
    try:
        with rasterio.open(match["path"]) as src:
            left, bottom, right, top = transform_bounds(
                "EPSG:4326", src.crs, task.min_lon, task.min_lat, task.max_lon, task.max_lat, densify_pts=21
            )
            win = from_bounds(left, bottom, right, top, transform=src.transform)
            win = win.round_offsets().round_lengths().intersection(Window(0, 0, src.width, src.height))
            if win.width < 1 or win.height < 1:
                raise HTTPException(status_code=404, detail="Grid ini berada di luar cakupan citra.")
            if win.width * win.height > MAX_RASTER_PIXELS:
                raise HTTPException(status_code=413, detail="Area grid terlalu besar untuk diunduh sebagai satu berkas.")

            data = src.read(window=win)
            profile = src.profile.copy()
            profile.update(
                driver="GTiff", height=int(win.height), width=int(win.width),
                transform=src.window_transform(win), tiled=True, blockxsize=256, blockysize=256, compress="deflate",
            )
            tmp_tif = os.path.join(temp_dir, "clip.tif")
            with rasterio.open(tmp_tif, "w", **profile) as dst:
                dst.write(data)
                dst.build_overviews([2, 4, 8], Resampling.average)

        out_path = os.path.join(temp_dir, f"{base}.tif")
        try:
            rasterio.shutil.copy(tmp_tif, out_path, driver="COG", compress="DEFLATE")
        except Exception:
            logger.warning("COG driver unavailable, serving tiled GeoTIFF with overviews instead")
            os.replace(tmp_tif, out_path)
    except HTTPException:
        _cleanup(temp_dir)
        raise
    except Exception as e:
        _cleanup(temp_dir)
        logger.exception("Grid raster export failed")
        raise HTTPException(status_code=500, detail=f"Gagal memotong citra: {e}")

    log_audit(db=db, user_id=current_user.id, action="EXPORT_RASTER", entity_type="task_grid",
              entity_id=task_grid_id, task_grid_id=task_grid_id)
    background_tasks.add_task(_cleanup, temp_dir)
    return FileResponse(out_path, filename=f"{base}.tif", media_type="image/tiff")


# ─── SHAPEFILE IMPORT (overwrite) ────────────────────────────────────────────

def _problem(status: int, code: str, message: str, solution: str) -> HTTPException:
    """Blocking error: what failed (`message`) and how to fix it (`solution`), rendered by the frontend."""
    return HTTPException(status_code=status, detail={"code": code, "message": message, "solution": solution})


def _warn(code: str, message: str, solution: str) -> Dict[str, str]:
    """Non-blocking finding shown in the preview."""
    return {"code": code, "message": message, "solution": solution}


UNSUPPORTED_FORMATS = (".gdb", ".gpkg", ".geojson", ".json", ".kml", ".kmz")


def _read_uploaded_shapefile(upload: UploadFile, temp_dir: str) -> gpd.GeoDataFrame:
    raw = upload.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise _problem(413, "FILE_TOO_LARGE", "Berkas lebih besar dari 50 MB.",
                       "Unggah hanya layer penutupan lahan grid ini (hasil unduhan dari aplikasi), bukan seluruh proyek.")
    zip_path = os.path.join(temp_dir, "upload.zip")
    with open(zip_path, "wb") as f:
        f.write(raw)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = [n for n in zf.namelist() if not n.startswith("__MACOSX")]
            lowered = [n.lower().rstrip("/") for n in names]
            shp_names = [n for n in names if n.lower().endswith(".shp")]
            if not shp_names:
                other = [n for n in lowered if n.endswith(UNSUPPORTED_FORMATS) or ".gdb/" in n]
                if other:
                    raise _problem(400, "UNSUPPORTED_FORMAT",
                                   "Zip berisi format selain Shapefile (misalnya File Geodatabase, GeoPackage, atau GeoJSON).",
                                   "Ekspor layer ke Shapefile dulu: QGIS → klik kanan layer → Export → Save Features As → ESRI Shapefile; "
                                   "ArcGIS → Export Features → format Shapefile. Lalu zip ulang.")
                raise _problem(400, "NO_SHP", "Tidak ada berkas .shp di dalam zip.",
                               "Zip harus berisi .shp, .shx, dan .dbf (disarankan juga .prj) dari satu layer.")
            if len(shp_names) > 1:
                raise _problem(400, "MULTIPLE_SHP", f"Zip berisi {len(shp_names)} berkas .shp.",
                               "Masukkan hanya satu layer (satu set .shp/.shx/.dbf/.prj) ke dalam zip.")
            stem = os.path.splitext(os.path.basename(shp_names[0]))[0]
            present = {os.path.splitext(n)[1].lower() for n in names if os.path.splitext(os.path.basename(n))[0] == stem}
            missing = [e for e in (".shx", ".dbf") if e not in present]
            if missing:
                raise _problem(400, "MISSING_PARTS", f"Berkas pendamping hilang: {', '.join(missing)}.",
                               "Shapefile terdiri dari beberapa berkas. Pilih semua berkas dengan nama yang sama "
                               f"({stem}.shp, .shx, .dbf, .prj) lalu kompres bersama.")
            # Extract by basename only (ignores paths in the zip) and only known shapefile parts
            for n in names:
                ext = os.path.splitext(n)[1].lower()
                if ext in SHP_PARTS and os.path.splitext(os.path.basename(n))[0] == stem:
                    with zf.open(n) as src_f, open(os.path.join(temp_dir, "in" + ext), "wb") as d:
                        shutil.copyfileobj(src_f, d)
    except zipfile.BadZipFile:
        raise _problem(400, "NOT_ZIP", "Berkas bukan zip yang valid.",
                       "Kompres berkas Shapefile menjadi .zip (klik kanan → Compress / Send to → Compressed folder). "
                       "Mengganti ekstensi saja tidak cukup.")
    try:
        return gpd.read_file(os.path.join(temp_dir, "in.shp"))
    except Exception as e:
        logger.warning(f"Shapefile import: unreadable file: {e}")
        raise _problem(400, "UNREADABLE", "Shapefile tidak dapat dibaca (berkas mungkin rusak atau tidak lengkap).",
                       "Ekspor ulang layer ke Shapefile dari QGIS/ArcGIS, lalu unggah kembali.")


def _prepare_import(gdf: gpd.GeoDataFrame, task: TaskGrid, existing_ids: set) -> Dict[str, Any]:
    """Validates the shapefile and converts it to save-ready features.
    Raises a structured 400 on blocking problems; returns non-blocking findings as `warnings`."""
    warnings: List[Dict[str, str]] = []
    gdf.columns = [str(c).upper() if c != "geometry" else c for c in gdf.columns]
    source = _classify_source(gdf, task)
    if source["match"] == "other_grid":
        raise _problem(400, "OTHER_GRID",
                       f"Berkas ini berasal dari grid lain ({source['source_grid_code']}), bukan {task.grid_code}.",
                       "Pilih grid yang sesuai di aplikasi, atau gunakan berkas hasil unduhan dari grid ini.")
    if "KODE_PL" not in gdf.columns:
        raise _problem(400, "NO_KODE_PL", "Kolom KODE_PL (kode kelas penutupan lahan) tidak ditemukan.",
                       "Tambahkan kolom angka bernama KODE_PL dan isi kode kelasnya, atau edit berkas hasil unduhan "
                       "aplikasi tanpa menghapus kolom tersebut.")

    if gdf.crs is None:
        warnings.append(_warn("NO_PRJ", "Berkas tidak memiliki .prj; sistem koordinat diasumsikan WGS84 (EPSG:4326).",
                              "Jika poligon tampak bergeser atau hilang, ekspor ulang dengan menyertakan berkas .prj."))
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    classes = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}
    grid_box = box(task.min_lon, task.min_lat, task.max_lon, task.max_lat)
    clip_box = grid_box.buffer(GRID_EDGE_TOL)

    features: List[GeoJSONFeature] = []
    used_ids: set = set()
    bad_class_rows: List[int] = []
    skipped_empty = skipped_outside = skipped_non_polygon = clipped = null_class = 0

    for row_no, (_, row) in enumerate(gdf.iterrows(), start=1):
        geom = row.geometry
        if geom is None or geom.is_empty:
            skipped_empty += 1
            continue
        geom = force_2d(geom)  # ArcGIS may write PolygonZ/M; the app stores 2D only
        raw_class = row["KODE_PL"]
        if raw_class is None or (isinstance(raw_class, float) and math.isnan(raw_class)):
            class_id = 0  # new polygon without a class: keep it as "Belum Teridentifikasi"
            null_class += 1
        else:
            try:
                class_id = int(float(raw_class))
            except (TypeError, ValueError):
                class_id = None
        if class_id not in classes:
            bad_class_rows.append(row_no)
            continue
        if not geom.is_valid:
            geom = make_valid(geom)
        if not geom.intersects(clip_box):
            skipped_outside += 1
            continue
        if not clip_box.contains(geom):
            geom = geom.intersection(grid_box)
            clipped += 1
        parts = [g for g in getattr(geom, "geoms", [geom]) if isinstance(g, (Polygon, MultiPolygon)) and not g.is_empty]
        if not parts:
            skipped_non_polygon += 1
            continue
        polys: List[Polygon] = []
        for g in parts:
            polys.extend(g.geoms if isinstance(g, MultiPolygon) else [g])

        try:
            raw_id = int(float(row["ID"])) if "ID" in gdf.columns else None
        except (TypeError, ValueError):
            raw_id = None
        for poly in polys:
            # Keep the DB id (so review pins stay attached) only for the first part and only if it belongs to this grid
            keep_id = raw_id if raw_id in existing_ids and raw_id not in used_ids else None
            if keep_id is not None:
                used_ids.add(keep_id)
            features.append(GeoJSONFeature(
                id=keep_id,
                geometry=mapping(poly),
                properties={"class_id": class_id, "class_name": classes[class_id]},
            ))

    if bad_class_rows:
        shown = ", ".join(map(str, bad_class_rows[:10])) + ("…" if len(bad_class_rows) > 10 else "")
        valid_codes = ", ".join(f"{cid} = {name}" for cid, name in sorted(classes.items()))
        raise _problem(400, "BAD_CLASS",
                       f"KODE_PL tidak dikenal atau bukan angka pada {len(bad_class_rows)} baris (baris ke-{shown}).",
                       f"Perbaiki nilai KODE_PL pada baris tersebut. Kode yang valid: {valid_codes}.")
    if not features:
        raise _problem(400, "NO_POLYGONS", "Tidak ada poligon yang dapat diimpor di dalam batas grid.",
                       "Pastikan layer bertipe Polygon (bukan titik/garis), berisi data, dan berada di area grid ini.")
    considered = len(features) + skipped_outside
    if skipped_outside and skipped_outside / considered > 0.5:
        raise _problem(400, "MOSTLY_OUTSIDE", "Sebagian besar poligon berada di luar batas grid ini.",
                       "Kemungkinan berkas berasal dari grid lain atau sistem koordinatnya salah. "
                       "Gunakan hasil unduhan grid ini, dan sertakan berkas .prj.")

    if source["match"] == "unknown":
        warnings.append(_warn("NO_GRID_CODE", "Berkas tidak memiliki kolom GRID_CODE; kecocokan grid hanya diperiksa dari posisi poligon.",
                              "Pastikan berkas memang dibuat untuk grid ini. Berkas hasil unduhan aplikasi selalu menyertakan kolom ini."))
    if null_class:
        warnings.append(_warn("NULL_CLASS", f"{null_class} poligon belum memiliki KODE_PL dan dijadikan kelas 0 (Belum Teridentifikasi).",
                              "Isi KODE_PL di QGIS/ArcGIS lalu unggah ulang, atau beri kelas lewat panel poligon setelah impor."))
    if clipped:
        warnings.append(_warn("CLIPPED", f"{clipped} poligon melewati batas grid dan dipotong.",
                              "Jika tidak diinginkan, rapikan batas poligon di sepanjang tepi grid sebelum mengunggah."))
    if skipped_outside:
        warnings.append(_warn("OUTSIDE_IGNORED", f"{skipped_outside} poligon berada di luar grid dan diabaikan.",
                              "Hapus poligon di luar grid dari layer, atau periksa apakah berkas berasal dari grid yang benar."))
    if skipped_non_polygon:
        warnings.append(_warn("NON_POLYGON", f"{skipped_non_polygon} objek bukan poligon (titik/garis) dan diabaikan.",
                              "Gunakan layer bertipe Polygon untuk penutupan lahan."))
    if skipped_empty:
        warnings.append(_warn("EMPTY_ROWS", f"{skipped_empty} baris tanpa geometri diabaikan.",
                              "Hapus baris kosong dari tabel atribut."))
    return {"features": features, "warnings": warnings, **source}


@router.post("/grid/{task_grid_id}/import/shp")
def import_grid_shapefile(
    task_grid_id: int,
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="True = hanya pratinjau; False = timpa poligon grid dengan isi berkas."),
    allow_other_year: bool = Query(False, description="Izinkan berkas dari tahun lain pada sel grid yang sama."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Replaces all polygons of the grid with the uploaded shapefile (zip).
    Call with dry_run=true first to preview, then dry_run=false to overwrite.
    Edit access (owner, not SUBMITTED/APPROVED) is enforced by the shared save pipeline."""
    task = _require_grid_edit_access(db, task_grid_id, current_user)
    existing_ids = {r[0] for r in db.query(Annotation.id).filter(Annotation.task_grid_id == task_grid_id).all()}

    temp_dir = tempfile.mkdtemp(prefix="grid_import_")
    try:
        gdf = _read_uploaded_shapefile(file, temp_dir)
        prepared = _prepare_import(gdf, task, existing_ids)
    finally:
        _cleanup(temp_dir)

    features: List[GeoJSONFeature] = prepared["features"]
    summary = {
        "file_polygons": len(features),
        "current_polygons": len(existing_ids),
        "kept_ids": sum(1 for f in features if f.id is not None),
        "warnings": prepared["warnings"],
        "match": prepared["match"],
        "source_grid_code": prepared["source_grid_code"],
        "target_grid_code": task.grid_code,
        "target_year": task.year,
    }
    if dry_run:
        return {"dry_run": True, **summary}
    if summary["match"] == "other_year" and not allow_other_year:
        raise _problem(409, "OTHER_YEAR",
                       f"Berkas berasal dari tahun lain ({summary['source_grid_code']}), sedangkan target adalah {task.grid_code}.",
                       "Jika memang ingin memakai poligon tahun lain sebagai dasar, centang persetujuan di pratinjau lalu timpa. "
                       "Jika tidak, pilih tahun yang sesuai.")

    if existing_ids:
        create_grid_snapshot_from_db(
            db=db, task_grid_id=task_grid_id, user_id=current_user.id, note="Sebelum impor Shapefile"
        )
    # synced_at=None: the overwrite is intentional, so the stale-tab deletion guard must not apply
    result = save_grid_annotations(
        task_grid_id, AnnotationSaveRequest(task_grid_id=task_grid_id, features=features), db, current_user
    )
    log_audit(db=db, user_id=current_user.id, action="IMPORT_SHP", entity_type="task_grid",
              entity_id=task_grid_id, task_grid_id=task_grid_id)
    return {
        "dry_run": False,
        **summary,
        "saved_count": result["count"],
        "dropped_duplicates": result.get("dropped_duplicates", 0),
    }
