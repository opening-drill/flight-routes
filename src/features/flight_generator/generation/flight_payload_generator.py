from random import choice, randint
from typing import Any, Callable

from ..config import URGENCY_LEVELS
from .gaza_point_generator import generate_random_gaza_point
from .payload_builders import build_flight_payload


def generate_single_flight_payload(
    geography_batch: Any,
    gaza_area_geojson: dict[str, Any],
) -> dict[str, object]:
    start = generate_random_gaza_point(
        gaza_area_geojson=gaza_area_geojson,
        geography_batch=geography_batch,
    )
    end = generate_random_gaza_point(
        gaza_area_geojson=gaza_area_geojson,
        geography_batch=geography_batch,
    )

    while start == end:
        end = generate_random_gaza_point(
            gaza_area_geojson=gaza_area_geojson,
            geography_batch=geography_batch,
        )

    return build_flight_payload(
        event_id=randint(1, 999_999),
        aircraft_id=randint(1_000, 9_999),
        start=start,
        end=end,
        urgency=choice(URGENCY_LEVELS),
    )


def generate_flight_payloads(
    num_flights: int,
    fetch_geography_batch: Callable[[], Any],
    fetch_gaza_area: Callable[[], dict[str, Any]],
) -> dict[str, object] | list[dict[str, object]]:
    if num_flights < 1:
        raise ValueError("num_flights must be at least 1")

    geography_batch = fetch_geography_batch()
    gaza_area_geojson = fetch_gaza_area()

    flights = [
        generate_single_flight_payload(
            geography_batch=geography_batch,
            gaza_area_geojson=gaza_area_geojson,
        )
        for _ in range(num_flights)
    ]

    if num_flights == 1:
        return flights[0]

    return flights
