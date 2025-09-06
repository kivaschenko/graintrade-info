import logging
import aiohttp
from ..config import VIBER_TOKEN, VIBER_API_URL

HEADERS = {
    "X-Viber-Auth-Token": VIBER_TOKEN or "",
    "Content-Type": "application/json",
}


async def send_viber_message(user_id: str, text: str):
    if not VIBER_TOKEN:
        logging.warning("Viber disabled: VIBER_TOKEN not set")
        return
    if not user_id:
        logging.warning("Viber skip: empty user_id")
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
                    logging.error(f"Viber API error: {data}")
                else:
                    logging.info(f"[VIBER] -> {user_id}")
    except Exception as e:
        logging.error(f"Viber error: {e}")
