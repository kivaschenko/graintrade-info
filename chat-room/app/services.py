import logging
import time

from .metrics import (
    QUEUE_PUBLISH_ATTEMPTS,
    QUEUE_PUBLISH_FAILURES,
    QUEUE_PUBLISH_LATENCY,
)
from .models import Message
from .rabbit_mq import QueueName, rabbitmq

logging.basicConfig(level=logging.INFO)


async def send_message_to_queue(
    message: Message, queue: QueueName = QueueName.MESSAGE_EVENTS
):
    queue_label = queue.value if isinstance(queue, QueueName) else str(queue)
    publish_start = time.perf_counter()
    try:
        await rabbitmq.connect()
        message_body = {
            "type": "new_message",
            "to_username": message.receiver_id,
            "message_text": message.content,
            "item_id": message.item_id,
        }
        await rabbitmq.publish(message=message_body, queue=queue)
        QUEUE_PUBLISH_ATTEMPTS.labels(queue=queue_label, status="success").inc()
    except Exception as e:
        logging.error(f"Failed to send message to RabbitMQ: {e}")
        QUEUE_PUBLISH_ATTEMPTS.labels(queue=queue_label, status="error").inc()
        QUEUE_PUBLISH_FAILURES.labels(queue=queue_label).inc()
    finally:
        QUEUE_PUBLISH_LATENCY.labels(queue=queue_label).observe(
            time.perf_counter() - publish_start
        )
        await rabbitmq.close()
        logging.info(f"Message ID {message.id} sent to queue.")
        # Ensure the connection is closed
