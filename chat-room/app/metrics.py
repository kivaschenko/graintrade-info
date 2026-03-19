"""Prometheus metric definitions shared across the chat-room service."""

from prometheus_client import Counter, Gauge, Histogram

# HTTP level metrics
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

# Chat-specific metrics
ACTIVE_CONNECTIONS = Gauge(
    "chat_active_connections",
    "Active WebSocket connections per room",
    labelnames=["room"],
)
ACTIVE_ROOMS = Gauge(
    "chat_active_rooms",
    "Number of chat rooms with at least one active connection",
)
MESSAGES_PERSISTED = Counter(
    "chat_messages_persisted_total",
    "Number of chat messages persisted per room",
    labelnames=["room"],
)
MESSAGES_BROADCAST = Counter(
    "chat_messages_broadcast_total",
    "Number of chat messages broadcast to clients per room",
    labelnames=["room"],
)
INVALID_MESSAGES = Counter(
    "chat_invalid_messages_total",
    "Number of invalid WebSocket payloads rejected",
    labelnames=["room", "reason"],
)
DB_WRITE_LATENCY = Histogram(
    "chat_message_db_write_seconds",
    "Time spent writing chat messages to the database",
    labelnames=["room"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
QUEUE_PUBLISH_LATENCY = Histogram(
    "chat_queue_publish_seconds",
    "Latency of publishing chat messages to the outbound queue",
    labelnames=["queue"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
QUEUE_PUBLISH_ATTEMPTS = Counter(
    "chat_queue_publish_total",
    "Count of queue publish attempts segmented by status",
    labelnames=["queue", "status"],
)
QUEUE_PUBLISH_FAILURES = Counter(
    "chat_queue_publish_failures_total",
    "Number of queue publish operations that raised exceptions",
    labelnames=["queue"],
)
