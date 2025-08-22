from pathlib import Path
from typing import Optional, Any, Dict
from datetime import timedelta, datetime
import asyncio
import hashlib
import httpx
import logging
import os
from dotenv import load_dotenv

from ..payments.base import BasePaymentProvider
from .payment_helpers import (
    save_signature_to_cache,
    get_signature_from_cache,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
FONDY_MERCHANT_ID = os.getenv("FONDY_MERCHANT_ID")
FONDY_MERCHANT_KEY = os.getenv("FONDY_MERCHANT_KEY")
BASE_URL = os.getenv("BASE_URL", "localhost:8000")
FONDY_CALLBACK_URL = f"{BASE_URL}/payments/confirm"
ORDER_DESCRIPTION = "sub-{tarif_name}-{start_date}-{end_date}-{user_id}"


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# -------------------
# Fondy payment service class
class FondyPaymentService(BasePaymentProvider):
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

    async def process_payment(
        self,
        amount: float,  # Value just from DB tarifs table
        order_id: str,
        order_desc: str,
        currency: str = "EUR",
        email: Optional[str] = None,
        server_callback_url: Optional[str] = FONDY_CALLBACK_URL,
    ) -> Dict[str, Any]:
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
        # Save signature to cache for later verification
        save_signature_to_cache(order_id, signature)
        # Send request to Fondy API
        r = await self._send_request(params)
        if r.get("response", {}).get("response_status") != "success":
            raise ValueError("Error from Fondy API: " + str(r))

        # Extract checkout URL and payment ID
        checkout_url, payment_id = await self._get_checkout_url(r)
        logging.info(f"Checkout URL: {checkout_url}, Payment ID: {payment_id}")

        return {
            "status": "success",
            "checkout_url": checkout_url,
            "message": "Successful payment attemp",
        }

    async def _send_request(self, params: Dict[str, Any]):
        async with httpx.AsyncClient() as client:
            r = await client.post(url=self.API_URL, json={"request": params})
        if r.status_code != 200:
            raise Exception("Error from Fondy API")
        return r.json()

    async def _get_checkout_url(self, r: Dict[str, Dict[str, str]]) -> tuple[str, str]:
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

    def normalize(self, payment_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize the payment response to a standard format.
        :param payment_response: The raw payment response from the provider.
        :return: A dictionary containing the normalized payment data.
        """
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
            return payment_data
        except KeyError as e:
            logging.error(f"Missing key in payment response: {e}")
            return {}

    def verify_signature(self, order_id: str, received_signature: str) -> bool:
        calculated_signature = get_signature_from_cache(order_id)
        if not calculated_signature:
            return False
        if isinstance(calculated_signature, bytes):
            calculated_signature = calculated_signature.decode("utf-8")
        if isinstance(received_signature, bytes):
            received_signature = received_signature.decode("utf-8")
        return received_signature == calculated_signature
