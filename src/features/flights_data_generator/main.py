import os

from .config import load_combined_region_geojson
from .data_generator import generate_flight_data
from ...services.kafka import (
    close_kafka_producer,
    create_kafka_producer,
    publish_json_messages,
)
from ...services.postgres import (
    close_postgres_connection,
    create_postgres_connection_from_env,
    fetch_polygon_rows,
    generate_unique_event_id,
    get_random_free_aircraft_id,
)


def publish_generated_flights(
    num_flights: int,
    postgres_connection,
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

    allowed_region_geojson = load_combined_region_geojson()
    blocked_polygons = fetch_polygon_rows(postgres_connection)
    payloads = generate_flight_data(
        num_flights=num_flights,
        next_event_id=lambda: generate_unique_event_id(postgres_connection),
        get_random_free_aircraft_id=lambda: get_random_free_aircraft_id(
            postgres_connection
        ),
        allowed_region_geojson=allowed_region_geojson,
        blocked_polygons=blocked_polygons,
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


def main() -> None:
    num_flights = int(os.getenv("FLIGHT_GENERATOR_NUM_FLIGHTS", "1"))
    postgres_connection = create_postgres_connection_from_env()

    try:
        publish_generated_flights(
            num_flights=num_flights,
            postgres_connection=postgres_connection,
        )
    finally:
        close_postgres_connection(postgres_connection)


if __name__ == "__main__":
    main()
