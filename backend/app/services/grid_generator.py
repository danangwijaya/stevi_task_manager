import json
import math
from typing import List, Dict, Any

def meters_to_lat_degrees(meters: float) -> float:
    # 1 degree lat ~ 111,320 meters
    return meters / 111320.0

def meters_to_lon_degrees(meters: float, lat: float) -> float:
    # 1 degree lon ~ 111,320 * cos(lat) meters
    rad = math.radians(lat)
    cos_lat = math.cos(rad)
    if cos_lat == 0:
        return 0
    return meters / (111320.0 * cos_lat)

def generate_spatial_grids(
    min_lon: float, 
    min_lat: float, 
    max_lon: float, 
    max_lat: float, 
    patch_size_px: int = 256, 
    pixel_res_m: float = 10.0,
    prefix: str = "SB"
) -> List[Dict[str, Any]]:
    """
    Generates a grid of exact (patch_size_px * pixel_res_m) meters per tile.
    e.g. 256 px * 10m = 2560m (2.56 km).
    """
    tile_size_m = patch_size_px * pixel_res_m
    delta_lat = meters_to_lat_degrees(tile_size_m)
    
    grids = []
    current_lat = min_lat
    row = 0
    
    while current_lat < max_lat:
        delta_lon = meters_to_lon_degrees(tile_size_m, current_lat + delta_lat / 2.0)
        current_lon = min_lon
        col = 0
        
        while current_lon < max_lon:
            top_lat = current_lat + delta_lat
            right_lon = current_lon + delta_lon
            
            grid_code = f"{prefix}_R{row:02d}_C{col:02d}"
            
            # GeoJSON Polygon geometry coordinates: [ [ [lon, lat], [lon, lat], ... ] ]
            polygon_coords = [
                [current_lon, current_lat],
                [right_lon, current_lat],
                [right_lon, top_lat],
                [current_lon, top_lat],
                [current_lon, current_lat]
            ]
            
            geom_geojson = {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            }
            
            grids.append({
                "grid_code": grid_code,
                "min_lon": current_lon,
                "min_lat": current_lat,
                "max_lon": right_lon,
                "max_lat": top_lat,
                "geom_geojson": json.dumps(geom_geojson)
            })
            
            current_lon += delta_lon
            col += 1
            
        current_lat += delta_lat
        row += 1
        
    return grids
