from pathlib import Path
from typing import Optional, Any, Dict
from datetime import timedelta, datetime, UTC
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
            normalized_data = dict(
                payment_id=payment_response["payment_id"],
                order_id=payment_response["order_id"],
                order_status=payment_response["order_status"],
                currency=payment_response["currency"],
                amount=payment_response["amount"],  # Amount in cents, already converted
                card_type=payment_response["card_type"],
                masked_card=payment_response["masked_card"],
                payment_system=payment_response["payment_system"],
                response_status=payment_response["response_status"],
                tran_type=payment_response["tran_type"],
                order_time=payment_response["order_time"],
                additional_info=payment_response["additional_info"],
                provider="fondy",
            )
            return normalized_data
        except KeyError as e:
            logging.error(f"Missing key in payment response: {e}")
            return {}

    def verify_signature(self, order_id: str, received_signature: str) -> bool:
        # TODO: Implement signature verification logic - regenerate signature for received data and compare with received_signature
        calculated_signature = get_signature_from_cache(order_id)
        if not calculated_signature:
            return False
        if isinstance(calculated_signature, bytes):
            calculated_signature = calculated_signature.decode("utf-8")
        if isinstance(received_signature, bytes):
            received_signature = received_signature.decode("utf-8")
        return received_signature == calculated_signature


fondy_response_example = {
    "rrn": "413957824276",
    "masked_card": "444455XXXXXX6666",
    "sender_cell_phone": "",
    "sender_account": "",
    "currency": "USD",
    "fee": "",
    "reversal_amount": "0",
    "settlement_amount": "0",
    "actual_amount": "3000",
    "response_description": "",
    "sender_email": "teodorathome@yahoo.com",
    "order_status": "approved",
    "response_status": "success",
    "order_time": "24.08.2025 11:55:00",
    "actual_currency": "USD",
    "order_id": "2aab9e19-5ae7-4915-b0c7-6f3c62ad2310",
    "tran_type": "purchase",
    "eci": "7",
    "settlement_date": "",
    "payment_system": "card",
    "approval_code": "426504",
    "merchant_id": 1396424,
    "settlement_currency": "",
    "payment_id": 876195373,
    "card_bin": 444455,
    "response_code": "",
    "card_type": "VISA",
    "amount": "3000",
    "signature": "8374b7bd55c8f8306f65fe77a656f200d5f16cf5",
    "product_id": "",
    "merchant_data": "",
    "rectoken": "",
    "rectoken_lifetime": "",
    "verification_status": "",
    "parent_order_id": "",
    "additional_info": '{"capture_status": null, "capture_amount": null, "reservation_data": "{}", "transaction_id": 2121158122, "bank_response_code": null, "bank_response_description": null, "client_fee": 0.0, "settlement_fee": 0.0, "bank_name": null, "bank_country": null, "card_type": "VISA", "card_product": "empty_visa", "card_category": null, "timeend": "24.08.2025 11:55:14", "ipaddress_v4": "188.163.31.56", "payment_method": "card", "version_3ds": 2, "flow": "frictionless", "is_test": true}',
    "response_signature_string": '**********|3000|USD|{"capture_status": null, "capture_amount": null, "reservation_data": "{}", "transaction_id": 2121158122, "bank_response_code": null, "bank_response_description": null, "client_fee": 0.0, "settlement_fee": 0.0, "bank_name": null, "bank_country": null, "card_type": "VISA", "card_product": "empty_visa", "card_category": null, "timeend": "24.08.2025 11:55:14", "ipaddress_v4": "188.163.31.56", "payment_method": "card", "version_3ds": 2, "flow": "frictionless", "is_**********": true}|3000|426504|444455|VISA|USD|7|444455XXXXXX6666|1396424|2aab9e19-5ae7-4915-b0c7-6f3c62ad2310|approved|24.08.2025 11:55:00|876195373|card|success|0|413957824276|teodorathome@yahoo.com|0|purchase',
}
