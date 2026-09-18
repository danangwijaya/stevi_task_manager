import os
import json
import tempfile
import zipfile
import shutil
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from shapely.geometry import shape, Polygon, MultiPolygon
import geopandas as gpd

from app.db.session import get_db
from app.db.models import TaskGrid, Annotation, User, ExportJob
from app.core.config import settings
from app.api.deps import get_current_user, get_current_active_admin
from app.services.rasterizer import build_unet_dataset_package

router = APIRouter()

def cleanup_temp_dir(dir_path: str):
    """Background task to remove temporary export directory."""
    try:
        shutil.rmtree(dir_path, ignore_errors=True)
    except Exception:
        pass

@router.post("/trigger")
def trigger_export(
    year: Optional[int] = 2025,
    only_approved: bool = False, # if True only APPROVED, if False include SUBMITTED for fast testing
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    1-Click Multi-spectral Dataset Export Pipeline.
    Gathers approved tasks, rasterizes vector polygons into pixel masks, and packages into train/val/test splits.
    """
    query = db.query(TaskGrid)
    if year:
        query = query.filter(TaskGrid.year == year)
    if only_approved:
        query = query.filter(TaskGrid.status == "APPROVED")
    else:
        query = query.filter(TaskGrid.status.in_(["APPROVED", "SUBMITTED", "IN_PROGRESS"]))
        
    tasks = query.all()
    
    if not tasks:
        raise HTTPException(
            status_code=400,
            detail="No tasks available for export. Please complete and approve grid annotations first."
        )

    tasks_data = []
    for t in tasks:
        anns = db.query(Annotation).filter(Annotation.task_grid_id == t.id).all()
        anns_list = [{"class_id": a.class_id, "geom": a.geom_geojson} for a in anns]
        tasks_data.append({
            "task": t,
            "annotations": anns_list
        })

    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    
    # Run dataset packaging
    result = build_unet_dataset_package(
        approved_tasks_data=tasks_data,
        output_base_dir=settings.EXPORT_DIR,
        patch_size=settings.PATCH_SIZE_PIXELS
    )

    # Record export job
    job = ExportJob(
        status="COMPLETED",
        year=year,
        total_patches=len(tasks),
        zip_file_path=result["zip_path"],
        log_message=f"Exported {len(tasks)} patches ({result['metadata']['splits']['train']} train, {result['metadata']['splits']['val']} val, {result['metadata']['splits']['test']} test)"
    )
    db.add(job)
    db.commit()

    return {
        "status": "success",
        "message": f"Successfully generated dataset with {len(tasks)} patches!",
        "job_id": job.id,
        "total_patches": len(tasks),
        "splits": result["metadata"]["splits"],
        "class_pixel_distribution": result["metadata"]["class_pixel_distribution"],
        "download_url": f"{settings.API_V1_STR}/export/download/{job.id}"
    }

@router.get("/download/{job_id}")
def download_dataset_zip(
    job_id: int,
    db: Session = Depends(get_db)
) -> Any:
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job or not job.zip_file_path or not os.path.exists(job.zip_file_path):
        raise HTTPException(status_code=404, detail="Dataset archive not found")
        
    return FileResponse(
        path=job.zip_file_path,
        filename=f"sentinel2_dataset_{job.year}.zip",
        media_type="application/zip"
    )

@router.get("/vector/summary")
def get_vector_export_summary(
    year: Optional[int] = None,
    only_approved: bool = False,
    study_area_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns summary metrics of digitized vector training samples with Land Cover attributes.
    """
    query = db.query(Annotation).join(TaskGrid)
    if year:
        query = query.filter(TaskGrid.year == year)
    if only_approved:
        query = query.filter(TaskGrid.status == "APPROVED")
    if study_area_id:
        query = query.filter(TaskGrid.study_area_id == study_area_id)

    annotations = query.all()
    classes_meta = {c["id"]: c for c in settings.LAND_COVER_CLASSES}
    
    total_samples = len(annotations)
    total_area_sqm = sum(a.area_sqm or 0 for a in annotations)
    total_area_ha = round(total_area_sqm / 10000.0, 2)
    
    unique_grids = set(a.task_grid_id for a in annotations if a.task_grid_id)
    
    class_counts = {}
    for a in annotations:
        cid = a.class_id
        if cid not in class_counts:
            cm = classes_meta.get(cid, {})
            class_counts[cid] = {
                "class_id": cid,
                "class_name": a.class_name or cm.get("name", f"Kelas {cid}"),
                "color": cm.get("color", "#9CA3AF"),
                "count": 0,
                "total_area_ha": 0.0
            }
        class_counts[cid]["count"] += 1
        class_counts[cid]["total_area_ha"] += round((a.area_sqm or 0) / 10000.0, 2)

    # Distinct years in db
    years_q = db.query(TaskGrid.year).distinct().all()
    available_years = sorted([y[0] for y in years_q if y[0] is not None])

    return {
        "total_samples": total_samples,
        "total_area_ha": total_area_ha,
        "total_grids": len(unique_grids),
        "classes": sorted(list(class_counts.values()), key=lambda x: x["count"], reverse=True),
        "available_years": available_years
    }

@router.get("/vector/geojson")
def export_vector_geojson(
    year: Optional[int] = None,
    only_approved: bool = False,
    study_area_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    Downloads GeoJSON file containing on-screen digitized training samples with Penutupan Lahan attributes.
    """
    query = db.query(Annotation).join(TaskGrid)
    if year:
        query = query.filter(TaskGrid.year == year)
    if only_approved:
        query = query.filter(TaskGrid.status == "APPROVED")
    if study_area_id:
        query = query.filter(TaskGrid.study_area_id == study_area_id)

    annotations = query.all()
    classes_meta = {c["id"]: c for c in settings.LAND_COVER_CLASSES}
    
    features = []
    for ann in annotations:
        try:
            geom = json.loads(ann.geom_geojson)
            tg = ann.task_grid
            cm = classes_meta.get(ann.class_id, {})
            c_name = ann.class_name or cm.get("name", f"Kelas {ann.class_id}")
            mapper = ann.author.full_name if ann.author else (tg.assignee.full_name if tg and tg.assignee else "Annotator")
            area_ha = round((ann.area_sqm or 0) / 10000.0, 4)
            area_m2 = round(ann.area_sqm or 0, 2)

            features.append({
                "type": "Feature",
                "id": ann.id,
                "geometry": geom,
                "properties": {
                    "id": ann.id,
                    "kode_pl": ann.class_id,
                    "nama_pl": c_name,
                    "penutupan_lahan": c_name,
                    "color_hex": cm.get("color", "#9CA3AF"),
                    "grid_code": tg.grid_code if tg else "",
                    "tahun": tg.year if tg else None,
                    "status_grid": tg.status if tg else "",
                    "mapper": mapper,
                    "luas_ha": area_ha,
                    "luas_m2": area_m2,
                    "created_at": ann.created_at.isoformat() if ann.created_at else None
                }
            })
        except Exception:
            continue

    geojson_data = {
        "type": "FeatureCollection",
        "name": f"training_samples_penutupan_lahan_{year or 'all'}",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "total_features": len(features),
        "features": features
    }

    content = json.dumps(geojson_data, ensure_ascii=False, indent=2)
    filename = f"training_samples_penutupan_lahan_{year or 'all'}.geojson"
    
    return Response(
        content=content,
        media_type="application/geo+json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )

@router.get("/vector/shapefile")
def export_vector_shapefile(
    background_tasks: BackgroundTasks,
    year: Optional[int] = None,
    only_approved: bool = False,
    study_area_id: Optional[int] = None,
    db: Session = Depends(get_db)
) -> Any:
    """
    Downloads ESRI Shapefile (.zip) bundle containing on-screen digitized training samples with Penutupan Lahan attributes.
    """
    query = db.query(Annotation).join(TaskGrid)
    if year:
        query = query.filter(TaskGrid.year == year)
    if only_approved:
        query = query.filter(TaskGrid.status == "APPROVED")
    if study_area_id:
        query = query.filter(TaskGrid.study_area_id == study_area_id)

    annotations = query.all()
    if not annotations:
        raise HTTPException(status_code=404, detail="Tidak ada data sampel digitasi vektor yang sesuai dengan filter.")

    classes_meta = {c["id"]: c for c in settings.LAND_COVER_CLASSES}
    records = []
    geometries = []

    for ann in annotations:
        try:
            geom_dict = json.loads(ann.geom_geojson)
            s_geom = shape(geom_dict)
            if not s_geom.is_valid:
                s_geom = s_geom.buffer(0)
            if s_geom.is_empty:
                continue

            # Standardize to MultiPolygon to prevent ESRI shapefile mixed-type schema errors
            if isinstance(s_geom, Polygon):
                s_geom = MultiPolygon([s_geom])
            elif not isinstance(s_geom, MultiPolygon):
                continue

            tg = ann.task_grid
            cm = classes_meta.get(ann.class_id, {})
            c_name = str(ann.class_name or cm.get("name", f"Kelas {ann.class_id}"))[:50]
            mapper = str(ann.author.full_name if ann.author else (tg.assignee.full_name if tg and tg.assignee else "Annotator"))[:50]
            grid_code = str(tg.grid_code if tg else "")[:20]
            status_grid = str(tg.status if tg else "")[:20]
            tahun = int(tg.year) if (tg and tg.year) else (year or 2026)
            luas_ha = round((ann.area_sqm or 0) / 10000.0, 4)
            luas_m2 = round(ann.area_sqm or 0, 2)

            records.append({
                "ID": int(ann.id),
                "KODE_PL": int(ann.class_id),
                "NAMA_PL": c_name,
                "PENUTUPAN": c_name,
                "GRID_CODE": grid_code,
                "TAHUN": tahun,
                "STATUS": status_grid,
                "MAPPER": mapper,
                "LUAS_HA": float(luas_ha),
                "LUAS_M2": float(luas_m2)
            })
            geometries.append(s_geom)
        except Exception:
            continue

    if not records:
        raise HTTPException(status_code=400, detail="Tidak ada geometri vektor valid yang dapat diekspor.")

    gdf = gpd.GeoDataFrame(records, geometry=geometries, crs="EPSG:4326")

    # Create temporary directory for shapefile generation
    temp_dir = tempfile.mkdtemp(prefix="export_shp_")
    shp_basename = f"training_samples_penutupan_lahan_{year or 'all'}"
    shp_path = os.path.join(temp_dir, f"{shp_basename}.shp")

    try:
        gdf.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")
        zip_filename = f"{shp_basename}_shp.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for ext in [".shp", ".shx", ".dbf", ".prj", ".cpg"]:
                file_to_add = os.path.join(temp_dir, f"{shp_basename}{ext}")
                if os.path.exists(file_to_add):
                    zipf.write(file_to_add, arcname=f"{shp_basename}{ext}")

        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'}
        )
    except Exception as e:
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"Gagal mengekspor Shapefile: {str(e)}")
