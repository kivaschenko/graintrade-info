from typing import Annotated, List
import logging
import os

from fastapi import (
    Depends,
    HTTPException,
    Security,
    status,
    BackgroundTasks,
    APIRouter,
)
from fastapi.security import (
    OAuth2PasswordBearer,
    SecurityScopes,
)

from asyncpg import Connection
from dotenv import load_dotenv
import bcrypt
import jwt
from .schemas import (
    CategoryInDB,
    CategoryInResponse,
    CategoryWithItems,
    UserInResponse,
    TokenData,
)
from ..infrastructure.database import get_db
from ..adapters import (
    AsyncpgUserRepository,
    AsyncpgCategoryRepository,
)

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN")
MAP_VIEW_LIMIT = 100

router = APIRouter(tags=["Categories"])
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
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

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


def get_category_repository(
    db: Connection = Depends(get_db),
) -> AsyncpgCategoryRepository:
    return AsyncpgCategoryRepository(conn=db)


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


@router.post("/categories", response_model=CategoryInResponse, status_code=201)
async def create_category(
    item: CategoryInDB,
    background_tasks: BackgroundTasks,
    repo: AsyncpgCategoryRepository = Depends(get_category_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    print(f"User ID: {user_id}, Scopes: {scopes}")
    # check scope and permissions here
    # TODO: Implement check for permissions here (e.g. tarif plan premium to create:category)
    if "create:item" not in scopes:
        logging.error("Not enough permissions")
        raise HTTPException(status_code=403, detail="Not enough permissions")
    new_item = await repo.create(item, user_id)
    if new_item is None:
        logging.error("Item not created")
        raise HTTPException(status_code=400, detail="Item not created")
    # background_tasks.add_task(
    #     app.state.kafka_handler.send_message, "new-item", new_item
    # )
    return new_item


@router.get("/categories", response_model=List[CategoryInResponse], status_code=200)
async def read_categories(
    repo: AsyncpgCategoryRepository = Depends(get_category_repository),
):
    return await repo.get_all()


@router.get(
    "/categories/{category_id}",
    response_model=CategoryInResponse,
    status_code=200,
)
async def read_item(
    category_id: int, repo: AsyncpgCategoryRepository = Depends(get_category_repository)
):
    db_item = await repo.get_by_id(category_id)
    if db_item is None:
        logging.error(f"Item with id {category_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return db_item


# ---------------------
# additional operations


@router.get(
    "/categories/{category_id}/items",
    response_model=CategoryWithItems,
    status_code=200,
)
async def read_items_by_category(
    category_id: int,
    offeset: int = 0,
    limit: int = 10,
    repo: AsyncpgCategoryRepository = Depends(get_category_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id, scopes = await get_current_user_id(token)
    logger.info(f"Getting items for category {category_id}")
    category_with_items = await repo.get_by_id_with_items(category_id, offeset, limit)
    logger.debug(f"Category with items: {category_with_items}")
    if category_with_items is None:
        logging.error(f"Category with id {category_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return category_with_items
