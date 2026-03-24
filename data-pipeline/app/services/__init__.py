from __future__ import annotations

from typing import Any

__all__ = ["GrainForecastPipeline"]


def __getattr__(name: str) -> Any:
	if name == "GrainForecastPipeline":
		from .grain_forecast_pipeline import GrainForecastPipeline

		return GrainForecastPipeline
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
