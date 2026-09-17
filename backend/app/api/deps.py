from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if (current_user.role or "").strip().lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (Admin required)"
        )
    return current_user

def get_current_active_reviewer(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allows Admin, Supervisi, or Dosen (Reviewer/QC access)"""
    role = (current_user.role or "").strip().lower()
    if role not in ["admin", "dosen", "supervisi"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hak akses tidak mencukupi (diperlukan akses Admin atau Supervisi)"
        )
    return current_user
