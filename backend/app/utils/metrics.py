from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge, CONTENT_TYPE_LATEST, generate_latest

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency",
    labelnames=["method", "path"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
ACTIVE_SUBSCRIPTIONS = Gauge(
    "active_subscriptions_total",
    "Number of currently active subscriptions",
)
ALERTS_SENT = Counter(
    "alerts_sent_total",
    "Total alerts sent to users",
)
EXPORT_REQUESTS = Counter(
    "export_requests_total",
    "Total export requests",
)

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def metrics_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    # Trim query params and limit path cardinality
    path = request.url.path
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time
    REQUEST_LATENCY.labels(method, path).observe(duration)
    REQUEST_COUNT.labels(method, path, response.status_code).inc()
    return response


def set_active_subscriptions(count: int):
    ACTIVE_SUBSCRIPTIONS.set(count)


def increment_alerts_sent():
    ALERTS_SENT.inc()


def increment_export_requests():
    EXPORT_REQUESTS.inc()
