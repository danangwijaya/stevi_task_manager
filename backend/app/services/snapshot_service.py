import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from shapely.geometry import shape

from app.db.models import GridSnapshot, AuditLog, Annotation, TaskGrid, TaskReviewPin
from app.core.config import settings

logger = logging.getLogger("snapshot_service")

def log_audit(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    task_grid_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """Logs an administrative or spatial operation into the audit_logs table."""
    try:
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            task_grid_id=task_grid_id,
            details=details,
            ip_address=ip_address,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        return log_entry
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")
        db.rollback()
        return None

def create_grid_snapshot_from_db(
    db: Session,
    task_grid_id: int,
    user_id: Optional[int],
    note: str = "Draf Disimpan",
    max_revisions: int = 20
) -> Optional[GridSnapshot]:
    """Creates a snapshot from current annotations in the database for the given grid."""
    try:
        annotations = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).all()
        features = []
        for a in annotations:
            try:
                geom = json.loads(a.geom_geojson) if isinstance(a.geom_geojson, str) else a.geom_geojson
            except Exception:
                continue
            features.append({
                "type": "Feature",
                "id": a.id,
                "properties": {
                    "id": a.id,
                    "class_id": a.class_id,
                    "class_name": a.class_name,
                    "area_sqm": a.area_sqm
                },
                "geometry": geom
            })
        
        geojson_str = json.dumps({"type": "FeatureCollection", "features": features})
        
        # Calculate next version
        last_version = db.query(func.max(GridSnapshot.version_number)).filter(GridSnapshot.task_grid_id == task_grid_id).scalar() or 0
        new_version = last_version + 1

        snap = GridSnapshot(
            task_grid_id=task_grid_id,
            user_id=user_id,
            version_number=new_version,
            note=note,
            features_count=len(features),
            geojson_data=geojson_str,
            created_at=datetime.utcnow()
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)

        # Auto-prune old revisions if exceeds max_revisions
        _prune_old_snapshots(db, task_grid_id, max_revisions)

        return snap
    except Exception as e:
        logger.error(f"Error creating snapshot for grid {task_grid_id}: {e}")
        db.rollback()
        return None

def create_grid_snapshot_from_features(
    db: Session,
    task_grid_id: int,
    user_id: Optional[int],
    features: List[Dict[str, Any]],
    note: str = "Draf Disimpan",
    max_revisions: int = 20
) -> Optional[GridSnapshot]:
    """Creates a snapshot directly from a list of GeoJSON features."""
    try:
        geojson_str = json.dumps({"type": "FeatureCollection", "features": features})
        last_version = db.query(func.max(GridSnapshot.version_number)).filter(GridSnapshot.task_grid_id == task_grid_id).scalar() or 0
        new_version = last_version + 1

        snap = GridSnapshot(
            task_grid_id=task_grid_id,
            user_id=user_id,
            version_number=new_version,
            note=note,
            features_count=len(features),
            geojson_data=geojson_str,
            created_at=datetime.utcnow()
        )
        db.add(snap)
        db.commit()
        db.refresh(snap)

        _prune_old_snapshots(db, task_grid_id, max_revisions)

        return snap
    except Exception as e:
        logger.error(f"Error creating snapshot from features for grid {task_grid_id}: {e}")
        db.rollback()
        return None

def _prune_old_snapshots(db: Session, task_grid_id: int, max_revisions: int):
    """Keeps the newest max_revisions snapshots and deletes older ones."""
    try:
        snapshots = (
            db.query(GridSnapshot.id)
            .filter(GridSnapshot.task_grid_id == task_grid_id)
            .order_by(GridSnapshot.version_number.desc())
            .all()
        )
        if len(snapshots) > max_revisions:
            ids_to_delete = [s.id for s in snapshots[max_revisions:]]
            db.query(GridSnapshot).filter(GridSnapshot.id.in_(ids_to_delete)).delete(synchronize_session=False)
            db.commit()
    except Exception as e:
        logger.warning(f"Failed to prune old snapshots for grid {task_grid_id}: {e}")

def restore_grid_snapshot(
    db: Session,
    task_grid_id: int,
    snapshot_id: int,
    user_id: int,
    ip_address: Optional[str] = None
) -> Dict[str, Any]:
    """Restores the annotations of a grid from a specific snapshot."""
    target_snap = db.query(GridSnapshot).filter(
        GridSnapshot.id == snapshot_id,
        GridSnapshot.task_grid_id == task_grid_id
    ).first()
    if not target_snap:
        raise ValueError("Snapshot riwayat tidak ditemukan.")

    # 1. Take safety snapshot of current state before restoring
    create_grid_snapshot_from_db(
        db=db,
        task_grid_id=task_grid_id,
        user_id=user_id,
        note=f"Sebelum Rollback ke v{target_snap.version_number}"
    )

    # 2. Parse GeoJSON data from target snapshot
    try:
        fc = json.loads(target_snap.geojson_data)
        features = fc.get("features", [])
    except Exception as e:
        raise ValueError(f"Data GeoJSON pada snapshot rusak: {e}")

    # 3. Clear existing annotations
    db.query(TaskReviewPin).filter(TaskReviewPin.task_grid_id == task_grid_id).update({"annotation_id": None}, synchronize_session=False)
    db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).delete()

    classes_dict = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}

    new_annotations = []
    for f in features:
        props = f.get("properties", {})
        class_id = int(props.get("class_id", 1))
        class_name = props.get("class_name", classes_dict.get(class_id, "Unknown"))
        geom_dict = f.get("geometry", {})
        
        area_sqm = props.get("area_sqm")
        if area_sqm is None:
            try:
                s_geom = shape(geom_dict)
                area_sqm = s_geom.area * (111320.0 ** 2)
            except Exception:
                area_sqm = 0.0

        ann = Annotation(
            task_grid_id=task_grid_id,
            user_id=user_id,
            class_id=class_id,
            class_name=class_name,
            geom_geojson=json.dumps(geom_dict),
            area_sqm=float(area_sqm)
        )
        new_annotations.append(ann)

    if new_annotations:
        db.bulk_save_objects(new_annotations)

    # Update TaskGrid timestamp
    task = db.query(TaskGrid).filter(TaskGrid.id == task_grid_id).first()
    if task:
        task.updated_at = datetime.utcnow()

    db.commit()

    # 4. Log the audit
    log_audit(
        db=db,
        user_id=user_id,
        action="RESTORE_SNAPSHOT",
        entity_type="task_grid",
        entity_id=task_grid_id,
        task_grid_id=task_grid_id,
        details=json.dumps({
            "restored_snapshot_id": snapshot_id,
            "version_number": target_snap.version_number,
            "features_restored": len(new_annotations),
            "original_note": target_snap.note
        }),
        ip_address=ip_address
    )

    return {
        "success": True,
        "restored_version": target_snap.version_number,
        "features_restored": len(new_annotations),
        "note": target_snap.note
    }
