import aio_pika
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

RABBITMQ_URL = "amqp://guest:guest@localhost/"
RABBITMQ_EXCHANGE = "item_exchange"
RABBITMQ_QUEUE = "item_notifications"

app = FastAPI()

clients = set()


@app.websocket("/ws/items/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
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
        await channel.declare_exchange(RABBITMQ_EXCHANGE, aio_pika.ExchangeType.DIRECT)
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(RABBITMQ_QUEUE, durable=True)
        await queue.bind(RABBITMQ_EXCHANGE)
        print("Waiting for messages...")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    print("Received:", message.body.decode())
                    # await notify_clients(message.body.decode())


# Run the RabbitMQ listener in the background
loop = asyncio.get_event_loop()
loop.create_task(rabbit_listener())
