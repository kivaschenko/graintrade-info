# database.py
# is responsible for creating a connection pool to the database and creating tables
# using the schema.sql file. It also provides a context manager to get a connection
# from the pool.
from pathlib import Path
import os
import asyncpg
from dotenv import load_dotenv
from contextlib import asynccontextmanager

BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)
load_dotenv(BASE_DIR / ".env")

PGHOST = os.getenv("PGHOST")
PGUSER = os.getenv("PGUSER")
PGPORT = os.getenv("PGPORT")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE")
# DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
DATABASE_URL = "postgresql://admin:test_password@db/postgres"


class Database:
    _pool = None

    @classmethod
    async def init(cls):
        cls._pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10)
        print("Database connection pool created")

    @classmethod
    async def release_connection(cls, connection):
        await cls._pool.release(connection)
        print("Connection released")

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        connection = await cls._pool.acquire()
        try:
            yield connection
        finally:
            await cls.release_connection(connection)

    @classmethod
    async def create_tables(cls):
        print("Creating tables")
        file_path = BASE_DIR / "app" / "schema.sql"
        file_ = open(file_path, "r")
        SCHEMA_SQL = file_.read()
        async with cls.get_connection() as connection:
            await connection.execute(SCHEMA_SQL)
            print("Tables created successfully")
        file_.close()
        print("Finished creating tables")


@asynccontextmanager
async def get_db():
    async with Database.get_connection() as connection:
        yield connection
