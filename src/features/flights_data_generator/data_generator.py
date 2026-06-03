from typing import Any, Callable

from .generation import generate_flight_payloads


def generate_flight_data(
    num_flights: int,
    next_event_id: Callable[[], int],
    get_random_free_aircraft_id: Callable[[], int],
    allowed_region_geojson: dict[str, Any],
    blocked_polygons: Any,
) -> dict[str, object] | list[dict[str, object]]:
    return generate_flight_payloads(
        num_flights=num_flights,
        next_event_id=next_event_id,
        get_random_free_aircraft_id=get_random_free_aircraft_id,
        allowed_region_geojson=allowed_region_geojson,
        blocked_polygons=blocked_polygons,
    )
