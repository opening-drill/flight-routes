def build_point_payload(latitude: float, longitude: float) -> dict[str, float]:
    return {
        "latitude": latitude,
        "longitude": longitude,
    }


def build_flight_payload(
    event_id: int,
    aircraft_id: int,
    start: dict[str, float],
    end: dict[str, float],
    urgency: str,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "aircraft_id": aircraft_id,
        "start": start,
        "end": end,
        "urgency": urgency,
    }
