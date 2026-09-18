import json
from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import TaskGrid, User, StudyArea, Annotation, TaskStatus
from app.api.deps import get_current_user, get_current_active_admin, get_current_active_reviewer
from app.services.grid_generator import generate_spatial_grids

router = APIRouter()

# ─────────────────────────────────────────────
# PYDANTIC SCHEMAS — StudyArea / Project
# ─────────────────────────────────────────────

class StudyAreaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    center_lat: float
    center_lon: float
    default_zoom: int
    total_tasks: int = 0
    approved_tasks: int = 0
    in_progress_tasks: int = 0
    submitted_tasks: int = 0
    contributors_count: int = 0
    priority: Optional[str] = "HIGH"
    difficulty: Optional[str] = "Moderate"
    campaign: Optional[str] = "GEOSTEVIA"
    created_at: datetime

    class Config:
        from_attributes = True

class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = None
    center_lat: float
    center_lon: float
    default_zoom: Optional[int] = 8
    priority: Optional[str] = "MEDIUM"
    difficulty: Optional[str] = "Moderate"
    # Bounding box for auto grid generation
    min_lon: Optional[float] = None
    min_lat: Optional[float] = None
    max_lon: Optional[float] = None
    max_lat: Optional[float] = None
    patch_size_px: Optional[int] = 1024
    pixel_res_m: Optional[float] = 10.0
    grid_prefix: Optional[str] = "P"

class UpdateProjectRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    default_zoom: Optional[int] = None
    priority: Optional[str] = None
    difficulty: Optional[str] = None

# ─────────────────────────────────────────────
# PROJECT / STUDY AREA ENDPOINTS
# ─────────────────────────────────────────────

@router.get("/projects", response_model=List[StudyAreaResponse])
def get_all_projects(
    db: Session = Depends(get_db)
) -> Any:
    """List all study area projects with grid statistics"""
    areas = db.query(StudyArea).order_by(StudyArea.id.asc()).all()
    result = []
    for a in areas:
        total = db.query(func.count(TaskGrid.id)).filter(TaskGrid.study_area_id == a.id).scalar() or 0
        approved = db.query(func.count(TaskGrid.id)).filter(
            TaskGrid.study_area_id == a.id, TaskGrid.status == "APPROVED"
        ).scalar() or 0
        submitted = db.query(func.count(TaskGrid.id)).filter(
            TaskGrid.study_area_id == a.id, TaskGrid.status == "SUBMITTED"
        ).scalar() or 0
        in_prog = db.query(func.count(TaskGrid.id)).filter(
            TaskGrid.study_area_id == a.id, TaskGrid.status.in_(["IN_PROGRESS", "ASSIGNED"])
        ).scalar() or 0
        contributors = db.query(func.count(func.distinct(TaskGrid.assigned_user_id))).filter(
            TaskGrid.study_area_id == a.id, TaskGrid.assigned_user_id.isnot(None)
        ).scalar() or 0

        priority = a.priority or "MEDIUM"
        difficulty = a.difficulty or "Moderate"

        result.append(StudyAreaResponse(
            id=a.id,
            name=a.name,
            description=a.description,
            center_lat=a.center_lat,
            center_lon=a.center_lon,
            default_zoom=a.default_zoom,
            total_tasks=total,
            approved_tasks=approved,
            in_progress_tasks=in_prog,
            submitted_tasks=submitted,
            contributors_count=contributors,
            priority=priority,
            difficulty=difficulty,
            campaign="GEOSTEVIA",
            created_at=a.created_at
        ))
    return result

