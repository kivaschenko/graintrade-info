# payments/checkout.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from .liqpay_client import LiqPayClient
from .now_client import NowClient
from ..models import payment_model  # має мати create(normalized)
from ..schemas import SubscriptionInDB
from ..database import redis_db
from datetime import date, timedelta
from databases import Database

router = APIRouter(prefix="/checkout", tags=["checkout"])
db = Database(os.getenv("DATABASE_URL"))


class CheckoutIn(BaseModel):
    user_id: int
    plan_id: int
    method: str  # "card" | "crypto"
    currency: str = "UAH"
    crypto_currency: str = "USDTTRC20"  # для crypto
    amount: float
    description: str = "Subscription"


@router.post("")
async def start_checkout(p: CheckoutIn):
    order_id = f"sub_{p.user_id}_{p.plan_id}"
    base = os.getenv("BASE_URL", "https://example.com")

    # забезпечуємо запис підписки
    sub_id = await db.fetch_val(
        "INSERT INTO subscriptions(user_id, plan_id, status, provider) VALUES ($1,$2,'incomplete',NULL) "
        "ON CONFLICT(user_id,plan_id) DO UPDATE SET status='incomplete' RETURNING id",
        p.user_id,
        p.plan_id,
    )

    if p.method == "card":
        lq = LiqPayClient()
        invoice = await lq.create_checkout(
            amount=p.amount,
            currency=p.currency,
            order_id=order_id,
            description=p.description,
            recurring=True,
            result_url=f"{base}/success?order_id={order_id}",
            server_url=f"{base}/webhooks/liqpay",
        )
        # фронт відкриває iframe: https://www.liqpay.ua/api/3/checkout?data=...&signature=...
        return {
            "ok": True,
            "provider": "liqpay",
            "data": invoice.get("data"),
            "signature": invoice.get("signature"),
        }

    elif p.method == "crypto":
        now = NowClient()
        sub = await now.create_subscription(
            amount=p.amount,
            price_currency=p.currency,
            pay_currency=p.crypto_currency,
            order_id=order_id,
            success_url=f"{base}/success?order_id={order_id}",
            cancel_url=f"{base}/cancel?order_id={order_id}",
        )
        # збережемо provider_ref
        await db.execute(
            "UPDATE subscriptions SET provider='nowpayments', provider_ref=$1 WHERE id=$2",
            sub.get("id"),
            sub_id,
        )
        return {"ok": True, "provider": "nowpayments", "subscription": sub}

    else:
        raise HTTPException(400, "Unknown method")
