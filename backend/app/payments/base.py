from abc import ABC, abstractmethod
from typing import Dict, Any


class BasePaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    """

    @abstractmethod
    async def process_payment(
        self, amount: float, order_id: str, currency: str, **kwargs
    ) -> str:
        """
        Returns the checkout URL for the payment.
        :param amount: The amount to be paid.
        :param order_id: The ID of the order for which the payment is being processed.
        :param currency: The currency of the payment.
        :param kwargs: Additional parameters specific to the payment provider.
        :return: A dict containing the checkout URL or data for LiqPay form.
        """
        pass

    @abstractmethod
    async def check_payment_status(self, order_id: str) -> Dict[str, Any]:
        """
        Retrieves the status of a payment using the transaction ID.
        :param order_id: The ID of the inside transaction to check.
        :return: A dictionary containing the payment status.
        """
        pass

    @abstractmethod
    def normalize(self, payment_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizes the payment response to a standard format.
        :param payment_response: The raw payment response from the provider.
        :return: A dictionary containing the normalized payment data.
        """
        pass

    @abstractmethod
    def verify_signature(self, data: Dict[str, Any], signature: str) -> bool:
        """
        Verifies the signature of the payment response.
        :param data: The payment response data.
        :param signature: The signature to verify.
        :return: True if the signature is valid, False otherwise.
        """
        pass
