import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..service_layer import payment_service
from ..models import payment_model, subscription_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Payment router initialized")

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/confirm")
async def confirm_payment(request: Request):
    logger.info("Request:", request)
    r = await request.json()

    try:
        if r["response_status"] != "success":
            logger.error("Payment not confirmed")
            # Payment not confirmed
            return JSONResponse(
                content={"status": "error", "message": "Payment not confirmed"},
                status_code=400,
            )
        # Verify signature
        payment_id = r["payment_id"]
        signature = r["signature"]

        print("Order ID:", r["order_id"], type(r["order_id"]))
        if not payment_service.verify_payment(
            payment_id=payment_id, received_signature=signature
        ):
            return JSONResponse(
                content={"status": "error", "message": "Signature verification failed"},
                status_code=400,
            )
        # Save payment data to DB
        payment_to_save = {
            "payment_id": payment_id,
            "order_id": r["order_id"],
            "order_status": r["order_status"],
            "currency": r["currency"],
            "amount": int(r["amount"]),
            "card_type": r["card_type"],
            "masked_card": r["masked_card"],
            "sender_email": r["sender_email"],
            "data": r,  # This is the full response from the payment gateway
        }
        # Save payment to DB
        logger.info("Saving payment to DB:", payment_to_save)
        await payment_model.create(payment_to_save)

        # Update subscription status
        await subscription_model.update_status(status="active", payment_id=payment_id)

        return JSONResponse(content={"status": "recieved"})
    except KeyError as e:
        logger.error("KeyError: %", e)
        return JSONResponse(
            content={"status": "error", "message": f"Missing required field: {str(e)}"},
            status_code=400,
        )

    except Exception as e:
        logger.error("Error processing payment: %", e)
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=500
        )
