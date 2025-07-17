import logging
from .rabbit_mq import rabbitmq, QueueName
from .models import Message

logging.basicConfig(level=logging.INFO)


async def send_message_to_queue(
    message: Message, queue: QueueName = QueueName.MESSAGE_EVENTS
):
    try:
        await rabbitmq.connect()
        message_body = {
            "type": "new_message",
            "to_username": message.receiver_id,
            "message_text": message.content,
            "item_id": message.item_id,
        }
        await rabbitmq.publish(message=message_body, queue=queue)
    except Exception as e:
        logging.error(f"Failed to send message to RabbitMQ: {e}")
    finally:
        await rabbitmq.close()
        logging.info(f"Message ID {message.id} sent to queue.")
        # Ensure the connection is closed
