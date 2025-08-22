from fastapi import APIRouter, Request
# from database import db

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/nowpayments")
async def nowpayments_webhook(request: Request):
    data = await request.json()
    order_id = data.get("order_id")
    status = data.get("payment_status")

    if not order_id:
        return {"ok": False}

    if status in ["confirmed", "finished"]:
        await db.execute(
            "UPDATE subscriptions SET status='active' WHERE provider_ref=$1",
            data.get("subscription_id"),
        )

    return {"ok": True}
