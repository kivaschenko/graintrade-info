import jwt
import pytest

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.utils.entitlements import require_entitlement
from app.models import subscription_model
from app.routers import JWT_SECRET, ALGORITHM


def _make_subscription(
    scope: str, status_value: str = "active", days_until_expiry: int = 30
):
    class _Tarif:
        def __init__(self, scope_name: str):
            self.scope = scope_name

    class _Subscription:
        def __init__(self, scope_name: str, subscription_status: str, end_delta: int):
            self.status = subscription_status
            self.end_date = datetime.now(tz=timezone.utc).date() + timedelta(
                days=end_delta
            )
            self.tarif = _Tarif(scope_name)

    return _Subscription(scope, status_value, days_until_expiry)


@pytest.fixture(name="oauth_scheme")
def oauth_scheme_fixture() -> OAuth2PasswordBearer:
    return OAuth2PasswordBearer(tokenUrl="token")


@pytest.mark.asyncio
async def test_require_entitlement_pass(monkeypatch, oauth_scheme):
    async def fake_get_by_user_id(user_id: int):
        assert user_id == 10
        return _make_subscription("business")

    monkeypatch.setattr(subscription_model, "get_by_user_id", fake_get_by_user_id)

    token = jwt.encode(
        {"user_id": 10, "scopes": ["import:export"]}, JWT_SECRET, algorithm=ALGORITHM
    )
    guard = require_entitlement(
        oauth_scheme=oauth_scheme,
        feature="import_export",
        requires_scopes={"import:export"},
        min_plan="business",
        audit_event="test_event",
    )

    context = await guard(token)

    assert context.user_id == 10
    assert context.subscription_scope == "business"
    assert context.has_scope("import:export")


@pytest.mark.asyncio
async def test_require_entitlement_missing_scope(monkeypatch, oauth_scheme):
    async def fake_get_by_user_id(user_id: int):
        return _make_subscription("business")

    monkeypatch.setattr(subscription_model, "get_by_user_id", fake_get_by_user_id)

    token = jwt.encode(
        {"user_id": 24, "scopes": ["read:item"]}, JWT_SECRET, algorithm=ALGORITHM
    )
    guard = require_entitlement(
        oauth_scheme=oauth_scheme,
        feature="import_export",
        requires_scopes={"import:export"},
        min_plan="business",
    )

    with pytest.raises(HTTPException) as exc:
        await guard(token)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Missing required OAuth scope" in exc.value.detail


@pytest.mark.asyncio
async def test_require_entitlement_insufficient_plan(monkeypatch, oauth_scheme):
    async def fake_get_by_user_id(user_id: int):
        return _make_subscription("premium")

    monkeypatch.setattr(subscription_model, "get_by_user_id", fake_get_by_user_id)

    token = jwt.encode(
        {"user_id": 7, "scopes": ["import:export"]}, JWT_SECRET, algorithm=ALGORITHM
    )
    guard = require_entitlement(
        oauth_scheme=oauth_scheme,
        feature="import_export",
        requires_scopes={"import:export"},
        min_plan="business",
    )

    with pytest.raises(HTTPException) as exc:
        await guard(token)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Business subscription required" in exc.value.detail


@pytest.mark.asyncio
async def test_require_entitlement_feature_denied(monkeypatch, oauth_scheme):
    async def fake_get_by_user_id(user_id: int):
        return _make_subscription("premium")

    monkeypatch.setattr(subscription_model, "get_by_user_id", fake_get_by_user_id)

    token = jwt.encode(
        {"user_id": 11, "scopes": ["read:item"]}, JWT_SECRET, algorithm=ALGORITHM
    )
    guard = require_entitlement(
        oauth_scheme=oauth_scheme,
        feature="import_export",
    )

    with pytest.raises(HTTPException) as exc:
        await guard(token)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Feature 'import_export' is not available" in exc.value.detail
