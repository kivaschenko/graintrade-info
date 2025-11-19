from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from ..models import subscription_model

ENTITLEMENTS: Dict[str, Dict[str, Any]] = {
    "free": {
        "exports": False,
        "import_export": False,
        "history_days": 0,
        "alerts_limit": 5,
        "map": True,
    },
    "premium": {
        "exports": True,
        "import_export": False,
        "history_days": 30,
        "alerts_limit": 50,
        "map": True,
    },
    "business": {
        "exports": True,
        "import_export": True,
        "history_days": 180,
        "alerts_limit": 300,
        "map": True,
        "sponsored_slots": 1,
    },
    "enterprise": {
        "exports": True,
        "import_export": True,
        "history_days": 365,
        "alerts_limit": 1000,
        "map": True,
        "sponsored_slots": 3,
    },
}


async def _get_scope_for_user(user_id: int) -> str:
    subscription = await subscription_model.get_by_user_id(user_id)
    if subscription is None or subscription.status != "active":
        return "free"

    if subscription.end_date and subscription.end_date < datetime.utcnow().date():
        return "free"

    scope = getattr(getattr(subscription, "tarif", None), "scope", None)
    return scope or "free"


async def ensure_feature(user_id: int, feature: str):
    scope = await _get_scope_for_user(user_id)
    if not ENTITLEMENTS.get(scope, {}).get(feature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Feature '{feature}' is not available for current subscription tier",
        )

async def get_feature_value(user_id: int, feature: str, default: Optional[Any] = None):
    scope = await _get_scope_for_user(user_id)
    return ENTITLEMENTS.get(scope, {}).get(feature, default)
