from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import db_models, schemas
from services.bus_dataset_service import normalize_plate

router = APIRouter()

@router.get("/", response_model=list[schemas.BusResponse])
def get_buses(db: Session = Depends(get_db)):
    buses = db.query(db_models.Bus).all()
    return buses

@router.get("/{bus_id}", response_model=schemas.BusResponse)
def get_bus(bus_id: int, db: Session = Depends(get_db)):
    bus = db.query(db_models.Bus).filter(db_models.Bus.id == bus_id).first()
    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return bus


@router.post("/", response_model=schemas.BusResponse)
def create_bus(bus_data: schemas.BusCreate, db: Session = Depends(get_db)):
    """Create a new bus entry with all available fields."""
    plate_number = normalize_plate(bus_data.plate_number)
    print(f"[POST /api/buses] Uploading new bus with plate: {bus_data.plate_number} (normalized: {plate_number})")
    
    if not plate_number:
        raise HTTPException(status_code=400, detail="Invalid plate number")

    existing = db.query(db_models.Bus).filter(db_models.Bus.plate_number == plate_number).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Bus with plate {plate_number} already exists")

    new_bus = db_models.Bus(
        plate_number=plate_number,
        bus_name=bus_data.bus_name,
        driver_name=bus_data.driver_name,
        mobile_number=bus_data.mobile_number,
        license_number=bus_data.license_number,
        years_of_experience=bus_data.years_of_experience,
        shift=bus_data.shift,
        bus_type=bus_data.bus_type,
        route=bus_data.route,
    )
    db.add(new_bus)
    db.commit()
    db.refresh(new_bus)
    print(f"[POST /api/buses] Created bus with ID: {new_bus.id}, plate: {new_bus.plate_number}")
    return new_bus
