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


async def send_item_to_category_topic(item: ItemInResponse):
    try:
        await rabbitmq.connect()
        message_body = {k: str(v) for k, v in item.__dict__.items()}
        await rabbitmq.publish_to_topic(
            category_id=item.category_id, message=message_body
        )
    except Exception as e:
        logging.error(f"Failed to send item to RabbitMQ topic: {e}")
    finally:
        await rabbitmq.close()
        # Ensure the connection is closed


async def send_new_item_notification(item: ItemInResponse):
    await send_item_to_queue(item=item)
    await send_item_to_category_topic(item=item)
