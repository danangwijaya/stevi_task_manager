import os
import sys
import time
import requests
import rasterio
from rasterio.enums import Resampling
import ee
import geopandas as gpd

# 1. Initialize GEE
ee.Initialize()

output_dir = "backend/data/raster/Test_Kalimantan_2024"
os.makedirs(output_dir, exist_ok=True)
output_cog_path = os.path.join(output_dir, "sentinel2_kalimantan_2024_10m-test.tif")

print("1. Menyiapkan geometri uji coba...")
# Ambil tile000 dari shapefile
gdf = gpd.read_file("backend/data/vector/download_tiles/download_tiles.shp")
t0 = gdf.iloc[0]
print(f"   Tile ID: {t0['tile_id']} ({t0['tile_name']})")
print(f"   BBOX Asli: W={t0['west']}, S={t0['south']}, E={t0['east']}, N={t0['north']}")

# Gunakan sub-kuadran 0.15 deg (~16km x 16km) untuk uji cepat
sub_w = float(t0['west'])
sub_s = float(t0['south'])
sub_e = sub_w + 0.15
sub_n = sub_s + 0.15
roi = ee.Geometry.Rectangle([sub_w, sub_s, sub_e, sub_n])

print("2. Menjalankan filter koleksi dan masking awan Sentinel-2 L2A 2024...")
def mask_s2_clouds(img):
    # SCL: 3=cloud shadow, 8=cloud med prob, 9=cloud high prob, 10=cirrus
    scl = img.select('SCL')
    scl_mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
    qa = img.select('QA60')
    cloud_mask = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
    return img.updateMask(scl_mask.And(cloud_mask))

collection = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(roi)
    .filterDate("2024-01-01", "2024-12-31")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 50))
    .map(mask_s2_clouds)
)

print("3. Menghitung piksel median tahunan (Cloud-free median)...")
composite = (
    collection.median()
    .select(["B2", "B3", "B4", "B8"]) # Blue, Green, Red, NIR
    .toInt16()
)

print("4. Mengambil download URL dari Google Earth Engine...")
download_url = composite.getDownloadURL({
    'scale': 10,
    'crs': 'EPSG:4326',
    'region': roi,
    'format': 'GEO_TIFF'
})
print("   URL didapat! Mengunduh GeoTIFF mentah...")

raw_tif_path = os.path.join(output_dir, "raw_temp.tif")
resp = requests.get(download_url, stream=True, timeout=120)
resp.raise_for_status()
with open(raw_tif_path, "wb") as f:
    for chunk in resp.iter_content(chunk_size=1024 * 1024):
        if chunk:
            f.write(chunk)

size_mb = os.path.getsize(raw_tif_path) / (1024 * 1024)
print(f"   Download selesai! Ukuran file mentah: {size_mb:.2f} MB")

print("5. Mengonversi ke Cloud-Optimized GeoTIFF (COG) dengan piramida overviews...")
with rasterio.open(raw_tif_path) as src:
    profile = src.profile.copy()
    profile.update({
        'driver': 'COG',
        'compress': 'deflate',
        'blocksize': 512
    })
    data = src.read()
    with rasterio.open(output_cog_path, 'w', **profile) as dst:
        dst.write(data)
        dst.descriptions = ('blue', 'green', 'red', 'nir')

os.remove(raw_tif_path)

cog_size_mb = os.path.getsize(output_cog_path) / (1024 * 1024)
print(f"✅ SUKSES! File COG berhasil dibuat: {output_cog_path} ({cog_size_mb:.2f} MB)")

# Verifikasi COG hasil
with rasterio.open(output_cog_path) as test_src:
    print(f"   Jumlah Band: {test_src.count}")
    print(f"   Dimensi: {test_src.width} x {test_src.height}")
    print(f"   Keterangan Band: {test_src.descriptions}")
    print(f"   Piramida (Overviews Band 1): {test_src.overviews(1)}")
    print(f"   CRS: {test_src.crs}")
