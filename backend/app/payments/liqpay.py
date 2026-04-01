from pathlib import Path
from typing import Optional, Any, Dict
from datetime import datetime, UTC
import base64
import hashlib
import httpx
import os
import json
from urllib.parse import urljoin
from dotenv import load_dotenv

from ..payments.base import BasePaymentProvider
from .payment_helpers import (
    save_signature_to_cache,
)
from ..logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")
LIQPAY_PUBLIC_KEY = os.getenv("LIQPAY_PUBLIC_KEY")
LIQPAY_PRIVATE_KEY = os.getenv("LIQPAY_PRIVATE_KEY")
BASE_URL = os.getenv("BASE_URL", "")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "")
LIQPAY_SERVER_CALLBACK_URL = os.getenv("LIQPAY_SERVER_CALLBACK_URL", "")


def _join_url(base: str, path: str) -> str | None:
    if not base:
        return None
    if not base.startswith(("http://", "https://")):
        logger.warning("Skipping malformed base URL (missing scheme): %s", base)
        return None
    return urljoin(base.rstrip("/") + "/", path.lstrip("/"))


def _resolve_callback_url() -> str | None:
    # If explicit callback URL is provided, use it as-is.
    explicit = LIQPAY_SERVER_CALLBACK_URL.strip()
    if explicit:
        if not explicit.startswith(("http://", "https://")):
            logger.warning(
                "Skipping malformed LIQPAY_SERVER_CALLBACK_URL (missing scheme): %s",
                explicit,
            )
            return None
        return explicit.rstrip("/")

    # Fallback to API base URL + callback path.
    return _join_url(BASE_URL, "/payments/confirm/liqpay")


LIQPAY_CALLBACK_URL = _resolve_callback_url()
RESULT_URL = _join_url(FRONTEND_BASE_URL or BASE_URL, "/tariffs")
ORDER_DESCRIPTION = "sub-{tarif_name}-{start_date}-{end_date}-{user_id}"

# ----------------------
# LiqPay payment service class


