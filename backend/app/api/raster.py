import os
import glob
import math
import io
import re
import shutil
import tempfile
import zipfile
import logging
from typing import Optional, List, Dict, Any
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, File, Form
from sqlalchemy.orm import Session
from pyproj import Transformer
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
import numpy as np
from PIL import Image

from app.core.config import settings
from app.db.session import get_db
from app.db.models import TaskGrid, StudyArea, User
from app.api.deps import get_current_active_admin

logger = logging.getLogger("raster_tile_server")
router = APIRouter()

# Coordinate transformer cache: WGS84 (EPSG:4326) -> Any native raster CRS
@lru_cache(maxsize=64)
def get_transformer_from_crs(crs_str: str) -> Transformer:
    """Cache Transformer from WGS84 EPSG:4326 to target raster CRS."""
    try:
        return Transformer.from_crs("EPSG:4326", crs_str, always_xy=True)
    except Exception as e:
        logger.warning(f"Fallback to EPSG:32747 for CRS {crs_str}: {e}")
        return Transformer.from_crs("EPSG:4326", "EPSG:32747", always_xy=True)

# Default fallback transformer
transformer_to_utm = get_transformer_from_crs("EPSG:32747")

# Pre-generate empty transparent 256x256 PNG to return instantly when out of bounds
def _make_transparent_tile() -> bytes:
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()

TRANSPARENT_TILE_BYTES = _make_transparent_tile()

# In-memory cache for raster index per year: { year: [ {"path": ..., "bounds": BoundingBox, "tile_key": ...} ] }
_raster_index_cache: Dict[int, List[Dict[str, Any]]] = {}

def get_available_years() -> List[int]:
    """Dynamically scan RASTER_BASE_DIR for available year directories e.g. Sumatera_Barat_2025, Kalimantan_2025, etc."""
    base_dir = settings.RASTER_BASE_DIR
    if not os.path.exists(base_dir):
        return [2025]
    years = []
    for entry in os.listdir(base_dir):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path):
            match = re.search(r"(\d{4})", entry)
            if match:
                years.append(int(match.group(1)))
    return sorted(list(set(years)), reverse=True) if years else [2025]

def get_year_raster_index(year: int) -> List[Dict[str, Any]]:
    """Build or retrieve in-memory spatial index for all GeoTIFFs of a given year across all project directories."""
    if year in _raster_index_cache:
        return _raster_index_cache[year]

    base_dir = settings.RASTER_BASE_DIR
    if not os.path.exists(base_dir):
        return []

    index = []
    # Scan all directories that contain the year
    for entry in os.listdir(base_dir):
        year_dir = os.path.join(base_dir, entry)
        if os.path.isdir(year_dir) and str(year) in entry:
            tif_files = glob.glob(os.path.join(year_dir, "*.tif")) + glob.glob(os.path.join(year_dir, "*.tiff"))
            for f in tif_files:
                try:
                    with rasterio.open(f) as src:
                        # Extract tile_key from filename, e.g. "0000000000-0000008192"
                        suffix = os.path.basename(f).split("_10m-")[-1].replace(".tif", "").replace(".tiff", "")
                        index.append({
                            "path": f,
                            "filename": os.path.basename(f),
                            "tile_key": suffix,
                            "bounds": src.bounds,
                            "crs": src.crs,
                            "dir_name": entry
                        })
                except Exception as e:
                    logger.warning(f"Failed to index raster {f}: {e}")

    _raster_index_cache[year] = index
    logger.info(f"Indexed {len(index)} raster files for year {year}")
    return index

def tile_to_lonlat_bounds(z: int, x: int, y: int):
    """Convert XYZ tile coordinates to WGS84 bounding box (min_lon, min_lat, max_lon, max_lat)."""
    n = 2.0 ** z
    lon_min = x / n * 360.0 - 180.0
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / n))))
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1.0 - 2.0 * (y + 1) / n))))
    return lon_min, lat_min, lon_max, lat_max

