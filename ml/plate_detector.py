from ultralytics import YOLO
import cv2
import numpy as np

# Using YOLOv8 for object detection - we'll use it to detect license plates
# If you have a custom trained model, replace 'yolov8n.pt' with your model path
MODEL_PATH = "yolov8n.pt"


class PlateDetector:
    def __init__(self, model_path=MODEL_PATH):
        self.model = YOLO(model_path)
        self.classes = self.model.names

    def detect_plates(self, frame):
        """
        Detect potential license plate regions in the frame.
        Since we're using general YOLO, we'll look for rectangular objects
        that could be license plates.
        """
        results = self.model(frame)
        detections = []

        for result in results:
            boxes = result.boxes
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                x1, y1, x2, y2 = map(int, xyxy)

                # Calculate aspect ratio to identify potential plates
                width = x2 - x1
                height = y2 - y1
                aspect_ratio = width / height if height > 0 else 0

                # License plates typically have aspect ratio between 2:1 and 5:1
                if 1.5 <= aspect_ratio <= 6:
                    detections.append(
                        {
                            "bbox": (x1, y1, x2, y2),
                            "confidence": conf,
                            "class": cls,
                            "label": self.classes[cls],
                        }
                    )

        return detections

    def draw_detections(self, frame, detections):
        """Draw bounding boxes on the frame"""
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{det['label']}: {det['confidence']:.2f}"
            cv2.putText(
                frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )
        return frame

    def crop_detection(self, frame, bbox):
        """Crop the detection region from the frame"""
        x1, y1, x2, y2 = bbox
        return frame[y1:y2, x1:x2]
