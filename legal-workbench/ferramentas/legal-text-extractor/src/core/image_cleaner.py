"""
ImageCleaner - Pre-processamento de imagens para OCR de documentos jurídicos.

Algoritmos vetorizados (Numpy/OpenCV) para limpeza de:
1. Documentos digitais (PJe): Marcas d'água cinza sobre texto preto
2. Documentos escaneados: Manchas, amarelamento, carimbos, speckles
3. Carimbos coloridos: Segmentacao HSV para azul, vermelho, verde
4. Detecao de layout multi-colunas para ordenacao correta de texto

Stack: opencv-python-headless, numpy, PIL
Constraint: Zero GUI (cv2.imshow proibido), execução em servidor/WSL

Author: Pedro Giudice
Date: 2025-11-25
Updated: 2026-01-07 - Added multi-column layout detection
Updated: 2026-01-07 - Added StampSegmenter integration for HSV-based stamp detection
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

import cv2
import numpy as np
from PIL import Image

if TYPE_CHECKING:
    pass


# =============================================================================
# MULTI-COLUMN LAYOUT DETECTION
# =============================================================================


class ColumnBoundary(NamedTuple):
    """Represents a detected column boundary (gap between columns)."""

    x_start: int  # Start X position of the gap
    x_end: int  # End X position of the gap
    width: int  # Width of the gap
    confidence: float  # Detection confidence (0.0-1.0)


@dataclass
class ColumnRegion:
    """Represents a detected column in the document."""

    index: int  # Column index (0-based, left to right)
    x_start: int  # Start X position (left edge)
    x_end: int  # End X position (right edge)
    width: int  # Column width in pixels
    text_density: float  # Relative text density (0.0-1.0)

    @property
    def center(self) -> int:
        """Returns the center X position of the column."""
        return (self.x_start + self.x_end) // 2


@dataclass
class LayoutMetadata:
    """
    Metadata about detected page layout for improved text reading order.

    This class captures the multi-column structure of a document page,
    enabling downstream OCR to process columns in the correct reading order.

    Attributes:
        num_columns: Number of detected columns (1 = single column)
        columns: List of ColumnRegion objects with positions
        column_boundaries: List of gaps between columns
        page_width: Total page width in pixels
        page_height: Total page height in pixels
        detection_method: Algorithm used for detection
        confidence: Overall detection confidence (0.0-1.0)
        is_multi_column: True if more than one column detected

    Example:
        >>> detector = ColumnLayoutDetector()
        >>> layout = detector.detect(image)
        >>> if layout.is_multi_column:
        ...     for col in layout.columns:
        ...         print(f"Column {col.index}: {col.x_start}-{col.x_end}")
    """

    num_columns: int
    columns: list[ColumnRegion]
    column_boundaries: list[ColumnBoundary]
    page_width: int
    page_height: int
    detection_method: str = "vertical_projection"
    confidence: float = 0.0

    @property
    def is_multi_column(self) -> bool:
        """Returns True if page has multiple columns."""
        return self.num_columns > 1

    def get_reading_order_regions(self) -> list[tuple[int, int, int, int]]:
        """
        Returns bounding boxes in reading order (left to right, top to bottom).

        For multi-column layouts, returns column regions that should be
        processed sequentially to maintain correct reading order.

        Returns:
            List of (x1, y1, x2, y2) tuples representing column bboxes
        """
        if not self.is_multi_column:
            return [(0, 0, self.page_width, self.page_height)]

        regions = []
        for col in sorted(self.columns, key=lambda c: c.x_start):
            regions.append((col.x_start, 0, col.x_end, self.page_height))
        return regions

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON output."""
        return {
            "num_columns": self.num_columns,
            "is_multi_column": self.is_multi_column,
            "columns": [
                {
                    "index": c.index,
                    "x_start": c.x_start,
                    "x_end": c.x_end,
                    "width": c.width,
                    "text_density": round(c.text_density, 3),
                }
                for c in self.columns
            ],
            "column_boundaries": [
                {
                    "x_start": b.x_start,
                    "x_end": b.x_end,
                    "width": b.width,
                    "confidence": round(b.confidence, 3),
                }
                for b in self.column_boundaries
            ],
            "page_width": self.page_width,
            "page_height": self.page_height,
            "detection_method": self.detection_method,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class ColumnDetectionConfig:
    """
    Configuration for multi-column detection algorithm.

    Attributes:
        min_column_width_ratio: Minimum column width as ratio of page width.
            Columns narrower than this are ignored (default: 0.1 = 10%).
        min_gap_width_px: Minimum gap width in pixels to be considered a column separator.
            Smaller gaps are treated as word spacing (default: 30px).
        min_gap_width_ratio: Alternative minimum gap as ratio of page width.
            Used when gap_width_px would be too small (default: 0.02 = 2%).
        projection_smoothing_kernel: Size of kernel for smoothing projection profile.
            Larger = more smoothing, fewer false positives (default: 15).
        valley_prominence: Minimum prominence of valleys in projection profile.
            Higher = fewer detected columns (default: 0.3).
        text_threshold: Threshold for binarizing image before analysis.
            Pixels below this are considered text (default: 128).
        edge_margin_ratio: Margin from page edges to ignore.
            Prevents detecting page borders as columns (default: 0.05 = 5%).
        max_columns: Maximum number of columns to detect (default: 4).
    """

    min_column_width_ratio: float = 0.1
    min_gap_width_px: int = 30
    min_gap_width_ratio: float = 0.02
    projection_smoothing_kernel: int = 15
    valley_prominence: float = 0.3
    text_threshold: int = 128
    edge_margin_ratio: float = 0.05
    max_columns: int = 4

    def get_min_gap_width(self, page_width: int) -> int:
        """Returns the minimum gap width for a given page width."""
        ratio_based = int(page_width * self.min_gap_width_ratio)
        return max(self.min_gap_width_px, ratio_based)


# Default configuration for legal documents
DEFAULT_COLUMN_CONFIG = ColumnDetectionConfig(
    min_column_width_ratio=0.15,  # Legal docs typically have wider columns
    min_gap_width_px=40,  # Clear separation between columns
    projection_smoothing_kernel=21,
    valley_prominence=0.25,
    max_columns=3,  # Legal docs rarely have more than 3 columns
)


class ColumnLayoutDetector:
    """
    Detects multi-column layouts in document images using vertical projection profile.

    Algorithm:
    1. Convert image to grayscale and binarize
    2. Compute vertical projection profile (sum of dark pixels per column)
    3. Smooth the profile to reduce noise
    4. Find valleys (low-density regions) that represent column gaps
    5. Validate gaps based on width and position constraints
    6. Return column regions with metadata

    The vertical projection profile technique is effective for:
    - Newspaper-style multi-column layouts
    - Legal documents with side-by-side sections
    - Academic papers with two-column format

    Example:
        >>> detector = ColumnLayoutDetector()
        >>> image = cv2.imread("document.png", cv2.IMREAD_GRAYSCALE)
        >>> layout = detector.detect(image)
        >>> print(f"Detected {layout.num_columns} columns")
    """

    def __init__(self, config: ColumnDetectionConfig | None = None):
        """
        Initialize the column detector.

        Args:
            config: Detection configuration. If None, uses DEFAULT_COLUMN_CONFIG.
        """
        self.config = config or DEFAULT_COLUMN_CONFIG

    def detect(self, image: np.ndarray) -> LayoutMetadata:
        """
        Detect column layout in an image.

        Args:
            image: Grayscale or BGR image (np.ndarray)

        Returns:
            LayoutMetadata with detected column structure

        Raises:
            ValueError: If image is empty or has invalid dimensions
        """
        if image is None or image.size == 0:
            raise ValueError("Image is empty or None")

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        height, width = gray.shape

        # Binarize image (text = dark = 0, background = light = 255)
        _, binary = cv2.threshold(gray, self.config.text_threshold, 255, cv2.THRESH_BINARY_INV)

        # Compute vertical projection profile
        projection = self._compute_vertical_projection(binary)

        # Smooth the projection to reduce noise
        smoothed = self._smooth_projection(projection, width)

        # Normalize projection for peak detection
        if smoothed.max() > 0:
            normalized = smoothed / smoothed.max()
        else:
            # No text detected - return single column layout
            return self._create_single_column_layout(width, height)

        # Find column boundaries (valleys in the projection)
        boundaries = self._find_column_boundaries(normalized, width)

        # Validate and create column regions
        columns = self._create_column_regions(boundaries, width, binary)

        # Calculate overall confidence
        confidence = self._calculate_confidence(columns, boundaries, normalized)

        return LayoutMetadata(
            num_columns=len(columns),
            columns=columns,
            column_boundaries=boundaries,
            page_width=width,
            page_height=height,
            detection_method="vertical_projection",
            confidence=confidence,
        )

    def _compute_vertical_projection(self, binary: np.ndarray) -> np.ndarray:
        """
        Compute vertical projection profile (sum of dark pixels per column).

        The projection profile represents text density at each X position.
        Higher values indicate more text content.

        Args:
            binary: Binarized image (text = 255, background = 0)

        Returns:
            1D array of shape (width,) with projection values
        """
        # Sum along vertical axis (axis=0) to get horizontal density
        projection = np.sum(binary, axis=0).astype(np.float64)
        return projection

    def _smooth_projection(self, projection: np.ndarray, width: int) -> np.ndarray:
        """
        Smooth the projection profile using a Gaussian kernel.

        Smoothing reduces noise from individual characters and
        produces cleaner column boundaries.

        Args:
            projection: Raw vertical projection profile
            width: Page width (used to adapt kernel size)

        Returns:
            Smoothed projection profile
        """
        kernel_size = self.config.projection_smoothing_kernel
        if kernel_size % 2 == 0:
            kernel_size += 1

        # Ensure kernel size is not larger than array
        kernel_size = min(kernel_size, len(projection) - 1)
        if kernel_size < 3:
            return projection

        # Use OpenCV's Gaussian blur for smooth results
        sigma = kernel_size / 4.0
        # GaussianBlur needs 2D input, so reshape
        projection_2d = projection.reshape(1, -1)
        smoothed_2d = cv2.GaussianBlur(projection_2d, (kernel_size, 1), sigma)
        return smoothed_2d.flatten()

    def _find_column_boundaries(self, normalized: np.ndarray, width: int) -> list[ColumnBoundary]:
        """
        Find column boundaries by detecting valleys in the projection profile.

        Valleys represent gaps between columns where text density is low.

        Args:
            normalized: Normalized projection profile (0.0-1.0)
            width: Page width in pixels

        Returns:
            List of ColumnBoundary objects
        """
        # Calculate edge margins to ignore
        margin = int(width * self.config.edge_margin_ratio)
        min_gap = self.config.get_min_gap_width(width)

        # Find valleys using a simple local minimum approach
        # (avoiding scipy dependency for simplicity)
        boundaries = []
        threshold = 1.0 - self.config.valley_prominence  # Valley threshold

        # Scan for regions where projection drops below threshold
        in_valley = False
        valley_start = 0

        for i in range(margin, width - margin):
            is_low = normalized[i] < threshold

            if is_low and not in_valley:
                # Start of a valley
                in_valley = True
                valley_start = i
            elif not is_low and in_valley:
                # End of a valley
                in_valley = False
                valley_end = i

                gap_width = valley_end - valley_start

                # Check if gap is wide enough
                if gap_width >= min_gap:
                    # Find the deepest point in the valley
                    valley_slice = normalized[valley_start:valley_end]
                    min_idx = np.argmin(valley_slice)
                    min_val = valley_slice[min_idx]

                    # Calculate confidence based on how deep the valley is
                    confidence = (1.0 - min_val) / self.config.valley_prominence
                    confidence = min(confidence, 1.0)

                    boundaries.append(
                        ColumnBoundary(
                            x_start=valley_start,
                            x_end=valley_end,
                            width=gap_width,
                            confidence=confidence,
                        )
                    )

        # Limit to max_columns - 1 boundaries
        max_boundaries = self.config.max_columns - 1
        if len(boundaries) > max_boundaries:
            # Keep the most confident boundaries
            boundaries = sorted(boundaries, key=lambda b: b.confidence, reverse=True)[
                :max_boundaries
            ]
            boundaries = sorted(boundaries, key=lambda b: b.x_start)

        return boundaries

    def _create_column_regions(
        self,
        boundaries: list[ColumnBoundary],
        width: int,
        binary: np.ndarray,
    ) -> list[ColumnRegion]:
        """
        Create column regions from detected boundaries.

        Args:
            boundaries: List of column boundaries
            width: Page width
            binary: Binarized image for density calculation

        Returns:
            List of ColumnRegion objects
        """
        if not boundaries:
            # Single column layout
            total_density = np.sum(binary) / (binary.size * 255) if binary.size > 0 else 0.0
            return [
                ColumnRegion(
                    index=0,
                    x_start=0,
                    x_end=width,
                    width=width,
                    text_density=total_density,
                )
            ]

        columns = []

        # First column: from start to first boundary
        first_end = boundaries[0].x_start
        columns.append(self._create_column(0, 0, first_end, binary))

        # Middle columns: between boundaries
        for i in range(len(boundaries) - 1):
            col_start = boundaries[i].x_end
            col_end = boundaries[i + 1].x_start
            columns.append(self._create_column(i + 1, col_start, col_end, binary))

        # Last column: from last boundary to end
        last_start = boundaries[-1].x_end
        columns.append(self._create_column(len(boundaries), last_start, width, binary))

        # Filter out columns that are too narrow
        min_width = int(width * self.config.min_column_width_ratio)
        columns = [c for c in columns if c.width >= min_width]

        # Re-index after filtering
        for i, col in enumerate(columns):
            col.index = i

        return columns

    def _create_column(
        self, index: int, x_start: int, x_end: int, binary: np.ndarray
    ) -> ColumnRegion:
        """Create a ColumnRegion with calculated text density."""
        width = x_end - x_start
        if width <= 0:
            return ColumnRegion(
                index=index, x_start=x_start, x_end=x_end, width=0, text_density=0.0
            )

        # Calculate text density in this column region
        column_slice = binary[:, x_start:x_end]
        if column_slice.size > 0:
            density = np.sum(column_slice) / (column_slice.size * 255)
        else:
            density = 0.0

        return ColumnRegion(
            index=index,
            x_start=x_start,
            x_end=x_end,
            width=width,
            text_density=float(density),
        )

    def _calculate_confidence(
        self,
        columns: list[ColumnRegion],
        boundaries: list[ColumnBoundary],
        normalized: np.ndarray,
    ) -> float:
        """
        Calculate overall confidence in the layout detection.

        Confidence is based on:
        - Boundary detection confidence
        - Column width consistency
        - Text density distribution

        Args:
            columns: Detected column regions
            boundaries: Detected boundaries
            normalized: Normalized projection profile

        Returns:
            Confidence score (0.0-1.0)
        """
        if len(columns) <= 1:
            # Single column is high confidence (common case)
            return 0.95

        if not boundaries:
            return 0.9

        # Average boundary confidence
        boundary_conf = np.mean([b.confidence for b in boundaries])

        # Column width consistency (low variance = high confidence)
        widths = [c.width for c in columns]
        if len(widths) > 1:
            width_std = np.std(widths) / np.mean(widths)
            width_consistency = max(0.0, 1.0 - width_std)
        else:
            width_consistency = 1.0

        # Text density variation (columns should have similar density)
        densities = [c.text_density for c in columns if c.text_density > 0]
        if len(densities) > 1:
            density_std = np.std(densities) / (np.mean(densities) + 0.01)
            density_consistency = max(0.0, 1.0 - density_std)
        else:
            density_consistency = 1.0

        # Combine factors
        confidence = 0.4 * boundary_conf + 0.3 * width_consistency + 0.3 * density_consistency

        return float(np.clip(confidence, 0.0, 1.0))

    def _create_single_column_layout(self, width: int, height: int) -> LayoutMetadata:
        """Create a single-column layout for pages with no detected columns."""
        return LayoutMetadata(
            num_columns=1,
            columns=[
                ColumnRegion(
                    index=0,
                    x_start=0,
                    x_end=width,
                    width=width,
                    text_density=0.0,
                )
            ],
            column_boundaries=[],
            page_width=width,
            page_height=height,
            detection_method="vertical_projection",
            confidence=0.95,  # Single column is a safe default
        )

    def detect_from_pil(self, image: Image.Image) -> LayoutMetadata:
        """
        Convenience method to detect layout from a PIL Image.

        Args:
            image: PIL Image (RGB or grayscale)

        Returns:
            LayoutMetadata with detected column structure
        """
        np_image = np.array(image)
        return self.detect(np_image)


# Singleton for convenient access
_column_detector: ColumnLayoutDetector | None = None


def get_column_detector(**kwargs) -> ColumnLayoutDetector:
    """
    Get singleton instance of ColumnLayoutDetector.

    Args:
        **kwargs: Arguments passed to ColumnLayoutDetector() on first call.

    Returns:
        ColumnLayoutDetector instance
    """
    global _column_detector
    if _column_detector is None:
        _column_detector = ColumnLayoutDetector(**kwargs)
    return _column_detector


def detect_columns(image: np.ndarray | Image.Image) -> LayoutMetadata:
    """
    Convenience function to detect column layout in an image.

    Args:
        image: Grayscale, BGR numpy array, or PIL Image

    Returns:
        LayoutMetadata with detected column structure

    Example:
        >>> from PIL import Image
        >>> img = Image.open("two_column_doc.png")
        >>> layout = detect_columns(img)
        >>> if layout.is_multi_column:
        ...     print(f"Found {layout.num_columns} columns!")
        ...     for col in layout.columns:
        ...         print(f"  Column {col.index}: x={col.x_start}-{col.x_end}")
    """
    detector = get_column_detector()
    if isinstance(image, Image.Image):
        return detector.detect_from_pil(image)
    return detector.detect(image)


# =============================================================================
# CLEANING MODE AND OPTIONS
# =============================================================================


class CleaningMode(str, Enum):
    """Modos de limpeza disponíveis."""

    AUTO = "auto"  # Detecta automaticamente baseado em histograma
    DIGITAL = "digital"  # Otimizado para PDFs digitais com marca d'água
    SCANNED = "scanned"  # Otimizado para scans com manchas/carimbos


@dataclass
class CLAHEConfig:
    """
    Configuracao do CLAHE (Contrast Limited Adaptive Histogram Equalization).

    CLAHE melhora o contraste local de imagens escuras/com iluminacao irregular
    sem amplificar ruido excessivamente.

    Attributes:
        enabled: Se True, aplica CLAHE automaticamente em imagens escuras.
        clip_limit: Limita amplificacao de contraste (2.0-4.0 recomendado).
            Maior = mais contraste, mas mais ruido.
        tile_grid_size: Tamanho do grid para equalizacao local.
            (8,8) = mais suave, (16,16) = mais detalhado.
        dark_threshold: Media de intensidade abaixo da qual imagem e considerada escura.
        dark_percentile: Percentil de pixels escuros para considerar imagem escura.
    """

    enabled: bool = True
    clip_limit: float = 2.5
    tile_grid_size: tuple[int, int] = (8, 8)
    dark_threshold: float = 100.0  # Media de intensidade < 100 = escura
    dark_percentile: float = 0.4  # 40% dos pixels < 100 = escura


@dataclass
class CleaningOptions:
    """
    Opções de configuração para o ImageCleaner.

    Permite customização granular dos algoritmos de limpeza.
    Use valores padrão para a maioria dos casos.

    Example:
        >>> options = CleaningOptions(
        ...     mode=CleaningMode.DIGITAL,
        ...     watermark_threshold=190,  # Mais agressivo
        ...     despeckle_kernel=5,       # Maior suavização
        ... )
        >>> cleaner = ImageCleaner.from_options(options)
    """

    # Modo de limpeza
    mode: CleaningMode = CleaningMode.AUTO

    # Threshold para remoção de marca d'água (0-255)
    # Pixels > threshold são convertidos para branco
    # Menor = mais agressivo (remove mais cinza)
    watermark_threshold: int = 200

    # Adaptive threshold settings
    # block_size: Tamanho da vizinhança (deve ser ímpar)
    # c: Constante subtraída da média
    adaptive_block_size: int = 31
    adaptive_c: int = 15

    # Kernel para despeckle (deve ser ímpar)
    # Maior = mais suavização (pode perder detalhes)
    despeckle_kernel: int = 3

    # Iterações de dilatação para máscaras de carimbo
    # Mais iterações = captura mais borda do carimbo
    stamp_dilate_iterations: int = 2

    # Ranges HSV customizados para carimbos
    # Se None, usa cores padrão (azul, vermelho, verde)
    custom_stamp_colors: list[tuple[np.ndarray, np.ndarray]] | None = None

    # Configuracao CLAHE para scans escuros
    clahe: CLAHEConfig = field(default_factory=CLAHEConfig)

    def __post_init__(self):
        """Valida parâmetros."""
        if not 0 <= self.watermark_threshold <= 255:
            raise ValueError("watermark_threshold deve ser 0-255")
        if self.adaptive_block_size % 2 == 0:
            self.adaptive_block_size += 1
        if self.despeckle_kernel % 2 == 0:
            self.despeckle_kernel += 1
        if not 0.5 <= self.clahe.clip_limit <= 10.0:
            raise ValueError("clahe.clip_limit deve ser entre 0.5 e 10.0")


# Presets comuns
PRESET_DIGITAL_AGGRESSIVE = CleaningOptions(
    mode=CleaningMode.DIGITAL,
    watermark_threshold=180,  # Remove mais cinza
    despeckle_kernel=3,
)

PRESET_SCANNED_CONSERVATIVE = CleaningOptions(
    mode=CleaningMode.SCANNED,
    watermark_threshold=210,  # Preserva mais detalhes
    adaptive_c=10,  # Menos agressivo
    despeckle_kernel=3,
)

PRESET_OCR_OPTIMIZED = CleaningOptions(
    mode=CleaningMode.AUTO,
    watermark_threshold=200,
    adaptive_block_size=21,  # Menor bloco para texto pequeno
    adaptive_c=12,
    despeckle_kernel=3,
)

# Preset para scans escuros - CLAHE agressivo
PRESET_DARK_SCAN = CleaningOptions(
    mode=CleaningMode.SCANNED,
    watermark_threshold=180,
    adaptive_block_size=31,
    adaptive_c=10,  # Menos agressivo apos CLAHE
    despeckle_kernel=3,
    clahe=CLAHEConfig(
        enabled=True,
        clip_limit=3.0,  # Mais contraste para scans muito escuros
        tile_grid_size=(8, 8),
        dark_threshold=90.0,
        dark_percentile=0.35,
    ),
)

# Preset para scans com iluminacao irregular
PRESET_UNEVEN_LIGHTING = CleaningOptions(
    mode=CleaningMode.SCANNED,
    watermark_threshold=200,
    adaptive_block_size=51,  # Blocos maiores para variacao de iluminacao
    adaptive_c=12,
    despeckle_kernel=3,
    clahe=CLAHEConfig(
        enabled=True,
        clip_limit=2.0,  # Moderado
        tile_grid_size=(16, 16),  # Tiles maiores para variacao ampla
        dark_threshold=120.0,
        dark_percentile=0.3,
    ),
)


# Ranges HSV padrão para carimbos comuns em documentos judiciais brasileiros
DEFAULT_STAMP_COLORS: list[tuple[np.ndarray, np.ndarray]] = [
    # Azul (carimbos azuis comuns)
    (np.array([100, 50, 50]), np.array([130, 255, 255])),
    # Vermelho (parte 1: H=0-10)
    (np.array([0, 50, 50]), np.array([10, 255, 255])),
    # Vermelho (parte 2: H=170-180)
    (np.array([170, 50, 50]), np.array([180, 255, 255])),
    # Verde (carimbos verdes menos comuns)
    (np.array([35, 50, 50]), np.array([85, 255, 255])),
]


class ImageCleaner:
    """
    Cleaner de imagens para pré-processamento de OCR.

    Métodos principais:
    - remove_gray_watermarks(): Remove marcas d'água cinza (documentos digitais)
    - clean_dirty_scan(): Limpa scans com iluminação irregular (adaptive threshold)
    - remove_color_stamps(): Remove carimbos coloridos (HSV segmentation)
    - remove_speckles(): Remove ruído pontual (morphological opening)
    - process_image(): Orquestrador inteligente (auto-detecção de modo)

    Example:
        >>> cleaner = ImageCleaner()
        >>> img = Image.open("scan.png")
        >>> cleaned = cleaner.process_image(img, mode="scanned")
        >>> cleaned.save("cleaned.png")
    """

    def __init__(
        self,
        watermark_threshold: int = 200,
        adaptive_block_size: int = 31,
        adaptive_c: int = 15,
        despeckle_kernel_size: int = 3,
        stamp_colors: list[tuple[np.ndarray, np.ndarray]] | None = None,
        clahe_config: CLAHEConfig | None = None,
    ):
        """
        Inicializa o cleaner com parâmetros configuráveis.

        Args:
            watermark_threshold: Limiar para remoção de cinza (0-255). Default 200.
                Pixels > threshold são convertidos para branco.
            adaptive_block_size: Tamanho do bloco para adaptive threshold. Deve ser ímpar.
            adaptive_c: Constante subtraída da média no adaptive threshold.
            despeckle_kernel_size: Tamanho do kernel para morphological opening.
                3x3 é recomendado para preservar pontuação.
            stamp_colors: Lista de ranges HSV [(lower, upper), ...] para carimbos.
                Se None, usa DEFAULT_STAMP_COLORS.
            clahe_config: Configuracao do CLAHE para scans escuros.
                Se None, usa configuracao padrao (CLAHEConfig()).
        """
        self.watermark_threshold = watermark_threshold
        self.adaptive_block_size = adaptive_block_size
        self.adaptive_c = adaptive_c
        self.despeckle_kernel_size = despeckle_kernel_size
        self.stamp_colors = stamp_colors or DEFAULT_STAMP_COLORS
        self.clahe_config = clahe_config or CLAHEConfig()

    @classmethod
    def from_options(cls, options: CleaningOptions) -> ImageCleaner:
        """
        Cria ImageCleaner a partir de CleaningOptions.

        Args:
            options: Instância de CleaningOptions

        Returns:
            ImageCleaner configurado

        Example:
            >>> opts = CleaningOptions(watermark_threshold=180)
            >>> cleaner = ImageCleaner.from_options(opts)
        """
        return cls(
            watermark_threshold=options.watermark_threshold,
            adaptive_block_size=options.adaptive_block_size,
            adaptive_c=options.adaptive_c,
            despeckle_kernel_size=options.despeckle_kernel,
            stamp_colors=options.custom_stamp_colors,
            clahe_config=options.clahe,
        )

    @staticmethod
    def remove_gray_watermarks(image: np.ndarray, threshold: int = 200) -> np.ndarray:
        """
        Remove marcas d'água cinza claro de documentos digitais.

        Algoritmo: Threshold global simples.
        - Texto jurídico legítimo é preto (#000000)
        - Marcas d'água digitais são cinza claro (geralmente > #C0C0C0 = 192)
        - Pixels com valor > threshold são convertidos para branco (255)

        Args:
            image: Imagem em grayscale (np.ndarray uint8, shape HxW)
            threshold: Limiar de cinza (0-255). Pixels > threshold → 255.

        Returns:
            Imagem limpa (grayscale np.ndarray)

        Example:
            >>> img = cv2.imread("digital.png", cv2.IMREAD_GRAYSCALE)
            >>> clean = ImageCleaner.remove_gray_watermarks(img, threshold=200)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Vetorização numpy: muito mais rápido que loops
        result = image.copy()
        result[result > threshold] = 255
        return result

    @staticmethod
    def clean_dirty_scan(image: np.ndarray, block_size: int = 31, c: int = 15) -> np.ndarray:
        """
        Limpa scans com iluminação irregular usando adaptive threshold.

        Algoritmo: Gaussian Adaptive Threshold.
        - Scans antigos têm variação de brilho (papel amarelado, sombras)
        - Threshold global falha: apaga texto em áreas claras, deixa ruído em escuras
        - Adaptive calcula limiar local baseado em vizinhança

        Args:
            image: Imagem em grayscale (np.ndarray uint8, shape HxW)
            block_size: Tamanho da vizinhança para cálculo do threshold. Deve ser ímpar.
            c: Constante subtraída da média ponderada.

        Returns:
            Imagem binarizada (grayscale np.ndarray, apenas 0 e 255)

        Example:
            >>> img = cv2.imread("old_scan.png", cv2.IMREAD_GRAYSCALE)
            >>> clean = ImageCleaner.clean_dirty_scan(img, block_size=31, c=15)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Garante block_size ímpar
        if block_size % 2 == 0:
            block_size += 1

        # Adaptive threshold usando média Gaussiana
        result = cv2.adaptiveThreshold(
            image,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=block_size,
            C=c,
        )

        return result

    @staticmethod
    def remove_color_stamps(
        image: np.ndarray,
        color_ranges: Sequence[tuple[np.ndarray, np.ndarray]] | None = None,
    ) -> np.ndarray:
        """
        Remove carimbos coloridos via segmentação HSV.

        Algoritmo: Color-based segmentation.
        1. Converte BGR → HSV (mais robusto a iluminação)
        2. Cria máscara para cada cor alvo usando cv2.inRange
        3. Dilata máscara para capturar bordas borradas
        4. Pinta região da máscara de branco
        5. Retorna em grayscale

        Args:
            image: Imagem BGR (np.ndarray uint8, shape HxWx3)
            color_ranges: Lista de tuplas (lower_hsv, upper_hsv) para cada cor.
                Se None, usa ranges padrão para carimbos azuis/vermelhos/verdes.

        Returns:
            Imagem grayscale com carimbos removidos (np.ndarray uint8, shape HxW)

        Example:
            >>> img = cv2.imread("with_stamp.png")  # BGR
            >>> clean = ImageCleaner.remove_color_stamps(img)
        """
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError("Input deve ser BGR (3D array com 3 canais)")

        if color_ranges is None:
            color_ranges = DEFAULT_STAMP_COLORS

        # Converte BGR → HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Cria máscara combinada para todas as cores
        combined_mask = np.zeros(image.shape[:2], dtype=np.uint8)

        for lower, upper in color_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, mask)

        # Dilata para pegar bordas borradas dos carimbos
        kernel = np.ones((5, 5), np.uint8)
        dilated_mask = cv2.dilate(combined_mask, kernel, iterations=2)

        # Pinta regiões mascaradas de branco na imagem original
        result = image.copy()
        result[dilated_mask > 0] = [255, 255, 255]

        # Converte para grayscale
        result_gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)

        return result_gray

    @staticmethod
    def remove_speckles(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """
        Remove ruído pontual (speckles) usando median filter.

        Algoritmo: Median Filter.
        - Substitui cada pixel pela mediana da vizinhança
        - Eficaz para ruído "salt-and-pepper" (pontos pretos/brancos isolados)
        - Preserva bordas melhor que blur gaussiano
        - Kernel 3x3 remove speckles sem destruir pontuação

        Args:
            image: Imagem grayscale ou binarizada (np.ndarray uint8)
            kernel_size: Tamanho do kernel (3 recomendado). Deve ser ímpar.

        Returns:
            Imagem despeckled (np.ndarray uint8)

        Example:
            >>> img = cv2.imread("noisy.png", cv2.IMREAD_GRAYSCALE)
            >>> clean = ImageCleaner.remove_speckles(img, kernel_size=3)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Garante kernel_size ímpar
        if kernel_size % 2 == 0:
            kernel_size += 1

        # Median filter - eficaz para salt-and-pepper noise
        result = cv2.medianBlur(image, kernel_size)

        return result

    # =========================================================================
    # CLAHE (Contrast Limited Adaptive Histogram Equalization) Methods
    # =========================================================================

    @staticmethod
    def analyze_darkness(
        image: np.ndarray,
        dark_threshold: float = 100.0,
        dark_percentile: float = 0.4,
    ) -> dict:
        """
        Analisa o nivel de escuridao de uma imagem via histograma.

        Retorna metricas detalhadas para decidir se CLAHE deve ser aplicado.

        Algoritmo:
        1. Calcula histograma normalizado
        2. Computa media de intensidade
        3. Calcula percentil de pixels escuros (< dark_threshold)
        4. Analisa distribuicao do histograma

        Args:
            image: Imagem grayscale (np.ndarray uint8, shape HxW)
            dark_threshold: Intensidade abaixo da qual pixel e considerado escuro.
            dark_percentile: Proporcao de pixels escuros para considerar imagem escura.

        Returns:
            Dict com metricas:
            - mean_intensity: Media de intensidade (0-255)
            - dark_pixel_ratio: Proporcao de pixels escuros
            - histogram: Histograma normalizado (256 bins)
            - is_dark: True se imagem e considerada escura
            - darkness_score: Score de escuridao (0-1, maior = mais escuro)

        Example:
            >>> img = cv2.imread("scan.png", cv2.IMREAD_GRAYSCALE)
            >>> metrics = ImageCleaner.analyze_darkness(img)
            >>> if metrics['is_dark']:
            ...     img = ImageCleaner.apply_clahe(img)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Calcula histograma
        hist = cv2.calcHist([image], [0], None, [256], [0, 256]).flatten()
        hist_norm = hist / hist.sum()

        # Media de intensidade
        mean_intensity = float(np.mean(image))

        # Proporcao de pixels escuros
        dark_pixel_ratio = float(np.sum(image < dark_threshold) / image.size)

        # Score de escuridao combinado (0-1)
        # Combina media baixa + alta proporcao de pixels escuros
        intensity_score = 1.0 - (mean_intensity / 255.0)  # 0=claro, 1=escuro
        darkness_score = (intensity_score * 0.6) + (dark_pixel_ratio * 0.4)

        # Determina se e escura
        is_dark = mean_intensity < dark_threshold or dark_pixel_ratio > dark_percentile

        return {
            "mean_intensity": mean_intensity,
            "dark_pixel_ratio": dark_pixel_ratio,
            "histogram": hist_norm,
            "is_dark": is_dark,
            "darkness_score": darkness_score,
        }

    @staticmethod
    def apply_clahe(
        image: np.ndarray,
        clip_limit: float = 2.5,
        tile_grid_size: tuple[int, int] = (8, 8),
    ) -> np.ndarray:
        """
        Aplica CLAHE (Contrast Limited Adaptive Histogram Equalization).

        CLAHE melhora o contraste local sem amplificar ruido excessivamente.
        Ideal para scans escuros ou com iluminacao irregular.

        Algoritmo:
        1. Divide imagem em tiles (grid)
        2. Aplica histogram equalization em cada tile
        3. Limita amplificacao de contraste (clip limit)
        4. Interpola bordas entre tiles para evitar artefatos

        Args:
            image: Imagem grayscale (np.ndarray uint8, shape HxW)
            clip_limit: Limita amplificacao de contraste (2.0-4.0 recomendado).
                Maior = mais contraste, mas pode amplificar ruido.
            tile_grid_size: Tamanho do grid para equalizacao local.
                (8,8) = mais suave, (16,16) = mais detalhado.

        Returns:
            Imagem com contraste melhorado (grayscale np.ndarray)

        Example:
            >>> img = cv2.imread("dark_scan.png", cv2.IMREAD_GRAYSCALE)
            >>> enhanced = ImageCleaner.apply_clahe(img, clip_limit=3.0)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Cria objeto CLAHE
        clahe = cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=tile_grid_size,
        )

        # Aplica CLAHE
        result = clahe.apply(image)

        return result

    @staticmethod
    def enhance_dark_scan(
        image: np.ndarray,
        clahe_config: CLAHEConfig | None = None,
        apply_otsu: bool = True,
    ) -> np.ndarray:
        """
        Pipeline completo para melhorar scans escuros.

        Combina CLAHE adaptativo com threshold Otsu para binarizacao otima.

        Pipeline:
        1. Analisa escuridao da imagem
        2. Se escura, aplica CLAHE
        3. Opcionalmente aplica threshold Otsu para binarizacao
        4. Retorna imagem melhorada

        Args:
            image: Imagem grayscale (np.ndarray uint8, shape HxW)
            clahe_config: Configuracao do CLAHE. Se None, usa padrao.
            apply_otsu: Se True, aplica threshold Otsu apos CLAHE.

        Returns:
            Imagem processada (grayscale np.ndarray)

        Example:
            >>> img = cv2.imread("dark_scan.png", cv2.IMREAD_GRAYSCALE)
            >>> config = CLAHEConfig(clip_limit=3.0)
            >>> enhanced = ImageCleaner.enhance_dark_scan(img, config)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        config = clahe_config or CLAHEConfig()

        # Analisa escuridao
        metrics = ImageCleaner.analyze_darkness(
            image,
            dark_threshold=config.dark_threshold,
            dark_percentile=config.dark_percentile,
        )

        result = image.copy()

        # Aplica CLAHE se imagem for escura e CLAHE estiver habilitado
        if config.enabled and metrics["is_dark"]:
            result = ImageCleaner.apply_clahe(
                result,
                clip_limit=config.clip_limit,
                tile_grid_size=config.tile_grid_size,
            )

        # Aplica threshold Otsu se solicitado
        if apply_otsu:
            _, result = cv2.threshold(
                result,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU,
            )

        return result

    @staticmethod
    def enhance_dark_scan_adaptive(
        image: np.ndarray,
        clahe_config: CLAHEConfig | None = None,
        block_size: int = 31,
        c: int = 15,
    ) -> np.ndarray:
        """
        Pipeline para scans escuros com threshold adaptativo.

        Combina CLAHE com Gaussian Adaptive Threshold para melhor resultado
        em documentos com iluminacao muito irregular.

        Pipeline:
        1. Analisa escuridao da imagem
        2. Se escura, aplica CLAHE
        3. Aplica Adaptive Threshold (Gaussian)
        4. Retorna imagem binarizada

        Args:
            image: Imagem grayscale (np.ndarray uint8, shape HxW)
            clahe_config: Configuracao do CLAHE. Se None, usa padrao.
            block_size: Tamanho do bloco para adaptive threshold.
            c: Constante subtraida da media no adaptive threshold.

        Returns:
            Imagem binarizada (grayscale np.ndarray, apenas 0 e 255)

        Example:
            >>> img = cv2.imread("dark_uneven_scan.png", cv2.IMREAD_GRAYSCALE)
            >>> config = CLAHEConfig(clip_limit=2.5, tile_grid_size=(16, 16))
            >>> enhanced = ImageCleaner.enhance_dark_scan_adaptive(img, config)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        config = clahe_config or CLAHEConfig()

        # Analisa escuridao
        metrics = ImageCleaner.analyze_darkness(
            image,
            dark_threshold=config.dark_threshold,
            dark_percentile=config.dark_percentile,
        )

        result = image.copy()

        # Aplica CLAHE se imagem for escura e CLAHE estiver habilitado
        if config.enabled and metrics["is_dark"]:
            result = ImageCleaner.apply_clahe(
                result,
                clip_limit=config.clip_limit,
                tile_grid_size=config.tile_grid_size,
            )

        # Aplica Adaptive Threshold
        result = ImageCleaner.clean_dirty_scan(result, block_size, c)

        return result

    @staticmethod
    def has_speckle_noise(image: np.ndarray, threshold: float = 0.02) -> bool:
        """
        Detecta se imagem tem ruído salt-and-pepper (speckles).

        Heurística: Em áreas majoritariamente brancas (>200),
        speckles aparecem como pixels escuros isolados.
        Calcula a proporção de pixels escuros em áreas brancas.

        Args:
            image: Grayscale image (np.ndarray uint8, shape HxW)
            threshold: Se proporção de ruído > threshold, retorna True.
                       Default 0.02 = 2% de ruído em áreas brancas.

        Returns:
            True se detectar speckles significativos

        Example:
            >>> img = cv2.imread("scan.png", cv2.IMREAD_GRAYSCALE)
            >>> if ImageCleaner.has_speckle_noise(img):
            ...     img = ImageCleaner.remove_speckles(img)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Cria máscara de áreas brancas
        white_mask = image > 200

        # Se não há área branca suficiente, não faz sentido analisar
        if white_mask.sum() < image.size * 0.3:
            return False

        # Dentro das áreas "brancas", conta pixels escuros (ruído)
        # Speckles são pixels < 150 em áreas que deveriam ser brancas
        noise_in_white = (image < 150) & white_mask
        noise_ratio = noise_in_white.sum() / white_mask.sum()

        return noise_ratio > threshold

    def detect_mode(self, image: np.ndarray) -> CleaningMode:
        """
        Detecta automaticamente o melhor modo de limpeza.

        Heurística baseada em análise de histograma:
        1. Documentos digitais têm distribuição bimodal limpa (preto + branco)
        2. Scans têm distribuição mais espalhada (cinzas, manchas)
        3. Presença de cores fortes indica carimbos

        Args:
            image: Imagem BGR ou grayscale

        Returns:
            CleaningMode.DIGITAL ou CleaningMode.SCANNED
        """
        # Converte para grayscale se necessário
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Calcula histograma
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()

        # Normaliza
        hist_norm = hist / hist.sum()

        # Métricas de distribuição
        # 1. Concentração nos extremos (0-50 e 200-255)
        dark_mass = hist_norm[:50].sum()
        light_mass = hist_norm[200:].sum()
        extreme_ratio = dark_mass + light_mass

        # 2. Spread no meio (50-200) = ruído/manchas
        mid_mass = hist_norm[50:200].sum()

        # Heurística:
        # - Digital: extremos > 80%, meio < 20%
        # - Scanned: meio > 20%
        if extreme_ratio > 0.8 and mid_mass < 0.2:
            return CleaningMode.DIGITAL
        else:
            return CleaningMode.SCANNED

    def process_image(
        self,
        image_pil: Image.Image,
        mode: str | CleaningMode = "auto",
        force_clahe: bool = False,
    ) -> Image.Image:
        """
        Orquestrador principal - processa imagem com pipeline apropriado.

        Pipelines:
        - DIGITAL: remove_gray_watermarks -> (opcional) remove_speckles
        - SCANNED: (opcional CLAHE) -> remove_color_stamps -> adaptive threshold -> despeckle
        - AUTO: detect_mode() -> pipeline correspondente

        O CLAHE e aplicado automaticamente em scans escuros quando:
        - clahe_config.enabled = True (padrao)
        - Imagem detectada como escura via analyze_darkness()

        Args:
            image_pil: Imagem PIL (RGB ou grayscale)
            mode: "auto", "digital", ou "scanned"
            force_clahe: Se True, aplica CLAHE independente da analise de escuridao.

        Returns:
            Imagem PIL processada (grayscale)

        Example:
            >>> cleaner = ImageCleaner()
            >>> img = Image.open("document.png")
            >>> clean = cleaner.process_image(img, mode="auto")
            >>> clean.save("clean.png")

            >>> # Para scan escuro, force CLAHE:
            >>> dark_cleaner = ImageCleaner.from_options(PRESET_DARK_SCAN)
            >>> clean = dark_cleaner.process_image(img, mode="scanned", force_clahe=True)
        """
        # Converte PIL -> Numpy (OpenCV usa BGR, PIL usa RGB)
        img_np = np.array(image_pil)

        # Se grayscale, converte para 3 canais para processamento uniforme
        if len(img_np.shape) == 2:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
        else:
            # PIL RGB -> OpenCV BGR
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # Determina modo
        if isinstance(mode, str):
            mode = CleaningMode(mode.lower())

        if mode == CleaningMode.AUTO:
            mode = self.detect_mode(img_bgr)

        # Converte para grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # Aplica pipeline baseado no modo
        if mode == CleaningMode.DIGITAL:
            # Pipeline digital: remove marca d'agua cinza
            result = self.remove_gray_watermarks(gray, self.watermark_threshold)
            # Despeckle condicional - so aplica se detectar ruido real
            # (evita degradar texto preto em documentos digitais limpos)
            if self.has_speckle_noise(result):
                result = self.remove_speckles(result, self.despeckle_kernel_size)

        else:  # SCANNED
            # Pipeline scanned com CLAHE adaptativo:
            # 1. Analisa escuridao e aplica CLAHE se necessario
            # 2. Remove carimbos coloridos
            # 3. Adaptive threshold
            # 4. Despeckle

            result = gray

            # Aplica CLAHE se habilitado e imagem escura (ou forcado)
            if self.clahe_config.enabled:
                metrics = self.analyze_darkness(
                    result,
                    dark_threshold=self.clahe_config.dark_threshold,
                    dark_percentile=self.clahe_config.dark_percentile,
                )

                if force_clahe or metrics["is_dark"]:
                    result = self.apply_clahe(
                        result,
                        clip_limit=self.clahe_config.clip_limit,
                        tile_grid_size=self.clahe_config.tile_grid_size,
                    )
                    # Reconstroi BGR para remocao de carimbos
                    img_bgr = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

            # Remove carimbos coloridos
            result = self.remove_color_stamps(img_bgr, self.stamp_colors)

            # Adaptive threshold (Gaussian)
            result = self.clean_dirty_scan(result, self.adaptive_block_size, self.adaptive_c)

            # Despeckle
            result = self.remove_speckles(result, self.despeckle_kernel_size)

        # Converte de volta para PIL
        result_pil = Image.fromarray(result, mode="L")  # L = grayscale

        return result_pil

    def process_image_with_layout(
        self,
        image_pil: Image.Image,
        mode: str | CleaningMode = "auto",
        force_clahe: bool = False,
        column_config: ColumnDetectionConfig | None = None,
    ) -> tuple[Image.Image, LayoutMetadata]:
        """
        Process image with cleaning and multi-column layout detection.

        This method combines the image cleaning pipeline with column layout
        detection to provide both a cleaned image and metadata about the
        document structure for improved OCR reading order.

        Pipelines:
        - Cleaning: Same as process_image()
        - Layout: Vertical projection profile analysis for column detection

        Args:
            image_pil: PIL Image (RGB or grayscale)
            mode: "auto", "digital", or "scanned"
            force_clahe: If True, apply CLAHE regardless of darkness analysis.
            column_config: Configuration for column detection.
                If None, uses DEFAULT_COLUMN_CONFIG.

        Returns:
            Tuple of (cleaned_image, layout_metadata):
            - cleaned_image: PIL Image (grayscale) after cleaning
            - layout_metadata: LayoutMetadata with column structure

        Example:
            >>> cleaner = ImageCleaner()
            >>> img = Image.open("two_column_legal_doc.png")
            >>> cleaned, layout = cleaner.process_image_with_layout(img)
            >>> print(f"Detected {layout.num_columns} columns")
            >>> if layout.is_multi_column:
            ...     for region in layout.get_reading_order_regions():
            ...         x1, y1, x2, y2 = region
            ...         column_img = cleaned.crop((x1, y1, x2, y2))
            ...         # Process each column separately for OCR
        """
        # First, detect layout on the original image (before cleaning)
        # This gives better results as cleaning may alter text density
        detector = ColumnLayoutDetector(config=column_config)
        layout = detector.detect_from_pil(image_pil)

        # Then clean the image
        cleaned = self.process_image(image_pil, mode=mode, force_clahe=force_clahe)

        return cleaned, layout

    def detect_layout(
        self,
        image_pil: Image.Image,
        config: ColumnDetectionConfig | None = None,
    ) -> LayoutMetadata:
        """
        Detect column layout without cleaning the image.

        This is useful when you only need layout information or when
        cleaning is done separately.

        Args:
            image_pil: PIL Image (RGB or grayscale)
            config: Configuration for column detection.
                If None, uses DEFAULT_COLUMN_CONFIG.

        Returns:
            LayoutMetadata with detected column structure

        Example:
            >>> cleaner = ImageCleaner()
            >>> img = Image.open("document.png")
            >>> layout = cleaner.detect_layout(img)
            >>> print(f"Layout: {layout.num_columns} columns, confidence={layout.confidence:.2f}")
        """
        detector = ColumnLayoutDetector(config=config)
        return detector.detect_from_pil(image_pil)


# Singleton para uso conveniente
_cleaner: ImageCleaner | None = None


def get_image_cleaner(**kwargs) -> ImageCleaner:
    """
    Obtém instância singleton do ImageCleaner.

    Args:
        **kwargs: Argumentos passados para ImageCleaner() na primeira chamada.

    Returns:
        Instância de ImageCleaner
    """
    global _cleaner
    if _cleaner is None:
        _cleaner = ImageCleaner(**kwargs)
    return _cleaner


# =============================================================================
# Enhanced Stamp Processing with StampSegmenter
# =============================================================================


def process_stamps_advanced(
    image: np.ndarray | Image.Image,
    mode: str = "remove",
    colors: list[str] | None = None,
    return_metadata: bool = True,
) -> tuple[np.ndarray | None, list[dict]]:
    """
    Process colored stamps using advanced HSV segmentation.

    This function provides a high-level interface to the StampSegmenter
    for detecting, removing, or extracting colored stamps from legal documents.

    Args:
        image: Input image (BGR numpy array or PIL Image)
        mode: Processing mode:
            - "remove": Remove stamps and return cleaned image
            - "extract": Extract stamp regions only
            - "both": Return both cleaned image and extracted stamps
            - "detect": Only detect stamps and return metadata
        colors: List of colors to detect. Options: "blue", "red", "green", "purple"
            If None, detects all colors.
        return_metadata: If True, return stamp metadata. If False, only image.

    Returns:
        Tuple of (processed_image, stamp_metadata)
        - processed_image: Cleaned grayscale image (mode="remove"/"both") or None
        - stamp_metadata: List of StampRegion dicts with detection info

    Example:
        >>> from PIL import Image
        >>> img = Image.open("document_with_stamps.png")
        >>> cleaned, stamps = process_stamps_advanced(img, mode="remove")
        >>> print(f"Found {len(stamps)} stamps")
        >>> for s in stamps:
        ...     print(f"  {s['color']} stamp at {s['bbox']}")
    """
    from .stamp_segmenter import (
        StampColor,
        StampMode,
        StampSegmenter,
        StampSegmenterConfig,
    )

    # Map string mode to enum
    mode_map = {
        "remove": StampMode.REMOVE,
        "extract": StampMode.EXTRACT,
        "both": StampMode.BOTH,
        "detect": StampMode.REMOVE,  # We still need the mask for detection
    }
    stamp_mode = mode_map.get(mode.lower(), StampMode.REMOVE)

    # Map color strings to enum
    color_map = {
        "blue": StampColor.BLUE,
        "red": StampColor.RED,
        "green": StampColor.GREEN,
        "purple": StampColor.PURPLE,
    }

    stamp_colors = None
    if colors:
        stamp_colors = [color_map[c.lower()] for c in colors if c.lower() in color_map]

    # Create config
    config = StampSegmenterConfig(
        colors=stamp_colors or [StampColor.BLUE, StampColor.RED, StampColor.GREEN],
        mode=stamp_mode,
    )

    # Process
    segmenter = StampSegmenter(config)
    result = segmenter.process(image)

    # Return based on mode
    if mode.lower() == "detect":
        return None, result.stamp_regions
    elif return_metadata:
        return result.cleaned_image, result.stamp_regions
    else:
        return result.cleaned_image, []


def detect_colored_stamps(
    image: np.ndarray | Image.Image,
) -> list[dict]:
    """
    Detect colored stamps in an image and return metadata only.

    This is a convenience function for quickly detecting stamps without
    modifying the image. Useful for analysis or conditional processing.

    Args:
        image: Input image (BGR numpy array or PIL Image)

    Returns:
        List of stamp metadata dicts, each containing:
        - color: Detected color name (blue, red, green, purple, unknown)
        - bbox: Bounding box (x, y, width, height)
        - area: Total pixel area
        - centroid: Center point (x, y)
        - confidence: Detection confidence (0-1)

    Example:
        >>> stamps = detect_colored_stamps(cv2.imread("document.png"))
        >>> if stamps:
        ...     print(f"Found {len(stamps)} stamps")
        ...     if any(s['color'] == 'blue' for s in stamps):
        ...         print("Document has official blue stamp!")
    """
    _, stamps = process_stamps_advanced(image, mode="detect")
    return stamps


def remove_stamps_for_ocr(
    image: np.ndarray | Image.Image,
) -> np.ndarray:
    """
    Remove all colored stamps from image to prepare for OCR.

    This is the most common use case: remove any colored stamps
    that might interfere with text extraction.

    Args:
        image: Input image (BGR numpy array or PIL Image)

    Returns:
        Grayscale image with stamps removed, ready for OCR

    Example:
        >>> img = cv2.imread("stamped_document.png")
        >>> cleaned = remove_stamps_for_ocr(img)
        >>> # Now pass cleaned to OCR engine
    """
    from .stamp_segmenter import StampSegmenter

    segmenter = StampSegmenter.for_ocr()
    result = segmenter.process(image)
    return result.cleaned_image


def extract_stamp_images(
    image: np.ndarray | Image.Image,
) -> tuple[list[np.ndarray], list[dict]]:
    """
    Extract individual stamp images from a document.

    Useful for archiving stamps separately or for stamp recognition.

    Args:
        image: Input image (BGR numpy array or PIL Image)

    Returns:
        Tuple of (stamp_images, stamp_metadata)
        - stamp_images: List of cropped stamp images (BGR numpy arrays)
        - stamp_metadata: List of StampRegion dicts

    Example:
        >>> stamps, metadata = extract_stamp_images(cv2.imread("document.png"))
        >>> for i, (img, meta) in enumerate(zip(stamps, metadata)):
        ...     cv2.imwrite(f"stamp_{i}_{meta['color']}.png", img)
    """
    from .stamp_segmenter import StampSegmenter

    segmenter = StampSegmenter.for_extraction()
    result = segmenter.process(image)
    return result.extracted_stamps, result.stamp_regions
