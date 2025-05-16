import os
import asyncpg


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:test_password@localhost:35432/postgres",
)
print(f"Using DATABASE_URL: {DATABASE_URL}")


class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            dsn=self.database_url, min_size=10, max_size=10, max_queries=50000
        )

    async def disconnect(self):
        self.pool.close()


database = Database(DATABASE_URL)
