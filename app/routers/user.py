from datetime import timedelta, datetime, timezone
from typing import Annotated
from asyncpg import Connection
from fastapi import Depends, APIRouter, HTTPException, Security, status
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)

import bcrypt
import jwt

from app import JWT_SECRET, JWT_EXPIRATION
from app.database import get_db
from app.schemas import UserInCreate, UserInDB, UserInResponse, TokenData, Token
from app.repositories.user_repository import AsyncpgUserRepository
from app.repositories.item_repository import AsyncpgItemRepository

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"me": "Read information about the current user", "items": "Read items"},
)


def get_user_repository(db: Connection = Depends(get_db)) -> AsyncpgUserRepository:
    return AsyncpgUserRepository(conn=db)


def get_item_repository(db: Connection = Depends(get_db)) -> AsyncpgItemRepository:
    return AsyncpgItemRepository(conn=db)


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
        print(e)
        return None


async def authenticate_user(repo: AsyncpgUserRepository, username: str, password: str):
    user = await get_user(repo, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    return encoded_jwt


async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print(f"payload: {payload}")
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(scopes=token_scopes, sub=username)
    except jwt.PyJWTError:
        raise credentials_exception
    user = await get_user(repo, username)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


async def get_current_active_user(
    current_user: Annotated[UserInDB, Security(get_current_user, scopes=["me"])]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    repo: AsyncpgUserRepository = Depends(get_user_repository),
) -> Token:
    user = await authenticate_user(repo, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=JWT_EXPIRATION)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": form_data.scopes},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me")
async def read_users_me(
    current_user: Annotated[UserInResponse, Depends(get_current_active_user)]
):
    return current_user


@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[UserInResponse, Depends(get_current_active_user)],
    repo: AsyncpgItemRepository = Depends(get_item_repository),
):
    return await repo.get_items_by_user_id(current_user.id)


@router.post(
    "/users/", response_model=UserInResponse, status_code=status.HTTP_201_CREATED
)
async def create_user(
    user: UserInCreate,
    repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    hashed_password = get_password_hash(user.password)
    user_to_db = UserInDB(
        hashed_password=hashed_password,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
    )
    return await repo.create(user_to_db)


@router.get("/users/", response_model=list[UserInResponse])
async def read_users(repo: AsyncpgUserRepository = Depends(get_user_repository)):
    return await repo.get_all()


@router.get("/users/{user_id}", response_model=UserInResponse)
async def read_user(
    user_id: int,
    repo: AsyncpgUserRepository = Depends(get_user_repository),
):
    return await repo.get_by_id(user_id)
