"""
ocr_service.py
==============
SAFEMETRIC OCR Service

Runs the EXACT uploaded image through the real OCR pipeline:
  Image file → OpenCV preprocessing → RapidOCR (PP-OCRv4) / PaddleOCR fallback
  → raw_text + bounding_boxes + confidence

Design guarantees:
- Always processes the specific image_path given. No caching across requests.
- No fake/demo data. No product-specific shortcuts.
- Low-confidence regions are preserved (NOT discarded) and flagged for officer review.
- Original image is never modified on disk.
"""
import os
import hashlib
from typing import Dict, Any, List, Optional
from app.ocr.preprocessing import preprocess_image

# Check for RapidOCR and PaddleOCR availability
RAPID_AVAILABLE = False
rapid_ocr_engine = None

try:
    from rapidocr_onnxruntime import RapidOCR
    rapid_ocr_engine = RapidOCR()
    RAPID_AVAILABLE = True
    print("[OCR] RapidOCR (PP-OCRv4 ONNX) loaded successfully.")
except Exception as e:
    print(f"[OCR Warning] RapidOCR unavailable: {e}")
    RAPID_AVAILABLE = False

PADDLE_AVAILABLE = False
paddle_ocr_engine = None

try:
    from paddleocr import PaddleOCR
    paddle_ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    PADDLE_AVAILABLE = True
    print("[OCR] PaddleOCR loaded as fallback engine.")
except Exception:
    PADDLE_AVAILABLE = False

LOW_CONFIDENCE_THRESHOLD = 80.0


