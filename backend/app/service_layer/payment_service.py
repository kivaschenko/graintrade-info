from pathlib import Path
from typing import Optional, Any, Dict
from datetime import date, timedelta, datetime
import asyncio
import hashlib
import httpx
import logging
import uuid
import os
from dotenv import load_dotenv
import redis

from ..models import subscription_model, payment_model
from ..schemas import (
    SubscriptionInDB,
    SubscriptionStatus,
)
from ..database import redis_db
from ..rabbit_mq import rabbitmq, QueueName

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
FONDY_MERCHANT_ID = os.getenv("FONDY_MERCHANT_ID")
FONDY_MERCHANT_KEY = os.getenv("FONDY_MERCHANT_KEY")
BASE_URL = os.getenv("BASE_URL", "localhost:8000")
CALLBACK_URL = f"{BASE_URL}/payments/confirm"
ORDER_DESCRIPTION = "sub-{tarif_name}-{start_date}-{end_date}-{user_id}"


logging.basicConfig(level=logging.INFO)


# -------------------
# Helpers


def create_order_description(
    tarif_name: str,
    start_date: date,
    end_date: date,
    user_id: int,
) -> str:
    """Create description string for payment service"""
    return ORDER_DESCRIPTION.format(
        tarif_name=tarif_name,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
    )


def make_start_end_dates_for_monthly_case() -> tuple[date, date]:
    start_date = date.today()
    end_date = start_date + timedelta(days=31)
    return start_date, end_date


def save_signature_to_cache(order_id: str, signature: str):
    r = redis.Redis().from_pool(redis_db.pool)
    res = r.set(name=order_id, value=signature, ex=600)
    if not res:
        logging.error(f"Failed to save signature for order_id {order_id} in cache")
    else:
        logging.info(f"Signature saved for order_id {order_id} in cache")
    r.close()


def get_signature_from_cache(order_id: str):
    r = redis.Redis().from_pool(redis_db.pool)
    signature = r.get(name=order_id)
    r.close()
    return signature


def verify_payment(order_id: str, received_signature: str) -> bool:
    calculated_signature = get_signature_from_cache(order_id)
    if not calculated_signature:
        return False
    if isinstance(calculated_signature, bytes):
        calculated_signature = calculated_signature.decode("utf-8")
    if isinstance(received_signature, bytes):
        received_signature = received_signature.decode("utf-8")
    return received_signature == calculated_signature


# -------------------
# Fondy payment service class
class FondyPaymentService:
    API_URL = "https://pay.fondy.eu/api/checkout/url/"

    def __init__(
        self,
        merchant_id: str = FONDY_MERCHANT_ID,  # type: ignore
        merchant_key: str = FONDY_MERCHANT_KEY,  # type: ignore
    ):
        self.merchant_id = merchant_id
        self.merchant_key = merchant_key

    def _generate_signature(self, params: dict) -> str:
        """Generate signature for Fondy API"""
        signature_string = "|".join([str(params[key]) for key in sorted(params.keys())])
        signature_string = f"{self.merchant_key}|{signature_string}"
        return hashlib.sha1(signature_string.encode("utf-8")).hexdigest()

    async def create_subscription_payment(
        self,
        amount: float,  # Value just from DB tarifs table
        order_id: str | None,
        order_desc: str,
        currency: str = "EUR",
        email: Optional[str] = None,
        server_callback_url: Optional[str] = None,
    ) -> tuple[Dict[str, Any], str]:
        """Create recurring payment for subscription"""
        params = {
            "order_id": order_id,
            "merchant_id": self.merchant_id,
            "order_desc": order_desc,
            "amount": str(int(amount * 100)),  # Convert to cents
            "currency": currency,
        }
        if email:
            params["sender_email"] = email
        if server_callback_url:
            params["server_callback_url"] = server_callback_url
        signature = self._generate_signature(params)
        params["signature"] = signature
        return params, signature

    async def send_request_to_fondy_api(self, params: Dict[str, Any]):
        async with httpx.AsyncClient() as client:
            r = await client.post(url=self.API_URL, json={"request": params})
        if r.status_code != 200:
            raise Exception("Error from Fondy API")
        return r.json()

    async def extract_checkout_url(
        self, r: Dict[str, Dict[str, str]]
    ) -> tuple[str, str]:
        response_body: dict = r.get("response", {})
        response_status = response_body.get("response_status", " ")
        if response_status == "success":
            payment_id = response_body.get("payment_id", " ")
            checkout_url = response_body.get("checkout_url", " ")
        elif response_status == "failure":
            error_code = response_body.get("error_code", " ")
            error_message = response_body.get("error_message", " ")
            raise ValueError(
                f"Invalid response from payment service:  {error_code} - {error_message}"
            )
        return checkout_url, payment_id

    async def _make_status_request(self, order_id: str) -> dict:
        """
        Make a request to Fondy API to check payment status
        """
        params = {
            "order_id": order_id,
            "merchant_id": self.merchant_id,
        }
        # Generate signature for status request
        signature = self._generate_signature(params)
        params["signature"] = signature

        async with httpx.AsyncClient() as client:
            r = await client.post(
                url="https://pay.fondy.eu/api/status/order_id", json={"request": params}
            )
            if r.status_code != 200:
                raise ValueError(f"Error from Fondy API: {r.status_code}")

            response = r.json()
            return response.get("response", {})

    async def check_payment_status(self, order_id: str) -> Optional[dict]:
        """
        Check payment status with progressive intervals
        """
        start_time = datetime.now()
        expiration_time = start_time + timedelta(hours=24)

        try:
            # First 5 minutes - check every 30 seconds
            while datetime.now() < start_time + timedelta(minutes=5):
                status = await self._make_status_request(order_id)
                if status.get("order_status") in ["approved", "declined", "expired"]:
                    return status
                await asyncio.sleep(30)

            # Next hour - check every 5 minutes
            while datetime.now() < start_time + timedelta(hours=1):
                status = await self._make_status_request(order_id)
                if status.get("order_status") in ["approved", "declined", "expired"]:
                    return status
                await asyncio.sleep(300)

            # Until expiration - check every 30 minutes
            while datetime.now() < expiration_time:
                status = await self._make_status_request(order_id)
                if status.get("order_status") in ["approved", "declined", "expired"]:
                    return status
                await asyncio.sleep(1800)

            return None

        except Exception as e:
            logging.error(
                f"Error checking payment status for order {order_id}: {str(e)}"
            )
            return None


