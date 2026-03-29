import re
import cv2
import numpy as np

try:
    import easyocr
except Exception:
    easyocr = None


PLATE_REGEX = re.compile(r"^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$")

_easy_reader = None


def _get_easy_reader():
    """Initialize EasyOCR reader with optimized settings for speed"""
    global _easy_reader
    if _easy_reader is not None:
        return _easy_reader
    if easyocr is None:
        return None
    try:
        # Optimized for speed: use lightweight model, no GPU, parallel disabled
        _easy_reader = easyocr.Reader(["en"], gpu=False, model_storage_directory="./models", 
                                      user_network_directory="./models", verbose=False, 
                                      quantize=True)
    except Exception:
        _easy_reader = None
    return _easy_reader


def _normalize_text(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def _preprocess_image(image_crop):
    """Fast single-stage preprocessing optimized for license plates"""
    if image_crop is None or image_crop.size == 0:
        return None

    if len(image_crop.shape) == 2:
        gray = image_crop
    else:
        gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape[:2]
    
    # Only upscale if image is very small
    if w < 100:
        gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    
    # Single efficient enhancement pass
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Light denoising only
    denoised = cv2.bilateralFilter(enhanced, 5, 30, 30)
    
    return denoised


def _candidate_score(text: str, conf: float) -> float:
    score = conf
    if len(text) >= 8:
        score += 0.15
    if PLATE_REGEX.match(text):
        score += 0.45
    if re.match(r"^[A-Z0-9]{6,12}$", text):
        score += 0.1
    return score


def extract_text_with_conf(image_crop):
    """
    Fast OCR extraction with single-pass processing.
    Optimized for real-time camera performance.
    """
    preprocessed = _preprocess_image(image_crop)
    if preprocessed is None:
        return "", 0.0, "none"

    best_text = ""
    best_conf = 0.0
    best_engine = "easyocr"
    best_score = -1.0

    easy = _get_easy_reader()
    if easy is None:
        return "", 0.0, "none"

    try:
        # Single fast OCR pass instead of multiple variants
        results = easy.readtext(preprocessed, detail=1, workers=0)
        
        for item in results:
            if len(item) >= 3:
                text = _normalize_text(item[1])
                conf = float(item[2]) if item[2] is not None else 0.0
                
                if not text:
                    continue
                
                score = _candidate_score(text, conf)
                
                # Early termination on high confidence match
                if score > best_score:
                    best_text, best_conf, best_engine, best_score = text, conf, "easyocr", score
                    
                    # Stop early if we found a valid plate with high confidence
                    if PLATE_REGEX.match(text) and conf > 0.7:
                        break
    except Exception as e:
        pass

    return best_text, best_conf, best_engine


def extract_text(image_crop):
    text, _, _ = extract_text_with_conf(image_crop)
    return text
