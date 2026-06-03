import redis
import json
from typing import Optional, List
from models import Flight

class RedisDB:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        # מתחבר לשרת Redis. בברירת מחדל מתחבר ל-localhost על יציאה 6379.
        # מושלם לשימוש עם Redis Insight.
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    
    def _get_key(self, flight_id: str) -> str:
        return f"flight:{flight_id}"

    def save_flight(self, flight: Flight) -> None:
        """שומר או מעדכן את הרשומת הטיסה ברדיס בפורמט JSON"""
        # המרת אובייקט Pydantic ל-JSON string
        flight_json = flight.model_dump_json()
        self.r.set(self._get_key(flight.flight_id), flight_json)
        print(f"Flight {flight.flight_id} saved successfully to Redis.")

    def get_flight(self, flight_id: str) -> Optional[Flight]:
        """שולף רשומת טיסה מהרדיס לפי ID"""
        flight_json = self.r.get(self._get_key(flight_id))
        if flight_json:
            # המרה חזרה מ-JSON לאובייקט Pydantic
            return Flight.model_validate_json(flight_json)
        return None

    def delete_flight(self, flight_id: str) -> bool:
        """מוחק אובייקט טיסה"""
        result = self.r.delete(self._get_key(flight_id))
        return result > 0

    def get_all_flights(self) -> List[Flight]:
        """שולף את כל הטיסות שיש ב-DB"""
        keys = self.r.keys("flight:*")
        flights = []
        for key in keys:
            flight_json = self.r.get(key)
            if flight_json:
                flights.append(Flight.model_validate_json(flight_json))
        return flights

    def update_flight_location(self, flight_id: str, new_lat: float, new_lng: float) -> Optional[Flight]:
        """מעדכן מיקום נוכחי ומוסיף את המיקום למסלול (example logic)"""
        flight = self.get_flight(flight_id)
        if flight:
            new_coord = {"lat": new_lat, "lng": new_lng}
            flight.current_location = new_coord
            flight.flight_path.append(new_coord)
            self.save_flight(flight)
            return flight
        return None
