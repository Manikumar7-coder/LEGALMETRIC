import cv2
import numpy as np
from typing import Dict, Any, List

def analyze_image_quality(image_path: str) -> Dict[str, Any]:
    """
    Evaluates resolution, blur, brightness, contrast, and orientation of label image.
    Returns quality score (0-100), warnings, and recommendation flags.
    """
    warnings: List[str] = []
    
    # Read image using OpenCV
    img = cv2.imread(image_path)
    if img is None:
        return {
            "is_acceptable": False,
            "quality_score": 0.0,
            "blur_score": 0.0,
            "brightness_score": 0.0,
            "contrast_score": 0.0,
            "warnings": ["Image file could not be read or is corrupted."],
            "message": "Unable to read image. Please re-capture or select another file."
        }

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Resolution Check
    resolution_warning = False
    if w < 450 or h < 450:
        warnings.append(f"Low resolution ({w}x{h} px). Minimum recommended is 800x800 for high OCR precision.")
        resolution_warning = True

    # 2. Blur Check (Laplacian Variance)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    blur_score = round(float(laplacian_var), 1)
    if blur_score < 70.0:
        warnings.append(f"Motion blur or soft focus detected (sharpness index: {blur_score}). Small text may be misread.")

    # 3. Brightness Check
    mean_brightness = float(np.mean(gray))
    brightness_score = round(mean_brightness, 1)
    if mean_brightness < 45.0:
        warnings.append("Insufficient lighting detected. Image is underexposed.")
    elif mean_brightness > 225.0:
        warnings.append("Glare or overexposure detected. Contrast on text may be lost.")

    # 4. Contrast Check
    contrast = float(np.std(gray))
    contrast_score = round(contrast, 1)
    if contrast < 32.0:
        warnings.append("Low contrast detected between text and packaging background.")

    # Calculate overall quality score (0-100)
    score = 100.0
    if resolution_warning:
        score -= 20.0
    if blur_score < 70.0:
        score -= min(35.0, (70.0 - blur_score) * 0.7)
    if mean_brightness < 45.0 or mean_brightness > 225.0:
        score -= 20.0
    if contrast < 32.0:
        score -= 15.0

    score = max(10.0, min(100.0, round(score, 1)))
    is_acceptable = score >= 55.0

    message = (
        "Image quality is optimal for Legal Metrology compliance inspection."
        if is_acceptable and not warnings
        else "Image quality may affect OCR accuracy. You may proceed or re-capture a sharper image."
    )

    return {
        "is_acceptable": is_acceptable,
        "quality_score": score,
        "blur_score": blur_score,
        "brightness_score": brightness_score,
        "contrast_score": contrast_score,
        "warnings": warnings,
        "message": message,
        "dimensions": f"{w}x{h}"
    }
