import logging
from email.message import EmailMessage
import aiosmtplib
from ..config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASS,
    BULK_MAILTRAP_HOST,
    BULK_MAILTRAP_PASS,
    EMAIL_FROM,
)


async def send_email(to_email: str, subject: str, body_html: str, bulk: bool = False):
    if not to_email:
        logging.warning("Email skip: empty recipient")
        return
    message = EmailMessage()
    message["From"] = EMAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body_html, subtype="html")

    hostname = BULK_MAILTRAP_HOST if bulk else SMTP_HOST
    password = BULK_MAILTRAP_PASS if bulk else SMTP_PASS

    logging.info(f"[EMAIL] -> {to_email} : {subject}")
    await aiosmtplib.send(
        message,
        hostname=hostname,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=password,
        start_tls=True,
    )
