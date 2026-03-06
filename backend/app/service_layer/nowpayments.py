from pathlib import Path
import httpx
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
BASE = "https://api.nowpayments.io/v1"
API_KEY = os.getenv("NOWPAYMENTS_API_KEY")


class NowPaymentsClient:
    def __init__(self):
        self.headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}

    async def create_subscription(
        self,
        *,
        amount: float,
        price_currency: str,
        pay_currency: str,
        order_id: str,
        success_url: str,
        cancel_url: str,
    ):
        payload = {
            "interval": 30,  # days
            "interval_type": "day",
            "price_amount": amount,
            "price_currency": price_currency,
            "pay_currency": pay_currency,
            "order_id": order_id,
            "order_description": f"Subscription {order_id}",
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BASE}/subscription", headers=self.headers, json=payload
            )
            r.raise_for_status()
            return r.json()

    async def get_payment_status(self, payment_id: str):
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{BASE}/payment/{payment_id}", headers=self.headers)
            r.raise_for_status()
            return r.json()
