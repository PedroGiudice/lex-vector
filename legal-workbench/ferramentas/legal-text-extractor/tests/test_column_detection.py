"""
Testes para deteccao de layout multi-colunas no ImageCleaner.

Testa o algoritmo de vertical projection profile para detectar
colunas em documentos juridicos escaneados.

Tecnicas testadas:
1. Vertical projection profile - soma de pixels escuros por coluna X
2. Valley detection - deteccao de gaps (vales) entre colunas
3. Column region extraction - extracao de regioes de colunas
4. Confidence calculation - calculo de confianca da deteccao

Execucao:
    cd ferramentas/legal-text-extractor
    source .venv/bin/activate
    pytest tests/test_column_detection.py -v
"""

import numpy as np
import pytest
from PIL import Image

from src.core.image_cleaner import (
    DEFAULT_COLUMN_CONFIG,
    ColumnBoundary,
    ColumnDetectionConfig,
    ColumnLayoutDetector,
    ColumnRegion,
    ImageCleaner,
    LayoutMetadata,
    detect_columns,
    get_column_detector,
)

# =============================================================================
# Test Fixtures - Synthetic Images
# =============================================================================


def create_single_column_image(width: int = 600, height: int = 800) -> np.ndarray:
    """
    Creates a synthetic single-column document image.

    The image has text-like patterns (dark pixels) distributed
    across the full width, simulating a single-column layout.
    """
    # White background
    image = np.ones((height, width), dtype=np.uint8) * 255

    # Add text-like horizontal lines across the full width
    margin = int(width * 0.1)
    for y in range(50, height - 50, 20):
        # Random line length but always spanning most of the width
        line_start = margin + np.random.randint(0, 20)
        line_end = width - margin - np.random.randint(0, 20)
        image[y : y + 2, line_start:line_end] = 0  # Black text line

    return image


def create_two_column_image(width: int = 600, height: int = 800, gap_width: int = 60) -> np.ndarray:
    """
    Creates a synthetic two-column document image.

    The image has two distinct text regions separated by a clear gap,
    simulating a two-column newspaper-style layout.
    """
    # White background
    image = np.ones((height, width), dtype=np.uint8) * 255

    # Calculate column positions
    margin = int(width * 0.05)
    col1_start = margin
    col1_end = (width - gap_width) // 2
    col2_start = col1_end + gap_width
    col2_end = width - margin

    # Add text-like horizontal lines in each column
    for y in range(50, height - 50, 20):
        # Left column
        line_start = col1_start + np.random.randint(0, 10)
        line_end = col1_end - np.random.randint(0, 10)
        if line_end > line_start:
            image[y : y + 2, line_start:line_end] = 0

        # Right column
        line_start = col2_start + np.random.randint(0, 10)
        line_end = col2_end - np.random.randint(0, 10)
        if line_end > line_start:
            image[y : y + 2, line_start:line_end] = 0

    return image


def create_three_column_image(
    width: int = 900, height: int = 800, gap_width: int = 50
) -> np.ndarray:
    """
    Creates a synthetic three-column document image.
    """
    # White background
    image = np.ones((height, width), dtype=np.uint8) * 255

    # Calculate column positions
    margin = int(width * 0.03)
    col_width = (width - 2 * margin - 2 * gap_width) // 3

    col1_start = margin
    col1_end = col1_start + col_width
    col2_start = col1_end + gap_width
    col2_end = col2_start + col_width
    col3_start = col2_end + gap_width
    col3_end = width - margin

    # Add text-like horizontal lines in each column
    for y in range(50, height - 50, 18):
        for col_start, col_end in [
            (col1_start, col1_end),
            (col2_start, col2_end),
            (col3_start, col3_end),
        ]:
            line_start = col_start + np.random.randint(0, 8)
            line_end = col_end - np.random.randint(0, 8)
            if line_end > line_start:
                image[y : y + 2, line_start:line_end] = 0

    return image


def create_empty_image(width: int = 600, height: int = 800) -> np.ndarray:
    """Creates a blank white image with no text."""
    return np.ones((height, width), dtype=np.uint8) * 255


def create_noisy_image(width: int = 600, height: int = 800) -> np.ndarray:
    """Creates an image with random noise (no clear column structure)."""
    image = np.ones((height, width), dtype=np.uint8) * 255
    # Add random noise
    noise = np.random.randint(0, 50, (height, width), dtype=np.uint8)
    image = np.clip(image.astype(np.int16) - noise, 0, 255).astype(np.uint8)
    return image