def render_tile_from_raster(
    raster_path: str,
    utm_min_x: float,
    utm_min_y: float,
    utm_max_x: float,
    utm_max_y: float,
    mode: str = "rgb",
    stretch_min: float = 150.0,
    stretch_max: float = 2600.0,
    gamma: float = 1.0
) -> Optional[bytes]:
    """Read bounding box window from COG file, stretch colors with optional gamma correction, and return PNG bytes."""
    try:
        with rasterio.open(raster_path) as src:
            b = src.bounds
            # Quick check if bounding box intersects raster extent
            if utm_max_x < b.left or utm_min_x > b.right or utm_max_y < b.bottom or utm_min_y > b.top:
                return None

            # Calculate pixel window in native raster CRS
            win = from_bounds(utm_min_x, utm_min_y, utm_max_x, utm_max_y, src.transform)

            # Band configuration:
            # 1: Blue, 2: Green, 3: Red, 4: NIR (or adapt if fewer bands)
            if src.count >= 4 and mode == "cir":
                band_indices = (4, 3, 2)
            elif src.count >= 3:
                band_indices = (3, 2, 1)
            elif src.count == 1:
                band_indices = (1, 1, 1)
            else:
                band_indices = tuple(min(i + 1, src.count) for i in range(3))

            # Read 3 bands resampled to 256x256 tile
            data = src.read(
                band_indices,
                window=win,
                boundless=True,
                fill_value=src.nodata or -32768,
                out_shape=(3, 256, 256),
                resampling=Resampling.bilinear
            )

            # Check for valid pixels
            nodata_val = src.nodata if src.nodata is not None else -32768
            valid_mask = (data[0] != nodata_val) & (data[0] > 0)

            if not np.any(valid_mask):
                return None

            # Stretch reflectance values into 0..255 with optional gamma
            span = max(stretch_max - stretch_min, 1.0)
            if gamma != 1.0 and gamma > 0:
                inv_gamma = 1.0 / gamma
                norm0 = np.clip((data[0].astype(np.float32) - stretch_min) / span, 0.0, 1.0)
                norm1 = np.clip((data[1].astype(np.float32) - stretch_min) / span, 0.0, 1.0)
                norm2 = np.clip((data[2].astype(np.float32) - stretch_min) / span, 0.0, 1.0)
                ch0 = (np.power(norm0, inv_gamma) * 255.0).astype(np.uint8)
                ch1 = (np.power(norm1, inv_gamma) * 255.0).astype(np.uint8)
                ch2 = (np.power(norm2, inv_gamma) * 255.0).astype(np.uint8)
            else:
                scale = 255.0 / span
                ch0 = np.clip((data[0].astype(np.float32) - stretch_min) * scale, 0, 255).astype(np.uint8)
                ch1 = np.clip((data[1].astype(np.float32) - stretch_min) * scale, 0, 255).astype(np.uint8)
                ch2 = np.clip((data[2].astype(np.float32) - stretch_min) * scale, 0, 255).astype(np.uint8)
            
            alpha = np.where(valid_mask, 255, 0).astype(np.uint8)

            rgba = np.dstack([ch0, ch1, ch2, alpha])
            img = Image.fromarray(rgba, "RGBA")

            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=False)
            return buf.getvalue()
    except Exception as e:
        logger.error(f"Error rendering tile from {raster_path}: {e}")
        return None

# --- API Endpoints ---

@router.get("/years")
def list_available_years():
    """Returns all available raster years found in data/raster/ (e.g. 2025, 2022, and 2018)."""
    years = get_available_years()
    return {
        "available_years": years,
        "default_year": years[0] if years else 2025
    }

@router.get("/packages")
def list_raster_packages():
    """List all stored raster COG packages per folder/year with file counts and sizes."""
    base_dir = settings.RASTER_BASE_DIR
    if not os.path.exists(base_dir):
        return []
    packages = []
    for entry in sorted(os.listdir(base_dir)):
        p = os.path.join(base_dir, entry)
        if os.path.isdir(p) and not entry.startswith("."):
            tifs = glob.glob(os.path.join(p, "*.tif")) + glob.glob(os.path.join(p, "*.tiff"))
            if tifs:
                total_bytes = sum(os.path.getsize(f) for f in tifs)
                match = re.search(r"(\d{4})", entry)
                yr = int(match.group(1)) if match else None
                packages.append({
                    "folder_name": entry,
                    "year": yr,
                    "files_count": len(tifs),
                    "total_size_mb": round(total_bytes / (1024 * 1024), 2),
                    "path": p
                })
    return packages

@router.get("/info/{grid_code}")
def get_grid_raster_info(grid_code: str, db: Session = Depends(get_db)):
    """Returns raster metadata and available years for a specific grid."""
    grid = db.query(TaskGrid).filter(TaskGrid.grid_code == grid_code).first()
    if not grid:
        raise HTTPException(status_code=404, detail="Grid not found")

    available_years = []
    years = get_available_years()
    for yr in years:
        year_index = get_year_raster_index(yr)
        match = next((item for item in year_index if item["tile_key"] == grid.tile_key), None)
        if match:
            available_years.append(yr)

    return {
        "grid_code": grid.grid_code,
        "tile_key": grid.tile_key,
        "available_years": available_years,
        "default_year": available_years[0] if available_years else 2025,
        "bounds": {
            "min_lon": grid.min_lon,
            "min_lat": grid.min_lat,
            "max_lon": grid.max_lon,
            "max_lat": grid.max_lat
        },
        "resolution_meters": 10.0,
        "bands": ["Blue (B2)", "Green (B3)", "Red (B4)", "NIR (B8)"]
    }

