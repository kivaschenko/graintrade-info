import logging
import os
from datetime import date, timedelta
import aio_pika
import aio_pika.abc
from ..schemas import UserInResponse, SubscriptionStatus, SubscriptionInDB

# RabbitMQ configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
RABBITMQ_QUEUE = "user_notifications"


async def send_user_to_rabbitmq(user: UserInResponse):
    """
    Send user data to RabbitMQ queue.
    """
    try:
        # Create a connection to RabbitMQ
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            # Create a channel
            channel: aio_pika.abc.AbstractChannel = await connection.channel()
            # Publish message to the exchange
            message_body = user.model_dump_json().encode("utf-8")
            message = aio_pika.Message(body=message_body)
            await channel.default_exchange.publish(message, routing_key=RABBITMQ_QUEUE)
            logging.info(f"User {user.id} sent to RabbitMQ queue {RABBITMQ_QUEUE}")
    except Exception as e:
        logging.error(f"Failed to send user to RabbitMQ: {e}")
    finally:
        await connection.close()  # Ensure the connection is closed


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
    print(f"Free subscription created for user {user_id}: {new_subscription.id}")
    return new_subscription
