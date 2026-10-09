from typing import Any, List, Dict, Optional
import json
import os
import math
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from shapely.geometry import shape, mapping, Polygon, MultiPolygon, box
from shapely.ops import unary_union
from shapely.validation import make_valid, explain_validity
from shapely.strtree import STRtree

from app.db.session import get_db
from app.db.models import Annotation, TaskGrid, User, LandCoverClass, TaskReviewPin, GridSnapshot, AuditLog
from app.core.config import settings
from app.api.deps import get_current_user
from app.services.snapshot_service import create_grid_snapshot_from_db, restore_grid_snapshot, log_audit

router = APIRouter()

class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class AnnotationSaveRequest(BaseModel):
    task_grid_id: int
    features: List[GeoJSONFeature]

@router.get("/classes")
def get_classes() -> Any:
    """Returns the 12 standard land cover classes"""
    return settings.LAND_COVER_CLASSES

@router.get("/overview")
def get_annotations_overview(
    study_area_id: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Returns aggregated digitations across all grids with segments by grid, mapper, and land cover class.
    """
    query = db.query(TaskGrid).join(Annotation).distinct()
    if study_area_id:
        query = query.filter(TaskGrid.study_area_id == study_area_id)
    if year:
        query = query.filter(TaskGrid.year == year)
    grids = query.all()

    classes_meta = {c["id"]: c for c in settings.LAND_COVER_CLASSES}

    by_grid = []
    by_mapper_dict = {}
    by_class_dict = {
        c["id"]: {
            "class_id": c["id"],
            "name": c["name"],
            "color": c["color"],
            "count": 0,
            "total_area_ha": 0.0
        } for c in settings.LAND_COVER_CLASSES
    }
    total_polygons = 0
    total_area_sqm = 0.0

    for grid in grids:
        anns = db.query(Annotation).filter(Annotation.task_grid_id == grid.id).all()
        grid_sqm = sum(a.area_sqm or 0 for a in anns)
        total_area_sqm += grid_sqm
        total_polygons += len(anns)

        grid_classes = {}
        for a in anns:
            c_id = a.class_id
            if c_id not in grid_classes:
                grid_classes[c_id] = {
                    "class_id": c_id,
                    "class_name": a.class_name,
                    "color": classes_meta.get(c_id, {}).get("color", "#9CA3AF"),
                    "count": 0,
                    "area_ha": 0.0
                }
            grid_classes[c_id]["count"] += 1
            ha = (a.area_sqm or 0) / 10000.0
            grid_classes[c_id]["area_ha"] += round(ha, 2)

            if c_id in by_class_dict:
                by_class_dict[c_id]["count"] += 1
                by_class_dict[c_id]["total_area_ha"] += round(ha, 2)

            # mapper aggregation
            u_id = a.user_id or (grid.assigned_user_id if grid.assigned_user_id else 0)
            u_name = a.author.full_name if a.author else (grid.assignee.full_name if grid.assignee else "Unknown")
            u_uname = a.author.username if a.author else (grid.assignee.username if grid.assignee else "")
            u_nim = a.author.nim_nip if a.author else (grid.assignee.nim_nip if grid.assignee else "")
            if u_id not in by_mapper_dict:
                by_mapper_dict[u_id] = {
                    "user_id": u_id,
                    "full_name": u_name,
                    "username": u_uname,
                    "nim_nip": u_nim,
                    "grids": set(),
                    "polygon_count": 0,
                    "total_area_ha": 0.0
                }
            by_mapper_dict[u_id]["grids"].add(grid.grid_code)
            by_mapper_dict[u_id]["polygon_count"] += 1
            by_mapper_dict[u_id]["total_area_ha"] += round(ha, 2)

        by_grid.append({
            "task_id": grid.id,
            "grid_code": grid.grid_code,
            "year": grid.year,
            "study_area_id": grid.study_area_id,
            "study_area_name": grid.study_area.name if grid.study_area else "",
            "status": grid.status,
            "assigned_user_id": grid.assigned_user_id,
            "assigned_user_name": grid.assignee.full_name if grid.assignee else "Belum Diambil",
            "assigned_user_username": grid.assignee.username if grid.assignee else "",
            "assigned_user_nim": grid.assignee.nim_nip if grid.assignee else "",
            "annotation_count": len(anns),
            "total_area_ha": round(grid_sqm / 10000.0, 2),
            "min_lat": grid.min_lat,
            "min_lon": grid.min_lon,
            "max_lat": grid.max_lat,
            "max_lon": grid.max_lon,
            "bounds": [[grid.min_lat, grid.min_lon], [grid.max_lat, grid.max_lon]],
            "center": [(grid.min_lat + grid.max_lat)/2.0, (grid.min_lon + grid.max_lon)/2.0],
            "classes": sorted(list(grid_classes.values()), key=lambda x: x["count"], reverse=True)
        })

    by_mapper = []
    for u_id, m in by_mapper_dict.items():
        by_mapper.append({
            "user_id": m["user_id"],
            "full_name": m["full_name"],
            "username": m["username"],
            "nim_nip": m["nim_nip"],
            "grids_count": len(m["grids"]),
            "grids_list": sorted(list(m["grids"])),
            "polygon_count": m["polygon_count"],
            "total_area_ha": round(m["total_area_ha"], 2)
        })
    by_mapper.sort(key=lambda x: x["polygon_count"], reverse=True)

    by_class = []
    for c_id, c in by_class_dict.items():
        if c["count"] > 0:
            c["percentage"] = round((c["count"] / total_polygons * 100.0), 1) if total_polygons > 0 else 0
            by_class.append(c)
    by_class.sort(key=lambda x: x["count"], reverse=True)

    return {
        "summary": {
            "total_annotations": total_polygons,
            "total_grids_digitized": len(by_grid),
            "total_area_ha": round(total_area_sqm / 10000.0, 2)
        },
        "by_grid": sorted(by_grid, key=lambda x: x["annotation_count"], reverse=True),
        "by_mapper": by_mapper,
        "by_class": by_class
    }

@router.get("/all-features")
def get_all_annotations_features(
    study_area_id: Optional[int] = None,
    year: Optional[int] = None,
    task_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Returns a unified GeoJSON FeatureCollection containing all polygons across all digitized grids.
    """
    query = db.query(Annotation).join(TaskGrid)
    if study_area_id:
        query = query.filter(TaskGrid.study_area_id == study_area_id)
    if year:
        query = query.filter(TaskGrid.year == year)
    if task_status:
        query = query.filter(TaskGrid.status == task_status)
        
    annotations = query.all()
    classes_meta = {c["id"]: c for c in settings.LAND_COVER_CLASSES}
    
    features = []
    for ann in annotations:
        try:
            geom = json.loads(ann.geom_geojson)
            tg = ann.task_grid
            c_meta = classes_meta.get(ann.class_id, {})
            features.append({
                "type": "Feature",
                "id": ann.id,
                "geometry": geom,
                "properties": {
                    "id": ann.id,
                    "task_grid_id": ann.task_grid_id,
                    "grid_code": tg.grid_code if tg else "",
                    "year": tg.year if tg else 2025,
                    "task_status": tg.status if tg else "UNKNOWN",
                    "class_id": ann.class_id,
                    "class_name": ann.class_name,
                    "color_hex": c_meta.get("color", "#9CA3AF"),
                    "author_id": ann.user_id,
                    "author_name": ann.author.full_name if ann.author else (tg.assignee.full_name if tg and tg.assignee else "Unknown"),
                    "area_sqm": ann.area_sqm,
                    "area_ha": round((ann.area_sqm or 0) / 10000.0, 2),
                    "created_at": ann.created_at.isoformat() if ann.created_at else None,
                    "bounds": [[tg.min_lat, tg.min_lon], [tg.max_lat, tg.max_lon]] if tg else None
                }
            })
        except Exception:
            continue

    return {
        "type": "FeatureCollection",
        "total_features": len(features),
        "features": features
    }

@router.get("/grid/{task_grid_id}")
def get_grid_annotations(
    task_grid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Returns GeoJSON FeatureCollection containing all polygons for this task grid.
    """
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")
        
    annotations = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).all()
    
    features = []
    for ann in annotations:
        try:
            geom = json.loads(ann.geom_geojson)
            if geom.get("type") in ["MultiPolygon", "GeometryCollection"]:
                s_geom = shape(geom)
                sub_polys = _extract_polygons(s_geom, min_area_sqm=0.1)
                for idx, p in enumerate(sub_polys):
                    p_id = ann.id if idx == 0 else f"{ann.id}_{idx}"
                    features.append({
                        "type": "Feature",
                        "id": p_id,
                        "geometry": mapping(p),
                        "properties": {
                            "id": p_id,
                            "class_id": ann.class_id,
                            "class_name": ann.class_name,
                            "user_id": ann.user_id,
                            "author_name": ann.author.full_name if ann.author else "Unknown",
                            "area_sqm": p.area * (111320.0 ** 2),
                            "created_at": ann.created_at.isoformat() if ann.created_at else None
                        }
                    })
            else:
                features.append({
                    "type": "Feature",
                    "id": ann.id,
                    "geometry": geom,
                    "properties": {
                        "id": ann.id,
                        "class_id": ann.class_id,
                        "class_name": ann.class_name,
                        "user_id": ann.user_id,
                        "author_name": ann.author.full_name if ann.author else "Unknown",
                        "area_sqm": ann.area_sqm,
                        "created_at": ann.created_at.isoformat() if ann.created_at else None
                    }
                })
        except Exception:
            continue
        
    return {
        "type": "FeatureCollection",
        "task_grid_id": task_grid_id,
        "grid_code": task.grid_code,
        "features": features
    }

@router.get("/grid/{task_grid_id}/neighbors-features")
def get_neighbors_annotations(
    task_grid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Returns a GeoJSON FeatureCollection of polygons from neighboring task grids
    for edge-matching and border alignment. Read-only for mapper.
    """
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")

    # Buffer around current task's bbox (1.5x grid extent to catch all surrounding neighbors)
    d_lat = abs(task.max_lat - task.min_lat) * 1.5 if (task.max_lat and task.min_lat) else 0.05
    d_lon = abs(task.max_lon - task.min_lon) * 1.5 if (task.max_lon and task.min_lon) else 0.05

    min_lat_b = task.min_lat - d_lat
    max_lat_b = task.max_lat + d_lat
    min_lon_b = task.min_lon - d_lon
    max_lon_b = task.max_lon + d_lon

    # Query neighboring grids in the same study area and year
    neighbor_tasks = db.query(TaskGrid).filter(
        TaskGrid.id != task_grid_id,
        TaskGrid.study_area_id == task.study_area_id,
        TaskGrid.year == task.year,
        TaskGrid.min_lat <= max_lat_b,
        TaskGrid.max_lat >= min_lat_b,
        TaskGrid.min_lon <= max_lon_b,
        TaskGrid.max_lon >= min_lon_b
    ).all()

    if not neighbor_tasks:
        return {
            "type": "FeatureCollection",
            "total_features": 0,
            "features": []
        }

    neighbor_ids = [t.id for t in neighbor_tasks]
    neighbor_code_map = {t.id: t.grid_code for t in neighbor_tasks}

    # Fetch annotations from these neighboring grids (exclude unclassified class 0)
    annotations = db.query(Annotation).filter(
        Annotation.task_grid_id.in_(neighbor_ids),
        Annotation.class_id > 0
    ).all()

    classes_meta = {c["id"]: c for c in settings.LAND_COVER_CLASSES}
    features = []
    for ann in annotations:
        try:
            geom = json.loads(ann.geom_geojson)
            c_meta = classes_meta.get(ann.class_id, {})
            features.append({
                "type": "Feature",
                "id": f"neighbor_{ann.id}",
                "geometry": geom,
                "properties": {
                    "id": ann.id,
                    "task_grid_id": ann.task_grid_id,
                    "grid_code": neighbor_code_map.get(ann.task_grid_id, ""),
                    "class_id": ann.class_id,
                    "class_name": ann.class_name,
                    "color_hex": c_meta.get("color", "#9CA3AF"),
                    "area_ha": round((ann.area_sqm or 0) / 10000.0, 2),
                    "is_neighbor": True
                }
            })
        except Exception:
            continue

    return {
        "type": "FeatureCollection",
        "total_features": len(features),
        "features": features
    }

@router.post("/grid/{task_grid_id}")
def save_grid_annotations(
    task_grid_id: int,
    data: AnnotationSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Saves/syncs the polygons for the specified task grid.
    """
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")

    # Lock task row with row-level lock to prevent concurrent save race condition inflation
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).with_for_update().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")

    user_role = (current_user.role or "").strip().lower()
    if task.assigned_user_id is not None and user_role not in ["admin", "dosen"] and task.assigned_user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail=f"Grid ini telah ditugaskan ke {task.assignee.full_name if task.assignee else 'pengguna lain'}. Anda tidak dapat mengubah data pada grid ini."
        )

    # Auto-claim unassigned grid if annotator begins digitizing it
    if task.assigned_user_id is None:
        task.assigned_user_id = current_user.id
        task.status = "IN_PROGRESS"

    existing_count = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).count()
    if len(data.features) == 0 and existing_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Ditolak: Permintaan simpan kosong (0 fitur) sementara grid memiliki {existing_count} poligon tersimpan di server. Aksi dibatalkan untuk mencegah kehilangan data."
        )

    # Clear previous annotations for this grid to sync cleanly (safeguard review pins)
    db.query(TaskReviewPin).filter(TaskReviewPin.task_grid_id == task_grid_id).update({"annotation_id": None}, synchronize_session=False)
    db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).delete()
    
    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}

    new_annotations = []
    seen_geom_keys = set()

    for f in data.features:
        class_id = int(f.properties.get("class_id", 1))
        class_name = f.properties.get("class_name", classes_dict.get(class_id, "Unknown"))
        
        geom_dict = f.geometry
        try:
            s_geom = shape(geom_dict)
            # STRICT SINGLEPART GUARANTEE:
            # Explode any MultiPolygon or GeometryCollection into distinct Polygon objects
            extracted_polys = _extract_polygons(s_geom, min_area_sqm=0.1)
            if not extracted_polys:
                continue

            for poly_part in extracted_polys:
                part_geojson = mapping(poly_part)
                # Deduplication key based on normalized coordinate structure
                geom_key = json.dumps(part_geojson, sort_keys=True)
                if geom_key in seen_geom_keys:
                    continue
                seen_geom_keys.add(geom_key)

                area_sqm = poly_part.area * (111320.0 ** 2)
                ann = Annotation(
                    task_grid_id=task_grid_id,
                    user_id=current_user.id,
                    class_id=class_id,
                    class_name=class_name,
                    geom_geojson=json.dumps(part_geojson),
                    area_sqm=area_sqm
                )
                db.add(ann)
                new_annotations.append(ann)
        except Exception:
            continue
        
    # Auto mark task as IN_PROGRESS if it was ASSIGNED or UNASSIGNED
    if task.status in ["ASSIGNED", "REVISION_NEEDED", "UNASSIGNED"]:
        task.status = "IN_PROGRESS"
        if task.assigned_user_id is None:
            task.assigned_user_id = current_user.id
        
    db.commit()

    # Automatically record version snapshot & audit log
    if len(new_annotations) > 0:
        create_grid_snapshot_from_db(
            db=db,
            task_grid_id=task_grid_id,
            user_id=current_user.id,
            note="Draf Disimpan"
        )
        log_audit(
            db=db,
            user_id=current_user.id,
            action="SAVE_ANNOTATIONS",
            entity_type="task_grid",
            entity_id=task_grid_id,
            task_grid_id=task_grid_id,
        )

    saved_features = []
    for ann in new_annotations:
        saved_features.append({
            "type": "Feature",
            "id": ann.id,
            "geometry": json.loads(ann.geom_geojson),
            "properties": {
                "id": ann.id,
                "class_id": ann.class_id,
                "class_name": ann.class_name,
                "user_id": ann.user_id,
                "area_sqm": ann.area_sqm
            }
        })

    return {
        "message": f"Successfully saved {len(new_annotations)} annotation polygons",
        "count": len(new_annotations),
        "saved_features": saved_features
    }

@router.get("/grid/{task_grid_id}/snapshots")
def get_grid_snapshots(
    task_grid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Returns list of version snapshots for a task grid."""
    snapshots = (
        db.query(GridSnapshot)
        .filter(GridSnapshot.task_grid_id == task_grid_id)
        .order_by(GridSnapshot.version_number.desc())
        .all()
    )
    res = []
    for s in snapshots:
        author_name = s.author.full_name if s.author else (s.author.username if s.author else "Sistem")
        res.append({
            "id": s.id,
            "task_grid_id": s.task_grid_id,
            "version_number": s.version_number,
            "note": s.note,
            "features_count": s.features_count,
            "user_id": s.user_id,
            "author_name": author_name,
            "created_at": s.created_at
        })
    return res

@router.get("/grid/{task_grid_id}/snapshots/{snapshot_id}")
def get_grid_snapshot_detail(
    task_grid_id: int,
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Returns full details of a snapshot including GeoJSON payload for inspection or diffing."""
    s = db.query(GridSnapshot).filter(
        GridSnapshot.id == snapshot_id,
        GridSnapshot.task_grid_id == task_grid_id
    ).first()
    if not s:
        raise HTTPException(status_code=404, detail="Snapshot tidak ditemukan.")
    
    author_name = s.author.full_name if s.author else "Sistem"
    try:
        geo = json.loads(s.geojson_data)
    except Exception:
        geo = {"type": "FeatureCollection", "features": []}

    return {
        "id": s.id,
        "task_grid_id": s.task_grid_id,
        "version_number": s.version_number,
        "note": s.note,
        "features_count": s.features_count,
        "user_id": s.user_id,
        "author_name": author_name,
        "created_at": s.created_at,
        "geojson_data": geo
    }

@router.post("/grid/{task_grid_id}/snapshots/{snapshot_id}/restore")
def restore_snapshot_endpoint(
    task_grid_id: int,
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Restores annotations of a grid back to the specified version snapshot."""
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")

    user_role = (current_user.role or "").strip().lower()
    if task.assigned_user_id is not None and user_role not in ["admin", "dosen"] and task.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Hanya penanggung jawab grid, dosen, atau admin yang dapat memulihkan versi.")

    try:
        result = restore_grid_snapshot(
            db=db,
            task_grid_id=task_grid_id,
            snapshot_id=snapshot_id,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memulihkan snapshot: {e}")

@router.get("/audit-logs")
def get_audit_logs(
    task_grid_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Returns recent system audit logs."""
    q = db.query(AuditLog).order_by(AuditLog.id.desc())
    if task_grid_id:
        q = q.filter(AuditLog.task_grid_id == task_grid_id)
    if action:
        q = q.filter(AuditLog.action == action)
    logs = q.limit(min(limit, 200)).all()
    
    return [
        {
            "id": l.id,
            "user_id": l.user_id,
            "user_name": l.user.full_name if l.user else "Sistem",
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "task_grid_id": l.task_grid_id,
            "details": l.details,
            "ip_address": l.ip_address,
            "created_at": l.created_at
        }
        for l in logs
    ]


@router.post("/grid/{task_grid_id}/copy-from/{source_task_id}")
def copy_annotations_from_task(
    task_grid_id: int,
    source_task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Copies all polygon annotations from source_task_id (e.g. year 2017) to task_grid_id (e.g. year 2025).
    """
    target_task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not target_task:
        raise HTTPException(status_code=404, detail="Target task grid not found")
        
    source_task = db.query(TaskGrid).filter(TaskGrid.id == source_task_id).first()
    if not source_task:
        raise HTTPException(status_code=404, detail="Source task grid not found")
        
    user_role = (current_user.role or "").strip().lower()
    if user_role not in ["admin", "dosen"] and target_task.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this task")

    source_annotations = db.query(Annotation).filter(Annotation.task_grid_id == source_task_id).all()
    if not source_annotations:
        raise HTTPException(status_code=400, detail="Grid sumber tidak memiliki poligon anotasi untuk disalin")

    # Clear existing target annotations
    db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).delete()

    cloned = []
    for sa in source_annotations:
        new_ann = Annotation(
            task_grid_id=task_grid_id,
            user_id=current_user.id,
            class_id=sa.class_id,
            class_name=sa.class_name,
            geom_geojson=sa.geom_geojson,
            area_sqm=sa.area_sqm
        )
        db.add(new_ann)
        cloned.append(new_ann)

    if target_task.status in ["UNASSIGNED", "ASSIGNED", "REVISION_NEEDED"]:
        target_task.status = "IN_PROGRESS"
        if target_task.assigned_user_id is None:
            target_task.assigned_user_id = current_user.id

    db.commit()
    return {
        "message": f"Berhasil menyalin {len(cloned)} poligon anotasi dari grid {source_task.grid_code} ({source_task.year})!",
        "count": len(cloned)
    }

@router.post("/grid/{task_grid_id}/init-base")
def init_base_polygon(
    task_grid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Creates a single 'Belum Terklasifikasi' polygon covering the entire grid bounding box.
    This is the starting point for the cut-polygon semantic segmentation workflow.
    Only works when the grid has NO existing annotations.
    """
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")
    
    user_role = (current_user.role or "").strip().lower()
    if user_role not in ["admin", "dosen"] and task.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Grid ini bukan milik Anda")

    existing_count = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).count()
    if existing_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Grid sudah memiliki {existing_count} poligon anotasi. Init base hanya untuk grid kosong."
        )

    # Create full-grid polygon
    base_geom = {
        "type": "Polygon",
        "coordinates": [[
            [task.min_lon, task.min_lat],
            [task.max_lon, task.min_lat],
            [task.max_lon, task.max_lat],
            [task.min_lon, task.max_lat],
            [task.min_lon, task.min_lat]
        ]]
    }

    # Calculate approximate area
    try:
        s_geom = shape(base_geom)
        area_sqm = s_geom.area * (111320.0 ** 2)
    except Exception:
        area_sqm = 0.0

    base_cname = settings.LAND_COVER_CLASSES[0]["name"] if settings.LAND_COVER_CLASSES else "Belum Teridentifikasi"
    base_ann = Annotation(
        task_grid_id=task_grid_id,
        user_id=current_user.id,
        class_id=0,
        class_name=base_cname,
        geom_geojson=json.dumps(base_geom),
        area_sqm=area_sqm
    )
    db.add(base_ann)

    # Auto-set task to IN_PROGRESS if still ASSIGNED or UNASSIGNED
    if task.status in ["ASSIGNED", "UNASSIGNED"]:
        task.status = "IN_PROGRESS"
        if task.assigned_user_id is None:
            task.assigned_user_id = current_user.id

    db.commit()
    db.refresh(base_ann)
    return {
        "message": "Base polygon 'Belum Teridentifikasi' berhasil dibuat menutupi seluruh area grid",
        "annotation_id": base_ann.id,
        "area_sqm": base_ann.area_sqm
    }


@router.post("/grid/{task_grid_id}/validate-topology")
def validate_topology(
    task_grid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Validates topology of all annotation polygons in a grid:
    1. Self-intersection check per polygon (Shapely is_valid)
    2. Overlap detection between polygons (pairwise intersection area)
    3. Gap detection (union of all polygons vs grid bounding box)
    4. Coverage percentage
    5. Check for remaining 'Belum Teridentifikasi' polygons
    """
    from shapely.geometry import box
    from shapely.ops import unary_union
    from shapely.validation import explain_validity

    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")

    annotations = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).all()
    if not annotations:
        return {
            "valid": False,
            "coverage_percent": 0.0,
            "errors": [{"type": "NO_ANNOTATIONS", "message": "Belum ada poligon anotasi di grid ini"}],
            "warnings": [],
            "polygon_count": 0
        }

    # Build grid bounding box as Shapely geometry
    grid_box = box(task.min_lon, task.min_lat, task.max_lon, task.max_lat)
    grid_area = grid_box.area

    errors = []
    warnings = []
    shapely_polygons = []
    unclassified_ids = []

    for ann in annotations:
        try:
            geom_dict = json.loads(ann.geom_geojson)
            s_geom = shape(geom_dict)
        except Exception as e:
            errors.append({
                "type": "INVALID_GEOM",
                "annotation_id": ann.id,
                "class_name": ann.class_name,
                "message": f"Geometri tidak valid: {str(e)}"
            })
            continue

        # 1. Self-intersection / validity check
        if not s_geom.is_valid:
            reason = explain_validity(s_geom)
            errors.append({
                "type": "SELF_INTERSECTION",
                "annotation_id": ann.id,
                "class_name": ann.class_name,
                "geometry": mapping(s_geom),
                "message": f"Poligon #{ann.id} memiliki geometri tidak valid: {reason}"
            })
            # Try to fix for further analysis
            try:
                s_geom = s_geom.buffer(0)
            except Exception:
                continue

        shapely_polygons.append({"geom": s_geom, "ann": ann})

        # 5. Check for unclassified
        if ann.class_id == 0:
            unclassified_ids.append(ann.id)

    # 2. Overlap detection with STRtree spatial index (10x-100x faster than O(N^2))
    # 1 deg ~ 111320 meters, 1 sq meter ~ 8.07e-11 deg²
    SQM_TO_DEG2 = 1.0 / (111320.0 ** 2)
    ERROR_OVERLAP_THRESHOLD = 3.0 * SQM_TO_DEG2   # Overlaps >= 3.0 m² are blocking errors
    WARNING_OVERLAP_THRESHOLD = 0.5 * SQM_TO_DEG2 # Overlaps 0.5 - 3.0 m² are non-blocking micro-slivers

    valid_polys = [sp for sp in shapely_polygons if sp["geom"].is_valid and not sp["geom"].is_empty]
    
    if len(valid_polys) > 1:
        geoms_list = [sp["geom"] for sp in valid_polys]
        tree = STRtree(geoms_list)
        candidate_pairs = tree.query(geoms_list, predicate="intersects")

        overlap_count = 0
        MAX_DISPLAY_ERRORS = 100

        for i, j in zip(candidate_pairs[0], candidate_pairs[1]):
            if i < j:
                try:
                    inter = geoms_list[i].intersection(geoms_list[j])
                    if inter.area > ERROR_OVERLAP_THRESHOLD:
                        overlap_count += 1
                        if len(errors) < MAX_DISPLAY_ERRORS:
                            overlap_pct = (inter.area / grid_area) * 100
                            overlap_sqm = inter.area * (111320.0 ** 2)
                            ann_i = valid_polys[i]["ann"]
                            ann_j = valid_polys[j]["ann"]
                            errors.append({
                                "type": "OVERLAP",
                                "annotation_ids": [ann_i.id, ann_j.id],
                                "class_names": [ann_i.class_name, ann_j.class_name],
                                "area_sqm": round(overlap_sqm, 2),
                                "geometry": mapping(inter),
                                "message": f"Tumpang tindih {round(overlap_sqm, 1)} m² ({overlap_pct:.4f}% dari grid) antara poligon #{ann_i.id} ({ann_i.class_name}) dan #{ann_j.id} ({ann_j.class_name})"
                            })
                    elif inter.area > WARNING_OVERLAP_THRESHOLD:
                        overlap_sqm = inter.area * (111320.0 ** 2)
                        ann_i = valid_polys[i]["ann"]
                        ann_j = valid_polys[j]["ann"]
                        warnings.append({
                            "type": "MICRO_OVERLAP",
                            "annotation_ids": [ann_i.id, ann_j.id],
                            "area_sqm": round(overlap_sqm, 2),
                            "geometry": mapping(inter),
                            "message": f"Tumpang tindih mikro tepi {round(overlap_sqm, 2)} m² antara #{ann_i.id} dan #{ann_j.id} (toleransi digitasi wajar)"
                        })
                except Exception:
                    pass

        if overlap_count > MAX_DISPLAY_ERRORS:
            warnings.append({
                "type": "OVERLAP_OVERFLOW",
                "message": f"Ditemukan total {overlap_count} tumpang tindih. Menampilkan {MAX_DISPLAY_ERRORS} masalah pertama untuk efisiensi tampilan."
            })

    # 3 & 4. Gap detection and coverage
    coverage_percent = 0.0
    try:
        all_geoms = [sp["geom"] for sp in shapely_polygons if sp["geom"].is_valid]
        if all_geoms:
            union_geom = unary_union(all_geoms)
            # Clip to grid bounds
            covered = union_geom.intersection(grid_box)
            coverage_percent = (covered.area / grid_area) * 100 if grid_area > 0 else 0
            coverage_percent = min(coverage_percent, 100.0)

            gap_area = grid_box.difference(covered)
            if gap_area.area > ERROR_OVERLAP_THRESHOLD:
                gap_pct = (gap_area.area / grid_area) * 100
                gap_sqm = gap_area.area * (111320.0 ** 2)
                if gap_pct > 5.0:
                    errors.append({
                        "type": "GAP",
                        "area_sqm": round(gap_sqm, 2),
                        "geometry": mapping(gap_area),
                        "message": f"Area kosong (gap) terdeteksi: {gap_pct:.2f}% dari grid ({round(gap_sqm, 1)} m²) belum tercakup poligon"
                    })
                elif gap_pct > 0.5:
                    warnings.append({
                        "type": "SMALL_GAP",
                        "area_sqm": round(gap_sqm, 2),
                        "geometry": mapping(gap_area),
                        "message": f"Area kosong kecil terdeteksi: {gap_pct:.2f}% dari grid ({round(gap_sqm, 1)} m²) — pertimbangkan untuk menutup celah"
                    })
    except Exception as e:
        warnings.append({
            "type": "COVERAGE_CALC_ERROR",
            "message": f"Gagal menghitung cakupan: {str(e)}"
        })

    # Unclassified polygons ("Belum Teridentifikasi" id=0): Informational warning so topology passes
    if unclassified_ids:
        warnings.append({
            "type": "UNCLASSIFIED",
            "annotation_ids": unclassified_ids,
            "message": f"{len(unclassified_ids)} poligon berstatus 'Belum Teridentifikasi'. Topologi tetap valid namun pastikan kelas diassign sebelum finalisasi."
        })

    is_valid = len(errors) == 0

    return {
        "valid": is_valid,
        "coverage_percent": round(coverage_percent, 2),
        "polygon_count": len(annotations),
        "errors": errors,
        "warnings": warnings
    }


class AutoHealOptionsRequest(BaseModel):
    remove_duplicates: bool = True
    heal_geometries: bool = True
    clip_overlaps: bool = True
    overlap_priority: str = "smaller_first"  # "smaller_first", "larger_first", "specific_class_first"
    remove_slivers: bool = True
    min_sliver_area_sqm: float = 0.5
    fill_gaps: bool = False
    fill_gap_class_id: int = 0


@router.post("/grid/{task_grid_id}/auto-heal-topology")
def auto_heal_topology(
    task_grid_id: int,
    options: Optional[AutoHealOptionsRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Auto-heals topological errors in a task grid with configurable options:
    1. Removes ghost/duplicate overlapping polygons (> 90% overlap area).
    2. Removes degenerate zero-area / micro-sliver polygons (< min_sliver_area_sqm).
    3. Heals invalid geometries with Shapely make_valid / buffer(0) (resolves self-intersections and collapsed components).
    4. Removes zero-area / degenerate collapsed line holes from polygon interiors.
    5. Clips overlapping boundaries based on selectable priority.
    6. Optionally fills residual empty gaps with a specified land cover class.
    """
    from shapely.geometry import shape, mapping, Polygon, box
    from shapely.validation import make_valid
    from shapely.ops import unary_union
    
    if options is None:
        options = AutoHealOptionsRequest()
        
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")

    annotations = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).all()
    if not annotations:
        return {"message": "Tidak ada poligon untuk diperbaiki", "healed_count": 0, "removed_count": 0, "duplicate_count": 0, "clipped_count": 0, "gaps_filled_count": 0}

    # 0. Safety snapshot before modifying geometries
    create_grid_snapshot_from_db(
        db=db,
        task_grid_id=task_grid_id,
        user_id=current_user.id,
        note="Sebelum Auto-Heal QC"
    )

    healed_count = 0
    removed_count = 0
    duplicate_count = 0
    clipped_count = 0
    gaps_filled_count = 0
    
    min_area_deg = (max(0.01, options.min_sliver_area_sqm) / (111320.0 ** 2))

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1: Eliminate exact/near-exact duplicate overlapping polygons (> 90%)
    # ─────────────────────────────────────────────────────────────────────────
    if options.remove_duplicates:
        seen_geoms = []
        duplicate_ids = set()

        for ann in annotations:
            try:
                geom_dict = json.loads(ann.geom_geojson)
                s_geom = shape(geom_dict)
            except Exception:
                continue

            if s_geom.is_empty or s_geom.area < min_area_deg:
                continue

            is_dup = False
            for idx, (sg, s_ann) in enumerate(seen_geoms):
                area_ratio = min(ann.area_sqm, s_ann.area_sqm) / max(ann.area_sqm, s_ann.area_sqm) if max(ann.area_sqm, s_ann.area_sqm) > 0 else 0
                if area_ratio > 0.85:
                    try:
                        inter_area = s_geom.intersection(sg).area
                        if (inter_area / s_geom.area) > 0.90 and (inter_area / sg.area) > 0.90:
                            is_dup = True
                            # Priority: prefer specific class over generic "Belum Teridentifikasi" (id=0) or base "Hutan Lahan Kering" (id=1)
                            if s_ann.class_id in [0, 1] and ann.class_id not in [0, 1]:
                                duplicate_ids.add(s_ann.id)
                                seen_geoms[idx] = (s_geom, ann)
                            else:
                                duplicate_ids.add(ann.id)
                            break
                    except Exception:
                        pass

            if not is_dup:
                seen_geoms.append((s_geom, ann))

        if duplicate_ids:
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id.in_(duplicate_ids)).update({"annotation_id": None}, synchronize_session=False)
            db.query(Annotation).filter(Annotation.id.in_(duplicate_ids)).delete(synchronize_session=False)
            duplicate_count = len(duplicate_ids)
            removed_count += duplicate_count
            annotations = [a for a in annotations if a.id not in duplicate_ids]

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 2: Heal invalid geometries, micro-slivers, and degenerate holes
    # ─────────────────────────────────────────────────────────────────────────
    ann_map = {a.id: a for a in annotations}
    working_list = []

    for ann in annotations:
        try:
            geom_dict = json.loads(ann.geom_geojson)
            s_geom = shape(geom_dict)
        except Exception:
            # Unparseable geometry: detach pins and delete
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann.id).update({"annotation_id": None}, synchronize_session=False)
            db.delete(ann)
            ann_map.pop(ann.id, None)
            removed_count += 1
            continue

        # Check for zero area or sliver/thin ribbon
        area_sqm = s_geom.area * (111320.0 ** 2)
        perim_m = s_geom.length * 111320.0
        avg_thickness_m = area_sqm / (perim_m / 2.0) if perim_m > 0 else 0
        is_sliver = (options.remove_slivers and (s_geom.area < min_area_deg or (area_sqm < 60.0 and avg_thickness_m < 0.5)))

        if s_geom.is_empty:
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann.id).update({"annotation_id": None}, synchronize_session=False)
            db.delete(ann)
            ann_map.pop(ann.id, None)
            removed_count += 1
            continue

        if is_sliver:
            # Instead of leaving a hole/void, absorb sliver into adjacent neighbor
            s_buff = s_geom.buffer(1.5e-6)
            best_neighbor = None
            best_len = -1
            for other_ann in annotations:
                if other_ann.id == ann.id or other_ann.id not in ann_map:
                    continue
                try:
                    o_geom = shape(json.loads(other_ann.geom_geojson))
                    if s_geom.intersects(o_geom) or s_buff.intersects(o_geom):
                        inter = s_buff.intersection(o_geom)
                        score = inter.length if inter.length > 0 else inter.area
                        if score > best_len:
                            best_len = score
                            best_neighbor = other_ann
                except Exception:
                    pass

            if best_neighbor:
                try:
                    o_geom = shape(json.loads(best_neighbor.geom_geojson))
                    merged = unary_union([o_geom.buffer(1.5e-6), s_geom.buffer(1.5e-6)]).buffer(-1.5e-6)
                    merged = make_valid(merged)
                    extracted = _extract_polygons(merged)
                    if extracted:
                        best_neighbor.geom_geojson = json.dumps(mapping(extracted[0]))
                        best_neighbor.area_sqm = extracted[0].area * (111320.0 ** 2)
                        db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann.id).update({"annotation_id": None}, synchronize_session=False)
                        db.delete(ann)
                        ann_map.pop(ann.id, None)
                        removed_count += 1
                        healed_count += 1
                        continue
                except Exception:
                    pass

            # If isolated floating sliver with no neighbor, delete it
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann.id).update({"annotation_id": None}, synchronize_session=False)
            db.delete(ann)
            ann_map.pop(ann.id, None)
            removed_count += 1
            continue

        was_healed = False
        # If invalid (e.g. self-intersection, too few points)
        if options.heal_geometries and not s_geom.is_valid:
            try:
                s_geom = make_valid(s_geom)
                was_healed = True
            except Exception:
                try:
                    s_geom = s_geom.buffer(0)
                    was_healed = True
                except Exception:
                    pass

        # If it has degenerate holes, clean them
        if options.heal_geometries and s_geom.geom_type == 'Polygon' and len(s_geom.interiors) > 0:
            cleaned_holes = [h for h in s_geom.interiors if Polygon(h).area > 1e-9]
            if len(cleaned_holes) != len(s_geom.interiors):
                s_geom = Polygon(s_geom.exterior, cleaned_holes)
                was_healed = True

        effective_min_sqm = max(3.0, options.min_sliver_area_sqm) if options.remove_slivers else 2.0
        extracted = _extract_polygons(s_geom, min_area_sqm=effective_min_sqm)
        if not extracted:
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann.id).update({"annotation_id": None}, synchronize_session=False)
            db.delete(ann)
            ann_map.pop(ann.id, None)
            removed_count += 1
            continue

        if was_healed:
            healed_count += 1

        working_list.append({
            "ann": ann,
            "geom": extracted[0],
            "area_sqm": extracted[0].area * (111320.0 ** 2),
            "was_modified": was_healed or (extracted[0].wkt != s_geom.wkt)
        })

        for extra_p in extracted[1:]:
            extra_sqm = extra_p.area * (111320.0 ** 2)
            if extra_sqm >= 3.0:
                new_ann = Annotation(
                    task_grid_id=task_grid_id,
                    user_id=ann.user_id,
                    class_id=ann.class_id,
                    class_name=ann.class_name,
                    geom_geojson=json.dumps(mapping(extra_p)),
                    area_sqm=extra_sqm
                )
                db.add(new_ann)
                db.flush()
                working_list.append({
                    "ann": new_ann,
                    "geom": extra_p,
                    "area_sqm": extra_sqm,
                    "was_modified": True
                })
                healed_count += 1

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 3: Auto-Clip Overlaps (Boundary Clashing & Subtraction)
    # ─────────────────────────────────────────────────────────────────────────
    accepted_list = []
    if options.clip_overlaps:
        # Priority sorting:
        if options.overlap_priority == "larger_first":
            working_list.sort(key=lambda x: (1 if x["ann"].class_id in [0, 1] else 0, -x["area_sqm"]))
        elif options.overlap_priority == "specific_class_first":
            working_list.sort(key=lambda x: 1 if x["ann"].class_id in [0, 1] else 0)
        else: # "smaller_first" (default)
            working_list.sort(key=lambda x: (1 if x["ann"].class_id in [0, 1] else 0, x["area_sqm"]))

        clip_thresh = 2.0 / (111320.0 ** 2)
        for item in working_list:
            cur_geom = item["geom"]
            cur_ann = item["ann"]
            was_clipped = False

            for accepted in accepted_list:
                if not cur_geom.is_empty and cur_geom.intersects(accepted["geom"]):
                    try:
                        inter = cur_geom.intersection(accepted["geom"])
                        if inter.area > clip_thresh:
                            cur_geom = cur_geom.difference(accepted["geom"])
                            cur_geom = make_valid(cur_geom)
                            was_clipped = True
                            clipped_count += 1
                    except Exception:
                        pass

            effective_min_sqm = max(3.0, options.min_sliver_area_sqm) if options.remove_slivers else 2.0
            extracted = _extract_polygons(cur_geom, min_area_sqm=effective_min_sqm)
            if not extracted:
                # Completely enveloped redundant polygon
                db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == cur_ann.id).update({"annotation_id": None}, synchronize_session=False)
                db.delete(cur_ann)
                removed_count += 1
            else:
                p0 = extracted[0]
                if was_clipped or item["was_modified"] or p0.wkt != item["geom"].wkt:
                    cur_ann.geom_geojson = json.dumps(mapping(p0))
                    cur_ann.area_sqm = p0.area * (111320.0 ** 2)

                accepted_list.append({
                    "ann": cur_ann,
                    "geom": p0,
                    "area_sqm": p0.area * (111320.0 ** 2)
                })

                for extra_p in extracted[1:]:
                    extra_sqm = extra_p.area * (111320.0 ** 2)
                    if extra_sqm >= 3.0:
                        new_ann = Annotation(
                            task_grid_id=task_grid_id,
                            user_id=cur_ann.user_id,
                            class_id=cur_ann.class_id,
                            class_name=cur_ann.class_name,
                            geom_geojson=json.dumps(mapping(extra_p)),
                            area_sqm=extra_sqm
                        )
                        db.add(new_ann)
                        db.flush()
                        accepted_list.append({
                            "ann": new_ann,
                            "geom": extra_p,
                            "area_sqm": extra_sqm
                        })
    else:
        for item in working_list:
            if item["was_modified"]:
                item["ann"].geom_geojson = json.dumps(mapping(item["geom"]))
                item["ann"].area_sqm = item["area_sqm"]
            accepted_list.append(item)

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 4: Fill Residual Empty Gaps (Optional)
    # ─────────────────────────────────────────────────────────────────────────
    if options.fill_gaps and accepted_list:
        try:
            grid_box = box(task.min_lon, task.min_lat, task.max_lon, task.max_lat)
            all_valid = [it["geom"] for it in accepted_list if not it["geom"].is_empty and it["geom"].is_valid]
            if all_valid:
                union_all = unary_union(all_valid)
                gap_geom = grid_box.difference(union_all)
                gap_polys = _extract_polygons(gap_geom, min_area_sqm=max(0.5, options.min_sliver_area_sqm))
                
                classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}
                gap_cid = options.fill_gap_class_id if options.fill_gap_class_id in classes_dict else 0
                gap_cname = classes_dict.get(gap_cid, "Belum Teridentifikasi")
                
                for gp in gap_polys:
                    new_gap_ann = Annotation(
                        task_grid_id=task_grid_id,
                        user_id=current_user.id,
                        class_id=gap_cid,
                        class_name=gap_cname,
                        geom_geojson=json.dumps(mapping(gp)),
                        area_sqm=gp.area * (111320.0 ** 2)
                    )
                    db.add(new_gap_ann)
                    gaps_filled_count += 1
        except Exception as e:
            pass

    db.commit()

    msg_parts = []
    if duplicate_count > 0:
        msg_parts.append(f"{duplicate_count} duplikat layer dihapus")
    if clipped_count > 0:
        msg_parts.append(f"{clipped_count} irisan overlap dipotong rapi")
    if healed_count > 0:
        msg_parts.append(f"{healed_count} geometri diperbaiki")
    if (removed_count - duplicate_count) > 0:
        msg_parts.append(f"{removed_count - duplicate_count} serpihan dibersihkan")
    if gaps_filled_count > 0:
        msg_parts.append(f"{gaps_filled_count} celah kosong diisi")

    msg = "Berhasil merapikan topologi! " + (", ".join(msg_parts) if msg_parts else "Semua poligon valid.")

    # Record snapshot of the healed state & audit log
    create_grid_snapshot_from_db(
        db=db,
        task_grid_id=task_grid_id,
        user_id=current_user.id,
        note="Hasil Auto-Heal QC"
    )
    log_audit(
        db=db,
        user_id=current_user.id,
        action="AUTO_HEAL",
        entity_type="task_grid",
        entity_id=task_grid_id,
        task_grid_id=task_grid_id,
        details=json.dumps({"healed": healed_count, "duplicates": duplicate_count, "clipped": clipped_count, "gaps": gaps_filled_count})
    )

    return {
        "message": msg,
        "healed_count": healed_count,
        "removed_count": removed_count,
        "duplicate_count": duplicate_count,
        "clipped_count": clipped_count,
        "gaps_filled_count": gaps_filled_count
    }


@router.post("/grid/{task_grid_id}/clean-slivers")
def clean_slivers_endpoint(
    task_grid_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Specifically detects and absorbs all razor-thin slivers and micro-ribbons (< 60m² or thickness < 50cm)
    into their adjacent neighboring polygons with the longest shared boundary.
    Leaves NO gaps, voids, or holes behind.
    """
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")

    annotations = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).all()
    if not annotations:
        return {"message": "Tidak ada poligon untuk dibersihkan.", "absorbed_count": 0}

    # Create safety backup snapshot
    create_grid_snapshot_from_db(
        db=db,
        task_grid_id=task_grid_id,
        user_id=current_user.id,
        note="Sebelum Pembersihan Sliver Otomatis"
    )

    slivers = []
    regulars = []

    for a in annotations:
        try:
            geom = shape(json.loads(a.geom_geojson))
            if not geom.is_valid:
                geom = make_valid(geom)
            area_sqm = a.area_sqm or (geom.area * (111320.0 ** 2))
            perim_m = geom.length * 111320.0
            avg_thickness_m = area_sqm / (perim_m / 2.0) if perim_m > 0 else 0
            if area_sqm < 60.0 and avg_thickness_m < 0.5:
                slivers.append({"ann": a, "geom": geom, "area": area_sqm})
            else:
                regulars.append({"ann": a, "geom": geom, "area": area_sqm})
        except Exception:
            continue

    if not slivers:
        return {"message": "Tidak ditemukan poligon sliver / garis tipis pada grid ini.", "absorbed_count": 0}

    absorbed_count = 0
    for s in slivers:
        s_buff = s["geom"].buffer(1.5e-6)
        best_r = None
        best_score = -1
        for r in regulars:
            if s["geom"].intersects(r["geom"]) or s_buff.intersects(r["geom"]):
                inter = s_buff.intersection(r["geom"])
                score = inter.length if inter.length > 0 else inter.area
                if score > best_score:
                    best_score = score
                    best_r = r

        if best_r:
            try:
                merged = unary_union([best_r["geom"].buffer(1.5e-6), s["geom"].buffer(1.5e-6)]).buffer(-1.5e-6)
                merged = make_valid(merged)
                extracted = _extract_polygons(merged)
                if extracted:
                    best_r["geom"] = extracted[0]
                    best_r["area"] = extracted[0].area * (111320.0 ** 2)
                    best_r["ann"].geom_geojson = json.dumps(mapping(extracted[0]))
                    best_r["ann"].area_sqm = best_r["area"]
                    db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == s["ann"].id).update({"annotation_id": None}, synchronize_session=False)
                    db.delete(s["ann"])
                    absorbed_count += 1
            except Exception:
                pass
        else:
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == s["ann"].id).update({"annotation_id": None}, synchronize_session=False)
            db.delete(s["ann"])
            absorbed_count += 1

    db.commit()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CLEAN_SLIVERS",
        entity_type="task_grid",
        entity_id=task_grid_id,
        task_grid_id=task_grid_id,
        details=json.dumps({"absorbed_count": absorbed_count})
    )

    return {
        "message": f"Berhasil menyerap {absorbed_count} sliver garis ke poligon tetangga!",
        "absorbed_count": absorbed_count
    }


class ResolveOverlapRequest(BaseModel):
    task_grid_id: int
    ann_id_a: int
    ann_id_b: int
    action: str  # "clip_a_by_b", "clip_b_by_a", "merge_into_a", "merge_into_b"
    target_class_id: Optional[int] = None


@router.post("/resolve-overlap")
def resolve_overlap(
    req: ResolveOverlapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Interactively resolves an overlap between two specific annotation polygons:
    - clip_a_by_b: Subtracts Polygon B from Polygon A (A is trimmed, B remains intact)
    - clip_b_by_a: Subtracts Polygon A from Polygon B (B is trimmed, A remains intact)
    - merge_into_a / merge_into_b: Unions both polygons into a single polygon
    """
    from shapely.geometry import shape, mapping
    from shapely.validation import make_valid
    
    ann_a = db.query(Annotation).filter(Annotation.id == req.ann_id_a, Annotation.task_grid_id == req.task_grid_id).first()
    ann_b = db.query(Annotation).filter(Annotation.id == req.ann_id_b, Annotation.task_grid_id == req.task_grid_id).first()
    
    if not ann_a or not ann_b:
        raise HTTPException(status_code=404, detail="Salah satu atau kedua poligon tidak ditemukan pada grid ini")
        
    try:
        geom_a = shape(json.loads(ann_a.geom_geojson))
        geom_b = shape(json.loads(ann_b.geom_geojson))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca geometri poligon: {e}")

    if not geom_a.is_valid:
        geom_a = make_valid(geom_a)
    if not geom_b.is_valid:
        geom_b = make_valid(geom_b)
        
    if not geom_a.intersects(geom_b):
        return {"message": f"Poligon #{ann_a.id} dan #{ann_b.id} tidak tumpang tindih."}

    inter = geom_a.intersection(geom_b)
    if inter.is_empty or inter.area <= 0:
        return {"message": f"Poligon #{ann_a.id} dan #{ann_b.id} hanya bersentuhan di garis batas (tidak bertumpuk)."}
        
    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}
    
    if req.action == "clip_a_by_b":
        # Subtract B from A: A is clipped, B remains unchanged
        diff = geom_a.difference(geom_b)
        diff = make_valid(diff)
        polys = _extract_polygons(diff, min_area_sqm=3.0)
        if not polys:
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann_a.id).update({"annotation_id": None}, synchronize_session=False)
            db.delete(ann_a)
            db.commit()
            return {"message": f"Poligon #{ann_a.id} terhapus karena seluruh areanya berada di dalam Poligon #{ann_b.id}."}
            
        ann_a.geom_geojson = json.dumps(mapping(polys[0]))
        ann_a.area_sqm = polys[0].area * (111320.0 ** 2)
        for extra in polys[1:]:
            extra_sqm = extra.area * (111320.0 ** 2)
            if extra_sqm >= 3.0:
                new_ann = Annotation(
                    task_grid_id=req.task_grid_id,
                    user_id=ann_a.user_id,
                    class_id=ann_a.class_id,
                    class_name=ann_a.class_name,
                    geom_geojson=json.dumps(mapping(extra)),
                    area_sqm=extra_sqm
                )
                db.add(new_ann)
        db.commit()
        return {"message": f"Poligon #{ann_a.id} ({ann_a.class_name}) berhasil dipotong oleh #{ann_b.id} ({ann_b.class_name}). Bentuk #{ann_b.id} tetap utuh."}
        
    elif req.action == "clip_b_by_a":
        # Subtract A from B: B is clipped, A remains unchanged
        diff = geom_b.difference(geom_a)
        diff = make_valid(diff)
        polys = _extract_polygons(diff, min_area_sqm=3.0)
        if not polys:
            db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann_b.id).update({"annotation_id": None}, synchronize_session=False)
            db.delete(ann_b)
            db.commit()
            return {"message": f"Poligon #{ann_b.id} terhapus karena seluruh areanya berada di dalam Poligon #{ann_a.id}."}
            
        ann_b.geom_geojson = json.dumps(mapping(polys[0]))
        ann_b.area_sqm = polys[0].area * (111320.0 ** 2)
        for extra in polys[1:]:
            extra_sqm = extra.area * (111320.0 ** 2)
            if extra_sqm >= 3.0:
                new_ann = Annotation(
                    task_grid_id=req.task_grid_id,
                    user_id=ann_b.user_id,
                    class_id=ann_b.class_id,
                    class_name=ann_b.class_name,
                    geom_geojson=json.dumps(mapping(extra)),
                    area_sqm=extra_sqm
                )
                db.add(new_ann)
        db.commit()
        return {"message": f"Poligon #{ann_b.id} ({ann_b.class_name}) berhasil dipotong oleh #{ann_a.id} ({ann_a.class_name}). Bentuk #{ann_a.id} tetap utuh."}
        
    elif req.action.startswith("merge"):
        union_geom = geom_a.union(geom_b)
        union_geom = make_valid(union_geom)
        polys = _extract_polygons(union_geom, min_area_sqm=0.1)
        if not polys:
            raise HTTPException(status_code=400, detail="Gagal menggabungkan poligon")
            
        target_cid = req.target_class_id if req.target_class_id is not None else ann_a.class_id
        target_cname = classes_dict.get(target_cid, ann_a.class_name)
        
        ann_a.class_id = target_cid
        ann_a.class_name = target_cname
        ann_a.geom_geojson = json.dumps(mapping(polys[0]))
        ann_a.area_sqm = polys[0].area * (111320.0 ** 2)
        
        # Point review pins of B to A
        db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann_b.id).update({"annotation_id": ann_a.id}, synchronize_session=False)
        db.delete(ann_b)
        
        for extra in polys[1:]:
            new_ann = Annotation(
                task_grid_id=req.task_grid_id,
                user_id=ann_a.user_id,
                class_id=target_cid,
                class_name=target_cname,
                geom_geojson=json.dumps(mapping(extra)),
                area_sqm=extra.area * (111320.0 ** 2)
            )
            db.add(new_ann)
            
        db.commit()
        return {"message": f"Poligon #{ann_a.id} dan #{ann_b.id} berhasil digabung menjadi satu poligon '{target_cname}'."}
        
    else:
        raise HTTPException(status_code=400, detail="Aksi tidak dikenal. Gunakan: clip_a_by_b, clip_b_by_a, atau merge_into_a")


@router.post("/{annotation_id}/repair-geometry")
def repair_single_annotation_geometry(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Repairs a single invalid polygon geometry (make_valid, clean degenerate holes).
    """
    from shapely.geometry import shape, mapping, Polygon
    from shapely.validation import make_valid
    
    ann = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Annotation not found")
        
    try:
        s_geom = shape(json.loads(ann.geom_geojson))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Format geometri rusak: {e}")
        
    try:
        s_geom = make_valid(s_geom)
    except Exception:
        try:
            s_geom = s_geom.buffer(0)
        except Exception:
            pass
            
    if s_geom.geom_type == 'Polygon' and len(s_geom.interiors) > 0:
        cleaned_holes = [h for h in s_geom.interiors if Polygon(h).area > 1e-9]
        if len(cleaned_holes) != len(s_geom.interiors):
            s_geom = Polygon(s_geom.exterior, cleaned_holes)
            
    polys = _extract_polygons(s_geom, min_area_sqm=0.1)
    if not polys:
        raise HTTPException(status_code=400, detail="Geometri tidak dapat dipulihkan atau luasnya 0 m²")
        
    ann.geom_geojson = json.dumps(mapping(polys[0]))
    ann.area_sqm = polys[0].area * (111320.0 ** 2)
    
    for extra in polys[1:]:
        new_ann = Annotation(
            task_grid_id=ann.task_grid_id,
            user_id=ann.user_id,
            class_id=ann.class_id,
            class_name=ann.class_name,
            geom_geojson=json.dumps(mapping(extra)),
            area_sqm=extra.area * (111320.0 ** 2)
        )
        db.add(new_ann)
        
    db.commit()
    db.refresh(ann)
    return {
        "message": f"Geometri poligon #{ann.id} ({ann.class_name}) berhasil diperbaiki dan valid!",
        "id": ann.id,
        "area_sqm": ann.area_sqm
    }


class FillGapsRequest(BaseModel):
    class_id: int = 0
    min_gap_area_sqm: float = 1.0


@router.post("/grid/{task_grid_id}/fill-gaps")
def fill_grid_gaps(
    task_grid_id: int,
    req: FillGapsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Detects unassigned empty space (gaps) in the task grid and creates new polygons with chosen class.
    """
    from shapely.geometry import box, shape, mapping
    from shapely.ops import unary_union
    
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")
        
    annotations = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).all()
    if not annotations:
        raise HTTPException(status_code=400, detail="Grid belum memiliki poligon dasar")
        
    grid_box = box(task.min_lon, task.min_lat, task.max_lon, task.max_lat)
    valid_geoms = []
    for ann in annotations:
        try:
            g = shape(json.loads(ann.geom_geojson))
            if g.is_valid and not g.is_empty:
                valid_geoms.append(g)
        except Exception:
            pass
            
    if not valid_geoms:
        raise HTTPException(status_code=400, detail="Tidak ada geometri valid untuk menghitung celah")
        
    union_geoms = unary_union(valid_geoms)
    gap_geom = grid_box.difference(union_geoms)
    
    polys = _extract_polygons(gap_geom, min_area_sqm=req.min_gap_area_sqm)
    if not polys:
        return {"message": "Tidak ditemukan celah kosong yang melebihi ambang batas luas", "gaps_created": 0}
        
    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}
    cid = req.class_id if req.class_id in classes_dict else 0
    cname = classes_dict.get(cid, "Belum Teridentifikasi")
    
    for p in polys:
        new_ann = Annotation(
            task_grid_id=task_grid_id,
            user_id=current_user.id,
            class_id=cid,
            class_name=cname,
            geom_geojson=json.dumps(mapping(p)),
            area_sqm=p.area * (111320.0 ** 2)
        )
        db.add(new_ann)
        
    db.commit()
    return {
        "message": f"Berhasil mengisi {len(polys)} celah kosong dengan kelas '{cname}'!",
        "gaps_created": len(polys)
    }


@router.delete("/{annotation_id}")
def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    ann = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Annotation not found")
        
    role = (current_user.role or "").lower().strip()
    if role not in ["admin", "dosen"] and ann.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this annotation")
        
    # Safeguard review pins before deleting annotation
    db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == annotation_id).update({"annotation_id": None}, synchronize_session=False)
    db.delete(ann)
    db.commit()
    return {"message": "Annotation deleted successfully"}


# ─────────────────────────────────────────────────────────────────────────────
# ADVANCED GIS DIGITIZATION: SPLIT (CUT) & MERGE POLYGONS
# ─────────────────────────────────────────────────────────────────────────────

class SplitByPolygonRequest(BaseModel):
    task_grid_id: int
    cutting_geom: Dict[str, Any]
    target_annotation_id: Optional[int] = None
    target_feature: Optional[Dict[str, Any]] = None
    new_class_id: Optional[int] = 0
    persist: Optional[bool] = False

class SplitByLineRequest(BaseModel):
    task_grid_id: int
    line_geom: Dict[str, Any]
    target_annotation_id: Optional[int] = None
    target_feature: Optional[Dict[str, Any]] = None
    new_class_id: Optional[int] = 0
    persist: Optional[bool] = False

class MergePolygonsRequest(BaseModel):
    task_grid_id: Optional[int] = None
    annotation_ids: Optional[List[Any]] = None
    features: Optional[List[Dict[str, Any]]] = None
    target_class_id: Optional[int] = None
    persist: Optional[bool] = False

class GridMergePolygonsRequest(BaseModel):
    annotation_ids: List[Any]
    target_class_id: Optional[int] = None

class UpdateAnnotationClassRequest(BaseModel):
    class_id: int


def _clean_spikes_and_holes(poly):
    """
    Eliminates needle spikes, whiskers, and degenerate collapsed slit holes
    from a Shapely Polygon.
    """
    from shapely.geometry import Polygon as SPolygon, MultiPolygon as SMultiPolygon
    from shapely.validation import make_valid

    if poly is None or poly.is_empty:
        return poly
    if poly.geom_type == 'MultiPolygon':
        cleaned_parts = [_clean_spikes_and_holes(p) for p in poly.geoms]
        cleaned_parts = [p for p in cleaned_parts if p and not p.is_empty and p.geom_type == 'Polygon']
        return SMultiPolygon(cleaned_parts) if cleaned_parts else poly
    if poly.geom_type != 'Polygon':
        return poly

    # 1. Clean collapsed/zero-area interior holes
    cleaned_holes = []
    if len(poly.interiors) > 0:
        for h in poly.interiors:
            if SPolygon(h).area > 1e-9:
                cleaned_holes.append(h)

    # 2. Clean foldback turnaround spikes on exterior ring:
    ext_coords = list(poly.exterior.coords)
    changed = True
    iterations = 0
    while changed and len(ext_coords) > 3 and iterations < 10:
        changed = False
        iterations += 1
        n = len(ext_coords) - 1
        skip = set()
        for i in range(n):
            if i in skip:
                continue
            prev_pt = ext_coords[(i - 1 + n) % n]
            curr_pt = ext_coords[i]
            next_pt = ext_coords[(i + 1) % n]
            # If distance from prev_pt to next_pt is negligible, it's a spike back-and-forth
            if abs(prev_pt[0] - next_pt[0]) < 1e-8 and abs(prev_pt[1] - next_pt[1]) < 1e-8:
                skip.add(i)
                changed = True
        if changed:
            ext_coords = [ext_coords[i] for i in range(n) if i not in skip]
            if ext_coords and ext_coords[0] != ext_coords[-1]:
                ext_coords.append(ext_coords[0])

    # 3. Deduplicate consecutive duplicate vertices
    clean_ext = []
    for pt in ext_coords:
        if not clean_ext or abs(pt[0] - clean_ext[-1][0]) > 1e-9 or abs(pt[1] - clean_ext[-1][1]) > 1e-9:
            clean_ext.append(pt)
    if len(clean_ext) > 1 and clean_ext[0] != clean_ext[-1]:
        clean_ext.append(clean_ext[0])

    if len(clean_ext) < 4:
        return SPolygon()

    try:
        new_poly = SPolygon(clean_ext, cleaned_holes)
        if not new_poly.is_valid:
            new_poly = make_valid(new_poly)
            if new_poly.geom_type == 'GeometryCollection':
                valid_pieces = [g for g in new_poly.geoms if g.geom_type == 'Polygon']
                if valid_pieces:
                    new_poly = valid_pieces[0] if len(valid_pieces) == 1 else SMultiPolygon(valid_pieces)
        return new_poly
    except Exception:
        return poly


def _extract_polygons(geom, min_area_sqm=3.0):
    """
    Recursively unpacks GeometryCollection / MultiPolygon into distinct Polygon objects,
    validates/heals geometry with make_valid, and filters out micro-slivers below min_area_sqm.
    Cleans spikes and collapsed line holes automatically.
    """
    from shapely.validation import make_valid
    if geom is None or geom.is_empty:
        return []

    # Convert minimum area in square meters to approximate degrees squared (1 deg ~ 111320m)
    min_area_deg = (min_area_sqm / (111320.0 ** 2)) if min_area_sqm > 0 else 1e-12

    if not geom.is_valid:
        try:
            geom = make_valid(geom)
        except Exception:
            try:
                geom = geom.buffer(0)
            except Exception:
                pass

    if geom.geom_type == 'Polygon':
        geom = _clean_spikes_and_holes(geom)
        if geom.is_valid and geom.area >= min_area_deg:
            return [geom]
        return []
    elif geom.geom_type == 'MultiPolygon':
        polys = []
        for g in geom.geoms:
            polys.extend(_extract_polygons(g, min_area_sqm=min_area_sqm))
        return polys
    elif geom.geom_type == 'GeometryCollection':
        polys = []
        for g in geom.geoms:
            polys.extend(_extract_polygons(g, min_area_sqm=min_area_sqm))
        return polys
    return []


@router.put("/{annotation_id}/class")
def update_annotation_class(
    annotation_id: int,
    data: UpdateAnnotationClassRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Updates the class of a single annotation polygon instantly"""
    ann = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Annotation not found")
        
    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}
    if data.class_id not in classes_dict:
        raise HTTPException(status_code=400, detail="Invalid class_id")
        
    ann.class_id = data.class_id
    ann.class_name = classes_dict[data.class_id]
    db.commit()
    db.refresh(ann)
    return {
        "message": f"Kelas poligon #{ann.id} diubah menjadi '{ann.class_name}'",
        "id": ann.id,
        "class_id": ann.class_id,
        "class_name": ann.class_name
    }


def _clean_line_coords(line, min_dist=1e-5):
    raw = list(line.coords)
    if len(raw) < 2:
        return raw
    cleaned = [raw[0]]
    for p in raw[1:]:
        prev = cleaned[-1]
        dist = math.hypot(p[0] - prev[0], p[1] - prev[1])
        if dist > min_dist:
            cleaned.append(p)
    if len(cleaned) < 2 and len(raw) >= 2:
        cleaned = [raw[0], raw[-1]]
    return cleaned


def _get_stable_direction(coords, from_end=True, min_dist=2e-5):
    """
    Finds the true stable direction vector of a line's endpoint,
    filtering out any microscopic mouse double-click jitter.
    """
    if from_end:
        p_ref = coords[-1]
        for i in range(len(coords) - 2, -1, -1):
            dx = p_ref[0] - coords[i][0]
            dy = p_ref[1] - coords[i][1]
            dist = math.hypot(dx, dy)
            if dist >= min_dist:
                return dx / dist, dy / dist
        dx = coords[-1][0] - coords[0][0]
        dy = coords[-1][1] - coords[0][1]
        dist = math.hypot(dx, dy)
        return (dx / dist, dy / dist) if dist > 0 else (1.0, 0.0)
    else:
        p_ref = coords[0]
        for i in range(1, len(coords)):
            dx = p_ref[0] - coords[i][0]
            dy = p_ref[1] - coords[i][1]
            dist = math.hypot(dx, dy)
            if dist >= min_dist:
                return dx / dist, dy / dist
        dx = coords[0][0] - coords[-1][0]
        dy = coords[0][1] - coords[-1][1]
        dist = math.hypot(dx, dy)
        return (dx / dist, dy / dist) if dist > 0 else (-1.0, 0.0)


def _extend_line(line, factor=0.25, max_ext_deg=5e-4, min_ext_deg=5e-5):
    """
    Extends line slightly at both ends by ~5 to 30 meters along its true direction so split()
    cuts cleanly across polygon boundaries, even when vertices snap directly on the boundary.
    """
    import math
    from shapely.geometry import LineString
    try:
        raw_coords = list(line.coords)
        if len(raw_coords) < 2:
            return line
        coords = _clean_line_coords(line)
        if len(coords) < 2:
            return line

        total_len = line.length
        ext_len = min(max_ext_deg, max(min_ext_deg, total_len * factor))

        # Backward ray from start
        u_back_x, u_back_y = _get_stable_direction(coords, from_end=False)
        p0_ext = (coords[0][0] + u_back_x * ext_len, coords[0][1] + u_back_y * ext_len)

        # Forward ray from end
        u_fwd_x, u_fwd_y = _get_stable_direction(coords, from_end=True)
        p1_ext = (coords[-1][0] + u_fwd_x * ext_len, coords[-1][1] + u_fwd_y * ext_len)

        return LineString([p0_ext] + coords[1:-1] + [p1_ext])
    except Exception:
        return line


def _extend_line_to_bounds(line, geom_bounds, multiplier=0.5):
    """
    Extends a line's endpoints along its true stable trajectory just enough to exit
    the given polygon boundary cleanly without shooting across the entire map.
    """
    import math
    from shapely.geometry import LineString
    try:
        raw_coords = list(line.coords)
        if len(raw_coords) < 2:
            return line
        coords = _clean_line_coords(line)
        if len(coords) < 2:
            return line

        minx, miny, maxx, maxy = geom_bounds
        bbox_diag = math.hypot(maxx - minx, maxy - miny)
        # Moderate extension: capped to at most ~200 meters to prevent shooting into distant polygons
        ext_dist = min(max(bbox_diag * multiplier, 5e-5), 0.002)

        # Direction 0: backward from start
        u_back_x, u_back_y = _get_stable_direction(coords, from_end=False)
        p0_ext = (coords[0][0] + u_back_x * ext_dist, coords[0][1] + u_back_y * ext_dist)

        # Direction 1: forward from end
        u_fwd_x, u_fwd_y = _get_stable_direction(coords, from_end=True)
        p1_ext = (coords[-1][0] + u_fwd_x * ext_dist, coords[-1][1] + u_fwd_y * ext_dist)

        return LineString([p0_ext] + coords[1:-1] + [p1_ext])
    except Exception:
        return line


@router.post("/split-by-polygon")
def split_by_polygon(
    req: SplitByPolygonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    True Semantic Segmentation Cut: Splits existing polygon(s) using a cutting polygon.
    Both the Inside (Intersection) and Outside (Difference) pieces are preserved!
    Works seamlessly on populated or fresh/empty grids.
    """
    from shapely.geometry import shape, mapping
    
    task = db.query(TaskGrid).filter(TaskGrid.id == req.task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")
        
    try:
        cutter = shape(req.cutting_geom)
        if not cutter.is_valid:
            cutter = cutter.buffer(0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid cutting geometry: {str(e)}")

    task_poly = None
    if task.geom_geojson:
        try:
            task_poly = shape(json.loads(task.geom_geojson))
            if not task_poly.is_valid:
                task_poly = task_poly.buffer(0)
        except Exception:
            task_poly = None

    # Clip cutter to task grid boundary if task_poly exists
    if task_poly:
        if not cutter.intersects(task_poly):
            raise HTTPException(status_code=400, detail="Area pemotong berada di luar batas grid task.")
        cutter_in_grid = cutter.intersection(task_poly)
    else:
        cutter_in_grid = cutter

    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}
    new_class_id = req.new_class_id if req.new_class_id in classes_dict else 0
    new_class_name = classes_dict.get(new_class_id, "Belum Teridentifikasi")

    # CASE 0: target_feature provided directly from frontend (Draft-Mode friendly & 100% Undoable)
    if req.target_feature and "geometry" in req.target_feature:
        target_f = req.target_feature
        try:
            poly = shape(target_f["geometry"])
            if not poly.is_valid:
                poly = poly.buffer(0)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Geometri poligon target tidak valid: {str(e)}")

        target_ui_id = target_f.get("_uiId") or target_f.get("properties", {}).get("_uiId")
        target_id = target_f.get("id") or target_f.get("properties", {}).get("id")
        parent_class_id = int(target_f.get("properties", {}).get("class_id", 0))
        parent_class_name = target_f.get("properties", {}).get("class_name", classes_dict.get(parent_class_id, "Belum Teridentifikasi"))

        inter_polys = _extract_polygons(poly.intersection(cutter_in_grid), min_area_sqm=0.1)
        diff_polys = _extract_polygons(poly.difference(cutter_in_grid), min_area_sqm=0.1)

        if inter_polys:
            target_cut_cid = new_class_id if (new_class_id and new_class_id in classes_dict and new_class_id > 0) else parent_class_id
            target_cut_cname = classes_dict.get(target_cut_cid, parent_class_name)

            if not req.persist:
                created_features = []
                for dp in diff_polys:
                    created_features.append({
                        "type": "Feature",
                        "geometry": mapping(dp),
                        "properties": {
                            "class_id": parent_class_id,
                            "class_name": parent_class_name,
                            "area_sqm": dp.area * (111320.0 ** 2),
                            "author_name": current_user.full_name or "Unknown",
                        }
                    })
                for ip in inter_polys:
                    created_features.append({
                        "type": "Feature",
                        "geometry": mapping(ip),
                        "properties": {
                            "class_id": target_cut_cid,
                            "class_name": target_cut_cname,
                            "area_sqm": ip.area * (111320.0 ** 2),
                            "author_name": current_user.full_name or "Unknown",
                        }
                    })
                return {
                    "message": "Poligon berhasil dipisah menjadi bagian independen!",
                    "split_count": len(inter_polys),
                    "deleted_ids": [target_id] if (target_id and isinstance(target_id, int)) else [],
                    "deleted_ui_id": target_ui_id,
                    "created_features": created_features,
                    "updated_features": []
                }
        else:
            raise HTTPException(
                status_code=400,
                detail="Area pemotong tidak beririsan dengan poligon target."
            )

    # Fetch all annotations for this task grid
    all_anns = db.query(Annotation).filter(Annotation.task_grid_id == req.task_grid_id).all()

    target_ann = None
    if req.target_annotation_id:
        target_ann = db.query(Annotation).filter(
            Annotation.id == req.target_annotation_id,
            Annotation.task_grid_id == req.task_grid_id
        ).first()
        if not target_ann:
            target_ann = db.query(Annotation).filter(
                Annotation.id == req.target_annotation_id
            ).first()

    cutter_box = box(*cutter.bounds)
    candidate_anns_with_area = []
    for ann in all_anns:
        try:
            poly = shape(json.loads(ann.geom_geojson))
            if not poly.is_valid:
                poly = poly.buffer(0)

            if not cutter_box.intersects(poly):
                continue

            if not poly.intersects(cutter):
                continue

            inter = poly.intersection(cutter)
            inter_area = inter.area if inter and not inter.is_empty else 0
            if inter_area > 1e-10:
                candidate_anns_with_area.append((ann, poly, inter_area))
        except Exception:
            continue

    split_occurred = False
    new_created_count = 0
    deleted_ids = []
    new_annotations_list = []
    updated_annotations_list = []

    # CASE 1: Grid has NO annotations yet! Slice directly from task grid polygon
    if len(all_anns) == 0:
        if task_poly:
            inter_polys = _extract_polygons(cutter_in_grid, min_area_sqm=0.1)
            diff_polys = _extract_polygons(task_poly.difference(cutter_in_grid), min_area_sqm=0.1)
            
            if not req.persist and inter_polys:
                created_features = []
                for dp in diff_polys:
                    created_features.append({
                        "type": "Feature",
                        "geometry": mapping(dp),
                        "properties": {
                            "class_id": 0,
                            "class_name": "Belum Teridentifikasi",
                            "area_sqm": dp.area * (111320.0 ** 2),
                            "author_name": current_user.full_name or "Unknown",
                        }
                    })
                for ip in inter_polys:
                    created_features.append({
                        "type": "Feature",
                        "geometry": mapping(ip),
                        "properties": {
                            "class_id": new_class_id,
                            "class_name": new_class_name,
                            "area_sqm": ip.area * (111320.0 ** 2),
                            "author_name": current_user.full_name or "Unknown",
                        }
                    })
                return {
                    "message": "Poligon berhasil dipisah menjadi bagian independen!",
                    "split_count": len(inter_polys),
                    "deleted_ids": [],
                    "deleted_ui_id": None,
                    "created_features": created_features,
                    "updated_features": []
                }

            if inter_polys:
                # Add intersection pieces (assigned with new_class_id)
                for ip in inter_polys:
                    ip_geojson = mapping(ip)
                    area_sqm = ip.area * (111320.0 ** 2)
                    ann_ip = Annotation(
                        task_grid_id=req.task_grid_id,
                        user_id=current_user.id,
                        class_id=new_class_id,
                        class_name=new_class_name,
                        geom_geojson=json.dumps(ip_geojson),
                        area_sqm=area_sqm
                    )
                    db.add(ann_ip)
                    new_annotations_list.append(ann_ip)
                    new_created_count += 1
                
                # Add difference pieces (remaining area marked as unclassified 0)
                for dp in diff_polys:
                    dp_geojson = mapping(dp)
                    area_sqm = dp.area * (111320.0 ** 2)
                    ann_dp = Annotation(
                        task_grid_id=req.task_grid_id,
                        user_id=current_user.id,
                        class_id=0,
                        class_name="Belum Teridentifikasi",
                        geom_geojson=json.dumps(dp_geojson),
                        area_sqm=area_sqm
                    )
                    db.add(ann_dp)
                    new_annotations_list.append(ann_dp)
                split_occurred = True
        else:
            cut_polys = _extract_polygons(cutter_in_grid, min_area_sqm=0.1)
            for cp in cut_polys:
                area_sqm = cp.area * (111320.0 ** 2)
                ann_cp = Annotation(
                    task_grid_id=req.task_grid_id,
                    user_id=current_user.id,
                    class_id=new_class_id,
                    class_name=new_class_name,
                    geom_geojson=json.dumps(mapping(cp)),
                    area_sqm=area_sqm
                )
                db.add(ann_cp)
                new_annotations_list.append(ann_cp)
                new_created_count += 1
            if new_created_count > 0:
                split_occurred = True

    # CASE 2: Grid has existing annotations
    else:
        if not candidate_anns_with_area:
            raise HTTPException(status_code=400, detail="Area pemotong tidak membelah poligon manapun. Pastikan melintasi batas poligon target.")

        # Sort candidates by coverage ratio (inter_area / poly.area) descending so foreground polygons take priority over giant background polygons
        candidate_anns_with_area.sort(key=lambda x: (x[2] / (x[1].area + 1e-12), -x[1].area), reverse=True)
        cutter_area = cutter.area

        # Determine target polygons:
        # If user explicitly requested target_ann AND it has significant overlap (> 5% of cutter), prioritize it
        target_candidates = []
        if target_ann:
            matched = [c for c in candidate_anns_with_area if c[0].id == target_ann.id and c[2] > 0.05 * cutter_area]
            if matched:
                target_candidates.append(matched[0])
                for c in candidate_anns_with_area:
                    if c[0].id != target_ann.id:
                        target_candidates.append(c)

        if not target_candidates:
            # Sort descending by overlap area so the primary polygon is first
            target_candidates = candidate_anns_with_area

        for ann, poly, inter_area in target_candidates:
            try:
                intersection = poly.intersection(cutter)
                difference = poly.difference(cutter)

                inter_polys = _extract_polygons(intersection, min_area_sqm=10.0)
                diff_polys = _extract_polygons(difference, min_area_sqm=10.0)

                if inter_polys and diff_polys:
                    split_occurred = True
                    target_cut_cid = new_class_id if (new_class_id and new_class_id in classes_dict and new_class_id > 0) else ann.class_id
                    target_cut_cname = classes_dict.get(target_cut_cid, ann.class_name)

                    if not req.persist:
                        created_features = []
                        for dp in diff_polys:
                            created_features.append({
                                "type": "Feature",
                                "geometry": mapping(dp),
                                "properties": {
                                    "class_id": ann.class_id,
                                    "class_name": ann.class_name,
                                    "area_sqm": dp.area * (111320.0 ** 2),
                                    "author_name": current_user.full_name or "Unknown",
                                }
                            })
                        for ip in inter_polys:
                            created_features.append({
                                "type": "Feature",
                                "geometry": mapping(ip),
                                "properties": {
                                    "class_id": target_cut_cid,
                                    "class_name": target_cut_cname,
                                    "area_sqm": ip.area * (111320.0 ** 2),
                                    "author_name": current_user.full_name or "Unknown",
                                }
                            })
                        return {
                            "message": "Poligon berhasil dipisah menjadi bagian independen!",
                            "split_count": len(inter_polys),
                            "deleted_ids": [ann.id],
                            "created_features": created_features,
                            "updated_features": []
                        }
                    deleted_ids.append(ann.id)
                    # Remove original polygon record (safeguard review pins)
                    db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann.id).update({"annotation_id": None}, synchronize_session=False)
                    db.delete(ann)

                    # Add difference pieces (keeping original class)
                    for dp in diff_polys:
                        dp_geojson = mapping(dp)
                        area_sqm = dp.area * (111320.0 ** 2)
                        new_dp = Annotation(
                            task_grid_id=req.task_grid_id,
                            user_id=current_user.id,
                            class_id=ann.class_id,
                            class_name=ann.class_name,
                            geom_geojson=json.dumps(dp_geojson),
                            area_sqm=area_sqm
                        )
                        db.add(new_dp)
                        new_annotations_list.append(new_dp)

                    target_cut_cid = new_class_id if (new_class_id and new_class_id in classes_dict and new_class_id > 0) else ann.class_id
                    target_cut_cname = classes_dict.get(target_cut_cid, ann.class_name)

                    # Add intersection pieces (assigned with new_class_id or parent class)
                    for ip in inter_polys:
                        ip_geojson = mapping(ip)
                        area_sqm = ip.area * (111320.0 ** 2)
                        new_ip = Annotation(
                            task_grid_id=req.task_grid_id,
                            user_id=current_user.id,
                            class_id=target_cut_cid,
                            class_name=target_cut_cname,
                            geom_geojson=json.dumps(ip_geojson),
                            area_sqm=area_sqm
                        )
                        db.add(new_ip)
                        new_annotations_list.append(new_ip)
                        new_created_count += 1

                    # Single target cut complete: STOP cascade cutting adjacent polygons!
                    break

                elif inter_polys and not diff_polys:
                    # Polygon is completely enclosed by cutter -> reclassify
                    split_occurred = True
                    target_cut_cid = new_class_id if (new_class_id and new_class_id in classes_dict and new_class_id > 0) else ann.class_id
                    ann.class_id = target_cut_cid
                    ann.class_name = classes_dict.get(target_cut_cid, ann.class_name)
                    ann.user_id = current_user.id
                    new_created_count += 1
                    updated_annotations_list.append(ann)
                    break
            except Exception:
                continue

    if not split_occurred:
        raise HTTPException(status_code=400, detail="Garis atau area pemotong tidak membelah poligon manapun. Pastikan melintasi batas poligon target.")

    if task.status in ["ASSIGNED", "UNASSIGNED", "REVISION_NEEDED"]:
        task.status = "IN_PROGRESS"

    db.commit()

    created_features = []
    for na in new_annotations_list:
        db.refresh(na)
        created_features.append({
            "type": "Feature",
            "id": na.id,
            "geometry": json.loads(na.geom_geojson),
            "properties": {
                "id": na.id,
                "class_id": na.class_id,
                "class_name": na.class_name,
                "user_id": na.user_id,
                "author_name": current_user.full_name or "Unknown",
                "area_sqm": na.area_sqm,
                "created_at": na.created_at.isoformat() if na.created_at else None
            }
        })

    updated_features_res = []
    for ua in updated_annotations_list:
        db.refresh(ua)
        updated_features_res.append({
            "type": "Feature",
            "id": ua.id,
            "geometry": json.loads(ua.geom_geojson),
            "properties": {
                "id": ua.id,
                "class_id": ua.class_id,
                "class_name": ua.class_name,
                "user_id": ua.user_id,
                "author_name": current_user.full_name or "Unknown",
                "area_sqm": ua.area_sqm,
                "created_at": ua.created_at.isoformat() if ua.created_at else None
            }
        })

    return {
        "message": "Poligon berhasil dipisah menjadi bagian independen!",
        "split_count": new_created_count,
        "deleted_ids": deleted_ids,
        "created_features": created_features,
        "updated_features": updated_features_res
    }


@router.post("/split-by-line")
def split_by_line(
    req: SplitByLineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Split Blade: Splits polygon(s) across a line blade into 2 or more separate polygons.
    """
    from shapely.geometry import shape, mapping
    from shapely.ops import split
    
    task = db.query(TaskGrid).filter(TaskGrid.id == req.task_grid_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task grid not found")
        
    try:
        blade = shape(req.line_geom)
        if not blade.is_valid:
            blade = blade.buffer(0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid line geometry: {str(e)}")

    task_poly = None
    if task.geom_geojson:
        try:
            task_poly = shape(json.loads(task.geom_geojson))
            if not task_poly.is_valid:
                task_poly = task_poly.buffer(0)
        except Exception:
            task_poly = None

    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}
    new_class_id = req.new_class_id if req.new_class_id in classes_dict else 0
    new_class_name = classes_dict.get(new_class_id, "Belum Teridentifikasi")

    # CASE 0: target_feature provided directly from frontend (Draft-Mode friendly & 100% Undoable)
    if req.target_feature and "geometry" in req.target_feature:
        target_f = req.target_feature
        try:
            poly = shape(target_f["geometry"])
            if not poly.is_valid:
                poly = poly.buffer(0)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Geometri poligon target tidak valid: {str(e)}")

        target_ui_id = target_f.get("_uiId") or target_f.get("properties", {}).get("_uiId")
        target_id = target_f.get("id") or target_f.get("properties", {}).get("id")
        parent_class_id = int(target_f.get("properties", {}).get("class_id", 0))
        parent_class_name = target_f.get("properties", {}).get("class_name", classes_dict.get(parent_class_id, "Belum Teridentifikasi"))

        pieces = []
        if poly.geom_type == 'MultiPolygon':
            target_sub_idx = None
            sub_pieces = []
            for idx, g in enumerate(poly.geoms):
                ext_bounds_1 = _extend_line_to_bounds(blade, g.bounds, multiplier=1.5)
                ext_bounds_2 = _extend_line_to_bounds(blade, g.bounds, multiplier=2.5)
                for test_blade in [blade, _extend_line(blade, factor=0.25), _extend_line(blade, factor=0.5), ext_bounds_1, ext_bounds_2]:
                    try:
                        if g.intersects(test_blade):
                            sub_res = split(g, test_blade)
                            p_list = _extract_polygons(sub_res, min_area_sqm=0.1)
                            if len(p_list) > 1:
                                target_sub_idx = idx
                                sub_pieces = p_list
                                break
                    except Exception:
                        continue
                if len(sub_pieces) > 1:
                    break
            if len(sub_pieces) > 1:
                other_geoms = [g for idx, g in enumerate(poly.geoms) if idx != target_sub_idx]
                pieces = sub_pieces + other_geoms
        else:
            ext_bounds_1 = _extend_line_to_bounds(blade, poly.bounds, multiplier=1.5)
            ext_bounds_2 = _extend_line_to_bounds(blade, poly.bounds, multiplier=2.5)
            for test_blade in [blade, _extend_line(blade, factor=0.25), _extend_line(blade, factor=0.5), ext_bounds_1, ext_bounds_2]:
                try:
                    if poly.intersects(test_blade):
                        res = split(poly, test_blade)
                        p_list = _extract_polygons(res, min_area_sqm=0.1)
                        if len(p_list) > 1:
                            pieces = p_list
                            break
                except Exception:
                    continue

        if len(pieces) > 1:
            pieces.sort(key=lambda p: p.area, reverse=True)
            p0 = pieces[0]
            target_slice_cid = new_class_id if (new_class_id and new_class_id > 0 and new_class_id != parent_class_id) else parent_class_id
            target_slice_cname = classes_dict.get(target_slice_cid, parent_class_name)

            if not req.persist:
                created_features = []
                created_features.append({
                    "type": "Feature",
                    "geometry": mapping(p0),
                    "properties": {
                        "class_id": parent_class_id,
                        "class_name": parent_class_name,
                        "area_sqm": p0.area * (111320.0 ** 2),
                        "author_name": current_user.full_name or "Unknown",
                    }
                })
                for p in pieces[1:]:
                    created_features.append({
                        "type": "Feature",
                        "geometry": mapping(p),
                        "properties": {
                            "class_id": target_slice_cid,
                            "class_name": target_slice_cname,
                            "area_sqm": p.area * (111320.0 ** 2),
                            "author_name": current_user.full_name or "Unknown",
                        }
                    })
                return {
                    "message": "Poligon berhasil dipotong dengan garis pemisah!",
                    "deleted_ids": [target_id] if (target_id and isinstance(target_id, int)) else [],
                    "deleted_ui_id": target_ui_id,
                    "created_features": created_features
                }
        else:
            raise HTTPException(
                status_code=400,
                detail="Garis pemotong harus melintasi kedua ujung batas poligon target."
            )

    # Fetch all annotations for this task grid
    all_annotations = db.query(Annotation).filter(Annotation.task_grid_id == req.task_grid_id).all()

    split_occurred = False
    deleted_ids = []
    new_annotations_list = []

    # CASE 1: Grid has NO annotations yet! Slices task grid itself
    if len(all_annotations) == 0 and task_poly:
        ext_task = _extend_line_to_bounds(blade, task_poly.bounds)
        for cut_blade in [blade, ext_task]:
            if task_poly.intersects(cut_blade):
                try:
                    res = split(task_poly, cut_blade)
                    pieces = _extract_polygons(res, min_area_sqm=0.1)
                    if len(pieces) > 1:
                        if not req.persist:
                            created_features = []
                            created_features.append({
                                "type": "Feature",
                                "geometry": mapping(pieces[0]),
                                "properties": {
                                    "class_id": 0,
                                    "class_name": "Belum Teridentifikasi",
                                    "area_sqm": pieces[0].area * (111320.0 ** 2),
                                    "author_name": current_user.full_name or "Unknown",
                                }
                            })
                            for p in pieces[1:]:
                                created_features.append({
                                    "type": "Feature",
                                    "geometry": mapping(p),
                                    "properties": {
                                        "class_id": new_class_id,
                                        "class_name": new_class_name,
                                        "area_sqm": p.area * (111320.0 ** 2),
                                        "author_name": current_user.full_name or "Unknown",
                                    }
                                })
                            return {
                                "message": "Poligon berhasil dipotong dengan garis pemisah!",
                                "deleted_ids": [],
                                "deleted_ui_id": None,
                                "created_features": created_features
                            }
                        split_occurred = True
                        p0 = pieces[0]
                        area_sqm = p0.area * (111320.0 ** 2)
                        ann_p0 = Annotation(
                            task_grid_id=req.task_grid_id,
                            user_id=current_user.id,
                            class_id=0,
                            class_name="Belum Teridentifikasi",
                            geom_geojson=json.dumps(mapping(p0)),
                            area_sqm=area_sqm
                        )
                        db.add(ann_p0)
                        new_annotations_list.append(ann_p0)
                        for p in pieces[1:]:
                            area_sqm = p.area * (111320.0 ** 2)
                            ann_pi = Annotation(
                                task_grid_id=req.task_grid_id,
                                user_id=current_user.id,
                                class_id=new_class_id,
                                class_name=new_class_name,
                                geom_geojson=json.dumps(mapping(p)),
                                area_sqm=area_sqm
                            )
                            db.add(ann_pi)
                            new_annotations_list.append(ann_pi)
                        break
                except Exception:
                    pass

    # CASE 2: Grid has existing annotations
    if not split_occurred and all_annotations:
        test_ext_blade = _extend_line(blade, factor=0.3, max_ext_deg=1e-3, min_ext_deg=5e-5)
        candidate_anns_with_len = []
        for ann in all_annotations:
            try:
                poly = shape(json.loads(ann.geom_geojson))
                if not poly.is_valid:
                    poly = poly.buffer(0)

                if not poly.intersects(blade) and not poly.intersects(test_ext_blade):
                    continue

                inter = poly.intersection(blade)
                i_len = inter.length if inter and not inter.is_empty else 0
                candidate_anns_with_len.append((ann, poly, i_len))
            except Exception:
                continue

        if not candidate_anns_with_len:
            raise HTTPException(status_code=400, detail="Garis pemotong harus melintasi batas poligon dari ujung ke ujung.")

        # Sort strictly by smallest polygon area first (foreground objects) so giant background polygons are never prioritized
        candidate_anns_with_len.sort(key=lambda x: (x[1].area, -x[2]))

        target_ann = None
        if req.target_annotation_id:
            target_ann = db.query(Annotation).filter(
                Annotation.id == req.target_annotation_id,
                Annotation.task_grid_id == req.task_grid_id
            ).first()
            if not target_ann:
                target_ann = db.query(Annotation).filter(
                    Annotation.id == req.target_annotation_id
                ).first()

        candidates = []
        if target_ann:
            matched = [c for c in candidate_anns_with_len if c[0].id == target_ann.id and c[2] > 1e-6]
            if matched:
                candidates.append((matched[0][0], matched[0][1]))
                for c in candidate_anns_with_len:
                    if c[0].id != target_ann.id:
                        candidates.append((c[0], c[1]))
            else:
                candidates = [(c[0], c[1]) for c in candidate_anns_with_len]
        else:
            candidates = [(c[0], c[1]) for c in candidate_anns_with_len]

        for ann, poly in candidates:
            # Case A: MultiPolygon
            if poly.geom_type == 'MultiPolygon':
                sub_cands = []
                for idx, g in enumerate(poly.geoms):
                    inter = g.intersection(blade)
                    i_len = inter.length if inter and not inter.is_empty else 0
                    if g.intersects(blade) or g.intersects(test_ext_blade):
                        sub_cands.append((idx, g, i_len))
                sub_cands.sort(key=lambda x: (x[1].area, -x[2]))

                target_sub_idx = None
                sub_pieces = []
                for idx, g, _ in sub_cands:
                    for test_blade in [blade, _extend_line(blade, factor=0.25, max_ext_deg=5e-4), _extend_line(blade, factor=0.5, max_ext_deg=1e-3)]:
                        try:
                            if g.intersects(test_blade):
                                sub_res = split(g, test_blade)
                                p_list = _extract_polygons(sub_res) if sub_res else []
                                if len(p_list) > 1:
                                    target_sub_idx = idx
                                    sub_pieces = p_list
                                    break
                        except Exception:
                            continue
                    if len(sub_pieces) > 1:
                        break

                if len(sub_pieces) > 1:
                    split_occurred = True
                    deleted_ids.append(ann.id)
                    db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann.id).update(
                        {"annotation_id": None}, synchronize_session=False
                    )
                    db.delete(ann)

                    target_slice_cid = new_class_id if (new_class_id and new_class_id > 0 and new_class_id != ann.class_id) else ann.class_id
                    target_slice_cname = classes_dict.get(target_slice_cid, ann.class_name)

                    sub_pieces.sort(key=lambda p: p.area, reverse=True)
                    p0 = sub_pieces[0]
                    ann_p0 = Annotation(
                        task_grid_id=req.task_grid_id,
                        user_id=current_user.id,
                        class_id=ann.class_id,
                        class_name=ann.class_name,
                        geom_geojson=json.dumps(mapping(p0)),
                        area_sqm=p0.area * (111320.0 ** 2)
                    )
                    db.add(ann_p0)
                    new_annotations_list.append(ann_p0)

                    for p in sub_pieces[1:]:
                        ann_pi = Annotation(
                            task_grid_id=req.task_grid_id,
                            user_id=current_user.id,
                            class_id=target_slice_cid,
                            class_name=target_slice_cname,
                            geom_geojson=json.dumps(mapping(p)),
                            area_sqm=p.area * (111320.0 ** 2)
                        )
                        db.add(ann_pi)
                        new_annotations_list.append(ann_pi)

                    for idx, g in enumerate(poly.geoms):
                        if idx != target_sub_idx:
                            ann_other = Annotation(
                                task_grid_id=req.task_grid_id,
                                user_id=current_user.id,
                                class_id=ann.class_id,
                                class_name=ann.class_name,
                                geom_geojson=json.dumps(mapping(g)),
                                area_sqm=g.area * (111320.0 ** 2)
                            )
                            db.add(ann_other)
                            new_annotations_list.append(ann_other)

                    break

            # Case B: Standard singlepart Polygon
            else:
                pieces = []
                for test_blade in [blade, _extend_line(blade, factor=0.25, max_ext_deg=5e-4), _extend_line(blade, factor=0.5, max_ext_deg=1e-3)]:
                    try:
                        if poly.intersects(test_blade):
                            res = split(poly, test_blade)
                            p_list = _extract_polygons(res) if res else []
                            if len(p_list) > 1:
                                pieces = p_list
                                break
                    except Exception:
                        continue

                if len(pieces) > 1:
                    target_slice_cid = new_class_id if (new_class_id and new_class_id > 0 and new_class_id != ann.class_id) else ann.class_id
                    target_slice_cname = classes_dict.get(target_slice_cid, ann.class_name)
                    pieces.sort(key=lambda p: p.area, reverse=True)
                    p0 = pieces[0]

                    if not req.persist:
                        created_features = []
                        created_features.append({
                            "type": "Feature",
                            "geometry": mapping(p0),
                            "properties": {
                                "class_id": ann.class_id,
                                "class_name": ann.class_name,
                                "area_sqm": p0.area * (111320.0 ** 2),
                                "author_name": current_user.full_name or "Unknown",
                            }
                        })
                        for p in pieces[1:]:
                            created_features.append({
                                "type": "Feature",
                                "geometry": mapping(p),
                                "properties": {
                                    "class_id": target_slice_cid,
                                    "class_name": target_slice_cname,
                                    "area_sqm": p.area * (111320.0 ** 2),
                                    "author_name": current_user.full_name or "Unknown",
                                }
                            })
                        return {
                            "message": "Poligon berhasil dipotong dengan garis pemisah!",
                            "deleted_ids": [ann.id],
                            "created_features": created_features
                        }

                    split_occurred = True
                    deleted_ids.append(ann.id)
                    db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == ann.id).update(
                        {"annotation_id": None}, synchronize_session=False
                    )
                    db.delete(ann)
                    ann_p0 = Annotation(
                        task_grid_id=req.task_grid_id,
                        user_id=current_user.id,
                        class_id=ann.class_id,
                        class_name=ann.class_name,
                        geom_geojson=json.dumps(mapping(p0)),
                        area_sqm=p0.area * (111320.0 ** 2)
                    )
                    db.add(ann_p0)
                    new_annotations_list.append(ann_p0)

                    for p in pieces[1:]:
                        ann_pi = Annotation(
                            task_grid_id=req.task_grid_id,
                            user_id=current_user.id,
                            class_id=target_slice_cid,
                            class_name=target_slice_cname,
                            geom_geojson=json.dumps(mapping(p)),
                            area_sqm=p.area * (111320.0 ** 2)
                        )
                        db.add(ann_pi)
                        new_annotations_list.append(ann_pi)

                    break # Target bisected, stop cascade-cutting other polygons!

    if not split_occurred:
        raise HTTPException(status_code=400, detail="Garis pemotong harus melintasi batas poligon dari ujung ke ujung.")

    if task.status in ["ASSIGNED", "UNASSIGNED", "REVISION_NEEDED"]:
        task.status = "IN_PROGRESS"

    db.commit()

    created_features = []
    for na in new_annotations_list:
        db.refresh(na)
        created_features.append({
            "type": "Feature",
            "id": na.id,
            "geometry": json.loads(na.geom_geojson),
            "properties": {
                "id": na.id,
                "class_id": na.class_id,
                "class_name": na.class_name,
                "user_id": na.user_id,
                "author_name": current_user.full_name or "Unknown",
                "area_sqm": na.area_sqm,
                "created_at": na.created_at.isoformat() if na.created_at else None
            }
        })

    return {
        "message": "Poligon berhasil dipotong dengan garis pemisah!",
        "deleted_ids": deleted_ids,
        "created_features": created_features
    }


@router.post("/merge")
def merge_polygons(
    req: MergePolygonsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Merges multiple adjacent polygons into a single polygon.
    """
    from shapely.geometry import shape, mapping
    from shapely.ops import unary_union
    
    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}

    if req.features and len(req.features) >= 2:
        geoms = []
        for f in req.features:
            try:
                g = shape(f["geometry"])
                if not g.is_valid:
                    g = g.buffer(0)
                geoms.append(g)
            except Exception:
                pass

        if not geoms:
            raise HTTPException(status_code=400, detail="Geometri poligon tidak valid.")

        if req.target_class_id and req.target_class_id in classes_dict:
            target_class_id = req.target_class_id
            target_class_name = classes_dict[target_class_id]
        else:
            target_class_id = req.features[0].get("properties", {}).get("class_id", 1)
            target_class_name = classes_dict.get(target_class_id, "Tutupan Lahan")

        merged_geom = unary_union(geoms)
        try:
            from shapely import set_precision
            merged_geom = set_precision(merged_geom, grid_size=1e-7)
        except Exception:
            pass

        merged_polys = _extract_polygons(merged_geom, min_area_sqm=0.1)
        if len(merged_polys) > 1:
            try:
                buffered_union = unary_union([g.buffer(1.5e-5) for g in geoms]).buffer(-1.5e-5)
                bridged_polys = _extract_polygons(buffered_union, min_area_sqm=0.1)
                if len(bridged_polys) == 1:
                    merged_polys = bridged_polys
            except Exception:
                pass

        cleaned_merged_polys = []
        for mp in merged_polys:
            cleaned_p = _clean_spikes_and_holes(mp)
            if cleaned_p and not cleaned_p.is_empty and cleaned_p.area > 1e-12:
                cleaned_merged_polys.append(cleaned_p)
        merged_polys = cleaned_merged_polys or merged_polys

        if not merged_polys or len(merged_polys) > 1:
            raise HTTPException(
                status_code=400,
                detail="Poligon yang dipilih tidak bersebelahan atau tidak bersentuhan. Hanya poligon yang bersentuhan yang dapat digabungkan."
            )

        final_merged = merged_polys[0]
        created_feat = {
            "type": "Feature",
            "geometry": mapping(final_merged),
            "properties": {
                "class_id": target_class_id,
                "class_name": target_class_name,
                "area_sqm": final_merged.area * (111320.0 ** 2),
                "author_name": current_user.full_name or "Unknown",
            }
        }
        if not req.persist:
            del_ids = [f.get("id") for f in req.features if f.get("id") and (isinstance(f.get("id"), int) or (isinstance(f.get("id"), str) and str(f.get("id")).isdigit()))]
            del_ui_ids = [f.get("_uiId") for f in req.features if f.get("_uiId")]
            return {
                "message": f"Berhasil menggabungkan {len(req.features)} poligon menjadi 1 poligon '{target_class_name}'!",
                "deleted_ids": del_ids,
                "deleted_ui_ids": del_ui_ids,
                "created_features": [created_feat]
            }

    valid_int_ids = []
    if req.annotation_ids:
        for aid in req.annotation_ids:
            if isinstance(aid, int):
                valid_int_ids.append(aid)
            elif isinstance(aid, str) and aid.isdigit():
                valid_int_ids.append(int(aid))

    if not valid_int_ids or len(valid_int_ids) < 2:
        raise HTTPException(status_code=400, detail="Pilih minimal 2 poligon untuk digabungkan.")
        
    query = db.query(Annotation).filter(Annotation.id.in_(valid_int_ids))
    if req.task_grid_id:
        query = query.filter(Annotation.task_grid_id == req.task_grid_id)
    annotations = query.all()
    
    if len(annotations) < 2:
        raise HTTPException(status_code=404, detail="Poligon yang dipilih tidak ditemukan.")
    if req.target_class_id and req.target_class_id in classes_dict:
        target_class_id = req.target_class_id
        target_class_name = classes_dict[target_class_id]
    else:
        # Fallback to the annotation with the LARGEST area among selected polygons
        def _get_area(ann):
            try:
                if ann.area_sqm:
                    return float(ann.area_sqm)
                return shape(json.loads(ann.geom_geojson)).area
            except Exception:
                return 0.0
        largest_ann = max(annotations, key=_get_area)
        target_class_id = largest_ann.class_id
        target_class_name = classes_dict.get(target_class_id, largest_ann.class_name)

    geoms = []
    for ann in annotations:
        try:
            poly = shape(json.loads(ann.geom_geojson))
            if not poly.is_valid:
                poly = poly.buffer(0)
            geoms.append(poly)
        except Exception:
            pass

    if not geoms:
        raise HTTPException(status_code=400, detail="Geometri poligon tidak valid.")

    merged_geom = unary_union(geoms)
    try:
        from shapely import set_precision
        merged_geom = set_precision(merged_geom, grid_size=1e-7)
    except Exception:
        pass

    merged_polys = _extract_polygons(merged_geom, min_area_sqm=0.1)

    # If unary_union produced > 1 polygon, attempt micro-gap bridging (up to ~1.5 meters)
    if len(merged_polys) > 1:
        try:
            buffered_union = unary_union([g.buffer(1.5e-5) for g in geoms]).buffer(-1.5e-5)
            bridged_polys = _extract_polygons(buffered_union, min_area_sqm=0.1)
            if len(bridged_polys) == 1:
                merged_polys = bridged_polys
        except Exception:
            pass

    # Clean any whiskers, turnaround spikes, or collapsed slit lines
    cleaned_merged_polys = []
    for mp in merged_polys:
        cleaned_p = _clean_spikes_and_holes(mp)
        if cleaned_p and not cleaned_p.is_empty and cleaned_p.area > 1e-12:
            cleaned_merged_polys.append(cleaned_p)
    merged_polys = cleaned_merged_polys or merged_polys

    if not merged_polys:
        raise HTTPException(status_code=400, detail="Gagal menggabungkan geometri poligon terpilih.")

    if len(merged_polys) > 1:
        raise HTTPException(
            status_code=400,
            detail="Poligon yang dipilih tidak bersebelahan atau tidak bersentuhan. Hanya poligon yang bertampalan atau berbatasan langsung yang dapat digabungkan."
        )

    # Strictly 1 singlepart merged polygon
    final_merged_poly = merged_polys[0]

    ann_ids = [ann.id for ann in annotations]
    if not req.persist:
        created_feat = {
            "type": "Feature",
            "geometry": mapping(final_merged_poly),
            "properties": {
                "class_id": target_class_id,
                "class_name": target_class_name,
                "area_sqm": final_merged_poly.area * (111320.0 ** 2),
                "author_name": current_user.full_name or "Unknown",
            }
        }
        return {
            "message": f"Berhasil menggabungkan {len(annotations)} poligon menjadi 1 poligon '{target_class_name}'!",
            "deleted_ids": ann_ids,
            "created_features": [created_feat]
        }

    # Delete old annotations (safeguard review pins)
    db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id.in_(ann_ids)).update({"annotation_id": None}, synchronize_session=False)
    for ann in annotations:
        db.delete(ann)

    area_sqm = final_merged_poly.area * (111320.0 ** 2)
    m_ann = Annotation(
        task_grid_id=req.task_grid_id,
        user_id=current_user.id,
        class_id=target_class_id,
        class_name=target_class_name,
        geom_geojson=json.dumps(mapping(final_merged_poly)),
        area_sqm=area_sqm
    )
    db.add(m_ann)
    db.commit()
    db.refresh(m_ann)

    new_merged_annotations = [m_ann]

    created_features = []
    for ma in new_merged_annotations:
        db.refresh(ma)
        created_features.append({
            "type": "Feature",
            "id": ma.id,
            "geometry": json.loads(ma.geom_geojson),
            "properties": {
                "id": ma.id,
                "class_id": ma.class_id,
                "class_name": ma.class_name,
                "user_id": ma.user_id,
                "author_name": current_user.full_name or "Unknown",
                "area_sqm": ma.area_sqm,
                "created_at": ma.created_at.isoformat() if ma.created_at else None
            }
        })

    return {
        "message": f"Berhasil menggabungkan {len(annotations)} poligon menjadi 1 poligon '{target_class_name}'!",
        "deleted_ids": ann_ids,
        "created_features": created_features
    }


@router.post("/grid/{task_grid_id}/merge")
def merge_polygons_grid_alias(
    task_grid_id: int,
    req: GridMergePolygonsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Alias endpoint for merging polygons by task_grid_id in the URL path.
    """
    unified_req = MergePolygonsRequest(
        task_grid_id=task_grid_id,
        annotation_ids=req.annotation_ids,
        target_class_id=req.target_class_id
    )
    return merge_polygons(unified_req, db, current_user)


class SmartDeleteRequest(BaseModel):
    annotation_id: int
    absorb_into_id: Optional[int] = None


@router.post("/grid/{task_grid_id}/smart-delete")
def smart_delete_polygon(
    task_grid_id: int,
    req: SmartDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Deletes a polygon by absorbing / merging it into an adjacent neighboring polygon,
    ensuring no void/hole/gap is left behind in the land cover training dataset.
    """
    target = db.query(Annotation).filter(
        Annotation.id == req.annotation_id,
        Annotation.task_grid_id == task_grid_id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Poligon target tidak ditemukan.")

    other_annotations = db.query(Annotation).filter(
        Annotation.task_grid_id == task_grid_id,
        Annotation.id != target.id
    ).all()

    if not other_annotations:
        raise HTTPException(
            status_code=400,
            detail="Ini adalah satu-satunya poligon di dalam grid. Poligon tunggal tidak dapat dihapus karena akan mengosongkan seluruh grid tile."
        )

    try:
        t_poly = shape(json.loads(target.geom_geojson))
        if not t_poly.is_valid:
            t_poly = t_poly.buffer(0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Geometri poligon target tidak valid: {str(e)}")

    neighbor_candidates = []
    for o in other_annotations:
        try:
            o_poly = shape(json.loads(o.geom_geojson))
            if not o_poly.is_valid:
                o_poly = o_poly.buffer(0)

            # Check adjacency (touching or buffered intersection to handle micro gaps)
            shared_boundary_len = 0.0
            is_touching = t_poly.touches(o_poly) or t_poly.intersects(o_poly)
            if is_touching:
                inter = t_poly.intersection(o_poly)
                shared_boundary_len = inter.length if inter.length > 0 else inter.area
            else:
                # Slight buffer for micro-precision gaps from snapping
                buffered_t = t_poly.buffer(1e-6)
                if buffered_t.intersects(o_poly):
                    inter = buffered_t.intersection(o_poly)
                    shared_boundary_len = inter.area

            neighbor_candidates.append({
                "annotation": o,
                "geom": o_poly,
                "shared_len": shared_boundary_len,
                "distance": t_poly.distance(o_poly)
            })
        except Exception:
            continue

    if not neighbor_candidates:
        raise HTTPException(status_code=400, detail="Tidak ditemukan poligon tetangga yang valid.")

    chosen_neighbor = None
    if req.absorb_into_id:
        match = [c for c in neighbor_candidates if c["annotation"].id == req.absorb_into_id]
        if match:
            chosen_neighbor = match[0]

    if not chosen_neighbor:
        # Sort by longest shared boundary, then minimum distance
        neighbor_candidates.sort(key=lambda x: (x["shared_len"], -x["distance"]), reverse=True)
        chosen_neighbor = neighbor_candidates[0]

    target_neighbor_ann = chosen_neighbor["annotation"]
    neighbor_poly = chosen_neighbor["geom"]

    # Union the two geometries
    merged_geom = unary_union([neighbor_poly, t_poly])
    merged_polys = _extract_polygons(merged_geom)

    if not merged_polys:
        raise HTTPException(status_code=500, detail="Gagal menggabungkan geometri poligon.")

    # Delete the target polygon (safeguard review pins)
    db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == target.id).update({"annotation_id": None}, synchronize_session=False)
    db.delete(target)

    # Update neighbor annotation with unioned geometry
    main_poly = merged_polys[0]
    area_sqm = main_poly.area * (111320.0 ** 2)
    target_neighbor_ann.geom_geojson = json.dumps(mapping(main_poly))
    target_neighbor_ann.area_sqm = area_sqm

    # If unary_union split into multiple distinct parts (e.g. multi-polygon), add remaining
    extra_annotations = []
    for extra_poly in merged_polys[1:]:
        extra_area = extra_poly.area * (111320.0 ** 2)
        ex_ann = Annotation(
            task_grid_id=task_grid_id,
            user_id=current_user.id,
            class_id=target_neighbor_ann.class_id,
            class_name=target_neighbor_ann.class_name,
            geom_geojson=json.dumps(mapping(extra_poly)),
            area_sqm=extra_area
        )
        db.add(ex_ann)
        extra_annotations.append(ex_ann)

    db.commit()
    db.refresh(target_neighbor_ann)

    updated_features_res = [{
        "type": "Feature",
        "id": target_neighbor_ann.id,
        "geometry": json.loads(target_neighbor_ann.geom_geojson),
        "properties": {
            "id": target_neighbor_ann.id,
            "class_id": target_neighbor_ann.class_id,
            "class_name": target_neighbor_ann.class_name,
            "user_id": target_neighbor_ann.user_id,
            "author_name": current_user.full_name or "Unknown",
            "area_sqm": target_neighbor_ann.area_sqm,
            "created_at": target_neighbor_ann.created_at.isoformat() if target_neighbor_ann.created_at else None
        }
    }]

    created_features_res = []
    for ex_ann in extra_annotations:
        db.refresh(ex_ann)
        created_features_res.append({
            "type": "Feature",
            "id": ex_ann.id,
            "geometry": json.loads(ex_ann.geom_geojson),
            "properties": {
                "id": ex_ann.id,
                "class_id": ex_ann.class_id,
                "class_name": ex_ann.class_name,
                "user_id": ex_ann.user_id,
                "author_name": current_user.full_name or "Unknown",
                "area_sqm": ex_ann.area_sqm,
                "created_at": ex_ann.created_at.isoformat() if ex_ann.created_at else None
            }
        })

    return {
        "message": f"Poligon berhasil dihapus dan disatukan ke '{target_neighbor_ann.class_name}'!",
        "absorbed_into_class": target_neighbor_ann.class_name,
        "absorbed_into_id": target_neighbor_ann.id,
        "deleted_ids": [target.id],
        "updated_features": updated_features_res,
        "created_features": created_features_res
    }


# ─────────────────────────────────────────────
# AI-ASSISTED DIGITIZING (Magic Wand / Interactive Segment)
# ─────────────────────────────────────────────

class AISegmentRequest(BaseModel):
    task_grid_id: Optional[int] = None
    grid_code: Optional[str] = None
    lat: float
    lon: float
    year: Optional[int] = None
    tolerance: Optional[float] = 25.0
    mode: Optional[str] = "click"

@router.post("/ai-segment")
def ai_segment_proposal(
    req: AISegmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    AI-Assisted Magic Wand segmentation:
    Analyzes local Sentinel-2 multi-spectral reflectance around (lat, lon),
    performs adaptive contour segmentation, calculates spectral indices (NDVI/NDWI),
    and returns a candidate GeoJSON polygon with auto-classified land cover.
    """
    if req.task_grid_id:
        grid = db.query(TaskGrid).filter(TaskGrid.id == req.task_grid_id).first()
    elif req.grid_code:
        grid = db.query(TaskGrid).filter(TaskGrid.grid_code == req.grid_code).first()
    else:
        raise HTTPException(status_code=400, detail="task_grid_id atau grid_code harus disertakan")

    if not grid:
        raise HTTPException(status_code=404, detail="Grid tugas tidak ditemukan")

    target_year = req.year or grid.year or 2025
    from app.api.raster import get_year_raster_index, get_transformer_from_crs
    from pyproj import Transformer
    import rasterio
    import rasterio.features
    from rasterio.windows import Window
    import numpy as np

    # Find matching raster file
    year_index = get_year_raster_index(target_year)
    match = next((item for item in year_index if item["tile_key"] == grid.tile_key), None)
    if not match:
        base_dir = settings.RASTER_BASE_DIR
        if os.path.exists(base_dir):
            for entry in os.listdir(base_dir):
                if str(target_year) in entry:
                    cand = os.path.join(base_dir, entry, f"sentinel2_sumbar_{target_year}_10m-{grid.tile_key}.tif")
                    if os.path.exists(cand):
                        try:
                            with rasterio.open(cand) as src:
                                match = {"path": cand, "crs": src.crs}
                        except Exception:
                            pass
                        break

    candidate_polygon = None
    suggested_class_id = 1
    suggested_class_name = "Hutan Lahan Kering"
    confidence = 0.85

    if match and os.path.exists(match["path"]):
        try:
            with rasterio.open(match["path"]) as src:
                crs_str = str(src.crs) if src.crs else "EPSG:32747"
                trans = get_transformer_from_crs(crs_str)
                inv_trans = Transformer.from_crs(crs_str, "EPSG:4326", always_xy=True)

                native_x, native_y = trans.transform(req.lon, req.lat)
                center_row, center_col = src.index(native_x, native_y)

                # Define window of 48x48 pixels (~480m x 480m at 10m Sentinel-2)
                win_radius = 24
                row_start = max(0, center_row - win_radius)
                col_start = max(0, center_col - win_radius)
                row_end = min(src.height, center_row + win_radius)
                col_end = min(src.width, center_col + win_radius)

                win_h = row_end - row_start
                win_w = col_end - col_start

                if win_h > 4 and win_w > 4:
                    win = Window(col_start, row_start, win_w, win_h)
                    band_count = min(4, src.count)
                    bands_to_read = tuple(range(1, band_count + 1))
                    data = src.read(bands_to_read, window=win).astype(np.float32)

                    local_y = center_row - row_start
                    local_x = center_col - col_start
                    local_y = max(0, min(win_h - 1, local_y))
                    local_x = max(0, min(win_w - 1, local_x))

                    seed_val = data[:, local_y, local_x]

                    # Multi-spectral Euclidean difference
                    diff = np.sqrt(np.sum((data - seed_val[:, None, None])**2, axis=0))

                    # Adaptive percentile threshold
                    tol_percentile = max(5.0, min(75.0, req.tolerance or 25.0))
                    thresh = np.percentile(diff, tol_percentile)
                    binary_mask = (diff <= thresh).astype(np.uint8)

                    # BFS flood-fill from seed to keep connected region
                    visited = np.zeros((win_h, win_w), dtype=np.uint8)
                    queue = [(local_y, local_x)]
                    visited[local_y, local_x] = 1
                    max_pixels = 1200
                    count = 0
                    while queue and count < max_pixels:
                        cy, cx = queue.pop(0)
                        count += 1
                        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < win_h and 0 <= nx < win_w:
                                if not visited[ny, nx] and binary_mask[ny, nx]:
                                    visited[ny, nx] = 1
                                    queue.append((ny, nx))

                    # Convert binary mask into polygon using window affine transform
                    win_transform = rasterio.windows.transform(win, src.transform)
                    shapes = list(rasterio.features.shapes(visited, mask=(visited == 1), transform=win_transform))

                    if shapes:
                        best_geom = None
                        max_area = 0
                        for geom_dict, val in shapes:
                            if val == 1:
                                p = shape(geom_dict)
                                if p.area > max_area:
                                    max_area = p.area
                                    best_geom = p

                        if best_geom and best_geom.is_valid:
                            # Re-project polygon vertices back to WGS84 (lon, lat)
                            def transform_to_wgs84(poly_obj):
                                def reproject_ring(coords):
                                    return [inv_trans.transform(x, y) for x, y in coords]
                                if poly_obj.geom_type == 'Polygon':
                                    ext = reproject_ring(poly_obj.exterior.coords)
                                    interiors = [reproject_ring(r.coords) for r in poly_obj.interiors]
                                    return Polygon(ext, interiors)
                                return poly_obj

                            wgs_poly = transform_to_wgs84(best_geom)
                            wgs_poly = wgs_poly.simplify(0.00002, preserve_topology=True)
                            if wgs_poly.is_valid and not wgs_poly.is_empty:
                                candidate_polygon = wgs_poly

                                # Compute NDVI & NDWI to infer Land Cover Class
                                # Band 1: Blue, Band 2: Green, Band 3: Red, Band 4: NIR (if count >= 4)
                                if data.shape[0] >= 4:
                                    blue = np.mean(data[0][visited == 1])
                                    green = np.mean(data[1][visited == 1])
                                    red = np.mean(data[2][visited == 1])
                                    nir = np.mean(data[3][visited == 1])

                                    denom_ndvi = nir + red + 1e-5
                                    ndvi = (nir - red) / denom_ndvi
                                    denom_ndwi = green + nir + 1e-5
                                    ndwi = (green - nir) / denom_ndwi

                                    if ndwi > 0.08:
                                        suggested_class_id = 9
                                        suggested_class_name = "Tubuh Air"
                                        confidence = 0.94
                                    elif ndvi > 0.65:
                                        suggested_class_id = 1
                                        suggested_class_name = "Hutan Lahan Kering"
                                        confidence = 0.90
                                    elif ndvi > 0.35:
                                        suggested_class_id = 4
                                        suggested_class_name = "Pertanian Lahan Kering"
                                        confidence = 0.85
                                    elif ndvi < 0.18:
                                        suggested_class_id = 6
                                        suggested_class_name = "Bangunan & Permukiman"
                                        confidence = 0.82
                                    else:
                                        suggested_class_id = 3
                                        suggested_class_name = "Semak & Belukar"
                                        confidence = 0.80
        except Exception as e:
            pass

    # Fallback to smooth polygon (~20m radius) if raster processing was unavailable
    if not candidate_polygon:
        delta = 0.00018 # ~20 meters
        candidate_polygon = box(req.lon - delta, req.lat - delta, req.lon + delta, req.lat + delta).buffer(0.00004)

    area_sqm = candidate_polygon.area * (111320.0 ** 2)

    return {
        "type": "Feature",
        "geometry": mapping(candidate_polygon),
        "properties": {
            "suggested_class_id": suggested_class_id,
            "suggested_class_name": suggested_class_name,
            "confidence": round(confidence, 2),
            "area_sqm": round(area_sqm, 2),
            "area_ha": round(area_sqm / 10000.0, 3)
        }
    }


@router.post("/fix-multipolygons")
def fix_all_multipolygons_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Self-heal database migration endpoint:
    Finds any MultiPolygon or GeometryCollection annotations across all grids
    and safely explodes them into independent singlepart Polygon annotations.
    """
    from app.db.explode_all_multipolygons import explode_all_multipolygons
    result = explode_all_multipolygons(db=db)
    return {
        "message": f"Berhasil memproses pemecahan multi-part poligon: {result['deleted_multipart_count']} multi-part dipecah menjadi {result['created_singlepart_count']} poligon tunggal.",
        "details": result
    }




