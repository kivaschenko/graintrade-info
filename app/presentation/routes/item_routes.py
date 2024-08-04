from typing import List, Annotated
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from asyncpg import Connection
from app.domain.item import ItemInDB, ItemInResponse
from app.infrastructure import (
    AsyncpgItemRepository,
    AsyncpgItemUserRepository,
    AsyncpgUserRepository,
)
from app.infrastructure.persistence.database import get_db
from config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_item_repository(db: Connection = Depends(get_db)) -> AsyncpgItemRepository:
    return AsyncpgItemRepository(conn=db)


def get_user_repository(db: Connection = Depends(get_db)) -> AsyncpgUserRepository:
    return AsyncpgUserRepository(conn=db)


def get_item_user_repository(
    db: Connection = Depends(get_db),
) -> AsyncpgItemUserRepository:
    return AsyncpgItemUserRepository(conn=db)


def get_user(repo, username: str):
    try:
        return repo.get_by_username(username)
    except Exception as e:
        return None


async def get_current_username(token: Annotated[str, Depends(oauth2_scheme)] = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError as e:
        raise credentials_exception
    return username


async def verify_ownership(user_id, item_id, item_user_repo: AsyncpgItemUserRepository):
    item_user = await item_user_repo.get_by_user_id_item_id(user_id, item_id)
    if item_user is None:
        raise HTTPException(status_code=403, detail="User does not own the item")
    return item_user


# ------------------------
# standard CRUD operations


@router.post("/items", response_model=ItemInResponse, status_code=201, tags=["items"])
async def create_item(
    item: ItemInDB,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = await get_current_username(token)
    return await repo.create(item, username)


@router.get(
    "/items", response_model=List[ItemInResponse], status_code=200, tags=["items"]
)
async def read_items(
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    offset: int = 0,
    limit: int = 10,
):
    return await repo.get_all(offset=offset, limit=limit)


@router.get(
    "/items/{item_id}", response_model=ItemInResponse, status_code=200, tags=["items"]
)
async def read_item(
    item_id: int, repo: AsyncpgItemRepository = Depends(get_item_repository)
):
    db_item = await repo.get_by_id(item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@router.put(
    "/items/{item_id}",
    response_model=ItemInResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["items"],
)
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


@router.delete(
    "/items/{item_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["items"],
)
async def delete_item_bound_to_user(
    item_id: int,
    item_user_repo: AsyncpgItemUserRepository = Depends(get_item_user_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise credentials_exception
        await item_user_repo.remove_item_from_user(user_id, item_id)
        return {"status": "success", "message": "Item deleted successfully"}
    except jwt.ExpiredSignatureError:
        return {"status": "error", "message": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"status": "error", "message": "Invalid token"}
    except Exception as e:
        return {"status": "error", "message": "An error occurred: " + str(e)}


# ---------------------
# additional operations


@router.get(
    "/find-items-in-distance",
    response_model=List[ItemInResponse],
    tags=["filter items"],
)
async def find_items_in_radius(
    latitude: float,
    longitude: float,
    distance: int,  # in meters
    repo: AsyncpgItemRepository = Depends(get_item_repository),
):
    """Find all items within a given distance from a given point. The distance is in meters."""
    return await repo.find_in_distance(latitude, longitude, distance)


@router.get("/filter-items", response_model=List[ItemInResponse], tags=["filter items"])
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
