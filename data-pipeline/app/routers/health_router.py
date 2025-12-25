# src/data_pipeline/routers/health_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db, check_connection
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "data-pipeline",
        "timestamp": datetime.now().isoformat(),
        "environment": settings.ENV
    }


@router.get("/database")
def database_health(db: Session = Depends(get_db)):
    """Check database connectivity"""
    try:
        # Try to execute a simple query
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/spark")
def spark_health():
    """Check Spark connectivity"""
    try:
        from ..spark_services import get_spark_session
        spark = get_spark_session()
        version = spark.version
        return {
            "status": "healthy",
            "spark": "connected",
            "version": version,
            "master": settings.SPARK_MASTER,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "spark": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
