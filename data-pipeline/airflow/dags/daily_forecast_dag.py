"""
Daily Forecast DAG — runs once per day at 06:00 UTC.

Flow
----
1. check_data_freshness  — verify recent ingestion logs exist (sensor-like)
2. run_forecast_pipeline — trigger GrainForecastPipeline via HTTP and poll
3. verify_predictions    — lightweight check that predictions were persisted

The GrainForecastPipeline (POST /pipeline/forecast) internally:
  • Downloads 2-year market history from Yahoo Finance
  • Runs Bronze → Silver → Gold Delta Lake transformation via PySpark
  • Generates 7-day price predictions using exponential smoothing / linear trend
  • Persists predictions to PostgreSQL (consumed by GET /forecasts/)

Schedule: 06:00 UTC daily — after overnight ingest_dag runs
(ingest_dag runs at 00:00, 06:00, 12:00, 18:00 UTC so at 06:00 there
is already a fresh ingest run from 06:00 or the midnight run).
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta

import requests
from airflow.decorators import dag, task

# ── Configuration ─────────────────────────────────────────────────────────────
PIPELINE_URL = os.environ.get("DATA_PIPELINE_URL", "http://data-pipeline:8004")

FORECAST_POLL_TIMEOUT_S = 45 * 60   # 45 minutes (Spark + prediction model)
FORECAST_POLL_INTERVAL_S = 20        # check every 20 seconds

# Minimum accepted predictions count — alert if fewer are returned
MIN_PREDICTIONS_EXPECTED = 5

DEFAULT_ARGS = {
    "owner": "data-pipeline",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
    "email_on_retry": False,
}


# ── Helper ────────────────────────────────────────────────────────────────────

def _poll_until_done(status_url: str, timeout_s: int, interval_s: int) -> dict:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        resp = requests.get(status_url, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        status = payload.get("status", "unknown")
        if status == "completed":
            return payload
        if status == "failed":
            error = payload.get("error_message") or payload.get("error", "no detail")
            raise RuntimeError(f"Pipeline job failed: {error!r}")
        time.sleep(interval_s)
    raise TimeoutError(f"Forecast pipeline did not finish within {timeout_s}s")


# ── DAG definition ────────────────────────────────────────────────────────────

@dag(
    dag_id="daily_forecast_dag",
    description="Daily end-to-end GrainForecastPipeline: ingest → transform → predict",
    schedule="0 6 * * *",       # 06:00 UTC every day
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,           # forecast is heavy; never run two in parallel
    tags=["forecast", "data-pipeline", "gold", "daily"],
    default_args=DEFAULT_ARGS,
)
def daily_forecast_dag() -> None:

    @task(task_id="check_data_freshness")
    def check_data_freshness() -> dict:
        """
        Lightweight check: verify the data-pipeline service is healthy and the
        forecasts endpoint responds before committing a long Spark+ML run.

        Does NOT block on ingestion data — the forecast pipeline fetches its
        own market data from Yahoo Finance internally.
        """
        health_url = f"{PIPELINE_URL}/health"
        resp = requests.get(health_url, timeout=10)
        resp.raise_for_status()
        health = resp.json()

        status = health.get("status", "unknown")
        if status not in ("healthy", "ok", "running"):
            raise RuntimeError(f"Data-pipeline health check failed: {health}")

        return {"health": health, "checked_at": datetime.utcnow().isoformat()}

    @task(task_id="run_forecast_pipeline")
    def run_forecast_pipeline(health_result: dict) -> dict:
        """
        Trigger the GrainForecastPipeline and block until it finishes.

        Returns the job summary including predictions_saved count.
        """
        resp = requests.post(f"{PIPELINE_URL}/pipeline/forecast", timeout=15)
        resp.raise_for_status()
        job = resp.json()
        job_id = job["job_id"]

        status_url = f"{PIPELINE_URL}/pipeline/jobs/{job_id}"
        result = _poll_until_done(
            status_url, FORECAST_POLL_TIMEOUT_S, FORECAST_POLL_INTERVAL_S
        )

        import logging
        logging.getLogger(__name__).info(
            "Forecast pipeline %s finished: records_written=%s",
            job_id,
            result.get("records_written"),
        )
        return {"job_id": job_id, **result}

    @task(task_id="verify_predictions")
    def verify_predictions(forecast_result: dict) -> dict:
        """
        Confirm that predictions are readable from the forecasts endpoint.

        A low prediction count is logged as a warning, not a failure, to
        avoid daily DAG alerts during data-sparse periods (e.g. weekends).
        """
        import logging
        log = logging.getLogger(__name__)

        resp = requests.get(
            f"{PIPELINE_URL}/forecasts/",
            params={"days_ahead": 7, "limit": 50},
            timeout=15,
        )
        resp.raise_for_status()
        predictions = resp.json()
        count = len(predictions)

        if count < MIN_PREDICTIONS_EXPECTED:
            log.warning(
                "Only %d predictions found after forecast run (expected >= %d). "
                "Check parsers and logs.",
                count,
                MIN_PREDICTIONS_EXPECTED,
            )
        else:
            log.info("Forecast verification passed: %d predictions available", count)

        return {
            "predictions_available": count,
            "job_id": forecast_result.get("job_id"),
            "verified_at": datetime.utcnow().isoformat(),
        }

    # Wire up linear pipeline: health → forecast → verify
    health = check_data_freshness()
    forecast = run_forecast_pipeline(health)
    verify_predictions(forecast)


daily_forecast_dag()
