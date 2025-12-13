"""Prometheus metrics for the notifications app."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

from prometheus_client import Counter, Gauge, Histogram

# Business-level metrics for notifications app
NOTIFICATIONS_SENT_COUNT = Counter(
    "notifications_sent_total",
    "Increment for each notification sent",
    labelnames=["channel"],
)
NOTIFICATIONS_PROCESSED_COUNT = Counter(
    "notifications_processed_total",
    "Increment for each notification processed",
    labelnames=["event_type", "channel", "status"],
)
FAILED_NOTIFICATIONS_COUNT = Counter(
    "failed_notifications_total",
    "Increment for each failed notification",
    labelnames=["channel", "reason"],
)
NOTIFICATIONS_PROCESSING_LATENCY = Histogram(
    "notifications_processing_duration_seconds",
    "Time taken to process notifications",
    labelnames=["event_type", "channel"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
NOTIFICATIONS_RETRY_GAUGE = Gauge(
    "notifications_retry_in_progress",
    "Number of notifications currently being retried",
)
TEMPLATE_RENDERING_ERRORS = Counter(
    "template_rendering_errors_total",
    "Increment for each template rendering error",
    labelnames=["template_name"],
)
DELIVERY_LATENCY = Histogram(
    "notification_delivery_latency_seconds",
    "Time taken from notification creation to delivery",
    labelnames=["channel"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)
DATABASE_CONNECTION_ERRORS = Counter(
    "database_connection_errors_total",
    "Increment for each database connection error encountered",
    labelnames=["operation"],
)
DATABASE_CONNECTION_CALLS = Counter(
    "database_connection_calls_total",
    "Increment for each database connection call made",
    labelnames=["operation"],
)
DATABASE_CONNECTION_DURATION = Histogram(
    "database_connection_duration_seconds",
    "Time taken for database connection calls",
    labelnames=["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
)
EXTERNAL_SERVICE_ERRORS = Counter(
    "external_service_errors_total",
    "Increment for each error encountered when calling external services",
    labelnames=["service_name", "error_type"],
)


def begin_notification_processing() -> float:
    """Mark the start of a notification processing attempt."""

    NOTIFICATIONS_RETRY_GAUGE.inc()
    return time.perf_counter()


def finish_notification_processing(
    *,
    event_type: str,
    channel: str,
    status: str,
    start_time: float,
    failure_reason: Optional[str] = None,
) -> None:
    """Record metrics for a completed notification processing attempt."""

    duration = time.perf_counter() - start_time
    NOTIFICATIONS_PROCESSING_LATENCY.labels(
        event_type=event_type, channel=channel
    ).observe(duration)
    NOTIFICATIONS_PROCESSED_COUNT.labels(
        event_type=event_type, channel=channel, status=status
    ).inc()
    if status == "failure":
        FAILED_NOTIFICATIONS_COUNT.labels(
            channel=channel, reason=failure_reason or "unknown"
        ).inc()
    NOTIFICATIONS_RETRY_GAUGE.dec()


def _parse_datetime(value: str) -> Optional[datetime]:
    """Best-effort conversion of a string timestamp to an aware datetime."""

    if not isinstance(value, str) or not value or value.lower() == "none":
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def record_delivery_latency(created_at: Optional[str], channel: str) -> None:
    """Record total latency from creation to delivery when timestamps are available."""

    if not created_at:
        return
    parsed = _parse_datetime(created_at)
    if not parsed:
        return
    now = datetime.now(timezone.utc)
    latency = (now - parsed).total_seconds()
    if latency >= 0:
        DELIVERY_LATENCY.labels(channel=channel).observe(latency)


@asynccontextmanager
async def track_db_operation(operation: str) -> AsyncIterator[None]:
    """Async context manager that captures DB call counts, latency, and failures."""

    DATABASE_CONNECTION_CALLS.labels(operation=operation).inc()
    start = time.perf_counter()
    try:
        yield
    except Exception:
        DATABASE_CONNECTION_ERRORS.labels(operation=operation).inc()
        raise
    finally:
        duration = time.perf_counter() - start
        DATABASE_CONNECTION_DURATION.labels(operation=operation).observe(duration)
