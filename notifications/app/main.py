import asyncio
import logging


from .database import database
from .rabbit_mq import QueueName, get_rabbitmq_connection
from .consumers import (
    handle_item_notification,
    handle_message_notification,
    handle_password_recovery_notification,
    handle_payment_notification,
)


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


async def main():
    rabbitmq = await get_rabbitmq_connection()
    logging.info("RabbitMQ connection established and consumers started.")
    logging.info(f"Consuming from queue: {QueueName.MESSAGE_EVENTS.value}")
    # Start consuming messages from the RabbitMQ queue
    await rabbitmq.consume(
        queue=QueueName.MESSAGE_EVENTS.value,
        callback=handle_message_notification,
    )
    # Start consuming item notifications
    logging.info(f"Consuming from queue: {QueueName.ITEM_EVENTS.value}")
    await rabbitmq.consume(
        queue=QueueName.ITEM_EVENTS.value,
        callback=handle_item_notification,
    )
    # Start consuming payment notifications
    logging.info(f"Consuming from queue: {QueueName.PAYMENT_EVENTS.value}")
    await rabbitmq.consume(
        queue=QueueName.PAYMENT_EVENTS.value,
        callback=handle_payment_notification,
    )

    # Start consuming password recovery notifications
    logging.info(f"Consuming from queue: {QueueName.RECOVERY_EVENTS.value}")
    await rabbitmq.consume(
        queue=QueueName.RECOVERY_EVENTS.value,
        callback=handle_password_recovery_notification,
    )

    # Keep the script running to listen for messages
    logging.info("Waiting for notifications...")
    return rabbitmq


if __name__ == "__main__":
    logging.info("Starting notification service...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(database.connect())
    logging.info("Connected to database.")
    rabbitmq = loop.run_until_complete(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("Shutting down notification service...")
    finally:
        loop.run_until_complete(rabbitmq.close())
        loop.run_until_complete(database.disconnect())
        loop.close()
        logging.info("Notification service stopped.")
