from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import db_models
from services.score_service import calculate_punctuality

router = APIRouter()

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    total_buses = db.query(db_models.Bus).count()
    total_events = db.query(db_models.Event).count()
    
    on_time = db.query(db_models.Bus).filter(db_models.Bus.current_status == "On Time").count()
    delayed = db.query(db_models.Bus).filter(db_models.Bus.current_status == "Delayed").count()
    
    return {
        "total_buses": total_buses,
        "total_events": total_events,
        "on_time": on_time,
        "delayed": delayed
    }


@router.get("/events")
def get_event_reports(limit: int = 100, db: Session = Depends(get_db)):
    events = db.query(db_models.Event).order_by(db_models.Event.timestamp.desc()).limit(limit).all()
    result = []

    for event in events:
        timing = calculate_punctuality(event.timestamp)
        bus = event.bus
        result.append(
            {
                "event_id": event.id,
                "plate_number": bus.plate_number if bus else "UNKNOWN",
                "bus_number": bus.bus_name if bus and bus.bus_name else "UNKNOWN",
                "driver_name": bus.driver_name if bus and bus.driver_name else "UNKNOWN",
                "status": timing["status"],
                "score": timing["score"],
                "time": event.timestamp.strftime("%I:%M:%S %p"),
                "date": event.timestamp.strftime("%Y-%m-%d"),
                "day": event.timestamp.strftime("%A"),
                "confidence": event.confidence,
                "camera_id": event.camera_id,
            }
        )

    return {
        "college_start": "09:00 AM",
        "college_end": "04:10 PM",
        "events": result,
    }
