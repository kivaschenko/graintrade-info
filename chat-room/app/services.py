import logging
from .rabbit_mq import rabbitmq, QueueName

logging.basicConfig(level=logging.INFO)


async def send_message_to_queue(
    message: dict, queue: QueueName = QueueName.MESSAGE_EVENTS
):
    try:
        await rabbitmq.connect()
        await rabbitmq.publish(message, queue=queue)
    except Exception as e:
        logging.error(f"Failed to send message to RabbitMQ: {e}")
    finally:
        await rabbitmq.close()
        logging.info(f"Message ID {message['id']} sent to queue.")
        # Ensure the connection is closed
