import json
import re
from datetime import datetime, timedelta
from typing import Optional, List

import redis

from models import Coordinate, Flight, PolygonModel


def _repair_python_json_literals(raw: str) -> str:
    """Redis entries edited by hand may use Python None/True/False instead of JSON."""
    raw = re.sub(r"\bNone\b", "null", raw)
    raw = re.sub(r"\bTrue\b", "true", raw)
    raw = re.sub(r"\bFalse\b", "false", raw)
    return raw


def _normalize_eta(value) -> datetime:
    """Accept ISO datetimes or legacy time-only strings like '10:34:07'."""
    if value is None:
        return datetime.now() + timedelta(hours=1)
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return datetime.now() + timedelta(hours=1)
        time_only = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", value)
        if time_only:
            hour, minute, second = (
                int(time_only.group(1)),
                int(time_only.group(2)),
                int(time_only.group(3) or 0),
            )
            today = datetime.now().date()
            return datetime(today.year, today.month, today.day, hour, minute, second)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now() + timedelta(hours=1)


def _coerce_flight_data(data: dict) -> dict:
    coerced = dict(data)
    coerced["eta"] = _normalize_eta(coerced.get("eta"))
    return coerced

class RedisDB:
    def __init__(self, host: str = '127.0.0.1', port: int = 6379, db: int = 0):
        # מתחבר לשרת Redis. בברירת מחדל מתחבר ל-localhost על יציאה 6379.
        # מושלם לשימוש עם Redis Insight.
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
    
    def _get_key(self, flight_id: str) -> str:
        return f"flight:{flight_id}"

    def save_flight(self, flight: Flight) -> None:
        """שומר או מעדכן את הרשומת הטיסה ברדיס בפורמט JSON"""
        flight_json = flight.model_dump_json()
        self.r.set(self._get_key(flight.flight_id), flight_json)
        print(f"Flight {flight.flight_id} saved successfully to Redis.")

    def _parse_flight_json(self, flight_json: str, redis_key: str) -> Optional[Flight]:
        try:
            data = json.loads(_repair_python_json_literals(flight_json))
            flight = Flight.model_validate(_coerce_flight_data(data))
            repaired_json = flight.model_dump_json()
            if repaired_json != flight_json:
                self.r.set(redis_key, repaired_json)
                print(f"Repaired flight record {flight.flight_id}")
            return flight
        except Exception as exc:
            flight_id = redis_key.removeprefix("flight:")
            print(f"Skipping corrupt flight {flight_id}: {exc}")
            return None

    def get_flight(self, flight_id: str) -> Optional[Flight]:
        """שולף רשומת טיסה מהרדיס לפי ID"""
        redis_key = self._get_key(flight_id)
        flight_json = self.r.get(redis_key)
        if flight_json:
            return self._parse_flight_json(flight_json, redis_key)
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
            if not flight_json:
                continue
            flight = self._parse_flight_json(flight_json, key)
            if flight is not None:
                flights.append(flight)
        return flights

    def update_flight_location(self, flight_id: str, new_lat: float, new_lng: float) -> Optional[Flight]:
        """מעדכן מיקום נוכחי ומוסיף את המיקום למסלול (example logic)"""
        flight = self.get_flight(flight_id)
        if flight:
            new_coord = Coordinate(lat=new_lat, lng=new_lng)
            flight.current_location = new_coord
            flight.flight_path.append(new_coord)
            self.save_flight(flight)
            return flight
        return None

    def _get_polygon_key(self, name: str) -> str:
        return f"polygon:{name}"

    def save_polygon(self, polygon: PolygonModel) -> None:
        """שומר או מעדכן פוליגון ברדיס בפורמט JSON"""
        polygon_json = polygon.model_dump_json()
        self.r.set(self._get_polygon_key(polygon.name), polygon_json)
        print(f"Polygon {polygon.name} saved successfully to Redis.")

    def get_polygon(self, name: str) -> Optional[PolygonModel]:
        """שולף פוליגון מהרדיס לפי שם"""
        polygon_json = self.r.get(self._get_polygon_key(name))
        if polygon_json:
            return PolygonModel.model_validate_json(polygon_json)
        return None

    def delete_polygon(self, name: str) -> bool:
        """מוחק פוליגון"""
        result = self.r.delete(self._get_polygon_key(name))
        return result > 0

    def get_all_polygons(self) -> List[PolygonModel]:
        """שולף את כל הפוליגונים שיש ב-DB"""
        keys = self.r.keys("polygon:*")
        polygons = []
        for key in keys:
            polygon_json = self.r.get(key)
            if polygon_json:
                polygons.append(PolygonModel.model_validate_json(polygon_json))
        return polygons
