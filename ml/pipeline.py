import cv2
import os
import time
import requests
from detect import detect_objects
from ocr import extract_text

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
CAMERA_URL = os.getenv("CAMERA_URL", "0")
ENABLE_DISPLAY = os.getenv("ENABLE_DISPLAY", "False").lower() in ("true", "1", "yes")

def process_frame(frame):
    # Detect objects
    results = detect_objects(frame)
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Check if detection is a bus (class 5 in COCO)
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            if cls == 5 and conf > 0.5:
                # Mocked plate extraction and OCR for demonstration
                # In real app: crop frame based on box.xyxy and run extract_text(crop)
                plate_text = "ABC-1234"
                
                # Send to backend
                event_data = {
                    "plate_number": plate_text,
                    "camera_id": "cam_01",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "confidence": conf
                }
                try:
                    requests.post(f"{BACKEND_URL}/api/events/detection", json=event_data)
                except Exception as e:
                    print("Failed to send event:", e)

def main():
    # Attempt to use CAMERA_URL. If integer, treat as webcam source.
    source = int(CAMERA_URL) if CAMERA_URL.isdigit() else CAMERA_URL
    cap = cv2.VideoCapture(source)
    
    print(f"Started pipeline reading from: {source}")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        process_frame(frame)
        
        if ENABLE_DISPLAY:
            # Display the frame to the user
            cv2.imshow("Vehitrax AI Camera Feed", frame)
            
            # Wait 1000 ms (1 second) and allow quitting by pressing 'q'
            if cv2.waitKey(1000) & 0xFF == ord('q'):
                break
        else:
            time.sleep(1)
            
    cap.release()
    if ENABLE_DISPLAY:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
