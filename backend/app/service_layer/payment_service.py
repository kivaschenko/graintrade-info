from typing import Dict, Any
import uuid

from ..models import subscription_model, payment_model
from ..schemas import (
    SubscriptionInDB,
    SubscriptionStatus,
    SubscriptionInResponse,
)
from ..payments import (
    LiqPayPaymentService,
    make_start_end_dates_for_monthly_case,
)
from ..rabbit_mq import rabbitmq, QueueName
from ..logger import logger


PAYMENT_PROVIDERS = {
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
        logger.info(f"Created a new Free subscription: {subscription}")
        await subscription_model.update_status_by_order_id(
            SubscriptionStatus.ACTIVE, order_id
        )
        logger.info(f"Updated status of subscription: {subscription}")
        if not subscription:
            raise ValueError("Failed to create subscription in the database")
        return True
    except Exception as e:
        logger.error(f"Error was during create free subscription: {e}")
        return False


# ---------------------------------
# Handlers for Any payment provider


async def payment_for_subscription_handler(
    user_id: int,
    tarif_id: int,
    amount: float,
    currency: str,
    email: str,
    payment_provider_name: str,
    order_desc: str = "",
    language: str = "en",
) -> Dict[str, Any] | None:
    """Handle payment for subscription using specified payment provider"""
    payment_service = PAYMENT_PROVIDERS.get(payment_provider_name)
    if not payment_service:
        logger.error(f"Payment provider {payment_provider_name} not found")
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
                provider=payment_provider_name,
            )
        )
        if not subscription:
            raise ValueError("Failed to create subscription in the database")
        logger.info(f"Created a new subscription: {subscription}")

        # Process payment
        logger.info(f"Processing payment for order_id: {order_id}")
        checkout_result: Dict[str, Any] = await payment_service.process_payment(
            amount, order_id, order_desc, currency, email, language=language
        )
        # Avoid mutating the dict returned by the payment service
        result_with_order: Dict[str, Any] = dict(checkout_result)
        result_with_order["order_id"] = order_id
        return result_with_order
    except Exception as e:
        logger.exception(f"Error in payment_for_subscription_handler: {str(e)}")
        return None


async def update_subscription_and_save_payment_confirmation(
    payment_response: Dict[str, Any],
    payment_provider_name: str = "liqpay",
):
    """Update subscription status and save payment confirmation"""
    payment_service = PAYMENT_PROVIDERS.get(payment_provider_name)
    if not payment_service:
        logger.error(f"Payment provider {payment_provider_name} not found")
        return False

    # Initialize the payment service
    payment_service = payment_service()

    try:
        order_id = payment_response.get("order_id")
        if not order_id:
            logger.error("Order ID is missing in the payment response")
            return False

        # # Verify the signature
        # if not payment_service.verify_signature(
        #     payment_response.get("order_id", ""), payment_response.get("signature", "")
        # ):
        #     logger.error("Invalid payment signature")
        #     return False

    except KeyError as e:
        logger.error(f"Missing key in payment response: {e}")
        return False

    # Save payment confirmation and update subscription status
    try:
        order_id = payment_response.get("order_id")
        existing_payment = await payment_model.get_by_order_id(order_id)
        existing_subscription = await subscription_model.get_by_order_id(order_id)
        if (
            existing_payment is not None
            and existing_subscription is not None
            and existing_subscription.status == SubscriptionStatus.ACTIVE
        ):
            logger.info(
                "Payment confirmation for order_id %s already processed; skipping duplicate update",
                order_id,
            )
            return True

        logger.info(f"Normalizing payment data for order_id: {order_id}")
        payment_data = payment_service.normalize(payment_response)
        logger.info(f"Creating payment record for order_id: {order_id}")
        payment_record: Dict[str, Any] = await payment_model.create(payment_data)
        logger.info(f"Payment record created, updating subscription for order_id: {order_id}")
        await subscription_model.update_status_by_order_id(
            SubscriptionStatus.ACTIVE, order_id, payment_record
        )
        logger.info(f"Subscription activated for order_id: {order_id}")
        return True
    except Exception as e:
        logger.exception(
            f"Error updating subscription and saving payment confirmation for order_id {payment_response.get('order_id')}: {str(e)}"
        )
        return False


async def verify_payment_status(
    order_id: str, payment_provider_name: str = "liqpay"
) -> bool:
    """Verify payment status for a given order ID"""
    payment_service = PAYMENT_PROVIDERS.get(payment_provider_name)
    if not payment_service:
        logger.error(f"Payment provider {payment_provider_name} not found")
        return False

    # Initialize the payment service
    payment_service = payment_service()

    try:
        status = await payment_service.check_payment_status(order_id)
        if not status:
            logger.warning(f"Payment status for order_id {order_id} is None")
            return False
    except Exception as e:
        logger.error(f"Error checking payment status: {str(e)}")
        return False

    provider_status = status.get("status")
    if payment_provider_name == "liqpay" and provider_status in ["success", "subscribed"]:
        # Process successful payment
        updated = await update_subscription_and_save_payment_confirmation(
            status, payment_provider_name
        )
        return bool(updated)

    logger.info(
        "Payment %s finished with provider status: %s",
        order_id,
        provider_status,
    )
    return False


# ----------------------------
# RabbitMQ publisher


async def send_success_payment_details_to_queue(
    payment_dict: dict, queue: QueueName = QueueName.PAYMENT_EVENTS
):
    try:
        await rabbitmq.connect()
        await rabbitmq.publish(message=payment_dict, queue=queue)
    except Exception as e:
        logger.error(f"Failed to send item to RabbitMQ: {e}")
    finally:
        await rabbitmq.close()
        # Ensure the connection is closed
        logger.info("RabbitMQ connection closed after publishing payment details")
        return True
    return False
