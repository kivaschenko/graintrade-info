import pytest

from fastapi import HTTPException
from fastapi import status

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
