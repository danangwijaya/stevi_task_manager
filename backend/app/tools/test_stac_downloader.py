"""
Test script for Sentinel-2 STAC Downloader & Compositor (Optimized Windowed Reproject)
"""
import os
import sys
import math
import time
import requests
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.windows import from_bounds as win_from_bounds

def get_utm_epsg(lon: float, lat: float) -> int:
    zone = int((lon + 180) / 6) + 1
    if lat >= 0:
        return 32600 + zone
    else:
        return 32700 + zone

def read_and_reproject_band(src, target_bounds, dst_shape, dst_transform, target_crs, dtype, resampling_mode=Resampling.bilinear):
    """Read minimal window from remote COG, then reproject in-memory."""
    min_x, min_y, max_x, max_y = target_bounds
    height, width = dst_shape
    
    # 1. Transform target bounds to raster's native CRS
    src_min_x, src_min_y, src_max_x, src_max_y = transform_bounds(target_crs, src.crs, min_x, min_y, max_x, max_y)
    
    # 2. Check if bounds overlap with raster extent
    b = src.bounds
    if src_max_x < b.left or src_min_x > b.right or src_max_y < b.bottom or src_min_y > b.top:
        return np.zeros((height, width), dtype=dtype)
        
    # 3. Compute window in source pixels
    win = win_from_bounds(src_min_x, src_min_y, src_max_x, src_max_y, transform=src.transform)
    # Round window to avoid edge artifacts
    win = win.round_offsets().round_shape()
    
    # 4. Read ONLY the requested window over HTTP
    win_data = src.read(1, window=win, boundless=True, fill_value=0)
    win_transform = rasterio.windows.transform(win, src.transform)
    
    # 5. Fast in-memory reproject to target grid
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

