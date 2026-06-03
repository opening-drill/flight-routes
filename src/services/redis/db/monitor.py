import time
from database import RedisDB
import api_client
from flight_service import validate_and_fix_existing_flight

def run_monitor(interval_seconds: int = 30):
    """
    תסריט רץ ברקע (Daemon) שדוגם את הרדיס ואת ה-API כל 30 שניות, 
    כדי לזהות מסלולי טיסה שמתנגשים עם פוליגונים חדשים ולעדכן אותם דינמית.
    """
    print(f"Starting flight monitor... polling every {interval_seconds} seconds.")
    db = RedisDB()
    
    while True:
        try:
            print("\n[Monitor] Fetching latest polygons from API...")
            polygons = api_client.get_all_polygons()
            
            print("[Monitor] Fetching all active flights from Redis...")
            flights = db.get_all_flights()
            
            updates = 0
            for flight in flights:
                # בודק האם המסלול הקיים בעייתי, ומתקן במקרה הצורך
                was_fixed = validate_and_fix_existing_flight(flight, polygons)
                if was_fixed:
                    print(f"[Monitor] Saving updated flight {flight.flight_id} to Redis...")
                    db.save_flight(flight)
                    updates += 1
            
            print(f"[Monitor] Scan complete. {len(flights)} flights checked, {updates} updated.")
            
        except Exception as e:
            print(f"[Monitor] Error during polling cycle: {e}")
            
        print(f"[Monitor] Sleeping for {interval_seconds} seconds...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_monitor()
