import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import logging


class KafkaHandler:
    def __init__(self, loop, bootstrap_servers, topic):
        self.loop = loop
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id="my-group",
        )
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
        )

    async def start(self):
        await self.producer.start()
        await self.consumer.start()

    async def stop(self):
        await self.consumer.stop()
        await self.producer.stop()

    async def send_message(self, message):
        try:
            await self.producer.send_and_wait(self.topic, message.encode("utf-8"))
        except Exception as e:
            logging.error(f"Failed to send message: {e}")

    async def consume_messages(self):
        try:
            async for msg in self.consumer:
                print(f"Consumed message: {msg.value.decode('utf-8')}")
        except Exception as e:
            logging.error(f"Failed to consume messages: {e}")


async def main():
    loop = asyncio.get_running_loop()
    kafka_handler = KafkaHandler(loop, "localhost:9092", "my_topic")

    await kafka_handler.start()

    # Example of sending a message
    await kafka_handler.send_message("Hello, Kafka!")

    # Example of consuming messages
    await kafka_handler.consume_messages()

    await kafka_handler.stop()


if __name__ == "__main__":
    asyncio.run(main())
