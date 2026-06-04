import os
from typing import List

import requests

from models import GeoJsonPolygon, PolygonModel

CORE_BASE = os.getenv(
    "CORE_BASE_URL",
    "https://core-service-1015949672422.europe-west1.run.app",
)
API_URL = os.getenv(
    "POLYGONS_API_URL",
    f"{CORE_BASE.rstrip('/')}/api/polygons",
)


def _api_key() -> str:
    return (
        os.getenv("CORE_API_KEY")
        or os.getenv("POLYGONS_API_KEY")
        or "adminkey123456789"
    )


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Api-Key": _api_key(),
    }

def dispatch() -> dict | None:
    """Trigger Core dispatch (`GET /api/dispatch`)."""
    try:
        response = requests.get(
            f"{CORE_BASE.rstrip('/')}/api/dispatch",
            headers=_headers(),
            params={"limit": 100, "page": 1},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to call dispatch API: {e}")
        return None


def get_all_polygons() -> List[PolygonModel]:
    """Fetch no-fly polygons from Core (`GET /api/polygons`)."""
    try:
        response = requests.get(
            API_URL,
            headers=_headers(),
            params={"limit": 100, "page": 1},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        polygons = []
        for poly_data in data.get("polygons", []):
            try:
                area = poly_data.get("geojson") or poly_data.get("area") or {}
                polygon = PolygonModel(
                    name=poly_data.get("name", "Unknown"),
                    geojson=GeoJsonPolygon(
                        type=area.get("type", "Polygon"),
                        coordinates=area.get("coordinates", []),
                    ),
                    zone=poly_data.get("zone", "UNKNOWN"),
                    state_duration=poly_data.get("state_duartion", 0),
                )
                polygons.append(polygon)
            except Exception as e:
                print(f"Error parsing polygon {poly_data.get('id')}: {e}")

        return polygons
    except requests.RequestException as e:
        print(f"Failed to fetch polygons from API: {e}")
        return []
