from random import choice
from typing import Any, Callable

from ..config import URGENCY_LEVELS
from .allowed_point_generator import generate_random_allowed_point
from .payload_builders import build_flight_payload


def generate_single_flight_payload(
    event_id: int,
    aircraft_id: int,
    allowed_region_geojson: dict[str, Any],
    blocked_polygons: Any,
) -> dict[str, object]:
    start = generate_random_allowed_point(
        allowed_region_geojson=allowed_region_geojson,
        blocked_polygons=blocked_polygons,
    )
    end = generate_random_allowed_point(
        allowed_region_geojson=allowed_region_geojson,
        blocked_polygons=blocked_polygons,
    )

    while start == end:
        end = generate_random_allowed_point(
            allowed_region_geojson=allowed_region_geojson,
            blocked_polygons=blocked_polygons,
        )

    return build_flight_payload(
        event_id=event_id,
        aircraft_id=aircraft_id,
        start=start,
        end=end,
        urgency=choice(URGENCY_LEVELS),
    )


def generate_flight_payloads(
    num_flights: int,
    next_event_id: Callable[[], int],
    get_random_free_aircraft_id: Callable[[], int],
    allowed_region_geojson: dict[str, Any],
    blocked_polygons: Any,
) -> dict[str, object] | list[dict[str, object]]:
    if num_flights < 1:
        raise ValueError("num_flights must be at least 1")

    flights = [
        generate_single_flight_payload(
            event_id=next_event_id(),
            aircraft_id=get_random_free_aircraft_id(),
            allowed_region_geojson=allowed_region_geojson,
            blocked_polygons=blocked_polygons,
        )
        for _ in range(num_flights)
    ]

    if num_flights == 1:
        return flights[0]

    return flights
