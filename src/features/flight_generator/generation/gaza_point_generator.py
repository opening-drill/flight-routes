import random
from typing import Any

from ..geo import bounding_box, extract_polygons, point_in_any_polygon
from .payload_builders import build_point_payload


def generate_random_gaza_point(
    gaza_area_geojson: dict[str, Any],
    geography_batch: Any,
    max_attempts: int = 5_000,
) -> dict[str, float]:
    gaza_polygons = extract_polygons(gaza_area_geojson)
    blocked_polygons = extract_polygons(geography_batch)

    if not gaza_polygons:
        raise ValueError("Gaza area GeoJSON does not contain any polygons")

    min_longitude, min_latitude, max_longitude, max_latitude = bounding_box(
        gaza_polygons
    )

    for _ in range(max_attempts):
        longitude = random.uniform(min_longitude, max_longitude)
        latitude = random.uniform(min_latitude, max_latitude)

        if not point_in_any_polygon(longitude, latitude, gaza_polygons):
            continue

        if point_in_any_polygon(longitude, latitude, blocked_polygons):
            continue

        return build_point_payload(latitude=latitude, longitude=longitude)

    raise RuntimeError(
        "Failed to generate a Gaza point outside geography polygons "
        f"after {max_attempts} attempts"
    )