@router.get("/tiles/{year}/{grid_code}/{z}/{x}/{y}.png")
def get_grid_tile(
    year: int,
    grid_code: str,
    z: int,
    x: int,
    y: int,
    mode: str = Query("rgb", pattern="^(rgb|cir)$"),
    stretch_min: float = Query(150.0),
    stretch_max: float = Query(2600.0),
    gamma: float = Query(1.0),
    db: Session = Depends(get_db)
):
    """
    Serves a 256x256 PNG tile for a specific grid code and year.
    Fast dynamic reading directly from the tiled COG file with dynamic CRS support.
    """
    grid = db.query(TaskGrid).filter(TaskGrid.grid_code == grid_code).first()
    if not grid:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    year_index = get_year_raster_index(year)
    match = next((item for item in year_index if item["tile_key"] == grid.tile_key), None)

    if not match:
        # Fallback check inside Sumatera_Barat_{year}
        base_dir = settings.RASTER_BASE_DIR
        for entry in os.listdir(base_dir):
            if str(year) in entry:
                cand = os.path.join(base_dir, entry, f"sentinel2_sumbar_{year}_10m-{grid.tile_key}.tif")
                if os.path.exists(cand):
                    try:
                        with rasterio.open(cand) as src:
                            match = {"path": cand, "crs": src.crs}
                    except Exception:
                        pass
                    break

    if not match:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    raster_path = match["path"]
    crs_str = str(match["crs"]) if match.get("crs") else "EPSG:32747"
    trans = get_transformer_from_crs(crs_str)

    # Compute tile bounds in native raster CRS
    lon_min, lat_min, lon_max, lat_max = tile_to_lonlat_bounds(z, x, y)
    native_min_x, native_min_y = trans.transform(lon_min, lat_min)
    native_max_x, native_max_y = trans.transform(lon_max, lat_max)

    tile_bytes = render_tile_from_raster(
        raster_path=raster_path,
        utm_min_x=native_min_x,
        utm_min_y=native_min_y,
        utm_max_x=native_max_x,
        utm_max_y=native_max_y,
        mode=mode,
        stretch_min=stretch_min,
        stretch_max=stretch_max,
        gamma=gamma
    )

    if not tile_bytes:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    return Response(
        content=tile_bytes,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400, immutable"}
    )

@router.get("/tiles/{year}/{z}/{x}/{y}.png")
def get_mosaic_tile(
    year: int,
    z: int,
    x: int,
    y: int,
    mode: str = Query("rgb", pattern="^(rgb|cir)$"),
    stretch_min: float = Query(150.0),
    stretch_max: float = Query(2600.0),
    gamma: float = Query(1.0)
):
    """
    Serves a 256x256 mosaic tile for the given year across any study area.
    Finds intersecting COG file(s) on-the-fly and streams the rendered tile with dynamic CRS.
    """
    year_index = get_year_raster_index(year)
    if not year_index:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    lon_min, lat_min, lon_max, lat_max = tile_to_lonlat_bounds(z, x, y)

    # Find candidate raster files that intersect this tile
    best_candidate = None
    best_coords = None

    for item in year_index:
        try:
            crs_str = str(item["crs"]) if item.get("crs") else "EPSG:32747"
            trans = get_transformer_from_crs(crs_str)
            t_min_x, t_min_y = trans.transform(lon_min, lat_min)
            t_max_x, t_max_y = trans.transform(lon_max, lat_max)
            b = item["bounds"]
            if not (t_max_x < b.left or t_min_x > b.right or t_max_y < b.bottom or t_min_y > b.top):
                best_candidate = item
                best_coords = (t_min_x, t_min_y, t_max_x, t_max_y)
                break
        except Exception:
            continue

    if not best_candidate:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    t_min_x, t_min_y, t_max_x, t_max_y = best_coords
    tile_bytes = render_tile_from_raster(
        raster_path=best_candidate["path"],
        utm_min_x=t_min_x,
        utm_min_y=t_min_y,
        utm_max_x=t_max_x,
        utm_max_y=t_max_y,
        mode=mode,
        stretch_min=stretch_min,
        stretch_max=stretch_max,
        gamma=gamma
    )

    if not tile_bytes:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    return Response(
        content=tile_bytes,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400, immutable"}
    )

