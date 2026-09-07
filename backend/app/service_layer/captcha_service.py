import os

import httpx
from fastapi import HTTPException, status


def _captcha_enabled() -> bool:
    return os.getenv("CAPTCHA_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _captcha_secret() -> str:
    return os.getenv("CAPTCHA_SECRET_KEY", "").strip()


def _captcha_verify_url() -> str:
    return os.getenv(
        "CAPTCHA_VERIFY_URL", "https://www.google.com/recaptcha/api/siteverify"
    ).strip()


def _captcha_min_score() -> float:
    try:
        return float(os.getenv("CAPTCHA_MIN_SCORE", "0.5"))
    except ValueError:
        return 0.5


async def verify_captcha_or_raise(
    captcha_token: str | None,
    *,
    remote_ip: str | None = None,
    expected_action: str | None = None,
) -> None:
    if not _captcha_enabled():
        return

    if not captcha_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA token is required",
        )

    secret = _captcha_secret()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CAPTCHA is not configured",
        )

    payload = {"secret": secret, "response": captcha_token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(_captcha_verify_url(), data=payload)
            response.raise_for_status()
            verification = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CAPTCHA verification unavailable",
        )

    if not verification.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA verification failed",
        )

    if expected_action and verification.get("action"):
        if verification.get("action") != expected_action:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CAPTCHA action mismatch",
            )

    score = verification.get("score")
    if score is not None:
        try:
            if float(score) < _captcha_min_score():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CAPTCHA score too low",
                )
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid CAPTCHA score",
            )
