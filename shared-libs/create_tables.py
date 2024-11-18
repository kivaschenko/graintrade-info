"""
The method to create tables in the database.
"""

from pathlib import Path
import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
print(f"BASE_DIR: {BASE_DIR}")
load_dotenv(BASE_DIR / "app" / ".env")
SCHEMA_FILE = BASE_DIR / "app" / "schema.sql"
print(f"SCHEMA_FILE: {SCHEMA_FILE}")
CATEGORIES_FILE = BASE_DIR / "shared-libs" / "insert_categories.sql"

PGHOST = os.getenv("PGHOST")
PGUSER = os.getenv("PGUSER")
PGPORT = os.getenv("PGPORT")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE")
DSN = f"dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD} host={PGHOST} port={PGPORT}"
# DSN = "postgresql://admin:test_password@localhost:35432/postgres"


def create_tables():
    """
    Creates tables in the database using the schema.sql file.

    Args:
        None

    Returns:
        None
    """
    conn = psycopg2.connect(
        dsn=DSN,
    )
    cursor = conn.cursor()
    print("Connected to the database")
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        print("Reading schema.sql file")
        stmt = f.read()
        print(stmt)
        cursor.execute(stmt)
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables created")


def insert_category():
    """
    Inserts categories in the database.

    Args:
        None

    Returns:
        None
    """
    conn = psycopg2.connect(
        dsn=DSN,
    )
    cursor = conn.cursor()
    print("Connected to the database")
    with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
        print("Reading insert_categories.sql file")
        stmt = f.read()
        print(stmt)
        cursor.execute(stmt)
    conn.commit()
    cursor.close()
    conn.close()
    print("Categories inserted")


if __name__ == "__main__":
    print(f"DSN: {DSN}")
    # create_tables()
    insert_category()