def _format_ocr_output(
    boxes: List[Dict[str, Any]],
    text_lines: List[str],
    original_path: str,
    preprocessed_path: Optional[str] = None,
    engine_name: str = "RapidOCR (PP-OCRv4 ONNX)",
    quality_metrics: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Standardizes OCR output into a structured, verifiable payload.
    Preserves low-confidence regions for review without making legal determinations.
    """
    count = len(boxes)
    if count == 0:
        return {
            "raw_text": "",
            "text_lines": [],
            "bounding_boxes": [],
            "avg_confidence": 0.0,
            "confidence_summary": {
                "average_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "total_regions": 0,
                "high_confidence_count": 0,
                "low_confidence_count": 0,
                "threshold": LOW_CONFIDENCE_THRESHOLD,
                "low_confidence_review_required": False
            },
            "low_confidence_regions": [],
            "low_confidence_review_required": False,
            "original_image_path": original_path,
            "preprocessed_image_path": preprocessed_path,
            "engine": engine_name,
            "limitations": ["No text regions optically detected on the package image."]
        }

    confidences = [b["confidence"] for b in boxes]
    avg_conf = round(sum(confidences) / count, 1)
    min_conf = round(min(confidences), 1)
    max_conf = round(max(confidences), 1)

    low_conf_regions = []
    for i, b in enumerate(boxes, 1):
        b["line_number"] = i
        is_low = b["confidence"] < LOW_CONFIDENCE_THRESHOLD
        b["is_low_confidence"] = is_low
        if is_low:
            low_conf_regions.append({
                "line_number": i,
                "text": b["text"],
                "box": b["box"],
                "confidence": b["confidence"],
                "reason": (
                    f"Optical recognition confidence ({b['confidence']}%) is below "
                    f"the {LOW_CONFIDENCE_THRESHOLD}% review threshold."
                )
            })

    limitations = []
    if low_conf_regions:
        sample_low = low_conf_regions[0]
        limitations.append(
            f"Preserved {len(low_conf_regions)} low-confidence region(s) for officer review "
            f"(e.g. line {sample_low['line_number']} '{sample_low['text']}' at {sample_low['confidence']}%)."
        )

    single_chars = [b['text'] for b in boxes if len(b['text'].strip()) == 1]
    if single_chars:
        limitations.append(
            f"Detected {len(single_chars)} isolated single-character token(s); "
            "reflections on curved/flexible packaging may introduce ambiguity."
        )

    if quality_metrics:
        if quality_metrics.get("sharpness_index", 0) > 1000 and quality_metrics.get("contrast_std", 0) > 65:
            limitations.append(
                "High specular reflection / gloss detected on flexible packaging substrate; "
                "adaptive contrast equalization applied."
            )

    raw_text = "\n".join(text_lines)

    return {
        "raw_text": raw_text,
        "text_lines": text_lines,
        "bounding_boxes": boxes,
        "avg_confidence": avg_conf,
        "confidence_summary": {
            "average_confidence": avg_conf,
            "min_confidence": min_conf,
            "max_confidence": max_conf,
            "total_regions": count,
            "high_confidence_count": count - len(low_conf_regions),
            "low_confidence_count": len(low_conf_regions),
            "threshold": LOW_CONFIDENCE_THRESHOLD,
            "low_confidence_review_required": len(low_conf_regions) > 0
        },
        "low_confidence_regions": low_conf_regions,
        "low_confidence_review_required": len(low_conf_regions) > 0,
        "original_image_path": original_path,
        "preprocessed_image_path": preprocessed_path,
        "engine": engine_name,
        "limitations": limitations
    }


class OCRService:
    """
    SAFEMETRIC OCR Service.
    Processes the EXACT image file at image_path — no caching, no shared state, no fake data.
    Returns raw OCR text, bounding boxes, and confidence for every uploaded product image.
    """

    def process_image(self, image_path: str, hint: str = "", is_demo: bool = False) -> Dict[str, Any]:
        """
        Executes the complete OCR pipeline on the exact image file specified.
        Image → EXIF orientation fix → CLAHE preprocessing → RapidOCR / PaddleOCR fallback
        Returns raw_text, bounding_boxes, confidence — no guessing, no inventing text.
        """
        # 1. Run OpenCV Preprocessing (non-destructive; saves preprocessed copy)
        preprocessed_img = None
        scale_factor = 1.0
        preprocessed_path = None
        prep_result = None
        try:
            prep_result = preprocess_image(image_path, save_processed=True)
            preprocessed_img = prep_result.processed_image
            scale_factor = prep_result.scale_factor
            preprocessed_path = prep_result.processed_path
        except Exception as e:
            print(f"[OCR Warning] Preprocessing failed for {image_path}: {e}")

        # 2. Primary Engine: RapidOCR (PP-OCRv4 via ONNX)
        if RAPID_AVAILABLE and rapid_ocr_engine is not None:
            try:
                img_input = preprocessed_img if preprocessed_img is not None else image_path
                result, elapse = rapid_ocr_engine(img_input)
                if result:
                    boxes = []
                    text_lines = []
                    for line in result:
                        raw_box = line[0]
                        text = str(line[1]).strip()
                        if not text:
                            continue
                        conf = float(line[2])
                        conf_pct = round(conf * 100, 1) if conf <= 1.0 else round(conf, 1)

                        # Scale bounding box back to original coordinates if image was resized
                        if scale_factor != 1.0 and scale_factor > 0:
                            box = [[round(pt[0] / scale_factor), round(pt[1] / scale_factor)] for pt in raw_box]
                        else:
                            box = raw_box

                        boxes.append({"text": text, "box": box, "confidence": conf_pct})
                        text_lines.append(text)

                    return _format_ocr_output(
                        boxes=boxes,
                        text_lines=text_lines,
                        original_path=image_path,
                        preprocessed_path=preprocessed_path,
                        engine_name="RapidOCR (PP-OCRv4 ONNX)",
                        quality_metrics=prep_result.quality_metrics if prep_result else None
                    )
                else:
                    return _format_ocr_output(
                        boxes=[],
                        text_lines=[],
                        original_path=image_path,
                        preprocessed_path=preprocessed_path,
                        engine_name="RapidOCR (PP-OCRv4 ONNX)",
                        quality_metrics=prep_result.quality_metrics if prep_result else None
                    )
            except Exception as e:
                print(f"[RapidOCR Engine Error] {e}")

        # 3. Secondary Fallback: PaddleOCR if installed
        if PADDLE_AVAILABLE and paddle_ocr_engine is not None:
            try:
                result = paddle_ocr_engine.ocr(image_path, cls=True)
                boxes = []
                text_lines = []
                if result and len(result) > 0 and result[0] is not None:
                    for line in result[0]:
                        box = line[0]
                        text, conf = line[1]
                        conf_pct = round(float(conf) * 100, 1)
                        boxes.append({"text": text, "box": box, "confidence": conf_pct})
                        text_lines.append(text)
                return _format_ocr_output(
                    boxes=boxes,
                    text_lines=text_lines,
                    original_path=image_path,
                    preprocessed_path=preprocessed_path,
                    engine_name="PaddleOCR",
                    quality_metrics=prep_result.quality_metrics if prep_result else None
                )
            except Exception as e:
                print(f"[PaddleOCR Engine Error] {e}")

        # 4. No OCR engine available — return empty result (never fake data)
        return _format_ocr_output(
            boxes=[],
            text_lines=[],
            original_path=image_path,
            preprocessed_path=preprocessed_path,
            engine_name="None (no OCR engine installed)",
            quality_metrics=None
        )

    def get_ocr_debug_info(self, image_path: str) -> Dict[str, Any]:
        """
        Returns structured OCR debug info for development/tracing:
        source image path, SHA-256 hash, engine, char count, box count, avg confidence, raw text sample.
        """
        result = self.process_image(image_path)
        img_hash = "unknown"
        try:
            with open(image_path, 'rb') as f:
                img_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        except Exception:
            pass
        return {
            "inspection_source_path": image_path,
            "image_sha256_prefix": img_hash,
            "engine": result.get("engine"),
            "ocr_char_count": len(result.get("raw_text", "")),
            "ocr_box_count": len(result.get("bounding_boxes", [])),
            "avg_confidence": result.get("avg_confidence", 0.0),
            "raw_text_sample": result.get("raw_text", "")[:500],
            "bounding_boxes": result.get("bounding_boxes", [])
        }

    def extract_text(self, image_path: str, hint: str = "", is_demo: bool = False) -> str:
        res = self.process_image(image_path)
        return res.get("raw_text", "")

    def get_confidence(self, image_path: str, hint: str = "", is_demo: bool = False) -> float:
        res = self.process_image(image_path)
        return res.get("avg_confidence", 0.0)

    def get_bounding_boxes(self, image_path: str, hint: str = "", is_demo: bool = False) -> List[Dict[str, Any]]:
        res = self.process_image(image_path)
        return res.get("bounding_boxes", [])


ocr_service = OCRService()
