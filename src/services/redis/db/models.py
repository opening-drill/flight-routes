from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class Coordinate(BaseModel):
    lat: float
    lng: float

class Flight(BaseModel):
    flight_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="מזהה ייחודי לטיסה")
    start_point: Coordinate = Field(description="נקודת התחלה")
    end_point: Coordinate = Field(description="נקודת סיום")
    average_speed_kmh: float = Field(description="מהירות ממוצעת")
    flight_path: List[Coordinate] = Field(default=[], description="מסלול הטיסה")
    urgency_level: str = Field(description="רמת דחיפות")
    current_location: Optional[Coordinate] = Field(default=None, description="מיקום נוכחי")
    eta: datetime = Field(description="שעת הגעה ליעד")

    def model_post_init(self, __context) -> None:
        # Default current_location to start_point if not provided
        if self.current_location is None:
            self.current_location = self.start_point
