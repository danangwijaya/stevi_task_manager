from datetime import timedelta
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
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
    role: Optional[str] = "ANNOTATOR"

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
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
        "role": user.role
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
        username=signup_data.username,
        full_name=signup_data.full_name,
        email=signup_data.email,
        hashed_password=get_password_hash(signup_data.password),
        role="ANNOTATOR",
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
        "role": new_user.role
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
            role="ANNOTATOR",
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
        "role": user.role
    }

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    return current_user

@router.get("/users", response_model=List[UserResponse])
def read_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """List all users (students & instructors)"""
    return db.query(User).order_by(User.id.asc()).all()

@router.post("/users", response_model=UserResponse)
def create_user_by_admin(
    user_in: CreateUserRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin creates a new user account"""
    existing = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username atau email sudah digunakan")
    
    new_user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role or "ANNOTATOR",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

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
    
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.role is not None:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password:
        user.hashed_password = get_password_hash(user_in.password)
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
def delete_user_by_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_active_admin)
) -> Any:
    """Admin deletes a user account"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus akun admin sendiri yang sedang aktif")
    
    db.delete(user)
    db.commit()
    return {"message": f"User {user.username} berhasil dihapus"}
