import requests
from typing import List
from models import PolygonModel, GeoJsonPolygon

API_URL = "https://666skt42-3000.uks1.devtunnels.ms/polygons/get_api_polygons"

def get_all_polygons() -> List[PolygonModel]:
    """
    Fetches polygons from the external API and maps them to PolygonModel.
    """
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        
        polygons = []
        for poly_data in data.get("polygons", []):
            try:
                # ממרים את השדות מה-API (כמו area ו-state_duartion) למודל שלנו
                polygon = PolygonModel(
                    name=poly_data.get("name", "Unknown"),
                    geojson=GeoJsonPolygon(
                        type=poly_data.get("area", {}).get("type", "Polygon"),
                        coordinates=poly_data.get("area", {}).get("coordinates", [])
                    ),
                    zone=poly_data.get("zone", "UNKNOWN"),
                    # שים לב לשגיאת הכתיב בשדה state_duartion שמגיע מה-API
                    state_duration=poly_data.get("state_duartion", 0) 
                )
                polygons.append(polygon)
            except Exception as e:
                print(f"Error parsing polygon {poly_data.get('id')}: {e}")
                
        return polygons
    except requests.RequestException as e:
        print(f"Failed to fetch polygons from API: {e}")
        return []
