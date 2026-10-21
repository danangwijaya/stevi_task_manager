"""Delta save: the client sends only what it changed.

The full-grid save (POST /annotations/grid/{id}) deletes every row that is missing from the payload, so a stale
tab or a re-sent request can erase or duplicate other work. Here nothing is deleted unless the client names it,
inserts are keyed by a client-assigned `client_uid` (re-sends are idempotent) and every update or delete carries
the row `version` (its updated_at) the client last saw: if the row changed since, the server keeps its own
version ("server wins") and returns it in `conflicts` so the client refreshes just that row.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from shapely.geometry import mapping, shape
from sqlalchemy.orm import Session

from app.api.annotations import (
    _extract_polygons,
    _near_duplicate_pairs,
    _parse_client_time,
    _require_grid_edit_access,
    _utc_iso,
)
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.models import Annotation, TaskReviewPin, User
from app.db.session import get_db
from app.services.snapshot_service import log_audit, record_autosave_snapshot

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_CHANGES_PER_REQUEST = 5000
VERSION_TOLERANCE = timedelta(milliseconds=1)
SQM_PER_DEG2 = 111320.0 ** 2


class ChangeFeature(BaseModel):
    id: Optional[int] = None            # database id, when the client knows it
    client_uid: Optional[str] = None    # key of a polygon the client created
    version: Optional[str] = None       # `version` the client last received for this id
    geometry: Dict[str, Any]
    properties: Dict[str, Any] = {}


class DeleteRef(BaseModel):
    id: int
    version: Optional[str] = None


class GridChangesRequest(BaseModel):
    upserts: List[ChangeFeature] = []
    deletes: List[DeleteRef] = []


def _feature_json(row: Annotation, author_name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "type": "Feature",
        "id": row.id,
        "geometry": json.loads(row.geom_geojson),
        "properties": {
            "id": row.id,
            "client_uid": row.client_uid,
            "class_id": row.class_id,
            "class_name": row.class_name,
            "user_id": row.user_id,
            "author_name": author_name,
            "area_sqm": row.area_sqm,
            "version": _utc_iso(row.updated_at) if row.updated_at else None,
        },
    }


def _changed_since(row: Annotation, version: Optional[str]) -> bool:
    """True when `row` was modified after the version the client knows. A missing version means no check."""
    known = _parse_client_time(version)
    if known is None or row.updated_at is None:
        return False
    return row.updated_at - known > VERSION_TOLERANCE


def _clean_parts(geometry: Dict[str, Any]):
    s_geom = shape(geometry)
    if s_geom.is_valid and s_geom.geom_type == "Polygon" and len(s_geom.interiors) == 0:
        return [s_geom]
    return _extract_polygons(s_geom, min_area_sqm=0.1)


@router.post("/grid/{task_grid_id}/changes")
def save_grid_changes(
    task_grid_id: int,
    req: GridChangesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    if len(req.upserts) + len(req.deletes) > MAX_CHANGES_PER_REQUEST:
        raise HTTPException(status_code=413, detail=f"Terlalu banyak perubahan dalam satu permintaan (maks {MAX_CHANGES_PER_REQUEST}).")

    task = _require_grid_edit_access(db, task_grid_id, current_user)
    if task.assigned_user_id is None:
        task.assigned_user_id = current_user.id
    if task.status in ("ASSIGNED", "REVISION_NEEDED", "UNASSIGNED"):
        task.status = "IN_PROGRESS"

    classes = {c["id"]: c["name"] for c in settings.LAND_COVER_CLASSES}

    ids = {u.id for u in req.upserts if u.id is not None} | {d.id for d in req.deletes}
    uids = {u.client_uid for u in req.upserts if u.client_uid}
    by_id: Dict[int, Annotation] = {}
    by_uid: Dict[str, Annotation] = {}
    if ids:
        for a in db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id, Annotation.id.in_(ids)).all():
            by_id[a.id] = a
    if uids:
        for a in db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id, Annotation.client_uid.in_(uids)).all():
            by_uid[a.client_uid] = a

    touched: List[Annotation] = []        # rows written by this request (inserted or updated)
    conflicts: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    extra_new: List[Annotation] = []      # additional rows when a cleaned polygon splits into several parts
    id_map: Dict[str, int] = {}

    for u in req.upserts:
        key = u.client_uid or (str(u.id) if u.id is not None else None)
        try:
            class_id = int(u.properties.get("class_id") or 0)
        except (TypeError, ValueError):
            class_id = 0
        if class_id not in classes:
            class_id = 0
        class_name = classes.get(class_id, "Belum Teridentifikasi")
        try:
            parts = _clean_parts(u.geometry)
        except Exception as e:
            rejected.append({"id": u.id, "client_uid": u.client_uid, "reason": f"Geometri tidak valid: {e}"})
            continue
        if not parts:
            rejected.append({"id": u.id, "client_uid": u.client_uid, "reason": "Geometri kosong atau terlalu kecil setelah dibersihkan."})
            continue

        row = by_id.get(u.id) if u.id is not None else None
        if u.id is not None and row is None:
            rejected.append({"id": u.id, "client_uid": u.client_uid, "reason": "Poligon tidak ditemukan di grid ini (mungkin sudah dihapus)."})
            continue
        if row is None and u.client_uid:
            row = by_uid.get(u.client_uid)            # replay of an insert: update the same row
        elif row is not None and _changed_since(row, u.version):
            conflicts.append({"id": row.id, "client_uid": u.client_uid, "reason": "changed", "server_feature": _feature_json(row)})
            continue

        first = parts[0]
        if row is None:
            row = Annotation(task_grid_id=task_grid_id, user_id=current_user.id, client_uid=u.client_uid,
                             class_id=class_id, class_name=class_name,
                             geom_geojson=json.dumps(mapping(first)), area_sqm=first.area * SQM_PER_DEG2)
            db.add(row)
            if u.client_uid:
                by_uid[u.client_uid] = row            # a duplicate uid later in this request updates this row
        else:
            row.class_id, row.class_name = class_id, class_name
            row.geom_geojson = json.dumps(mapping(first))
            row.area_sqm = first.area * SQM_PER_DEG2
        touched.append(row)
        for n, extra in enumerate(parts[1:], start=1):
            e_row = Annotation(task_grid_id=task_grid_id, user_id=current_user.id,
                               client_uid=f"{u.client_uid}#{n}" if u.client_uid else None,
                               class_id=class_id, class_name=class_name,
                               geom_geojson=json.dumps(mapping(extra)), area_sqm=extra.area * SQM_PER_DEG2)
            db.add(e_row)
            extra_new.append(e_row)

    deleted: List[int] = []
    for d in req.deletes:
        row = by_id.get(d.id)
        if row is None:
            deleted.append(d.id)                     # already gone: the delete is satisfied
            continue
        if _changed_since(row, d.version):
            conflicts.append({"id": row.id, "client_uid": None, "reason": "changed", "server_feature": _feature_json(row)})
            continue
        db.query(TaskReviewPin).filter(TaskReviewPin.annotation_id == row.id).update({"annotation_id": None}, synchronize_session=False)
        db.delete(row)
        deleted.append(d.id)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Permintaan yang sama sedang diproses. Ulangi simpan.")
    # read ids BEFORE commit: after it every attribute is expired and would cost one query per row
    for r in touched + extra_new:
        if r.client_uid:
            id_map[r.client_uid] = r.id
    upserted_ids = [r.id for r in touched]
    new_ids = [r.id for r in touched + extra_new]
    extra_ids = {r.id for r in extra_new}
    db.commit()

    versions = {}
    extra_features = []
    if new_ids:
        for a in db.query(Annotation).filter(Annotation.id.in_(new_ids)).all():
            versions[a.id] = _utc_iso(a.updated_at)
        extra_features = [_feature_json(a, current_user.full_name) for a in db.query(Annotation).filter(Annotation.id.in_(extra_ids)).all()] if extra_ids else []

    duplicate_warnings: List[Dict[str, Any]] = []
    if touched or deleted:
        try:
            snap_rows = db.query(Annotation).filter(Annotation.task_grid_id == task_grid_id).all()
            try:
                duplicate_warnings = _near_duplicate_pairs(snap_rows, set(new_ids))
            except Exception as dup_err:
                logger.warning(f"Duplicate check failed for grid {task_grid_id}: {dup_err}")
            features = [{"type": "Feature", "id": a.id,
                         "properties": {"id": a.id, "class_id": a.class_id, "class_name": a.class_name, "area_sqm": round(a.area_sqm or 0, 2)},
                         "geometry": json.loads(a.geom_geojson)} for a in snap_rows]
            record_autosave_snapshot(db, task_grid_id, current_user.id,
                                     json.dumps({"type": "FeatureCollection", "features": features}), len(features))
        except Exception as e:
            logger.warning(f"Could not create version snapshot for grid {task_grid_id}: {e}")
            db.rollback()
        log_audit(db=db, user_id=current_user.id, action="SAVE_ANNOTATIONS", entity_type="task_grid",
                  entity_id=task_grid_id, task_grid_id=task_grid_id,
                  details=json.dumps({"mode": "delta", "upserts": len(touched), "deletes": len(deleted), "conflicts": len(conflicts)}))
        if duplicate_warnings:
            log_audit(db=db, user_id=current_user.id, action="DUPLICATE_SUSPECT", entity_type="task_grid",
                      entity_id=task_grid_id, task_grid_id=task_grid_id,
                      details=json.dumps({"mode": "delta", "pairs": duplicate_warnings,
                                          "upsert_ids": [u.id for u in req.upserts if u.id is not None][:50],
                                          "upsert_new": sum(1 for u in req.upserts if u.id is None),
                                          "deleted_ids": deleted[:50], "conflict_ids": [c["id"] for c in conflicts][:50]}))

    return {
        "id_map": id_map,
        "versions": {str(k): v for k, v in versions.items()},
        "upserted": upserted_ids,
        "deleted": deleted,
        "conflicts": conflicts,
        "rejected": rejected,
        "extra_features": extra_features,
        "duplicate_warnings": duplicate_warnings,
        "server_time": _utc_iso(datetime.utcnow()),
    }
