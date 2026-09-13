from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from app.services.gee_service import gee_service
from app.api.deps import get_current_user
from app.db.models import User

router = APIRouter()

@router.get("/status")
def get_gee_status(
    current_user: User = Depends(get_current_user)
) -> Any:
    return {
        "gee_active": gee_service.is_active(),
        "service_account": bool(gee_service.initialized),
        "supported_layers": [
            {"id": "true_color", "name": "True Color (RGB 4-3-2)", "desc": "Visual wajar alami"},
            {"id": "false_color_nir", "name": "False Color NIR (8-4-3)", "desc": "Vegetasi tampak merah menyala"},
            {"id": "swir", "name": "Agriculture SWIR (11-8-2)", "desc": "Sawah, kebun, tanah, dan tambang jelas"},
            {"id": "ndvi", "name": "NDVI Colorized", "desc": "Peta indeks kerapatan kehijauan vegetasi"}
        ],
        "available_years": [2017, 2021, 2025]
    }

@router.get("/tiles")
def get_gee_tiles(
    layer: str = Query("true_color", enum=["true_color", "false_color_nir", "swir", "ndvi", "google_sat", "esri_sat", "osm"]),
    year: int = Query(2025, enum=[2017, 2021, 2025]),
    min_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
    current_user: User = Depends(get_current_user)
) -> Any:
    bbox = None
    if all(v is not None for v in [min_lon, min_lat, max_lon, max_lat]):
        bbox = [min_lon, min_lat, max_lon, max_lat]
        
    tile_info = gee_service.get_map_tile_url(layer_type=layer, year=year, bbox=bbox)
    return tile_info
