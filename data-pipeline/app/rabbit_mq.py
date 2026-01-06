import aio_pika
import json

from app.logger import logger
from app.config import settings
from typing import List


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
            await self.channel.default_exchange.publish(  # type: ignore
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
            queue_created = await self.channel.declare_queue(queue, durable=True)  # type: ignore
            await queue_created.consume(callback, no_ack=False)
            await self.connection.connected.wait()  # type: ignore
        except Exception as e:
            logger.error(f"Failed to consume messages from RabbitMQ: {e}")

    async def close(self):
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")


def get_rabbitmq_instance() -> RabbitMQ:
    return RabbitMQ(
        host=settings.RABBITMQ_HOST,
        port=5672,
        username=settings.RABBITMQ_USER,
        password=settings.RABBITMQ_PASS,
        vhost=settings.RABBITMQ_VHOST,
        queues=["data_processing_queue"],
    )