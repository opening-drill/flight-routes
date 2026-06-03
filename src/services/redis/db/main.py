from database import RedisDB
from models import Flight, Coordinate
from datetime import datetime, timedelta

def main():
    # 1. חיבור ל-Redis
    # ודאי שיש לך שרת Redis פועל ברקע (על פורט 6379 כדי להתחבר ב-Redis Insight)
    db = RedisDB()

    # 2. יצירת אובייקט טיסה חדש (לפי השדות שביקשת)
    start = Coordinate(lat=32.0853, lng=34.7818) # תל אביב לדוגמה
    end = Coordinate(lat=31.7683, lng=35.2137)   # ירושלים לדוגמה
    
    new_flight = Flight(
        start_point=start,
        end_point=end,
        average_speed_kmh=120.5,
        urgency_level="HIGH",
        flight_path=[start], # מתחילים עם הנקודה הראשונה במסלול
        eta=datetime.now() + timedelta(hours=1)
    )

    # 3. שמירת הטיסה ל-Redis
    print("Saving new flight...")
    db.save_flight(new_flight)

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

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Make sure your Redis server is running locally on port 6379.")
