import asyncpg
from contextlib import asynccontextmanager


@asynccontextmanager
async def get_db():
    from . import DATABASE_URL

    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    print("Connected to database!")
    try:
        yield conn
        print("Committing transaction...")
    finally:
        await conn.close()
        print("Connection to database closed!")
