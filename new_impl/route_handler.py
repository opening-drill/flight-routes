import json
from datetime import datetime, timedelta
from typing import Any

import config  # noqa: F401

from confluent_kafka import Message
from database import RedisDB
from flightRouteCalculator import GPSDronePathPlanner
from models import Coordinate, Flight

from config import SAFETY_BUFFER_METERS
from polygons import fetch_polygons, polygons_to_geojson


def _load_kafka_payload(msg: Message) -> dict[str, Any]:
    return json.loads(msg.value().decode("utf-8"))


def _coords_from_payload(payload: dict[str, Any]) -> tuple[tuple[float, float], tuple[float, float]]:
    start = (payload["start"]["latitude"], payload["start"]["longitude"])
    end = (payload["end"]["latitude"], payload["end"]["longitude"])
    return start, end


def _flight_from_route(
    payload: dict[str, Any],
    start: tuple[float, float],
    end: tuple[float, float],
    waypoints: list[tuple[float, float]],
) -> Flight:
    flight = Flight(
        start_point=Coordinate(lat=start[0], lng=start[1]),
        end_point=Coordinate(lat=end[0], lng=end[1]),
        average_speed_kmh=float(payload.get("speed_kmh", 100.0)),
        urgency_level=str(payload.get("urgency", "NORMAL")),
        flight_path=[Coordinate(lat=lat, lng=lng) for lat, lng in waypoints],
        eta=datetime.now() + timedelta(hours=1),
    )
    flight_id = payload.get("flight_id") or payload.get("aircraft_id")
    if flight_id:
        flight.flight_id = str(flight_id)
    return flight


def process_kafka_message(msg: Message, db: RedisDB, planner: GPSDronePathPlanner | None) -> GPSDronePathPlanner | None:
    """
    Calculate a flight route from a Kafka event and persist it to Redis.
    Returns an updated planner when polygons were refreshed.
    """
    payload = _load_kafka_payload(msg)
    start, end = _coords_from_payload(payload)

    polygons = get_polygons()
    geojson = polygons_to_geojson(polygons)
    if geojson["features"]:
        planner = GPSDronePathPlanner(geojson, safety_buffer_meters=SAFETY_BUFFER_METERS)

    if planner is None:
        raise RuntimeError("No no-fly polygons available; cannot plan a route.")

    print(
        f"\n[Consumer] event={payload.get('event_id')} aircraft={payload.get('aircraft_id')} "
        f"route {start} -> {end}"
    )

    waypoints = planner.plan_route(start_gps=start, goal_gps=end)
    flight = _flight_from_route(payload, start, end, waypoints)

    db.save_flight(flight)
    print(f"[Consumer] Saved flight {flight.flight_id} with {len(waypoints)} waypoints.")
    return planner
