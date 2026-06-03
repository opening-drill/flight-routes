from database import RedisDB
from models import Flight, Coordinate, PolygonModel, GeoJsonPolygon
from datetime import datetime, timedelta
import api_client
from flight_service import create_new_flight


def main():
    # 1. חיבור ל-Redis
    db = RedisDB()

    # 2. שימוש בפונקציה ליצירת טיסה
    start = Coordinate(lat=32.0853, lng=34.7818) # תל אביב
    end = Coordinate(lat=31.7683, lng=35.2137)   # ירושלים
    
    new_flight = create_new_flight(db, start, end, speed=120.5, urgency="HIGH")

    # 4. שליפת הטיסה חזרה כדי לוודא שינויים
    print("\nFetching flight from Redis...")
    fetched_flight = db.get_flight(new_flight.flight_id)
    if fetched_flight:
        print(f"Fetched ID: {fetched_flight.flight_id}")
        print(f"Current Location: lat={fetched_flight.current_location.lat}, lng={fetched_flight.current_location.lng}")
        print(f"ETA: {fetched_flight.eta}")

    # 5. עדכון מיקום
    print("\nUpdating flight location...")
    db.update_flight_location(new_flight.flight_id, 31.9, 34.9)
    
    updated_flight = db.get_flight(new_flight.flight_id)
    print(f"Updated Location: lat={updated_flight.current_location.lat}, lng={updated_flight.current_location.lng}")
    print(f"Path length: {len(updated_flight.flight_path)}")

    # 6. יצירת ושמירת פוליגון
    print("\nCreating and saving a polygon...")
    polygon = PolygonModel(
        name="test_polygon",
        geojson=GeoJsonPolygon(
            type="Polygon",
            coordinates=[[[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [0.0, 0.0]]]
        ),
        zone="GAZA_SOUTH",
        state_duration=0
    )
    db.save_polygon(polygon)

    # 7. שליפת פוליגון
    print("\nFetching polygon from Redis...")
    fetched_polygon = db.get_polygon("test_polygon")
    if fetched_polygon:
        print(f"Fetched Polygon: {fetched_polygon.name}, Zone: {fetched_polygon.zone}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure your Redis server is running locally on port 6379.")
