# payments/webhooks_now.py
from fastapi import APIRouter, Request
from . import payment_model

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/nowpayments")
async def now_hook(request: Request):
    body = await request.json()
    status = body.get("payment_status")  # waiting, confirmed, finished, failed
    order_id = body.get("order_id")
    if not order_id:
        return {"ok": False}

    if status in ["confirmed", "finished"]:
        normalized = {
            "payment_id": str(body.get("payment_id")),
            "order_id": order_id,
            "order_status": status,
            "currency": body.get("pay_currency"),
            "amount": int(float(body.get("pay_amount", 0)) * 100),
            "payment_system": "nowpayments",
            "provider": "nowpayments",
            "method": "crypto",
            "provider_payment_id": str(body.get("payment_id")),
        }
        await payment_model.create(normalized)
        # активуй підписку до +30 днів
    return {"ok": True}
