# payments/now_client.py
import httpx, os

BASE = "https://api.nowpayments.io/v1"
API_KEY = os.getenv("NOWPAYMENTS_API_KEY")


class NowClient:
    def __init__(self):
        self.h = {"x-api-key": API_KEY, "Content-Type": "application/json"}

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
            "interval": 30,
            "interval_type": "day",
            "price_amount": amount,
            "price_currency": price_currency,
            "pay_currency": pay_currency,
            "order_id": order_id,
            "order_description": f"Subscription {order_id}",
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{BASE}/subscription", json=payload, headers=self.h)
            r.raise_for_status()
            return r.json()

    async def payment_status(self, payment_id: str):
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{BASE}/payment/{payment_id}", headers=self.h)
            r.raise_for_status()
            return r.json()
