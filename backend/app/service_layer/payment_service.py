import json
import hashlib
import asyncio
import httpx
import logging
import uuid
from typing import Optional, Any, Dict
from datetime import date, timedelta

import redis

from ..models import subscription_model, tarif_model, user_model
from ..schemas import (
    SubscriptionInDB,
    SubscriptionInResponse,
    TarifInResponse,
    UserInResponse,
)
from ..database import redis_db

FONDY_MERCHANT_ID = "1555037"
FONDY_MERCHANT_KEY = "test"
# FONDY_MERCHANT_KEY = "z0LvpvmJZOXo14ezf3oL43Fs5p18XNbQ"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_service")


ORDER_DESCRIPTION = """
    Subscription_{tarif_name}_{start_date}_{end_date}_{user_id}_{subscription_id}.
    Payment for using web site: graintrade.info according tariff plan: {tarif_name}.
    User: {full_name}.
    """

# -------------------
# Helpers


def make_start_end_dates_for_monthly_case() -> tuple[date, date]:
    start_date = date.today()
    end_date = start_date + timedelta(days=31)
    return start_date, end_date


class FondyPaymentService:
    API_URL = "https://pay.fondy.eu/api/checkout/url/"

    def __init__(
        self,
        merchant_id: str = FONDY_MERCHANT_ID,
        merchant_key: str = FONDY_MERCHANT_KEY,
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
        # Send request to Fondy API
        logger.info(f"Sending payment request to Fondy: {params}")
        async with httpx.AsyncClient() as client:
            r = await client.post(url=self.API_URL, json={"request": params})
        if r.status_code != 200:
            logger.error(f"Error from Fondy API: {r.text}")
            raise Exception("Error from Fondy API")
        logger.info(f"Response from Fondy API: {r.json()}")
        return r.json()

    def _extract_checkout_url(
        self, r: Dict[str, Dict[str, str]]
    ) -> tuple[str | bool, str | bool]:
        checkout_url = False
        payment_id = False

        # {'response': {
        #   'checkout_url': 'https://pay.fondy.eu/merchants/5ad6b888f4becb0c33d543d54e57d86c/default/index.html?token=9e16b2695d48e06519c24aac4bb5f3bed4800439',
        #   'payment_id': '862387020',
        # 'response_status': 'success'
        # }}
        response_body: dict = r.get("response", {})
        response_status = response_body.get("response_status", " ")
        if response_status == "success":
            payment_id = response_body.get("payment_id", " ")
            logger.info(f"Payment ID: {payment_id}")
            checkout_url = response_body.get("checkout_url", " ")
            logger.info(f"Checkout URL: {checkout_url}")
        elif response_status == "failure":
            error_code = response_body.get("error_code", " ")
            error_message = response_body.get("error_message", " ")
            raise ValueError(
                f"Invalid response from payment service:  {error_code} - {error_message}"
            )
        return checkout_url, payment_id

    def _create_order_description(
        self,
        tarif_name: str,
        start_date: date,
        end_date: date,
        user_id: int,
        subscription_id: int,
        full_name: str | None,
    ) -> str:
        """Create description string for payment service"""
        return ORDER_DESCRIPTION.format(
            tarif_name=tarif_name,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            subscription_id=subscription_id,
            full_name=full_name,
        )

    async def get_checkout_url_from_payment_api(
        self, user_id: int, tarif_id: int
    ) -> str | bool:
        """Send all needing payment data to Fondy API and recieve the checkout URL to pass to frondend."""
        try:
            # Prepare start and end dates for current Subscription
            start_date, end_date = make_start_end_dates_for_monthly_case()

            # Create a new subscription record in DB with status 'inactive'
            subscribtion_to_db = SubscriptionInDB(
                user_id=user_id,
                tarif_id=tarif_id,
                start_date=start_date,
                end_date=end_date,
                status="inactive",
            )
            subscription: SubscriptionInResponse = await subscription_model.create(
                subscribtion_to_db
            )

            # Get needing Tariff Plan
            current_tarif: TarifInResponse = await tarif_model.get_by_id(
                tarif_id=tarif_id
            )

            # Get info about current User
            current_user: UserInResponse = await user_model.get_by_id(user_id=user_id)

            # Create order description
            order_desc = self._create_order_description(
                tarif_name=current_tarif.name,
                start_date=start_date,
                end_date=end_date,
                user_id=user_id,
                subscription_id=subscription.id,
                full_name=current_user.full_name,
            )

            # Create payment data for payload
            payment_data, signature = await self.create_subscription_payment(
                amount=current_tarif.price,
                order_id=subscription.order_id,
                order_desc=order_desc,
                currency=current_tarif.currency,
                email=current_user.email,
                # server_callback_url="my-server-callback-url",
            )
            logger.info(f"Payment created: {payment_data}")

            # Send request to Fondy API
            r = await self.send_request_to_fondy_api(payment_data)

            # Get checkout URL and payment_id
            checkout_url, payment_id = self._extract_checkout_url(r)
            assert isinstance(checkout_url, str)
            assert isinstance(payment_id, str)
            logger.info(f"Got checkout URL: {checkout_url}")
            # Update subscriptions table table in DB and add payment_id value
            await subscription_model.update_payment_id(
                payment_id=payment_id, id=subscription.id
            )
            # Save signature in cache by payment_id name
            save_signature_to_cache(payment_id=payment_id, signature=signature)
            return checkout_url

        except Exception as e:
            logger.error(f"Error testing payment service: {str(e)}")
            raise e
        return False


def save_signature_to_cache(payment_id: str, signature: str):
    """Save signature in Redis cache by payment_id name"""
    # Connect to Redis
    r = redis.Redis().from_pool(redis_db.pool)
    # Save in Redis signature for 10 minutes
    r.set(name=payment_id, value=signature, ex=600)
    logging.info("Saved signature for payment_id: %", payment_id)
    r.close()


def get_signature_from_cache(payment_id: str) -> str | None:
    """Get signature from Redis cache by payment_id name"""
    # Connect to Redis
    r = redis.Redis().from_pool(redis_db.pool)
    # Get signature from Redis
    signature = r.get(name=payment_id)
    r.close()
    # Check if signature is found
    if signature:
        logging.info("Got signature % for payment_id: %", signature, payment_id)
        return signature
    else:
        logging.error("Signature not found for payment_id: %", payment_id)
        return None


def verify_payment(payment_id: str, received_signature: str) -> bool:
    """Verify payment callback from Fondy"""
    calculated_signature = get_signature_from_cache(payment_id)
    if not calculated_signature:
        logging.error("Signature not found in cache")
        return False
    # Compare received signature with calculated signature
    if isinstance(calculated_signature, bytes):
        calculated_signature = calculated_signature.decode("utf-8")
    if isinstance(received_signature, bytes):
        received_signature = received_signature.decode("utf-8")
    logging.info(
        f"Comparing signatures: received: {received_signature}, calculated: {calculated_signature}"
    )
    # Compare signatures
    return received_signature == calculated_signature


# -------------------
# Handlers for Fondy API


# ----------------------------
# Test the FondyPaymentService


async def test_payment_service():
    try:
        payment_service = FondyPaymentService(
            merchant_id="1396424", merchant_key="test"
        )

        order_id = str(uuid.uuid4())
        # Create test payment
        payment_data, signature = await payment_service.create_subscription_payment(
            amount=5.0,
            currency="EUR",
            order_id=order_id,
            order_desc="sub-112358-1325",
            email="kivaschenko@protonmail.com",
        )
        logger.info(f"Payment created: {payment_data} with signature: {signature}")

        r = await payment_service.send_request_to_fondy_api(payment_data)
        checkout_url = payment_service._extract_checkout_url(r)
        print("Result:", checkout_url)

    except Exception as e:
        logger.error(f"Error testing payment service: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(test_payment_service())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
