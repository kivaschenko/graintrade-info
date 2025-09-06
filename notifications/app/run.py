import asyncio
import logging
from .config import RABBITMQ_URL
from .consumers import handle_item_notification

import aio_pika
from enum import Enum


class QueueName(str, Enum):
    ITEM_EVENTS = "ITEM_EVENTS"


async def main():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    conn = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await conn.channel()
    await channel.set_qos(prefetch_count=10)

    queue = await channel.declare_queue(QueueName.ITEM_EVENTS.value, durable=True)
    await queue.consume(handle_item_notification)

    logging.info("Notification Service running...")
    return conn


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    conn = loop.run_until_complete(main())
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(conn.close())
