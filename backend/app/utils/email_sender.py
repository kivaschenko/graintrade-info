from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr

conf = ConnectionConfig(
    MAIL_USERNAME="",
    MAIL_PASSWORD="secreet",
    MAIL_FROM="admin@graintrade.info",
    MAIL_PORT=1025,
    MAIL_SERVER="mailhog",
    MAIL_SSL_TLS=False,
    MAIL_STARTTLS=False,
    USE_CREDENTIALS=False,
)


async def send_recovery_email(email: EmailStr, recovery_url: str):
    message = MessageSchema(
        subject="Password Recovery",
        recipients=[email],
        body=f"""
        Hello!

        You have requested to reset your password. Please click the link below to reset it:

        {recovery_url}

        If you didn't request this, please ignore this email.

        The link will expire in 30 minutes.
        """,
        subtype="html",
    )

    fm = FastMail(conf)
    await fm.send_message(message)


# async def send_recovery_email(email: EmailStr, recovery_url: str):
#     print(f"Sending recovery email to {email} with URL: {recovery_url}")
#     message = MessageSchema(
#         subject="Password Recovery",
#         recipients=[email],
#         body=f"""
#         Hello!

#         You have requested to reset your password. Please click the link below to reset it:

#         {recovery_url}

#         If you didn't request this, please ignore this email.

#         The link will expire in 30 minutes.
#         """,
#         subtype="html",
#     )
#     print(f"Message prepared: {message}")
