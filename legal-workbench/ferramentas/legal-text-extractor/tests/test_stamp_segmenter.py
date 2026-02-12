#!/usr/bin/env python3
"""
Unit tests for StampSegmenter - HSV-based colored stamp detection.

Tests cover:
1. HSV range validation and configuration
2. Color mask creation for different stamp colors
3. Stamp detection with various shapes and sizes
4. Removal mode (stamps replaced with white)
5. Extraction mode (individual stamp images)
6. Metadata accuracy (bbox, area, centroid, color)
7. Edge cases (no stamps, overlapping stamps, low contrast)

Execution:
    cd ferramentas/legal-text-extractor
    source .venv/bin/activate
    pytest tests/test_stamp_segmenter.py -v
"""

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest
from PIL import Image

# Adiciona o diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.stamp_segmenter import (
    HSVRange,
    StampColor,
    StampMode,
    StampSegmenter,
    StampSegmenterConfig,
    detect_stamps,
    extract_stamps,
    remove_stamps_for_ocr,
)

# =============================================================================
# Test Fixtures - Synthetic Images
# =============================================================================


def create_white_background(height: int = 400, width: int = 600) -> np.ndarray:
    """Create white background image (BGR)."""
    return np.full((height, width, 3), 255, dtype=np.uint8)


