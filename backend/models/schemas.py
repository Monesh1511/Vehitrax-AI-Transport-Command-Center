from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DetectionEvent(BaseModel):
    plate_number: str
    camera_id: str
    timestamp: datetime
    confidence: float
    bus_name: Optional[str] = None
    driver_name: Optional[str] = None
    route: Optional[str] = None
    
class BusCreate(BaseModel):
    plate_number: str
    bus_name: Optional[str] = None
    driver_name: Optional[str] = None
    mobile_number: Optional[str] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[int] = None
    shift: Optional[str] = None
    bus_type: Optional[str] = None
    route: Optional[str] = None

class BusResponse(BaseModel):
    id: int
    plate_number: str
    bus_name: Optional[str] = None
    driver_name: Optional[str] = None
    mobile_number: Optional[str] = None
    license_number: Optional[str] = None
    years_of_experience: Optional[int] = None
    shift: Optional[str] = None
    bus_type: Optional[str] = None
    route: Optional[str] = None
    current_status: str
    last_seen: datetime

    class Config:
        from_attributes = True

class EventResponse(BaseModel):
    id: int
    bus_id: int
    timestamp: datetime
    camera_id: str
    event_type: str
    confidence: float

    class Config:
        from_attributes = True
