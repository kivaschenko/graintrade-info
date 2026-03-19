# src/data_pipeline/database.py
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.ENV == "development"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, info={"app_name": "data_pipeline"})

# Metadata for reflection and migrations
metadata = MetaData()

# Base class for ORM models
Base = declarative_base(metadata=metadata)


def get_db():
    """
    Dependency for FastAPI to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    """
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")


def check_connection():
    """
    Check database connection
    """
    try:
        with engine.connect() as conn:
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
