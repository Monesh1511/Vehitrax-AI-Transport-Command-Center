from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import db_models, schemas
from services.event_service import process_detection
from ws.manager import manager

router = APIRouter()

@router.get("/", response_model=list[schemas.EventResponse])
def get_events(limit: int = 100, db: Session = Depends(get_db)):
    events = db.query(db_models.Event).order_by(db_models.Event.timestamp.desc()).limit(limit).all()
    return events

@router.post("/detection", response_model=schemas.EventResponse)
def create_detection_event(detection: schemas.DetectionEvent, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    event = process_detection(db, detection)
    
    event_data = schemas.EventResponse.model_validate(event).model_dump(mode="json")
    
    async def broadcast_event():
        await manager.broadcast({"type": "DETECTION", "data": event_data})
        
    background_tasks.add_task(broadcast_event)
    return event


@router.delete("/clear")
def clear_events(db: Session = Depends(get_db)):
    deleted = db.query(db_models.Event).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}
