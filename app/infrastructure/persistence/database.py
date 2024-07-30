import asyncpg
from contextlib import asynccontextmanager
from config import settings


class Database:
    _pool = None

    @classmethod
    async def init(cls):
        cls._pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
        print("pool", cls._pool.__repr__())

    @classmethod
    async def release_connection(cls, connection):
        await cls._pool.release(connection)
        print("connection released", connection)

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        connection = await cls._pool.acquire()
        print("connection", connection)
        try:
            yield connection
        finally:
            await cls.release_connection(connection)
            print("connection released", connection)

    @classmethod
    async def create_tables(cls):
        print("Creating tables")
        file_path = (
            settings.BASE_DIR / "app" / "infrastructure" / "persistence" / "schema.sql"
        )
        print("file_path", file_path)
        file_ = open(file_path, "r")
        SCHEMA_SQL = file_.read()
        print("SCHEMA_SQL", SCHEMA_SQL)
        async with cls.get_connection() as connection:
            await connection.execute(SCHEMA_SQL)
            print("Tables created successfully")
        file_.close()
        print("Finished creating tables")


@asynccontextmanager
async def get_db():
    async with Database.get_connection() as connection:
        yield connection
        print("connection released by get_db")
