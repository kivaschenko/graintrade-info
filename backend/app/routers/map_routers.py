import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from ..models import subscription_model, tarif_model
from ..utils.entitlements import EntitlementContext, require_entitlement

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
    counter: str,
    entitlement: Annotated[
        EntitlementContext,
        Depends(
            require_entitlement(
                oauth_scheme=oauth2_scheme,
                feature="map",
                requires_scopes={"view:map"},
                audit_event="map_counter",
            )
        ),
    ],
):
    if counter not in COUNTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown counter '{counter}'",
        )

    user_id = entitlement.user_id
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
