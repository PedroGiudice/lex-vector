"""
Compute page signatures for pattern matching.

A signature is a feature vector that captures the visual/structural
characteristics of a page, enabling similarity matching against
previously observed patterns.

Feature vector components (normalized to 0.0-1.0):
1. Page dimensions ratio (width/height)
2. Text area ratio (safe_bbox area / total area)
3. Character density (chars / safe_bbox area)
4. Has tarja (lateral stripe) - boolean as float
5. Tarja position ratio (tarja_x_cut / page_width)
6. Complexity score (derived from PageComplexity)
7. Recommended engine score (derived from engine type)
8. Needs cleaning - boolean as float
9. Page type (NATIVE=0.0, RASTER=1.0)
10. Cleaning reasons count (normalized)
"""
import hashlib
import json
from typing import Optional
from dataclasses import dataclass

from .models import SignatureVector, PatternType
from src.config import PageType, PageComplexity


# Complexity to score mapping
COMPLEXITY_SCORES = {
    PageComplexity.NATIVE_CLEAN: 0.0,
    PageComplexity.NATIVE_WITH_ARTIFACTS: 0.25,
    PageComplexity.RASTER_CLEAN: 0.5,
    PageComplexity.RASTER_DIRTY: 0.75,
    PageComplexity.RASTER_DEGRADED: 1.0,
}

# Engine to score mapping
ENGINE_SCORES = {
    "pdfplumber": 0.0,
    "tesseract": 0.5,
    "marker": 1.0,
    "surya": 0.8,
    "docling": 0.7,
}

# Pattern type inference based on page characteristics
PATTERN_INFERENCE_RULES = [
    # (condition_fn, pattern_type, confidence)
    (lambda p: p.get("char_count", 0) < 50, PatternType.IMAGE, 0.7),
    (lambda p: p.get("has_tarja", False), PatternType.HEADER, 0.6),
    (lambda p: p.get("complexity") == PageComplexity.NATIVE_CLEAN, PatternType.TEXT_BLOCK, 0.8),
]


@dataclass
class PageSignatureInput:
    """Input data for signature computation."""
    page_num: int
    page_type: str  # "NATIVE" or "RASTER_NEEDED"
    safe_bbox: list[float]  # [x0, y0, x1, y1]
    has_tarja: bool
    char_count: int

    # Optional fields (may not be present in all layouts)
    page_width: float = 612.0  # Default letter width in points
    page_height: float = 792.0  # Default letter height in points
    tarja_x_cut: Optional[float] = None
    complexity: Optional[str] = None
    recommended_engine: Optional[str] = None
    needs_cleaning: bool = False
    cleaning_reason: Optional[list[str]] = None

    @classmethod
    def from_layout_page(cls, page_data: dict, page_width: float = 612.0, page_height: float = 792.0) -> "PageSignatureInput":
        """Create from layout.json page data."""
        return cls(
            page_num=page_data["page_num"],
            page_type=page_data["type"],
            safe_bbox=page_data["safe_bbox"],
            has_tarja=page_data.get("has_tarja", False),
            char_count=page_data.get("char_count", 0),
            page_width=page_width,
            page_height=page_height,
            tarja_x_cut=page_data.get("tarja_x_cut"),
            complexity=page_data.get("complexity"),
            recommended_engine=page_data.get("recommended_engine"),
            needs_cleaning=page_data.get("needs_cleaning", False),
            cleaning_reason=page_data.get("cleaning_reason"),
        )


