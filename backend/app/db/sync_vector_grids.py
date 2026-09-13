import os
import json
import logging
import sqlite3
import geopandas as gpd
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.db.models import User, StudyArea, TaskGrid, Annotation, LandCoverClass, UserRole, TaskStatus
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_vector_grids")

def sync_all():
    logger.info("1. Creating database tables in PostgreSQL if not exist...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    try:
        # --- A. Migrate / Seed Land Cover Classes ---
        if db.query(LandCoverClass).count() == 0:
            logger.info("Seeding Land Cover Classes...")
            for c in settings.LAND_COVER_CLASSES:
                db.add(LandCoverClass(
                    class_id=c["id"],
                    name=c["name"],
                    color_hex=c["color"],
                    description=c["description"],
                    is_active=True
                ))
            db.commit()
            logger.info(f"Seeded {len(settings.LAND_COVER_CLASSES)} Land Cover Classes.")

        # --- B. Migrate Users from SQLite if empty ---
        if db.query(User).count() == 0:
            sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "geoai_landcover.db")
            if os.path.exists(sqlite_path):
                logger.info(f"Migrating users from existing SQLite database: {sqlite_path}...")
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, email, full_name, hashed_password, role, is_active FROM users")
                users_data = cursor.fetchall()
                for row in users_data:
                    u = User(
                        id=row[0],
                        username=row[1],
                        email=row[2],
                        full_name=row[3],
                        hashed_password=row[4],
                        role=row[5],
                        is_active=bool(row[6])
                    )
                    db.add(u)
                db.commit()
                conn.close()
                logger.info(f"Successfully migrated {len(users_data)} users to PostgreSQL.")
            else:
                from app.core.security import get_password_hash
                admin_user = User(
                    username="admin",
                    email="admin@geoai.ac.id",
                    full_name="Lead Administrator / Reviewer",
                    hashed_password=get_password_hash("admin123"),
                    role="admin",
                    is_active=True
                )
                db.add(admin_user)
                db.commit()
                logger.info("Created default admin user.")

        # --- C. Ensure Study Area ---
        study_area = db.query(StudyArea).filter(StudyArea.name == "Provinsi Sumatera Barat (Seluruh Wilayah)").first()
        if not study_area:
            logger.info("Creating Study Area for Sumatera Barat...")
            study_area = StudyArea(
                name="Provinsi Sumatera Barat (Seluruh Wilayah)",
                description="Kawasan pemetaan data latih tutupan lahan se-Sumatera Barat dari citra satelit Sentinel-2 komposit (56 grid COG).",
                center_lat=-0.750,
                center_lon=100.500,
                default_zoom=8
            )
            db.add(study_area)
            db.commit()
            db.refresh(study_area)

        # --- D. Import 56 Grids from tif_extents.shp ---
        shp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "vector", "tif_extents.shp")
        if not os.path.exists(shp_path):
            raise FileNotFoundError(f"Shapefile not found: {shp_path}")

        logger.info(f"Reading shapefile: {shp_path}...")
        gdf = gpd.read_file(shp_path)
        logger.info(f"Found {len(gdf)} features with CRS: {gdf.crs}")

        # Reproject to WGS84 (EPSG:4326)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)

        # Sort spatially (north to south, west to east) for clean grid numbering
        gdf["center_y"] = gdf.geometry.centroid.y
        gdf["center_x"] = gdf.geometry.centroid.x
        gdf = gdf.sort_values(by=["center_y", "center_x"], ascending=[False, True]).reset_index(drop=True)

        raster_2022_dir = os.path.join(settings.RASTER_BASE_DIR, "Sumatera_Barat_2022")
        raster_2025_dir = os.path.join(settings.RASTER_BASE_DIR, "Sumatera_Barat_2025")
        
        existing_grids = {g.grid_code: g for g in db.query(TaskGrid).filter(TaskGrid.study_area_id == study_area.id).all()}
        
        imported_count = 0
        updated_count = 0

        for idx, row in gdf.iterrows():
            grid_num = idx + 1
            grid_code = f"SB_GRID_{grid_num:03d}"
            
            # Extract tile key e.g. "0000000000-0000008192"
            raw_fn = row["filename"]
            suffix = raw_fn.split("_10m-")[-1].replace(".tif", "")
            tile_key = suffix
            
            # Geometry & Bounds
            bounds = row.geometry.bounds # (minx, miny, maxx, maxy)
            min_lon, min_lat, max_lon, max_lat = bounds
            
            # GeoJSON geometry
            geom_dict = row.geometry.__geo_interface__
            geom_geojson_str = json.dumps(geom_dict)
            
            # Expected filenames
            fn_2022 = f"sentinel2_sumbar_2022_10m-{tile_key}.tif"
            fn_2025 = f"sentinel2_sumbar_2025_10m-{tile_key}.tif"
            
            has_2022 = os.path.exists(os.path.join(raster_2022_dir, fn_2022))
            has_2025 = os.path.exists(os.path.join(raster_2025_dir, fn_2025))

            if grid_code in existing_grids:
                tg = existing_grids[grid_code]
                tg.min_lon = round(min_lon, 6)
                tg.min_lat = round(min_lat, 6)
                tg.max_lon = round(max_lon, 6)
                tg.max_lat = round(max_lat, 6)
                tg.geom_geojson = geom_geojson_str
                tg.tile_key = tile_key
                tg.raster_file_2022 = fn_2022 if has_2022 else None
                tg.raster_file_2025 = fn_2025 if has_2025 else None
                updated_count += 1
            else:
                tg = TaskGrid(
                    grid_code=grid_code,
                    study_area_id=study_area.id,
                    year=2025,
                    min_lon=round(min_lon, 6),
                    min_lat=round(min_lat, 6),
                    max_lon=round(max_lon, 6),
                    max_lat=round(max_lat, 6),
                    geom_geojson=geom_geojson_str,
                    tile_key=tile_key,
                    raster_file_2022=fn_2022 if has_2022 else None,
                    raster_file_2025=fn_2025 if has_2025 else None,
                    status=TaskStatus.UNASSIGNED.value
                )
                db.add(tg)
                imported_count += 1

        db.commit()
        logger.info(f"Sync complete! Imported: {imported_count}, Updated: {updated_count}, Total TaskGrids in DB: {db.query(TaskGrid).count()}")

    except Exception as e:
        logger.error(f"Error during synchronization: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    sync_all()
