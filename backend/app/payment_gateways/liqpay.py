from pathlib import Path
from typing import Optional, Any, Dict
from datetime import date, timedelta, datetime
import asyncio
import hashlib
import httpx
import logging
import uuid
import os
from dotenv import load_dotenv
import redis

from ..models import subscription_model, payment_model
from ..schemas import (
    SubscriptionInDB,
    SubscriptionStatus,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

LIQPAY_PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY")
LIQPAY_PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY")
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


class LiqPayGateway:
    def __init__(
        self,
        public_key: str = LIQPAY_PUBLIC_KEY,
        private_key: str = LIQPAY_PRIVATE_KEY,
    ):
        self.public_key = public_key
        self.private_key = private_key

    def _encode_data(self, params: dict) -> str:
        json_str = json.dumps(params)
        return base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    def _sign_data(self, data: str) -> str:
        sign_str = self.private_key + data + self.private_key
        return base64.b64encode(hashlib.sha1(sign_str.encode("utf-8")).digest()).decode(
            "utf-8"
        )

    async def create_subscription_payment(
        self,
        amount: float,
        order_id: str,
        order_desc: str,
        currency: str = "UAH",
        email: Optional[str] = None,
        server_callback_url: Optional[str] = None,
    ) -> tuple[Dict[str, Any], str]:
        params = {
            "public_key": self.public_key,
            "action": "pay",
            "version": "3",
            "amount": str(amount),
            "currency": currency,
            "description": order_desc,
            "order_id": order_id,
            "recurringbytoken": "1",  # Enable recurring
            "sandbox": "1" if os.getenv("LIQPAY_SANDBOX") == "1" else "0",
        }
        if email:
            params["email"] = email
        if server_callback_url:
            params["server_url"] = server_callback_url

        data = self._encode_data(params)
        signature = self._sign_data(data)
        return {"data": data, "signature": signature}, signature

    async def send_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            r = await client.post(LIQPAY_API_URL, data=params)
        if r.status_code != 200:
            raise Exception("Error from LiqPay API")
        return r.json()

    async def extract_checkout_url(self, r: Dict[str, Any]) -> tuple[str, str]:
        if r.get("status") == "success":
            return r.get("checkout_url", ""), r.get("order_id", "")
        else:
            error_message = r.get("err_description", "Unknown error")
            raise ValueError(f"LiqPay error: {error_message}")

    async def check_payment_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        params = {
            "public_key": self.public_key,
            "action": "status",
            "version": "3",
            "order_id": order_id,
        }
        data = self._encode_data(params)
        signature = self._sign_data(data)
        payload = {"data": data, "signature": signature}
        async with httpx.AsyncClient() as client:
            r = await client.post(LIQPAY_API_URL, data=payload)
        if r.status_code != 200:
            return None
        resp = r.json()
        return resp if resp.get("status") else None
