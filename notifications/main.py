import logging
import aio_pika
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

RABBITMQ_USER = "rabbit_user"
RABBITMQ_PASSWORD = "SoYjysnlhorTtzj"
RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@rabbitmq/"
# RabbitMQ exchange and queue names
ITEM_RABBITMQ_EXCHANGE = "item_exchange"
ITEM_RABBITMQ_QUEUE = "item_notifications"
USER_RABBITMQ_EXCHANGE = "user_exchange"
USER_RABBITMQ_QUEUE = "user_notifications"

app = FastAPI()

logging.basicConfig(
    level=logging.INFO,
    filename=__name__ + ".log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

clients = set()


@app.websocket("/ws/items/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    logging.info(f"Client connected: {websocket.client}")
    try:
        while True:
            await asyncio.sleep(1)  # Keep the connection alive
    except WebSocketDisconnect:
        clients.remove(websocket)


# Notify all connected clients
async def notify_clients(message: str):
    for client in clients:
        await client.send_text(message)


# Listner RabbitMQ
async def rabbit_listener():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.declare_exchange(
            ITEM_RABBITMQ_EXCHANGE, aio_pika.ExchangeType.DIRECT
        )
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(ITEM_RABBITMQ_QUEUE, durable=True)
        await queue.bind(ITEM_RABBITMQ_EXCHANGE)
        logging.info("Waiting for messages...")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    logging.info(f"Received: {message.body.decode()}")


# Listner RabbitMQ for user notifications
async def user_rabbit_listener():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.declare_exchange(
            USER_RABBITMQ_EXCHANGE, aio_pika.ExchangeType.DIRECT
        )
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(USER_RABBITMQ_QUEUE, durable=True)
        await queue.bind(USER_RABBITMQ_EXCHANGE)
        logging.info("Waiting for user messages...")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    logging.info(f"Received user message: {message.body.decode()}")


# Run the RabbitMQ listener in the background
loop = asyncio.get_event_loop()
loop.create_task(rabbit_listener())
loop.create_task(user_rabbit_listener())
# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8001)
