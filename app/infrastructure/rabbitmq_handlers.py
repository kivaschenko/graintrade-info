import asyncio
import logging
from aio_pika import connect_robust, Message, ExchangeType


class RabbitMQHandler:
    def __init__(self, loop, rabbitmq_url, queue_name):
        self.loop = loop
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

    async def start(self):
        try:
            # Establish connection and channel
            self.connection = await connect_robust(self.rabbitmq_url, loop=self.loop)
            self.channel = await self.connection.channel()

            # Declare an exchange and a queue
            self.exchange = await self.channel.declare_exchange(
                "direct_exchange", ExchangeType.DIRECT
            )
            self.queue = await self.channel.declare_queue(self.queue_name, durable=True)

            # Bind the queue to the exchange
            await self.queue.bind(self.exchange, routing_key=self.queue_name)

            logging.info("RabbitMQ connection established")
        except Exception as e:
            logging.error(f"Failed to start RabbitMQ handler: {e}")
            raise

    async def stop(self):
        if self.connection:
            await self.connection.close()
            logging.info("RabbitMQ connection closed")

    async def send_message(self, message):
        try:
            await self.exchange.publish(
                Message(body=message.encode("utf-8")),
                routing_key=self.queue_name,
            )
            logging.info(f"Message sent: {message}")
        except Exception as e:
            logging.error(f"Failed to send message: {e}")

    async def consume_messages(self):
        try:
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        logging.info(
                            f"Consumed message: {message.body.decode('utf-8')}"
                        )
        except Exception as e:
            logging.error(f"Failed to consume messages: {e}")


async def main():
    loop = asyncio.get_running_loop()
    rabbitmq_handler = RabbitMQHandler(
        loop, "amqp://guest:guest@localhost/", "my_queue"
    )

    await rabbitmq_handler.start()

    # Example of sending a message
    await rabbitmq_handler.send_message("Hello, RabbitMQ!")

    # Example of consuming messages
    await rabbitmq_handler.consume_messages()

    await rabbitmq_handler.stop()


if __name__ == "__main__":
    asyncio.run(main())
