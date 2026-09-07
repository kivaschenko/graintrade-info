import pytest

from fastapi import HTTPException
from fastapi import status

from app.service_layer import captcha_service
from app.service_layer.captcha_service import verify_captcha_or_raise


@pytest.mark.asyncio
async def test_captcha_verification_is_skipped_when_disabled(monkeypatch):
    monkeypatch.setenv("CAPTCHA_ENABLED", "false")
    await verify_captcha_or_raise(None)


@pytest.mark.asyncio
async def test_captcha_verification_requires_token_when_enabled(monkeypatch):
    monkeypatch.setenv("CAPTCHA_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_SECRET_KEY", "test-secret")

    with pytest.raises(HTTPException) as exc:
        await verify_captcha_or_raise(None)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == "CAPTCHA token is required"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "payload"),
    [
        (
            "/users/",
            {
                "email": "user@example.com",
                "password": "very-strong-password",
                "full_name": "User Name",
            },
        ),
        ("/password-recovery", {"email": "user@example.com"}),
        ("/reset-password", {"token": "invalid-token", "new_password": "new-password"}),
    ],
)
async def test_protected_forms_require_captcha_token_when_enabled(
    monkeypatch, test_client, path, payload
):
    monkeypatch.setenv("CAPTCHA_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_SECRET_KEY", "test-secret")

    response = await test_client.post(path, json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "CAPTCHA token is required"


class _CaptchaResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _CaptchaAsyncClient:
    def __init__(self, payload):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, data):
        return _CaptchaResponse(self._payload)


@pytest.mark.asyncio
async def test_signup_rejects_captcha_action_mismatch(monkeypatch, test_client):
    monkeypatch.setenv("CAPTCHA_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_SECRET_KEY", "test-secret")
    monkeypatch.setattr(
        captcha_service,
        "httpx",
        type(
            "_HttpxMock",
            (),
            {
                "AsyncClient": lambda timeout: _CaptchaAsyncClient(
                    {"success": True, "action": "wrong_action", "score": 0.9}
                ),
                "HTTPError": Exception,
            },
        ),
    )

    response = await test_client.post(
        "/users/",
        json={
            "email": "user@example.com",
            "password": "very-strong-password",
            "captcha_token": "valid-looking-token",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "CAPTCHA action mismatch"


@pytest.mark.asyncio
async def test_password_recovery_rejects_low_captcha_score(monkeypatch, test_client):
    monkeypatch.setenv("CAPTCHA_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_SECRET_KEY", "test-secret")
    monkeypatch.setenv("CAPTCHA_MIN_SCORE", "0.5")
    monkeypatch.setattr(
        captcha_service,
        "httpx",
        type(
            "_HttpxMock",
            (),
            {
                "AsyncClient": lambda timeout: _CaptchaAsyncClient(
                    {
                        "success": True,
                        "action": "password_recovery",
                        "score": 0.1,
                    }
                ),
                "HTTPError": Exception,
            },
        ),
    )

    response = await test_client.post(
        "/password-recovery",
        json={
            "email": "user@example.com",
            "captcha_token": "valid-looking-token",
        },
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "CAPTCHA score too low"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("path", "payload"),
    [
        (
            "/users/",
            {
                "email": "user@example.com",
                "password": "very-strong-password",
                "captcha_token": "valid-looking-token",
            },
        ),
        (
            "/password-recovery",
            {
                "email": "user@example.com",
                "captcha_token": "valid-looking-token",
            },
        ),
        (
            "/reset-password",
            {
                "token": "invalid-token",
                "new_password": "new-password",
                "captcha_token": "valid-looking-token",
            },
        ),
    ],
)
async def test_protected_forms_reject_missing_captcha_action(
    monkeypatch, test_client, path, payload
):
    monkeypatch.setenv("CAPTCHA_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_SECRET_KEY", "test-secret")
    monkeypatch.setattr(
        captcha_service,
        "httpx",
        type(
            "_HttpxMock",
            (),
            {
                "AsyncClient": lambda timeout: _CaptchaAsyncClient({"success": True}),
                "HTTPError": Exception,
            },
        ),
    )

    response = await test_client.post(path, json=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "CAPTCHA action mismatch"
