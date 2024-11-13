from app.rabbit_mq import RabbitMQ


async def publish_document_upload_event(
    rabbitmq: RabbitMQ,
    queue: str,
    document_uuid: str,
    params: dict,
) -> None:
    message = {
        "event": "document_upload",
        "document_uuid": document_uuid,
        "params": params,
    }
    await rabbitmq.publish(message, queue)
