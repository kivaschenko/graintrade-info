import logging
import asyncio
import aio_pika
import aio_pika.abc
from app.routers.schemas import UserInResponse

RABBITMQ_URL = "amqp://guest:guest@localhost/"
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
