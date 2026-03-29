from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String, unique=True, index=True)
    bus_name = Column(String, nullable=True)
    driver_name = Column(String, nullable=True)
    mobile_number = Column(String, nullable=True)
    license_number = Column(String, nullable=True)
    years_of_experience = Column(Integer, nullable=True)
    shift = Column(String, nullable=True)
    bus_type = Column(String, nullable=True)
    route = Column(String, nullable=True)
    current_status = Column(String, default="Unknown") # On Time, Delayed, Enter, Exit
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    
class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    bus_id = Column(Integer, ForeignKey("buses.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    camera_id = Column(String)
    event_type = Column(String) # ENTRY, EXIT
    confidence = Column(Float)
    
    bus = relationship("Bus")
