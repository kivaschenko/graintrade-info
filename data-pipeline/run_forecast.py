"""Run the GrainForecastPipeline with a stable import path.

Usage:
    source venv/bin/activate
    python run_forecast.py

This ensures the project root is on `sys.path` so `import app` works even when
invoked from different working directories or in some IDE run configurations.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.grain_forecast_pipeline import GrainForecastPipeline
from app.logger import logger

if __name__ == "__main__":
    try:
        pipeline = GrainForecastPipeline()
        summary = pipeline.run()
        logger.info("Pipeline summary: %s", summary)
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc)
        raise
