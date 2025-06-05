from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..service_layer import payment_service


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/confirm")
async def confirm_payment(request: Request):
    r = await request.json()
    print("Received payment confirmation:", r)
    try:
        if r["response_status"] != "success":
            return JSONResponse(
                content={"status": "error", "message": "Payment not confirmed"},
                status_code=400,
            )
        # order_id = r["order_id"]
        # signature = r["signature"]
        # if not payment_service.verify_payment(order_id, signature):
        #     return JSONResponse(
        #         content={"status": "error", "message": "Signature verification failed"},
        #         status_code=400,
        #     )
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