class LiqPayPaymentService(BasePaymentProvider):
    # API_URL is used for the browser-based checkout flow (form submissions / redirects).
    # API_REQUEST_URL is used for server-to-server LiqPay API calls (e.g., status checks,
    # subscription management, and other backend operations) and must not be confused
    # with the checkout endpoint above.
    API_URL = "https://www.liqpay.ua/api/3/checkout"
    API_REQUEST_URL = "https://www.liqpay.ua/api/request"
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
        if not public_key or not private_key:
            raise ValueError("LiqPay keys are not configured")
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
        currency: str = "USD",
        email: Optional[str] = None,
        server_callback_url: Optional[str] = LIQPAY_CALLBACK_URL,
        result_url: Optional[str] = None,
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
        else:
            raise ValueError(
                "LiqPay server callback URL is not configured. "
                "Set LIQPAY_SERVER_CALLBACK_URL or BASE_URL (for security, BASE_URL should use the https scheme)."
            )
        if result_url:
            params["result_url"] = result_url
        elif RESULT_URL:
            params["result_url"] = RESULT_URL

        logger.info(
            "Preparing LiqPay payment: order_id=%s, amount=%.2f %s, server_callback_url=%s, result_url=%s",
            order_id,
            amount,
            currency,
            params.get("server_url"),
            params.get("result_url"),
        )

        data = self._generate_data(params)
        signature = self._generate_signature(data)
        signature_saved = save_signature_to_cache(order_id, signature)
        if not signature_saved:
            logger.warning(
                "Continuing LiqPay checkout without cached signature for order_id: %s",
                order_id,
            )
        logger.info(
            "LiqPay payment params prepared: order_id=%s, server_url=%s, result_url=%s",
            order_id,
            params.get("server_url"),
            params.get("result_url"),
        )
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
        """Check payment status using LiqPay API by order_id."""
        params = {
            "action": "status",
            "version": 3,
            "public_key": self.public_key,
            "order_id": order_id,
        }
        data = self._generate_data(params)
        generated_signature = self._generate_signature(data)

        async with httpx.AsyncClient() as client:
            r = await client.post(
                url=self.API_REQUEST_URL,
                data={"data": data, "signature": generated_signature},
            )
        if r.status_code != 200:
            raise Exception(f"Error from LiqPay API: HTTP {r.status_code}")
        response_data = r.json()
        logger.info(
            "LiqPay status response for order_id=%s: status=%s, raw=%s",
            order_id,
            response_data.get("status"),
            response_data,
        )
        return response_data

    def normalize(self, payment_data: dict) -> dict:
        """Normalize LiqPay payment data to common format"""
        #  "create_date": "1715597977414"
        # Convert create_date from milliseconds to datetime string format
        try:
            order_time = datetime.fromtimestamp(
                int(payment_data["create_date"]) / 1000, tz=UTC
            ).strftime("%d.%m.%Y %H:%M:%S")
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing create_date: {str(e)}")
            order_time = datetime.now(tz=UTC).strftime("%d.%m.%Y %H:%M:%S")

        # LiqPay live callbacks may omit card-related fields depending on payment method.
        payment_id = payment_data.get("payment_id") or payment_data.get("transaction_id")
        if payment_id is None:
            # Keep deterministic fallback so persistence does not fail.
            payment_id = 0

        try:
            amount_value = float(payment_data.get("amount", 0))
        except (TypeError, ValueError):
            amount_value = 0.0

        additional_info = payment_data.copy()
        normalized_data = dict(
            payment_id=payment_id,
            order_id=payment_data.get("order_id"),
            order_status=payment_data.get("status") or "unknown",
            currency=payment_data.get("currency") or "UAH",
            amount=int(amount_value * 100),  # Convert to cents
            card_type=payment_data.get("sender_card_type") or "unknown",
            masked_card=payment_data.get("sender_card_mask2") or "",
            payment_system=payment_data.get("paytype") or payment_data.get("type") or "unknown",
            response_status=payment_data.get("status") or "unknown",
            tran_type=payment_data.get("action") or "pay",
            order_time=order_time,
            additional_info=additional_info,
            provider="liqpay",
        )

        return normalized_data

    def verify_signature(self, data: Dict[str, Any], signature: str) -> bool:
        """Verify LiqPay signature for a provided payload."""
        try:
            encoded_data = self._generate_data(data)
            expected_signature = self._generate_signature(encoded_data)
            return expected_signature == signature
        except Exception as e:
            logger.error(f"Failed to verify LiqPay signature: {e}")
            return False


# payment_data_example = {
#     "payment_id": 2699352001,
#     "action": "pay",
#     "status": "success",
#     "version": 3,
#     "type": "buy",
#     "paytype": "card",
#     "public_key": "sandbox_i73022413705",
#     "acq_id": 414963,
#     "order_id": "560c6ed2-cf3e-4dcb-b2f2-3b6209d8b788",
#     "liqpay_order_id": "K3O5CGZE1756027569147559",
#     "description": "sub-Premium-2025-08-24-2025-09-24-5",
#     "sender_first_name": "Оксана",
#     "sender_last_name": "Іващенко",
#     "sender_card_mask2": "424242*42",
#     "sender_card_bank": "Test",
#     "sender_card_type": "visa",
#     "sender_card_country": 804,
#     "ip": "188.163.31.56",
#     "amount": 30.0,
#     "currency": "USD",
#     "sender_commission": 0.0,
#     "receiver_commission": 0.45,
#     "agent_commission": 0.0,
#     "amount_debit": 1250.0,
#     "amount_credit": 1250.0,
#     "commission_debit": 0.0,
#     "commission_credit": 18.75,
#     "currency_debit": "UAH",
#     "currency_credit": "UAH",
#     "sender_bonus": 0.0,
#     "amount_bonus": 0.0,
#     "mpi_eci": "7",
#     "is_3ds": False,
#     "language": "uk",
#     "create_date": 1756027569150,
#     "end_date": 1756027569317,
#     "transaction_id": 2699352001,
# }