@router.post("/upload")
async def upload_raster_zip(
    file: UploadFile = File(...),
    study_area_id: int = Form(...),
    year: int = Form(...),
    mode: str = Form("append"), # "append" or "replace"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """
    Upload and extract a .zip file containing COG raster GeoTIFF (.tif/.tiff) imagery
    for a specific study area and year.
    Validates GeoTIFFs, indexes metadata, and puts them into RASTER_BASE_DIR.
    """
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="File yang diunggah harus berekstensi .zip yang berisi file citra raster GeoTIFF (.tif / .tiff)"
        )

    study_area = db.query(StudyArea).filter(StudyArea.id == study_area_id).first()
    if not study_area:
        raise HTTPException(status_code=404, detail="Proyek / Wilayah kajian tidak ditemukan")

    clean_area = re.sub(r'[^a-zA-Z0-9]+', '_', study_area.name).strip('_')
    target_folder_name = f"{clean_area}_{year}"
    dest_dir = os.path.join(settings.RASTER_BASE_DIR, target_folder_name)
    os.makedirs(dest_dir, exist_ok=True)

    # Save uploaded zip to temp file
    temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(temp_zip_fd)

    temp_extract_dir = tempfile.mkdtemp(prefix="raster_cog_")

    try:
        # Write uploaded zip in chunks
        with open(temp_zip_path, "wb") as f_out:
            while chunk := await file.read(1024 * 1024 * 4): # 4MB chunks
                f_out.write(chunk)

        try:
            with zipfile.ZipFile(temp_zip_path, 'r') as zf:
                zf.extractall(temp_extract_dir)
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="File .zip rusak atau tidak dapat diekstrak")

        # Discover all .tif / .tiff files
        valid_tifs = []
        for root, _, files in os.walk(temp_extract_dir):
            if "__MACOSX" in root:
                continue
            for f in files:
                if f.startswith("."):
                    continue
                if f.lower().endswith((".tif", ".tiff")):
                    valid_tifs.append(os.path.join(root, f))

        if not valid_tifs:
            raise HTTPException(
                status_code=400,
                detail="File .zip tidak memuat file citra GeoTIFF (.tif atau .tiff). Pastikan arsip zip berisi file raster COG."
            )

        # If mode == 'replace', clean existing tif files in dest_dir
        if mode == "replace":
            for existing_f in glob.glob(os.path.join(dest_dir, "*.tif*")):
                try:
                    os.remove(existing_f)
                except Exception as e:
                    logger.warning(f"Failed to remove old raster file {existing_f}: {e}")

        # Validate with rasterio and copy into dest_dir
        extracted_info = []
        total_size_bytes = 0
        detected_crs = set()

        for tif_path in valid_tifs:
            base_fname = os.path.basename(tif_path)
            try:
                with rasterio.open(tif_path) as src:
                    crs_name = src.crs.to_string() if src.crs else "Unknown"
                    detected_crs.add(crs_name)
                    extracted_info.append({
                        "filename": base_fname,
                        "crs": crs_name,
                        "width": src.width,
                        "height": src.height,
                        "bands": src.count,
                        "size_bytes": os.path.getsize(tif_path)
                    })
                    total_size_bytes += os.path.getsize(tif_path)
            except Exception as e:
                logger.warning(f"File {base_fname} bukan format GeoTIFF yang valid: {e}")
                continue

            target_path = os.path.join(dest_dir, base_fname)
            shutil.copy2(tif_path, target_path)

            # Check if auxiliary XML file exists
            aux_xml = tif_path + ".aux.xml"
            if os.path.exists(aux_xml):
                shutil.copy2(aux_xml, target_path + ".aux.xml")

        if not extracted_info:
            raise HTTPException(
                status_code=400,
                detail="Tidak ada file GeoTIFF yang valid terbaca dari arsip .zip yang diunggah"
            )

        # Clear cache to force index refresh
        _raster_index_cache.clear()

        # Check matched grids for this study area and year
        matched_grids_count = db.query(TaskGrid).filter(
            TaskGrid.study_area_id == study_area.id,
            TaskGrid.year == year
        ).count()

        total_size_mb = round(total_size_bytes / (1024 * 1024), 2)
        crs_str = ", ".join(detected_crs) if detected_crs else "WGS84 / UTM"

        return {
            "success": True,
            "message": f"Berhasil mengunggah dan mengekstrak {len(extracted_info)} file citra raster COG ({total_size_mb} MB) untuk {study_area.name} (Tahun {year})",
            "study_area_id": study_area.id,
            "study_area_name": study_area.name,
            "year": year,
            "target_folder": target_folder_name,
            "mode": mode,
            "files_count": len(extracted_info),
            "total_size_mb": total_size_mb,
            "crs_detected": crs_str,
            "matched_tasks_count": matched_grids_count,
            "sample_files": [item["filename"] for item in extracted_info[:5]]
        }

    finally:
        if os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except Exception:
                pass
        if os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            except Exception:
                pass
