from datetime import datetime, timezone

from fastapi import HTTPException, status
import logging

from app.schemas import SubscriptionInResponse


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


async def check_subscription_status(subscription: SubscriptionInResponse) -> bool:
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


# --- Helper to check and increment useage ---
async def check_and_increment_usage(user_id: int, usage_type: str):
    pass
