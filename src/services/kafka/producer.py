import logging
# pyrefly: ignore [missing-import]
from confluent_kafka import Producer
from src.services.kafka import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaProducer")

class KafkaProducerWrapper:
    def __init__(self):
        logger.info(f"Initializing Kafka Producer with bootstrap servers: {config.BOOTSTRAP_SERVERS}")
        self.producer = Producer(config.kafka_config)

    def _delivery_report(self, err, msg):
        """Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush()."""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.info(
                f"Message delivered to topic '{msg.topic()}' "
                f"partition [{msg.partition()}] @ offset {msg.offset()}"
            )

    def send_message(self, topic: str, value: str, key: str = None):
        """Asynchronously sends a message to Kafka.
        Calls poll(0) to handle delivery callbacks from previous messages."""
        try:
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=value.encode('utf-8'),
                callback=self._delivery_report
            )
            # Serve delivery callback queue. 
            # A poll(0) is non-blocking and handles callbacks for completed events.
            self.producer.poll(0)
        except BufferError:
            logger.warning("Local queue full, waiting for free space...")
            self.producer.poll(1)
            self.send_message(topic, value, key)
        except Exception as e:
            logger.error(f"Failed to produce message: {e}")

    def flush(self, timeout: float = 10.0):
        """Wait for all outstanding messages to be delivered."""
        logger.info("Flushing Kafka producer queue...")
        self.producer.flush(timeout)
        logger.info("Flush complete.")
