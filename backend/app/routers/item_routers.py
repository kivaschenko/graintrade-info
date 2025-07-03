from typing import Annotated, List, Optional
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

from ..schemas import (
    ItemInDB,
    ItemInResponse,
    ItemsByUserResponse,
)
from ..models import items_model
from ..service_layer import item_services
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
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# ==========
# Dependency


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)]):
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
    background_tasks: BackgroundTasks,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    if token is None or token == "null" or token == "":
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
    background_tasks.add_task(item_services.send_item_to_queue, new_item)
    return new_item


@router.get("/items", status_code=200, tags=["Items"])
async def read_items(
    offset: int = 0,
    limit: int = 10,
    token: Annotated[str, Depends(oauth2_scheme)] = 'null',
):
    """Get all items with count value"""
    try:
        # Add map access permission check
        if token != 'null':
            _, scopes = await get_current_user_id(token)
            has_map_access = 'view:map' in scopes
        else:
            has_map_access = False
        # Get items and count value
        items, total_items = await items_model.get_all(offset=offset, limit=limit)
        print(f"items: {items}, total_items: {total_items}")
        return {"items": items, "total_items": total_items, "has_map_access": has_map_access}
    except Exception as e:
        logging.error(f"Error in read_items: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get(
    "/items/{item_id}", response_model=ItemInResponse, status_code=200, tags=["Items"]
)
async def read_item(
    item_id: int, token: Annotated[str, Depends(oauth2_scheme)] = "null"
):
    """Return certain item's info."""
    try:
        db_item = await items_model.get_by_id(item_id)
        if db_item is None:
            logging.error(f"Item with id {item_id} not found")
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
        # If token is provided, verify permisiion and increment map views
        if token != "null":
            user_id, scopes = await get_current_user_id(token)
            if "read:item" not in scopes:
                raise HTTPException(status.HTTP_403_FORBIDDEN)
            # Increment map views counter for the user
            await items_model.map_views_increment(user_id)
        return db_item
    except Exception as e:
        logging.error(f"Error in read_item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete(
    "/items/{item_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["Items"],
)
async def delete_item_bound_to_user(
    item_id: int,
    token: Annotated[
        str, Depends(oauth2_scheme)
    ] = "null",  # Default to 'null' if no token is provided
):
    """Delete an item by its ID, only if the user has the 'delete:item' scope."""
    if token == "null":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided"
        )
    try:
        user_id, scopes = await get_current_user_id(token)
        if "delete:item" not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        await items_model.delete(item_id, user_id)
        return {"status": "success", "message": "Item deleted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Something went wrong: {e}"}


@router.get(
    "/items-by-user/{user_id}", response_model=ItemsByUserResponse, tags=["Items"]
)
async def read_items_by_user(
    user_id: int,
    offset: int = 0,
    limit: int = 10,
    token: Annotated[
        str, Depends(oauth2_scheme)
    ] = "null",  # Default to 'null' if no token is provided,
):
    """Return all items created by a specific user."""
    try:
        if token == "null":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided"
            )
        _, scopes = await get_current_user_id(token)
        if "read:item" not in scopes:
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        items, total_items = await items_model.get_items_by_user_id(
            user_id=user_id, offset=offset, limit=limit
        )
        return {"items": items, "total_items": total_items}
    except Exception as e:
        logging.error(f"Error read items by user_id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


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
    min_price: float = 0.0,
    max_price: float = 999999.0,
    currency: str = "UAH",
    min_amount: int = 0,
    max_amount: int = 999999,
    measure: str = "",
    terms_delivery: str = "",
    country: str = "",
    region: str = "",
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


@router.get("/items-geojson", response_model=dict, tags=["Items"])
async def get_items_geojson(
    category_id: Optional[int] = None,
    offer_type: Optional[str] = "all",
    min_price: Optional[int] = 0,
    max_price: Optional[int] = 999999,
    country: Optional[str] = "all",
    currency: Optional[str] = "all",
    incoterm: Optional[str] = "all",
    token: Annotated[str, Depends(oauth2_scheme)] = "null",
):
    """Get filtered items with geo information.
    GET /items-geojson?category_id=32&offer_type=buy&min_price=12000&country=Ukraine&currency=uah&incoterm=DAP HTTP/1.1
    """
    try:
        # Optionally, add scope check here if only authorized users can view the full map
        _, scopes = await get_current_user_id(token)
        if "view:map" not in scopes:  # Example scope check
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        items = await items_model.get_filtered_items_geo_json(
            category_id=category_id,
            offer_type=offer_type,
            min_price=min_price,
            max_price=max_price,
            country=country,
            currency=currency,
            incoterm=incoterm,
        )
        return {"status": "success", "items": items}
    except Exception as e:
        logging.error(f"Error in get_all_items_geojson: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
