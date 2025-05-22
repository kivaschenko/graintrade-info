import asyncio
import logging
import asyncpg

import redis


# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "postgresql://admin:test_password@localhost:35432/postgres",
# )
DATABASE_URL = "postgresql://admin:test_password@localhost:35432/postgres"  # debug mode
logging.info(f"Using DATABASE_URL: {DATABASE_URL}")


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn=self.database_url, min_size=10, max_size=10, max_queries=50000
        )
        logging.info("Created Pool for DB: %", self.pool)

    async def disconnect(self):
        await self.pool.close()
        logging.info("Disconnect the DB...")


database = Database(DATABASE_URL)

# ---------------------
# Redis connector

REDIS_URL = "redis://localhost:6379"
# REDIS_URL = "redis://localhost"


class RedisDB:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url

    def connect(self):
        self.pool = redis.ConnectionPool().from_url(self.redis_url)
        logging.info("Created Pool for Redis: %", self.pool)

    def disconnect(self):
        self.pool.close()
        logging.info("Closed Redis connection...")


redis_db = RedisDB(redis_url=REDIS_URL)

if __name__ == "__main__":
    redis_db.connect()
    # Test connection
    print("Redis connected:", redis_db.pool)
    # Close connections
    redis_db.disconnect()
    # Create async loop
    loop = asyncio.get_event_loop()
    # Create database connection
    database = Database(DATABASE_URL)
    # Connect to database
    loop.run_until_complete(database.connect())
    # Test connection
    print("Database connected:", database.pool)
    # Close connections
    loop.run_until_complete(database.disconnect())
