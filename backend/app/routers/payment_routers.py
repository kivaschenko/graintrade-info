from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ..service_layer import payment_service
from ..logger import logger


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/confirm/liqpay")
async def confirm_liqpay(request: Request, background_tasks: BackgroundTasks):
    decoded_data = None
    logger.info("LiqPay webhook called")
    try:
        form = await request.form()
        data = form.get("data")
        signature = form.get("signature")
        if not data or not signature:
            logger.error("Missing data or signature in LiqPay webhook form")
            return JSONResponse(
                content={"status": "error", "message": "Missing data or signature"},
                status_code=400,
            )
        import base64
        import json

        decoded_data = json.loads(base64.b64decode(data).decode("utf-8"))
        logger.info(f"LiqPay webhook decoded payload: order_id={decoded_data.get('order_id')}, status={decoded_data.get('status')}")
        print(f"\n\tDecoded LiqPay data: {decoded_data}\n\tSignature: {signature}\n\tRemove this print statement in production code!\n")
    except Exception as e:
        logger.exception("Failed to decode LiqPay webhook payload")
        return JSONResponse(
            content={"status": "error", "message": f"Invalid LiqPay payload: {str(e)}"},
            status_code=400,
        )
    
    try:
        if decoded_data["status"] not in ["success", "subscribed"]:
            logger.warning(f"LiqPay webhook received non-success status: {decoded_data.get('status')}")
            return JSONResponse(
                content={"status": "error", "message": "Payment not confirmed"},
                status_code=400,
            )
        
        logger.info(f"Processing LiqPay payment confirmation for order_id: {decoded_data.get('order_id')}")
        updated = await payment_service.update_subscription_and_save_payment_confirmation(
            decoded_data, payment_provider_name="liqpay"
        )
        if not updated:
            logger.error(f"Failed to update subscription for order_id: {decoded_data.get('order_id')}")
            return JSONResponse(
                content={
                    "status": "error",
                    "message": "Failed to persist payment confirmation",
                },
                status_code=500,
            )
        logger.info(f"Successfully processed LiqPay payment for order_id: {decoded_data.get('order_id')}")
        return JSONResponse(content={"status": "received"})
    except KeyError as e:
        logger.exception(f"Missing required field in LiqPay payment response: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": f"Missing required field: {str(e)}"},
            status_code=400,
        )
    except Exception as e:
        logger.exception(f"Unexpected error processing LiqPay webhook: {str(e)}")
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=500
        )
    finally:
        if decoded_data:
            background_tasks.add_task(
                payment_service.send_success_payment_details_to_queue,
                payment_dict=decoded_data,
            )
