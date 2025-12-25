# src/data_pipeline/routers/ingestion_router.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.database import get_db
from ..models import IngestionLog, DataSource
from ..schemas import IngestionJobRequest, IngestionLogResponse
from ..spark_services import ingest_to_bronze, transform_to_silver, create_gold_tables
from app.logger import logger

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def run_ingestion_job(
    job_id: str,
    data_source_id: int,
    layer: str,
    db_url: str
):
    """
    Background task to run ingestion job
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Create new database session for background task
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Get data source
        data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
        if not data_source:
            logger.error(f"Data source {data_source_id} not found")
            return
        
        # Get or create ingestion log
        log = db.query(IngestionLog).filter(IngestionLog.job_id == job_id).first()
        if not log:
            log = IngestionLog(
                data_source_id=data_source_id,
                job_id=job_id,
                status="running",
                layer=layer,
                started_at=datetime.now()
            )
            db.add(log)
            db.commit()
        
        log.status = "running"
        db.commit()
        
        result = {}
        
        # Execute ingestion based on layer
        if layer == "bronze":
            result = ingest_to_bronze(
                source_path=data_source.file_path or data_source.url,
                source_format=data_source.source_type,
                source_name=data_source.name,
                table_name=f"{data_source.name}_raw"
            )
        elif layer == "silver":
            result = transform_to_silver(
                bronze_table_name=f"{data_source.name}_raw",
                silver_table_name=f"{data_source.name}_clean"
            )
        elif layer == "gold":
            # Assume commodity name is in config
            commodity_name = data_source.config.get("commodity_name", "wheat")
            result = create_gold_tables(
                silver_table_name=f"{data_source.name}_clean",
                commodity_name=commodity_name
            )
        
        # Update log with results
        log.status = result.get("status", "completed")
        log.records_read = result.get("records_read", 0)
        log.records_written = result.get("records_written", 0)
        log.records_failed = result.get("records_removed", 0)
        log.output_path = result.get("output_path")
        log.completed_at = datetime.now()
        
        if result.get("status") == "failed":
            log.error_message = result.get("error")
        
        # Update data source last ingestion time
        data_source.last_ingestion = datetime.now()
        
        db.commit()
        
        logger.info(f"Ingestion job {job_id} completed: {result}")
        
    except Exception as e:
        logger.error(f"Ingestion job {job_id} failed: {str(e)}")
        log.status = "failed"
        log.error_message = str(e)
        log.completed_at = datetime.now()
        db.commit()
    
    finally:
        db.close()


@router.post("/start", response_model=IngestionLogResponse, status_code=202)
def start_ingestion(
    request: IngestionJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start an ingestion job (async)
    """
    # Validate data source exists
    data_source = db.query(DataSource).filter(DataSource.id == request.data_source_id).first()
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    if not data_source.is_active:
        raise HTTPException(status_code=400, detail="Data source is not active")
    
    # Validate layer
    if request.layer not in ["bronze", "silver", "gold"]:
        raise HTTPException(status_code=400, detail="Invalid layer. Must be: bronze, silver, or gold")
    
    # Create job ID
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    
    # Create ingestion log
    log = IngestionLog(
        data_source_id=request.data_source_id,
        job_id=job_id,
        status="started",
        layer=request.layer,
        started_at=datetime.now()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    # Start background task
    from app.config import settings
    background_tasks.add_task(
        run_ingestion_job,
        job_id=job_id,
        data_source_id=request.data_source_id,
        layer=request.layer,
        db_url=settings.DATABASE_URL
    )
    
    logger.info(f"Started ingestion job: {job_id}")
    
    return log


@router.get("/jobs", response_model=List[IngestionLogResponse])
def list_ingestion_jobs(
    limit: int = 100,
    offset: int = 0,
    status: str = None,
    db: Session = Depends(get_db)
):
    """List ingestion jobs"""
    query = db.query(IngestionLog)
    
    if status:
        query = query.filter(IngestionLog.status == status)
    
    logs = query.order_by(IngestionLog.started_at.desc()).offset(offset).limit(limit).all()
    return logs


@router.get("/jobs/{job_id}", response_model=IngestionLogResponse)
def get_ingestion_job(job_id: str, db: Session = Depends(get_db)):
    """Get ingestion job status"""
    log = db.query(IngestionLog).filter(IngestionLog.job_id == job_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Job not found")
    return log
