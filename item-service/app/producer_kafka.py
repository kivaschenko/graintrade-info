import json
import asyncio
import logging
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

TOPIC = "new-item"
KAFKA_BROKER = "kafka:9092"  # Replace with your Kafka broker address


# Initialize the Kafka producer
async def init_kafka_producer():
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()
    return producer


# Function to send a message to Kafka
async def send_message(producer: AIOKafkaProducer, message: dict):
    try:
        # Send the message to the Kafka topic
        await producer.send_and_wait(TOPIC, message)
        logging.info(f"Message sent: {message}")
    except KafkaError as e:
        logging.error(f"Failed to send message: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


# Function to close the Kafka producer
async def close_kafka_producer(producer: AIOKafkaProducer):
    await producer.stop()
    logging.info("Kafka producer closed")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    producer = loop.run_until_complete(init_kafka_producer())

    try:
        # Example message to send
        message = {"item_id": 123, "item_name": "Sample Item"}
        loop.run_until_complete(send_message(producer, message))
    finally:
        loop.run_until_complete(close_kafka_producer(producer))
