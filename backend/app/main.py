from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, tasks, annotations, gee, export_dataset, arcgis, raster
from app.db.seed import seed_database
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Collaborative Web Platform for Sentinel-2 Land Cover Deep Learning U-Net Training Samples",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing GeoAI Training Sample Platform...")
    seed_database()

# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication & Users"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["Task Grids & Management"])
app.include_router(annotations.router, prefix=f"{settings.API_V1_STR}/annotations", tags=["Spatial Annotations & Classes"])
app.include_router(raster.router, prefix=f"{settings.API_V1_STR}/raster", tags=["Sentinel-2 Dynamic COG Tile Server"])
app.include_router(gee.router, prefix=f"{settings.API_V1_STR}/gee", tags=["Google Earth Engine & Satellite Layers"])
app.include_router(arcgis.router, prefix=f"{settings.API_V1_STR}/arcgis", tags=["ArcGIS Sentinel-2 L2A ImageServer"])
app.include_router(export_dataset.router, prefix=f"{settings.API_V1_STR}/export", tags=["1-Click U-Net Dataset Export"])

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }
