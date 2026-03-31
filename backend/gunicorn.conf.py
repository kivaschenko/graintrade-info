# Gunicorn configuration file - Optimized for production
import multiprocessing
import sys

# =======================
# Worker Configuration
# =======================
# Use 4 workers for backend service (limited by container allocation: 1.5 CPU cores)
# This is intentionally conservative to avoid OOM kills
workers = min(4, multiprocessing.cpu_count())

worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000  # Max websocket/connection per worker
worker_timeout = 30        # Kill worker if hanging
max_requests = 1000        # Restart worker after N requests (memory leak prevention)
max_requests_jitter = 50   # Add randomness to request limits

# =======================
# Server Socket
# =======================
bind = "0.0.0.0:8000"
backlog = 2048             # TCP listen backlog

# =======================
# Logging
# =======================
log_file = "-"             # Log to stdout (Docker will capture it)
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(q)s" %(D)s'
accesslog = "-"            # Log to stdout
errorlog = "-"             # Log errors to stdout
loglevel = "warning"       # Log warnings and above

# =======================
# Server Hooks
# =======================
def on_starting(server):
    """Called just before the master process is initialized."""
    print(f"🚀 Gunicorn server starting with {workers} workers", file=sys.stderr)

def when_ready(server):
    """Called just after the server is started."""
    print(f"✅ Gunicorn server ready for requests. Listening on {bind}", file=sys.stderr)

def worker_int(worker):
    """Called when a worker receives SIGINT."""
    print(f"🛑 Worker {worker.pid} received SIGINT", file=sys.stderr)

def worker_abort(worker):
    """Called when a worker is force-closed due to timeout."""
    print(f"⚠️  Worker {worker.pid} aborted (timeout={worker_timeout}s)", file=sys.stderr)
