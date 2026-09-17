from datetime import timedelta, datetime
import secrets
import string
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import User, TaskGrid, Annotation, TaskStatus
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.api.deps import get_current_user, get_current_active_admin

router = APIRouter()

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    full_name: str
    role: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    assigned_tasks_count: Optional[int] = 0
    annotations_count: Optional[int] = 0
    # Optional Administrative Fields
    phone: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    nim_nip: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class SignUpRequest(BaseModel):
    username: str
    full_name: str
    email: str
    password: str

class OAuthRequest(BaseModel):
    provider: str # 'google' | 'github'
    email: Optional[str] = None
    full_name: Optional[str] = None
    username: Optional[str] = None

class CreateUserRequest(BaseModel):
    username: str
    full_name: str
    email: str
    password: str
    role: Optional[str] = "annotator"
    phone: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    nim_nip: Optional[str] = None
    address: Optional[str] = None

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    nim_nip: Optional[str] = None
    address: Optional[str] = None

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    nim_nip: Optional[str] = None
    address: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    password: Optional[str] = None

@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    user = db.query(User).filter(
        (User.username == login_data.username) | (User.email == login_data.username)
    ).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username atau password salah"
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Akun tidak aktif")
        
    access_token = create_access_token(user.username)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": (user.role or "annotator").lower()
    }

@router.post("/signup", response_model=Token)
def signup(
    signup_data: SignUpRequest,
    db: Session = Depends(get_db)
) -> Any:
    """Register new student / annotator account"""
    existing_user = db.query(User).filter(
        (User.username == signup_data.username) | (User.email == signup_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username atau email sudah terdaftar"
        )
    
    new_user = User(
        username=signup_data.username.strip(),
        full_name=signup_data.full_name.strip(),
        email=signup_data.email.strip(),
        hashed_password=get_password_hash(signup_data.password),
        role="annotator",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(new_user.username)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "username": new_user.username,
        "full_name": new_user.full_name,
        "role": "annotator"
    }

@router.post("/oauth", response_model=Token)
def oauth_login(
    oauth_data: OAuthRequest,
    db: Session = Depends(get_db)
) -> Any:
    """OAuth login/signup via Google or GitHub"""
    provider_prefix = "google" if oauth_data.provider.lower() == "google" else "github"
    email = oauth_data.email or f"{provider_prefix}_user@geoai.id"
    username = oauth_data.username or f"{provider_prefix}_{email.split('@')[0]}"
    full_name = oauth_data.full_name or f"{provider_prefix.title()} User"

    user = db.query(User).filter((User.email == email) | (User.username == username)).first()
    if not user:
        user = User(
            username=username,
            full_name=full_name,
            email=email,
            hashed_password=get_password_hash(f"oauth_{provider_prefix}_2026"),
            role="annotator",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(user.username)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": (user.role or "annotator").lower()
    }

@router.get("/me", response_model=UserResponse)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    tasks_count = db.query(TaskGrid).filter(TaskGrid.assigned_user_id == current_user.id).count()
    annotations_count = db.query(Annotation).filter(Annotation.user_id == current_user.id).count()
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": (current_user.role or "annotator").lower(),
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "assigned_tasks_count": tasks_count,
        "annotations_count": annotations_count,
        "phone": current_user.phone,
        "institution": current_user.institution,
        "department": current_user.department,
        "nim_nip": current_user.nim_nip,
        "address": current_user.address
    }

