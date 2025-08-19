from typing import Any, Dict, Optional


class PaymentGateway:
    async def create_subscription_payment(
        self,
        amount: float,
        order_id: str,
        order_desc: str,
        currency: str = "UAH",
        email: Optional[str] = None,
        server_callback_url: Optional[str] = None,
    ) -> tuple[Dict[str, Any], str]:
        raise NotImplementedError

    async def send_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    async def check_payment_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