def create_blue_stamp_image() -> np.ndarray:
    """
    Create synthetic image with blue stamp.

    Blue in BGR: (255, 150, 50) -> HSV: (105, 200, 255)
    """
    img = create_white_background()

    # Add black text
    cv2.rectangle(img, (50, 30), (550, 70), (0, 0, 0), -1)

    # Add blue stamp (circular)
    center = (300, 200)
    cv2.circle(img, center, 60, (255, 150, 50), -1)  # Blue in BGR
    cv2.circle(img, center, 50, (255, 180, 80), -1)  # Lighter blue center

    # Add text in stamp
    cv2.putText(img, "RECEBIDO", (240, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return img


def create_red_stamp_image() -> np.ndarray:
    """
    Create synthetic image with red stamp.

    Red in BGR: (50, 50, 255) -> HSV: (0, 200, 255)
    """
    img = create_white_background()

    # Add black text
    cv2.rectangle(img, (50, 30), (550, 70), (0, 0, 0), -1)

    # Add red rectangular stamp
    cv2.rectangle(img, (200, 150), (400, 250), (50, 50, 255), -1)  # Red in BGR

    return img


def create_green_stamp_image() -> np.ndarray:
    """
    Create synthetic image with green stamp.

    Green in BGR: (50, 200, 50) -> HSV: (60, 192, 200)
    """
    img = create_white_background()

    # Add black text
    cv2.rectangle(img, (50, 30), (550, 70), (0, 0, 0), -1)

    # Add green elliptical stamp
    cv2.ellipse(img, (300, 200), (80, 50), 0, 0, 360, (50, 200, 50), -1)

    return img


def create_multi_stamp_image() -> np.ndarray:
    """Create image with multiple stamps of different colors."""
    img = create_white_background(500, 700)

    # Add black text
    cv2.rectangle(img, (50, 30), (650, 70), (0, 0, 0), -1)
    cv2.rectangle(img, (50, 400), (650, 440), (0, 0, 0), -1)

    # Blue stamp (top-left)
    cv2.circle(img, (150, 200), 50, (255, 150, 50), -1)

    # Red stamp (top-right)
    cv2.rectangle(img, (450, 150), (600, 250), (50, 50, 255), -1)

    # Green stamp (bottom-center)
    cv2.ellipse(img, (350, 320), (60, 40), 0, 0, 360, (50, 200, 50), -1)

    return img


def create_no_stamp_image() -> np.ndarray:
    """Create image with no colored stamps (only black text)."""
    img = create_white_background()

    # Add black text
    cv2.rectangle(img, (50, 30), (550, 70), (0, 0, 0), -1)
    cv2.rectangle(img, (50, 100), (400, 140), (0, 0, 0), -1)
    cv2.rectangle(img, (50, 170), (500, 210), (0, 0, 0), -1)

    # Add gray element (should not be detected as stamp)
    cv2.rectangle(img, (200, 250), (400, 350), (150, 150, 150), -1)

    return img


def create_low_saturation_stamp() -> np.ndarray:
    """Create image with low saturation blue (should not be detected)."""
    img = create_white_background()

    # Add desaturated blue (low S value)
    # BGR: (200, 200, 220) -> very low saturation
    cv2.circle(img, (300, 200), 60, (200, 200, 220), -1)

    return img


# =============================================================================
# Test Classes
# =============================================================================


class TestHSVRange:
    """Tests for HSVRange configuration class."""

    def test_valid_range_creation(self):
        """Test creating valid HSV range."""
        hsv = HSVRange(h_min=100, h_max=130, s_min=50, v_min=50)

        assert hsv.h_min == 100
        assert hsv.h_max == 130
        assert hsv.s_min == 50
        assert hsv.s_max == 255
        assert hsv.v_min == 50
        assert hsv.v_max == 255

    def test_to_opencv_bounds(self):
        """Test conversion to OpenCV inRange format."""
        hsv = HSVRange(h_min=100, h_max=130, s_min=50, v_min=50, name="blue")
        lower, upper = hsv.to_opencv_bounds()

        np.testing.assert_array_equal(lower, [100, 50, 50])
        np.testing.assert_array_equal(upper, [130, 255, 255])

    def test_invalid_h_min(self):
        """Test that invalid h_min raises error."""
        with pytest.raises(ValueError, match="h_min must be 0-180"):
            HSVRange(h_min=200, h_max=130)

    def test_invalid_h_max(self):
        """Test that invalid h_max raises error."""
        with pytest.raises(ValueError, match="h_max must be 0-180"):
            HSVRange(h_min=100, h_max=200)

    def test_invalid_s_min(self):
        """Test that invalid s_min raises error."""
        with pytest.raises(ValueError, match="s_min must be 0-255"):
            HSVRange(h_min=100, h_max=130, s_min=300)


class TestStampSegmenterConfig:
    """Tests for StampSegmenterConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = StampSegmenterConfig()

        assert StampColor.BLUE in config.colors
        assert StampColor.RED in config.colors
        assert StampColor.GREEN in config.colors
        assert config.mode == StampMode.REMOVE
        assert config.min_area == 100
        assert config.max_area_ratio == 0.3

    def test_get_hsv_ranges_default(self):
        """Test getting default HSV ranges."""
        config = StampSegmenterConfig()
        ranges = config.get_hsv_ranges()

        # Should have ranges for blue, red (2 ranges), and green
        assert len(ranges) >= 4

    def test_get_hsv_ranges_custom(self):
        """Test that custom ranges override default."""
        custom_range = HSVRange(h_min=50, h_max=70, name="yellow")
        config = StampSegmenterConfig(custom_ranges=[custom_range])
        ranges = config.get_hsv_ranges()

        assert len(ranges) == 1
        assert ranges[0].name == "yellow"


class TestStampSegmenter:
    """Core tests for StampSegmenter."""

    def test_detect_blue_stamp(self):
        """Test detection of blue stamp."""
        img = create_blue_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        assert result.has_stamps
        assert len(result.stamp_regions) >= 1

        # Check color detection
        colors = [r["color"] for r in result.stamp_regions]
        assert "blue" in colors

    def test_detect_red_stamp(self):
        """Test detection of red stamp."""
        img = create_red_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        assert result.has_stamps
        colors = [r["color"] for r in result.stamp_regions]
        assert "red" in colors

    def test_detect_green_stamp(self):
        """Test detection of green stamp."""
        img = create_green_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        assert result.has_stamps
        colors = [r["color"] for r in result.stamp_regions]
        assert "green" in colors

    def test_detect_multiple_stamps(self):
        """Test detection of multiple stamps."""
        img = create_multi_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        assert result.has_stamps
        assert len(result.stamp_regions) >= 3

        colors = set(r["color"] for r in result.stamp_regions)
        assert "blue" in colors
        assert "red" in colors
        assert "green" in colors

    def test_no_stamps_detected(self):
        """Test that no stamps are detected in clean image."""
        img = create_no_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        assert not result.has_stamps
        assert len(result.stamp_regions) == 0

    def test_low_saturation_not_detected(self):
        """Test that low saturation colors are not detected as stamps."""
        img = create_low_saturation_stamp()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        # Should not detect the low saturation "blue"
        assert not result.has_stamps

    def test_remove_mode(self):
        """Test that remove mode cleans stamps from image."""
        img = create_blue_stamp_image()
        config = StampSegmenterConfig(mode=StampMode.REMOVE)
        segmenter = StampSegmenter(config)
        result = segmenter.process(img)

        assert result.cleaned_image is not None
        assert len(result.cleaned_image.shape) == 2  # Grayscale

        # The stamp region should be mostly white now
        stamp = result.stamp_regions[0]
        x, y, w, h = stamp["bbox"]
        region = result.cleaned_image[y : y + h, x : x + w]
        mean_intensity = np.mean(region)

        # Should be bright (stamp removed)
        assert mean_intensity > 200

    def test_extract_mode(self):
        """Test that extract mode returns stamp images."""
        img = create_multi_stamp_image()
        config = StampSegmenterConfig(mode=StampMode.EXTRACT)
        segmenter = StampSegmenter(config)
        result = segmenter.process(img)

        assert len(result.extracted_stamps) == len(result.stamp_regions)

        # Each extracted stamp should be a valid image
        for stamp_img in result.extracted_stamps:
            assert stamp_img is not None
            assert len(stamp_img.shape) == 3  # BGR
            assert stamp_img.shape[2] == 3

    def test_both_mode(self):
        """Test that both mode returns cleaned image and extracted stamps."""
        img = create_blue_stamp_image()
        config = StampSegmenterConfig(mode=StampMode.BOTH)
        segmenter = StampSegmenter(config)
        result = segmenter.process(img)

        assert result.cleaned_image is not None
        assert len(result.extracted_stamps) >= 1

    def test_stamp_metadata_bbox(self):
        """Test that bounding box is accurate."""
        img = create_blue_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        stamp = result.stamp_regions[0]
        x, y, w, h = stamp["bbox"]

        # Blue stamp is centered at (300, 200) with radius 60
        # So bbox should be approximately (240, 140, 120, 120)
        assert 200 < x < 280  # x should be around 240
        assert 100 < y < 180  # y should be around 140
        assert 100 < w < 150  # width should be around 120
        assert 100 < h < 150  # height should be around 120

    def test_stamp_metadata_area(self):
        """Test that area calculation is reasonable."""
        img = create_blue_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        stamp = result.stamp_regions[0]
        area = stamp["area"]

        # Blue stamp is circle with radius ~60
        # Area should be approximately pi * 60^2 = ~11310
        assert 5000 < area < 20000

    def test_stamp_metadata_centroid(self):
        """Test that centroid is accurate."""
        img = create_blue_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        stamp = result.stamp_regions[0]
        cx, cy = stamp["centroid"]

        # Blue stamp is centered at (300, 200)
        assert 250 < cx < 350
        assert 150 < cy < 250

    def test_stamp_metadata_confidence(self):
        """Test that confidence is valid."""
        img = create_blue_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        stamp = result.stamp_regions[0]
        confidence = stamp["confidence"]

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.3  # Should have reasonable confidence

    def test_processing_time(self):
        """Test that processing time is recorded."""
        img = create_blue_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        assert result.processing_time_ms > 0
        assert result.processing_time_ms < 1000  # Should be fast

    def test_pil_input(self):
        """Test that PIL Image input works."""
        img_bgr = create_blue_stamp_image()
        # Convert BGR to RGB for PIL
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        segmenter = StampSegmenter()
        result = segmenter.process(img_pil)

        assert result.has_stamps

    def test_grayscale_input(self):
        """Test that grayscale input is handled."""
        img_bgr = create_blue_stamp_image()
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        segmenter = StampSegmenter()
        result = segmenter.process(img_gray)

        # Grayscale has no color info, so no stamps should be detected
        assert not result.has_stamps

    def test_for_ocr_factory(self):
        """Test for_ocr factory method."""
        segmenter = StampSegmenter.for_ocr()

        assert StampColor.PURPLE in segmenter.config.colors
        assert segmenter.config.mode == StampMode.REMOVE
        assert segmenter.config.dilate_iterations == 3

    def test_for_extraction_factory(self):
        """Test for_extraction factory method."""
        segmenter = StampSegmenter.for_extraction()

        assert segmenter.config.mode == StampMode.EXTRACT
        assert segmenter.config.dilate_iterations == 1
        assert segmenter.config.confidence_threshold == 0.4

    def test_process_pil_convenience(self):
        """Test process_pil convenience method."""
        img_bgr = create_blue_stamp_image()
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        segmenter = StampSegmenter()
        cleaned_pil, regions = segmenter.process_pil(img_pil)

        assert cleaned_pil is not None
        assert isinstance(cleaned_pil, Image.Image)
        assert cleaned_pil.mode == "L"  # Grayscale
        assert len(regions) >= 1


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_remove_stamps_for_ocr(self):
        """Test remove_stamps_for_ocr function."""
        img = create_blue_stamp_image()
        cleaned = remove_stamps_for_ocr(img)

        assert cleaned is not None
        assert len(cleaned.shape) == 2  # Grayscale

    def test_extract_stamps(self):
        """Test extract_stamps function."""
        img = create_multi_stamp_image()
        stamps, metadata = extract_stamps(img)

        assert len(stamps) >= 1
        assert len(metadata) == len(stamps)

    def test_detect_stamps(self):
        """Test detect_stamps function."""
        img = create_multi_stamp_image()
        regions = detect_stamps(img)

        assert len(regions) >= 3
        colors = [r["color"] for r in regions]
        assert "blue" in colors

    def test_detect_stamps_with_color_filter(self):
        """Test detect_stamps with specific color."""
        img = create_multi_stamp_image()
        regions = detect_stamps(img, colors=[StampColor.BLUE])

        # Should only find blue stamps
        for region in regions:
            assert region["color"] == "blue"


class TestStampSegmentationResult:
    """Tests for StampSegmentationResult helper properties."""

    def test_has_stamps_true(self):
        """Test has_stamps returns True when stamps found."""
        img = create_blue_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        assert result.has_stamps is True

    def test_has_stamps_false(self):
        """Test has_stamps returns False when no stamps."""
        img = create_no_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        assert result.has_stamps is False

    def test_total_stamp_area(self):
        """Test total_stamp_area calculation."""
        img = create_multi_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        total_area = result.total_stamp_area
        individual_sum = sum(r["area"] for r in result.stamp_regions)

        assert total_area == individual_sum
        assert total_area > 0

    def test_stamp_colors_found(self):
        """Test stamp_colors_found returns unique colors."""
        img = create_multi_stamp_image()
        segmenter = StampSegmenter()
        result = segmenter.process(img)

        colors = result.stamp_colors_found
        assert "blue" in colors
        assert "red" in colors
        assert "green" in colors


# =============================================================================
# Integration with ImageCleaner
# =============================================================================


class TestImageCleanerIntegration:
    """Tests for integration with ImageCleaner module."""

    def test_process_stamps_advanced_remove(self):
        """Test process_stamps_advanced in remove mode."""
        from src.core.image_cleaner import process_stamps_advanced

        img = create_blue_stamp_image()
        cleaned, metadata = process_stamps_advanced(img, mode="remove")

        assert cleaned is not None
        assert len(metadata) >= 1

    def test_process_stamps_advanced_detect(self):
        """Test process_stamps_advanced in detect mode."""
        from src.core.image_cleaner import process_stamps_advanced

        img = create_multi_stamp_image()
        cleaned, metadata = process_stamps_advanced(img, mode="detect")

        assert cleaned is None  # detect mode doesn't return image
        assert len(metadata) >= 3

    def test_process_stamps_advanced_color_filter(self):
        """Test process_stamps_advanced with color filter."""
        from src.core.image_cleaner import process_stamps_advanced

        img = create_multi_stamp_image()
        _, metadata = process_stamps_advanced(img, mode="detect", colors=["blue", "red"])

        colors = [m["color"] for m in metadata]
        # Should only have blue and red
        for color in colors:
            assert color in ["blue", "red"]

    def test_detect_colored_stamps(self):
        """Test detect_colored_stamps convenience function."""
        from src.core.image_cleaner import detect_colored_stamps

        img = create_blue_stamp_image()
        stamps = detect_colored_stamps(img)

        assert len(stamps) >= 1
        assert stamps[0]["color"] == "blue"

    def test_remove_stamps_for_ocr_integration(self):
        """Test remove_stamps_for_ocr from image_cleaner module."""
        from src.core.image_cleaner import remove_stamps_for_ocr as remove_fn

        img = create_red_stamp_image()
        cleaned = remove_fn(img)

        assert cleaned is not None
        assert len(cleaned.shape) == 2

    def test_extract_stamp_images(self):
        """Test extract_stamp_images function."""
        from src.core.image_cleaner import extract_stamp_images

        img = create_multi_stamp_image()
        stamps, metadata = extract_stamp_images(img)

        assert len(stamps) >= 1
        assert len(metadata) == len(stamps)


# =============================================================================
# Run Tests
# =============================================================================


def run_tests():
    """Run all tests manually."""
    print("\n" + "=" * 60)
    print("STAMP SEGMENTER - TEST SUITE")
    print("=" * 60 + "\n")

    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
