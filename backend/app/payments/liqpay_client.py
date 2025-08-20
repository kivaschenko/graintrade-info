from pathlib import Path
from datetime import date, timedelta
import hashlib
import base64
import httpx
import logging
import json
import os
from dotenv import load_dotenv
import redis

from ..models import subscription_model, payment_model
from ..schemas import (
    SubscriptionInDB,
    SubscriptionStatus,
)
from ..database import redis_db

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

LIQPAY_PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY", "")
LIQPAY_PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY", "")
LIQPAY_API_URL = "https://www.liqpay.ua/api/request"
BASE_URL = os.getenv("BASE_URL", "localhost:8000")
CALLBACK_URL = f"{BASE_URL}/payments/confirm"
ORDER_DESCRIPTION = "sub-{tarif_name}-{start_date}-{end_date}-{user_id}"


logging.basicConfig(level=logging.INFO)

# -------------------
# Helpers


def create_order_description(
    tarif_name: str,
    start_date: date,
    end_date: date,
    user_id: int,
) -> str:
    """Create description string for payment service"""
    return ORDER_DESCRIPTION.format(
        tarif_name=tarif_name,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
    )


def make_start_end_dates_for_monthly_case() -> tuple[date, date]:
    start_date = date.today()
    end_date = start_date + timedelta(days=31)
    return start_date, end_date


def save_signature_to_cache(order_id: str, signature: str):
    r = redis.Redis().from_pool(redis_db.pool)
    res = r.set(name=order_id, value=signature, ex=600)
    if not res:
        logging.error(f"Failed to save signature for order_id {order_id} in cache")
    else:
        logging.info(f"Signature saved for order_id {order_id} in cache")
    r.close()


def get_signature_from_cache(order_id: str):
    r = redis.Redis().from_pool(redis_db.pool)
    signature = r.get(name=order_id)
    r.close()
    return signature


class LiqPayClient:
    def __init__(self):
        self.pub = LIQPAY_PUBLIC_KEY
        self.prv = LIQPAY_PRIVATE_KEY

    def _encode(self, params: dict) -> str:
        return base64.b64encode(json.dumps(params).encode()).decode()

    def _sign(self, data: str) -> str:
        raw = f"{self.prv}{data}{self.prv}".encode()
        return base64.b64encode(hashlib.sha1(raw).digest()).decode()

    async def create_checkout(
        self,
        *,
        amount: float,
        currency: str,
        order_id: str,
        description: str,
        recurring: bool,
        result_url: str,
        server_url: str,
    ):
        params = {
            "version": "3",
            "public_key": self.pub,
            "action": "pay",
            "amount": amount,
            "currency": currency,
            "description": description,
            "order_id": order_id,
            "result_url": result_url,
            "server_url": server_url,
        }
        if recurring:
            params.update({"subscribe": "1", "subscribe_periodicity": "month"})
        data = self._encode(params)
        sign = self._sign(data)
        async with httpx.AsyncClient() as c:
            r = await c.post(LIQPAY_API_URL, json={"data": data, "signature": sign})
            r.raise_for_status()
            return r.json()  # містить data + signature

    def verify(self, data: str, signature: str) -> bool:
        return self._sign(data) == signature


if __name__ == "__main__":
    import asyncio

    async def test_main():
        # Create test function to get checkout
        liqpay_client = LiqPayClient()
        res = await liqpay_client.create_checkout(
            amount=500.00,
            currency="UAH",
            order_id="test-order-id",
            description="test-description",
            recurring=True,
            result_url="localhost:8000/check-payment",
            server_url="localhost:8000/check",
        )
        print(res)

    asyncio.run(test_main())