def test_composite_patch():
    # tile000 bounds: 108.5, -3.0, 109.0, -2.5
    # Let's test a 0.15 deg x 0.15 deg patch (~1600x1600 pixels at 10m)
    west, south = 108.5, -3.0
    east, north = 108.65, -2.85
    year = 2024
    
    print(f"Testing Sentinel-2 STAC composite for bbox [{west}, {south}, {east}, {north}] (Year: {year})")
    
    # 1. Determine target UTM CRS
    center_lon = (west + east) / 2
    center_lat = (south + north) / 2
    utm_code = get_utm_epsg(center_lon, center_lat)
    target_crs = f"EPSG:{utm_code}"
    print(f"Target UTM CRS: {target_crs}")
    
    # 2. Compute target grid in UTM
    min_x, min_y, max_x, max_y = transform_bounds("EPSG:4326", target_crs, west, south, east, north)
    res = 10.0  # 10m
    min_x = math.floor(min_x / res) * res
    min_y = math.floor(min_y / res) * res
    max_x = math.ceil(max_x / res) * res
    max_y = math.ceil(max_y / res) * res
    width = int(round((max_x - min_x) / res))
    height = int(round((max_y - min_y) / res))
    dst_transform = from_bounds(min_x, min_y, max_x, max_y, width, height)
    target_bounds = (min_x, min_y, max_x, max_y)
    
    print(f"Grid dimensions: {width} x {height} ({width * height / 1e6:.2f} Mpix)")
    
    # 3. Query STAC API
    stac_url = "https://earth-search.aws.element84.com/v1/search"
    payload = {
        "collections": ["sentinel-2-l2a"],
        "bbox": [west, south, east, north],
        "datetime": f"{year}-01-01T00:00:00Z/{year}-12-31T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": 25}},
        "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}],
        "limit": 6
    }
    
    t0 = time.time()
    resp = requests.post(stac_url, json=payload, timeout=20).json()
    scenes = resp.get("features", [])
    print(f"STAC search returned {len(scenes)} scenes in {time.time()-t0:.2f}s")
    
    if not scenes:
        print("No scenes found!")
        return
        
    for s in scenes:
        print(f" - {s['id']}: Cloud={s['properties'].get('eo:cloud_cover'):.1f}%, Date={s['properties'].get('datetime')[:10]}")

    band_names = ['blue', 'green', 'red', 'nir']
    band_assets = {'blue': 'blue', 'green': 'green', 'red': 'red', 'nir': 'nir'}
    
    valid_scenes_stack = []
    
    env_config = {
        'GDAL_DISABLE_READDIR_ON_OPEN': 'EMPTY_DIR',
        'CPL_VSIL_CURL_ALLOWED_EXTENSIONS': '.tif',
        'VSI_CACHE': True,
        'VSI_CACHE_SIZE': 50000000,
        'GDAL_HTTP_MERGE_CONSECUTIVE_RANGES': 'YES',
        'GDAL_HTTP_MULTIPLEX': 'YES',
        'GDAL_HTTP_VERSION': '2'
    }
    
    with rasterio.Env(**env_config):
        for idx, scene in enumerate(scenes):
            s_id = scene['id']
            print(f"\nProcessing scene [{idx+1}/{len(scenes)}]: {s_id}")
            t_s = time.time()
            
            # Read SCL window first
            scl_href = scene['assets']['scl']['href']
            with rasterio.open(scl_href) as scl_src:
                scl_data = read_and_reproject_band(
                    scl_src, target_bounds, (height, width), dst_transform, target_crs,
                    dtype=np.uint8, resampling_mode=Resampling.nearest
                )
            
            # SCL valid mask:
            # 2: dark area, 4: vegetation, 5: bare soil, 6: water, 7: unclassified
            valid_mask = np.isin(scl_data, [2, 4, 5, 6, 7])
            valid_pct = np.count_nonzero(valid_mask) / (width * height) * 100
            print(f"  Valid pixels in ROI from SCL: {valid_pct:.1f}%")
            
            if valid_pct < 5.0:
                print("  Skipping scene (insufficient coverage or too cloudy)")
                continue
                
            # Read 4 bands
            scene_bands = []
            for b_name in band_names:
                href = scene['assets'][band_assets[b_name]]['href']
                with rasterio.open(href) as b_src:
                    b_data = read_and_reproject_band(
                        b_src, target_bounds, (height, width), dst_transform, target_crs,
                        dtype=np.uint16, resampling_mode=Resampling.bilinear
                    )
                    b_data[~valid_mask] = 0
                    scene_bands.append(b_data)
            
            valid_scenes_stack.append(np.stack(scene_bands, axis=0))
            print(f"  Scene fetched, warped & masked in {time.time()-t_s:.2f}s")
            
            if len(valid_scenes_stack) >= 4:
                print("  Reached target 4 clean scenes. Proceeding to composite.")
                break
    
    if not valid_scenes_stack:
        print("No valid scene data accumulated!")
        return

    # 5. Compute median composite across scenes
    print(f"\nComputing median composite across {len(valid_scenes_stack)} scenes...")
    t_comp = time.time()
    stack = np.stack(valid_scenes_stack, axis=0).astype(np.float32)
    stack[stack == 0] = np.nan
    
    with np.errstate(all='ignore'):
        composite = np.nanmedian(stack, axis=0)
        
    composite = np.nan_to_num(composite, nan=0.0).astype(np.int16)
    print(f"Composite computed in {time.time()-t_comp:.2f}s. Shape: {composite.shape}")
    
    # 6. Save as COG
    out_dir = "backend/data/raster/Test_Kalimantan_2024"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "sentinel2_kalimantan_2024_10m-test_patch.tif")
    
    print(f"\nWriting Cloud-Optimized GeoTIFF (COG) to: {out_file}")
    t_w = time.time()
    
    cog_profile = {
        'driver': 'COG',
        'dtype': 'int16',
        'nodata': 0,
        'width': width,
        'height': height,
        'count': 4,
        'crs': target_crs,
        'transform': dst_transform,
        'compress': 'deflate',
        'blocksize': 512,
        'overview_resampling': 'bilinear'
    }
    
    with rasterio.open(out_file, 'w', **cog_profile) as dst:
        dst.write(composite)
        dst.descriptions = ('blue', 'green', 'red', 'nir')
        
    print(f"COG written in {time.time()-t_w:.2f}s. File size: {os.path.getsize(out_file)/(1024*1024):.2f} MB")
    
    # 7. Verify COG
    with rasterio.open(out_file) as src:
        print("\n=== VERIFYING GENERATED COG ===")
        print("Driver:", src.driver)
        print("CRS:", src.crs)
        print("Shape:", src.shape)
        print("Count (bands):", src.count)
        print("Descriptions:", src.descriptions)
        print("Overviews:", [src.overviews(i) for i in range(1, 5)])
        print("Nodata:", src.nodata)
        print("Band 1 (Blue) min/max/mean:", src.read(1).min(), src.read(1).max(), f"{src.read(1)[src.read(1)>0].mean():.1f}")
        print("Band 2 (Green) min/max/mean:", src.read(2).min(), src.read(2).max(), f"{src.read(2)[src.read(2)>0].mean():.1f}")
        print("Band 3 (Red) min/max/mean:", src.read(3).min(), src.read(3).max(), f"{src.read(3)[src.read(3)>0].mean():.1f}")
        print("Band 4 (NIR) min/max/mean:", src.read(4).min(), src.read(4).max(), f"{src.read(4)[src.read(4)>0].mean():.1f}")

if __name__ == "__main__":
    test_composite_patch()
