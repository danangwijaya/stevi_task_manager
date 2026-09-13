from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.session import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOSEN = "dosen"
    ANNOTATOR = "annotator"

class TaskStatus(str, enum.Enum):
    UNASSIGNED = "UNASSIGNED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REVISION_NEEDED = "REVISION_NEEDED"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.ANNOTATOR.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assigned_tasks = relationship("TaskGrid", back_populates="assignee", foreign_keys="TaskGrid.assigned_user_id")
    annotations = relationship("Annotation", back_populates="author")

class StudyArea(Base):
    __tablename__ = "study_areas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    default_zoom = Column(Integer, default=11)
    bounds_geojson = Column(Text, nullable=True) # GeoJSON boundary
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("TaskGrid", back_populates="study_area", cascade="all, delete-orphan")

class TaskGrid(Base):
    __tablename__ = "task_grids"
    
    id = Column(Integer, primary_key=True, index=True)
    grid_code = Column(String(50), unique=True, index=True, nullable=False)
    study_area_id = Column(Integer, ForeignKey("study_areas.id"), nullable=False)
    year = Column(Integer, default=2026, nullable=False)
    
    # Bounding Box in WGS84
    min_lon = Column(Float, nullable=False)
    min_lat = Column(Float, nullable=False)
    max_lon = Column(Float, nullable=False)
    max_lat = Column(Float, nullable=False)
    geom_geojson = Column(Text, nullable=False) # Polygon GeoJSON
    
    # Raster COG Integration (Dynamic multi-year support)
    tile_key = Column(String(100), index=True, nullable=True) # e.g. "0000000000-0000008192"
    raster_file_2022 = Column(String(255), nullable=True)
    raster_file_2025 = Column(String(255), nullable=True)
    
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(30), default=TaskStatus.UNASSIGNED.value, nullable=False)
    reviewer_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    study_area = relationship("StudyArea", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assigned_user_id])
    annotations = relationship("Annotation", back_populates="task_grid", cascade="all, delete-orphan")

class Annotation(Base):
    __tablename__ = "annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    task_grid_id = Column(Integer, ForeignKey("task_grids.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, nullable=False) # 1 to 12
    class_name = Column(String(100), nullable=False)
    geom_geojson = Column(Text, nullable=False) # GeoJSON Feature geometry
    area_sqm = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task_grid = relationship("TaskGrid", back_populates="annotations")
    author = relationship("User", back_populates="annotations")

class LandCoverClass(Base):
    __tablename__ = "land_cover_classes"
    
    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    color_hex = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

class ExportJob(Base):
    __tablename__ = "export_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(30), default="PENDING")
    year = Column(Integer, nullable=False)
    total_patches = Column(Integer, default=0)
    zip_file_path = Column(String(255), nullable=True)
    log_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
