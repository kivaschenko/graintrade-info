import os
import logging
import asyncpg
from contextlib import asynccontextmanager

logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)


DATABASE_URL = os.getenv("DATABASE_URL")
# DATABASE_URL = "postgresql://admin:dev_password@localhost:5432/postgres"
logger.info(f"Using DATABASE_URL: {DATABASE_URL}")


class Database:
    _pool = None

    @classmethod
    async def init(cls):
        try:
            cls._pool = await asyncpg.create_pool(
                dsn=DATABASE_URL, min_size=1, max_size=10, timeout=60
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Error creating database connection pool: {e}")
            raise e

    @classmethod
    async def release_connection(cls, connection):
        await cls._pool.release(connection)
        logger.info(
            f"Connection {connection} released. Connection pool size: %s",
            cls._pool.get_size(),
        )

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        connection = await cls._pool.acquire()
        try:
            yield connection
        finally:
            await cls.release_connection(connection)


@asynccontextmanager
async def get_db():
    async with Database.get_connection() as connection:
        yield connection
