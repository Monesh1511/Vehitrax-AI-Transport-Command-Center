import requests
import os
import base64
from io import BytesIO
from PIL import Image
import numpy as np

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml:8001")


class ScannerService:
    def __init__(self):
        self.ml_url = ML_SERVICE_URL

    def scan_image(self, image_data: bytes) -> dict:
        """
        Send image to ML service for plate scanning.
        Returns the detected plates and their information.
        """
        try:
            # Try to call ML service
            response = requests.post(
                f"{self.ml_url}/api/scan", files={"image": image_data}, timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"ML service error: {response.status_code}"}

        except requests.exceptions.ConnectionError:
            # ML service not available, return error
            return {"error": "ML service is not available"}
        except Exception as e:
            return {"error": str(e)}

    def scan_base64_image(self, base64_image: str) -> dict:
        """Scan a base64 encoded image"""
        try:
            # Remove data URL prefix if present
            if "," in base64_image:
                base64_image = base64_image.split(",")[1]

            image_data = base64.b64decode(base64_image)
            return self.scan_image(image_data)
        except Exception as e:
            return {"error": f"Failed to decode image: {str(e)}"}


# Singleton instance
scanner_service = ScannerService()
