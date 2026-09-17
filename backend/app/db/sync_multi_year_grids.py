import os
import json
import logging
import geopandas as gpd
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.db.models import User, StudyArea, TaskGrid, Annotation, LandCoverClass, UserRole, TaskStatus
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_multi_year_grids")

def sync_multi_year_grids():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    try:
        study_area = db.query(StudyArea).filter(StudyArea.name == "Provinsi Sumatera Barat (Seluruh Wilayah)").first()
        if not study_area:
            study_area = db.query(StudyArea).first()
        if not study_area:
            logger.error("No study area found! Please run seed.py first.")
            return

        shp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "vector", "tif_extents.shp")
        if not os.path.exists(shp_path):
            raise FileNotFoundError(f"Shapefile not found: {shp_path}")

        logger.info(f"Reading shapefile: {shp_path}...")
        gdf = gpd.read_file(shp_path)
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)

        gdf["center_y"] = gdf.geometry.centroid.y
        gdf["center_x"] = gdf.geometry.centroid.x
        gdf = gdf.sort_values(by=["center_y", "center_x"], ascending=[False, True]).reset_index(drop=True)

        available_years = [2025, 2022, 2018, 2017]
        logger.info(f"Target multi-year synchronization for years: {available_years}")

        # Fetch existing task grids
        all_grids = db.query(TaskGrid).filter(TaskGrid.study_area_id == study_area.id).all()
        grid_by_code = {g.grid_code: g for g in all_grids}

        # Step 1: Migrate legacy 2025 grids named "SB_GRID_XXX" to "SB_GRID_XXX_2025"
        migrated_2025_count = 0
        for idx in range(len(gdf)):
            grid_num = idx + 1
            old_code = f"SB_GRID_{grid_num:03d}"
            new_code = f"SB_GRID_{grid_num:03d}_2025"
            if old_code in grid_by_code and new_code not in grid_by_code:
                tg = grid_by_code[old_code]
                tg.grid_code = new_code
                tg.year = 2025
                grid_by_code[new_code] = tg
                del grid_by_code[old_code]
                migrated_2025_count += 1

        db.flush()
        if migrated_2025_count > 0:
            logger.info(f"Migrated {migrated_2025_count} legacy 2025 grids to suffix format (e.g. SB_GRID_XXX_2025).")

        # Step 2: Create grids for all available years
        created_per_year = {yr: 0 for yr in available_years}
        updated_per_year = {yr: 0 for yr in available_years}

        for yr in available_years:
            year_raster_dir = os.path.join(settings.RASTER_BASE_DIR, f"Sumatera_Barat_{yr}")

            for idx, row in gdf.iterrows():
                grid_num = idx + 1
                grid_code = f"SB_GRID_{grid_num:03d}_{yr}"
                
                raw_fn = row["filename"]
                suffix = raw_fn.split("_10m-")[-1].replace(".tif", "")
                tile_key = suffix
                
                bounds = row.geometry.bounds
                min_lon, min_lat, max_lon, max_lat = bounds
                geom_geojson_str = json.dumps(row.geometry.__geo_interface__)
                
                fn_year = f"sentinel2_sumbar_{yr}_10m-{tile_key}.tif"
                has_raster = os.path.exists(os.path.join(year_raster_dir, fn_year))

                if grid_code in grid_by_code:
                    tg = grid_by_code[grid_code]
                    tg.min_lon = round(min_lon, 6)
                    tg.min_lat = round(min_lat, 6)
                    tg.max_lon = round(max_lon, 6)
                    tg.max_lat = round(max_lat, 6)
                    tg.geom_geojson = geom_geojson_str
                    tg.tile_key = tile_key
                    if yr == 2022:
                        tg.raster_file_2022 = fn_year if has_raster else None
                    elif yr == 2025:
                        tg.raster_file_2025 = fn_year if has_raster else None
                    updated_per_year[yr] += 1
                else:
                    tg = TaskGrid(
                        grid_code=grid_code,
                        study_area_id=study_area.id,
                        year=yr,
                        min_lon=round(min_lon, 6),
                        min_lat=round(min_lat, 6),
                        max_lon=round(max_lon, 6),
                        max_lat=round(max_lat, 6),
                        geom_geojson=geom_geojson_str,
                        tile_key=tile_key,
                        raster_file_2022=fn_year if (yr == 2022 and has_raster) else None,
                        raster_file_2025=fn_year if (yr == 2025 and has_raster) else None,
                        status=TaskStatus.UNASSIGNED.value
                    )
                    db.add(tg)
                    grid_by_code[grid_code] = tg
                    created_per_year[yr] += 1

        db.commit()
        logger.info(f"Sync Multi-Year complete!")
        for yr in available_years:
            total_yr = db.query(TaskGrid).filter(TaskGrid.year == yr).count()
            logger.info(f"  Year {yr}: Created {created_per_year[yr]}, Updated {updated_per_year[yr]}, Total in DB: {total_yr}")

        logger.info(f"Grand Total TaskGrids in DB: {db.query(TaskGrid).count()}")

    except Exception as e:
        logger.error(f"Error during multi-year sync: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    sync_multi_year_grids()
