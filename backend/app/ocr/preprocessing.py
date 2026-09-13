import os
import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional, Union
from dataclasses import dataclass
from PIL import Image, ImageOps


@dataclass
class PreprocessingResult:
    """Encapsulates all outputs, variants, and metrics from the preprocessing pipeline."""
    original_path: Optional[str]
    processed_path: Optional[str]
    processed_image: np.ndarray          # 3-channel BGR image optimal for OCR engines
    original_image: np.ndarray           # Unmodified original image
    grayscale_image: np.ndarray          # 1-channel grayscale representation
    enhanced_image: np.ndarray           # 1-channel CLAHE enhanced & sharpened grayscale
    binarized_image: np.ndarray          # 1-channel adaptive Gaussian threshold
    otsu_binarized_image: np.ndarray     # 1-channel Otsu threshold
    original_dimensions: Tuple[int, int] # (width, height)
    processed_dimensions: Tuple[int, int]# (width, height)
    scale_factor: float                  # Scaling applied (1.0 = no resize)
    rotation_angle: float                # Deskew angle in degrees
    exif_orientation: int                # Original EXIF orientation tag (1 = normal)
    quality_metrics: Dict[str, Any]      # Sharpness, brightness, contrast metrics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_path": self.original_path,
            "processed_path": self.processed_path,
            "original_dimensions": {
                "width": self.original_dimensions[0],
                "height": self.original_dimensions[1]
            },
            "processed_dimensions": {
                "width": self.processed_dimensions[0],
                "height": self.processed_dimensions[1]
            },
            "scale_factor": round(self.scale_factor, 3),
            "rotation_angle": round(self.rotation_angle, 2),
            "exif_orientation": self.exif_orientation,
            "quality_metrics": self.quality_metrics
        }


