from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
import jwt
import bcrypt
from ..models import user_model
from ..utils.email_sender import send_recovery_email
from . import JWT_SECRET, ALGORITHM

router = APIRouter(tags=["password-recovery"])

# Constants
RECOVERY_TOKEN_EXPIRE_MINUTES = 30
RECOVERY_SECRET = "your-recovery-secret-key"  # Move to environment variables
RECOVERY_URL = "http://localhost:8081/reset-password?token={recovery_token}"  # Update to your actual URL


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str


def get_password_hash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@router.post("/password-recovery", status_code=status.HTTP_200_OK)
async def request_password_recovery(
    request: PasswordResetRequest, background_tasks: BackgroundTasks
):
    # Find user by email
    user = await user_model.get_by_email(request.email)
    if not user:
        # Always return success to prevent email enumeration
        return {"message": "If the email exists, a recovery link has been sent"}

    # Generate recovery token
    recovery_token = jwt.encode(
        {
            "user_id": user.id,
            "exp": datetime.now(timezone.utc)
            + timedelta(minutes=RECOVERY_TOKEN_EXPIRE_MINUTES),
        },
        JWT_SECRET,
        algorithm=ALGORITHM,
    )

    # Generate recovery URL
    recovery_url = RECOVERY_URL.format(recovery_token=recovery_token)
    print(recovery_url)
    # Send email in background
    background_tasks.add_task(
        send_recovery_email, email=user.email, recovery_url=recovery_url
    )

    return {"message": "If the email exists, a recovery link has been sent"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(reset_data: PasswordReset):
    try:
        # Verify token
        payload = jwt.decode(reset_data.token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        # Get user
        user = await user_model.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )

        # Update password
        hashed_password = get_password_hash(reset_data.new_password)
        await user_model.update_password(user_id, hashed_password)

        return {"message": "Password successfully updated"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Recovery token has expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
