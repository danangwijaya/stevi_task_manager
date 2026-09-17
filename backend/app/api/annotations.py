from typing import Any, List, Dict, Optional
import json
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from shapely.geometry import shape

from app.db.session import get_db
from app.db.models import Annotation, TaskGrid, User, LandCoverClass
from app.core.config import settings
from app.api.deps import get_current_user

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
        geom = json.loads(ann.geom_geojson)
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
        
    return {
        "type": "FeatureCollection",
        "task_grid_id": task_grid_id,
        "grid_code": task.grid_code,
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
        
    if current_user.role != "admin" and task.assigned_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit annotations for this task")

    # Clear previous annotations for this grid to sync cleanly
    db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).delete()
    
    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}

    new_annotations = []
    for f in data.features:
        class_id = int(f.properties.get("class_id", 1))
        class_name = f.properties.get("class_name", classes_dict.get(class_id, "Unknown"))
        
        # Calculate area approx
        geom_dict = f.geometry
        try:
            s_geom = shape(geom_dict)
            # 1 deg ~ 111km
            area_deg = s_geom.area
            area_sqm = area_deg * (111320.0 ** 2)
        except Exception:
            area_sqm = 0.0

        ann = Annotation(
            task_grid_id=task_grid_id,
            user_id=current_user.id,
            class_id=class_id,
            class_name=class_name,
            geom_geojson=json.dumps(geom_dict),
            area_sqm=area_sqm
        )
        db.add(ann)
        new_annotations.append(ann)
        
    # Auto mark task as IN_PROGRESS if it was ASSIGNED
    if task.status in ["ASSIGNED", "REVISION_NEEDED"]:
        task.status = "IN_PROGRESS"
        
    db.commit()
    return {"message": f"Successfully saved {len(new_annotations)} annotation polygons", "count": len(new_annotations)}

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
        
    if current_user.role != "admin" and target_task.assigned_user_id != current_user.id:
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
    
    if current_user.role != "admin" and task.assigned_user_id != current_user.id:
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

    base_ann = Annotation(
        task_grid_id=task_grid_id,
        user_id=current_user.id,
        class_id=0,
        class_name="Belum Terklasifikasi",
        geom_geojson=json.dumps(base_geom),
        area_sqm=area_sqm
    )
    db.add(base_ann)

    # Auto-set task to IN_PROGRESS if still ASSIGNED
    if task.status in ["ASSIGNED", "UNASSIGNED"]:
        task.status = "IN_PROGRESS"

    db.commit()
    db.refresh(base_ann)
    return {
        "message": "Base polygon 'Belum Terklasifikasi' berhasil dibuat menutupi seluruh area grid",
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
    5. Check for remaining 'Belum Terklasifikasi' polygons
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
                "message": f"Poligon memiliki geometri tidak valid: {reason}"
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

    # 2. Overlap detection (pairwise)
    OVERLAP_THRESHOLD = 1e-10  # ~1 sq meter in degree² terms
    for i in range(len(shapely_polygons)):
        for j in range(i + 1, len(shapely_polygons)):
            try:
                intersection = shapely_polygons[i]["geom"].intersection(shapely_polygons[j]["geom"])
                if intersection.area > OVERLAP_THRESHOLD:
                    overlap_pct = (intersection.area / grid_area) * 100
                    errors.append({
                        "type": "OVERLAP",
                        "annotation_ids": [shapely_polygons[i]["ann"].id, shapely_polygons[j]["ann"].id],
                        "class_names": [shapely_polygons[i]["ann"].class_name, shapely_polygons[j]["ann"].class_name],
                        "message": f"Tumpang tindih terdeteksi ({overlap_pct:.4f}% dari grid) antara poligon #{shapely_polygons[i]['ann'].id} ({shapely_polygons[i]['ann'].class_name}) dan #{shapely_polygons[j]['ann'].id} ({shapely_polygons[j]['ann'].class_name})"
                    })
            except Exception:
                pass

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
            if gap_area.area > OVERLAP_THRESHOLD:
                gap_pct = (gap_area.area / grid_area) * 100
                if gap_pct > 5.0:
                    errors.append({
                        "type": "GAP",
                        "message": f"Area kosong (gap) terdeteksi: {gap_pct:.2f}% dari grid belum tercakup poligon"
                    })
                elif gap_pct > 0.5:
                    warnings.append({
                        "type": "SMALL_GAP",
                        "message": f"Area kosong kecil terdeteksi: {gap_pct:.2f}% dari grid — pertimbangkan untuk menutup celah"
                    })
    except Exception as e:
        warnings.append({
            "type": "COVERAGE_CALC_ERROR",
            "message": f"Gagal menghitung cakupan: {str(e)}"
        })

    # Unclassified warning
    if unclassified_ids:
        errors.append({
            "type": "UNCLASSIFIED",
            "annotation_ids": unclassified_ids,
            "message": f"{len(unclassified_ids)} poligon masih berstatus 'Belum Terklasifikasi'. Assign kelas tutupan lahan sebelum submit."
        })

    is_valid = len(errors) == 0

    return {
        "valid": is_valid,
        "coverage_percent": round(coverage_percent, 2),
        "polygon_count": len(annotations),
        "errors": errors,
        "warnings": warnings
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
        
    if current_user.role != "admin" and ann.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this annotation")
        
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
    new_class_id: Optional[int] = 0

class SplitByLineRequest(BaseModel):
    task_grid_id: int
    line_geom: Dict[str, Any]
    target_annotation_id: Optional[int] = None
    new_class_id: Optional[int] = 0

class MergePolygonsRequest(BaseModel):
    task_grid_id: int
    annotation_ids: List[int]
    target_class_id: int

class UpdateAnnotationClassRequest(BaseModel):
    class_id: int


def _extract_polygons(geom):
    """Recursively unpacks GeometryCollection / MultiPolygon into distinct Polygon objects"""
    if geom.is_empty:
        return []
    if geom.geom_type == 'Polygon':
        return [geom] if geom.area > 1e-12 else []
    elif geom.geom_type == 'MultiPolygon':
        return [g for g in geom.geoms if g.area > 1e-12]
    elif geom.geom_type == 'GeometryCollection':
        polys = []
        for g in geom.geoms:
            polys.extend(_extract_polygons(g))
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


def _extend_line(line, factor=0.2):
    """Extend line slightly at both ends so split() cuts across polygon boundaries reliably"""
    from shapely.geometry import LineString
    try:
        coords = list(line.coords)
        if len(coords) < 2:
            return line
        dx0 = coords[0][0] - coords[1][0]
        dy0 = coords[0][1] - coords[1][1]
        p0_ext = (coords[0][0] + dx0 * factor, coords[0][1] + dy0 * factor)
        
        dx1 = coords[-1][0] - coords[-2][0]
        dy1 = coords[-1][1] - coords[-2][1]
        p1_ext = (coords[-1][0] + dx1 * factor, coords[-1][1] + dy1 * factor)
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
    new_class_name = classes_dict.get(new_class_id, "Belum Terklasifikasi")

    # Fetch candidate annotations
    query = db.query(Annotation).filter(Annotation.task_grid_id == req.task_grid_id)
    if req.target_annotation_id:
        query = query.filter(Annotation.id == req.target_annotation_id)
    annotations = query.all()

    split_occurred = False
    new_created_count = 0

    # CASE 1: Grid has NO annotations yet! Slice directly from task grid polygon
    if len(annotations) == 0:
        if task_poly:
            inter_polys = _extract_polygons(cutter_in_grid)
            diff_polys = _extract_polygons(task_poly.difference(cutter_in_grid))
            
            if inter_polys:
                # Add intersection pieces (assigned with new_class_id)
                for ip in inter_polys:
                    ip_geojson = mapping(ip)
                    area_sqm = ip.area * (111320.0 ** 2)
                    db.add(Annotation(
                        task_grid_id=req.task_grid_id,
                        user_id=current_user.id,
                        class_id=new_class_id,
                        class_name=new_class_name,
                        geom_geojson=json.dumps(ip_geojson),
                        area_sqm=area_sqm
                    ))
                    new_created_count += 1
                
                # Add difference pieces (remaining area marked as unclassified 0)
                for dp in diff_polys:
                    dp_geojson = mapping(dp)
                    area_sqm = dp.area * (111320.0 ** 2)
                    db.add(Annotation(
                        task_grid_id=req.task_grid_id,
                        user_id=current_user.id,
                        class_id=0,
                        class_name="Belum Terklasifikasi",
                        geom_geojson=json.dumps(dp_geojson),
                        area_sqm=area_sqm
                    ))
                split_occurred = True
        else:
            cut_polys = _extract_polygons(cutter_in_grid)
            for cp in cut_polys:
                area_sqm = cp.area * (111320.0 ** 2)
                db.add(Annotation(
                    task_grid_id=req.task_grid_id,
                    user_id=current_user.id,
                    class_id=new_class_id,
                    class_name=new_class_name,
                    geom_geojson=json.dumps(mapping(cp)),
                    area_sqm=area_sqm
                ))
                new_created_count += 1
            if new_created_count > 0:
                split_occurred = True

    # CASE 2: Grid has existing annotations
    else:
        for ann in annotations:
            try:
                poly = shape(json.loads(ann.geom_geojson))
                if not poly.is_valid:
                    poly = poly.buffer(0)
                    
                if not poly.intersects(cutter):
                    continue

                intersection = poly.intersection(cutter)
                difference = poly.difference(cutter)

                inter_polys = _extract_polygons(intersection)
                diff_polys = _extract_polygons(difference)

                if inter_polys and diff_polys:
                    split_occurred = True
                    # Remove original polygon record
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

                    # Add intersection pieces (assigned with new_class_id)
                    for ip in inter_polys:
                        ip_geojson = mapping(ip)
                        area_sqm = ip.area * (111320.0 ** 2)
                        new_ip = Annotation(
                            task_grid_id=req.task_grid_id,
                            user_id=current_user.id,
                            class_id=new_class_id,
                            class_name=new_class_name,
                            geom_geojson=json.dumps(ip_geojson),
                            area_sqm=area_sqm
                        )
                        db.add(new_ip)
                        new_created_count += 1
                elif inter_polys and not diff_polys:
                    # Polygon is completely enclosed by cutter -> reclassify
                    split_occurred = True
                    ann.class_id = new_class_id
                    ann.class_name = new_class_name
                    ann.user_id = current_user.id
                    new_created_count += 1
            except Exception:
                continue

        # If cutter didn't split or reclassify any polygon (e.g. drawn in unannotated open space in grid)
        if not split_occurred:
            cut_polys = _extract_polygons(cutter_in_grid)
            for cp in cut_polys:
                area_sqm = cp.area * (111320.0 ** 2)
                db.add(Annotation(
                    task_grid_id=req.task_grid_id,
                    user_id=current_user.id,
                    class_id=new_class_id,
                    class_name=new_class_name,
                    geom_geojson=json.dumps(mapping(cp)),
                    area_sqm=area_sqm
                ))
                new_created_count += 1
            if new_created_count > 0:
                split_occurred = True

    if not split_occurred:
        raise HTTPException(status_code=400, detail="Garis pemotong tidak memotong poligon manapun atau poligon berada di luar area.")

    if task.status in ["ASSIGNED", "UNASSIGNED", "REVISION_NEEDED"]:
        task.status = "IN_PROGRESS"

    db.commit()
    return {"message": "Poligon berhasil dipisah menjadi bagian independen!", "split_count": new_created_count}


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
    new_class_name = classes_dict.get(new_class_id, "Belum Terklasifikasi")

    query = db.query(Annotation).filter(Annotation.task_grid_id == req.task_grid_id)
    if req.target_annotation_id:
        query = query.filter(Annotation.id == req.target_annotation_id)
    annotations = query.all()

    split_occurred = False
    extended_blade = _extend_line(blade, factor=0.15)

    # CASE 1: Grid has NO annotations yet! Slices task grid itself
    if len(annotations) == 0 and task_poly:
        cut_blade = blade if task_poly.intersects(blade) else extended_blade
        if task_poly.intersects(cut_blade):
            try:
                res = split(task_poly, cut_blade)
                pieces = _extract_polygons(res)
                if len(pieces) > 1:
                    split_occurred = True
                    p0 = pieces[0]
                    area_sqm = p0.area * (111320.0 ** 2)
                    db.add(Annotation(
                        task_grid_id=req.task_grid_id,
                        user_id=current_user.id,
                        class_id=0,
                        class_name="Belum Terklasifikasi",
                        geom_geojson=json.dumps(mapping(p0)),
                        area_sqm=area_sqm
                    ))
                    for p in pieces[1:]:
                        area_sqm = p.area * (111320.0 ** 2)
                        db.add(Annotation(
                            task_grid_id=req.task_grid_id,
                            user_id=current_user.id,
                            class_id=new_class_id,
                            class_name=new_class_name,
                            geom_geojson=json.dumps(mapping(p)),
                            area_sqm=area_sqm
                        ))
            except Exception:
                pass

    # CASE 2: Grid has existing annotations
    if not split_occurred and annotations:
        for ann in annotations:
            try:
                poly = shape(json.loads(ann.geom_geojson))
                if not poly.is_valid:
                    poly = poly.buffer(0)
                    
                if not poly.intersects(blade) and not poly.intersects(extended_blade):
                    continue

                # Try original blade first, then extended blade
                res = None
                if poly.intersects(blade):
                    res = split(poly, blade)
                pieces = _extract_polygons(res) if res else []
                
                if len(pieces) <= 1 and poly.intersects(extended_blade):
                    res = split(poly, extended_blade)
                    pieces = _extract_polygons(res)

                if len(pieces) > 1:
                    split_occurred = True
                    db.delete(ann)

                    # Piece 0 gets original class
                    p0 = pieces[0]
                    area_sqm = p0.area * (111320.0 ** 2)
                    db.add(Annotation(
                        task_grid_id=req.task_grid_id,
                        user_id=current_user.id,
                        class_id=ann.class_id,
                        class_name=ann.class_name,
                        geom_geojson=json.dumps(mapping(p0)),
                        area_sqm=area_sqm
                    ))

                    # Remaining pieces get new class
                    for p in pieces[1:]:
                        area_sqm = p.area * (111320.0 ** 2)
                        db.add(Annotation(
                            task_grid_id=req.task_grid_id,
                            user_id=current_user.id,
                            class_id=new_class_id,
                            class_name=new_class_name,
                            geom_geojson=json.dumps(mapping(p)),
                            area_sqm=area_sqm
                        ))
            except Exception:
                continue

    if not split_occurred:
        raise HTTPException(status_code=400, detail="Garis pemotong harus melintasi batas poligon dari ujung ke ujung.")

    if task.status in ["ASSIGNED", "UNASSIGNED", "REVISION_NEEDED"]:
        task.status = "IN_PROGRESS"

    db.commit()
    return {"message": "Poligon berhasil dipotong dengan garis pemisah!"}


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
    
    if len(req.annotation_ids) < 2:
        raise HTTPException(status_code=400, detail="Pilih minimal 2 poligon untuk digabungkan.")
        
    annotations = db.query(Annotation).filter(
        Annotation.task_grid_id == req.task_grid_id,
        Annotation.id.in_(req.annotation_ids)
    ).all()
    
    if len(annotations) < 2:
        raise HTTPException(status_code=404, detail="Poligon yang dipilih tidak ditemukan.")

    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}
    target_class_id = req.target_class_id if req.target_class_id in classes_dict else annotations[0].class_id
    target_class_name = classes_dict.get(target_class_id, annotations[0].class_name)

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
    merged_polys = _extract_polygons(merged_geom)

    # Delete old annotations
    for ann in annotations:
        db.delete(ann)

    # Add merged annotation(s)
    for mp in merged_polys:
        area_sqm = mp.area * (111320.0 ** 2)
        db.add(Annotation(
            task_grid_id=req.task_grid_id,
            user_id=current_user.id,
            class_id=target_class_id,
            class_name=target_class_name,
            geom_geojson=json.dumps(mapping(mp)),
            area_sqm=area_sqm
        ))

    db.commit()
    return {"message": f"Berhasil menggabungkan {len(annotations)} poligon menjadi 1 poligon '{target_class_name}'!"}