@router.put("/me", response_model=UserResponse)
def update_user_me(
    profile_in: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Current logged-in user updates their own profile details"""
    if profile_in.email is not None and profile_in.email.strip() != current_user.email:
        existing_email = db.query(User).filter(User.email == profile_in.email.strip(), User.id != current_user.id).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email sudah digunakan oleh akun lain")
        current_user.email = profile_in.email.strip()

    if profile_in.full_name is not None and profile_in.full_name.strip():
        current_user.full_name = profile_in.full_name.strip()

    if profile_in.phone is not None:
        current_user.phone = profile_in.phone.strip() if profile_in.phone.strip() else None

    if profile_in.institution is not None:
        current_user.institution = profile_in.institution.strip() if profile_in.institution.strip() else None

    if profile_in.department is not None:
        current_user.department = profile_in.department.strip() if profile_in.department.strip() else None

    if profile_in.nim_nip is not None:
        current_user.nim_nip = profile_in.nim_nip.strip() if profile_in.nim_nip.strip() else None

    if profile_in.address is not None:
        current_user.address = profile_in.address.strip() if profile_in.address.strip() else None

    if profile_in.password and profile_in.password.strip():
        current_user.hashed_password = get_password_hash(profile_in.password.strip())

    db.commit()
    db.refresh(current_user)

    tasks_count = db.query(TaskGrid).filter(TaskGrid.assigned_user_id == current_user.id).count()
    annotations_count = db.query(Annotation).filter(Annotation.user_id == current_user.id).count()
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": (current_user.role or "annotator").lower(),
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "assigned_tasks_count": tasks_count,
        "annotations_count": annotations_count,
        "phone": current_user.phone,
        "institution": current_user.institution,
        "department": current_user.department,
        "nim_nip": current_user.nim_nip,
        "address": current_user.address
    }

@router.get("/users", response_model=List[UserResponse])
def read_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all users (students & instructors) with task & annotation counts"""
    users = db.query(User).order_by(User.id.asc()).all()
    
    task_counts = dict(
        db.query(TaskGrid.assigned_user_id, func.count(TaskGrid.id))
        .filter(TaskGrid.assigned_user_id.isnot(None))
        .group_by(TaskGrid.assigned_user_id)
        .all()
    )
    annotation_counts = dict(
        db.query(Annotation.user_id, func.count(Annotation.id))
        .group_by(Annotation.user_id)
        .all()
    )
    
    results = []
    for u in users:
        results.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": (u.role or "annotator").lower(),
            "is_active": u.is_active,
            "created_at": u.created_at,
            "assigned_tasks_count": task_counts.get(u.id, 0),
            "annotations_count": annotation_counts.get(u.id, 0),
            "phone": u.phone,
            "institution": u.institution,
            "department": u.department,
            "nim_nip": u.nim_nip,
            "address": u.address
        })
    return results

