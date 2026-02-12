#!/usr/bin/env python3
"""
Demo script for StampSegmenter - HSV-based colored stamp detection.

This script demonstrates the key capabilities of the stamp segmentation system:
1. Detecting colored stamps (blue, red, green) in documents
2. Removing stamps for clean OCR
3. Extracting individual stamp images
4. Getting detailed metadata about detected stamps

Usage:
    cd ferramentas/legal-text-extractor
    source .venv/bin/activate
    python scripts/demo_stamp_segmenter.py
"""

import sys
from pathlib import Path

import cv2
import numpy as np

# Adiciona o diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.image_cleaner import (
    detect_colored_stamps,
    extract_stamp_images,
    process_stamps_advanced,
    remove_stamps_for_ocr,
)
from src.core.stamp_segmenter import (
    HSVRange,
    StampMode,
    StampSegmenter,
    StampSegmenterConfig,
)


def create_demo_document() -> np.ndarray:
    """Create a synthetic legal document with colored stamps."""
    # White background (A4 proportions)
    img = np.full((800, 600, 3), 255, dtype=np.uint8)

    # Header text (black)
    cv2.rectangle(img, (50, 30), (550, 60), (0, 0, 0), -1)
    cv2.putText(
        img, "PODER JUDICIARIO", (180, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
    )

    # Body text (black lines simulating paragraphs)
    for y in range(100, 400, 30):
        cv2.rectangle(img, (50, y), (550, y + 15), (0, 0, 0), -1)

    # Blue circular stamp (official seal) - top right
    cv2.circle(img, (480, 150), 50, (255, 100, 50), -1)  # Blue in BGR
    cv2.circle(img, (480, 150), 40, (255, 150, 80), 2)
    cv2.putText(img, "OFICIAL", (445, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    # Red rectangular stamp ("URGENTE") - bottom
    cv2.rectangle(img, (200, 500), (400, 560), (50, 50, 255), -1)  # Red in BGR
    cv2.putText(img, "URGENTE", (245, 540), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Green elliptical stamp (environmental) - side
    cv2.ellipse(img, (100, 600), (60, 40), 0, 0, 360, (50, 200, 50), -1)  # Green
    cv2.putText(img, "IBAMA", (70, 605), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # More text after stamps
    for y in range(650, 750, 30):
        cv2.rectangle(img, (50, y), (550, y + 15), (0, 0, 0), -1)

    return img


def demo_basic_detection():
    """Demo 1: Basic stamp detection."""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Stamp Detection")
    print("=" * 60)

    img = create_demo_document()
    segmenter = StampSegmenter()
    result = segmenter.process(img)

    print(f"\nDocument analyzed in {result.processing_time_ms:.2f}ms")
    print(f"Stamps detected: {len(result.stamp_regions)}")

    if result.has_stamps:
        print("\nDetected stamps:")
        for i, stamp in enumerate(result.stamp_regions, 1):
            print(f"  {i}. Color: {stamp['color']}")
            print(f"     Position: x={stamp['bbox'][0]}, y={stamp['bbox'][1]}")
            print(f"     Size: {stamp['bbox'][2]}x{stamp['bbox'][3]} pixels")
            print(f"     Area: {stamp['area']} pixels")
            print(f"     Confidence: {stamp['confidence']:.1%}")

    print(f"\nColors found: {result.stamp_colors_found}")
    print(f"Total stamp area: {result.total_stamp_area} pixels")


def demo_stamp_removal():
    """Demo 2: Remove stamps for OCR."""
    print("\n" + "=" * 60)
    print("DEMO 2: Remove Stamps for OCR")
    print("=" * 60)

    img = create_demo_document()

    # Using convenience function
    cleaned = remove_stamps_for_ocr(img)

    print(f"\nOriginal image shape: {img.shape}")
    print(f"Cleaned image shape: {cleaned.shape}")
    print(f"Cleaned image is grayscale: {len(cleaned.shape) == 2}")

    # Verify stamps were removed (check mean intensity in stamp regions)
    # Blue stamp was at (480, 150) with radius 50
    stamp_region = cleaned[100:200, 430:530]
    mean_intensity = np.mean(stamp_region)
    print(f"\nBlue stamp region mean intensity: {mean_intensity:.1f}")
    print(f"Stamp successfully removed: {mean_intensity > 200}")


def demo_stamp_extraction():
    """Demo 3: Extract individual stamps."""
    print("\n" + "=" * 60)
    print("DEMO 3: Extract Individual Stamps")
    print("=" * 60)

    img = create_demo_document()

    stamps, metadata = extract_stamp_images(img)

    print(f"\nExtracted {len(stamps)} stamp images")

    for i, (stamp_img, meta) in enumerate(zip(stamps, metadata), 1):
        print(f"\n  Stamp {i}: {meta['color']}")
        print(f"    Image size: {stamp_img.shape}")
        print(f"    Centroid: {meta['centroid']}")


def demo_custom_config():
    """Demo 4: Custom HSV configuration."""
    print("\n" + "=" * 60)
    print("DEMO 4: Custom HSV Configuration")
    print("=" * 60)

    img = create_demo_document()

    # Create custom config for only blue stamps
    custom_blue = HSVRange(
        h_min=100,
        h_max=130,
        s_min=40,  # Lower saturation threshold
        v_min=40,
        name="custom_blue",
    )

    config = StampSegmenterConfig(
        custom_ranges=[custom_blue],
        mode=StampMode.BOTH,
        min_area=500,  # Only larger stamps
    )

    segmenter = StampSegmenter(config)
    result = segmenter.process(img)

    print("\nUsing custom config for blue stamps only:")
    print(f"  Stamps found: {len(result.stamp_regions)}")
    for stamp in result.stamp_regions:
        print(f"    - {stamp['color']} at {stamp['bbox'][:2]}")


def demo_integration_with_cleaner():
    """Demo 5: Integration with ImageCleaner module."""
    print("\n" + "=" * 60)
    print("DEMO 5: Integration with ImageCleaner")
    print("=" * 60)

    img = create_demo_document()

    # Using process_stamps_advanced from image_cleaner
    cleaned, metadata = process_stamps_advanced(
        img,
        mode="remove",
        colors=["blue", "red"],  # Only blue and red
        return_metadata=True,
    )

    print("\nUsing process_stamps_advanced:")
    print(f"  Cleaned image shape: {cleaned.shape if cleaned is not None else 'None'}")
    print(f"  Stamps found: {len(metadata)}")

    # Using detect_colored_stamps
    all_stamps = detect_colored_stamps(img)
    print("\nUsing detect_colored_stamps:")
    print(f"  Total stamps: {len(all_stamps)}")


def run_all_demos():
    """Run all demonstration functions."""
    print("\n" + "=" * 60)
    print("STAMP SEGMENTER - DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo shows HSV-based colored stamp detection for")
    print("legal documents. Commonly used for:")
    print("  - Removing stamps before OCR")
    print("  - Extracting stamps for archival")
    print("  - Detecting document authenticity markers")

    demo_basic_detection()
    demo_stamp_removal()
    demo_stamp_extraction()
    demo_custom_config()
    demo_integration_with_cleaner()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_all_demos()
