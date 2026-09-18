import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath("backend"))

from app.db.session import SessionLocal, engine
from app.db.models import StudyArea, TaskGrid, TaskStatus
from app.services.grid_generator import generate_spatial_grids
from sqlalchemy import text

ADDITIONAL_PROJECTS = [
    {
        "name": "IKN Nusantara & Kalimantan Timur (Kawasan Penyangga)",
        "description": "Pemetaan data latih tutupan lahan kawasan Ibu Kota Nusantara (IKN) dan Kalimantan Timur berbasis citra satelit Sentinel-2 multi-spektral untuk evaluasi jasa ekosistem dan keanekaragaman hayati.",
        "center_lat": -0.950,
        "center_lon": 116.850,
        "default_zoom": 10,
        "min_lon": 116.65,
        "min_lat": -1.10,
        "max_lon": 117.05,
        "max_lat": -0.80,
        "prefix": "IKN"
    },
    {
        "name": "Kawasan Restorasi Mangrove & Pesisir Riau",
        "description": "Pemetaan tutupan lahan pesisir, ekosistem mangrove, dan sempadan sungai untuk mendukung restorasi lahan basah dan cadangan karbon biru (blue carbon).",
        "center_lat": 1.500,
        "center_lon": 101.800,
        "default_zoom": 10,
        "min_lon": 101.65,
        "min_lat": 1.35,
        "max_lon": 102.05,
        "max_lat": 1.65,
        "prefix": "RAU"
    },
    {
        "name": "Kawasan Danau Toba & Hutan Batang Toru",
        "description": "Pemetaan tutupan lahan kawasan tangkapan air Danau Toba, hutan lindung Bukit Barisan, dan koridor satwa liar menggunakan komposit citra Sentinel-2 multi-spektral.",
        "center_lat": 2.650,
        "center_lon": 98.850,
        "default_zoom": 10,
        "min_lon": 101.65,
        "min_lat": 1.35,
        "max_lon": 102.05,
        "max_lat": 1.65,
        "prefix": "TBA"
    }
]

def seed_projects(db):
    created_areas = 0
    created_grids = 0

    for p in ADDITIONAL_PROJECTS:
        area = db.query(StudyArea).filter(StudyArea.name == p["name"]).first()
        if not area:
            area = StudyArea(
                name=p["name"],
                description=p["description"],
                center_lat=p["center_lat"],
                center_lon=p["center_lon"],
                default_zoom=p["default_zoom"],
                created_at=datetime.utcnow()
            )
            db.add(area)
            db.commit()
            db.refresh(area)
            created_areas += 1
            print(f"Created StudyArea: {area.name} (ID: {area.id})")

        # Check existing grids for this area
        grid_count = db.query(TaskGrid).filter(TaskGrid.study_area_id == area.id).count()
        if grid_count == 0:
            generated = generate_spatial_grids(
                min_lon=p["min_lon"],
                min_lat=p["min_lat"],
                max_lon=p["max_lon"],
                max_lat=p["max_lat"],
                prefix=p["prefix"],
                patch_size_px=1024,
                pixel_res_m=10.0
            )
            for g in generated:
                grid_code = f"{g['grid_code']}_2026"
                if db.query(TaskGrid).filter(TaskGrid.grid_code == grid_code).first():
                    continue
                db.add(TaskGrid(
                    grid_code=grid_code,
                    study_area_id=area.id,
                    year=2026,
                    min_lon=g["min_lon"],
                    min_lat=g["min_lat"],
                    max_lon=g["max_lon"],
                    max_lat=g["max_lat"],
                    geom_geojson=g["geom_geojson"],
                    status=TaskStatus.UNASSIGNED.value,
                    updated_at=datetime.utcnow()
                ))
                created_grids += 1
            db.commit()
            print(f"Generated {created_grids} grids for {area.name}")

    if engine.dialect.name == "postgresql":
        try:
            db.execute(text("SELECT setval('study_areas_id_seq', COALESCE((SELECT MAX(id) FROM study_areas), 1), true);"))
            db.execute(text("SELECT setval('task_grids_id_seq', COALESCE((SELECT MAX(id) FROM task_grids), 1), true);"))
            db.commit()
        except Exception:
            pass

    return created_areas, created_grids

def main():
    db = SessionLocal()
    try:
        areas, grids = seed_projects(db)
        print(f"Done seeding projects! New areas: {areas}, New grids: {grids}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
