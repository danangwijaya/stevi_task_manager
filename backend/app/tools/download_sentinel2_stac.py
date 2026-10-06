#!/usr/bin/env python3
"""
Sentinel-2 Annual Cloud-Free COG Downloader & Compositor
========================================================
Downloads Sentinel-2 L2A surface reflectance data using AWS Open Data STAC API (free, open, no auth required),
applies Scene Classification Layer (SCL) cloud/shadow masking, computes an annual median composite,
and writes directly into Cloud-Optimized GeoTIFF (COG) with pyramids and 4 bands (Blue, Green, Red, NIR).

Designed for high performance on VPS (32 Cores, 128 GB RAM) and local testing.
Compatible with backend/app/api/raster.py tile server.
"""

import os
import sys
import math
import time
import argparse
import logging
from typing import List, Tuple, Dict, Any, Optional

import requests
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.windows import from_bounds as win_from_bounds

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SentinelDownloader")

STAC_ENDPOINT = "https://earth-search.aws.element84.com/v1/search"
BAND_NAMES = ["blue", "green", "red", "nir"]
BAND_ASSET_KEYS = {"blue": "blue", "green": "green", "red": "red", "nir": "nir"}

GDAL_ENV = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
    "VSI_CACHE": True,
    "VSI_CACHE_SIZE": 100000000,
    "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
    "GDAL_HTTP_MULTIPLEX": "YES",
    "GDAL_HTTP_VERSION": "2"
}

def get_utm_epsg(lon: float, lat: float) -> int:
    """Determine EPSG code for UTM zone from longitude and latitude."""
    zone = int((lon + 180) / 6) + 1
    return 32600 + zone if lat >= 0 else 32700 + zone

def read_and_reproject_band(
    src: rasterio.DatasetReader,
    target_bounds: Tuple[float, float, float, float],
    dst_shape: Tuple[int, int],
    dst_transform: rasterio.Affine,
    target_crs: str,
    dtype: np.dtype,
    resampling_mode: Resampling = Resampling.bilinear
) -> np.ndarray:
    """Read window from remote COG over HTTP, then reproject in-memory to target UTM grid."""
    min_x, min_y, max_x, max_y = target_bounds
    height, width = dst_shape

    # 1. Transform target bounds into the source raster's native CRS
    src_min_x, src_min_y, src_max_x, src_max_y = transform_bounds(target_crs, src.crs, min_x, min_y, max_x, max_y)

    # 2. Check if window intersects with raster bounds
    b = src.bounds
    if src_max_x < b.left or src_min_x > b.right or src_max_y < b.bottom or src_min_y > b.top:
        return np.zeros((height, width), dtype=dtype)

    # 3. Compute window in source pixel coordinates
    win = win_from_bounds(src_min_x, src_min_y, src_max_x, src_max_y, transform=src.transform)

    # 4. Read ONLY that specific window from the remote S3 COG
    win_data = src.read(1, window=win, boundless=True, fill_value=0)
    win_transform = rasterio.windows.transform(win, src.transform)

    # 5. In-memory fast reprojection to target grid
    dst_data = np.zeros((height, width), dtype=dtype)
    reproject(
        source=win_data,
        destination=dst_data,
        src_transform=win_transform,
        src_crs=src.crs,
        dst_transform=dst_transform,
        dst_crs=target_crs,
        resampling=resampling_mode
    )
    return dst_data

