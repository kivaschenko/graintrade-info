"""
The method to create tables in the database.
"""

from pathlib import Path
import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

PGHOST = os.getenv("PGHOST")
PGUSER = os.getenv("PGUSER")
PGPORT = os.getenv("PGPORT")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE")
DSN = f"dbname={PGDATABASE} user={PGUSER} password={PGPASSWORD} host={PGHOST} port={PGPORT}"


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
    with open("schema.sql", "r", encoding="utf-8") as f:
        print("Reading schema.sql file")
        stmt = f.read()
        print(stmt)
        cursor.execute(stmt)
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables created")


if __name__ == "__main__":
    create_tables()
