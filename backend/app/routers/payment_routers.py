from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/confirm")
async def confirm_payment(request: Request):
    print("Request:", request)
    r = await request.json()
    print(r)
    return JSONResponse(content={"status": "recieved"})
