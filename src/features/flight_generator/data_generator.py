from typing import Any, Callable

from .generation import generate_flight_payloads


def generate_flight_data(
    num_flights: int,
    fetch_geography_batch: Callable[[], Any],
    fetch_gaza_area: Callable[[], dict[str, Any]],
) -> dict[str, object] | list[dict[str, object]]:
    return generate_flight_payloads(
        num_flights=num_flights,
        fetch_geography_batch=fetch_geography_batch,
        fetch_gaza_area=fetch_gaza_area,
    )
