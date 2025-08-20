from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

from dotenv import load_dotenv

from ..service_layer.nowpayments import NowPaymentsClient
# from database import db

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

router = APIRouter(prefix="/api/crypto", tags=["Crypto"])


class CheckoutRequest(BaseModel):
    user_id: int
    plan_id: int
    amount: float
    currency: str = "UAH"
    crypto_currency: str = "USDTTRC20"


@router.post("/checkout")
async def create_crypto_checkout(data: CheckoutRequest):
    order_id = f"crypto_{data.user_id}_{data.plan_id}"
    client = NowPaymentsClient()

    success_url = f"{os.getenv('BASE_URL')}/success"
    cancel_url = f"{os.getenv('BASE_URL')}/cancel"

    try:
        subscription = await client.create_subscription(
            amount=data.amount,
            price_currency=data.currency,
            pay_currency=data.crypto_currency,
            order_id=order_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        await db.execute(
            "INSERT INTO subscriptions(user_id, plan_id, status, provider, provider_ref) VALUES ($1,$2,'incomplete','nowpayments',$3)",
            data.user_id,
            data.plan_id,
            subscription.get("id"),
        )

        return {"ok": True, "subscription": subscription}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{payment_id}")
async def check_payment_status(payment_id: str):
    client = NowPaymentsClient()
    return await client.get_payment_status(payment_id)
