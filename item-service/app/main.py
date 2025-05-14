# main.py
from typing import List, Annotated
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
import jwt
from app.schemas import (
    ItemInDB,
    ItemInResponse,
    CategoryInDB,
    CategoryInResponse,
    CategoryWithItems,
)
from app.database import database
from app import items_model, category_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    try:
        yield
    finally:
        await database.disconnect()


JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN")
MAP_VIEW_LIMIT = 100

app = FastAPI(lifespan=lifespan, title="Item-service API", version="0.1.0")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


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


@app.post("/items", response_model=ItemInResponse, status_code=201, tags=["Items"])
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


@app.get("/items", response_model=List[ItemInResponse], status_code=200, tags=["Items"])
async def read_items(
    offset: int = 0,
    limit: int = 10,
):
    return await items_model.get_all(offset=offset, limit=limit)


@app.get(
    "/items/{item_id}", response_model=ItemInResponse, status_code=200, tags=["Items"]
)
async def read_item(item_id: int, token: Annotated[str, Depends(oauth2_scheme)] = None):
    _, scopes = get_current_user_id(token)
    if "read:item" not in scopes:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    db_item = await items_model.get_by_id(item_id)
    if db_item is None:
        logging.error(f"Item with id {item_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return db_item


@app.delete(
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
        user_id, scopes = get_current_user_id(token)
        if "delete:item" not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        await items_model.delete(user_id, item_id)
        return {"status": "success", "message": "Item deleted successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Something went wrong: {e}"}


@app.get(
    "/items-by-user/{user_id}", response_model=List[ItemInResponse], tags=["Items"]
)
async def read_items_by_user(
    user_id: int,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    _, scopes = get_current_user_id(token)
    if "read:item" not in scopes:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return await items_model.get_items_by_user_id(user_id)


@app.get(
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


@app.get("/filter-items", response_model=List[ItemInResponse], tags=["filter items"])
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


# ---------------------
# Category endpoints


@app.post(
    "/categories",
    response_model=CategoryInResponse,
    status_code=201,
    tags=["Categories"],
)
async def create_category(
    category: CategoryInDB,
    # background_tasks: BackgroundTasks,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    print(f"User ID: {user_id}, Scopes: {scopes}")
    if "create:category" not in scopes:
        logging.error("Not enough permissions")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    new_category = await category_model.create(category=category)
    if new_category is None:
        logging.error("Item not created")
        raise HTTPException(status_code=400, detail="Item not created")
    # background_tasks.add_task(
    #     app.state.kafka_handler.send_message, "new-category", new_category
    # )
    return new_category


@app.get(
    "/categories",
    response_model=List[CategoryInResponse],
    status_code=200,
    tags=["Categories"],
)
async def read_categories():
    return await category_model.get_all()


@app.get(
    "/categories/{category_id}",
    response_model=CategoryInResponse,
    status_code=200,
    tags=["Categories"],
)
async def read_category(category_id: int):
    db_category = await category_model.get_by_id(category_id)
    if db_category is None:
        logging.error(f"Category with id {category_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return db_category


@app.get(
    "/categories/{category_id}/items",
    response_model=CategoryWithItems,
    status_code=200,
    tags=["Categories"],
)
async def read_items_by_category(
    category_id: int,
    offeset: int = 0,
    limit: int = 10,
):
    logging.info(f"Getting items for category {category_id}")
    try:
        category_with_items = await category_model.get_by_id_with_items(
            category_id, offeset, limit
        )
        logging.info(f"Category with items: {category_with_items}")
        if category_with_items is None:
            logging.error(f"Category with id {category_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
            )
        return category_with_items
    finally:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
