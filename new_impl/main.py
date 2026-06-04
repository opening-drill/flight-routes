"""
Entry point: background Redis monitor + continuous Kafka consumption.

Flow:
  1. run_monitor polls Redis/API on an interval (daemon thread)
  2. Main thread consumes Kafka topic messages
  3. Each message triggers route calculation
  4. Resulting flight is written to Redis
"""

import threading

import config  # noqa: F401 — loads .env, app.ini, and import paths first

from confluent_kafka import Consumer
from config import settings
from database import RedisDB
from monitor import run_monitor
from route_handler import process_kafka_message


def start_monitor_thread() -> threading.Thread:
    thread = threading.Thread(
        target=run_monitor,
        kwargs={"interval_seconds": settings.monitor_interval_seconds},
        name="redis-flight-monitor",
        daemon=True,
    )
    thread.start()
    print(f"[Main] Started run_monitor (every {settings.monitor_interval_seconds}s).")
    return thread


def run_kafka_consumer(db: RedisDB) -> None:
    consumer = Consumer(settings.kafka_consumer_config())
    consumer.subscribe([settings.kafka_topic])
    print(f"[Main] Subscribed to Kafka topic: {settings.kafka_topic}")

    planner = None
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None or msg.error() is not None:
                continue
            try:
                planner = process_kafka_message(msg, db, planner)
            except Exception as exc:
                print(f"[Consumer] Failed to process message: {exc}")
    except KeyboardInterrupt:
        print("\n[Main] Shutting down...")
    finally:
        consumer.close()


def main() -> None:
    start_monitor_thread()
    db = RedisDB(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
    )
    run_kafka_consumer(db)


if __name__ == "__main__":
    main()
