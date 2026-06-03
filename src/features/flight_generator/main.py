import importlib
import os
from typing import Any, Callable

from .data_generator import generate_flight_data
from ...services.kafka import (
    close_kafka_producer,
    create_kafka_producer,
    publish_json_messages,
)


def publish_generated_flights(
    num_flights: int,
    fetch_geography_batch: Callable[[], Any],
    fetch_gaza_area: Callable[[], dict[str, Any]],
    bootstrap_servers: str | None = None,
    topic: str | None = None,
) -> list[dict[str, object]]:
    kafka_bootstrap_servers = bootstrap_servers or os.getenv(
        "FLIGHT_GENERATOR_KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092",
    )
    kafka_topic = topic or os.getenv(
        "FLIGHT_GENERATOR_KAFKA_TOPIC",
        "flight-routes",
    )

    payloads = generate_flight_data(
        num_flights=num_flights,
        fetch_geography_batch=fetch_geography_batch,
        fetch_gaza_area=fetch_gaza_area,
    )
    producer = create_kafka_producer(kafka_bootstrap_servers)

    try:
        return publish_json_messages(
            producer=producer,
            topic=kafka_topic,
            messages=payloads,
        )
    finally:
        close_kafka_producer(producer)


def _load_callable_from_env(env_var_name: str) -> Callable[[], Any]:
    import_path = os.getenv(env_var_name)
    if not import_path:
        raise ValueError(
            f"Missing required environment variable: {env_var_name}. "
            "Expected format: package.module:function_name"
        )

    module_name, separator, function_name = import_path.partition(":")
    if not separator or not module_name or not function_name:
        raise ValueError(
            f"Invalid value for {env_var_name}: {import_path}. "
            "Expected format: package.module:function_name"
        )

    module = importlib.import_module(module_name)
    fetch_function = getattr(module, function_name)

    if not callable(fetch_function):
        raise TypeError(
            f"{env_var_name} resolved to a non-callable object: {import_path}"
        )

    return fetch_function


def main() -> None:
    num_flights = int(os.getenv("FLIGHT_GENERATOR_NUM_FLIGHTS", "1"))
    fetch_geography_batch = _load_callable_from_env(
        "FLIGHT_GENERATOR_GEOGRAPHY_FETCHER"
    )
    fetch_gaza_area = _load_callable_from_env("FLIGHT_GENERATOR_GAZA_FETCHER")

    publish_generated_flights(
        num_flights=num_flights,
        fetch_geography_batch=fetch_geography_batch,
        fetch_gaza_area=fetch_gaza_area,
    )


if __name__ == "__main__":
    main()
