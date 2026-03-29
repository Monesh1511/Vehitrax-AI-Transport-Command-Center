import csv
import os
import re
from sqlalchemy.orm import Session
from models import db_models


def normalize_plate(plate: str | None) -> str:
    if not plate:
        return ""
    return re.sub(r"[^A-Z0-9]", "", plate.upper())


def _build_dataset_path() -> str:
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(backend_dir)
    return os.path.join(root_dir, "ml", "bus_dataset.csv")


def seed_buses_from_dataset(db: Session) -> dict:
    dataset_path = _build_dataset_path()
    if not os.path.exists(dataset_path):
        return {"inserted": 0, "updated": 0, "skipped": 0, "message": f"Dataset not found: {dataset_path}"}

    inserted = 0
    updated = 0
    skipped = 0

    with open(dataset_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            raw_plate = (row.get("number_plate") or "").strip()
            plate_number = normalize_plate(raw_plate)
            if not plate_number:
                skipped += 1
                continue

            bus_name = (row.get("bus_number") or "").strip() or None
            driver_name = (row.get("driver_name") or "").strip() or None
            mobile_number = (row.get("mobile_number") or "").strip() or None
            license_number = (row.get("license_number") or "").strip() or None
            shift = (row.get("shift") or "").strip() or None
            bus_type = (row.get("bus_type") or "").strip() or None
            years_exp = row.get("years_of_experience")
            try:
                years_of_experience = int(years_exp) if years_exp else None
            except (ValueError, TypeError):
                years_of_experience = None

            route = " / ".join([item for item in [bus_type, shift] if item]) or None

            bus = db.query(db_models.Bus).filter(db_models.Bus.plate_number == plate_number).first()
            if bus is None:
                bus = db_models.Bus(
                    plate_number=plate_number,
                    bus_name=bus_name,
                    driver_name=driver_name,
                    mobile_number=mobile_number,
                    license_number=license_number,
                    years_of_experience=years_of_experience,
                    shift=shift,
                    bus_type=bus_type,
                    route=route,
                )
                db.add(bus)
                inserted += 1
                continue

            changed = False
            if bus_name and (not bus.bus_name or bus.bus_name == "UNKNOWN"):
                bus.bus_name = bus_name
                changed = True
            if driver_name and (not bus.driver_name or bus.driver_name == "UNKNOWN"):
                bus.driver_name = driver_name
                changed = True
            if mobile_number and (not bus.mobile_number or bus.mobile_number == "UNKNOWN"):
                bus.mobile_number = mobile_number
                changed = True
            if license_number and (not bus.license_number or bus.license_number == "UNKNOWN"):
                bus.license_number = license_number
                changed = True
            if years_of_experience and (not bus.years_of_experience):
                bus.years_of_experience = years_of_experience
                changed = True
            if shift and (not bus.shift or bus.shift == "UNKNOWN"):
                bus.shift = shift
                changed = True
            if bus_type and (not bus.bus_type or bus.bus_type == "UNKNOWN"):
                bus.bus_type = bus_type
                changed = True
            if route and (not bus.route or bus.route == "UNKNOWN"):
                bus.route = route
                changed = True

            if changed:
                updated += 1
            else:
                skipped += 1

    db.commit()
    return {"inserted": inserted, "updated": updated, "skipped": skipped, "message": f"Seeded from {dataset_path}"}
