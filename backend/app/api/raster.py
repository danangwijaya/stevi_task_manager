import os
import glob
import math
import io
import re
import logging
from typing import Optional, List, Dict, Any
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from pyproj import Transformer
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
import numpy as np
from PIL import Image

from app.core.config import settings
from app.db.session import get_db
from app.db.models import TaskGrid

logger = logging.getLogger("raster_tile_server")
router = APIRouter()

# Coordinate transformer: WGS84 (EPSG:4326) -> UTM Zone 47S (EPSG:32747)
transformer_to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32747", always_xy=True)

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
    """Dynamically scan RASTER_BASE_DIR for available year directories e.g. Sumatera_Barat_2025, Sumatera_Barat_2022, Sumatera_Barat_2018"""
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
    """Build or retrieve in-memory spatial index for all GeoTIFFs of a given year."""
    if year in _raster_index_cache:
        return _raster_index_cache[year]

    base_dir = settings.RASTER_BASE_DIR
    year_dir = os.path.join(base_dir, f"Sumatera_Barat_{year}")
    if not os.path.exists(year_dir):
        return []

    tif_files = glob.glob(os.path.join(year_dir, "*.tif"))
    index = []
    for f in tif_files:
        try:
            with rasterio.open(f) as src:
                # Extract tile_key from filename, e.g. "0000000000-0000008192"
                suffix = os.path.basename(f).split("_10m-")[-1].replace(".tif", "")
                index.append({
                    "path": f,
                    "filename": os.path.basename(f),
                    "tile_key": suffix,
                    "bounds": src.bounds,
                    "crs": src.crs
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
    stretch_max: float = 2600.0
) -> Optional[bytes]:
    """Read bounding box window from COG file, stretch colors, and return PNG bytes."""
    try:
        with rasterio.open(raster_path) as src:
            b = src.bounds
            # Quick check if bounding box intersects raster extent
            if utm_max_x < b.left or utm_min_x > b.right or utm_max_y < b.bottom or utm_min_y > b.top:
                return None

            # Calculate pixel window in native raster CRS
            win = from_bounds(utm_min_x, utm_min_y, utm_max_x, utm_max_y, src.transform)

            # Band configuration:
            # 1: Blue, 2: Green, 3: Red, 4: NIR
            if mode == "cir": # Color Infrared (False Color: NIR, Red, Green)
                band_indices = (4, 3, 2)
            else: # Standard RGB (True Color: Red, Green, Blue)
                band_indices = (3, 2, 1)

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

            # Stretch reflectance values into 0..255
            # Clamp between stretch_min and stretch_max
            scale = 255.0 / max(stretch_max - stretch_min, 1.0)
            
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
    """Returns all available raster years found in data/raster/ (e.g. 2025, 2022, and 2018 when added)."""
    years = get_available_years()
    return {
        "available_years": years,
        "default_year": years[0] if years else 2025
    }

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
    db: Session = Depends(get_db)
):
    """
    Serves a 256x256 PNG tile for a specific grid code and year.
    Fast dynamic reading directly from the tiled COG file.
    """
    grid = db.query(TaskGrid).filter(TaskGrid.grid_code == grid_code).first()
    if not grid:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    # Locate raster file for this year & tile_key
    base_dir = settings.RASTER_BASE_DIR
    year_dir = os.path.join(base_dir, f"Sumatera_Barat_{year}")
    raster_path = os.path.join(year_dir, f"sentinel2_sumbar_{year}_10m-{grid.tile_key}.tif")

    if not os.path.exists(raster_path):
        # Fallback search inside directory
        year_index = get_year_raster_index(year)
        match = next((item for item in year_index if item["tile_key"] == grid.tile_key), None)
        if match:
            raster_path = match["path"]
        else:
            return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    # Compute tile bounds in UTM 47S
    lon_min, lat_min, lon_max, lat_max = tile_to_lonlat_bounds(z, x, y)
    utm_min_x, utm_min_y = transformer_to_utm.transform(lon_min, lat_min)
    utm_max_x, utm_max_y = transformer_to_utm.transform(lon_max, lat_max)

    tile_bytes = render_tile_from_raster(
        raster_path=raster_path,
        utm_min_x=utm_min_x,
        utm_min_y=utm_min_y,
        utm_max_x=utm_max_x,
        utm_max_y=utm_max_y,
        mode=mode,
        stretch_min=stretch_min,
        stretch_max=stretch_max
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
    stretch_max: float = Query(2600.0)
):
    """
    Serves a 256x256 mosaic tile for the entire province for the given year.
    Finds intersecting COG file(s) on-the-fly and streams the rendered tile.
    """
    year_index = get_year_raster_index(year)
    if not year_index:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    lon_min, lat_min, lon_max, lat_max = tile_to_lonlat_bounds(z, x, y)
    utm_min_x, utm_min_y = transformer_to_utm.transform(lon_min, lat_min)
    utm_max_x, utm_max_y = transformer_to_utm.transform(lon_max, lat_max)

    # Find candidate raster files that intersect this tile
    candidates = [
        item for item in year_index
        if not (utm_max_x < item["bounds"].left or utm_min_x > item["bounds"].right or
                utm_max_y < item["bounds"].bottom or utm_min_y > item["bounds"].top)
    ]

    if not candidates:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    # Render from the best candidate (first match)
    tile_bytes = render_tile_from_raster(
        raster_path=candidates[0]["path"],
        utm_min_x=utm_min_x,
        utm_min_y=utm_min_y,
        utm_max_x=utm_max_x,
        utm_max_y=utm_max_y,
        mode=mode,
        stretch_min=stretch_min,
        stretch_max=stretch_max
    )

    if not tile_bytes:
        return Response(content=TRANSPARENT_TILE_BYTES, media_type="image/png")

    return Response(
        content=tile_bytes,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400, immutable"}
    )
