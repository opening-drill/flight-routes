import logging
# pyrefly: ignore [missing-import]
from confluent_kafka import Consumer, KafkaError, KafkaException
from src.services.kafka import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaConsumer")

class KafkaConsumerWrapper:
    def __init__(self):
        logger.info(
            f"Initializing Kafka Consumer with group ID '{config.GROUP_ID}' "
            f"on bootstrap servers: {config.BOOTSTRAP_SERVERS}"
        )
        self.consumer = Consumer({**config.kafka_config, 'group.id': config.GROUP_ID})
        self.running = False

    def subscribe(self, topics: list):
        """Subscribes the consumer to the listed topics."""
        logger.info(f"Subscribing to topics: {topics}")
        self.consumer.subscribe(topics)

    def start_polling(self, message_handler, poll_timeout: float = 1.0):
        """Starts a loop to poll Kafka for messages and invoke the message_handler callback."""
        self.running = True
        logger.info("Started polling for messages...")
        try:
            while self.running:
                msg = self.consumer.poll(timeout=poll_timeout)
                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event - not an error
                        logger.info(
                            f"Reached end of partition: {msg.topic()} [{msg.partition()}] "
                            f"at offset {msg.offset()}"
                        )
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    # Message received successfully
                    key = msg.key().decode('utf-8') if msg.key() else None
                    value = msg.value().decode('utf-8') if msg.value() else None
                    
                    logger.info(
                        f"Message received: partition={msg.partition()}, offset={msg.offset()}"
                    )
                    try:
                        # Invoke custom callback
                        message_handler(key, value)
                    except Exception as handler_err:
                        logger.error(f"Error executing message handler: {handler_err}")
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received in polling loop.")
        finally:
            self.close()

    def stop(self):
        """Signals the polling loop to stop."""
        logger.info("Stopping Kafka consumer polling...")
        self.running = False

    def close(self):
        """Closes the consumer connection and commits remaining offsets."""
        logger.info("Closing Kafka consumer...")
        self.consumer.close()
        logger.info("Kafka consumer closed.")
