from typing import Annotated, List
import logging

from fastapi import (
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    APIRouter,
)
from fastapi.security import (
    OAuth2PasswordBearer,
)

import jwt

from .schemas import (
    ItemInDB,
    ItemInResponse,
)
from ..models import items_model
from . import JWT_SECRET

router = APIRouter(tags=["Items"])
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "me": "Read information about the current user.",
        "create:item": "Allowed to create a new Item",
        "read:item": "Allowed to read items.",
        "delete:item": "Allowed to delete item.",
        "add:category": "Allowed to add a new Category",
        "view:map": "Allowed to view map.",
    },
)

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


# ==========
# Dependency


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)] = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("user_id")
        scopes: str = payload.get("scopes")
        if user_id is None:
            logging.error("No user_id found in token")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logging.error(e)
        raise credentials_exception
    return user_id, scopes


# ------------------
# Items endpoints


@router.post("/items", response_model=ItemInResponse, status_code=201, tags=["Items"])
async def create_item(
    item: ItemInDB,
    # background_tasks: BackgroundTasks,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    logging.info(f"User ID: {user_id}, Scopes: {scopes}")
    # check scope and permissions here
    if "create:item" not in scopes:
        logging.error("Not enough permissions")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    new_item = await items_model.create(item=item, user_id=user_id)
    if new_item is None:
        logging.error("Item not created")
        raise HTTPException(status_code=400, detail="Item not created")
    logging.info(f"New item created: {new_item}")
    # background_tasks.add_task(
    #     app.state.kafka_handler.send_message, "new-item", new_item
    # )

    return new_item


@router.get(
    "/items", response_model=List[ItemInResponse], status_code=200, tags=["Items"]
)
async def read_items(
    offset: int = 0,
    limit: int = 10,
):
    return await items_model.get_all(offset=offset, limit=limit)


@router.get(
    "/items/{item_id}", response_model=ItemInResponse, status_code=200, tags=["Items"]
)
async def read_item(item_id: int, token: Annotated[str, Depends(oauth2_scheme)] = None):
    """Return certain item's info."""
    user_id, scopes = await get_current_user_id(token)
    if "read:item" not in scopes:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    db_item = await items_model.get_by_id(item_id)
    if db_item is None:
        logging.error(f"Item with id {item_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    # Increment map views counter for the user
    await items_model.map_views_increment(user_id)
    return db_item


@router.delete(
    "/items/{item_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["Items"],
)
async def delete_item_bound_to_user(
    item_id: int,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    try:
        user_id, scopes = await get_current_user_id(token)
        if "delete:item" not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        await items_model.delete(user_id, item_id)
        return {"status": "success", "message": "Item deleted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Something went wrong: {e}"}


@router.get(
    "/items-by-user/{user_id}", response_model=List[ItemInResponse], tags=["Items"]
)
async def read_items_by_user(
    user_id: int,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    _, scopes = await get_current_user_id(token)
    if "read:item" not in scopes:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return await items_model.get_items_by_user_id(user_id)


@router.get(
    "/find-items-in-distance",
    response_model=List[ItemInResponse],
    tags=["filter items"],
)
async def find_items_in_radius(
    latitude: float,
    longitude: float,
    distance: int,  # in meters
):
    """Find all items within a given distance from a given point. The distance is in meters."""
    return await items_model.find_in_distance(
        longitude=longitude, latitude=latitude, distance=distance
    )


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
):
    return await items_model.get_filtered_items(
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
