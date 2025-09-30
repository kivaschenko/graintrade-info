import logging
from ..rabbit_mq import rabbitmq, QueueName
from ..schemas import ItemInResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_item_to_queue(
    item: ItemInResponse, queue: QueueName = QueueName.ITEM_EVENTS
):
    try:
        await rabbitmq.connect()
        message_body = {k: str(v) for k, v in item.__dict__.items()}
        await rabbitmq.publish(message=message_body, queue=queue)
    except Exception as e:
        logging.error(f"Failed to send item to RabbitMQ: {e}")
    finally:
        await rabbitmq.close()
        # Ensure the connection is closed


async def send_deleted_item_to_queue(
    item_id: int,
    telegram_message_id: int,
    chat_id: int,
    queue: QueueName = QueueName.DELETED_ITEMS,
):
    try:
        await rabbitmq.connect()
        message_body = {
            "id": str(item_id),
            "telegram_message_id": str(telegram_message_id),
            "chat_id": str(chat_id),
        }
        await rabbitmq.publish(message=message_body, queue=queue)
        logging.info(f"Sent deleted item ID {item_id} to queue {queue}")
    except Exception as e:
        logging.error(f"Failed to send deleted item to RabbitMQ: {e}")
    finally:
        await rabbitmq.close()
        # Ensure the connection is closed