class ImagePreprocessor:
    """
    Production-grade computer vision preprocessing pipeline tailored for Legal Metrology packaging labels.
    
    Operations:
    1. EXIF Orientation Normalization: Transposes mobile photos to upright orientation.
    2. Orientation / Deskew Detection: Straightens rotated text lines using Hough transforms.
    3. Aspect-Preserving Resizing: Normalizes resolution for optimal OCR text recognition.
    4. Edge-Preserving Denoising: Uses Bilateral Filtering to smooth packaging grain/sheen while keeping font edges crisp.
    5. CLAHE Contrast Improvement: Balances localized glare on shiny plastic/foil packaging and shadows.
    6. Unsharp Stroke Sharpening: Accentuate fine print (MRP, date codes, net weights).
    7. Multi-Mode Binarization: Adaptive Gaussian and Otsu thresholding for high-contrast OCR fallback.
    8. Strict Immutability: Preserves user's original image completely intact on disk.
    """

    def __init__(
        self,
        target_width: int = 1200,
        min_width: int = 800,
        max_width: int = 2400,
        clahe_clip: float = 2.5,
        clahe_grid: Tuple[int, int] = (8, 8)
    ):
        self.target_width = target_width
        self.min_width = min_width
        self.max_width = max_width
        self.clahe_clip = clahe_clip
        self.clahe_grid = clahe_grid

    def load_image(
        self,
        image_input: Union[str, np.ndarray, Image.Image]
    ) -> Tuple[np.ndarray, np.ndarray, Optional[str], int]:
        """
        Loads image, extracts EXIF orientation, applies EXIF transpose, and preserves original image.
        Returns: (transposed_bgr, original_bgr, original_path, exif_orientation)
        """
        original_path = None
        exif_orientation = 1

        if isinstance(image_input, str):
            original_path = image_input
            if not os.path.exists(image_input):
                raise FileNotFoundError(f"Image not found at: {image_input}")

            # Read via PIL to extract EXIF and apply transpose safely
            with Image.open(image_input) as pil_img:
                exif = pil_img.getexif()
                exif_orientation = exif.get(0x0112, 1) if exif else 1
                transposed_pil = ImageOps.exif_transpose(pil_img)

                # Convert to RGB numpy then BGR
                rgb_arr = np.array(transposed_pil.convert("RGB"))
                transposed_bgr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

            # Also read raw original via OpenCV for pristine reference
            original_bgr = cv2.imread(image_input)
            if original_bgr is None:
                original_bgr = transposed_bgr.copy()

        elif isinstance(image_input, Image.Image):
            exif = image_input.getexif()
            exif_orientation = exif.get(0x0112, 1) if exif else 1
            transposed_pil = ImageOps.exif_transpose(image_input)
            rgb_arr = np.array(transposed_pil.convert("RGB"))
            transposed_bgr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)
            original_bgr = transposed_bgr.copy()

        elif isinstance(image_input, np.ndarray):
            transposed_bgr = image_input.copy()
            original_bgr = image_input.copy()

        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

        return transposed_bgr, original_bgr, original_path, exif_orientation

    def detect_deskew_angle(self, image: np.ndarray) -> float:
        """
        Detects fine skew angle (-45° to +45°) of text baselines using Hough line detection.
        Rejects minor noise (|angle| < 0.5°).
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Edge detection tailored for text line baselines
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=80, maxLineGap=10)

        if lines is None or len(lines) == 0:
            return 0.0

        try:
            reshaped_lines = np.asarray(lines).reshape(-1, 4)
        except Exception:
            return 0.0

        angles = []
        for x1, y1, x2, y2 in reshaped_lines:
            if x1 > x2:
                x1, y1, x2, y2 = x2, y2, x1, y1
            dx = float(x2 - x1)
            dy = float(y2 - y1)
            if dx == 0.0 and dy == 0.0:
                continue
            angle = float(np.degrees(np.arctan2(dy, dx)))
            if -45.0 <= angle <= 45.0:
                angles.append(angle)

        if not angles:
            return 0.0

        median_angle = float(np.median(angles))
        # Ignore negligible tilt
        if abs(median_angle) < 0.5:
            return 0.0

        return median_angle

    def correct_orientation(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Straightens skewed image based on detected text baseline angle.
        Rotates image around center using white background border to avoid black borders.
        """
        angle = self.detect_deskew_angle(image)
        if abs(angle) < 0.5:
            return image, 0.0

        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Determine background fill color (white for text labels)
        border_color = (255, 255, 255) if len(image.shape) == 3 else 255
        corrected = cv2.warpAffine(
            image,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=border_color
        )
        return corrected, angle

    def resize_for_ocr(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Resizes image to optimal OCR dimensions while strictly preserving aspect ratio.
        - Upscales small images (< min_width) using INTER_CUBIC.
        - Downscales huge images (> max_width) using INTER_AREA.
        - Preserves dimensions if already in optimal range.
        """
        h, w = image.shape[:2]
        scale = 1.0

        if w < self.min_width:
            scale = self.target_width / float(w)
            target_h = int(round(h * scale))
            resized = cv2.resize(image, (self.target_width, target_h), interpolation=cv2.INTER_CUBIC)
            return resized, scale
        elif w > self.max_width or max(h, w) > 2600:
            scale = self.target_width / float(w)
            target_h = int(round(h * scale))
            resized = cv2.resize(image, (self.target_width, target_h), interpolation=cv2.INTER_AREA)
            return resized, scale
        else:
            return image.copy(), 1.0

    def reduce_noise(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Bilateral filtering smooths packaging substrate noise, halftone print dots,
        and sensor grain while retaining sharp text stroke boundaries.
        """
        return cv2.bilateralFilter(gray_image, d=9, sigmaColor=75, sigmaSpace=75)

    def enhance_contrast_and_edges(self, denoised_gray: np.ndarray) -> np.ndarray:
        """
        Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) followed by
        unsharp masking to enhance fine text strokes (MRP, dates, metric units).
        """
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip, tileGridSize=self.clahe_grid)
        enhanced = clahe.apply(denoised_gray)

        # Unsharp masking: sharpened = original + 0.4 * (original - gaussian_blur)
        gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
        sharpened = cv2.addWeighted(enhanced, 1.4, gaussian, -0.4, 0)
        return sharpened

    def binarize(self, enhanced_gray: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates two high-contrast binarized representations:
        1. Adaptive Gaussian Threshold: excels at handling non-uniform illumination on glossy foil/bags.
        2. Otsu Global Threshold: clean baseline for high-contrast labels.
        """
        adaptive_thresh = cv2.adaptiveThreshold(
            enhanced_gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,
            C=8
        )
        _, otsu_thresh = cv2.threshold(
            enhanced_gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        return adaptive_thresh, otsu_thresh

    def compute_quality_metrics(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Computes objective optical quality metrics: sharpness, brightness, and contrast."""
        laplacian_var = float(cv2.Laplacian(gray_image, cv2.CV_64F).var())
        mean_brightness = float(np.mean(gray_image))
        std_contrast = float(np.std(gray_image))

        return {
            "sharpness_index": round(laplacian_var, 1),
            "brightness_mean": round(mean_brightness, 1),
            "contrast_std": round(std_contrast, 1),
            "is_sharp": laplacian_var >= 70.0,
            "has_good_exposure": 45.0 <= mean_brightness <= 225.0,
            "has_good_contrast": std_contrast >= 32.0
        }

    def preprocess(
        self,
        image_input: Union[str, np.ndarray, Image.Image],
        output_path: Optional[str] = None,
        save_processed: bool = True
    ) -> PreprocessingResult:
        """
        Executes complete, non-destructive packaging label preprocessing pipeline.
        The user's original image is never modified.
        """
        # 1. Load image and extract EXIF orientation
        img, orig_img, orig_path, exif_orient = self.load_image(image_input)
        orig_h, orig_w = orig_img.shape[:2]

        # 2. Orientation / Deskew Correction
        straightened, skew_angle = self.correct_orientation(img)

        # 3. Resolution Normalization / Resizing
        resized, scale_factor = self.resize_for_ocr(straightened)
        proc_h, proc_w = resized.shape[:2]

        # 4. Grayscale Conversion
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # 5. Edge-Preserving Noise Reduction
        denoised = self.reduce_noise(gray)

        # 6. CLAHE Contrast Enhancement & Stroke Sharpening
        enhanced = self.enhance_contrast_and_edges(denoised)

        # 7. Binarization (Adaptive & Otsu)
        adaptive_bin, otsu_bin = self.binarize(enhanced)

        # 8. Compute Quality Metrics
        quality_metrics = self.compute_quality_metrics(enhanced)

        # 9. Format 3-Channel Processed Image for OCR
        processed_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

        # 10. File Persistence (Non-destructive: saves to a distinct output path)
        final_output_path = None
        if save_processed:
            if output_path:
                final_output_path = output_path
            elif orig_path:
                base_dir = os.path.dirname(orig_path)
                base_name, _ = os.path.splitext(os.path.basename(orig_path))
                final_output_path = os.path.join(base_dir, f"{base_name}_preprocessed.png")

            if final_output_path:
                os.makedirs(os.path.dirname(os.path.abspath(final_output_path)), exist_ok=True)
                cv2.imwrite(final_output_path, processed_bgr)

        return PreprocessingResult(
            original_path=orig_path,
            processed_path=final_output_path,
            processed_image=processed_bgr,
            original_image=orig_img,
            grayscale_image=gray,
            enhanced_image=enhanced,
            binarized_image=adaptive_bin,
            otsu_binarized_image=otsu_bin,
            original_dimensions=(orig_w, orig_h),
            processed_dimensions=(proc_w, proc_h),
            scale_factor=scale_factor,
            rotation_angle=skew_angle,
            exif_orientation=exif_orient,
            quality_metrics=quality_metrics
        )


# Global singleton preprocessor instance
default_preprocessor = ImagePreprocessor()


def preprocess_for_ocr(image_path: str, output_path: str = None) -> np.ndarray:
    """
    Backward-compatible convenience function used by OCRService and routers.
    Preprocesses the packaging image, optionally saves to output_path,
    and returns the processed 3-channel BGR numpy ndarray ready for RapidOCR / PaddleOCR.
    The original image file at image_path is strictly preserved without modification.
    """
    result = default_preprocessor.preprocess(
        image_input=image_path,
        output_path=output_path,
        save_processed=bool(output_path is not None)
    )
    return result.processed_image


def preprocess_image(
    image_input: Union[str, np.ndarray, Image.Image],
    output_path: Optional[str] = None,
    save_processed: bool = True
) -> PreprocessingResult:
    """Convenience function returning the full PreprocessingResult object."""
    return default_preprocessor.preprocess(
        image_input=image_input,
        output_path=output_path,
        save_processed=save_processed
    )


def get_adaptive_threshold(gray_img: np.ndarray) -> np.ndarray:
    """Computes binarized adaptive threshold image for fine print segments."""
    return cv2.adaptiveThreshold(
        gray_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
    )
