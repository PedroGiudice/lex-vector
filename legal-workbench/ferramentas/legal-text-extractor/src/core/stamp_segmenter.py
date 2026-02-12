"""
StampSegmenter - HSV-based segmentation for colored stamps in legal documents.

Provides detection, extraction, and removal of colored stamps (carimbos) commonly
found in Brazilian legal documents:
- Blue stamps (azul): Official seals, "RECEBIDO" stamps
- Red stamps (vermelho): "URGENTE", date stamps, authentication marks
- Green stamps (verde): Environmental agency stamps, some certifications

Algorithm: HSV Color Space Segmentation
- HSV is more robust to lighting variations than RGB
- H (Hue): Color type (0-180 in OpenCV, 0-360 in standard)
- S (Saturation): Color intensity (0-255)
- V (Value): Brightness (0-255)

Author: Claude Code Agent
Date: 2026-01-07
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TypedDict

import cv2
import numpy as np
from PIL import Image


class StampColor(str, Enum):
    """Predefined stamp colors commonly found in legal documents."""

    BLUE = "blue"
    RED = "red"
    GREEN = "green"
    PURPLE = "purple"
    CUSTOM = "custom"


class StampMode(str, Enum):
    """Processing mode for stamps."""

    REMOVE = "remove"  # Remove stamps for clean OCR
    EXTRACT = "extract"  # Extract stamp regions only
    BOTH = "both"  # Return both cleaned image and extracted stamps


class StampRegion(TypedDict):
    """Metadata for a detected stamp region."""

    color: str
    bbox: tuple[int, int, int, int]  # (x, y, width, height)
    area: int  # Total pixel area
    centroid: tuple[int, int]  # (x, y) center point
    confidence: float  # Detection confidence (0-1)
    contour_points: int  # Number of contour points


@dataclass
class HSVRange:
    """
    HSV color range for stamp detection.

    OpenCV uses H: 0-180, S: 0-255, V: 0-255
    Standard HSV uses H: 0-360, so divide by 2 for OpenCV.

    Example:
        >>> blue = HSVRange(h_min=100, h_max=130, s_min=50, v_min=50)
        >>> blue.to_opencv_bounds()
        (array([100, 50, 50]), array([130, 255, 255]))
    """

    h_min: int
    h_max: int
    s_min: int = 50
    s_max: int = 255
    v_min: int = 50
    v_max: int = 255
    name: str = "custom"

    def to_opencv_bounds(self) -> tuple[np.ndarray, np.ndarray]:
        """Convert to OpenCV inRange() format."""
        lower = np.array([self.h_min, self.s_min, self.v_min], dtype=np.uint8)
        upper = np.array([self.h_max, self.s_max, self.v_max], dtype=np.uint8)
        return lower, upper

    def __post_init__(self):
        """Validate ranges."""
        if not 0 <= self.h_min <= 180:
            raise ValueError(f"h_min must be 0-180, got {self.h_min}")
        if not 0 <= self.h_max <= 180:
            raise ValueError(f"h_max must be 0-180, got {self.h_max}")
        if not 0 <= self.s_min <= 255:
            raise ValueError(f"s_min must be 0-255, got {self.s_min}")
        if not 0 <= self.v_min <= 255:
            raise ValueError(f"v_min must be 0-255, got {self.v_min}")


# Default HSV ranges for common stamp colors in Brazilian legal documents
# These values are tuned for typical scan quality and lighting conditions

DEFAULT_STAMP_RANGES: dict[StampColor, list[HSVRange]] = {
    # Blue stamps - most common in official documents
    # H: 100-130 covers navy blue to sky blue
    StampColor.BLUE: [HSVRange(h_min=100, h_max=130, s_min=50, v_min=50, name="blue")],
    # Red stamps - "URGENTE", date stamps
    # Red wraps around 0 in HSV, so we need two ranges
    StampColor.RED: [
        HSVRange(h_min=0, h_max=10, s_min=50, v_min=50, name="red_low"),
        HSVRange(h_min=170, h_max=180, s_min=50, v_min=50, name="red_high"),
    ],
    # Green stamps - less common but used by environmental agencies
    # Broader range to catch various green shades
    StampColor.GREEN: [HSVRange(h_min=35, h_max=85, s_min=40, v_min=40, name="green")],
    # Purple stamps - rare but sometimes used
    StampColor.PURPLE: [HSVRange(h_min=130, h_max=160, s_min=40, v_min=40, name="purple")],
}


@dataclass
class StampSegmenterConfig:
    """
    Configuration for StampSegmenter.

    Attributes:
        colors: List of stamp colors to detect (or custom HSV ranges)
        mode: Processing mode (remove, extract, or both)
        min_area: Minimum contour area to consider as stamp (filters noise)
        max_area_ratio: Maximum stamp area as ratio of image (filters large regions)
        dilate_kernel: Kernel size for mask dilation (captures stamp edges)
        dilate_iterations: Number of dilation iterations
        morph_close_kernel: Kernel size for morphological closing (fills gaps)
        blur_kernel: Gaussian blur kernel for pre-processing (reduces noise)
        confidence_threshold: Minimum saturation mean for valid stamp
        custom_ranges: Custom HSV ranges (overrides colors if provided)
    """

    colors: list[StampColor] = field(
        default_factory=lambda: [StampColor.BLUE, StampColor.RED, StampColor.GREEN]
    )
    mode: StampMode = StampMode.REMOVE
    min_area: int = 100  # Minimum 100 pixels
    max_area_ratio: float = 0.3  # Max 30% of image
    dilate_kernel: int = 5
    dilate_iterations: int = 2
    morph_close_kernel: int = 7
    blur_kernel: int = 3
    confidence_threshold: float = 0.3
    custom_ranges: list[HSVRange] | None = None

    def get_hsv_ranges(self) -> list[HSVRange]:
        """Get all HSV ranges to use for detection."""
        if self.custom_ranges:
            return self.custom_ranges

        ranges = []
        for color in self.colors:
            if color in DEFAULT_STAMP_RANGES:
                ranges.extend(DEFAULT_STAMP_RANGES[color])
        return ranges


@dataclass
class StampSegmentationResult:
    """
    Result of stamp segmentation.

    Attributes:
        cleaned_image: Image with stamps removed (grayscale)
        stamp_mask: Binary mask of detected stamps
        stamp_regions: List of detected stamp regions with metadata
        extracted_stamps: Individual stamp images (if mode is EXTRACT or BOTH)
        processing_time_ms: Processing time in milliseconds
    """

    cleaned_image: np.ndarray | None
    stamp_mask: np.ndarray
    stamp_regions: list[StampRegion]
    extracted_stamps: list[np.ndarray]
    processing_time_ms: float

    @property
    def has_stamps(self) -> bool:
        """Check if any stamps were detected."""
        return len(self.stamp_regions) > 0

    @property
    def total_stamp_area(self) -> int:
        """Total area covered by stamps."""
        return sum(r["area"] for r in self.stamp_regions)

    @property
    def stamp_colors_found(self) -> list[str]:
        """Unique colors of detected stamps."""
        return list(set(r["color"] for r in self.stamp_regions))


class StampSegmenter:
    """
    HSV-based stamp segmentation for legal document images.

    Main capabilities:
    1. Detect colored stamps using HSV color space segmentation
    2. Remove stamps for clean OCR (replace with white)
    3. Extract stamp regions for separate analysis
    4. Provide metadata about detected stamps

    Example:
        >>> segmenter = StampSegmenter()
        >>> img = cv2.imread("document.png")
        >>> result = segmenter.process(img)
        >>> if result.has_stamps:
        ...     print(f"Found {len(result.stamp_regions)} stamps")
        ...     cleaned = result.cleaned_image
    """

    def __init__(self, config: StampSegmenterConfig | None = None):
        """
        Initialize StampSegmenter.

        Args:
            config: Configuration options. Uses defaults if not provided.
        """
        self.config = config or StampSegmenterConfig()

    @classmethod
    def for_ocr(cls) -> StampSegmenter:
        """
        Create segmenter optimized for OCR pre-processing.

        Uses aggressive settings to remove all stamp colors.
        """
        config = StampSegmenterConfig(
            colors=[StampColor.BLUE, StampColor.RED, StampColor.GREEN, StampColor.PURPLE],
            mode=StampMode.REMOVE,
            dilate_iterations=3,  # More aggressive edge capture
            min_area=50,  # Catch smaller stamp fragments
        )
        return cls(config)

    @classmethod
    def for_extraction(cls) -> StampSegmenter:
        """
        Create segmenter optimized for stamp extraction.

        Uses conservative settings to extract clean stamp regions.
        """
        config = StampSegmenterConfig(
            colors=[StampColor.BLUE, StampColor.RED, StampColor.GREEN],
            mode=StampMode.EXTRACT,
            dilate_iterations=1,  # Less dilation to keep stamp boundaries tight
            min_area=200,  # Filter small noise
            confidence_threshold=0.4,  # Higher confidence required
        )
        return cls(config)

    def _create_color_mask(self, hsv_image: np.ndarray, ranges: list[HSVRange]) -> np.ndarray:
        """
        Create binary mask for specified HSV ranges.

        Args:
            hsv_image: Image in HSV color space
            ranges: List of HSV ranges to detect

        Returns:
            Binary mask (255 where color detected, 0 elsewhere)
        """
        combined_mask = np.zeros(hsv_image.shape[:2], dtype=np.uint8)

        for hsv_range in ranges:
            lower, upper = hsv_range.to_opencv_bounds()
            mask = cv2.inRange(hsv_image, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, mask)

        return combined_mask

    def _refine_mask(self, mask: np.ndarray) -> np.ndarray:
        """
        Refine the stamp mask using morphological operations.

        Operations:
        1. Morphological closing to fill small gaps in stamps
        2. Dilation to capture stamp edges
        3. Optional Gaussian blur for smoother edges

        Args:
            mask: Raw binary mask from color detection

        Returns:
            Refined binary mask
        """
        # Morphological closing: fills small holes in detected regions
        close_kernel = np.ones(
            (self.config.morph_close_kernel, self.config.morph_close_kernel),
            dtype=np.uint8,
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel)

        # Dilation: expands mask to capture blurred stamp edges
        dilate_kernel = np.ones(
            (self.config.dilate_kernel, self.config.dilate_kernel),
            dtype=np.uint8,
        )
        mask = cv2.dilate(mask, dilate_kernel, iterations=self.config.dilate_iterations)

        return mask

    def _extract_stamp_regions(
        self,
        mask: np.ndarray,
        original_bgr: np.ndarray,
        hsv_image: np.ndarray,
    ) -> tuple[list[StampRegion], list[np.ndarray]]:
        """
        Extract individual stamp regions from mask.

        Args:
            mask: Binary mask of detected stamps
            original_bgr: Original image in BGR format
            hsv_image: Image in HSV format for color analysis

        Returns:
            Tuple of (stamp_regions metadata, extracted stamp images)
        """
        regions: list[StampRegion] = []
        extracted: list[np.ndarray] = []

        # Find contours in mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        image_area = mask.shape[0] * mask.shape[1]
        max_area = int(image_area * self.config.max_area_ratio)

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by area
            if area < self.config.min_area or area > max_area:
                continue

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Calculate centroid
            M = cv2.moments(contour)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = x + w // 2, y + h // 2

            # Determine dominant color from HSV
            roi_mask = np.zeros(mask.shape, dtype=np.uint8)
            cv2.drawContours(roi_mask, [contour], -1, 255, -1)

            hsv_roi = hsv_image[roi_mask > 0]
            if len(hsv_roi) > 0:
                mean_h = np.mean(hsv_roi[:, 0])
                mean_s = np.mean(hsv_roi[:, 1])

                # Determine color name based on hue
                # OpenCV uses H: 0-180 (half of standard 0-360)
                # Red wraps around 0/180, so check both ends
                if mean_h < 10 or mean_h > 170:
                    color_name = "red"
                elif 35 <= mean_h <= 85:
                    color_name = "green"
                elif 85 < mean_h <= 135:
                    # Blue range: 85-135 covers cyan, azure, and pure blue
                    # Pure blue in BGR (255, 0, 0) = H=120
                    # Cyan-ish blues (255, 150, 50) = H~105
                    color_name = "blue"
                elif 135 < mean_h <= 165:
                    color_name = "purple"
                else:
                    color_name = "unknown"

                # Confidence based on saturation (higher S = more certain it's a colored stamp)
                confidence = min(1.0, mean_s / 255.0 * 1.5)
            else:
                color_name = "unknown"
                confidence = 0.0

            # Skip low confidence detections
            if confidence < self.config.confidence_threshold:
                continue

            # Create region metadata
            region: StampRegion = {
                "color": color_name,
                "bbox": (x, y, w, h),
                "area": int(area),
                "centroid": (cx, cy),
                "confidence": round(confidence, 3),
                "contour_points": len(contour),
            }
            regions.append(region)

            # Extract stamp image if needed
            if self.config.mode in (StampMode.EXTRACT, StampMode.BOTH):
                stamp_img = original_bgr[y : y + h, x : x + w].copy()
                extracted.append(stamp_img)

        return regions, extracted

    def _remove_stamps(self, image: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Remove stamps from image by replacing masked regions with white.

        Args:
            image: Original image (BGR)
            mask: Binary mask of stamp regions

        Returns:
            Image with stamps removed (grayscale)
        """
        result = image.copy()

        # Paint masked regions white
        result[mask > 0] = [255, 255, 255]

        # Convert to grayscale
        result_gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)

        return result_gray

    def process(self, image: np.ndarray | Image.Image) -> StampSegmentationResult:
        """
        Process image to detect, extract, or remove colored stamps.

        Args:
            image: Input image (BGR numpy array or PIL Image)

        Returns:
            StampSegmentationResult with processed data

        Example:
            >>> segmenter = StampSegmenter()
            >>> result = segmenter.process(cv2.imread("scan.png"))
            >>> print(f"Found stamps: {result.has_stamps}")
            >>> print(f"Colors: {result.stamp_colors_found}")
        """
        import time

        start_time = time.perf_counter()

        # Convert PIL to numpy if needed
        if isinstance(image, Image.Image):
            image = np.array(image)
            # PIL is RGB, OpenCV expects BGR
            if len(image.shape) == 3 and image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Ensure we have a color image
        if len(image.shape) == 2:
            # Grayscale - convert to BGR for processing
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Optional: pre-process with Gaussian blur to reduce noise
        if self.config.blur_kernel > 1:
            image_blurred = cv2.GaussianBlur(
                image, (self.config.blur_kernel, self.config.blur_kernel), 0
            )
        else:
            image_blurred = image

        # Convert to HSV color space
        hsv_image = cv2.cvtColor(image_blurred, cv2.COLOR_BGR2HSV)

        # Get HSV ranges for detection
        hsv_ranges = self.config.get_hsv_ranges()

        # Create color mask
        raw_mask = self._create_color_mask(hsv_image, hsv_ranges)

        # Refine mask
        refined_mask = self._refine_mask(raw_mask)

        # Extract regions and metadata
        regions, extracted_stamps = self._extract_stamp_regions(refined_mask, image, hsv_image)

        # Remove stamps if mode requires it
        cleaned_image = None
        if self.config.mode in (StampMode.REMOVE, StampMode.BOTH):
            cleaned_image = self._remove_stamps(image, refined_mask)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return StampSegmentationResult(
            cleaned_image=cleaned_image,
            stamp_mask=refined_mask,
            stamp_regions=regions,
            extracted_stamps=extracted_stamps,
            processing_time_ms=round(elapsed_ms, 2),
        )

    def process_pil(self, image: Image.Image) -> tuple[Image.Image | None, list[StampRegion]]:
        """
        Convenience method for PIL Image processing.

        Args:
            image: PIL Image

        Returns:
            Tuple of (cleaned PIL Image or None, list of stamp regions)
        """
        result = self.process(image)

        cleaned_pil = None
        if result.cleaned_image is not None:
            cleaned_pil = Image.fromarray(result.cleaned_image, mode="L")

        return cleaned_pil, result.stamp_regions


