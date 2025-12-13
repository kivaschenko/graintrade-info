import logging
from time import perf_counter

import asyncpg
import redis

from .config import DATABASE_URL, REDIS_URL
from .metrics import (
    DATABASE_CONNECTION_CALLS,
    DATABASE_CONNECTION_DURATION,
    DATABASE_CONNECTION_ERRORS,
)


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url

    async def connect(self):
        operation = "postgres_connect"
        DATABASE_CONNECTION_CALLS.labels(operation=operation).inc()
        start = perf_counter()
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.database_url, min_size=10, max_size=10, max_queries=50000
            )
        except Exception as exc:
            DATABASE_CONNECTION_ERRORS.labels(operation=operation).inc()
            logging.exception(f"Failed to create PostgreSQL pool: {exc}")
            raise
        else:
            logging.info(f"Created Pool for DB: {self.pool}")
        finally:
            duration = perf_counter() - start
            DATABASE_CONNECTION_DURATION.labels(operation=operation).observe(duration)

    async def disconnect(self):
        operation = "postgres_disconnect"
        DATABASE_CONNECTION_CALLS.labels(operation=operation).inc()
        start = perf_counter()
        try:
            if hasattr(self, "pool") and self.pool:
                await self.pool.close()
        except Exception as exc:
            DATABASE_CONNECTION_ERRORS.labels(operation=operation).inc()
            logging.exception(f"Error closing PostgreSQL pool: {exc}")
            raise
        else:
            logging.info("Disconnect the DB...")
        finally:
            duration = perf_counter() - start
            DATABASE_CONNECTION_DURATION.labels(operation=operation).observe(duration)


if DATABASE_URL:
    database = Database(DATABASE_URL)
else:
    raise ValueError("DATABASE_URL not defined!")

# ---------------------
# Redis connector


class RedisDB:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url

    def connect(self):
        operation = "redis_connect"
        DATABASE_CONNECTION_CALLS.labels(operation=operation).inc()
        start = perf_counter()
        try:
            self.pool = redis.ConnectionPool().from_url(self.redis_url)
        except Exception as exc:
            DATABASE_CONNECTION_ERRORS.labels(operation=operation).inc()
            logging.exception(f"Failed to create Redis pool: {exc}")
            raise
        else:
            logging.info(f"Created Pool for Redis: {self.pool}")
        finally:
            duration = perf_counter() - start
            DATABASE_CONNECTION_DURATION.labels(operation=operation).observe(duration)

    def disconnect(self):
        operation = "redis_disconnect"
        DATABASE_CONNECTION_CALLS.labels(operation=operation).inc()
        start = perf_counter()
        try:
            if hasattr(self, "pool") and self.pool:
                self.pool.close()
        except Exception as exc:
            DATABASE_CONNECTION_ERRORS.labels(operation=operation).inc()
            logging.exception(f"Error closing Redis pool: {exc}")
            raise
        else:
            logging.info("Closed Redis connection...")
        finally:
            duration = perf_counter() - start
            DATABASE_CONNECTION_DURATION.labels(operation=operation).observe(duration)


if REDIS_URL:
    redis_db = RedisDB(redis_url=REDIS_URL)
else:
    raise ValueError("REDIS_URL not defined!")
