from pathlib import Path
import aio_pika
import json
import os
import logging

from typing import List, Dict
from enum import StrEnum
from dotenv import load_dotenv

from .model import get_all_categories
from .schemas import CategoryInResponse

# Initialize logger
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Get RabbitMQ connection parameters from environment variables
rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
rabbitmq_port: int = int(os.getenv("RABBITMQ_PORT", 5672))
rabbitmq_username: str = os.getenv("RABBITMQ_USER", "guest")
rabbitmq_password: str = os.getenv("RABBITMQ_PASS", "guest")
rabbitmq_vhost = os.getenv("RABBITMQ_VHOST", "/")

if not rabbitmq_host or not rabbitmq_username or not rabbitmq_password:
    raise ValueError("Check environment variables for RabbitMQ!")


class QueueName(StrEnum):
    ITEM_EVENTS = "item.events"
    USER_EVENTS = "user.events"
    PAYMENT_EVENTS = "payment.events"
    MESSAGE_EVENTS = "message.events"


# Generate the list of all queue names dynamically
ALL_QUEUES: List[str] = [queue.value for queue in QueueName]

# generate topics from categories
ALL_TOPICS: Dict[int, str] = {}


async def create_topics_from_categories():
    """Create RabbitMQ topics based on categories."""
    categories: List[CategoryInResponse] = await get_all_categories()
    for category in categories:
        if not ALL_TOPICS.get(category.id):
            # Create topic in the format: parent_category.name
            if category.parent_category:
                topic = f"{category.parent_category.lower().replace(' ', '_')}.{category.name.lower().replace(' ', '_')}"
                # Store the topic with category ID as key
                ALL_TOPICS.update({category.id: topic})
            else:
                # If no parent category, use just the category name
                topic = category.name.lower().replace(" ", "_")
        else:
            # If topic already exists, skip creation
            continue


class RabbitMQ:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        vhost: str,
        queues: List[str],
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.vhost = vhost
        # self.connection = None
        # self.channel = None
        self.queues = queues
        # Initialize topics from categories
        self.topics = ALL_TOPICS

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                login=self.username,
                password=self.password,
                virtualhost=self.vhost,
            )
            self.channel = await self.connection.channel()
            for queue in self.queues:
                await self.channel.declare_queue(queue, durable=True)
                logger.info(f"Connected to RabbitMQ on {self.host}, queue: {queue}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")

    async def publish(self, message: dict, queue: str):
        if not self.channel:
            await self.connect()
        try:
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue,
            )
            logger.info(f"Message published to RabbitMQ: {message}")
        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {e}")

    async def consume(self, queue: str, callback):
        if not self.channel:
            await self.connect()
        try:
            queue_created = await self.channel.declare_queue(queue, durable=True)
            await queue_created.consume(callback, no_ack=False)
            await self.connection.connected.wait()
        except Exception as e:
            logger.error(f"Failed to consume messages from RabbitMQ: {e}")

    async def publish_to_topic(self, category_id: int, message: dict):
        topic = self.topics.get(category_id)
        if not topic:
            logger.error(f"No topic found for category ID: {category_id}")
            return
        try:
            topic_exchange = await self.channel.declare_exchange(
                "topic_items", aio_pika.ExchangeType.TOPIC, durable=True
            )
            await topic_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(message).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=topic,
            )
            logger.info(f"Message published to topic {topic}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish message to topic {topic}: {e}")

    async def consume_from_topic(self, topic: str, callback):
        if not self.channel:
            await self.connect()
        try:
            topic_exchange = await self.channel.declare_exchange(
                "topic_items", aio_pika.ExchangeType.TOPIC, durable=True
            )
            queue = await self.channel.declare_queue("", exclusive=True)
            await queue.bind(topic_exchange, routing_key=topic)
            await queue.consume(callback, no_ack=False)
            logger.info(f"Consuming from topic {topic}")
        except Exception as e:
            logger.error(f"Failed to consume messages from topic {topic}: {e}")

    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")


# Initialize RabbitMQ connection
rabbitmq = RabbitMQ(
    host=rabbitmq_host,
    port=rabbitmq_port,
    username=rabbitmq_username,
    password=rabbitmq_password,
    vhost=rabbitmq_vhost,
    queues=ALL_QUEUES,
)


async def get_rabbitmq_connection():
    rabbitmq = RabbitMQ(
        host=rabbitmq_host,
        port=rabbitmq_port,
        username=rabbitmq_username,
        password=rabbitmq_password,
        vhost=rabbitmq_vhost,
        queues=ALL_QUEUES,
    )
    await rabbitmq.connect()
    return rabbitmq


if __name__ == "__main__":
    # Test the RabbitMQ connection and message publishing/consuming
    import asyncio

    # Test creating topics from categories
    asyncio.run(create_topics_from_categories())

    async def publish_document_upload_event(
        rabbitmq: RabbitMQ = rabbitmq,
        queue: str = QueueName.MESSAGE_EVENTS,
        document_uuid: str = "test_uuid",
        document_type: str = "test_type",
        params: dict = {"key": "value"},
    ) -> None:
        message = {
            "event": "document_upload",
            "document_uuid": document_uuid,
            "document_type": document_type,
            "params": params,
        }
        await rabbitmq.publish(message, queue)

    async def test_rabbitmq():
        await rabbitmq.connect()
        queue = QueueName.MESSAGE_EVENTS
        print(f"Publish messages to queue: {queue}")
        await publish_document_upload_event(rabbitmq, queue)
        await rabbitmq.close()

    asyncio.run(test_rabbitmq())

    async def test_rabbitmq_consume():
        await rabbitmq.connect()

        async def callback(message: aio_pika.IncomingMessage):
            async with message.process():
                print("Received message:", json.loads(message.body.decode()))

        queue = QueueName.MESSAGE_EVENTS
        print(f"Consume messages from queue: {queue}")
        await rabbitmq.consume(queue, callback)

    asyncio.run(test_rabbitmq_consume())
