import os
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import TaskGrid, Annotation, User, ExportJob
from app.core.config import settings
from app.api.deps import get_current_user, get_current_active_admin
from app.services.rasterizer import build_unet_dataset_package

router = APIRouter()

@router.post("/trigger")
def trigger_export(
    year: Optional[int] = 2025,
    only_approved: bool = False, # if True only APPROVED, if False include SUBMITTED for fast testing
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    1-Click U-Net Multi-spectral Dataset Export Pipeline.
    Gathers approved tasks, rasterizes vector polygons into 256x256 pixel masks, and packages into train/val/test splits.
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
        "message": f"Successfully generated U-Net dataset with {len(tasks)} patches!",
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
        filename=f"sentinel2_unet_dataset_{job.year}.zip",
        media_type="application/zip"
    )
