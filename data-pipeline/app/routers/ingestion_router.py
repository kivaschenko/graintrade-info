"""
Simplified Ingestion Router

Much simpler than the enhanced version:
- No config validation layer
- No factory pattern
- Direct parser names
- Clear error messages
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.database import get_db
from app.models import IngestionLog
from app.services.ingestion_service import run_ingestion, get_available_parsers
from app.logger import logger
from app.config import settings


router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/start/{parser_name}")
def start_ingestion(
    parser_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start an ingestion job for a specific parser.
    
    Supported parsers:
    - apk_inform
    - investing_com
    - yfinance
    - tripoli_land
    - currency
    - graintradecomua
    
    Example: POST /ingestion/start/yfinance
    """
    # Validate parser name
    available = get_available_parsers()
    if parser_name not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown parser: {parser_name}. Available: {', '.join(available.keys())}",
        )
    
    # Create job ID
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    # Create job log
    log = IngestionLog(
        job_id=job_id,
        parser_name=parser_name,
        status="started",
        layer="bronze",
        started_at=datetime.now(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    logger.info(f"Created ingestion job {job_id} for parser {parser_name}")
    
    # Start background task
    background_tasks.add_task(
        run_ingestion,
        parser_name=parser_name,
        job_id=job_id,
        db=db,
        layer="bronze",
    )
    
    return {
        "job_id": job_id,
        "parser_name": parser_name,
        "status": "started",
        "created_at": log.created_at,
    }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get status of an ingestion job."""
    log = db.query(IngestionLog).filter(IngestionLog.job_id == job_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": log.job_id,
        "parser_name": log.parser_name,
        "status": log.status,
        "records_read": log.records_read,
        "records_written": log.records_written,
        "error_message": log.error_message,
        "started_at": log.started_at,
        "completed_at": log.completed_at,
    }


@router.get("/parsers")
def list_available_parsers():
    """Get list of available parsers and their configuration."""
    return get_available_parsers()


@router.get("/jobs")
def list_jobs(
    parser_name: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    List ingestion jobs with optional filtering.
    
    Query parameters:
    - parser_name: Filter by parser name
    - status: Filter by status (started, running, completed, failed)
    - skip: Skip first N results
    - limit: Return maximum N results
    """
    query = db.query(IngestionLog)
    
    if parser_name:
        query = query.filter(IngestionLog.parser_name == parser_name)
    
    if status:
        query = query.filter(IngestionLog.status == status)
    
    jobs = query.order_by(IngestionLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "job_id": job.job_id,
            "parser_name": job.parser_name,
            "status": job.status,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
        }
        for job in jobs
    ]
