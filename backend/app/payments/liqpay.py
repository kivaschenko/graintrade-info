from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime, UTC
import base64
import hashlib
import httpx
import logging
import os
import json
from dotenv import load_dotenv

from ..payments.base import BasePaymentProvider
from .payment_helpers import (
    save_signature_to_cache,
    get_signature_from_cache,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
LIQPAY_PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY")
LIQPAY_PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY")
BASE_URL = os.getenv("BASE_URL", "localhost:8000")
LIQPAY_CALLBACK_URL = f"{BASE_URL}/payments/confirm/liqpay"
ORDER_DESCRIPTION = "sub-{tarif_name}-{start_date}-{end_date}-{user_id}"


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# ----------------------
# LiqPay payment service class


class LiqPayPaymentService(BasePaymentProvider):
    API_URL = "https://www.liqpay.ua/api/3/checkout"
    _supportedActions = ["pay", "hold", "subscribe", "paydonate"]

    _button_translations = {"uk": "Сплатити", "en": "Pay"}

    _FORM_TEMPLATE = """
        <form method="POST" action="{action}" accept-charset="utf-8">
            <input type="hidden" name="data" value="{data}" />
            <input type="hidden" name="signature" value="{signature}" />
            <script type="text/javascript" src="https://static.liqpay.ua/libjs/sdk_button.js"></script>
            <sdk-button label="{label}" background="#77CC5D" onClick="submit()"></sdk-button>
        </form>
    """

    def __init__(
        self,
        public_key: str = LIQPAY_PUBLIC_KEY,  # type: ignore
        private_key: str = LIQPAY_PRIVATE_KEY,  # type: ignore
    ):
        self.public_key = public_key
        self.private_key = private_key

    def _generate_data(self, params: dict) -> str:
        """Generate base64-encoded data for LiqPay API"""
        json_str = json.dumps(params)
        return base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

    def _generate_signature(self, data: str) -> str:
        """Generate signature for LiqPay API"""
        sign_str = self.private_key + data + self.private_key
        sha1 = hashlib.sha1(sign_str.encode("utf-8")).digest()
        return base64.b64encode(sha1).decode("utf-8")

    async def process_payment(
        self,
        amount: float,
        order_id: str,
        order_desc: str,
        currency: str = "EUR",
        email: Optional[str] = None,
        server_callback_url: Optional[str] = LIQPAY_CALLBACK_URL,
        language: str = "uk",
    ) -> Dict[str, Any]:
        """Create payment for subscription using LiqPay"""
        params = {
            "version": 3,
            "public_key": self.public_key,
            "amount": amount,
            "currency": currency,
            "order_id": order_id,
            "description": order_desc,
            "action": "pay",
            "language": language,
        }
        if email:
            params["email"] = email
        if server_callback_url:
            params["server_url"] = server_callback_url

        data = self._generate_data(params)
        signature = self._generate_signature(data)
        save_signature_to_cache(order_id, signature)
        logging.info(f"LiqPay payment params: {params}")
        return {
            "status": "success",
            "liqpay_form": {
                "data": data,
                "signature": signature,
                "action": self.API_URL,
                "label": self._button_translations.get(language, "Pay"),
            },
            "message": "Successful payment attempt",
        }

    async def check_payment_status(self, order_id: str) -> Dict[str, Any]:
        """Check payment status using LiqPay API"""
        signature = get_signature_from_cache(order_id)
        if not signature:
            raise ValueError("Signature not found in cache for order_id: " + order_id)

        params = {
            "version": 3,
            "public_key": self.public_key,
            "order_id": order_id,
        }
        data = self._generate_data(params)
        generated_signature = self._generate_signature(data)
        if generated_signature != signature:
            raise ValueError("Invalid signature for order_id: " + order_id)

        async with httpx.AsyncClient() as client:
            r = await client.post(
                url=self.API_URL + "/status",
                data={"data": data, "signature": generated_signature},
            )
        if r.status_code != 200:
            raise Exception("Error from LiqPay API")
        response_data = r.json()
        logging.info(f"LiqPay status response: {response_data}")
        return response_data

    def normalize(self, payment_data: dict) -> dict:
        """Normalize LiqPay payment data to common format"""
        #  "create_date": "1715597977414"
        # Convert create_date from milliseconds to datetime string format
        try:
            order_time = datetime.fromtimestamp(
                int(payment_data["create_date"]) / 1000, tz=UTC
            ).strftime("%d.%m.%Y %H:%M:%S")
            print(f"Parsed order_time: {order_time}")
        except (ValueError, KeyError) as e:
            logging.error(f"Error parsing create_date: {str(e)}")
            order_time = datetime.now(tz=UTC).strftime("%d.%m.%Y %H:%M:%S")
        additional_info = payment_data.copy()
        normalized_data = dict(
            payment_id=payment_data.get("payment_id"),
            order_id=payment_data.get("order_id"),
            order_status=payment_data.get("status"),
            currency=payment_data.get("currency"),
            amount=int(payment_data["amount"] * 100),  # Convert to cents
            card_type=payment_data.get("sender_card_type"),
            masked_card=payment_data.get("sender_card_mask2"),
            payment_system=payment_data.get("paytype"),
            response_status=payment_data.get("status"),
            tran_type=payment_data.get("action"),
            order_time=order_time,
            additional_info=additional_info,
            provider="liqpay",
        )

        return normalized_data

    def verify_signature(self, order_id: str, received_signature: str) -> bool:
        """Verify the signature of the payment data"""
        # TODO: Implement signature verification logic - regenerate signature for received data and compare with received_signature
        signature = get_signature_from_cache(order_id)
        if not signature:
            logging.error(f"Signature not found in cache for order_id: {order_id}")
            return False
        return signature == received_signature


# ----------------------
# Webhook handler for LiqPay payment confirmation
# async def handle_liqpay_webhook(payment_data: dict):
#     try:
#         # Extract necessary fields from payment_data
#         order_id = payment_data.get("order_id")
#         if not order_id:
#             logging.error("Order ID is missing in the payment data")
#             return False

#         # Verify payment signature
#         liqpay_service = LiqPayPaymentService(
#             public_key=LIQPAY_PUBLIC_KEY,  # type: ignore
#             private_key=LIQPAY_PRIVATE_KEY,  # type: ignore
#         )
#         if not await liqpay_service.verify_payment(payment_data):
#             logging.error("Invalid payment signature")
#             return False

#         # Save payment confirmation and update subscription status
#         await update_subscription_and_save_payment_confirmation(payment_data)

#         # Send success details to RabbitMQ queue
#         await send_success_payment_details_to_queue(payment_data)

#         return True
#     except Exception as e:
#         logging.error(f"Error handling LiqPay webhook: {str(e)}")
#         return False
#     finally:
#         logging.info("LiqPay webhook handler completed")
#         return True
#     return False

payment_data_example = {
    "payment_id": 2699352001,
    "action": "pay",
    "status": "success",
    "version": 3,
    "type": "buy",
    "paytype": "card",
    "public_key": "sandbox_i73022413705",
    "acq_id": 414963,
    "order_id": "560c6ed2-cf3e-4dcb-b2f2-3b6209d8b788",
    "liqpay_order_id": "K3O5CGZE1756027569147559",
    "description": "sub-Premium-2025-08-24-2025-09-24-5",
    "sender_first_name": "Оксана",
    "sender_last_name": "Іващенко",
    "sender_card_mask2": "424242*42",
    "sender_card_bank": "Test",
    "sender_card_type": "visa",
    "sender_card_country": 804,
    "ip": "188.163.31.56",
    "amount": 30.0,
    "currency": "USD",
    "sender_commission": 0.0,
    "receiver_commission": 0.45,
    "agent_commission": 0.0,
    "amount_debit": 1250.0,
    "amount_credit": 1250.0,
    "commission_debit": 0.0,
    "commission_credit": 18.75,
    "currency_debit": "UAH",
    "currency_credit": "UAH",
    "sender_bonus": 0.0,
    "amount_bonus": 0.0,
    "mpi_eci": "7",
    "is_3ds": False,
    "language": "uk",
    "create_date": 1756027569150,
    "end_date": 1756027569317,
    "transaction_id": 2699352001,
}
