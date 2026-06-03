import random
from typing import Any

from ..geo import bounding_box, extract_polygons, point_in_any_polygon
from .payload_builders import build_point_payload


def generate_random_allowed_point(
    allowed_region_geojson: dict[str, Any],
    blocked_polygons: Any,
    max_attempts: int = 5_000,
) -> dict[str, float]:
    allowed_polygons = extract_polygons(allowed_region_geojson)
    restricted_polygons = extract_polygons(blocked_polygons)

    if not allowed_polygons:
        raise ValueError("Allowed region GeoJSON does not contain any polygons")

    min_longitude, min_latitude, max_longitude, max_latitude = bounding_box(
        allowed_polygons
    )

    for _ in range(max_attempts):
        longitude = random.uniform(min_longitude, max_longitude)
        latitude = random.uniform(min_latitude, max_latitude)

        if not point_in_any_polygon(longitude, latitude, allowed_polygons):
            continue

        if point_in_any_polygon(longitude, latitude, restricted_polygons):
            continue

        return build_point_payload(latitude=latitude, longitude=longitude)

    raise RuntimeError(
        "Failed to generate a point inside the allowed region and outside "
        f"restricted polygons after {max_attempts} attempts"
    )
