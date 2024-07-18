from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import List, Annotated
from asyncpg import Connection
from app.schemas import ItemInDB, ItemInResponse
from app.repositories.item_repository import AsyncpgItemRepository
from app.database import get_db

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_item_repository(db: Connection = Depends(get_db)) -> AsyncpgItemRepository:
    return AsyncpgItemRepository(conn=db)


# ------------------------
# standard CRUD operations


@router.post("/items/", response_model=ItemInResponse)
async def create_item(
    item: ItemInDB,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    print(item)
    print(token + " is the token")
    return await repo.create(item)


@router.get("/items/", response_model=List[ItemInResponse])
async def read_items(
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    offset: int = 0,
    limit: int = 10,
):
    return await repo.get_all(offset=offset, limit=limit)


@router.get("/items/{item_id}", response_model=ItemInResponse)
async def read_item(
    item_id: int, repo: AsyncpgItemRepository = Depends(get_item_repository)
):
    db_item = await repo.get_by_id(item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.put("/items/{item_id}", response_model=ItemInResponse)
async def update_item(
    item_id: int,
    item: ItemInDB,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    db_item = await repo.update(item_id, item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    await repo.delete(item_id)
    return {"message": "Item deleted successfully"}


# ---------------------
# additional operations


@router.get("/find-items-in-distance/")
async def find_items_in_radius(
    latitude: float,
    longitude: float,
    distance: int,  # in meters
    repo: AsyncpgItemRepository = Depends(get_item_repository),
):
    """Find all items within a given distance from a given point. The distance is in meters."""
    return await repo.find_in_distance(latitude, longitude, distance)
