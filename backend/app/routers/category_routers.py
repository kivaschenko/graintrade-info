from typing import Annotated, List
import logging

from fastapi import (
    Depends,
    HTTPException,
    status,
    APIRouter,
)
from fastapi.security import (
    OAuth2PasswordBearer,
)

import jwt
from .schemas import (
    CategoryInDB,
    CategoryInResponse,
    CategoryWithItems,
)
from ..models import category_model
from . import JWT_SECRET


router = APIRouter(tags=["Categories"])

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


# ---------------------
# Category endpoints


@router.post(
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


@router.get(
    "/categories",
    response_model=List[CategoryInResponse],
    status_code=200,
    tags=["Categories"],
)
async def read_categories():
    return await category_model.get_all()


@router.get(
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


@router.get(
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
