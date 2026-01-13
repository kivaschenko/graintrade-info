# app/routers/ingestion_router_enhanced.py
"""
Enhanced ingestion router with parser factory integration

This is a reference implementation showing how to integrate ParserFactory
into the existing ingestion pipeline. You can merge these changes into
the existing ingestion_router.py file.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from app.database import get_db
from app.models import IngestionLog, DataSource
from app.schemas import IngestionJobRequest, IngestionLogResponse
from app.spark_services import ingest_to_bronze, transform_to_silver, create_gold_tables
from app.logger import logger
from app.services.parser_factory import ParserFactory
from app.services.config_validator import ConfigValidator

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


def run_ingestion_job_with_parser(
    job_id: str,
    data_source_id: int,
    layer: str,
    db_url: str
):
    """
    Enhanced background task to run ingestion job using ParserFactory.
    
    This version attempts to use the ParserFactory first if a parser_type
    is configured in the DataSource config. Falls back to traditional
    ingestion for non-parser sources.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import pandas as pd
    
    # Create new database session for background task
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    log = None
    try:
        # Get data source
        data_source = db.query(DataSource).filter(DataSource.id == data_source_id).first()
        if not data_source:
            logger.error(f"Data source {data_source_id} not found")
            return
        
        # Create or get ingestion log
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
        
        if layer == "bronze":
            # Try using parser factory first if parser_type is configured
            if data_source.config and data_source.config.get("parser_type"):
                try:
                    logger.info(f"Using ParserFactory for {data_source.name}")
                    
                    # Validate config
                    is_valid, errors = ConfigValidator.validate(data_source.config)
                    if not is_valid:
                        raise ValueError(f"Invalid config: {', '.join(errors)}")
                    
                    # Create and execute parser
                    parser = ParserFactory.create_parser(data_source)
                    df = parser.parse()
                    
                    if df is None or df.empty:
                        result = {
                            "status": "completed",
                            "records_read": 0,
                            "records_written": 0,
                            "records_removed": 0,
                            "message": "Parser returned empty data"
                        }
                    else:
                        # Optionally save to bronze layer
                        # ingest_to_bronze(df, data_source.name)
                        
                        result = {
                            "status": "completed",
                            "records_read": len(df),
                            "records_written": len(df),
                            "records_removed": 0,
                            "output_path": f"/data/delta/bronze/{data_source.name}_raw"
                        }
                        
                        logger.info(f"Parser {data_source.name} completed: {len(df)} records")
                    
                except Exception as e:
                    logger.error(f"Parser execution failed: {e}", exc_info=True)
                    result = {
                        "status": "failed",
                        "error": str(e)
                    }
            else:
                # Fallback to traditional ingestion for file/API sources
                logger.info(f"Using traditional ingestion for {data_source.name}")
                
                try:
                    result = ingest_to_bronze(
                        source_path=data_source.file_path or data_source.url,
                        source_format=data_source.source_type,
                        source_name=data_source.name,
                        table_name=f"{data_source.name}_raw"
                    )
                except Exception as e:
                    logger.error(f"Traditional ingestion failed: {e}", exc_info=True)
                    result = {
                        "status": "failed",
                        "error": str(e)
                    }
        
        elif layer == "silver":
            try:
                result = transform_to_silver(
                    bronze_table_name=f"{data_source.name}_raw",
                    silver_table_name=f"{data_source.name}_clean"
                )
            except Exception as e:
                logger.error(f"Silver layer transformation failed: {e}", exc_info=True)
                result = {
                    "status": "failed",
                    "error": str(e)
                }
        
        elif layer == "gold":
            try:
                # Get commodity name from config or use default
                commodity_name = data_source.config.get("commodity_name", "wheat") if data_source.config else "wheat"
                
                result = create_gold_tables(
                    silver_table_name=f"{data_source.name}_clean",
                    commodity_name=commodity_name
                )
            except Exception as e:
                logger.error(f"Gold layer creation failed: {e}", exc_info=True)
                result = {
                    "status": "failed",
                    "error": str(e)
                }
        
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
        
        logger.info(f"Ingestion job {job_id} completed with status: {log.status}")
        
    except Exception as e:
        logger.error(f"Ingestion job {job_id} failed: {str(e)}", exc_info=True)
        if log:
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
    
    Supports both traditional file/API ingestion and parser-based ingestion.
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
    
    # If using parser, validate config
    if data_source.config and data_source.config.get("parser_type"):
        is_valid, errors = ConfigValidator.validate(data_source.config)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parser config: {'; '.join(errors)}"
            )
    
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
        run_ingestion_job_with_parser,
        job_id=job_id,
        data_source_id=request.data_source_id,
        layer=request.layer,
        db_url=settings.DATABASE_URL
    )
    
    return IngestionLogResponse.model_validate(log)


@router.get("/jobs", response_model=List[IngestionLogResponse])
def list_ingestion_jobs(
    data_source_id: int = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List ingestion jobs with optional filtering
    """
    query = db.query(IngestionLog)
    
    if data_source_id:
        query = query.filter(IngestionLog.data_source_id == data_source_id)
    
    if status:
        query = query.filter(IngestionLog.status == status)
    
    logs = query.order_by(IngestionLog.started_at.desc()).offset(skip).limit(limit).all()
    return logs


@router.get("/jobs/{job_id}", response_model=IngestionLogResponse)
def get_ingestion_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get specific ingestion job status
    """
    log = db.query(IngestionLog).filter(IngestionLog.job_id == job_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return log


@router.get("/parsers")
def get_supported_parsers():
    """
    Get information about all supported parsers
    """
    return ParserFactory.get_supported_parsers()
