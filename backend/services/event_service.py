from sqlalchemy.orm import Session
from models import db_models, schemas
from services.score_service import calculate_punctuality
from services.bus_dataset_service import normalize_plate

def process_detection(db: Session, detection: schemas.DetectionEvent):
    detection.plate_number = normalize_plate(detection.plate_number)
    print(f"[process_detection] Searching for bus with normalized plate: {detection.plate_number}")
    punctuality = calculate_punctuality(detection.timestamp)

    # 1. Find or create bus
    bus = db.query(db_models.Bus).filter(db_models.Bus.plate_number == detection.plate_number).first()
    print(f"[process_detection] Bus lookup result: {bus.id if bus else 'NOT FOUND'}")
    if not bus:
        bus = db_models.Bus(
            plate_number=detection.plate_number,
            bus_name=detection.bus_name,
            driver_name=detection.driver_name,
            route=detection.route
        )
        db.add(bus)
    else:
        # Update existing details if provided
        if detection.bus_name and detection.bus_name != "UNKNOWN":
            bus.bus_name = detection.bus_name
        if detection.driver_name and detection.driver_name != "UNKNOWN":
            bus.driver_name = detection.driver_name
        if detection.route and detection.route != "UNKNOWN":
            bus.route = detection.route

    db.commit()
    db.refresh(bus)
        
    # 2. Record event
    event = db_models.Event(
        bus_id=bus.id,
        camera_id=detection.camera_id,
        timestamp=detection.timestamp,
        event_type=punctuality["event_type"],
        confidence=detection.confidence
    )
    db.add(event)
    
    # 3. Update bus last seen and status
    bus.last_seen = detection.timestamp
    bus.current_status = punctuality["status"]
    
    db.commit()
    db.refresh(event)
    print(f"[process_detection] Created event with ID: {event.id}, bus_id: {event.bus_id}, type: {event.event_type}")
    return event
