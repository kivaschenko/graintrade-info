from app.infrastructure.rabbitmq_handlers import RabbitMQHandler
import asyncio
import logging
from aio_pika import connect_robust, Message, ExchangeType
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
    # Get the current event loop
    loop = asyncio.get_running_loop()
    # Create an instance of the RabbitMQ handler
    rabbitmq_handler = RabbitMQHandler(loop, RABBITMQ_URL, RABBITMQ_QUEUE)
    # Start the RabbitMQ handler
    await rabbitmq_handler.start()
    # Send the message to the queue
    await rabbitmq_handler.send_message(item.model_dump_json())
    # Stop the RabbitMQ handler
    await rabbitmq_handler.stop()


# --------------------------------------------------------
# Publisher/Subscriber pattern for RabbitMQ
# Not completely implemented yet
async def create_rabbitmq_connection():
    """Create a RabbitMQ connection."""
    try:
        # Establish connection to RabbitMQ
        connection = await connect_robust(RABBITMQ_URL)
        return connection
    except Exception as e:
        logging.error(f"Failed to connect to RabbitMQ: {e}")
        return None


async def create_rabbitmq_channel(connection):
    """Create a RabbitMQ channel."""
    try:
        # Create a channel
        channel = await connection.channel()
        return channel
    except Exception as e:
        logging.error(f"Failed to create RabbitMQ channel: {e}")
        return None


async def create_rabbitmq_exchange(channel, exchange_name, exchange_type):
    """Create a RabbitMQ exchange."""
    try:
        # Declare an exchange
        exchange = await channel.declare_exchange(
            exchange_name, ExchangeType(exchange_type)
        )
        return exchange
    except Exception as e:
        logging.error(f"Failed to declare RabbitMQ exchange: {e}")
        return None


def create_routing_key_for_item(
    item_country: str, item_region: str, item_category_id: int, item_offer_type: str
):
    """Create a routing key for the item based on its country, category, and type offer."""
    return f"{item_country.lower()}.{item_region.lower()}.{item_category_id}.{item_offer_type.lower()}"


async def publish_new_item_message_to_topic_exchange(item: ItemInResponse):
    """Publish a new item message to the topic exchange."""
    try:
        # Create a RabbitMQ connection
        connection = await create_rabbitmq_connection()
        if not connection:
            return

        # Create a RabbitMQ channel
        channel = await create_rabbitmq_channel(connection)
        if not channel:
            return

        # Create a RabbitMQ exchange
        exchange_name = "item_topic_exchange"
        exchange_type = "topic"
        exchange = await create_rabbitmq_exchange(channel, exchange_name, exchange_type)
        if not exchange:
            return

        # Create a routing key for the item
        routing_key = create_routing_key_for_item(
            item.country, item.region, item.category_id, item.offer_type
        )

        # Publish the message to the exchange
        message_body = item.model_dump_json()
        message = Message(body=message_body.encode("utf-8"))
        await exchange.publish(message, routing_key=routing_key)

        logging.info(f"Message sent: {message_body}")
    except Exception as e:
        logging.error(f"Failed to publish message: {e}")
    finally:
        # Close the connection
        await connection.close()


# Example usage
if __name__ == "__main__":
    # Example item
    item = ItemInResponse(
        id=1,
        name="Sample Item",
        description="This is a sample item.",
        price=19.99,
        country="US",
        region="CA",
        category="Electronics",
        type_offer="New",
    )
    # Send the message to the queue
    asyncio.run(send_message_to_queue(item))
