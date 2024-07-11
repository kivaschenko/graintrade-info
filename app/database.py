import os
import asyncpg
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
PGHOST = os.getenv("PGHOST")
PGUSER = os.getenv("PGUSER")
PGPORT = os.getenv("PGPORT")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE")
DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"


@asynccontextmanager
async def get_db():
    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)
    print("Connected to database!")
    try:
        yield conn
        print("Committing transaction...")
    finally:
        await conn.close()
        print("Connection to database closed!")


async def create_table():
    async with get_db() as conn:
        print("Creating table items if not exists...")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                title VARCHAR(50) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                currency VARCHAR(3) NOT NULL,
                amount INTEGER NOT NULL,
                measure VARCHAR(10) NOT NULL,
                terms_delivery VARCHAR(50) NOT NULL,
                country VARCHAR(150) NOT NULL,
                region VARCHAR(150),
                latitude DECIMAL(9, 6) NOT NULL,
                longitude DECIMAL(9, 6) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
            )
            RETURNING id, title, description, price, currency, amount, measure, terms_delivery, country, latitude, longitude, created_at
            """
        )
        print("Table items created successfully!")
