import logging
import asyncpg
import redis
from .config import DATABASE_URL, REDIS_URL


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn=self.database_url, min_size=10, max_size=10, max_queries=50000
        )
        logging.info(f"Created Pool for DB: {self.pool}")

    async def disconnect(self):
        await self.pool.close()
        logging.info("Disconnect the DB...")


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
        self.pool = redis.ConnectionPool().from_url(self.redis_url)
        logging.info(f"Created Pool for Redis: {self.pool}")

    def disconnect(self):
        self.pool.close()
        logging.info("Closed Redis connection...")


if REDIS_URL:
    redis_db = RedisDB(redis_url=REDIS_URL)
else:
    raise ValueError("REDIS_URL not defined!")
