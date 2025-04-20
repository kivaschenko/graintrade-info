from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
print(f"BASE_DIR: {BASE_DIR}")


load_dotenv(BASE_DIR / ".env")
print(f"Loading environment variables from {BASE_DIR / '.env'}")


# Load environment variables from .env file
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN")
MAP_VIEW_LIMIT = os.getenv("MAP_VIEW_LIMIT")

if JWT_SECRET is None:
    raise ValueError("JWT_SECRET not found in .env file")
if ALGORITHM is None:
    raise ValueError("ALGORITHM not found in .env file")
if ACCESS_TOKEN_EXPIRE_MINUTES is None:
    raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES not found in .env file")
if MAP_VIEW_LIMIT is None:
    raise ValueError("MAP_VIEW_LIMIT not found in .env file")
if not JWT_SECRET or not ALGORITHM or not ACCESS_TOKEN_EXPIRE_MINUTES:
    raise ValueError(
        "JWT_SECRET, ALGORITHM, or ACCESS_TOKEN_EXPIRE_MINUTES not found in .env file"
    )
print(f"JWT_SECRET: {JWT_SECRET}")
print(f"ALGORITHM: {ALGORITHM}")
print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {ACCESS_TOKEN_EXPIRE_MINUTES}")
print(f"MAP_VIEW_LIMIT: {MAP_VIEW_LIMIT}")
