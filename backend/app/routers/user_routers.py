from datetime import timedelta, datetime, timezone
import logging

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
import bcrypt
import jwt
from ..schemas import (
    UserInCreate,
    UserInDB,
    UserInResponse,
    TokenData,
    Token,
)
from ..models import user_model, subscription_model
from . import JWT_SECRET, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, MAP_VIEW_LIMIT


router = APIRouter(tags=["users"])

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

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# --------------------------
# Scopes according to Tariff
SCOPES = {
    "basic": [
        "me",
        "create:item",
        "read:item",
        "delete:item",
        "view:map",
    ],
    "premium": [
        "me",
        "create:item",
        "read:item",
        "delete:item",
        "view:map",
        "add:category",
    ],
    "pro": [
        "me",
        "create:item",
        "read:item",
        "delete:item",
        "view:map",
        "add:category",
    ],
}


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def get_user(username: str):
    try:
        return user_model.get_by_username(username)
    except Exception as e:
        logging.error(f"Error getting user: {e}")
        return None


async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create an access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
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
    user = await get_user(username=token_data.username)
    if not user:
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
    """Get the current active user."""
    logging.info(f"Current user: {current_user.username}")
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


# =======
# Routes


@router.post("/token", response_model=Token, tags=["login"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Create an access token for the user."""
    logging.info(f"User {form_data.username} is trying to log in")

    if not form_data.username or not form_data.password:
        logging.error("Username or password not provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required",
        )

    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        logging.error("Incorrect username or password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.disabled:
        logging.error("User is disabled")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Get current subscription
        scopes = [
            "me",
        ]
        current_subscr = await subscription_model.get_by_user_id(user.id)
        if current_subscr:
            scope = current_subscr.tarif.scope
            scopes = SCOPES[scope]
        # Create the access token
        access_token_expires = timedelta(minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES))
        access_token = create_access_token(
            data={
                "sub": user.username,
                "scopes": scopes,
                "user_id": user.id,
            },
            expires_delta=access_token_expires,
        )

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token",
            )

        logging.info(f"Access token created for user {user.username}")
        print(f"Access token: {access_token}")
        return Token(access_token=access_token, token_type="bearer")

    except Exception as e:
        logging.error(f"Error during token creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication",
        )


@router.get("/users/me", response_model=UserInResponse, tags=["users"])
async def read_users_me(
    current_user: Annotated[UserInResponse, Depends(get_current_active_user)],
):
    logging.info(f"Current user within users/me: {current_user.username}")
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
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
):
    hashed_password = get_password_hash(user.password)
    user_to_db = UserInDB(
        hashed_password=hashed_password,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
    )
    new_user = await user_model.create(user_to_db)
    logging.info(f"Created a new User: {new_user}")
    return new_user


@router.get(
    "/users/{user_id}",
    response_model=UserInResponse,
    status_code=status.HTTP_200_OK,
    tags=["users"],
)
async def read_user(
    user_id: int,
):
    try:
        user = await user_model.get_by_id(user_id)
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
        phone=user.phone,
    )
    return await user_model.update(user_id, user_to_db)


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK, tags=["users"])
async def delete_user(
    user_id: int,
    current_active_user: Annotated[UserInResponse, Depends(get_current_active_user)],
):
    if current_active_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own user",
        )
    await user_model.delete(user_id)
    return {"status": "success"}


# ====================
# Tariff counters


# @router.post("/map/view")
# async def increment_map_view(
#     token: Annotated[str, Depends(oauth2_scheme)],
# ):
#     """Increment the map view counter for the user."""
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED, detail="Token not found"
#         )
#     user_id, scopes = await get_current_user_id(token)
#     user = await repo.get_by_id(user_id)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#         )

#     if user.map_views >= MAP_VIEW_LIMIT:
#         logging.error("Map view limit reached")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Map view limit reached"
#         )

#     new_map_views = await repo.increment_map_views(user_id)
#     return {"map_views": new_map_views}
