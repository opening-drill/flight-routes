import sys
import logging
import json
from src.services.kafka import config
from src.services.kafka.consumer import KafkaConsumerWrapper
from src.services.kafka.producer import KafkaProducerWrapper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MainService")

def main_kafka(process_flight_message):
    logger.info("Initializing Kafka Producer and Consumer...")
    producer = KafkaProducerWrapper()
    consumer = KafkaConsumerWrapper()

    consumer.subscribe([config.INPUT_TOPIC])

    try:
        # Poll Kafka for incoming messages
        consumer.start_polling(process_flight_message)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received.")
    finally:
        # Clean up resources
        producer.flush()
        consumer.close()