@router.post("/projects", response_model=StudyAreaResponse)
def create_project(
    project_in: CreateProjectRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin creates a new study area project, optionally auto-generating grid tiles"""
    existing = db.query(StudyArea).filter(StudyArea.name == project_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Nama proyek sudah terdaftar")

    new_area = StudyArea(
        name=project_in.name,
        description=project_in.description,
        center_lat=project_in.center_lat,
        center_lon=project_in.center_lon,
        default_zoom=project_in.default_zoom or 8,
        priority=project_in.priority or "MEDIUM",
        difficulty=project_in.difficulty or "Moderate"
    )
    db.add(new_area)
    db.commit()
    db.refresh(new_area)

    grid_count = 0
    # Auto-generate grids if bounding box is provided
    if all([
        project_in.min_lon is not None,
        project_in.min_lat is not None,
        project_in.max_lon is not None,
        project_in.max_lat is not None
    ]):
        prefix = (project_in.grid_prefix or "P")[:3].upper()
        grids = generate_spatial_grids(
            min_lon=project_in.min_lon,
            min_lat=project_in.min_lat,
            max_lon=project_in.max_lon,
            max_lat=project_in.max_lat,
            prefix=prefix,
            patch_size_px=project_in.patch_size_px or 1024,
            pixel_res_m=project_in.pixel_res_m or 10.0
        )
        for g in grids:
            grid_code = f"{g['grid_code']}_2026"
            # Skip if code already exists globally
            if db.query(TaskGrid).filter(TaskGrid.grid_code == grid_code).first():
                continue
            db.add(TaskGrid(
                grid_code=grid_code,
                study_area_id=new_area.id,
                year=2026,
                min_lon=g["min_lon"],
                min_lat=g["min_lat"],
                max_lon=g["max_lon"],
                max_lat=g["max_lat"],
                geom_geojson=g["geom_geojson"],
                status=TaskStatus.UNASSIGNED.value,
                updated_at=datetime.utcnow()
            ))
            grid_count += 1
        db.commit()

    return StudyAreaResponse(
        id=new_area.id,
        name=new_area.name,
        description=new_area.description,
        center_lat=new_area.center_lat,
        center_lon=new_area.center_lon,
        default_zoom=new_area.default_zoom,
        total_tasks=grid_count,
        approved_tasks=0,
        in_progress_tasks=0,
        submitted_tasks=0,
        contributors_count=0,
        priority=new_area.priority or "MEDIUM",
        difficulty=new_area.difficulty or "Moderate",
        campaign="GEOSTEVIA",
        created_at=new_area.created_at
    )

@router.put("/projects/{project_id}", response_model=StudyAreaResponse)
def update_project(
    project_id: int,
    project_in: UpdateProjectRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin edits project metadata"""
    area = db.query(StudyArea).filter(StudyArea.id == project_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    if project_in.name is not None:
        # Check name uniqueness
        clash = db.query(StudyArea).filter(StudyArea.name == project_in.name, StudyArea.id != project_id).first()
        if clash:
            raise HTTPException(status_code=400, detail="Nama proyek sudah digunakan")
        area.name = project_in.name
    if project_in.description is not None:
        area.description = project_in.description
    if project_in.center_lat is not None:
        area.center_lat = project_in.center_lat
    if project_in.center_lon is not None:
        area.center_lon = project_in.center_lon
    if project_in.default_zoom is not None:
        area.default_zoom = project_in.default_zoom
    if project_in.priority is not None:
        area.priority = project_in.priority
    if project_in.difficulty is not None:
        area.difficulty = project_in.difficulty

    db.commit()
    db.refresh(area)

    total = db.query(func.count(TaskGrid.id)).filter(TaskGrid.study_area_id == area.id).scalar() or 0
    approved = db.query(func.count(TaskGrid.id)).filter(
        TaskGrid.study_area_id == area.id, TaskGrid.status == "APPROVED"
    ).scalar() or 0
    in_prog = db.query(func.count(TaskGrid.id)).filter(
        TaskGrid.study_area_id == area.id, TaskGrid.status.in_(["IN_PROGRESS", "ASSIGNED"])
    ).scalar() or 0
    submitted = db.query(func.count(TaskGrid.id)).filter(
        TaskGrid.study_area_id == area.id, TaskGrid.status == "SUBMITTED"
    ).scalar() or 0
    contributors = db.query(func.count(func.distinct(TaskGrid.assigned_user_id))).filter(
        TaskGrid.study_area_id == area.id, TaskGrid.assigned_user_id.isnot(None)
    ).scalar() or 0

    return StudyAreaResponse(
        id=area.id, name=area.name, description=area.description,
        center_lat=area.center_lat, center_lon=area.center_lon,
        default_zoom=area.default_zoom, total_tasks=total,
        approved_tasks=approved, in_progress_tasks=in_prog,
        submitted_tasks=submitted, contributors_count=contributors,
        priority=area.priority or "MEDIUM",
        difficulty=area.difficulty or "Moderate",
        campaign="GEOSTEVIA",
        created_at=area.created_at
    )

@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin deletes a project and all its grids (cascade)"""
    area = db.query(StudyArea).filter(StudyArea.id == project_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    # Cascade: delete annotations first, then grids, then area
    db.query(Annotation).filter(
        Annotation.task_grid_id.in_(
            db.query(TaskGrid.id).filter(TaskGrid.study_area_id == project_id)
        )
    ).delete(synchronize_session=False)
    db.query(TaskGrid).filter(TaskGrid.study_area_id == project_id).delete(synchronize_session=False)
    db.delete(area)
    db.commit()
    return {"message": f"Proyek '{area.name}' dan semua grid-nya berhasil dihapus"}


@router.post("/projects/{project_id}/reset")
def reset_project_progress(
    project_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """
    Admin resets all task progress in a project:
    - Deletes all annotations created in the project's task grids
    - Resets all task grids to UNASSIGNED
    - Clears assigned_user_id, reviewer_notes, and completed_at
    """
    area = db.query(StudyArea).filter(StudyArea.id == project_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Proyek tidak ditemukan")

    total_tasks_count = db.query(TaskGrid.id).filter(TaskGrid.study_area_id == project_id).count()
    deleted_annotations_count = 0
    if total_tasks_count > 0:
        deleted_annotations_count = db.query(Annotation).filter(
            Annotation.task_grid_id.in_(
                db.query(TaskGrid.id).filter(TaskGrid.study_area_id == project_id)
            )
        ).delete(synchronize_session=False)
        db.query(TaskGrid).filter(TaskGrid.study_area_id == project_id).update(
            {
                TaskGrid.status: TaskStatus.UNASSIGNED.value,
                TaskGrid.assigned_user_id: None,
                TaskGrid.reviewer_notes: None,
                TaskGrid.completed_at: None,
                TaskGrid.updated_at: datetime.utcnow(),
            },
            synchronize_session=False
        )

    db.commit()
    return {
        "message": f"Progres proyek '{area.name}' berhasil direset. {total_tasks_count} grid dikembalikan ke status Tersedia, dan {deleted_annotations_count} poligon anotasi dibersihkan.",
        "project_id": project_id,
        "reset_tasks_count": total_tasks_count,
        "deleted_annotations_count": deleted_annotations_count
    }


# ─────────────────────────────────────────────
# IMPORT CUSTOM GRID (SHAPEFILE .ZIP / GEOJSON)
# ─────────────────────────────────────────────

@router.post("/import-grid")
async def import_custom_grid(
    file: UploadFile = File(...),
    study_area_id: Optional[int] = Form(None),
    new_project_name: Optional[str] = Form(None),
    new_project_desc: Optional[str] = Form(None),
    years_str: str = Form("2017,2021,2025"),
    grid_id_col: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """
    Imports custom grids from an uploaded Shapefile (.zip) or GeoJSON (.geojson / .json).
    - Reprojects to EPSG:4326 (WGS84) automatically
    - Calculates bounds and center coordinates
    - Creates task grids for specified years (e.g. 2017, 2021, 2025)
    """
    import tempfile, zipfile, os, shutil
    import geopandas as gpd
    from shapely.geometry import mapping

    if not file.filename:
        raise HTTPException(status_code=400, detail="File tidak valid")
        
    filename = file.filename.lower()
    if not (filename.endswith('.zip') or filename.endswith('.geojson') or filename.endswith('.json') or filename.endswith('.shp')):
        raise HTTPException(
            status_code=400,
            detail="Format file tidak didukung. Harap unggah Shapefile (.zip) atau GeoJSON (.geojson / .json)"
        )

    # Parse years
    try:
        years = [int(y.strip()) for y in years_str.split(',') if y.strip()]
        if not years:
            years = [2017, 2021, 2025]
    except Exception:
        years = [2017, 2021, 2025]

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file_path = os.path.join(tmpdir, file.filename)
        with open(temp_file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        try:
            if filename.endswith('.zip'):
                extract_dir = os.path.join(tmpdir, "extracted")
                os.makedirs(extract_dir, exist_ok=True)
                with zipfile.ZipFile(temp_file_path, 'r') as zf:
                    zf.extractall(extract_dir)
                
                # Find .shp file (including in subdirectories)
                shp_files = []
                for root, _, files in os.walk(extract_dir):
                    for fn in files:
                        if fn.lower().endswith('.shp'):
                            shp_files.append(os.path.join(root, fn))
                            
                if not shp_files:
                    raise HTTPException(
                        status_code=400,
                        detail="File .zip tidak berisi file Shapefile (.shp). Pastikan menyertakan .shp, .shx, .dbf, dan .prj."
                    )
                gdf = gpd.read_file(shp_files[0])
            else:
                gdf = gpd.read_file(temp_file_path)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Gagal membaca file geospasial: {str(e)}")

        if gdf.empty:
            raise HTTPException(status_code=400, detail="File vektor kosong (tidak memiliki feature poligon).")

        # Reproject to EPSG:4326 if needed
        try:
            if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
        except Exception as e:
            print(f"Reprojection notice: {e}")

        # Ensure project exists or create new project
        target_area = None
        if study_area_id:
            target_area = db.query(StudyArea).filter(StudyArea.id == study_area_id).first()
            
        if not target_area:
            base_name = os.path.splitext(file.filename)[0].replace('_', ' ')
            proj_name = new_project_name or f"Proyek Custom ({base_name})"
            total_bounds = gdf.total_bounds # minx, miny, maxx, maxy
            center_lon = float((total_bounds[0] + total_bounds[2]) / 2.0)
            center_lat = float((total_bounds[1] + total_bounds[3]) / 2.0)
            
            target_area = StudyArea(
                name=proj_name,
                description=new_project_desc or f"Diimpor dari file {file.filename} pada {datetime.now().strftime('%d %b %Y')}",
                center_lat=center_lat,
                center_lon=center_lon,
                default_zoom=9
            )
            db.add(target_area)
            db.commit()
            db.refresh(target_area)

        # Detect grid code column if not provided
        code_col = grid_id_col
        if not code_col or code_col not in gdf.columns:
            candidates = ['grid_code', 'grid_id', 'id', 'kode', 'kode_grid', 'name', 'nama', 'grid', 'fid']
            for c in candidates:
                for col in gdf.columns:
                    if col.lower() == c:
                        code_col = col
                        break
                if code_col:
                    break

        created_tasks = []
        for idx, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
                
            b = geom.bounds # minx, miny, maxx, maxy
            min_lon, min_lat, max_lon, max_lat = float(b[0]), float(b[1]), float(b[2]), float(b[3])
            
            if code_col and code_col in row and str(row[code_col]).strip():
                raw_code = str(row[code_col]).strip().replace(' ', '_')
            else:
                raw_code = f"GRID_{idx+1:03d}"
                
            geom_json = mapping(geom)
            
            for yr in years:
                grid_code_yr = f"{raw_code}_{yr}"
                existing = db.query(TaskGrid).filter(
                    TaskGrid.study_area_id == target_area.id,
                    TaskGrid.grid_code == grid_code_yr
                ).first()
                
                if existing:
                    continue
                    
                task = TaskGrid(
                    grid_code=grid_code_yr,
                    study_area_id=target_area.id,
                    year=yr,
                    min_lon=min_lon,
                    min_lat=min_lat,
                    max_lon=max_lon,
                    max_lat=max_lat,
                    geom_geojson=json.dumps(geom_json),
                    status=TaskStatus.UNASSIGNED.value
                )
                db.add(task)
                created_tasks.append(task)

        db.commit()
        return {
            "message": f"Berhasil mengimpor {len(gdf)} grid menjadi {len(created_tasks)} tugas!",
            "study_area_id": target_area.id,
            "study_area_name": target_area.name,
            "feature_count": len(gdf),
            "created_tasks_count": len(created_tasks),
            "years": years,
            "columns": [c for c in gdf.columns if c != 'geometry']
        }




class TaskGridResponse(BaseModel):
    id: int
    grid_code: str
    study_area_id: int
    study_area_name: Optional[str] = None
    year: int
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    geom_geojson: str
    assigned_user_id: Optional[int] = None
    assigned_user_name: Optional[str] = None
    status: str
    reviewer_notes: Optional[str] = None
    annotation_count: int = 0
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskStatusUpdate(BaseModel):
    status: str
    reviewer_notes: Optional[str] = None

class TaskAssignRequest(BaseModel):
    user_id: Optional[int] = None

class CreateTaskRequest(BaseModel):
    study_area_id: int
    grid_code: str
    year: Optional[int] = 2026
    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    assigned_user_id: Optional[int] = None

@router.post("/", response_model=TaskGridResponse)
def create_task(
    task_in: CreateTaskRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin creates a new task grid tile"""
    existing = db.query(TaskGrid).filter(TaskGrid.grid_code == task_in.grid_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Grid code '{task_in.grid_code}' sudah terdaftar")
    
    geom_dict = {
        "type": "Polygon",
        "coordinates": [[
            [task_in.min_lon, task_in.min_lat],
            [task_in.max_lon, task_in.min_lat],
            [task_in.max_lon, task_in.max_lat],
            [task_in.min_lon, task_in.max_lat],
            [task_in.min_lon, task_in.min_lat]
        ]]
    }
    
    initial_status = "ASSIGNED" if task_in.assigned_user_id else "UNASSIGNED"
    
    new_task = TaskGrid(
        grid_code=task_in.grid_code,
        study_area_id=task_in.study_area_id,
        year=task_in.year or 2026,
        min_lon=task_in.min_lon,
        min_lat=task_in.min_lat,
        max_lon=task_in.max_lon,
        max_lat=task_in.max_lat,
        geom_geojson=json.dumps(geom_dict),
        assigned_user_id=task_in.assigned_user_id,
        status=initial_status,
        updated_at=datetime.utcnow()
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    assignee_name = new_task.assignee.full_name if new_task.assignee else None
    study_name = new_task.study_area.name if new_task.study_area else None

    return TaskGridResponse(
        id=new_task.id,
        grid_code=new_task.grid_code,
        study_area_id=new_task.study_area_id,
        study_area_name=study_name,
        year=new_task.year,
        min_lon=new_task.min_lon,
        min_lat=new_task.min_lat,
        max_lon=new_task.max_lon,
        max_lat=new_task.max_lat,
        geom_geojson=new_task.geom_geojson,
        assigned_user_id=new_task.assigned_user_id,
        assigned_user_name=assignee_name,
        status=new_task.status,
        reviewer_notes=new_task.reviewer_notes,
        annotation_count=0,
        updated_at=new_task.updated_at
    )

@router.get("/", response_model=List[TaskGridResponse])
def get_tasks(
    study_area_id: Optional[int] = None,
    year: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    assigned_to_me: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    query = db.query(TaskGrid)
    
    if study_area_id:
        query = query.filter(TaskGrid.study_area_id == study_area_id)
    if year:
        query = query.filter(TaskGrid.year == year)
    if status_filter:
        query = query.filter(TaskGrid.status == status_filter)
    if assigned_to_me:
        query = query.filter(TaskGrid.assigned_user_id == current_user.id)
        
    tasks = query.all()
    
    result = []
    for t in tasks:
        ann_cnt = db.query(func.count(Annotation.id)).filter(Annotation.task_grid_id == t.id).scalar() or 0
        assignee_name = t.assignee.full_name if t.assignee else None
        study_name = t.study_area.name if t.study_area else None
        
        result.append(TaskGridResponse(
            id=t.id,
            grid_code=t.grid_code,
            study_area_id=t.study_area_id,
            study_area_name=study_name,
            year=t.year,
            min_lon=t.min_lon,
            min_lat=t.min_lat,
            max_lon=t.max_lon,
            max_lat=t.max_lat,
            geom_geojson=t.geom_geojson,
            assigned_user_id=t.assigned_user_id,
            assigned_user_name=assignee_name,
            status=t.status,
            reviewer_notes=t.reviewer_notes,
            annotation_count=ann_cnt,
            updated_at=t.updated_at
        ))
    return result

@router.get("/{task_id}", response_model=TaskGridResponse)
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    task = db.query(TaskGrid).filter(TaskGrid.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")
        
    ann_cnt = db.query(func.count(Annotation.id)).filter(Annotation.task_grid_id == task.id).scalar() or 0
    assignee_name = task.assignee.full_name if task.assignee else None
    study_name = task.study_area.name if task.study_area else None

    return TaskGridResponse(
        id=task.id,
        grid_code=task.grid_code,
        study_area_id=task.study_area_id,
        study_area_name=study_name,
        year=task.year,
        min_lon=task.min_lon,
        min_lat=task.min_lat,
        max_lon=task.max_lon,
        max_lat=task.max_lat,
        geom_geojson=task.geom_geojson,
        assigned_user_id=task.assigned_user_id,
        assigned_user_name=assignee_name,
        status=task.status,
        reviewer_notes=task.reviewer_notes,
        annotation_count=ann_cnt,
        updated_at=task.updated_at
    )

@router.get("/{task_id}/siblings")
def get_task_siblings(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Returns corresponding tasks for this exact spatial grid in other available years."""
    current = db.query(TaskGrid).filter(TaskGrid.id == task_id).first()
    if not current:
        raise HTTPException(status_code=404, detail="Task grid not found")
        
    parts = current.grid_code.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) == 4:
        base_code = parts[0]
    else:
        base_code = current.grid_code

    query = db.query(TaskGrid).filter(
        TaskGrid.study_area_id == current.study_area_id,
        TaskGrid.id != current.id
    )
    if current.tile_key:
        query = query.filter(
            (TaskGrid.tile_key == current.tile_key) | (TaskGrid.grid_code.like(f"{base_code}\\_%", escape="\\"))
        )
    else:
        query = query.filter(TaskGrid.grid_code.like(f"{base_code}\\_%", escape="\\"))

    candidates = query.order_by(TaskGrid.year.desc()).all()
    
    result = []
    for s in candidates:
        s_parts = s.grid_code.rsplit("_", 1)
        s_base = s_parts[0] if (len(s_parts) == 2 and s_parts[1].isdigit() and len(s_parts[1]) == 4) else s.grid_code
        is_match = bool((current.tile_key and s.tile_key == current.tile_key) or (s_base == base_code))
        if not is_match:
            continue

        ann_cnt = db.query(func.count(Annotation.id)).filter(Annotation.task_grid_id == s.id).scalar() or 0
        assignee_name = s.assignee.full_name if s.assignee else None
        result.append({
            "id": s.id,
            "grid_code": s.grid_code,
            "year": s.year,
            "status": s.status,
            "annotation_count": ann_cnt,
            "assigned_user_name": assignee_name
        })
    return result

@router.post("/{task_id}/claim")
def claim_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    HOT OSM style: Contributor claims/locks a grid tile to start annotating.
    Only UNASSIGNED grids can be claimed by contributors.
    Admins can force-assign any grid.
    """
    task = db.query(TaskGrid).filter(TaskGrid.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Non-admin users can ONLY claim UNASSIGNED grids
    if current_user.role != "admin":
        if task.status != "UNASSIGNED":
            status_labels = {
                "IN_PROGRESS": "sedang dikerjakan",
                "SUBMITTED": "menunggu review QC",
                "REVISION_NEEDED": "dalam proses revisi",
                "APPROVED": "sudah disetujui",
                "ASSIGNED": "sudah di-assign"
            }
            label = status_labels.get(task.status, task.status)
            assignee_info = f" oleh {task.assignee.full_name}" if task.assignee else ""
            raise HTTPException(
                status_code=400,
                detail=f"Grid ini tidak tersedia — status saat ini: {label}{assignee_info}. Hanya grid berstatus 'Tersedia' yang bisa diambil."
            )

    task.assigned_user_id = current_user.id
    task.status = "IN_PROGRESS"
    task.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return {
        "message": f"Berhasil mengklaim grid {task.grid_code}",
        "task_id": task.id,
        "status": task.status,
        "assigned_user_name": current_user.full_name
    }

@router.post("/{task_id}/unclaim")
def unclaim_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Release task back to pool. ADMIN ONLY.
    Contributors cannot release grids themselves — only admins can.
    """
    task = db.query(TaskGrid).filter(TaskGrid.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Hanya Administrator yang dapat melepas grid ke antrean umum. Hubungi admin jika ingin melepas grid ini."
        )

    task.assigned_user_id = None
    task.status = "UNASSIGNED"
    task.reviewer_notes = None
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return {"message": f"Grid {task.grid_code} dikembalikan ke antrean umum oleh admin", "task_id": task.id}

@router.post("/{task_id}/assign")
def assign_task(
    task_id: int,
    assign_req: TaskAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_reviewer)
) -> Any:
    task = db.query(TaskGrid).filter(TaskGrid.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if assign_req.user_id:
        target_user = db.query(User).filter(User.id == assign_req.user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        task.assigned_user_id = target_user.id
        if task.status == TaskStatus.UNASSIGNED.value:
            task.status = TaskStatus.ASSIGNED.value
    else:
        task.assigned_user_id = None
        task.status = TaskStatus.UNASSIGNED.value
        
    db.commit()
    db.refresh(task)
    return {"message": "Task assignment updated successfully", "task_id": task.id, "assigned_to": task.assigned_user_id}

@router.post("/{task_id}/status")
def update_task_status(
    task_id: int,
    status_update: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    task = db.query(TaskGrid).filter(TaskGrid.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_status = status_update.status.upper()
    old_status = task.status

    # Define valid transitions
    VALID_TRANSITIONS = {
        "UNASSIGNED": ["ASSIGNED", "IN_PROGRESS"],
        "ASSIGNED": ["IN_PROGRESS", "UNASSIGNED"],
        "IN_PROGRESS": ["SUBMITTED"],
        "SUBMITTED": ["APPROVED", "REVISION_NEEDED"],
        "REVISION_NEEDED": ["IN_PROGRESS", "SUBMITTED"],
        "APPROVED": ["REVISION_NEEDED"],  # Admin/Dosen can reopen
    }

    # Permissions check
    user_role = (current_user.role or "").strip().lower()
    if user_role not in ["admin", "dosen", "supervisi"]:
        if task.assigned_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Hanya dapat mengubah status grid milik sendiri")
        # Contributors can only: IN_PROGRESS->SUBMITTED, REVISION_NEEDED->SUBMITTED
        allowed_contributor = {
            "IN_PROGRESS": ["SUBMITTED"],
            "REVISION_NEEDED": ["SUBMITTED"],
        }
        contributor_allowed = allowed_contributor.get(old_status, [])
        if new_status not in contributor_allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Kontributor hanya dapat submit grid (status saat ini: {old_status})"
            )
    else:
        # Admin or Dosen Reviewer: validate transition is logical
        allowed = VALID_TRANSITIONS.get(old_status, [])
        if new_status not in allowed and new_status != "UNASSIGNED":
            raise HTTPException(
                status_code=400,
                detail=f"Transisi status tidak valid: {old_status} → {new_status}. Transisi yang diperbolehkan: {allowed}"
            )

    task.status = new_status
    task.updated_at = datetime.utcnow()
    if status_update.reviewer_notes is not None:
        task.reviewer_notes = status_update.reviewer_notes
    if new_status == "APPROVED":
        task.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return {"message": f"Status berhasil diubah: {old_status} → {new_status}", "task_id": task.id, "status": task.status}

@router.get("/stats/summary")
def get_project_stats(
    db: Session = Depends(get_db)
) -> Any:
    total_tasks = db.query(func.count(TaskGrid.id)).scalar() or 0
    unassigned = db.query(func.count(TaskGrid.id)).filter(TaskGrid.status == "UNASSIGNED").scalar() or 0
    assigned = db.query(func.count(TaskGrid.id)).filter(TaskGrid.status == "ASSIGNED").scalar() or 0
    in_progress = db.query(func.count(TaskGrid.id)).filter(TaskGrid.status == "IN_PROGRESS").scalar() or 0
    submitted = db.query(func.count(TaskGrid.id)).filter(TaskGrid.status == "SUBMITTED").scalar() or 0
    approved = db.query(func.count(TaskGrid.id)).filter(TaskGrid.status == "APPROVED").scalar() or 0
    revision = db.query(func.count(TaskGrid.id)).filter(TaskGrid.status == "REVISION_NEEDED").scalar() or 0
    total_annotations = db.query(func.count(Annotation.id)).scalar() or 0

    # Stats per student
    students = db.query(User).filter(func.lower(User.role) != "admin").all()
    student_stats = []
    for s in students:
        s_assigned = db.query(func.count(TaskGrid.id)).filter(TaskGrid.assigned_user_id == s.id).scalar() or 0
        s_submitted = db.query(func.count(TaskGrid.id)).filter(TaskGrid.assigned_user_id == s.id, TaskGrid.status == "SUBMITTED").scalar() or 0
        s_approved = db.query(func.count(TaskGrid.id)).filter(TaskGrid.assigned_user_id == s.id, TaskGrid.status == "APPROVED").scalar() or 0
        s_annotations = db.query(func.count(Annotation.id)).filter(Annotation.user_id == s.id).scalar() or 0
        
        student_stats.append({
            "user_id": s.id,
            "name": s.full_name,
            "username": s.username,
            "assigned_tasks": s_assigned,
            "submitted_tasks": s_submitted,
            "approved_tasks": s_approved,
            "total_polygons": s_annotations
        })

    student_stats.sort(key=lambda x: (x["total_polygons"], x["approved_tasks"], x["assigned_tasks"]), reverse=True)

    return {
        "total_tasks": total_tasks,
        "unassigned": unassigned,
        "assigned": assigned,
        "in_progress": in_progress,
        "submitted": submitted,
        "approved": approved,
        "revision_needed": revision,
        "total_polygons": total_annotations,
        "ready_for_dl_export": approved,
        "student_contributions": student_stats
    }
