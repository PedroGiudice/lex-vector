"""
Example: Using Engine Selector with automatic fallback.

Demonstrates:
1. Automatic PDF analysis (native text vs scanned)
2. Engine selection based on PDF type and available resources
3. Automatic fallback if primary engine fails
4. Resource checking (RAM, dependencies)
"""

import logging
from pathlib import Path
import sys

# Add src to path (for standalone execution)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines import get_selector, ExtractionResult


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """Demo engine selector with multiple PDFs."""

    # Get selector instance (singleton)
    selector = get_selector()

    # List available engines
    print("=== Available Engines ===")
    available = selector.get_available_engines()
    if not available:
        print("ERROR: No extraction engines available!")
        print("\nInstall at least one engine:")
        print("  pip install pdfplumber  # Lightweight, fast")
        print("  pip install pytesseract opencv-python pdf2image  # OCR")
        return

    for engine in available:
        print(f"  - {engine.name} (min RAM: {engine.min_ram_gb}GB)")

    # Example PDFs in test-documents/
    test_docs = Path(__file__).parent.parent / "test-documents"
    pdf_paths = [
        test_docs / "fixtures" / "fixture_pje.pdf",  # Native text
        test_docs / "fixtures" / "fixture_dirty.pdf",  # Mixed
    ]

    # Process each PDF
    for pdf_path in pdf_paths:
        if not pdf_path.exists():
            print(f"\nSkipping {pdf_path.name} (not found)")
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {pdf_path.name}")
        print(f"{'='*60}")

        # Analyze PDF first
        analysis = selector.analyze_pdf(pdf_path)
        print(f"\nPDF Analysis:")
        print(f"  Pages: {analysis['pages']}")
        print(f"  Native text ratio: {analysis['native_text_ratio']:.0%}")
        print(f"  Avg chars/page: {analysis['avg_chars_per_page']:.0f}")
        print(f"  Has native text: {analysis['has_native_text']}")

        # Select engine (without forcing)
        selected = selector.select_engine(pdf_path)
        if not selected:
            print("  ERROR: Could not select engine")
            continue

        print(f"\nSelected engine: {selected.name}")

        # Extract with automatic fallback
        try:
            result: ExtractionResult = selector.extract_with_fallback(
                pdf_path,
                max_retries=3  # Try up to 3 engines
            )

            print(f"\n✓ Extraction successful!")
            print(f"  Engine used: {result.engine_used}")
            print(f"  Pages: {result.pages}")
            print(f"  Characters: {len(result.text)}")
            print(f"  Confidence: {result.confidence:.2f}")

            if result.warnings:
                print(f"  Warnings:")
                for warning in result.warnings:
                    print(f"    - {warning}")

            # Preview first 200 chars
            preview = result.text[:200].replace("\n", " ")
            print(f"\n  Preview: {preview}...")

        except RuntimeError as e:
            print(f"\n✗ Extraction failed: {e}")


def demo_force_engine():
    """Demo forcing a specific engine."""
    print("\n\n=== Demo: Forcing Specific Engine ===")

    selector = get_selector()
    test_pdf = Path(__file__).parent.parent / "test-documents/fixtures/fixture_pje.pdf"

    if not test_pdf.exists():
        print("Test PDF not found")
        return

    # Force tesseract (even if pdfplumber would be better)
    print("\nForcing tesseract engine...")
    try:
        result = selector.extract_with_fallback(
            test_pdf,
            force_engine="tesseract",
            max_retries=1  # Don't fallback if forced engine fails
        )
        print(f"✓ Forced engine succeeded: {result.engine_used}")
        print(f"  Confidence: {result.confidence:.2f}")
    except RuntimeError as e:
        print(f"✗ Forced engine failed: {e}")


if __name__ == "__main__":
    main()
    demo_force_engine()
