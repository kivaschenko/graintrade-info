import asyncio
import json
import logging
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError, KafkaConnectionError
from confluent_kafka.admin import AdminClient, NewTopic
import time
from pydantic import BaseModel

class KafkaHandler:
    def __init__(self):
        self.bootstrap_servers = "localhost:9092"
        self.topic = "auth-service"
        # self.create_topic(self.topic)
        self.loop = asyncio.get_event_loop()
        self.producer = AIOKafkaProducer(
            loop=self.loop,
            bootstrap_servers=self.bootstrap_servers
        )

    def create_topic(self, topic_name):
        admin_client = AdminClient({'bootstrap.servers': self.bootstrap_servers})
        topic_list = [NewTopic(topic_name, num_partitions=1, replication_factor=1)]
        fs = admin_client.create_topics(topic_list)
        
        for topic, f in fs.items():
            try:
                f.result()  # The result itself is None
                logging.info(f"Topic {topic} created")
            except Exception as e:
                logging.error(f"Failed to create topic {topic}: {e}")

    async def start(self):
        """start the consumer"""
        await self.producer.start()

    async def stop(self):
        await self.producer.stop()

    async def send_message(self, topic, message):
        if isinstance(message, BaseModel):
            message = message.model_dump()
            print("Jsonify message: ", message)
        try:
            await self.producer.send_and_wait(
                topic, json.dumps(message).encode("utf-8")
            )
            logging.info(f"sent: {message}")
        except KafkaError as e:
            logging.error("error: %", e)
            raise e

    async def retry_start(self, retries=5, delay=5):
        for attempt in range(retries):
            try:
                await self.start()
                return
            except KafkaConnectionError as e:
                logging.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise e

async def produce():
    kafka_handler = KafkaHandler()
    await kafka_handler.retry_start()
    await kafka_handler.send_message("auth-service", {"message": "Hello, Kafka!"})
    await kafka_handler.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    asyncio.run(produce())