def search_stac_scenes(
    west: float,
    south: float,
    east: float,
    north: float,
    year: int,
    max_cloud: float = 30.0,
    limit: int = 12
) -> List[Dict[str, Any]]:
    """Query AWS STAC API for Sentinel-2 L2A scenes over the bounding box in the target year."""
    payload = {
        "collections": ["sentinel-2-l2a"],
        "bbox": [west, south, east, north],
        "datetime": f"{year}-01-01T00:00:00Z/{year}-12-31T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": max_cloud}},
        "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}],
        "limit": limit
    }
    for attempt in range(3):
        try:
            resp = requests.post(STAC_ENDPOINT, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json().get("features", [])
        except Exception as e:
            logger.warning(f"STAC search attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return []

def process_tile(
    tile_id: Any,
    tile_name: str,
    west: float,
    south: float,
    east: float,
    north: float,
    year: int,
    output_dir: str,
    target_clean_scenes: int = 4,
    max_cloud_cover: float = 30.0,
    overwrite: bool = False
) -> bool:
    """Download, mask clouds, compute median composite, and save as COG for a single tile grid."""
    out_filename = f"sentinel2_kalimantan_{year}_10m-{tile_name}.tif"
    out_path = os.path.join(output_dir, out_filename)

    if os.path.exists(out_path) and not overwrite:
        logger.info(f"Tile {tile_name} already exists at {out_path} ({os.path.getsize(out_path)/(1024*1024):.1f} MB). Skipping.")
        return True

    logger.info(f"--- Processing {tile_name} (ID: {tile_id}) | Bbox: [{west:.3f}, {south:.3f}, {east:.3f}, {north:.3f}] | Year: {year} ---")

    # 1. Target UTM Coordinate Reference System
    center_lon = (west + east) / 2.0
    center_lat = (south + north) / 2.0
    target_crs = f"EPSG:{get_utm_epsg(center_lon, center_lat)}"

    # 2. Target 10m Grid Definition
    min_x, min_y, max_x, max_y = transform_bounds("EPSG:4326", target_crs, west, south, east, north)
    res = 10.0
    min_x = math.floor(min_x / res) * res
    min_y = math.floor(min_y / res) * res
    max_x = math.ceil(max_x / res) * res
    max_y = math.ceil(max_y / res) * res
    width = int(round((max_x - min_x) / res))
    height = int(round((max_y - min_y) / res))
    dst_transform = from_bounds(min_x, min_y, max_x, max_y, width, height)
    target_bounds = (min_x, min_y, max_x, max_y)

    logger.info(f"Target CRS: {target_crs} | Grid: {width} x {height} ({width*height/1e6:.2f} Mpix)")

    # 3. Find scenes from STAC
    scenes = search_stac_scenes(west, south, east, north, year, max_cloud=max_cloud_cover, limit=12)
    if not scenes:
        logger.warning(f"No scenes with <{max_cloud_cover}% clouds found for {tile_name}. Widening cloud search to 50%...")
        scenes = search_stac_scenes(west, south, east, north, year, max_cloud=50.0, limit=12)
        if not scenes:
            logger.error(f"No scenes found for {tile_name} in {year}. Skipping.")
            return False

    logger.info(f"Found {len(scenes)} candidate scenes. Downloading cleanest {target_clean_scenes} scenes...")

    # 4. Fetch & cloud-mask bands
    valid_scenes_stack = []

    with rasterio.Env(**GDAL_ENV):
        for idx, scene in enumerate(scenes):
            scene_id = scene["id"]
            cloud_pct = scene["properties"].get("eo:cloud_cover", 0.0)
            date_str = scene["properties"].get("datetime", "")[:10]

            logger.info(f"Scene [{idx+1}/{len(scenes)}]: {scene_id} ({date_str}, {cloud_pct:.1f}% clouds)")
            t0 = time.time()

            # Read SCL window
            scl_href = scene["assets"]["scl"]["href"]
            try:
                with rasterio.open(scl_href) as scl_src:
                    scl_data = read_and_reproject_band(
                        scl_src, target_bounds, (height, width), dst_transform, target_crs,
                        dtype=np.uint8, resampling_mode=Resampling.nearest
                    )
            except Exception as e:
                logger.warning(f"  Failed to read SCL for {scene_id}: {e}")
                continue

            # SCL valid mask (2: dark area, 4: vegetation, 5: bare soil, 6: water, 7: unclassified)
            valid_mask = np.isin(scl_data, [2, 4, 5, 6, 7])
            valid_pct = np.count_nonzero(valid_mask) / (width * height) * 100.0

            if valid_pct < 5.0:
                logger.info(f"  Valid pixels: {valid_pct:.1f}% (Skipping - cloudy in this tile)")
                continue

            logger.info(f"  Valid pixels: {valid_pct:.1f}%. Reading bands (Blue, Green, Red, NIR)...")

            # Read 4 bands
            scene_bands = []
            fetch_success = True
            for b_name in BAND_NAMES:
                href = scene["assets"][BAND_ASSET_KEYS[b_name]]["href"]
                try:
                    with rasterio.open(href) as b_src:
                        b_data = read_and_reproject_band(
                            b_src, target_bounds, (height, width), dst_transform, target_crs,
                            dtype=np.uint16, resampling_mode=Resampling.bilinear
                        )
                        # Zero out cloudy / shadow pixels
                        b_data[~valid_mask] = 0
                        scene_bands.append(b_data)
                except Exception as e:
                    logger.warning(f"  Failed to fetch band {b_name} for {scene_id}: {e}")
                    fetch_success = False
                    break

            if fetch_success and len(scene_bands) == 4:
                valid_scenes_stack.append(np.stack(scene_bands, axis=0))
                logger.info(f"  Scene integrated in {time.time()-t0:.1f}s. (Collected {len(valid_scenes_stack)}/{target_clean_scenes})")

            if len(valid_scenes_stack) >= target_clean_scenes:
                break

    if not valid_scenes_stack:
        logger.error(f"Failed to accumulate valid scene data for {tile_name}.")
        return False

    # 5. Nanmedian composite
    logger.info(f"Computing median composite across {len(valid_scenes_stack)} clean scenes...")
    t_comp = time.time()
    stack = np.stack(valid_scenes_stack, axis=0).astype(np.float32)
    stack[stack == 0] = np.nan

    with np.errstate(all="ignore"):
        composite = np.nanmedian(stack, axis=0)

    composite = np.nan_to_num(composite, nan=0.0).astype(np.int16)
    logger.info(f"Composite computed in {time.time()-t_comp:.2f}s.")

    # 6. Save as COG
    logger.info(f"Writing Cloud-Optimized GeoTIFF (COG) to: {out_path}")
    t_w = time.time()
    os.makedirs(output_dir, exist_ok=True)

    cog_profile = {
        "driver": "COG",
        "dtype": "int16",
        "nodata": 0,
        "width": width,
        "height": height,
        "count": 4,
        "crs": target_crs,
        "transform": dst_transform,
        "compress": "deflate",
        "blocksize": 512,
        "overview_resampling": "bilinear"
    }

    with rasterio.open(out_path, "w", **cog_profile) as dst:
        dst.write(composite)
        dst.descriptions = ("blue", "green", "red", "nir")

    file_size_mb = os.path.getsize(out_path) / (1024 * 1024)
    logger.info(f"✓ {tile_name} successfully saved ({file_size_mb:.2f} MB) in {time.time()-t_w:.2f}s!")
    return True

def main():
    parser = argparse.ArgumentParser(description="Download & composite cloud-free Sentinel-2 COG per tile.")
    parser.add_argument("--shapefile", default="backend/data/vector/download_tiles/download_tiles.shp", help="Path to grid shapefile")
    parser.add_argument("--year", type=int, default=2024, help="Target imagery year (e.g. 2024, 2023)")
    parser.add_argument("--tile", type=str, default=None, help="Specific tile name(s) e.g. tile000 or tile000,tile001")
    parser.add_argument("--limit-tiles", type=int, default=None, help="Limit number of tiles to process")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory (default: backend/data/raster/Kalimantan_<YEAR>)")
    parser.add_argument("--scenes", type=int, default=4, help="Number of clean scenes to composite per tile (default: 4)")
    parser.add_argument("--max-cloud", type=float, default=25.0, help="Initial cloud cover threshold percent (default: 25.0)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing COG files")

    args = parser.parse_args()

    if not os.path.exists(args.shapefile):
        logger.error(f"Shapefile not found: {args.shapefile}")
        sys.exit(1)

    output_dir = args.output_dir or f"backend/data/raster/Kalimantan_{args.year}"
    os.makedirs(output_dir, exist_ok=True)

    gdf = gpd.read_file(args.shapefile)
    logger.info(f"Loaded {len(gdf)} tiles from {args.shapefile}")

    if args.tile:
        requested_tiles = [t.strip() for t in args.tile.split(",")]
        gdf = gdf[gdf["tile_name"].isin(requested_tiles)]
        if gdf.empty:
            logger.error(f"No tiles matched the names: {args.tile}")
            sys.exit(1)

    if args.limit_tiles:
        gdf = gdf.iloc[:args.limit_tiles]

    logger.info(f"Beginning processing for {len(gdf)} tile(s). Output folder: {output_dir}")

    success_count = 0
    start_total = time.time()

    for idx, row in gdf.iterrows():
        t_id = row.get("tile_id", idx)
        t_name = row.get("tile_name", f"tile_{idx}")
        west, south, east, north = row["west"], row["south"], row["east"], row["north"]

        ok = process_tile(
            tile_id=t_id,
            tile_name=t_name,
            west=float(west),
            south=float(south),
            east=float(east),
            north=float(north),
            year=args.year,
            output_dir=output_dir,
            target_clean_scenes=args.scenes,
            max_cloud_cover=args.max_cloud,
            overwrite=args.overwrite
        )
        if ok:
            success_count += 1

    total_elapsed = time.time() - start_total
    logger.info(f"Done! Successfully processed {success_count}/{len(gdf)} tiles in {total_elapsed/60:.1f} minutes.")

if __name__ == "__main__":
    main()
