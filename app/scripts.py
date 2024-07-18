import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
DEV_ENV_PATH = BASE_DIR / "dev.env"

DEVELOPMENT = os.getenv("DEVELOPMENT", "False").lower() == "true"
# Load environment variables from .env file or from sample_env if development mode
if not DEVELOPMENT:
    load_dotenv(ENV_PATH, override=True)
    print("Loaded .env file!")
else:
    try:
        load_dotenv(DEV_ENV_PATH, override=True)
    except FileNotFoundError:
        print("dev.env file not found! Loading sample_env file...")
        load_dotenv("sample_env")
    finally:
        print("Loaded sample_env file!")

PGHOST = os.getenv("PGHOST")
PGUSER = os.getenv("PGUSER")
PGPORT = os.getenv("PGPORT")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE")
DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"
# DATABASE_URL = "postgresql://user:password@db/dbname"
print(f"DATABASE_URL: {DATABASE_URL}")


def create_item_table(cursor):
    """Create table items if not exists"""
    print("Creating table items if not exists...")
    res = cursor.execute(
        """CREATE TABLE IF NOT EXISTS items (
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
            created_at TIMESTAMP DEFAULT NOW()
        );"""
    )
    print("Table items created successfully!")
    print(res)


def create_user_table(cursor):
    """Create table users if not exists"""
    print("Creating table users if not exists...")
    res = cursor.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) NOT NULL,
            email VARCHAR(100) NOT NULL,
            full_name VARCHAR(100),
            hashed_password VARCHAR(100) NOT NULL,
            disabled BOOLEAN DEFAULT FALSE
        );"""
    )
    print("Table users created successfully!")
    print(res)


def create_item_user_table(cursor):
    """Create table items_users if not exists"""
    print("Creating table items_users if not exists...")
    res = cursor.execute(
        """CREATE TABLE IF NOT EXISTS items_users (
            id SERIAL PRIMARY KEY,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL
        );"""
    )
    print("Table items_users created successfully!")
    print(res)


def create_tables():
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    create_item_table(cursor)
    create_user_table(cursor)
    create_item_user_table(cursor)

    cursor.close()
    conn.close()
