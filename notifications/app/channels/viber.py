import logging
import aiohttp
from ..config import (
    VIBER_TOKEN,
    VIBER_API_URL,
    VIBER_SENDER_NAME,
    VIBER_CHANNEL_POST_URL,
)
from ..metrics import (
    EXTERNAL_SERVICE_ERRORS,
    FAILED_NOTIFICATIONS_COUNT,
    NOTIFICATIONS_SENT_COUNT,
)

HEADERS = {
    "X-Viber-Auth-Token": VIBER_TOKEN or "",
    "Content-Type": "application/json",
}


async def send_viber_message(user_id: str, text: str) -> bool:
    if not VIBER_TOKEN:
        logging.warning("Viber disabled: VIBER_TOKEN not set")
        FAILED_NOTIFICATIONS_COUNT.labels(channel="viber", reason="disabled").inc()
        return False
    if not user_id:
        logging.warning("Viber skip: empty user_id")
        FAILED_NOTIFICATIONS_COUNT.labels(
            channel="viber", reason="missing_recipient"
        ).inc()
        return False
    payload = {
        "receiver": user_id,
        "min_api_version": 1,
        "sender": {"name": VIBER_SENDER_NAME},
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
                    return False
                else:
                    NOTIFICATIONS_SENT_COUNT.labels(channel="viber").inc()
                    logging.info(f"[VIBER] -> {user_id}")
                    return True
    except Exception as e:
        error_type = e.__class__.__name__
        FAILED_NOTIFICATIONS_COUNT.labels(channel="viber", reason=error_type).inc()
        EXTERNAL_SERVICE_ERRORS.labels(
            service_name="viber", error_type=error_type
        ).inc()
        logging.error(f"Viber error: {e}")
        return False

    return False


async def send_viber_channel_post(channel_id: str, text: str) -> bool:
    """Post a text message to a Viber Channel using Channels Post API.

    Requires a Channel token in `VIBER_TOKEN` and a valid `channel_id`.
    """
    if not VIBER_TOKEN:
        logging.warning("Viber disabled: VIBER_TOKEN not set for channel post")
        FAILED_NOTIFICATIONS_COUNT.labels(channel="viber", reason="disabled").inc()
        return False
    if not channel_id:
        logging.warning("Viber skip: empty channel_id")
        FAILED_NOTIFICATIONS_COUNT.labels(
            channel="viber", reason="missing_channel"
        ).inc()
        return False

    payload = {
        "type": "text",
        "text": text,
        "sender": {"name": VIBER_SENDER_NAME},
        "channel_id": channel_id,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                VIBER_CHANNEL_POST_URL, json=payload, headers=HEADERS
            ) as resp:
                data = await resp.json()
                # Viber returns status==0 on success (similar to PA API)
                if data.get("status") != 0:
                    FAILED_NOTIFICATIONS_COUNT.labels(
                        channel="viber", reason=f"status_{data.get('status')}"
                    ).inc()
                    EXTERNAL_SERVICE_ERRORS.labels(
                        service_name="viber", error_type=str(data.get("status"))
                    ).inc()
                    logging.error(
                        f"Viber Channel Post API error (channel {channel_id}): {data}"
                    )
                    return False
                NOTIFICATIONS_SENT_COUNT.labels(channel="viber").inc()
                logging.info(f"[VIBER-CHANNEL] -> {channel_id}")
                return True
    except Exception as e:
        error_type = e.__class__.__name__
        FAILED_NOTIFICATIONS_COUNT.labels(channel="viber", reason=error_type).inc()
        EXTERNAL_SERVICE_ERRORS.labels(
            service_name="viber", error_type=error_type
        ).inc()
        logging.error(f"Viber channel post error: {e}")
        return False

    return False


if __name__ == '__main__':
    import asyncio
    from ..config import VIBER_CHANNEL_ID

    # Try to send test message
    asyncio.run(send_viber_channel_post(channel_id=str(VIBER_CHANNEL_ID), text="Welcome to the channel! \n There is test message..."))