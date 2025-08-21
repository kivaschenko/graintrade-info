from typing import Dict, Any
import logging
import uuid

from ..models import subscription_model, payment_model
from ..schemas import (
    SubscriptionInDB,
    SubscriptionStatus,
    SubscriptionInResponse,
)
from ..payments import (
    BasePaymentProvider,
    FondyPaymentService,
    LiqPayPaymentService,
    create_order_description,
    make_start_end_dates_for_monthly_case,
)
from ..rabbit_mq import rabbitmq, QueueName


logging.basicConfig(level=logging.INFO)


PAYMENT_PROVIDERS = {
    "fondy": FondyPaymentService,
    "liqpay": LiqPayPaymentService,
    # Add other payment providers here as needed
}

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


# ---------------------------------
# Handlers for Any payment provider


async def payment_for_subscription_handler(
    user_id: int,
    tarif_id: int,
    tarif_name: str,
    amount: float,
    currency: str,
    email: str,
    payment_provider_name: str = "fondy",
) -> str | None:
    """Handle payment for subscription using specified payment provider"""
    payment_service = PAYMENT_PROVIDERS.get(payment_provider_name)
    if not payment_service:
        logging.error(f"Payment provider {payment_provider_name} not found")
        return None

    # Initialize the payment service
    payment_service = payment_service()

    try:
        order_id: str = str(uuid.uuid4())
        start_date, end_date = make_start_end_dates_for_monthly_case()
        subscription: SubscriptionInResponse = await subscription_model.create(
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
        logging.info(f"Created a new subscription: {subscription}")

        # Create order description
        order_desc = create_order_description(tarif_name, start_date, end_date, user_id)
        # Process payment
        logging.info(f"Processing payment for order_id: {order_id}")
        checkout_url = await payment_service.process_payment(
            amount, order_id, order_desc, currency, email
        )
        return checkout_url
    except Exception as e:
        logging.error(f"Error in payment_for_subscription_handler: {str(e)}")
        return None


async def update_subscription_and_save_payment_confirmation(
    payment_response: Dict[str, Any],
    payment_provider_name: str = "fondy",
):
    """Update subscription status and save payment confirmation"""
    payment_service = PAYMENT_PROVIDERS.get(payment_provider_name)
    if not payment_service:
        logging.error(f"Payment provider {payment_provider_name} not found")
        return False

    # Initialize the payment service
    payment_service = payment_service()

    try:
        order_id = payment_response.get("order_id")
        if not order_id:
            logging.error("Order ID is missing in the payment response")
            return False

        # Verify the signature
        if not payment_service.verify_signature(
            data=payment_response, signature=payment_response.get("signature", "")
        ):
            logging.error("Invalid payment signature")
            return False

    except KeyError as e:
        logging.error(f"Missing key in payment response: {e}")
        return False

    # Save payment confirmation and update subscription status
    try:
        payment_data = payment_service.normalize(payment_response)
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


async def verify_payment_status(
    order_id: str, payment_provider_name: str = "fondy"
) -> bool:
    """Verify payment status for a given order ID"""
    payment_service = PAYMENT_PROVIDERS.get(payment_provider_name)
    if not payment_service:
        logging.error(f"Payment provider {payment_provider_name} not found")
        return False

    # Initialize the payment service
    payment_service = payment_service()

    try:
        status = await payment_service.check_payment_status(order_id)
        if not status:
            logging.warning(f"Payment status for order_id {order_id} is None")
            return False
    except Exception as e:
        logging.error(f"Error checking payment status: {str(e)}")
        return False
    if payment_provider_name == "fondy":
        if status["order_status"] == "approved":
            # Process successful payment
            await update_subscription_and_save_payment_confirmation(
                status, payment_provider_name
            )
            return True
    elif payment_provider_name == "liqpay":
        if status["status"] in ["success", "subscribed"]:
            # Process successful payment
            await update_subscription_and_save_payment_confirmation(
                status, payment_provider_name
            )
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
        logging.info("RabbitMQ connection closed after publishing payment details")
        return True
    return False


if __name__ == "__main__":
    # Example usage
    pass
