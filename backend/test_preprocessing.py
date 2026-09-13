import os
import sys
import hashlib
import cv2
import numpy as np
from PIL import Image

# Ensure backend directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.ocr.preprocessing import (
    ImagePreprocessor,
    PreprocessingResult,
    preprocess_image,
    preprocess_for_ocr,
    get_adaptive_threshold
)
from app.ocr.ocr_service import OCRService


def get_file_md5(filepath: str) -> str:
    """Computes MD5 hash of a file to verify zero modifications."""
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_preprocessing_pipeline():
    print("=" * 65)
    print(" TESTING SAFEMETRIC IMAGE PREPROCESSING PIPELINE (LAY'S IMAGE)")
    print("=" * 65)

    # Locate the Lay's product image
    user_lays_path = r"C:\Users\doram\Downloads\lays.jpg"
    workspace_lays_path = os.path.join(BASE_DIR, "demo_samples", "lays.jpg")

    if os.path.exists(user_lays_path):
        lays_path = user_lays_path
    elif os.path.exists(workspace_lays_path):
        lays_path = workspace_lays_path
    else:
        raise FileNotFoundError("Lay's product image not found!")

    print(f"\n[Source Product Image]: {lays_path}")

    # -------------------------------------------------------------
    # 1. Verify Original Image Immutability (Zero Modification)
    # -------------------------------------------------------------
    print("\n--- 1. Testing Original Image Immutability ---")
    orig_hash_before = get_file_md5(lays_path)
    orig_size_before = os.path.getsize(lays_path)
    print(f"  Original MD5 Before: {orig_hash_before}")
    print(f"  Original Size:       {orig_size_before} bytes")

    output_processed_path = os.path.join(BASE_DIR, "uploads", "lays_preprocessed.png")
    os.makedirs(os.path.dirname(output_processed_path), exist_ok=True)

    # Run preprocessing pipeline
    preprocessor = ImagePreprocessor(target_width=1200, min_width=800, max_width=2400)
    result = preprocessor.preprocess(
        image_input=lays_path,
        output_path=output_processed_path,
        save_processed=True
    )

    orig_hash_after = get_file_md5(lays_path)
    orig_size_after = os.path.getsize(lays_path)
    assert orig_hash_before == orig_hash_after, "CRITICAL: Original file was modified during preprocessing!"
    assert orig_size_before == orig_size_after, "CRITICAL: Original file size changed!"
    print(f"  Original MD5 After:  {orig_hash_after}")
    print(f"  [PASS] User original image is 100% preserved and untouched!")

    # -------------------------------------------------------------
    # 2. Verify Output File Separation (Keep Both Images)
    # -------------------------------------------------------------
    print("\n--- 2. Testing Dual Image Retention (Original & Processed) ---")
    assert os.path.exists(lays_path), "Original image missing!"
    assert os.path.exists(output_processed_path), "Processed image missing!"
    assert lays_path != output_processed_path, "Original and processed paths must be distinct!"

    processed_size = os.path.getsize(output_processed_path)
    print(f"  1. Original Image Path:  {lays_path} ({orig_size_after} bytes)")
    print(f"  2. Processed Image Path: {output_processed_path} ({processed_size} bytes)")
    print(f"  [PASS] Both original and processed images are independently preserved on disk.")

    # -------------------------------------------------------------
    # 3. Testing Resolution Normalization & Aspect Ratio Preservation
    # -------------------------------------------------------------
    print("\n--- 3. Testing Aspect-Ratio Preserving Resizing ---")
    orig_w, orig_h = result.original_dimensions
    proc_w, proc_h = result.processed_dimensions
    scale = result.scale_factor

    orig_aspect = orig_h / float(orig_w)
    proc_aspect = proc_h / float(proc_w)
    aspect_diff = abs(orig_aspect - proc_aspect)

    print(f"  Original Dimensions:  {orig_w} x {orig_h} (Aspect Ratio: {orig_aspect:.4f})")
    print(f"  Processed Dimensions: {proc_w} x {proc_h} (Aspect Ratio: {proc_aspect:.4f})")
    print(f"  Scale Factor Applied: {scale:.3f}")
    print(f"  Aspect Ratio Delta:   {aspect_diff:.6f}")

    assert proc_w == 1200, f"Expected target width 1200, got {proc_w}"
    assert aspect_diff < 0.005, f"Aspect ratio distortion detected! Diff: {aspect_diff}"
    print("  [PASS] Resizing accurately targets optimal width while preserving packaging proportions.")

    # -------------------------------------------------------------
    # 4. Testing Orientation & Deskewing
    # -------------------------------------------------------------
    print("\n--- 4. Testing Orientation & Deskewing ---")
    print(f"  Lay's Package Skew Angle: {result.rotation_angle:.2f}° (Upright orientation)")
    print(f"  EXIF Orientation Tag:     {result.exif_orientation}")

    # Test artificial tilt recovery
    sample_img = cv2.imread(lays_path)
    sh, sw = sample_img.shape[:2]
    tilt_angle = 6.0
    rot_mat = cv2.getRotationMatrix2D((sw // 2, sh // 2), -tilt_angle, 1.0)
    tilted_img = cv2.warpAffine(sample_img, rot_mat, (sw, sh), borderMode=cv2.BORDER_REPLICATE)

    recovered_img, detected_angle = preprocessor.correct_orientation(tilted_img)
    print(f"  Artificial Tilt Introduced: -{tilt_angle}°")
    print(f"  Deskew Detected Angle:      {detected_angle:.2f}°")
    assert abs(abs(detected_angle) - tilt_angle) < 1.5, f"Deskew angle {detected_angle} deviates from expected {tilt_angle}"
    print("  [PASS] Orientation correction accurately detects text baseline tilt and straightens label.")

    # -------------------------------------------------------------
    # 5. Testing Noise Reduction & Contrast Improvement
    # -------------------------------------------------------------
    print("\n--- 5. Testing Noise Reduction & Contrast Improvement ---")
    raw_gray = cv2.cvtColor(sample_img, cv2.COLOR_BGR2GRAY)
    raw_contrast = float(np.std(raw_gray))
    raw_laplacian = float(cv2.Laplacian(raw_gray, cv2.CV_64F).var())

    metrics = result.quality_metrics
    enhanced_contrast = metrics["contrast_std"]
    enhanced_sharpness = metrics["sharpness_index"]

    print(f"  Raw Image Contrast (std):        {raw_contrast:.1f}")
    print(f"  Enhanced Contrast (CLAHE std):   {enhanced_contrast:.1f}")
    print(f"  Sharpness Index (Laplacian var): {enhanced_sharpness:.1f}")
    print(f"  Exposure Status:                 {metrics['has_good_exposure']}")

    assert enhanced_contrast > raw_contrast, "Contrast should be improved by CLAHE equalization!"
    assert enhanced_sharpness > 500.0, "Sharpness should remain high for text readability!"
    print("  [PASS] CLAHE and bilateral filtering successfully enhanced contrast on packaging sheen.")

    # -------------------------------------------------------------
    # 6. Testing Multi-Mode Binarization
    # -------------------------------------------------------------
    print("\n--- 6. Testing Multi-Mode Binarization ---")
    adaptive_bin = result.binarized_image
    otsu_bin = result.otsu_binarized_image

    assert adaptive_bin is not None, "Adaptive threshold image missing!"
    assert otsu_bin is not None, "Otsu threshold image missing!"
    assert adaptive_bin.shape == (proc_h, proc_w), f"Shape mismatch: {adaptive_bin.shape}"

    unique_vals = np.unique(adaptive_bin)
    assert set(unique_vals).issubset({0, 255}), "Adaptive threshold must be purely binary (0 or 255)!"
    print(f"  Adaptive Threshold Shape: {adaptive_bin.shape}, Pixel Values: {unique_vals}")
    print(f"  Otsu Threshold Shape:     {otsu_bin.shape}")
    print("  [PASS] Binarization modules produce valid high-contrast binary masks.")

    # -------------------------------------------------------------
    # 7. Testing Reusability by OCR Module (RapidOCR Integration)
    # -------------------------------------------------------------
    print("\n--- 7. Testing OCR Module Reusability (RapidOCR on Preprocessed Image) ---")
    ocr_service = OCRService()
    # Execute OCR service on Lay's image (real file, not demo)
    ocr_result = ocr_service.process_image(image_path=lays_path, is_demo=False)

    raw_text = ocr_result.get("raw_text", "")
    avg_conf = ocr_result.get("avg_confidence", 0.0)
    boxes = ocr_result.get("bounding_boxes", [])
    prep_path_returned = ocr_result.get("preprocessed_path")

    print(f"  OCR Detected Text Blocks:    {len(boxes)}")
    print(f"  Average Confidence:          {avg_conf}%")
    print(f"  Preprocessed Path Retained:  {prep_path_returned}")

    assert len(boxes) > 20, f"Expected >20 text blocks from Lay's nutrition label, got {len(boxes)}"
    assert avg_conf > 85.0, f"Expected high average confidence >85%, got {avg_conf}%"
    assert any("nutrition" in b["text"].lower() or "approx" in b["text"].lower() for b in boxes), \
        "Expected nutritional declaration extracted from Lay's label!"
    assert any("energy" in b["text"].lower() or "protein" in b["text"].lower() or "kcal" in b["text"].lower() for b in boxes), \
        "Expected mandatory nutritional fields (Energy / Protein / kcal) detected!"

    print("\n  Sample Declarations Detected by OCR:")
    for b in boxes[:6]:
        print(f"    - {b['text']} ({b['confidence']}%) [Box: {b['box']}]")

    print(f"\n  [PASS] OCR service successfully ingested preprocessed image and extracted declarations.")

    # -------------------------------------------------------------
    # 8. Confirm Zero Legal Validation Executed
    # -------------------------------------------------------------
    print("\n--- 8. Verifying Boundary (No Legal Validation) ---")
    assert "compliance_status" not in ocr_result, "CRITICAL: Legal compliance status must not be computed in preprocessing!"
    assert "violations" not in ocr_result, "CRITICAL: Violations must not be computed in preprocessing!"
    print("  [PASS] Pure preprocessing & OCR intake verified. Zero legal validation executed.")

    print("\n" + "=" * 65)
    print(" ALL PREPROCESSING PIPELINE TESTS PASSED (100%)!")
    print("=" * 65)


if __name__ == "__main__":
    test_preprocessing_pipeline()
