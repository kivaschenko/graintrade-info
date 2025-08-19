# payments/webhooks_liqpay.py
from fastapi import APIRouter, Request, HTTPException
import os, base64, json
from .liqpay_client import LiqPayClient
from . import payment_model  # має мати create(normalized)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
lq = LiqPayClient()


@router.post("/liqpay")
async def liqpay_hook(request: Request):
    form = await request.form()
    data, signature = form.get("data"), form.get("signature")
    if not data or not signature or not lq.verify(data, signature):
        raise HTTPException(401, "Invalid signature")
    obj = json.loads(base64.b64decode(data))
    status = obj.get("status")
    if status not in ["success", "sandbox", "subscribed", "subscr_success"]:
        return {"ok": True, "ignored": status}

    normalized = {
        "payment_id": str(obj.get("payment_id")),
        "order_id": obj.get("order_id"),
        "order_status": status,
        "currency": obj.get("currency"),
        "amount": int(float(obj.get("amount", 0)) * 100),
        "payment_system": "liqpay",
        "provider": "liqpay",
        "method": "card",
        "provider_payment_id": str(obj.get("payment_id")),
    }
    await payment_model.create(normalized)

    # Активуємо підписку на місяць
    # (заміни на свій апдейтер)
    return {"ok": True}
