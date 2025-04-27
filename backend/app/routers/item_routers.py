from typing import Annotated, List
import logging

from fastapi import (
    Depends,
    HTTPException,
    Security,
    status,
    BackgroundTasks,
    Query,
    APIRouter,
)
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
)

from asyncpg import Connection
import bcrypt
import jwt
from .schemas import (
    ItemInDB,
    ItemInResponse,
    UserInResponse,
    TokenData,
)
from app.infrastructure.database import get_db
from app.adapters import (
    AsyncpgUserRepository,
    AsyncpgItemRepository,
    AsyncpgItemUserRepository,
)
from app.service_layer.item_services import (
    send_message_to_queue,
)


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

router = APIRouter(tags=["Items"])
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "me": "Read information about the current user.",
        "basic_tarif": "Read and write items, limited access to features.",
        "premium_tarif": "Read and write items, full access to features.",
        "enterprise_tarif": "Read and write items, full access to features.",
        "admin": "Full access to all features.",
    },
)

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


# ==========
# Dependency


def get_user_repository(db: Connection = Depends(get_db)) -> AsyncpgUserRepository:
    return AsyncpgUserRepository(conn=db)


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def get_user(repo, username: str):
    try:
        return repo.get_by_username(username)
    except Exception as e:
        logging.error(f"Error getting user: {e}")
        return None


async def authenticate_user(repo: AsyncpgUserRepository, username: str, password: str):
    user = await get_user(repo, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    repo: AsyncpgUserRepository = Depends(get_user_repository),
    security_scopes: SecurityScopes = SecurityScopes(scopes=[]),
):
    """Get the current user from the token."""
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logging.error("Username not found in token")
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, username=username)
    except jwt.PyJWTError as e:
        logging.error(f"Error decoding token: {e}")
        raise credentials_exception
    user = await get_user(repo, username=token_data.username)
    if user is None:
        logging.error("User not found")
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            logging.error("Not enough permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    return user


async def get_current_active_user(
    current_user: Annotated[UserInResponse, Security(get_current_user, scopes=["me"])],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_item_repository(db: Connection = Depends(get_db)) -> AsyncpgItemRepository:
    return AsyncpgItemRepository(conn=db)


def get_item_user_repository(
    db: Connection = Depends(get_db),
) -> AsyncpgItemUserRepository:
    return AsyncpgItemUserRepository(conn=db)


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)] = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        scopes: str = payload.get("scopes")
        if user_id is None:
            logging.error("No user_id found in token")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logging.error(e)
        raise credentials_exception
    return user_id, scopes


# ------------------------
# standard CRUD operations


@router.post("/items", response_model=ItemInResponse, status_code=201, tags=["Items"])
async def create_item(
    item: ItemInDB,
    background_tasks: BackgroundTasks,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
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
    new_item = await repo.create(item, user_id)
    if new_item is None:
        logging.error("Item not created")
        raise HTTPException(status_code=400, detail="Item not created")
    logging.info(f"New item created: {new_item}")
    # Notify RabbitMQ about the new item
    try:
        # Send the message to RabbitMQ on background
        background_tasks.add_task(send_message_to_queue, new_item)
        logging.info("New item notification sent to RabbitMQ")
    except Exception as e:
        logging.error(f"Error sending message to RabbitMQ: {e}")
    return new_item


@router.get(
    "/items", response_model=List[ItemInResponse], status_code=200, tags=["Items"]
)
async def read_items(
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    offset: int = 0,
    limit: int = 10,
):
    return await repo.get_all(offset=offset, limit=limit)


@router.get(
    "/items/{item_id}", response_model=ItemInResponse, status_code=200, tags=["Items"]
)
async def read_item(
    item_id: int, repo: AsyncpgItemRepository = Depends(get_item_repository)
):
    db_item = await repo.get_by_id(item_id)
    if db_item is None:
        logging.error(f"Item with id {item_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return db_item


@router.put("/items/{item_id}", response_model=ItemInResponse, tags=["Items"])
async def update_item(
    item_id: int,
    item: ItemInDB,
    background_tasks: BackgroundTasks,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    print(f"User ID: {user_id}, Scopes: {scopes}")
    if "update:item" not in scopes:
        logging.error("Not enough permissions")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    updated_item = await repo.update(item_id, user_id, item)
    if updated_item is None:
        logging.error("Item not updated")
        raise HTTPException(status_code=400, detail="Item not updated")
    return updated_item


@router.delete("/items/{item_id}", status_code=200, tags=["Items"])
async def delete_item(
    item_id: int,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    print(f"User ID: {user_id}, Scopes: {scopes}")
    # check scope and permissions here
    if "delete:item" not in scopes:
        logging.error("Not enough permissions")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    try:
        await repo.delete(item_id, user_id)
    except ValueError as e:
        logging.error(e)
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "success", "message": "Item deleted successfully"}


# ---------------------
# additional operations


@router.get(
    "/items-by-user/{user_id}", response_model=List[ItemInResponse], tags=["Items"]
)
async def read_items_by_user(
    user_id: int,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
):
    return await repo.get_items_by_user_id(user_id)


@router.get(
    "/find-items-in-distance", response_model=List[ItemInResponse], tags=["Items"]
)
async def find_items_in_distance(
    latitude: float = Query(..., description="Latitude of the point"),
    longitude: float = Query(..., description="Longitude of the point"),
    distance: int = Query(..., description="Distance in meters"),
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    print(f"User ID: {user_id}, Scopes: {scopes}")
    # check scope and permissions here
    if "read:item" not in scopes:
        logging.error("Not enough permissions")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    items = await repo.find_in_distance(longitude, latitude, distance)
    return items


@router.get("/filter-items", response_model=List[ItemInResponse], tags=["Items"])
async def filter_items(
    min_price: float = Query(None, description="Minimum price"),
    max_price: float = Query(None, description="Maximum price"),
    currency: str = Query(None, description="Currency"),
    min_amount: int = Query(None, description="Minimum amount"),
    max_amount: int = Query(None, description="Maximum amount"),
    measure: str = Query(None, description="Measure"),
    terms_delivery: str = Query(None, description="Terms of delivery"),
    country: str = Query(None, description="Country"),
    region: str = Query(None, description="Region"),
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    print(f"User ID: {user_id}, Scopes: {scopes}")
    # check scope and permissions here
    if "read:item" not in scopes:
        logging.error("Not enough permissions")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    items = await repo.get_filtered_items(
        min_price,
        max_price,
        currency,
        min_amount,
        max_amount,
        measure,
        terms_delivery,
        country,
        region,
    )
    return items
