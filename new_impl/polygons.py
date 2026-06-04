from typing import List

import config  # noqa: F401 — ensures .env paths before redis/db imports

import api_client
from database import RedisDB
from models import PolygonModel
CORE_BASE = "https://core-service-1015949672422.europe-west1.run.app"
API_KEY   = "adminkey123456789"   # from env CORE_API_KEY in real deploy

HEADERS = {
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY,          # ⚠️ REQUIRED on every protected route
}

def get_polygons():
    r = requests.get(f"{CORE_BASE}/api/polygons",
                     headers=HEADERS, params={"limit": 100, "page": 1}, timeout=10)
    r.raise_for_status()
    data = r.json()
    # shape: { "polygons": [ { id, name, zone, area/geojson:{type:'Polygon',coordinates:[[[lng,lat],...]]} } ] }
    return data.get("polygons", [])

def fetch_polygons(db: RedisDB) -> List[PolygonModel]:
    """Prefer API polygons; fall back to Redis when the API is unavailable."""
    polygons = api_client.get_all_polygons()
    if polygons:
        return polygons
    return db.get_all_polygons()


def polygons_to_geojson(polygons: List[PolygonModel]) -> dict:
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
