from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import base64
import io
from PIL import Image
from services.scanner_service import scanner_service
from services.event_service import process_detection
from database import get_db
from models import schemas
from ws.manager import manager

router = APIRouter()


class ScanRequest(BaseModel):
    image: str  # Base64 encoded image


class ScanResponse(BaseModel):
    plates: list
    total_detected: int
    error: Optional[str] = None


@router.post("/scan", response_model=ScanResponse)
async def scan_image(image: UploadFile = File(...)):
    """
    Upload an image for plate scanning.
    Accepts image files (jpg, png, etc.)
    """
    try:
        # Read image data
        image_data = await image.read()

        # Scan for plates
        result = scanner_service.scan_image(image_data)

        if "error" in result:
            return ScanResponse(plates=[], total_detected=0, error=result["error"])

        return ScanResponse(
            plates=result.get("plates", []),
            total_detected=result.get("total_detected", 0),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-base64", response_model=ScanResponse)
async def scan_base64(request: ScanRequest):
    """
    Scan a base64 encoded image for plates.
    """
    try:
        result = scanner_service.scan_base64_image(request.image)

        if "error" in result:
            return ScanResponse(plates=[], total_detected=0, error=result["error"])

        return ScanResponse(
            plates=result.get("plates", []),
            total_detected=result.get("total_detected", 0),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-and-save")
async def scan_and_save(
    background_tasks: BackgroundTasks,
    image: UploadFile | None = File(default=None),
    request: ScanRequest | None = Body(default=None),
    db=Depends(get_db),
):
    """
    Scan an image and automatically save detected plates to database.
    """
    try:
        if image is not None:
            image_data = await image.read()
            result = scanner_service.scan_image(image_data)
        elif request is not None:
            result = scanner_service.scan_base64_image(request.image)
        else:
            raise HTTPException(status_code=400, detail="Provide either multipart image or base64 image")

        if "error" in result:
            return {"error": result["error"]}

        saved_plates = []
        for plate in result.get("plates", []):
            try:
                # Create detection event
                detection = schemas.DetectionEvent(
                    plate_number=plate["plate_number"],
                    camera_id="upload_scanner",
                    timestamp=plate["timestamp"],
                    confidence=plate["confidence"],
                )
                event = process_detection(db, detection)

                event_data = schemas.EventResponse.model_validate(event).model_dump(mode="json")
                event_data["detected_plate"] = plate["plate_number"]
                print(f"[scan-and-save] Broadcasting event with bus_id={event_data.get('bus_id')}, plate={plate['plate_number']}")

                async def broadcast_event(payload: dict):
                    await manager.broadcast({"type": "DETECTION", "data": payload})

                background_tasks.add_task(broadcast_event, event_data)

                saved_plates.append(
                    {
                        "plate_number": plate["plate_number"],
                        "event_id": event.id,
                        "bus_id": event.bus_id,
                        "confidence": plate["confidence"],
                    }
                )
            except Exception as e:
                print(f"Error saving plate {plate['plate_number']}: {e}")

        return {
            "scanned": result.get("total_detected", 0),
            "saved": len(saved_plates),
            "plates": saved_plates,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
