import hashlib
import asyncio
import requests
import logging
import uuid
from typing import Optional
from datetime import datetime

FONDY_MERCHANT_ID = "1555037"
FONDY_MERCHANT_KEY = "z0LvpvmJZOXo14ezf3oL43Fs5p18XNbQ"


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        amount: float,
        currency: str,
        order_id: str,
        subscription_id: str,
        email: Optional[str] = None,
    ) -> dict:
        """Create recurring payment for subscription"""
        params = {
            "order_id": order_id,
            "merchant_id": self.merchant_id,
            "order_desc": f"Subscription {subscription_id}",
            "amount": str(int(amount * 100)),  # Convert to cents
            "currency": currency,
            # "response_url": "http://localhost:8000/payment/callback",  # Replace with your callback URL
        }

        if email:
            params["sender_email"] = email

        params["signature"] = self._generate_signature(params)

        # Send request to Fondy API
        logger.info(f"Sending payment request to Fondy: {params}")
        response = requests.post(self.API_URL, json={"request": params})
        if response.status_code != 200:
            logger.error(f"Error from Fondy API: {response.text}")
            raise Exception("Error from Fondy API")
        logger.info(f"Response from Fondy API: {response.json()}")
        return response.json()

    def verify_payment(self, payment_data: dict) -> bool:
        """Verify payment callback from Fondy"""
        received_signature = payment_data.pop("signature", "")
        calculated_signature = self._generate_signature(payment_data)
        return received_signature == calculated_signature


async def test_payment_service():
    try:
        payment_service = FondyPaymentService(
            merchant_id="1396424", merchant_key="test"
        )

        order_id = str(uuid.uuid4())
        # Create test payment
        payment_data = await payment_service.create_subscription_payment(
            amount=10.0,
            currency="EUR",
            order_id=order_id,
            subscription_id="sub-112358-1325",
            email="kivaschenko@protonmail.com",
        )
        logger.info(f"Payment created: {payment_data}")

        if "response" not in payment_data and payment_data.get("response", {}).get(
            "error_code"
        ):
            raise ValueError(
                f"Invalid response from payment service: {payment_data['response']['error_message']}"
            )
        if payment_data.get("response", {}).get("checkout_url"):
            logger.info(f"Checkout URL: {payment_data['response']['checkout_url']}")

        # Verify payment
        is_valid = payment_service.verify_payment(payment_data)
        logger.info(f"Payment valid: {is_valid}")

        return payment_data, is_valid

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
