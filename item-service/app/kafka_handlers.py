import asyncio
import os
import json
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError


class KafkaHandler:
    def __init__(self, loop):
        self.loop = loop
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.consumer = AIOKafkaConsumer(
            "my_topic", loop=self.loop, bootstrap_servers=self.bootstrap_servers
        )
        self.producer = AIOKafkaProducer(
            loop=self.loop, bootstrap_servers=self.bootstrap_servers
        )

    async def start(self):
        await self.consumer.start()
        asyncio.ensure_future(self.consume())

    async def stop(self):
        await self.producer.stop()
        await self.consumer.stop()

    async def consume(self):
        async for msg in self.consumer:
            logging.info("consumed: {}".format(msg.value))
            await self.handle_message(msg)

    async def handle_message(self, msg):
        print("handle_message")
        print(msg)
        pass

    async def send_message(self, topic, message):
        try:
            await self.producer.send_and_wait(
                topic, json.dumps(message).encode("utf-8")
            )
            logging.info("sent: {}".format(message))
        except KafkaError as e:
            logging.error("error: {}".format(e))
            raise e


async def main():
    loop = asyncio.new_event_loop()
    kafka_handler = KafkaHandler(loop=loop)
    await kafka_handler.send_message(
        "my_topic", {"id": 1, "title": "New Item 1", "price": "100.10"}
    )
    await kafka_handler.start()
    await kafka_handler.consume()
    await kafka_handler.stop()
