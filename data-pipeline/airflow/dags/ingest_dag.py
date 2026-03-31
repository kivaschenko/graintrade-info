"""
Ingestion DAG — runs every 6 hours.

Flow
----
1. Fan-out: ingest each parser in parallel (bronze Delta Lake layer).
   Parsers: yfinance, apk_inform, investing_com, currency,
            tripoli_land, graintradecomua
2. Each task polls /ingestion/jobs/{job_id} until terminal status.
3. Fan-in (TriggerRule.ALL_DONE): transformation task is always
   attempted regardless of how many parsers failed, so fresh data
   is promoted to silver/gold even on partial ingestion runs.
4. Transformation task polls /pipeline/jobs/{job_id} until complete.

HTTP targets → data-pipeline FastAPI service:
  POST /ingestion/start/{parser_name}
  GET  /ingestion/jobs/{job_id}
  POST /pipeline/transformation
  GET  /pipeline/jobs/{job_id}
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta

import requests
from airflow.decorators import dag, task
from airflow.utils.trigger_rule import TriggerRule

# ── Configuration ────────────────────────────────────────────────────────────
# DATA_PIPELINE_URL is set via docker-compose environment variable so the
# same DAG file works in every environment without modification.
PIPELINE_URL = os.environ.get("DATA_PIPELINE_URL", "http://data-pipeline:8004")

# Maximum time to wait for a single parser job to reach a terminal status.
INGEST_POLL_TIMEOUT_S = 10 * 60  # 10 minutes
INGEST_POLL_INTERVAL_S = 10       # check every 10 seconds

# Maximum time to wait for the transformation job.
TRANSFORM_POLL_TIMEOUT_S = 30 * 60  # 30 minutes (Spark can take a while)
TRANSFORM_POLL_INTERVAL_S = 15

# Parsers registered in the data-pipeline (must match ENABLED_PARSERS env)
ALL_PARSERS = [
    "yfinance",
    "apk_inform",
    "investing_com",
    "currency",
    "tripoli_land",
    "graintradecomua",
]

DEFAULT_ARGS = {
    "owner": "data-pipeline",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}


# ── Helper ────────────────────────────────────────────────────────────────────

def _poll_until_done(
    status_url: str,
    timeout_s: int,
    interval_s: int,
) -> dict:
    """
    Poll `status_url` (GET) until the job reaches a terminal state.

    Returns the final status payload.
    Raises TimeoutError if the job doesn't finish within `timeout_s`.
    Raises RuntimeError if the job status is 'failed'.
    """
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
            raise RuntimeError(f"Job failed — {status_url} → {error!r}")

        time.sleep(interval_s)

    raise TimeoutError(f"Job did not finish within {timeout_s}s — {status_url}")


# ── DAG definition ────────────────────────────────────────────────────────────

@dag(
    dag_id="ingest_dag",
    description="Parallel data ingestion from all configured parsers + transformation",
    schedule="0 */6 * * *",   # every 6 hours
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,         # prevent overlap if a run is slow
    tags=["ingestion", "data-pipeline", "bronze"],
    default_args=DEFAULT_ARGS,
)
def ingest_dag() -> None:
    """
    Fan-out: one Airflow task per parser, all running in parallel.

    Dynamic task mapping (``task.expand``) creates one instance of
    ``ingest_parser`` per entry in ``ALL_PARSERS`` — each runs as a
    separate LocalExecutor subprocess.
    """

    @task(task_id="ingest_parser")
    def ingest_parser(parser_name: str) -> dict:
        """
        Trigger one parser ingestion job and poll until it finishes.

        ``soft_fail=True`` is not available on the @task decorator in all
        Airflow versions so we return a result dict regardless; the
        downstream transformation uses TriggerRule.ALL_DONE.
        """
        trigger_url = f"{PIPELINE_URL}/ingestion/start/{parser_name}"
        try:
            resp = requests.post(trigger_url, timeout=15)
            resp.raise_for_status()
            job = resp.json()
            job_id = job["job_id"]
        except Exception as exc:
            # Parser may be temporarily unavailable — log and return failure
            return {"parser": parser_name, "status": "failed", "error": str(exc)}

        status_url = f"{PIPELINE_URL}/ingestion/jobs/{job_id}"
        try:
            result = _poll_until_done(status_url, INGEST_POLL_TIMEOUT_S, INGEST_POLL_INTERVAL_S)
            return {"parser": parser_name, "job_id": job_id, **result}
        except (TimeoutError, RuntimeError) as exc:
            # Return failure info rather than raising so the fan-in
            # transformation task still runs via TriggerRule.ALL_DONE.
            return {"parser": parser_name, "job_id": job_id, "status": "failed", "error": str(exc)}

    @task(
        task_id="trigger_transformation",
        trigger_rule=TriggerRule.ALL_DONE,  # run even if some parsers failed
    )
    def trigger_transformation(ingest_results: list[dict]) -> dict:
        """
        Kick off Bronze→Silver→Gold transformation after all parsers are done.

        Counts how many parsers succeeded so the result is visible in
        the Airflow UI XCom panel.
        """
        completed = [r for r in ingest_results if r.get("status") == "completed"]
        failed = [r for r in ingest_results if r.get("status") != "completed"]
        if failed:
            failed_names = [r.get("parser", "unknown") for r in failed]
            import logging
            logging.getLogger(__name__).warning(
                "Some parsers failed, proceeding with transformation anyway: %s",
                failed_names,
            )

        if not completed:
            # Nothing was ingested — skip transformation
            return {"status": "skipped", "reason": "all parsers failed"}

        resp = requests.post(f"{PIPELINE_URL}/pipeline/transformation", timeout=15)
        resp.raise_for_status()
        job = resp.json()
        job_id = job["job_id"]

        status_url = f"{PIPELINE_URL}/pipeline/jobs/{job_id}"
        result = _poll_until_done(status_url, TRANSFORM_POLL_TIMEOUT_S, TRANSFORM_POLL_INTERVAL_S)
        return {
            "job_id": job_id,
            "parsers_completed": len(completed),
            "parsers_failed": len(failed),
            **result,
        }

    # Wire up: fan-out ingestion → fan-in transformation
    ingest_results = ingest_parser.expand(parser_name=ALL_PARSERS)
    trigger_transformation(ingest_results)


# Airflow 3.x requires the DAG to be instantiated at module level
ingest_dag()