# Convenience functions for common use cases


def remove_stamps_for_ocr(image: np.ndarray | Image.Image) -> np.ndarray:
    """
    Remove all colored stamps from image for OCR.

    This is a convenience function for the most common use case.

    Args:
        image: Input image (BGR numpy or PIL)

    Returns:
        Grayscale image with stamps removed
    """
    segmenter = StampSegmenter.for_ocr()
    result = segmenter.process(image)
    return result.cleaned_image


def extract_stamps(
    image: np.ndarray | Image.Image,
) -> tuple[list[np.ndarray], list[StampRegion]]:
    """
    Extract stamp regions from image.

    Args:
        image: Input image (BGR numpy or PIL)

    Returns:
        Tuple of (list of stamp images, list of stamp metadata)
    """
    segmenter = StampSegmenter.for_extraction()
    result = segmenter.process(image)
    return result.extracted_stamps, result.stamp_regions


def detect_stamps(
    image: np.ndarray | Image.Image,
    colors: list[StampColor] | None = None,
) -> list[StampRegion]:
    """
    Detect stamps in image and return metadata only.

    Args:
        image: Input image (BGR numpy or PIL)
        colors: Specific colors to detect (default: blue, red, green)

    Returns:
        List of StampRegion metadata dicts
    """
    config = StampSegmenterConfig(
        colors=colors or [StampColor.BLUE, StampColor.RED, StampColor.GREEN],
        mode=StampMode.REMOVE,  # We still need mask for detection
    )
    segmenter = StampSegmenter(config)
    result = segmenter.process(image)
    return result.stamp_regions
