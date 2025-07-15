from pathlib import Path
import os
import logging
import aio_pika
import json

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

async def publish_notification(payload: dict):
    connection = await aio_pika.connect_robust(
        host=self.host,
        port=self.port,
        login=self.username,
        password=self.password,
        virtualhost=self.vhost,
    )
    logger.info(f"Connected to RabbitMQ: {connection}")
    channel = await connection.channel()
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(payload).encode()),
        routing_key="notifications.email",
    )
    logger.info(f"Message published to RabbitMQ: {payload}")
    await connection.close()
    logger.info("Connection closed.")
