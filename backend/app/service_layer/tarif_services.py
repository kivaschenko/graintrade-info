from datetime import datetime, timezone

from fastapi import HTTPException, status
import logging

from app.adapters import AsyncpgItemRepository
from app.routers.schemas import SubscriptionInResponse

TARIFF_LIMITS = {
    "basic": {"items_limit": 5, "map_views": 10},
    "premium": {"items_limit": 20, "map_views": 50},
    "pro": {"items_limit": -1, "map_views": -1},  # unlimited
}


async def check_user_limits(
    user_id: int,
    subscription: SubscriptionInResponse,
    item_repo: AsyncpgItemRepository,
) -> None:
    """Check if user has reached their limits based on subscription."""
    if subscription.tarif.scope == "pro":
        return  # Pro users have no limits

    # Get user's current item count
    user_items = await item_repo.get_items_by_user_id(user_id)
    current_item_count = len(user_items)

    if (
        subscription.tarif.items_limit != -1
        and current_item_count >= subscription.tarif.items_limit
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached your items limit ({subscription.tarif.items_limit}) for {subscription.tarif.name} plan",
        )


async def check_map_view_limit(
    user_id: int,
    subscription: SubscriptionInResponse,
) -> bool:
    """Check if user can view map based on their subscription."""
    if subscription.tarif.map_views_limit == -1:  # unlimited views
        return True

    if subscription.map_views >= subscription.tarif.map_views_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached your map views limit ({subscription.tarif.map_views_limit}) for {subscription.tarif.name} plan",
        )
    return True


async def check_subscription_status(subscription: SubscriptionInResponse) -> None:
    """Check if subscription is active and not expired."""
    current_date = datetime.now(timezone.utc)
    logging.info(
        f"Checking subscription status for user {subscription.user_id} with subscription {subscription.id}"
    )

    if subscription.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your subscription is not active",
        )

    if current_date > subscription.end_date:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your subscription has expired",
        )
    logging.info(
        f"Subscription {subscription.id} is active and valid until {subscription.end_date}"
    )
    return True
