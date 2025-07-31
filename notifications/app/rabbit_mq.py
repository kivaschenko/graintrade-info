# app/rabbit_mq.py
from pathlib import Path
import aio_pika
import json
import os
import logging

from typing import List
from enum import StrEnum

from dotenv import load_dotenv

# Initialize logger
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Get RabbitMQ connection parameters from environment variables
rabbitmq_host = os.getenv("RABBITMQ_HOST")
rabbitmq_port = os.getenv("RABBITMQ_PORT", 5672)
rabbitmq_username = os.getenv("RABBITMQ_USER")
rabbitmq_password = os.getenv("RABBITMQ_PASS")
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
        self.connection = None
        self.channel = None
        self.queues = queues

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
