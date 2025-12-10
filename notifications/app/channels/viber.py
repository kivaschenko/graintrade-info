import logging
import aiohttp
from ..config import VIBER_TOKEN, VIBER_API_URL
from ..metrics import (
    EXTERNAL_SERVICE_ERRORS,
    FAILED_NOTIFICATIONS_COUNT,
    NOTIFICATIONS_SENT_COUNT,
)

HEADERS = {
    "X-Viber-Auth-Token": VIBER_TOKEN or "",
    "Content-Type": "application/json",
}


async def send_viber_message(user_id: str, text: str):
    if not VIBER_TOKEN:
        logging.warning("Viber disabled: VIBER_TOKEN not set")
        FAILED_NOTIFICATIONS_COUNT.labels(channel="viber", reason="disabled").inc()
        return
    if not user_id:
        logging.warning("Viber skip: empty user_id")
        FAILED_NOTIFICATIONS_COUNT.labels(
            channel="viber", reason="missing_recipient"
        ).inc()
        return
    payload = {
        "receiver": user_id,
        "min_api_version": 1,
        "sender": {"name": "NotifierBot"},
        "type": "text",
        "text": text,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                VIBER_API_URL, json=payload, headers=HEADERS
            ) as resp:
                data = await resp.json()
                if data.get("status") != 0:
                    FAILED_NOTIFICATIONS_COUNT.labels(
                        channel="viber", reason=f"status_{data.get('status')}"
                    ).inc()
                    EXTERNAL_SERVICE_ERRORS.labels(
                        service_name="viber", error_type=str(data.get("status"))
                    ).inc()
                    logging.error(f"Viber API error: {data}")
                else:
                    NOTIFICATIONS_SENT_COUNT.labels(channel="viber").inc()
                    logging.info(f"[VIBER] -> {user_id}")
    except Exception as e:
        error_type = e.__class__.__name__
        FAILED_NOTIFICATIONS_COUNT.labels(channel="viber", reason=error_type).inc()
        EXTERNAL_SERVICE_ERRORS.labels(
            service_name="viber", error_type=error_type
        ).inc()
        logging.error(f"Viber error: {e}")
