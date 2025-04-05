# database.py
# is responsible for creating a connection pool to the database and creating tables
# using the schema.sql file. It also provides a context manager to get a connection
# from the pool.
from pathlib import Path
import os
import logging
import asyncpg
from dotenv import load_dotenv
from contextlib import asynccontextmanager

logger = logging.getLogger("app_logger")
BASE_DIR = Path(__file__).resolve().parent.parent
print(f"BASE_DIR: {BASE_DIR}")
SCHEMA_SQL_FILE = BASE_DIR / "infrastructure" / "schema.sql"
# print(f"SCHEMA_SQL_FILE: {SCHEMA_SQL_FILE}")
CATEGORY_FILE = BASE_DIR / "infrastructure" / "insert_categories.sql"
load_dotenv(BASE_DIR.parent / ".env")

PGHOST = os.getenv("PGHOST")
PGUSER = os.getenv("PGUSER")
PGPORT = os.getenv("PGPORT")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE")
# DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
DATABASE_URL = "postgresql://admin:test_password@localhost:35432/postgres"
print(f"DATABASE_URL: {DATABASE_URL}")


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
        file_path = SCHEMA_SQL_FILE
        file_ = open(file_path, "r")
        SCHEMA_SQL = file_.read()
        async with cls.get_connection() as connection:
            await connection.execute(SCHEMA_SQL)
            print("Tables created successfully")
        file_.close()
        print("Finished creating tables")

    @classmethod
    async def insert_category(cls):
        print("Inserting categories")
        file_ = open(CATEGORY_FILE, "r")
        INSERT_CATEGORIES_SQL = file_.read()
        async with cls.get_connection() as connection:
            await connection.execute(INSERT_CATEGORIES_SQL)
            print("Categories inserted successfully")
        file_.close()
        print("Finished inserting categories")


@asynccontextmanager
async def get_db():
    async with Database.get_connection() as connection:
        yield connection