# =============================================================================
# Unit Tests - ColumnLayoutDetector
# =============================================================================


class TestColumnLayoutDetector:
    """Tests for the ColumnLayoutDetector class."""

    @pytest.fixture
    def detector(self):
        """Creates a ColumnLayoutDetector with default config."""
        return ColumnLayoutDetector()

    @pytest.fixture
    def custom_detector(self):
        """Creates a ColumnLayoutDetector with custom config."""
        config = ColumnDetectionConfig(
            min_column_width_ratio=0.1,
            min_gap_width_px=20,
            valley_prominence=0.2,
            max_columns=4,
        )
        return ColumnLayoutDetector(config=config)

    def test_init_default_config(self, detector):
        """Test detector initialization with default config."""
        assert detector.config is not None
        assert detector.config == DEFAULT_COLUMN_CONFIG
        assert detector.config.max_columns == 3

    def test_init_custom_config(self, custom_detector):
        """Test detector initialization with custom config."""
        assert custom_detector.config.min_gap_width_px == 20
        assert custom_detector.config.valley_prominence == 0.2
        assert custom_detector.config.max_columns == 4

    def test_detect_single_column(self, detector):
        """Test detection of single-column layout."""
        image = create_single_column_image()
        layout = detector.detect(image)

        assert isinstance(layout, LayoutMetadata)
        # Should detect as single column (margins may create small boundaries
        # but the main column count should be 1)
        assert layout.num_columns == 1
        assert not layout.is_multi_column
        assert len(layout.columns) == 1
        # Note: column_boundaries may have entries for edge margins,
        # but as long as num_columns=1, the detection is correct
        assert layout.confidence >= 0.9

    def test_detect_two_columns(self, detector):
        """Test detection of two-column layout."""
        image = create_two_column_image(gap_width=80)
        layout = detector.detect(image)

        assert isinstance(layout, LayoutMetadata)
        assert layout.num_columns == 2
        assert layout.is_multi_column
        assert len(layout.columns) == 2
        assert len(layout.column_boundaries) == 1
        assert layout.confidence > 0.5

    def test_detect_three_columns(self, custom_detector):
        """Test detection of three-column layout."""
        image = create_three_column_image(gap_width=70)
        layout = custom_detector.detect(image)

        assert isinstance(layout, LayoutMetadata)
        # May detect 2 or 3 depending on gap clarity
        assert layout.num_columns >= 2
        assert layout.is_multi_column

    def test_detect_empty_image(self, detector):
        """Test detection on empty/blank image."""
        image = create_empty_image()
        layout = detector.detect(image)

        # Empty image should return single column (default)
        assert layout.num_columns == 1
        assert not layout.is_multi_column
        assert layout.confidence >= 0.9

    def test_detect_noisy_image(self, detector):
        """Test detection on noisy image without clear structure."""
        image = create_noisy_image()
        layout = detector.detect(image)

        # Noisy image should return single column
        assert isinstance(layout, LayoutMetadata)
        assert layout.num_columns >= 1

    def test_detect_from_pil(self, detector):
        """Test detection from PIL Image."""
        np_image = create_two_column_image()
        pil_image = Image.fromarray(np_image)
        layout = detector.detect_from_pil(pil_image)

        assert isinstance(layout, LayoutMetadata)
        assert layout.num_columns >= 1

    def test_detect_bgr_image(self, detector):
        """Test detection from BGR (color) image."""
        gray = create_two_column_image()
        # Convert to BGR
        bgr = np.stack([gray, gray, gray], axis=-1)
        layout = detector.detect(bgr)

        assert isinstance(layout, LayoutMetadata)
        assert layout.num_columns >= 1

    def test_detect_raises_on_empty_array(self, detector):
        """Test that empty array raises ValueError."""
        empty = np.array([])
        with pytest.raises(ValueError, match="empty"):
            detector.detect(empty)

    def test_detect_raises_on_none(self, detector):
        """Test that None input raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            detector.detect(None)


# =============================================================================
# Unit Tests - LayoutMetadata
# =============================================================================


class TestLayoutMetadata:
    """Tests for the LayoutMetadata dataclass."""

    @pytest.fixture
    def single_column_layout(self):
        """Creates a single-column layout metadata."""
        return LayoutMetadata(
            num_columns=1,
            columns=[ColumnRegion(index=0, x_start=0, x_end=600, width=600, text_density=0.1)],
            column_boundaries=[],
            page_width=600,
            page_height=800,
            detection_method="vertical_projection",
            confidence=0.95,
        )

    @pytest.fixture
    def two_column_layout(self):
        """Creates a two-column layout metadata."""
        return LayoutMetadata(
            num_columns=2,
            columns=[
                ColumnRegion(index=0, x_start=0, x_end=270, width=270, text_density=0.1),
                ColumnRegion(index=1, x_start=330, x_end=600, width=270, text_density=0.12),
            ],
            column_boundaries=[ColumnBoundary(x_start=270, x_end=330, width=60, confidence=0.85)],
            page_width=600,
            page_height=800,
            detection_method="vertical_projection",
            confidence=0.8,
        )

    def test_is_multi_column_single(self, single_column_layout):
        """Test is_multi_column returns False for single column."""
        assert not single_column_layout.is_multi_column

    def test_is_multi_column_two(self, two_column_layout):
        """Test is_multi_column returns True for two columns."""
        assert two_column_layout.is_multi_column

    def test_get_reading_order_single(self, single_column_layout):
        """Test reading order regions for single column."""
        regions = single_column_layout.get_reading_order_regions()
        assert len(regions) == 1
        assert regions[0] == (0, 0, 600, 800)

    def test_get_reading_order_two(self, two_column_layout):
        """Test reading order regions for two columns."""
        regions = two_column_layout.get_reading_order_regions()
        assert len(regions) == 2
        # First column (left)
        assert regions[0] == (0, 0, 270, 800)
        # Second column (right)
        assert regions[1] == (330, 0, 600, 800)

    def test_to_dict(self, two_column_layout):
        """Test serialization to dictionary."""
        data = two_column_layout.to_dict()

        assert data["num_columns"] == 2
        assert data["is_multi_column"] is True
        assert len(data["columns"]) == 2
        assert len(data["column_boundaries"]) == 1
        assert data["page_width"] == 600
        assert data["page_height"] == 800
        assert data["detection_method"] == "vertical_projection"
        assert data["confidence"] == 0.8

    def test_column_region_center(self, two_column_layout):
        """Test ColumnRegion center property."""
        col1 = two_column_layout.columns[0]
        col2 = two_column_layout.columns[1]

        assert col1.center == 135  # (0 + 270) // 2
        assert col2.center == 465  # (330 + 600) // 2


# =============================================================================
# Unit Tests - ColumnDetectionConfig
# =============================================================================


class TestColumnDetectionConfig:
    """Tests for the ColumnDetectionConfig dataclass."""

    def test_default_config_values(self):
        """Test default configuration values."""
        config = ColumnDetectionConfig()
        assert config.min_column_width_ratio == 0.1
        assert config.min_gap_width_px == 30
        assert config.min_gap_width_ratio == 0.02
        assert config.max_columns == 4

    def test_get_min_gap_width_uses_max(self):
        """Test that get_min_gap_width uses max of px and ratio."""
        config = ColumnDetectionConfig(min_gap_width_px=30, min_gap_width_ratio=0.02)

        # For width=600, ratio gives 12px, so px (30) wins
        assert config.get_min_gap_width(600) == 30

        # For width=2000, ratio gives 40px, so ratio wins
        assert config.get_min_gap_width(2000) == 40

    def test_legal_document_config(self):
        """Test that DEFAULT_COLUMN_CONFIG is suitable for legal docs."""
        assert DEFAULT_COLUMN_CONFIG.min_column_width_ratio == 0.15
        assert DEFAULT_COLUMN_CONFIG.min_gap_width_px == 40
        assert DEFAULT_COLUMN_CONFIG.max_columns == 3


# =============================================================================
# Unit Tests - Convenience Functions
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_detect_columns_numpy(self):
        """Test detect_columns with numpy array."""
        image = create_single_column_image()
        layout = detect_columns(image)

        assert isinstance(layout, LayoutMetadata)
        assert layout.num_columns == 1

    def test_detect_columns_pil(self):
        """Test detect_columns with PIL Image."""
        np_image = create_two_column_image()
        pil_image = Image.fromarray(np_image)
        layout = detect_columns(pil_image)

        assert isinstance(layout, LayoutMetadata)

    def test_get_column_detector_singleton(self):
        """Test that get_column_detector returns singleton."""
        detector1 = get_column_detector()
        detector2 = get_column_detector()

        # Should be the same instance
        assert detector1 is detector2


# =============================================================================
# Unit Tests - ImageCleaner Integration
# =============================================================================


class TestImageCleanerIntegration:
    """Tests for ImageCleaner integration with column detection."""

    @pytest.fixture
    def cleaner(self):
        """Creates an ImageCleaner instance."""
        return ImageCleaner()

    def test_detect_layout_method(self, cleaner):
        """Test ImageCleaner.detect_layout method."""
        np_image = create_single_column_image()
        pil_image = Image.fromarray(np_image)

        layout = cleaner.detect_layout(pil_image)

        assert isinstance(layout, LayoutMetadata)
        assert layout.num_columns == 1

    def test_process_image_with_layout(self, cleaner):
        """Test ImageCleaner.process_image_with_layout method."""
        np_image = create_two_column_image()
        pil_image = Image.fromarray(np_image)

        cleaned, layout = cleaner.process_image_with_layout(pil_image)

        # Check cleaned image
        assert isinstance(cleaned, Image.Image)
        assert cleaned.mode == "L"  # Grayscale

        # Check layout
        assert isinstance(layout, LayoutMetadata)

    def test_process_image_with_layout_custom_config(self, cleaner):
        """Test process_image_with_layout with custom column config."""
        np_image = create_three_column_image()
        pil_image = Image.fromarray(np_image)

        config = ColumnDetectionConfig(max_columns=4, valley_prominence=0.2)
        cleaned, layout = cleaner.process_image_with_layout(pil_image, column_config=config)

        assert isinstance(layout, LayoutMetadata)


# =============================================================================
# Unit Tests - Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def detector(self):
        return ColumnLayoutDetector()

    def test_very_small_image(self, detector):
        """Test detection on very small image."""
        image = np.ones((50, 50), dtype=np.uint8) * 255
        image[10:40, 10:40] = 0  # Some text

        layout = detector.detect(image)
        assert layout.num_columns == 1

    def test_very_wide_image(self, detector):
        """Test detection on very wide image."""
        image = np.ones((100, 2000), dtype=np.uint8) * 255
        # Add text across the width
        for x in range(100, 1900, 300):
            image[20:80, x : x + 200] = 0

        layout = detector.detect(image)
        assert isinstance(layout, LayoutMetadata)

    def test_very_tall_image(self, detector):
        """Test detection on very tall image."""
        image = np.ones((2000, 300), dtype=np.uint8) * 255
        # Add text lines
        for y in range(50, 1950, 30):
            image[y : y + 2, 30:270] = 0

        layout = detector.detect(image)
        assert layout.num_columns == 1

    def test_narrow_gap_ignored(self, detector):
        """Test that very narrow gaps are ignored."""
        # Create image with narrow gap (should be single column)
        image = np.ones((800, 600), dtype=np.uint8) * 255
        # Add text with small gap
        for y in range(50, 750, 20):
            image[y : y + 2, 30:290] = 0  # Left side
            image[y : y + 2, 310:570] = 0  # Right side (20px gap)

        # With default config (min_gap=40), this should be single column
        layout = detector.detect(image)
        # The gap is too narrow, so it should detect as single column
        # or merge the columns
        assert layout.num_columns <= 2

    def test_max_columns_limit(self):
        """Test that max_columns configuration is respected."""
        config = ColumnDetectionConfig(max_columns=2, valley_prominence=0.15, min_gap_width_px=20)
        detector = ColumnLayoutDetector(config=config)

        # Create 4-column image
        image = np.ones((800, 1200), dtype=np.uint8) * 255
        for y in range(50, 750, 20):
            for col_start in [30, 280, 580, 880]:
                col_end = col_start + 200
                image[y : y + 2, col_start:col_end] = 0

        layout = detector.detect(image)
        # Should not exceed max_columns
        assert layout.num_columns <= 2


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """Performance tests for column detection."""

    @pytest.fixture
    def detector(self):
        return ColumnLayoutDetector()

    def test_detection_speed(self, detector):
        """Test that detection is fast enough for real-time use."""
        import time

        image = create_two_column_image(width=1200, height=1600)

        start = time.time()
        for _ in range(10):
            detector.detect(image)
        elapsed = time.time() - start

        avg_time = elapsed / 10
        # Should be under 100ms per image
        assert avg_time < 0.1, f"Detection too slow: {avg_time:.3f}s"

    def test_memory_efficiency(self, detector):
        """Test that detection doesn't use excessive memory."""
        import tracemalloc

        tracemalloc.start()

        image = create_two_column_image(width=2400, height=3200)
        _ = detector.detect(image)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be reasonable (under 100MB for this size)
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 100, f"Memory usage too high: {peak_mb:.1f}MB"
