import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
DEV_ENV_PATH = BASE_DIR / "dev.env"
DEVELOPMENT = False

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

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRED_IN_MINUTES", "60"))
