from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg import Connection
from app.adapters import AsyncpgUserRepository
from app.infrastructure.database import get_db
from app.config import settings

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

    if user.map_views >= settings.map_view_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Map view limit reached"
        )

    new_map_views = await repo.increment_map_views(user_id)
    return {"map_views": new_map_views}
