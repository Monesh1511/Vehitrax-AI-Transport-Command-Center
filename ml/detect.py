from ultralytics import YOLO

# Load the YOLO model (using YOLOv8 nano as placeholder since v11 API is consistent)
model = YOLO('yolov8n.pt') 

def detect_objects(frame):
    """
    Run YOLO detection on the frame.
    Returns the detection results.
    """
    results = model(frame)
    return results