@router.post("/users", response_model=UserResponse)
def create_user_by_admin(
    user_in: CreateUserRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin creates a new user account"""
    existing = db.query(User).filter(
        (User.username == user_in.username.strip()) | (User.email == user_in.email.strip())
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username atau email sudah digunakan")
    
    clean_role = (user_in.role or "annotator").strip().lower()
    if clean_role == "supervisi":
        clean_role = "dosen"
    elif clean_role not in ["admin", "dosen", "annotator"]:
        clean_role = "annotator"

    new_user = User(
        username=user_in.username.strip(),
        full_name=user_in.full_name.strip(),
        email=user_in.email.strip(),
        hashed_password=get_password_hash(user_in.password),
        role=clean_role,
        is_active=True,
        phone=user_in.phone.strip() if (user_in.phone and user_in.phone.strip()) else None,
        institution=user_in.institution.strip() if (user_in.institution and user_in.institution.strip()) else None,
        department=user_in.department.strip() if (user_in.department and user_in.department.strip()) else None,
        nim_nip=user_in.nim_nip.strip() if (user_in.nim_nip and user_in.nim_nip.strip()) else None,
        address=user_in.address.strip() if (user_in.address and user_in.address.strip()) else None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at,
        "assigned_tasks_count": 0,
        "annotations_count": 0,
        "phone": new_user.phone,
        "institution": new_user.institution,
        "department": new_user.department,
        "nim_nip": new_user.nim_nip,
        "address": new_user.address
    }

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_by_admin(
    user_id: int,
    user_in: UpdateUserRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin updates user profile, role, status or resets password"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    # Check duplicate email if changed
    if user_in.email is not None and user_in.email.strip() != user.email:
        existing_email = db.query(User).filter(User.email == user_in.email.strip(), User.id != user_id).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email sudah digunakan oleh akun lain")
        user.email = user_in.email.strip()

    if user_in.full_name is not None:
        user.full_name = user_in.full_name.strip()

    if user_in.phone is not None:
        user.phone = user_in.phone.strip() if user_in.phone.strip() else None

    if user_in.institution is not None:
        user.institution = user_in.institution.strip() if user_in.institution.strip() else None

    if user_in.department is not None:
        user.department = user_in.department.strip() if user_in.department.strip() else None

    if user_in.nim_nip is not None:
        user.nim_nip = user_in.nim_nip.strip() if user_in.nim_nip.strip() else None

    if user_in.address is not None:
        user.address = user_in.address.strip() if user_in.address.strip() else None

    if user_in.role is not None:
        clean_role = user_in.role.strip().lower()
        if clean_role == "supervisi":
            clean_role = "dosen"
        if clean_role in ["admin", "dosen", "annotator"]:
            # Prevent demoting the last admin
            if (user.role or "").lower() == "admin" and clean_role != "admin":
                active_admins = db.query(User).filter(func.lower(User.role) == "admin", User.is_active == True).count()
                if active_admins <= 1:
                    raise HTTPException(status_code=400, detail="Tidak dapat mengubah role admin terakhir di sistem")
            user.role = clean_role

    if user_in.is_active is not None:
        if (user.role or "").lower() == "admin" and not user_in.is_active:
            active_admins = db.query(User).filter(func.lower(User.role) == "admin", User.is_active == True).count()
            if active_admins <= 1:
                raise HTTPException(status_code=400, detail="Tidak dapat menonaktifkan admin terakhir di sistem")
        user.is_active = user_in.is_active

    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
    
    db.commit()
    db.refresh(user)

    tasks_count = db.query(TaskGrid).filter(TaskGrid.assigned_user_id == user.id).count()
    annotations_count = db.query(Annotation).filter(Annotation.user_id == user.id).count()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "role": (user.role or "annotator").lower(),
        "is_active": user.is_active,
        "created_at": user.created_at,
        "assigned_tasks_count": tasks_count,
        "annotations_count": annotations_count,
        "phone": user.phone,
        "institution": user.institution,
        "department": user.department,
        "nim_nip": user.nim_nip,
        "address": user.address
    }

@router.post("/users/{user_id}/reset-password")
def reset_password_by_admin(
    user_id: int,
    req: Optional[ResetPasswordRequest] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin resets user password with custom or auto-generated strong password"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    
    new_password = req.password.strip() if (req and req.password and req.password.strip()) else None
    if not new_password:
        chars = string.ascii_letters + string.digits
        random_part = ''.join(secrets.choice(chars) for _ in range(8))
        new_password = f"GeoAI-{random_part}"
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {
        "message": f"Password untuk user {user.username} berhasil di-reset",
        "new_password": new_password,
        "user_id": user.id,
        "username": user.username
    }

@router.delete("/users/{user_id}")
def delete_user_by_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin deletes or deactivates a user account with smart safety checks"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus akun admin sendiri yang sedang aktif")
    
    # Prevent deleting the last active admin
    if (user.role or "").lower() == "admin":
        active_admins = db.query(User).filter(func.lower(User.role) == "admin", User.is_active == True).count()
        if active_admins <= 1:
            raise HTTPException(status_code=400, detail="Tidak dapat menghapus admin terakhir yang aktif di sistem")

    # Check annotations
    annotations_count = db.query(Annotation).filter(Annotation.user_id == user.id).count()
    if annotations_count > 0:
        # User has digitized polygons! Deactivate (soft delete) to protect training dataset
        user.is_active = False
        db.commit()
        return {
            "message": f"Akun {user.username} dinonaktifkan (memiliki {annotations_count} poligon anotasi data latih agar dataset tetap utuh).",
            "action": "deactivated",
            "annotations_count": annotations_count
        }
    
    # If user has assigned tasks without annotations, release/unassign them cleanly
    assigned_tasks = db.query(TaskGrid).filter(TaskGrid.assigned_user_id == user.id).all()
    for task in assigned_tasks:
        task.assigned_user_id = None
        if task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
            task.status = TaskStatus.UNASSIGNED
    
    db.delete(user)
    db.commit()
    return {
        "message": f"User {user.username} berhasil dihapus permanen",
        "action": "deleted"
    }
