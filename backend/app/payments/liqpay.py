from pathlib import Path
from typing import Optional, Any, Dict
from datetime import timedelta, datetime
import base64
import asyncio
import hashlib
import httpx
import logging
import os
import json
from dotenv import load_dotenv

from ..payments.base import BasePaymentProvider
from .payment_helpers import (
    create_order_description,
    make_start_end_dates_for_monthly_case,
    save_signature_to_cache,
    get_signature_from_cache,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
LIQPAY_PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY")
LIQPAY_PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY")
BASE_URL = os.getenv("BASE_URL", "localhost:8000")
CALLBACK_URL = f"{BASE_URL}/payments/confirm"
ORDER_DESCRIPTION = "sub-{tarif_name}-{start_date}-{end_date}-{user_id}"


logging.basicConfig(level=logging.INFO)

# ----------------------
# LiqPay payment service class


class LiqPayPaymentService:
    API_URL = "https://www.liqpay.ua/api/3/checkout"

    def __init__(
        self,
        public_key: str = LIQPAY_PUBLIC_KEY,  # type: ignore
        private_key: str = LIQPAY_PRIVATE_KEY,  # type: ignore
    ):
        self.public_key = public_key
        self.private_key = private_key

    def _generate_signature(self, data: dict) -> str:
        """Generate signature for LiqPay API"""
        data_str = f"{self.private_key}{data}{self.private_key}"
        return hashlib.sha1(data_str.encode("utf-8")).hexdigest()

    async def create_subscription_payment(
        self,
        amount: float,
        order_id: str,
        order_desc: str,
        currency: str = "USD",
        email: Optional[str] = None,
        server_callback_url: Optional[str] = None,
    ) -> tuple[Dict[str, Any], str]:
        """Create payment for subscription using LiqPay"""
        params = {
            "version": 3,
            "public_key": self.public_key,
            "amount": amount,
            "currency": currency,
            "order_id": order_id,
            "description": order_desc,
        }
        if email:
            params["email"] = email
        if server_callback_url:
            params["server_url"] = server_callback_url

        # Generate signature

        data["signature"] = self._generate_signature(data)
        async with httpx.AsyncClient() as client:
            response = await client.post(self.API_URL, json=data)
            response.raise_for_status()
            return response.json()

    async def verify_payment(self, payment_data: dict) -> bool:
        """Verify payment signature"""
        received_signature = payment_data.pop("signature", None)
        if not received_signature:
            return False
        calculated_signature = self._generate_signature(payment_data)
        return received_signature == calculated_signature


# ----------------------
# Webhook handler for LiqPay payment confirmation
async def handle_liqpay_webhook(payment_data: dict):
    try:
        # Extract necessary fields from payment_data
        order_id = payment_data.get("order_id")
        if not order_id:
            logging.error("Order ID is missing in the payment data")
            return False

        # Verify payment signature
        liqpay_service = LiqPayPaymentService(
            public_key=LIQPAY_PUBLIC_KEY,  # type: ignore
            private_key=LIQPAY_PRIVATE_KEY,  # type: ignore
        )
        if not await liqpay_service.verify_payment(payment_data):
            logging.error("Invalid payment signature")
            return False

        # Save payment confirmation and update subscription status
        await update_subscription_and_save_payment_confirmation(payment_data)

        # Send success details to RabbitMQ queue
        await send_success_payment_details_to_queue(payment_data)

        return True
    except Exception as e:
        logging.error(f"Error handling LiqPay webhook: {str(e)}")
        return False
    finally:
        logging.info("LiqPay webhook handler completed")
        return True
    return False
