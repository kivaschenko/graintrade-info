from pathlib import Path
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
logging.info(f"BASE_DIR: {BASE_DIR}")
load_dotenv(BASE_DIR / ".env")
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        logging.info(f"Create Session: {db}")
        yield db
    finally:
        logging.info(f"Close Session: {db}")
        db.close()
