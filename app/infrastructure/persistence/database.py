import asyncpg
from contextlib import asynccontextmanager
from config import settings


@asynccontextmanager
async def get_db():
    from ... import DATABASE_URL

    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    print("Connected to database!")
    try:
        yield conn
        print("Committing transaction...")
    finally:
        await conn.close()
        print("Connection to database closed!")


class Database:
    _pool = None

    @classmethod
    async def init(cls):
        cls._pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
        print("pool", cls._pool.__repr__())

    @classmethod
    def release_connection(cls, connection):
        cls._pool.release(connection)
        print("connection released", connection)

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        connection = await cls._pool.acquire()
        print("connection", connection)
        try:
            yield connection
        finally:
            cls.release_connection(connection)
            print("connection released", connection)

    @classmethod
    async def create_tables(cls):
        print("Creating tables")
        file_path = settings.BASE_DIR / "app" / "schemas" / "schema.sql"
        print("file_path", file_path)
        file_ = open(file_path, "r")
        SCHEMA_SQL = file_.read()
        print("SCHEMA_SQL", SCHEMA_SQL)
        async with cls.get_connection() as connection:
            await connection.execute(SCHEMA_SQL)
            print("Tables created successfully")
        file_.close()
        print("Finished creating tables")
