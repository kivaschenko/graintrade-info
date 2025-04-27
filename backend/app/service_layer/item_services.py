import asyncio
import logging
import aio_pika
import aio_pika.abc
from app.routers.schemas import ItemInResponse

RABBITMQ_URL = "amqp://guest:guest@localhost/"
RABBITMQ_QUEUE = "item_notifications"

# -------------------------------------------------------
# BASE Implementation
# This is a simplified version of the RabbitMQ handler.
# It handles the connection to RabbitMQ and sending messages to a queue.


# This function is responsible for sending a message to the RabbitMQ queue.
async def send_message_to_queue(item: ItemInResponse):
    """Send a message about a new Item to the RabbitMQ queue."""
    try:
        # Create a connection to RabbitMQ
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        async with connection:
            # Create a channel
            channel: aio_pika.abc.AbstractChannel = await connection.channel()
            # Publish message to the exchange
            message_body = item.model_dump_json().encode("utf-8")
            message = aio_pika.Message(body=message_body)
            await channel.default_exchange.publish(message, routing_key=RABBITMQ_QUEUE)
            logging.info(f"Item {item.id} sent to RabbitMQ queue {RABBITMQ_QUEUE}")
    except Exception as e:
        logging.error(f"Failed to send item to RabbitMQ: {e}")
    finally:
        await connection.close()    # Ensure the connection is closed
