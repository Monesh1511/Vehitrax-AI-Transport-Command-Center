import cv2
import numpy as np
from plate_detector import PlateDetector
from ocr import extract_text_with_conf
import base64
import io
from PIL import Image
import time


class PlateScanner:
    def __init__(self):
        self.detector = PlateDetector()

    def preprocess_for_ocr(self, plate_img):
        """Preprocess plate image for better OCR accuracy"""
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)

        # Resize for better OCR
        resized = cv2.resize(denoised, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        return resized

    def scan_image(self, image_data):
        """
        Scan an image for license plates and extract text.
        image_data can be: numpy array, base64 string, or file path
        """
        # Load image if needed
        if isinstance(image_data, str):
            if image_data.startswith("data:image"):
                # Base64 image
                image_data = image_data.split(",")[1]
                img_bytes = base64.b64decode(image_data)
                img = Image.open(io.BytesIO(img_bytes))
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            else:
                # File path
                frame = cv2.imread(image_data)
        elif isinstance(image_data, bytes):
            # Raw bytes
            img = Image.open(io.BytesIO(image_data))
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        else:
            frame = image_data

        if frame is None:
            return {"error": "Could not load image"}

        # Detect plates
        detections = self.detector.detect_plates(frame)

        results = []
        for i, det in enumerate(detections):
            x1, y1, x2, y2 = det["bbox"]

            # Crop the plate region
            plate_img = frame[y1:y2, x1:x2]

            if plate_img.size == 0:
                continue

            # Preprocess for OCR
            processed = self.preprocess_for_ocr(plate_img)

            # Extract text
            plate_text, ocr_confidence, _ = extract_text_with_conf(processed)

            # Clean the text
            plate_text = self.clean_plate_text(plate_text)

            if plate_text:
                result = {
                    "plate_number": plate_text,
                    "confidence": float(min(1.0, max(det["confidence"], ocr_confidence))),
                    "bbox": det["bbox"],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "detection_id": i,
                }
                results.append(result)

                # Draw result on frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    plate_text,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

        return {
            "plates": results,
            "total_detected": len(results),
            "detections": detections,
        }

    def clean_plate_text(self, text):
        """Clean and format the extracted plate text"""
        import re

        # Remove spaces and special characters, keep only alphanumeric
        cleaned = re.sub(r"[^A-Za-z0-9\-]", "", text)

        # Common OCR corrections for plates
        replacements = {
            "O": "0",  # O to 0 when alone
            "I": "1",  # I to 1 when alone
            "S": "5",  # S to 5
            "B": "8",  # B to 8
        }

        # Apply context-aware replacements (simplified)
        if len(cleaned) > 3:
            first_char = cleaned[0]
            if first_char.isalpha() and cleaned[1:].isdigit():
                if first_char in replacements:
                    # Check if it should be replaced (context dependent)
                    if first_char in ["O", "I"]:
                        cleaned = replacements[first_char] + cleaned[1:]

        return cleaned

    def scan_video_frame(self, frame):
        """Scan a single video frame"""
        return self.scan_image(frame)
