"""
Pipeline orchestration router - Airflow integration entry points.

Exposes HTTP endpoints that Airflow DAGs call to trigger:
  - Bronze → Silver → Gold transformation (after batch ingestion)
  - Full GrainForecastPipeline (daily predictions)

All jobs are tracked via the same IngestionLog model so Airflow can poll
status at GET /pipeline/jobs/{job_id} or GET /ingestion/jobs/{job_id}.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.logger import logger
from app.models import IngestionLog

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Trigger endpoints (called by Airflow DAGs)
# ---------------------------------------------------------------------------

@router.post("/transformation", summary="Trigger Bronze→Silver→Gold transformation")
def trigger_transformation(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start a Bronze→Silver→Gold Spark transformation job.

    Airflow ingest_dag calls this after all parsers have finished ingesting
    to the bronze Delta Lake layer.

    Returns job_id which can be polled at GET /pipeline/jobs/{job_id}.
    """
    job_id = f"transform_{uuid.uuid4().hex[:12]}"
    log = IngestionLog(
        job_id=job_id,
        parser_name="transformation",
        status="started",
        layer="silver",
        started_at=_utcnow(),
    )
    db.add(log)
    db.commit()

    background_tasks.add_task(_run_transformation, job_id)
    logger.info("Transformation pipeline %s queued", job_id)
    return {"job_id": job_id, "status": "started", "started_at": log.started_at}


@router.post("/forecast", summary="Trigger end-to-end GrainForecastPipeline")
def trigger_forecast(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start the GrainForecastPipeline.

    This runs the complete end-to-end pipeline:
      1. Download market history from Yahoo Finance
      2. Bronze → Silver → Gold Delta Lake transformation via Spark
      3. Generate price predictions via linear/exponential smoothing model
      4. Persist predictions to PostgreSQL (read by the forecasts endpoint)

    Airflow daily_forecast_dag calls this once per day (06:00 UTC).
    Returns job_id which can be polled at GET /pipeline/jobs/{job_id}.
    """
    job_id = f"forecast_{uuid.uuid4().hex[:12]}"
    log = IngestionLog(
        job_id=job_id,
        parser_name="forecast",
        status="started",
        layer="gold",
        started_at=_utcnow(),
    )
    db.add(log)
    db.commit()

    background_tasks.add_task(_run_forecast, job_id)
    logger.info("Forecast pipeline %s queued", job_id)
    return {"job_id": job_id, "status": "started", "started_at": log.started_at}


# ---------------------------------------------------------------------------
# Status endpoint (polled by Airflow sensors)
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}", summary="Poll pipeline job status")
def get_pipeline_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Return status of a pipeline or ingestion job.

    Shared with /ingestion/jobs/{job_id} — both use IngestionLog.
    Terminal statuses: completed | failed
    Non-terminal statuses: started | running
    """
    log = db.query(IngestionLog).filter(IngestionLog.job_id == job_id).first()
    if not log:
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")

    return {
        "job_id": log.job_id,
        "parser_name": log.parser_name,
        "status": log.status,
        "layer": log.layer,
        "records_written": log.records_written,
        "started_at": log.started_at,
        "completed_at": log.completed_at,
        "error_message": log.error_message,
    }


# ---------------------------------------------------------------------------
# Background task implementations
# ---------------------------------------------------------------------------

def _run_transformation(job_id: str) -> None:
    """
    Background task: run Bronze → Silver → Gold transformation.

    Opens its own DB session (thread-safe, separate from request session).
    Iterates over known bronze tables and promotes each to silver,
    then creates gold aggregates for main grain commodities.

    Individual table failures are logged but do not abort the whole job —
    some parsers may not have run yet, so their bronze tables may be absent.
    """
    from app.spark_services.silver_layer import transform_to_silver
    from app.spark_services.gold_layer import create_gold_tables

    db = SessionLocal()
    log = None
    try:
        log = db.query(IngestionLog).filter(IngestionLog.job_id == job_id).first()
        log.status = "running"
        db.commit()

        total_written = 0

        # Bronze → Silver for each known source table
        bronze_to_silver_map = {
            "yfinance_bronze": "yfinance_silver",
            "apk_inform_bronze": "apk_inform_silver",
            "currency_bronze": "currency_silver",
            "tripoli_land_bronze": "tripoli_land_silver",
            "investing_com_bronze": "investing_com_silver",
            "graintradecomua_bronze": "graintradecomua_silver",
        }
        for bronze_name, silver_name in bronze_to_silver_map.items():
            try:
                result = transform_to_silver(bronze_name, silver_name)
                total_written += result.get("records_written", 0)
                logger.info("Silver transform %s → %s: %d records", bronze_name, silver_name, result.get("records_written", 0))
            except Exception as exc:
                # A missing/empty bronze table should not kill the whole job
                logger.warning("Silver transform skipped for %s: %s", bronze_name, exc)

        # Silver → Gold for primary grain commodities
        commodities = ["wheat", "corn", "soybeans", "oats", "rough rice"]
        for commodity in commodities:
            try:
                create_gold_tables("yfinance_silver", commodity)
                logger.info("Gold layer updated for %s", commodity)
            except Exception as exc:
                logger.warning("Gold layer skipped for %s: %s", commodity, exc)

        log.status = "completed"
        log.records_written = total_written
        log.completed_at = _utcnow()
        db.commit()
        logger.info("Transformation pipeline %s completed (%d records)", job_id, total_written)

    except Exception as exc:
        logger.error("Transformation pipeline %s failed: %s", job_id, exc)
        if log:
            log.status = "failed"
            log.error_message = str(exc)[:500]
            log.completed_at = _utcnow()
            db.commit()
    finally:
        db.close()


def _run_forecast(job_id: str) -> None:
    """
    Background task: run the full GrainForecastPipeline.

    Opens its own DB session (thread-safe, separate from request session).
    The GrainForecastPipeline internally handles:
      - Yahoo Finance market data download
      - Bronze → Silver → Gold Delta Lake via Spark
      - Prediction generation + persistence to PostgreSQL
    """
    from app.services.grain_forecast_pipeline import GrainForecastPipeline

    db = SessionLocal()
    log = None
    try:
        log = db.query(IngestionLog).filter(IngestionLog.job_id == job_id).first()
        log.status = "running"
        db.commit()

        pipeline = GrainForecastPipeline()
        summary = pipeline.run()

        predictions_saved = summary.get("predictions_saved", 0) if isinstance(summary, dict) else 0
        log.status = "completed"
        log.records_written = predictions_saved
        log.completed_at = _utcnow()
        db.commit()
        logger.info("Forecast pipeline %s completed: %s", job_id, summary)

    except Exception as exc:
        logger.error("Forecast pipeline %s failed: %s", job_id, exc)
        if log:
            log.status = "failed"
            log.error_message = str(exc)[:500]
            log.completed_at = _utcnow()
            db.commit()
    finally:
        db.close()
