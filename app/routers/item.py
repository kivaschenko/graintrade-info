import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import List, Annotated
from asyncpg import Connection
from app.schemas import ItemInDB, ItemInResponse
from app.repositories import AsyncpgItemRepository
from app.database import get_db
from app.service_layer.unit_of_works import AsyncpgUnitOfWork
from app import JWT_SECRET

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_item_repository(db: Connection = Depends(get_db)) -> AsyncpgItemRepository:
    return AsyncpgItemRepository(conn=db)


def get_unit_of_work(db: Connection = Depends(get_db)) -> AsyncpgUnitOfWork:
    return AsyncpgUnitOfWork(conn=db)


def get_user(repo, username: str):
    try:
        return repo.get_by_username(username)
    except Exception as e:
        print(e)
        return None


async def get_current_username(token: Annotated[str, Depends(oauth2_scheme)] = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError as e:
        print(e, "is the error")
        raise credentials_exception
    return username


# ------------------------
# standard CRUD operations


@router.post("/items/", response_model=ItemInResponse)
async def create_item(
    item: ItemInDB,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    print(item, "is the item")
    print(token + " is the token")
    username = await get_current_username(token)
    print(username, "is the username")
    return await repo.create(item, username)


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

@router.get("/filter-items/", response_model=List[ItemInResponse])
async def filter_items(
    min_price: float = None,
    max_price: float = None,
    currency: str = None,
    min_amount: int = None,
    max_amount: int = None,
    measure: str = None,
    terms_delivery: str = None,
    country: str = None,
    region: str = None,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
):
    return await repo.get_filtered_items(
        min_price=min_price,
        max_price=max_price,
        currency=currency,
        min_amount=min_amount,
        max_amount=max_amount,
        measure=measure,
        terms_delivery=terms_delivery,
        country=country,
        region=region,
    )