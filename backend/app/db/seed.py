import json
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine, Base
from app.db.models import User, StudyArea, TaskGrid, Annotation, LandCoverClass, UserRole, TaskStatus
from app.core.security import get_password_hash
from app.core.config import settings
from app.services.grid_generator import generate_spatial_grids

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_postgres_sequences(db: Session):
    """Synchronize primary key sequences with MAX(id) to avoid duplicate key violations."""
    if engine.dialect.name == "postgresql":
        logger.info("Synchronizing PostgreSQL ID sequences...")
        tables = [
            ("users", "users_id_seq"),
            ("study_areas", "study_areas_id_seq"),
            ("task_grids", "task_grids_id_seq"),
            ("annotations", "annotations_id_seq"),
            ("land_cover_classes", "land_cover_classes_id_seq")
        ]
        for table, seq in tables:
            try:
                db.execute(text(f"SELECT setval('{seq}', COALESCE((SELECT MAX(id) FROM {table}), 1), true);"))
            except Exception as e:
                logger.debug(f"Could not sync sequence {seq} for table {table}: {e}")
        db.commit()

def ensure_schema_migrations(db: Session):
    """Ensure newly added columns exist in postgres without breaking existing data."""
    if engine.dialect.name == "postgresql":
        logger.info("Ensuring users table schema migrations...")
        cols = [
            ("phone", "VARCHAR(50)"),
            ("institution", "VARCHAR(255)"),
            ("department", "VARCHAR(255)"),
            ("nim_nip", "VARCHAR(100)"),
            ("address", "TEXT"),
        ]
        for col_name, col_type in cols:
            try:
                db.execute(text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
            except Exception as e:
                logger.debug(f"Schema migration note for {col_name}: {e}")
        db.commit()

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 0. Ensure schema migrations
        ensure_schema_migrations(db)

        # 1. Seed Classes
        existing_classes = db.query(LandCoverClass).count()
        if existing_classes == 0:
            logger.info("Seeding 12 Land Cover Classes...")
            for c in settings.LAND_COVER_CLASSES:
                db.add(LandCoverClass(
                    class_id=c["id"],
                    name=c["name"],
                    color_hex=c["color"],
                    description=c["description"],
                    is_active=True
                ))
            db.commit()

        # 2. Seed Initial Admin Account
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            logger.info("Seeding Initial Administrator Account...")
            admin_user = User(
                username="admin",
                email="admin@geoai.ac.id",
                full_name="Lead Administrator / Reviewer",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()

        # 3. Study Areas & Task Grids (Only seed if database is empty)
        existing_grids_count = db.query(TaskGrid).count()
        if existing_grids_count == 0:
            logger.info("Database empty, initializing Study Area...")
            sa_sumbar = db.query(StudyArea).first()
            if not sa_sumbar:
                sa_sumbar = StudyArea(
                    name="Provinsi Sumatera Barat (Seluruh Wilayah)",
                    description="Kawasan pemetaan data latih tutupan lahan se-Sumatera Barat (19 Kab/Kota, Pesisir, Pegunungan Bukit Barisan, dan Mentawai).",
                    center_lat=-0.750,
                    center_lon=100.500,
                    default_zoom=8
                )
                db.add(sa_sumbar)
                db.commit()
                db.refresh(sa_sumbar)
            logger.info("Database initialized.")
        else:
            logger.info(f"Database contains {existing_grids_count} task grids. Retaining user data without resetting.")

        # 4. Synchronize all PostgreSQL sequences to MAX(id)
        sync_postgres_sequences(db)
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
