from typing import List
from datetime import datetime, timedelta
from shapely.geometry import LineString, Polygon as ShapelyPolygon
import math

from models import Coordinate, PolygonModel, Flight
from database import RedisDB
import api_client

def check_and_update_route(start: Coordinate, end: Coordinate, polygons: List[PolygonModel]) -> List[Coordinate]:
    """
    בודק האם יש התנגשות בין מסלול הטיסה הישיר לפוליגונים.
    אם יש התנגשות, מעדכן את המסלול ומוסיף נקודות ציון כדי לעקוף את הפוליגון.
    """
    direct_line = LineString([(start.lng, start.lat), (end.lng, end.lat)])
    
    shapely_polygons = []
    for p in polygons:
        if p.geojson.coordinates and len(p.geojson.coordinates) > 0:
            exterior_coords = p.geojson.coordinates[0]
            if len(exterior_coords) >= 3:
                shapely_polygons.append(ShapelyPolygon(exterior_coords))
    
    # בדיקת התנגשויות
    intersected_polygons = [sp for sp in shapely_polygons if direct_line.intersects(sp)]
    
    if not intersected_polygons:
        # אם אין התנגשות, מחזירים את המסלול הישיר
        return [start, end]
    
    # אם יש התנגשות, מנתבים מסביב למלבן החוסם של הפוליגון הראשון (Bounding Box)
    obs = intersected_polygons[0]
    minx, miny, maxx, maxy = obs.bounds 
    
    buffer = 0.05 
    safe_points = [
        (minx - buffer, miny - buffer),
        (minx - buffer, maxy + buffer),
        (maxx + buffer, maxy + buffer),
        (maxx + buffer, miny - buffer)
    ]
    
    # מציאת הנקודות הקרובות ביותר כדי לבנות את העקיפה
    safe_points.sort(key=lambda p: math.dist(p, (start.lng, start.lat)))
    p1 = safe_points[0] 
    
    remaining = safe_points[1:]
    remaining.sort(key=lambda p: math.dist(p, (end.lng, end.lat)))
    p2 = remaining[0] 
    
    # המסלול המעודכן
    return [
        start,
        Coordinate(lat=p1[1], lng=p1[0]),
        Coordinate(lat=p2[1], lng=p2[0]),
        end
    ]

def create_new_flight(db: RedisDB, start: Coordinate, end: Coordinate, speed: float, urgency: str) -> Flight:
    """
    יוצר טיסה חדשה.
    מושך פוליגונים, מפעיל את פונקציית הבדיקה והעדכון (check_and_update_route), ושומר ברדיס.
    """
    print("Fetching polygons from API...")
    polygons = api_client.get_all_polygons()
    print(f"Fetched {len(polygons)} polygons.")

    print("Checking and updating safe flight path...")
    safe_path = check_and_update_route(start, end, polygons)
    print(f"Final path has {len(safe_path)} waypoints.")

    new_flight = Flight(
        start_point=start,
        end_point=end,
        average_speed_kmh=speed,
        urgency_level=urgency,
        flight_path=safe_path,
        eta=datetime.now() + timedelta(hours=1)
    )

    print("Saving new flight to Redis...")
    db.save_flight(new_flight)
    return new_flight


def validate_and_fix_existing_flight(flight: Flight, polygons: List[PolygonModel]) -> bool:
    """
    בודק האם נתיב הטיסה הקיים (מהמיקום הנוכחי ליעד) מתנגש עם פוליגונים, ומעדכן אותו אם כן.
    מחשב מסלול חדש ומחזיר True אם המסלול עודכן, אחרת False.
    """
    if flight.current_location is None:
        return False
        
    start = flight.current_location
    end = flight.end_point
    
    # יצירת קו ישיר לבדיקת התנגשות
    direct_line = LineString([(start.lng, start.lat), (end.lng, end.lat)])
    
    shapely_polygons = []
    for p in polygons:
        if p.geojson.coordinates and len(p.geojson.coordinates) > 0:
            exterior_coords = p.geojson.coordinates[0]
            if len(exterior_coords) >= 3:
                shapely_polygons.append(ShapelyPolygon(exterior_coords))
                
    intersected_polygons = [sp for sp in shapely_polygons if direct_line.intersects(sp)]
    
    if not intersected_polygons:
        return False
        
    print(f"Collision detected for flight {flight.flight_id}! Recalculating route...")
    
    # חישוב מסלול מחדש מהמיקום הנוכחי
    new_safe_path = check_and_update_route(start, end, polygons)
    
    # עדכון מסלול הטיסה
    flight.flight_path = new_safe_path
    return True