def compute_signature(page_input: PageSignatureInput) -> SignatureVector:
    """
    Compute signature vector for a page.

    Args:
        page_input: Page data for signature computation

    Returns:
        SignatureVector with 10-dimensional feature vector

    Example:
        >>> page = PageSignatureInput(
        ...     page_num=1,
        ...     page_type="NATIVE",
        ...     safe_bbox=[0, 0, 590, 800],
        ...     has_tarja=True,
        ...     char_count=1500,
        ...     page_width=612,
        ...     page_height=792,
        ...     tarja_x_cut=580.0,
        ...     complexity="native_with_artifacts",
        ...     recommended_engine="pdfplumber",
        ...     needs_cleaning=True,
        ...     cleaning_reason=["lateral_stripe_detected"]
        ... )
        >>> sig = compute_signature(page)
        >>> len(sig.features)
        10
    """
    features = []

    # 1. Page dimensions ratio (width/height)
    if page_input.page_height > 0:
        dim_ratio = min(page_input.page_width / page_input.page_height, 2.0) / 2.0
    else:
        dim_ratio = 0.5
    features.append(dim_ratio)

    # 2. Text area ratio (safe_bbox area / total area)
    total_area = page_input.page_width * page_input.page_height
    if total_area > 0:
        bbox = page_input.safe_bbox
        bbox_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        area_ratio = min(bbox_area / total_area, 1.0)
    else:
        area_ratio = 1.0
    features.append(area_ratio)

    # 3. Character density (chars / safe_bbox area, normalized)
    if bbox_area > 0:
        # Typical density is around 0.01-0.1 chars per square point
        raw_density = page_input.char_count / bbox_area
        char_density = min(raw_density * 10, 1.0)  # Scale up and cap
    else:
        char_density = 0.0
    features.append(char_density)

    # 4. Has tarja (boolean as float)
    features.append(1.0 if page_input.has_tarja else 0.0)

    # 5. Tarja position ratio
    if page_input.tarja_x_cut is not None and page_input.page_width > 0:
        tarja_ratio = page_input.tarja_x_cut / page_input.page_width
    else:
        tarja_ratio = 0.0 if not page_input.has_tarja else 0.85  # Default tarja at 85%
    features.append(tarja_ratio)

    # 6. Complexity score
    complexity = page_input.complexity or (
        PageComplexity.NATIVE_CLEAN if page_input.page_type == "NATIVE" else PageComplexity.RASTER_DIRTY
    )
    complexity_score = COMPLEXITY_SCORES.get(complexity, 0.5)
    features.append(complexity_score)

    # 7. Recommended engine score
    engine = page_input.recommended_engine or "pdfplumber"
    engine_score = ENGINE_SCORES.get(engine, 0.5)
    features.append(engine_score)

    # 8. Needs cleaning (boolean as float)
    features.append(1.0 if page_input.needs_cleaning else 0.0)

    # 9. Page type (NATIVE=0.0, RASTER=1.0)
    page_type_score = 0.0 if page_input.page_type == PageType.NATIVE else 1.0
    features.append(page_type_score)

    # 10. Cleaning reasons count (normalized, max 5)
    reasons_count = len(page_input.cleaning_reason or [])
    features.append(min(reasons_count / 5.0, 1.0))

    # Compute hash
    vector_str = json.dumps(features, sort_keys=True)
    hash_str = hashlib.md5(vector_str.encode()).hexdigest()

    return SignatureVector(features=features, hash=hash_str)


def infer_pattern_type(page_input: PageSignatureInput) -> tuple[PatternType, float]:
    """
    Infer the most likely pattern type for a page.

    Args:
        page_input: Page data

    Returns:
        Tuple of (PatternType, confidence)
    """
    page_dict = {
        "page_num": page_input.page_num,
        "page_type": page_input.page_type,
        "safe_bbox": page_input.safe_bbox,
        "has_tarja": page_input.has_tarja,
        "char_count": page_input.char_count,
        "complexity": page_input.complexity,
    }

    for condition_fn, pattern_type, confidence in PATTERN_INFERENCE_RULES:
        try:
            if condition_fn(page_dict):
                return pattern_type, confidence
        except Exception:
            continue

    # Default: TEXT_BLOCK with moderate confidence
    return PatternType.TEXT_BLOCK, 0.5


def compute_signature_from_layout(layout_page: dict, page_width: float = 612.0, page_height: float = 792.0) -> SignatureVector:
    """
    Convenience function to compute signature directly from layout.json page.

    Args:
        layout_page: Page dict from layout.json
        page_width: Page width in points (default: letter)
        page_height: Page height in points (default: letter)

    Returns:
        SignatureVector

    Example:
        >>> layout = {"pages": [{"page_num": 1, "type": "NATIVE", ...}]}
        >>> sig = compute_signature_from_layout(layout["pages"][0])
    """
    page_input = PageSignatureInput.from_layout_page(layout_page, page_width, page_height)
    return compute_signature(page_input)
