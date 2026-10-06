import os
import json
import logging
from datetime import datetime
from shapely.geometry import shape, mapping
from sqlalchemy import text
from app.db.session import SessionLocal, engine
from app.db.models import StudyArea, TaskGrid, TaskStatus
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_test_sumbar")

PROJECT_NAME = "Uji Coba Sumatera Barat (3 Grid)"
GEOJSON_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "vector", "test_sumbar.geojson"
)

# Known tile key mappings and filenames for the 3 features in test_sumbar.geojson
# Feature 0: Padang Kota (tile_key: 0000016384-0000016384)
# Feature 1: Padang Selatan/Teluk Bayur (tile_key: 0000020480-0000020480)
# Feature 2: Padang Pariaman/Bandara (tile_key: 0000016384-0000016384)
GRID_TILES = {
    0: {
        "tile_key": "0000016384-0000016384",
        "raster_2025": "sentinel2_sumbar_2025_10m-0000016384-0000016384.tif",
        "raster_2022": "sentinel2_sumbar_2022_10m-0000016384-0000016384.tif"
    },
    1: {
        "tile_key": "0000020480-0000020480",
        "raster_2025": "sentinel2_sumbar_2025_10m-0000020480-0000020480.tif",
        "raster_2022": "sentinel2_sumbar_2022_10m-0000020480-0000020480.tif"
    },
    2: {
        "tile_key": "0000016384-0000016384",
        "raster_2025": "sentinel2_sumbar_2025_10m-0000016384-0000016384.tif",
        "raster_2022": "sentinel2_sumbar_2022_10m-0000016384-0000016384.tif"
    }
}

YEARS = [2025, 2022]

def create_test_sumbar_project():
    if not os.path.exists(GEOJSON_FILE):
        raise FileNotFoundError(f"File GeoJSON tidak ditemukan: {GEOJSON_FILE}")

    with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    features = geojson_data.get("features", [])
    if len(features) != 3:
        logger.warning(f"Jumlah feature pada GeoJSON: {len(features)} (diharapkan 3)")

    db = SessionLocal()
    try:
        # Check if project already exists
        area = db.query(StudyArea).filter(StudyArea.name == PROJECT_NAME).first()
        if not area:
            # Calculate center from features
            all_lons = []
            all_lats = []
            for feat in features:
                geom = shape(feat["geometry"])
                b = geom.bounds
                all_lons.extend([b[0], b[2]])
                all_lats.extend([b[1], b[3]])

            center_lon = round(sum(all_lons) / len(all_lons), 6)
            center_lat = round(sum(all_lats) / len(all_lats), 6)

            area = StudyArea(
                name=PROJECT_NAME,
                description="Proyek uji coba pemetaan data latih tutupan lahan berbasis 3 petak grid test_sumbar.geojson menggunakan citra Sentinel-2 komposit Sumatera Barat tahun 2025 dan 2022.",
                center_lat=center_lat,
                center_lon=center_lon,
                default_zoom=11,
                priority="HIGH",
                difficulty="Moderate",
                created_at=datetime.utcnow()
            )
            db.add(area)
            db.commit()
            db.refresh(area)
            logger.info(f"Berhasil membuat StudyArea: '{area.name}' (ID: {area.id})")
        else:
            logger.info(f"StudyArea '{area.name}' sudah ada (ID: {area.id})")

        # Create or update 3 grids for both 2025 and 2022
        existing_grids = {
            g.grid_code: g
            for g in db.query(TaskGrid).filter(TaskGrid.study_area_id == area.id).all()
        }

        created_count = 0
        updated_count = 0

        raster_2025_dir = os.path.join(settings.RASTER_BASE_DIR, "Sumatera_Barat_2025")
        raster_2022_dir = os.path.join(settings.RASTER_BASE_DIR, "Sumatera_Barat_2022")

        for idx, feat in enumerate(features[:3]):
            geom = shape(feat["geometry"])
            # Normalize MultiPolygon with single polygon to Polygon if applicable
            if geom.geom_type == "MultiPolygon" and len(geom.geoms) == 1:
                geom = geom.geoms[0]

            geom_geojson_str = json.dumps(mapping(geom))
            b = geom.bounds
            min_lon, min_lat, max_lon, max_lat = round(b[0], 6), round(b[1], 6), round(b[2], 6), round(b[3], 6)

            meta = GRID_TILES.get(idx, {})
            tile_key = meta.get("tile_key")
            fn_2025 = meta.get("raster_2025")
            fn_2022 = meta.get("raster_2022")

            has_2025 = os.path.exists(os.path.join(raster_2025_dir, fn_2025)) if fn_2025 else False
            has_2022 = os.path.exists(os.path.join(raster_2022_dir, fn_2022)) if fn_2022 else False

            grid_num = idx + 1

            for yr in YEARS:
                grid_code = f"TEST_SB_GRID_{grid_num:03d}_{yr}"

                if grid_code in existing_grids:
                    tg = existing_grids[grid_code]
                    tg.min_lon = min_lon
                    tg.min_lat = min_lat
                    tg.max_lon = max_lon
                    tg.max_lat = max_lat
                    tg.geom_geojson = geom_geojson_str
                    tg.tile_key = tile_key
                    tg.raster_file_2025 = fn_2025 if has_2025 else None
                    tg.raster_file_2022 = fn_2022 if has_2022 else None
                    updated_count += 1
                else:
                    tg = TaskGrid(
                        grid_code=grid_code,
                        study_area_id=area.id,
                        year=yr,
                        min_lon=min_lon,
                        min_lat=min_lat,
                        max_lon=max_lon,
                        max_lat=max_lat,
                        geom_geojson=geom_geojson_str,
                        tile_key=tile_key,
                        raster_file_2025=fn_2025 if has_2025 else None,
                        raster_file_2022=fn_2022 if has_2022 else None,
                        status=TaskStatus.UNASSIGNED.value,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(tg)
                    created_count += 1

        db.commit()

        # Sync PostgreSQL sequences
        if engine.dialect.name == "postgresql":
            try:
                db.execute(text("SELECT setval('study_areas_id_seq', COALESCE((SELECT MAX(id) FROM study_areas), 1), true);"))
                db.execute(text("SELECT setval('task_grids_id_seq', COALESCE((SELECT MAX(id) FROM task_grids), 1), true);"))
                db.commit()
            except Exception as e:
                logger.warning(f"Error resetting sequences: {e}")

        logger.info(
            f"Selesai! Project: '{area.name}' (ID: {area.id}). "
            f"Created Grids: {created_count}, Updated Grids: {updated_count}"
        )
        return area.id

    except Exception as e:
        db.rollback()
        logger.error(f"Gagal membuat project test sumbar: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_sumbar_project()
