from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import logging
from typing import Any, Annotated, Callable, Dict, Iterable, Optional, Set

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..models import subscription_model
from ..routers import JWT_SECRET, ALGORITHM

logger = logging.getLogger(__name__)

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

PLAN_ORDER: Dict[str, int] = {
    "free": 0,
    "premium": 1,
    "business": 2,
    "enterprise": 3,
}


@dataclass(slots=True)
class SubscriptionSnapshot:
    user_id: int
    scope: str
    status: str
    end_date: Optional[date]


@dataclass(slots=True)
class EntitlementContext:
    user_id: int
    token_scopes: Set[str]
    subscription_scope: str
    subscription_status: str
    subscription_expires_at: Optional[date]
    feature: Optional[str] = None
    audit_event: Optional[str] = None

    def has_scope(self, scope: str) -> bool:
        """Convenience helper used by endpoints."""
        return scope in self.token_scopes


async def _get_subscription_snapshot(user_id: int) -> SubscriptionSnapshot:
    subscription = await subscription_model.get_by_user_id(user_id)
    if subscription is None:
        return SubscriptionSnapshot(
            user_id=user_id, scope="free", status="inactive", end_date=None
        )

    status_value = getattr(subscription, "status", "inactive")
    end_date_value = getattr(subscription, "end_date", None)
    if isinstance(end_date_value, datetime):
        end_date_value = end_date_value.date()

    scope_value = getattr(getattr(subscription, "tarif", None), "scope", None) or "free"

    # Expired or inactive subscriptions default to free scope
    if status_value != "active" or (
        end_date_value and end_date_value < datetime.utcnow().date()
    ):
        return SubscriptionSnapshot(
            user_id=user_id, scope="free", status=status_value, end_date=end_date_value
        )

    return SubscriptionSnapshot(
        user_id=user_id,
        scope=scope_value,
        status=status_value,
        end_date=end_date_value,
    )


def _normalize_scopes(raw_scopes: Any) -> Set[str]:
    if raw_scopes is None:
        return set()
    if isinstance(raw_scopes, (list, set, tuple)):
        return {str(scope) for scope in raw_scopes}
    if isinstance(raw_scopes, str):
        if " " in raw_scopes:
            return {part for part in raw_scopes.split(" ") if part}
        return {raw_scopes}
    return {str(raw_scopes)}


async def ensure_feature(user_id: int, feature: str, *, scope: Optional[str] = None):
    scope_value = scope or (await _get_subscription_snapshot(user_id)).scope
    if not ENTITLEMENTS.get(scope_value, {}).get(feature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Feature '{feature}' is not available for current subscription tier",
        )


async def get_feature_value(user_id: int, feature: str, default: Optional[Any] = None):
    snapshot = await _get_subscription_snapshot(user_id)
    return ENTITLEMENTS.get(snapshot.scope, {}).get(feature, default)


def require_entitlement(
    *,
    oauth_scheme: OAuth2PasswordBearer,
    feature: Optional[str] = None,
    requires_scopes: Optional[Iterable[str]] = None,
    min_plan: Optional[str] = None,
    audit_event: Optional[str] = None,
) -> Callable[[str], Any]:
    """Return a FastAPI dependency enforcing subscription-based entitlements.

    The dependency decodes the access token, validates required OAuth scopes,
    checks subscription tier constraints, and optionally enforces feature
    availability declared in ``ENTITLEMENTS``. A successful check returns an
    :class:`EntitlementContext` instance that endpoints can reuse instead of
    re-validating subscription details.
    """

    required_scopes_set = {scope for scope in requires_scopes or []}

    if min_plan and min_plan not in PLAN_ORDER:
        raise ValueError(f"Unknown subscription plan '{min_plan}'")

    async def dependency(
        token: Annotated[str, Depends(oauth_scheme)],
    ) -> EntitlementContext:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        try:
            payload = jwt.decode(token, key=JWT_SECRET, algorithms=[ALGORITHM])
        except (
            jwt.PyJWTError
        ) as exc:  # pragma: no cover - defensive, depends on PyJWT internals
            logger.warning("Failed to decode JWT during entitlement check: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        token_scopes = _normalize_scopes(payload.get("scopes"))

        if required_scopes_set and not required_scopes_set.issubset(token_scopes):
            missing = ", ".join(sorted(required_scopes_set - token_scopes))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required OAuth scope(s): {missing}",
            )

        snapshot = await _get_subscription_snapshot(int(user_id))

        if min_plan:
            user_rank = PLAN_ORDER.get(snapshot.scope, 0)
            required_rank = PLAN_ORDER[min_plan]
            if user_rank < required_rank:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{min_plan.capitalize()} subscription required",
                )

        if feature:
            await ensure_feature(int(user_id), feature, scope=snapshot.scope)

        context = EntitlementContext(
            user_id=int(user_id),
            token_scopes=token_scopes,
            subscription_scope=snapshot.scope,
            subscription_status=snapshot.status,
            subscription_expires_at=snapshot.end_date,
            feature=feature,
            audit_event=audit_event,
        )

        if audit_event:
            logger.info(
                "Entitlement check passed | event=%s user=%s subscription_scope=%s feature=%s required_scopes=%s min_plan=%s",
                audit_event,
                context.user_id,
                context.subscription_scope,
                feature,
                ",".join(sorted(token_scopes)) or "-",
                min_plan or "-",
            )

        return context

    return dependency
