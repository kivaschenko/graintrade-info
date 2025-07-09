import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt

from ..models import subscription_model
from . import JWT_SECRET

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

router = APIRouter(tags=["map"])
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


COUNTERS = {
    "map_views": subscription_model.increment_map_views,
    "geo_search_count": subscription_model.increment_geo_search_count,
    "navigation_count": subscription_model.increment_navigation_count,
}

# ----------------------
# Map counters endpoints


@router.post("/mapbox/increment-counter")
async def increment_map_view(
    token: Annotated[str, Depends(oauth2_scheme)], counter: str
):
    if token is None or token == "null" or token == "":
        logging.error("No token provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    user_id, scopes = await get_current_user_id(token)
    user_id = int(user_id)
    try:
        counter = await COUNTERS[counter](user_id)
        return {"status": "success", "counter": counter}
    except Exception as e:
        logging.error(f"Error during update map_vie for user_id: {user_id} {e}.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Counter {counter} not updated.",
        )
