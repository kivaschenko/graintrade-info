# main.py
from typing import List, Annotated
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from asyncpg import Connection
import jwt
from .schemas import ItemInDB, ItemInResponse
from .database import Database, get_db
from .reposirory import AsyncpgItemRepository
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Database.init()
    try:
        yield
    finally:
        await Database._pool.close()

app = FastAPI(lifespan=lifespan)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
JWT_SECRET = settings.jwt_secret
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logging.info(f"Starting {settings.app_name}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_item_repository(db: Connection = Depends(get_db)) -> AsyncpgItemRepository:
    return AsyncpgItemRepository(conn=db)


async def get_current_user_id(token: Annotated[str, Depends(oauth2_scheme)] = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id: str = payload.get("user_id")
        if user_id is None:
            logging.error("No user_id found in token")
            raise credentials_exception
    except jwt.PyJWTError as e:
        logging.error(e)
        raise credentials_exception
    return user_id


# ------------------------
# standard CRUD operations


@app.post("/items", response_model=ItemInResponse, status_code=201, tags=["items"])
async def create_item(
    item: ItemInDB,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    token: Annotated[str, Depends(oauth2_scheme)] = None,
):
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = await get_current_user_id(token)
    return await repo.create(item, user_id)


@app.get(
    "/items", response_model=List[ItemInResponse], status_code=200, tags=["items"]
)
async def read_items(
    repo: AsyncpgItemRepository = Depends(get_item_repository),
    offset: int = 0,
    limit: int = 10,
):
    return await repo.get_all(offset=offset, limit=limit)


@app.get(
    "/items/{item_id}", response_model=ItemInResponse, status_code=200, tags=["items"]
)
async def read_item(
    item_id: int, repo: AsyncpgItemRepository = Depends(get_item_repository)
):
    db_item = await repo.get_by_id(item_id)
    if db_item is None:
        logging.error(f"Item with id {item_id} not found")
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.put(
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
    if token is None:
        logging.error("No token provided")
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = await get_current_user_id(token)
    db_item = await repo.update(item_id, item)
    if db_item is None:
        logging.error(f"Item with id {item_id} not found")
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item


@app.delete(
    "/items/{item_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["items"],
)
async def delete_item_bound_to_user(
    item_id: int,
    token: Annotated[str, Depends(oauth2_scheme)] = None,
    item_repo: AsyncpgItemRepository = Depends(get_item_repository),
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
            logging.error("No user_id found in token")
            raise credentials_exception
        await item_repo.delete(user_id, item_id)
        return {"status": "success", "message": "Item deleted successfully"}
    except jwt.ExpiredSignatureError:
        logging.error("Token has expired")
        return {"status": "error", "message": "Token has expired"}
    except jwt.InvalidTokenError:
        logging.error("Invalid token")
        return {"status": "error", "message": "Invalid token"}
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return {"status": "error", "message": "An error occurred: " + str(e)}


# ---------------------
# additional operations

@app.get("/items-by-user/{user_id}", response_model=List[ItemInResponse], tags=["items"])
async def read_items_by_user(
    user_id: int,
    repo: AsyncpgItemRepository = Depends(get_item_repository),
):
    return await repo.get_items_by_user_id(user_id)


@app.get(
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
    return await repo.find_in_distance(longitude=longitude, latitude=latitude, distance=distance)


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
