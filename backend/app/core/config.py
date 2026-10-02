from pydantic_settings import BaseSettings
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load .env from backend directory or project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

class Settings(BaseSettings):
    PROJECT_NAME: str = "GEOSTEVIA (Geospatial Ecosystem Services Analytics)"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "geoai_super_secret_jwt_key_2026_landcover_unet_sample")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # Database (PostgreSQL default, with SQLite fallback)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://danangwijaya@localhost:5432/geoai_landcover"
    )
    
    # Raster Base Directory
    RASTER_BASE_DIR: str = os.getenv(
        "RASTER_BASE_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raster")
    )
    
    # Google Earth Engine
    GEE_SERVICE_ACCOUNT: str = os.getenv("GEE_SERVICE_ACCOUNT", "")
    GEE_PRIVATE_KEY_PATH: str = os.getenv("GEE_PRIVATE_KEY_PATH", "")
    GEE_PROJECT_ID: str = os.getenv("GEE_PROJECT_ID", "")
    
    # Dataset Export Directory
    EXPORT_DIR: str = os.path.join(os.getcwd(), "exports")
    PATCH_SIZE_PIXELS: int = 256
    PIXEL_RESOLUTION_METERS: float = 10.0 # Sentinel-2 10m
    
    # 12 Land Cover Classes + 2 Topological Helper Classes (0: Belum Teridentifikasi, 13: Di Luar Wilayah Sampel)
    LAND_COVER_CLASSES: List[Dict[str, Any]] = [
        {"id": 0, "name": "Belum Teridentifikasi", "color": "#9CA3AF", "description": "Kelas default base polygon / draf — harus di-assign sebelum submit"},
        {"id": 1, "name": "Hutan Lahan Kering", "color": "#006400", "description": "Kanopi pohon lebat rapat, NDVI tinggi stabil"},
        {"id": 2, "name": "Hutan Mangrove / Rawa", "color": "#2E8B57", "description": "Pesisir/rawa, NDWI/MNDWI campuran, SWIR rendah"},
        {"id": 3, "name": "Semak & Belukar", "color": "#9ACD32", "description": "Kanopi rendah/terbuka, semak transisi"},
        {"id": 4, "name": "Pertanian Lahan Kering", "color": "#FFD700", "description": "Tegalan, ladang jagung/ubi, variasi musiman"},
        {"id": 5, "name": "Tanaman Perkebunan", "color": "#808000", "description": "Sawit, kelapa, karet, pola teratur homogen"},
        {"id": 6, "name": "Bangunan & Permukiman", "color": "#FF0000", "description": "Bangunan, jalan, pemukiman, NDBI tinggi"},
        {"id": 7, "name": "Lahan Terbuka", "color": "#D2B48C", "description": "Tanah gersang, pasir, albedo tinggi, NDVI rendah"},
        {"id": 8, "name": "Pertambangan", "color": "#8B4513", "description": "Galian tambang, tailing pond, kontras tekstur tinggi"},
        {"id": 9, "name": "Tubuh Air", "color": "#0000FF", "description": "Sungai, danau, waduk, NDWI tinggi, NIR ~ 0"},
        {"id": 10, "name": "Sawah Lahan Basah", "color": "#00FFFF", "description": "Sawah beririgasi, fase genangan air & vegetasi"},
        {"id": 11, "name": "Savanna", "color": "#F0E68C", "description": "Padang rumput terbuka dengan pohon tersebar"},
        {"id": 12, "name": "Tambak Pesisir", "color": "#008B8B", "description": "Kolam ikan/udang pesisir berpematang rapi"},
        {"id": 13, "name": "Di Luar Wilayah Sampel", "color": "#4B5563", "description": "Area di luar jangkauan citra / batas wilayah sampel (no-data / nodata margin)"}
    ]

    class Config:
        case_sensitive = True

settings = Settings()
