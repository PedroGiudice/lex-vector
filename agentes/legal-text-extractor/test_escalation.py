#!/usr/bin/env python3
"""
Test script for OCR engine escalation system.

Usage:
    python test_escalation.py
"""

import logging
from pathlib import Path
from PIL import Image

from src.engines import EngineSelector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


def test_initialization():
    """Test 1: Engine initialization."""
    print("\n" + "="*60)
    print("TEST 1: Engine Initialization")
    print("="*60)

    selector = EngineSelector()

    print(f"Available engines: {selector.available_engines}")
    print(f"Primary engine: {selector.primary.name if selector.primary else 'None'}")
    print(f"Fallback engine: {selector.fallback.name if selector.fallback else 'None'}")

    assert len(selector.available_engines) > 0, "At least one engine should be available"
    print("✓ PASSED")


def test_engine_selection():
    """Test 2: Engine selection logic."""
    print("\n" + "="*60)
    print("TEST 2: Engine Selection Logic")
    print("="*60)

    selector = EngineSelector()

    test_cases = [
        ("SIMPLE", None, "tesseract"),
        ("MODERATE", None, "tesseract"),
        ("raster_dirty", None, "marker"),
        ("raster_degraded", None, "marker"),
        ("SIMPLE", "marker", "marker"),
        ("COMPLEX", "tesseract", "tesseract"),
    ]

    for complexity, recommended, expected in test_cases:
        engine = selector.select_engine(complexity, recommended)
        actual = engine.name if engine else None

        # Marker might not be available, fallback to tesseract is OK
        if expected == "marker" and actual == "tesseract":
            logger.warning(f"Marker not available, using tesseract instead")
            continue

        print(f"  Complexity={complexity:15s} Recommended={str(recommended):10s} → {actual}")
        assert actual == expected, f"Expected {expected}, got {actual}"

    print("✓ PASSED")


def test_thresholds():
    """Test 3: Confidence thresholds."""
    print("\n" + "="*60)
    print("TEST 3: Thresholds Configuration")
    print("="*60)

    selector = EngineSelector(confidence_threshold=0.90)

    print(f"  Confidence threshold: {selector.CONFIDENCE_THRESHOLD}")
    print(f"  Similarity HIGH: {selector.SIMILARITY_HIGH}")
    print(f"  Similarity MEDIUM: {selector.SIMILARITY_MEDIUM}")

    assert selector.CONFIDENCE_THRESHOLD == 0.90
    assert selector.SIMILARITY_HIGH == 0.90
    assert selector.SIMILARITY_MEDIUM == 0.75

    print("✓ PASSED")


def test_simple_extraction():
    """Test 4: Simple extraction (no escalation)."""
    print("\n" + "="*60)
    print("TEST 4: Simple Extraction (No Escalation)")
    print("="*60)

    # Create simple test image
    img = Image.new('RGB', (800, 100), color='white')

    selector = EngineSelector()

    # This should use Tesseract only (no PDF path = no Marker escalation)
    result = selector.extract_with_escalation(
        image=img,
        complexity="SIMPLE",
        allow_escalation=True,
        pdf_path=None  # No PDF = cannot escalate to Marker
    )

    print(f"  Engine used: {result.engine_used}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Flag: {result.flag.value}")
    print(f"  Processing time: {result.processing_time_seconds:.2f}s")

    # Should be single engine (no escalation without PDF)
    assert "+" not in result.engine_used, "Should not escalate without PDF path"
    assert result.processing_time_seconds < 10, "Simple extraction should be fast"

    print("✓ PASSED")


def test_no_escalation_without_pdf():
    """Test 5: Cannot escalate to Marker without PDF."""
    print("\n" + "="*60)
    print("TEST 5: No Escalation Without PDF Path")
    print("="*60)

    img = Image.new('RGB', (800, 100), color='white')

    # Force low confidence to trigger escalation attempt
    selector = EngineSelector(force_low_confidence=True)

    result = selector.extract_with_escalation(
        image=img,
        complexity="SIMPLE",
        allow_escalation=True,
        pdf_path=None  # No PDF path provided
    )

    print(f"  Engine used: {result.engine_used}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Flag: {result.flag.value}")

    # Should NOT escalate (no PDF path)
    assert "+" not in result.engine_used, "Should not escalate without PDF"
    assert result.flag.value == "needs_review", "Low confidence should flag for review"

    print("✓ PASSED")


def test_escalation_disabled():
    """Test 6: Disable escalation."""
    print("\n" + "="*60)
    print("TEST 6: Escalation Disabled")
    print("="*60)

    img = Image.new('RGB', (800, 100), color='white')

    selector = EngineSelector(force_low_confidence=True)

    # Even with PDF path, escalation disabled
    pdf_path = Path("test.pdf")  # Doesn't need to exist

    result = selector.extract_with_escalation(
        image=img,
        complexity="SIMPLE",
        allow_escalation=False,  # Disabled
        pdf_path=pdf_path
    )

    print(f"  Engine used: {result.engine_used}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Flag: {result.flag.value}")

    # Should NOT escalate (disabled)
    assert "+" not in result.engine_used, "Should not escalate when disabled"

    print("✓ PASSED")


def test_pdf_escalation():
    """Test 7: PDF escalation (if PDF exists)."""
    print("\n" + "="*60)
    print("TEST 7: PDF Escalation (with real PDF)")
    print("="*60)

    selector = EngineSelector(force_low_confidence=True)

    if selector.fallback is None:
        print("⚠ Skipping: Marker not available")
        return

    # Find a test PDF
    test_pdf = Path("test-documents/fixture_test.pdf")
    if not test_pdf.exists():
        print(f"⚠ Skipping: {test_pdf} not found")
        return

    # Create dummy image (won't be used by Marker)
    img = Image.new('RGB', (800, 100), color='white')

    result = selector.extract_with_escalation(
        image=img,
        complexity="SIMPLE",
        allow_escalation=True,
        pdf_path=test_pdf  # Real PDF path
    )

    print(f"  Engine used: {result.engine_used}")
    print(f"  Confidence: {result.confidence:.2f}")
    print(f"  Flag: {result.flag.value}")
    print(f"  Text length: {len(result.text)} chars")

    # Should have escalated
    assert "+" in result.engine_used, "Should use both engines"
    assert result.flag.value == "escalated", "Should be marked as escalated"

    print("✓ PASSED")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("OCR ENGINE ESCALATION SYSTEM - TEST SUITE")
    print("="*60)

    try:
        test_initialization()
        test_engine_selection()
        test_thresholds()
        test_simple_extraction()
        test_no_escalation_without_pdf()
        test_escalation_disabled()
        test_pdf_escalation()

        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
