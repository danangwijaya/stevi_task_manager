import os
import json
import logging
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Try importing ee
try:
    import ee
    GEE_AVAILABLE = True
except ImportError:
    GEE_AVAILABLE = False
    logger.warning("earthengine-api not installed or unavailable.")

class GEEService:
    def __init__(self):
        self.initialized = False
        self._init_gee()

    def _init_gee(self):
        if not GEE_AVAILABLE:
            return
        
        # Check environment or service account key
        sa_key_path = os.getenv("GEE_PRIVATE_KEY_PATH", "")
        sa_email = os.getenv("GEE_SERVICE_ACCOUNT", "")
        project_id = os.getenv("GEE_PROJECT_ID", "")
        
        try:
            if sa_key_path and os.path.exists(sa_key_path) and sa_email:
                credentials = ee.ServiceAccountCredentials(sa_email, sa_key_path)
                ee.Initialize(credentials, project=project_id if project_id else None)
                self.initialized = True
                logger.info("Earth Engine initialized successfully via Service Account.")
            else:
                # Try default credentials
                ee.Initialize(project=project_id if project_id else None)
                self.initialized = True
                logger.info("Earth Engine initialized via default auth.")
        except Exception as e:
            logger.warning(f"GEE Initialization failed (Mock fallback active): {e}")
            self.initialized = False

    def is_active(self) -> bool:
        return self.initialized

    def _mask_s2_clouds(self, image):
        """
        Cloud masking using S2 QA60 bitmask and SCL layer (Level-2A).
        """
        qa = image.select('QA60')
        # Bits 10 and 11 are clouds and cirrus
        cloud_bit_mask = 1 << 10
        cirrus_bit_mask = 1 << 11
        mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
        
        # If SCL band exists (Level-2A Scene Classification)
        # SCL values: 3=cloud shadow, 8=cloud med prob, 9=cloud high prob, 10=cirrus
        if 'SCL' in image.bandNames().getInfo():
            scl = image.select('SCL')
            scl_mask = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10))
            mask = mask.And(scl_mask)
            
        return image.updateMask(mask).divide(10000) # scale to 0.0-1.0

    def get_sentinel2_composite(self, aoi_geometry, year: int = 2025):
        """
        Builds cloud-free median composite from Sentinel-2 Harmonized (COPERNICUS/S2_SR_HARMONIZED).
        """
        if not self.initialized:
            return None

        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        # Filter Sentinel-2 collection
        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(aoi_geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40))
            .map(self._mask_s2_clouds)
        )

        composite = collection.median().clip(aoi_geometry)
        
        # 1. Calculate Indices
        # NDVI = (B8 - B4) / (B8 + B4)
        ndvi = composite.normalizedDifference(['B8', 'B4']).rename('NDVI')
        # MNDWI = (B3 - B11) / (B3 + B11)
        mndwi = composite.normalizedDifference(['B3', 'B11']).rename('MNDWI')
        # NDBI = (B11 - B8) / (B11 + B8)
        ndbi = composite.normalizedDifference(['B11', 'B8']).rename('NDBI')
        # NDRE = (B8 - B5) / (B8 + B5)
        ndre = composite.normalizedDifference(['B8', 'B5']).rename('NDRE')

        # 2. Phenological statistics (NDVI Mean & StdDev over time)
        ndvi_series = collection.map(lambda img: img.normalizedDifference(['B8', 'B4']).rename('ndvi_ts'))
        ndvi_mean = ndvi_series.mean().rename('NDVI_mean')
        ndvi_std = ndvi_series.reduce(ee.Reducer.stdDev()).rename('NDVI_std')
        
        # 3. GLCM Textures on NIR (B8)
        b8_int = composite.select('B8').multiply(100).toInt32()
        glcm = b8_int.glcmTexture(size=3)
        glcm_contrast = glcm.select('B8_contrast').rename('GLCM_contrast')
        glcm_diss = glcm.select('B8_diss').rename('GLCM_diss')
        glcm_homo = glcm.select('B8_idm').rename('GLCM_homo')

        # Stack all bands together (20 bands total)
        full_stack = composite.select([
            'B2', 'B3', 'B4', 'B8',         # 10m bands
            'B5', 'B6', 'B7', 'B8A', 'B11', 'B12' # 20m bands resampled
        ]).addBands([
            ndvi, mndwi, ndbi, ndre,
            ndvi_mean, ndvi_std,
            glcm_contrast, glcm_diss, glcm_homo
        ])

        return full_stack

    def get_map_tile_url(self, layer_type: str = "true_color", year: int = 2025, bbox: Optional[list] = None) -> Dict[str, Any]:
        """
        Returns XYZ Tile URL template for MapLibre / Leaflet.
        If GEE is authenticated, generates dynamic GEE composite tiles.
        Otherwise, delivers real Sentinel-2 Cloudless mosaic tiles (EOX/Copernicus).
        """
        if not self.initialized:
            # Real Sentinel-2 Cloudless Mosaic from EOX per year
            if year == 2017:
                s2_cloudless_url = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2017_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg"
            elif year == 2021:
                s2_cloudless_url = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2021_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg"
            else: # 2025 / latest
                s2_cloudless_url = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg"

            # Fallbacks
            fallbacks = {
                "true_color": s2_cloudless_url,
                "false_color_nir": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "swir": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "ndvi": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "google_sat": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
                "esri_sat": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "osm": "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            }
            return {
                "url": fallbacks.get(layer_type, s2_cloudless_url),
                "is_gee": False,
                "layer_type": layer_type,
                "year": year,
                "source_name": f"Sentinel-2 Cloudless Mosaic ({year})"
            }

        try:
            # Default AOI covers Indonesia / Sumatra / Kalimantan
            if bbox:
                aoi = ee.Geometry.Rectangle(bbox)
            else:
                aoi = ee.Geometry.Rectangle([95.0, -5.0, 120.0, 7.0])
                
            composite = self.get_sentinel2_composite(aoi, year)
            if composite is None:
                raise Exception("Unable to build composite")

            vis_params = {}
            if layer_type == "true_color":
                vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0.0, 'max': 0.3}
            elif layer_type == "false_color_nir":
                vis_params = {'bands': ['B8', 'B4', 'B3'], 'min': 0.0, 'max': 0.4}
            elif layer_type == "swir":
                vis_params = {'bands': ['B11', 'B8', 'B2'], 'min': 0.0, 'max': 0.4}
            elif layer_type == "ndvi":
                vis_params = {
                    'bands': ['NDVI'],
                    'min': -0.2,
                    'max': 0.85,
                    'palette': ['#a50026', '#d73027', '#f46d43', '#fdae61', '#fee08b', '#ffffbf', '#d9ef8b', '#a6d96a', '#66bd63', '#1a9850', '#006837']
                }
            else:
                vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0.0, 'max': 0.3}

            map_id = ee.data.getMapId({
                'image': composite,
                **vis_params
            })
            
            return {
                "url": map_id['tile_fetcher'].url_format,
                "is_gee": True,
                "layer_type": layer_type,
                "year": year
            }
        except Exception as e:
            logger.error(f"Error generating GEE Tile URL: {e}")
            return {
                "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "is_gee": False,
                "layer_type": layer_type,
                "year": year,
                "error": str(e)
            }

gee_service = GEEService()
