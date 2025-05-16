import logging
import os
from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg import Connection


JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN")
MAP_VIEW_LIMIT = os.getenv("MAP_VIEW_LIMIT")


router = APIRouter(tags=["map"])


# @router.post("/map/view")
# async def increment_map_view(
#     user_id: int,
#     repo: AsyncpgUserRepository = Depends(get_user_repository),
# ):
#     user = await repo.get_by_id(user_id)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#         )

#     if user.map_views >= MAP_VIEW_LIMIT:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Map view limit reached"
#         )

#     new_map_views = await repo.increment_map_views(user_id)
#     return {"map_views": new_map_views}
