import logging
from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg import Connection
from app.adapters import AsyncpgUserRepository
from app.infrastructure.database import get_db

# ==========================================================
# Import environment variables
from dotenv import load_dotenv
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

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
logging.info(
    f"Environment variables loaded successfully from {BASE_DIR / '.env'} into item_routers.py"
)
# ==========================================================

router = APIRouter(tags=["map"])


def get_user_repository(db: Connection = Depends(get_db)) -> AsyncpgUserRepository:
    return AsyncpgUserRepository(conn=db)


@router.post("/map/view")
async def increment_map_view(
    user_id: int,
    repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.map_views >= MAP_VIEW_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Map view limit reached"
        )

    new_map_views = await repo.increment_map_views(user_id)
    return {"map_views": new_map_views}
