import logging
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ..service_layer import payment_service


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/confirm")
async def confirm_payment(request: Request, background_tasks: BackgroundTasks):
    print("Fondy webhook called")
    r = await request.json()
    logging.info(f"Received payment confirmation: {r}")
    try:
        if r["response_status"] != "success":
            return JSONResponse(
                content={"status": "error", "message": "Payment not confirmed"},
                status_code=400,
            )
        await payment_service.update_subscription_and_save_payment_confirmation(r)
        return JSONResponse(content={"status": "recieved"})
    except KeyError as e:
        return JSONResponse(
            content={"status": "error", "message": f"Missing required field: {str(e)}"},
            status_code=400,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=500
        )
    finally:
        background_tasks.add_task(
            payment_service.send_success_payment_details_to_queue, r
        )


# ...existing code...

from fastapi import Form


@router.post("/confirm/liqpay")
async def confirm_liqpay(request: Request, background_tasks: BackgroundTasks):
    print("Liqpay webhook called")
    try:
        form = await request.form()
        data = form.get("data")
        signature = form.get("signature")
        if not data or not signature:
            return JSONResponse(
                content={"status": "error", "message": "Missing data or signature"},
                status_code=400,
            )
        import base64
        import json

        decoded_data = json.loads(base64.b64decode(data).decode("utf-8"))
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"Invalid LiqPay payload: {str(e)}"},
            status_code=400,
        )
    logging.info(f"Received payment confirmation: {decoded_data}")
    try:
        if decoded_data["status"] not in ["success", "subscribed"]:
            return JSONResponse(
                content={"status": "error", "message": "Payment not confirmed"},
                status_code=400,
            )
        await payment_service.update_subscription_and_save_payment_confirmation(
            decoded_data, payment_provider_name="liqpay"
        )
        return JSONResponse(content={"status": "recieved"})
    except KeyError as e:
        return JSONResponse(
            content={"status": "error", "message": f"Missing required field: {str(e)}"},
            status_code=400,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)}, status_code=500
        )
    finally:
        background_tasks.add_task(
            payment_service.send_success_payment_details_to_queue,
            payment_dict=decoded_data,
        )


# ...existing code...
