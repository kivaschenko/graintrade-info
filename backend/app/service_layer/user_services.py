import logging
from ..schemas import UserInResponse
from ..rabbit_mq import rabbitmq, QueueName

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_user_to_rabbitmq(
    user: UserInResponse, queue: QueueName = QueueName.USER_EVENTS
):
    try:
        await rabbitmq.connect()
        message_body = {k: str(v) for k, v in user.__dict__.items()}
        await rabbitmq.publish(message=message_body, queue=queue)
    except Exception as e:
        logging.error(f"Failed to send user to RabbitMQ: {e}")
    finally:
        await rabbitmq.close()  # Ensure the connection is closed


async def create_free_subscription(user_id: int):
    """
    Create a free subscription for a user.
    """
    from ..models.subscription_model import (
        create_free_subscription as create_free_subscription_model,
    )  # Import here to avoid circular import

    new_subscription = await create_free_subscription_model(user_id=user_id)
    if new_subscription is None:
        raise ValueError("Failed to create free subscription")
    logging.info(f"Free subscription created for user {user_id}: {new_subscription.id}")
    return new_subscription
