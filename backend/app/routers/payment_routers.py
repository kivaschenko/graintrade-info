import logging
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import JSONResponse

from ..service_layer import payment_service


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/confirm")
async def confirm_payment(request: Request, background_tasks: BackgroundTasks):
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
