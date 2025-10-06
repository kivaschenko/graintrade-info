import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt

from ..models import subscription_model, tarif_model
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
        "import:export": "Allowed to import/export data via Excel/CSV.",
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
LIMIT_KEYS = {
    "map_views": "map_views_limit",
    "geo_search_count": "geo_search_limit",
    "navigation_count": "navigation_limit",
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
        # Get usage info for current user
        usage_info = await subscription_model.get_subscription_usage_for_user(user_id)
        counter_usage = usage_info.get(counter)
        scope = usage_info.get("tarif_scope")
        tarif = await tarif_model.get_tarif_by_scope(scope)
        limit_key = LIMIT_KEYS[counter]
        counter_limit = tarif.__getattribute__(limit_key)
        if counter_usage < counter_limit:
            counter_usage = await COUNTERS[counter](user_id)
            return {"status": "success", "counter": counter_usage}
        else:
            return {"status": "denied", "counter": counter_usage}
    except Exception as e:
        logging.error(f"Error during update map_vie for user_id: {user_id} {e}.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Counter {counter} not updated.",
        )
