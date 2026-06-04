"""
Plan B entry point:
  1. Call Core dispatch API
  2. Consume Kafka route events
  3. Enrich each message with the full planned coordinates array
  4. Persist enriched payload to Redis
"""

from __future__ import annotations

import json
import logging
import math
import sys
from typing import Any

import new_impl.config  # noqa: F401 — loads .env, paths, and API env

from flightRouteCalculator import GPSDronePathPlanner
from database import RedisDB
from models import PolygonModel
from src.services.kafka import main_kafka
import api_client
from new_impl.config import settings


def polygons_to_geojson(polygons: list[PolygonModel]) -> dict:
    features = []
    for polygon in polygons:
        if not polygon.geojson.coordinates:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {"name": polygon.name, "zone": polygon.zone},
                "geometry": {
                    "type": polygon.geojson.type,
                    "coordinates": polygon.geojson.coordinates,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}

logger = logging.getLogger("PlanB")

_planner: GPSDronePathPlanner | None = None
_db: RedisDB | None = None

_TRACKING_INTERVAL_METERS = 20.0
_EARTH_RADIUS_M = 6_371_000


def _coords_array(waypoints: list[tuple[float, float]]) -> list[dict[str, float]]:
    return [{"latitude": lat, "longitude": lng} for lat, lng in waypoints]


def _load_kafka_payload(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    payload: Any = json.loads(value)
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object, got {type(payload).__name__}")
    nested = payload.get("payload") or payload.get("data")
    if isinstance(nested, str):
        nested = json.loads(nested)
    if isinstance(nested, dict):
        payload = nested
    route = payload.get("route")
    if isinstance(route, dict):
        payload = {**payload, **route}
    return payload


def _normalize_point(point: Any) -> dict[str, float]:
    """Canonical {latitude, longitude} from supported point shapes."""
    if not isinstance(point, dict):
        raise ValueError(f"Expected point object, got {type(point).__name__}")

    if "latitude" in point and "longitude" in point:
        return {"latitude": float(point["latitude"]), "longitude": float(point["longitude"])}

    if "lat" in point:
        lng = point.get("longitude", point.get("lng", point.get("lon")))
        if lng is not None:
            return {"latitude": float(point["lat"]), "longitude": float(lng)}

    coords = point.get("coordinates")
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        # GeoJSON Point: [longitude, latitude]
        return {"latitude": float(coords[1]), "longitude": float(coords[0])}

    raise ValueError(f"Unsupported point format: {point!r}")


def _route_endpoints(
    payload: dict[str, Any],
) -> tuple[tuple[float, float], tuple[float, float], dict[str, float], dict[str, float]]:
    for start_key, end_key in (("start", "end"), ("origin", "target")):
        if start_key in payload and end_key in payload:
            start_obj = _normalize_point(payload[start_key])
            end_obj = _normalize_point(payload[end_key])
            start_gps = (start_obj["latitude"], start_obj["longitude"])
            end_gps = (end_obj["latitude"], end_obj["longitude"])
            return start_gps, end_gps, start_obj, end_obj

    raise ValueError(
        "Route event must include start/end with latitude & longitude "
        f"(keys present: {list(payload.keys())})"
    )


def _haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def _direct_route(
    start: tuple[float, float],
    end: tuple[float, float],
    interval_meters: float = _TRACKING_INTERVAL_METERS,
) -> list[tuple[float, float]]:
    """Straight A→Z path (start to end) with points every *interval_meters*."""
    distance = _haversine_m(start, end)
    if distance <= interval_meters:
        return [start, end]

    segments = max(1, int(distance // interval_meters))
    return [
        (
            start[0] + (i / segments) * (end[0] - start[0]),
            start[1] + (i / segments) * (end[1] - start[1]),
        )
        for i in range(segments + 1)
    ]


def _compute_waypoints(
    start: tuple[float, float],
    end: tuple[float, float],
) -> list[tuple[float, float]]:
    global _planner

    polygons = api_client.get_all_polygons()
    geojson = polygons_to_geojson(polygons)
    if not geojson["features"]:
        logger.info("No no-fly polygons available; using direct A-Z route (no planner)")
        return _direct_route(start, end)

    _planner = GPSDronePathPlanner(
        geojson,
        safety_buffer_meters=settings.safety_buffer_meters,
    )
    return _planner.plan_route(start_gps=start, goal_gps=end)


def _flight_id_from_payload(payload: dict[str, Any]) -> str:
    for key in ("flight_id", "aircraft_id", "event_id"):
        value = payload.get(key)
        if value:
            return str(value)
    return "unknown"


def _save_to_redis(db: RedisDB, payload: dict[str, Any]) -> None:
    record_id = _flight_id_from_payload(payload)
    raw_key = f"flight_raw:{record_id}"
    db.r.set(raw_key, json.dumps(payload))
    logger.info("Saved enriched raw payload to Redis key %s", raw_key)


def process_flight_message(key: str | None, value: str | None) -> None:
    del key  # unused
    logger.info("Processing Kafka message")

    try:
        raw_data = _load_kafka_payload(value)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("Skipping invalid Kafka payload: %s", exc)
        return

    try:
        start, end, start_obj, end_obj = _route_endpoints(raw_data)
    except ValueError as exc:
        logger.warning("Skipping non-route Kafka message: %s", exc)
        return

    # Keep canonical start/end on the stored payload (matches Kafka contract).
    raw_data["start"] = start_obj
    raw_data["end"] = end_obj

    waypoints = _compute_waypoints(start, end)

    raw_data["coordinates"] = _coords_array(waypoints)

    db = _db
    if db is None:
        raise RuntimeError("Redis client not initialized")

    _save_to_redis(db, raw_data)

    logger.info(
        "Route planned for event=%s aircraft=%s (%d coordinates)",
        raw_data.get("event_id"),
        raw_data.get("aircraft_id"),
        len(waypoints),
    )


def main() -> None:
    global _db

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    logger.info("Calling Core dispatch API...")
    _db = RedisDB(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
    )

    logger.info("Starting Kafka consumer on topic %s", settings.kafka_topic)
    main_kafka(process_flight_message)


if __name__ == "__main__":
    main()