# ----------------------
# Free subscription case


async def activate_free_subscription(user_id: int, tarif_id: int) -> bool:
    try:
        # Specify free order_id with prefix "free-"
        uuid_str = str(uuid.uuid4())
        uuid_list = ["free"] + uuid_str.split("-")[1:]
        order_id = "-".join(uuid_list)
        start_date, end_date = make_start_end_dates_for_monthly_case()
        # Create new inactive subscription
        subscription = await subscription_model.create(
            SubscriptionInDB(
                user_id=user_id,
                tarif_id=tarif_id,
                start_date=start_date,
                end_date=end_date,
                order_id=order_id,
                status=SubscriptionStatus.INACTIVE,
            )
        )
        logging.info(f"Created a new Free subscription: {subscription}")
        await subscription_model.update_status_by_order_id(
            SubscriptionStatus.ACTIVE, order_id
        )
        logging.info(f"Updated status of subscription: {subscription}")
        if not subscription:
            raise ValueError("Failed to create subscription in the database")
        return True
    except Exception as e:
        logging.error(f"Error was during create free subscription: {e}")
        return False


# ----------------------
# Handlers for Fondy API


async def payment_for_subscription_handler(
    user_id: int,
    tarif_id: int,
    tarif_name: str,
    amount: float,
    currency: str,
    email: str,
    server_callback_url: str = CALLBACK_URL,
) -> str | None:
    try:
        order_id = str(uuid.uuid4())
        start_date, end_date = make_start_end_dates_for_monthly_case()
        subscription = await subscription_model.create(
            SubscriptionInDB(
                user_id=user_id,
                tarif_id=tarif_id,
                start_date=start_date,
                end_date=end_date,
                order_id=order_id,
                status=SubscriptionStatus.INACTIVE,
            )
        )
        if not subscription:
            raise ValueError("Failed to create subscription in the database")
        order_id = subscription.order_id
        fondy_payment_service = FondyPaymentService(
            merchant_id="1396424", merchant_key="test"
        )
        order_desc = create_order_description(tarif_name, start_date, end_date, user_id)
        (
            payment_data,
            signature,
        ) = await fondy_payment_service.create_subscription_payment(
            amount, order_id, order_desc, currency, email, server_callback_url
        )
        logging.info("Payment data:", payment_data)
        r = await fondy_payment_service.send_request_to_fondy_api(payment_data)
        checkout_url, payment_id = await fondy_payment_service.extract_checkout_url(r)
        logging.info("Result:", checkout_url, payment_id)
        if not order_id:
            raise ValueError("Order ID is missing in the response")
        save_signature_to_cache(order_id, signature)
        return checkout_url
    except Exception as e:
        logging.error(f"Error in payment_for_subscription_handler: {str(e)}")
        return None


async def update_subscription_and_save_payment_confirmation(
    payment_response: dict[str, Any],
):
    try:
        payment_data = dict(
            payment_id=payment_response["payment_id"],
            order_id=payment_response["order_id"],
            order_status=payment_response["order_status"],
            currency=payment_response["currency"],
            amount=payment_response["amount"],  # Amount in cents, already converted
            card_type=payment_response["card_type"],
            card_bin=payment_response["card_bin"],
            masked_card=payment_response["masked_card"],
            payment_system=payment_response["payment_system"],
            sender_email=payment_response["sender_email"],
            approval_code=payment_response["approval_code"],
            response_status=payment_response["response_status"],
            tran_type=payment_response["tran_type"],
            eci=payment_response.get("eci"),
            settlement_amount=payment_response.get("settlement_amount"),
            actual_amount=payment_response["actual_amount"],
            order_time=payment_response["order_time"],
            additional_info=payment_response.get("additional_info", {}),
        )
        await payment_model.create(payment_data)
        await subscription_model.update_status_by_order_id(
            SubscriptionStatus.ACTIVE, payment_response["order_id"]
        )
        return True
    except Exception as e:
        logging.error(
            f"Error updating subscription and saving payment confirmation: {str(e)}"
        )
        return False


async def verify_payment_status(order_id: str):
    payment_service = FondyPaymentService()
    status = await payment_service.check_payment_status(order_id)
    if status is None:
        logging.warning(f"Payment {order_id} check timed out")
        return False
    if status["order_status"] == "approved":
        # Process successful payment
        await update_subscription_and_save_payment_confirmation(status)
        return True
    logging.info(f"Payment {order_id} finished with status: {status['order_status']}")
    return False


# RabbitMQ publisher


async def send_success_payment_details_to_queue(
    payment_dict: dict, queue: QueueName = QueueName.PAYMENT_EVENTS
):
    try:
        await rabbitmq.connect()
        await rabbitmq.publish(message=payment_dict, queue=queue)
    except Exception as e:
        logging.error(f"Failed to send item to RabbitMQ: {e}")
    finally:
        await rabbitmq.close()
        # Ensure the connection is closed
