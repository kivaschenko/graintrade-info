from datetime import timedelta, datetime, timezone
import logging
import os
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Security,
    status,
    BackgroundTasks,
)
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from asyncpg import Connection
from dotenv import load_dotenv
import bcrypt
import jwt
from app.routers.schemas import (
    UserInCreate,
    UserInDB,
    UserInResponse,
    TokenData,
    Token,
)
from app.infrastructure.database import get_db
from app.adapters import AsyncpgUserRepository

load_dotenv("../.env")
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("JWT_EXPIRES_IN")

router = APIRouter(tags=["users"])

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


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create an access token.
    TODO: Add more information to the token. For example, the user's role.
    Check the current tarif plan, define the user's permissions, etc.
    For now, we only add the expiration date.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)] = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("user_id")
        scopes: str = payload.get("scopes")
        if user_id is None:
            logging.error("No user_id found in token")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logging.error(e)
        raise credentials_exception
    return user_id, scopes


# =======
# Routes


@router.post("/token", response_model=Token, tags=["login"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    repo: AsyncpgUserRepository = Depends(get_user_repository),
) -> Token:
    """Create an access token for the user."""
    user = await authenticate_user(repo, form_data.username, form_data.password)
    if not user:
        logging.error("Incorrect username or password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.jwt_expires_in)
    # TODO: Add more information to the token. For example, the user's role.
    # Check the current tarif plan, define the user's permissions, etc.
    access_token = create_access_token(
        data={
            "sub": user.username,
            "scopes": ["me", "create:item", "read:item", "update:item", "delete:item"],
            "user_id": user.id,
        },
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=UserInResponse, tags=["users"])
async def read_users_me(
    current_user: Annotated[UserInResponse, Depends(get_current_active_user)],
):
    return current_user


@router.post(
    "/users/",
    response_model=UserInResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["users"],
)
async def create_user(
    user: UserInCreate,
    background_tasks: BackgroundTasks,
    repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    hashed_password = get_password_hash(user.password)
    user_to_db = UserInDB(
        hashed_password=hashed_password,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
    )
    new_user = await repo.create(user_to_db)
    if new_user is None:
        raise HTTPException(status_code=400, detail="User already exists")
    # background_tasks.add_task(send_message_to_kafka_about_new_user, new_user)
    return new_user


@router.get(
    "/users/",
    response_model=list[UserInResponse],
    status_code=status.HTTP_200_OK,
    tags=["users"],
)
async def read_users(repo: AsyncpgUserRepository = Depends(get_user_repository)):
    return await repo.get_all()


@router.get(
    "/users/{user_id}",
    response_model=UserInResponse,
    status_code=status.HTTP_200_OK,
    tags=["users"],
)
async def read_user(
    user_id: int,
    repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    try:
        user = await repo.get_by_id(user_id)
        return user
    except Exception as e:
        logging.error(f"Error getting user: {e}")
        raise HTTPException(status_code=404, detail="User not found")


@router.put(
    "/users/{user_id}",
    response_model=UserInResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["users"],
)
async def update_user(
    user_id: int,
    user: UserInCreate,
    current_active_user: Annotated[UserInResponse, Depends(get_current_active_user)],
    repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    if current_active_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own user",
        )
    user_to_db = UserInDB(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
    )
    return await repo.update(user_id, user_to_db)


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK, tags=["users"])
async def delete_user(
    user_id: int,
    current_active_user: Annotated[UserInResponse, Depends(get_current_active_user)],
    repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    if current_active_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own user",
        )
    await repo.delete(user_id)
    return {"status": "success"}


# ====================
# Tariff counters


@router.post("/map/view")
async def increment_map_view(
    token: Annotated[str, Depends(oauth2_scheme)],
    repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    """Increment the map view counter for the user."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found"
        )
    user_id, scopes = await get_current_user_id(token)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.map_views >= settings.map_view_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Map view limit reached"
        )

    new_map_views = await repo.increment_map_views(user_id)
    return {"map_views": new_map_views}
