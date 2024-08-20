import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.errors import KafkaError


class KafkaHandler:
    def __init__(self, loop):
        self.loop = loop
        self.consumer = AIOKafkaConsumer(
            "my_topic", loop=self.loop, bootstrap_servers="localhost:9092"
        )
        self.producer = AIOKafkaProducer(
            loop=self.loop, bootstrap_servers="localhost:9092"
        )

    async def start(self):
        """start the consumer"""
        await self.consumer.start()
        asyncio.ensure_future(self.consume())

    async def stop(self):
        await self.producer.stop()
        await self.consumer.stop()

    async def consume(self):
        async for msg in self.consumer:
            logging.info("consumed: %s", msg.value)
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
            logging.info("sent: %", message)
        except KafkaError as e:
            logging.error("error: %", e)
            raise e
