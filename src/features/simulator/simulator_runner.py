import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.env_loader import load_project_env
from src.features.simulator.simulation_service import generate_simulation_messages
from src.geo.config import load_combined_region_geojson
from src.services.kafka import (
    close_kafka_producer,
    open_kafka_producer,
    publish_messages,
)
from src.services.postgres import (
    close_postgres_connection,
    fetch_restricted_zone_rows,
    generate_unused_event_id,
    open_postgres_connection_from_env,
    select_random_free_aircraft_id,
)


def publish_simulation_messages(
    flight_count: int,
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
    restricted_zone_rows = fetch_restricted_zone_rows(postgres_connection)
    payloads = generate_simulation_messages(
        flight_count=flight_count,
        next_event_id_supplier=lambda: generate_unused_event_id(postgres_connection),
        free_aircraft_id_supplier=lambda: select_random_free_aircraft_id(
            postgres_connection
        ),
        allowed_region_geojson=allowed_region_geojson,
        restricted_zone_rows=restricted_zone_rows,
    )
    producer = open_kafka_producer(kafka_bootstrap_servers)

    try:
        return publish_messages(
            producer=producer,
            topic=kafka_topic,
            messages=payloads,
        )
    finally:
        close_kafka_producer(producer)


def run_simulator() -> None:
    load_project_env()
    flight_count = int(os.getenv("FLIGHT_GENERATOR_NUM_FLIGHTS", "1"))
    postgres_connection = open_postgres_connection_from_env()

    try:
        publish_simulation_messages(
            flight_count=flight_count,
            postgres_connection=postgres_connection,
        )
    finally:
        close_postgres_connection(postgres_connection)


if __name__ == "__main__":
    run_simulator()
