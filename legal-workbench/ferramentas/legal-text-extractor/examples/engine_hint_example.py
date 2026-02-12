#!/usr/bin/env python3
"""
Example: Using Context Store Engine Hints for OCR Optimization.

Demonstrates the NEW global engine hint system that:
1. Learns from document processing history
2. Suggests the best OCR engine based on similar documents
3. Works ACROSS cases (not just within a single case)
4. Falls back gracefully when no history exists

New Features (v2.0):
- get_engine_hint_for_signature(): Global hint search
- get_best_engine_for_pattern_type(): Pattern-based engine stats
- Enhanced Orchestrator integration with 4-tier engine selection

Usage:
    python examples/engine_hint_example.py
"""

import logging
import sys
import tempfile
from pathlib import Path

# Add src to path (for standalone execution)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.context import (
    ContextStore,
    EngineType,
    ObservationResult,
    PageSignatureInput,
    PatternType,
    SignatureVector,
    compute_signature,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_global_engine_hints():
    """
    Demo: Global Engine Hints.

    Shows how the Context Store suggests engines based on
    historical processing results across ALL cases.
    """
    print("=" * 60)
    print("Demo: Global Engine Hints")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "context.db"
        store = ContextStore(db_path)

        # ========================================
        # PHASE 1: Populate with historical data
        # ========================================
        print("\n1. Populating historical data...")

        # Simulate processing Case 1: PDF with tables
        caso1 = store.get_or_create_caso("0001-11.2024.8.26.0100", "pje")
        print(f"   Case 1: {caso1.numero_cnj}")

        # Page with TABLE pattern - Marker works best
        page_input_table = PageSignatureInput(
            page_num=1,
            page_type="NATIVE",
            safe_bbox=[50, 50, 550, 750],
            has_tarja=False,
            char_count=2000,
            complexity="native_with_artifacts",
            recommended_engine="marker",
        )
        sig_table = compute_signature(page_input_table)

        result_table = ObservationResult(
            page_num=1,
            engine_used=EngineType.MARKER,
            confidence=0.95,
            text_length=2000,
            pattern_type=PatternType.TABLE,
            success=True,
        )
        store.learn_from_page(caso1.id, sig_table, result_table)
        print("   - Learned: TABLE with MARKER (conf=0.95)")

        # Simulate processing Case 2: Scanned PDF with headers
        caso2 = store.get_or_create_caso("0002-22.2024.8.26.0200", "eproc")
        print(f"   Case 2: {caso2.numero_cnj}")

        # Page with HEADER pattern - Tesseract works for OCR
        page_input_header = PageSignatureInput(
            page_num=1,
            page_type="RASTER_NEEDED",
            safe_bbox=[50, 50, 550, 750],
            has_tarja=True,
            tarja_x_cut=540.0,
            char_count=0,  # Scanned
            complexity="raster_dirty",
            recommended_engine="tesseract",
        )
        sig_header = compute_signature(page_input_header)

        result_header = ObservationResult(
            page_num=1,
            engine_used=EngineType.TESSERACT,
            confidence=0.78,
            text_length=500,
            pattern_type=PatternType.HEADER,
            success=True,
        )
        store.learn_from_page(caso2.id, sig_header, result_header)
        print("   - Learned: HEADER (scanned) with TESSERACT (conf=0.78)")

        # Add more occurrences to build confidence
        import sqlite3

        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE observed_patterns SET occurrence_count = 10")
            conn.commit()
        print("   - Updated occurrence counts for reliability")

        # ========================================
        # PHASE 2: Query hints for new documents
        # ========================================
        print("\n2. Querying hints for new documents...")

        # New Case 3: Unknown document, similar to Case 1's table
        print("\n   Scenario A: New document with table-like signature")
        new_page_table = PageSignatureInput(
            page_num=1,
            page_type="NATIVE",
            safe_bbox=[55, 45, 545, 755],  # Similar to Case 1
            has_tarja=False,
            char_count=1900,  # Similar char count
            complexity="native_with_artifacts",
        )
        new_sig_table = compute_signature(new_page_table)

        hint = store.get_engine_hint_for_signature(
            signature_vector=new_sig_table.features,
            pattern_type=PatternType.TABLE,
            caso_id=None,  # Search globally
            min_occurrences=2,
        )

        if hint:
            print("   HINT FOUND!")
            print(f"   - Suggested engine: {hint.suggested_engine.value}")
            print(f"   - Confidence: {hint.confidence:.2f}")
            print(f"   - Similarity: {hint.similarity:.3f}")
            print(f"   - Based on {hint.occurrence_count} historical occurrences")
            print(f"   - Should use: {hint.should_use}")
        else:
            print("   No hint found (insufficient history)")

        # New document similar to scanned header
        print("\n   Scenario B: New scanned document with header")
        new_page_header = PageSignatureInput(
            page_num=1,
            page_type="RASTER_NEEDED",
            safe_bbox=[48, 52, 548, 748],
            has_tarja=True,
            tarja_x_cut=535.0,
            char_count=0,
            complexity="raster_dirty",
        )
        new_sig_header = compute_signature(new_page_header)

        hint2 = store.get_engine_hint_for_signature(
            signature_vector=new_sig_header.features,
            pattern_type=PatternType.HEADER,
            caso_id=None,
            min_occurrences=2,
        )

        if hint2:
            print("   HINT FOUND!")
            print(f"   - Suggested engine: {hint2.suggested_engine.value}")
            print(f"   - Confidence: {hint2.confidence:.2f}")
            print(f"   - Similarity: {hint2.similarity:.3f}")
        else:
            print("   No hint found")

        # ========================================
        # PHASE 3: Pattern-type based recommendations
        # ========================================
        print("\n3. Pattern-type based recommendations...")

        for pattern_type in [PatternType.TABLE, PatternType.HEADER, PatternType.IMAGE]:
            best = store.get_best_engine_for_pattern_type(pattern_type)
            if best:
                print(f"   Best engine for {pattern_type.value}: {best.value}")
            else:
                print(f"   No data for {pattern_type.value}")

        # ========================================
        # PHASE 4: Engine statistics
        # ========================================
        print("\n4. Engine statistics...")
        stats = store.get_engine_stats()
        for stat in stats:
            print(
                f"   {stat.engine.value}: "
                f"{stat.total_patterns} patterns, "
                f"avg_conf={stat.avg_confidence:.2f}, "
                f"reliability={stat.reliability_score:.2f}"
            )


def demo_orchestrator_integration():
    """
    Demo: Orchestrator Integration.

    Shows how the PipelineOrchestrator automatically uses
    engine hints during document processing.
    """
    print("\n" + "=" * 60)
    print("Demo: Orchestrator Integration")
    print("=" * 60)

    print("""
The PipelineOrchestrator now uses a 4-tier engine selection:

1. ContextStore Hint (if strong)
   - Queries get_engine_hint_for_signature()
   - Searches globally across all cases
   - Requires similarity >= 0.85 AND confidence >= 0.7

2. Layout Analysis Recommendation
   - From step_01_layout analysis
   - Based on page characteristics (native/raster, complexity)

3. Pattern-Type Historical Best
   - Queries get_best_engine_for_pattern_type()
   - Uses aggregated stats from all processed documents

4. Complexity-Based Fallback
   - Uses COMPLEXITY_ENGINE_MAP
   - Guaranteed to return a valid engine

Usage in Orchestrator:

    orchestrator = PipelineOrchestrator(
        context_db_path=Path("context.db"),
        caso_info={"numero_cnj": "...", "sistema": "pje"}
    )

    # Engine hints are queried automatically
    result = orchestrator.process(pdf_path)

The Orchestrator logs which selection tier was used:
    DEBUG - Using hint engine: marker (confidence=0.95, similarity=0.92)
    DEBUG - Using layout-recommended engine: pdfplumber
    DEBUG - Using historical best engine for table: marker
    DEBUG - Using complexity-based fallback engine: pdfplumber
""")


def demo_case_specific_priority():
    """
    Demo: Case-Specific Priority.

    Shows that patterns from the same case have priority
    over global patterns (more relevant context).
    """
    print("\n" + "=" * 60)
    print("Demo: Case-Specific Priority")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "context.db"
        store = ContextStore(db_path)

        # Case 1: Uses MARKER for tables
        caso1 = store.get_or_create_caso("caso1", "pje")
        sig1 = SignatureVector(features=[0.5, 0.5, 0.5, 0.5, 0.5], hash="table1")
        result1 = ObservationResult(
            page_num=1,
            engine_used=EngineType.MARKER,
            confidence=0.90,
            text_length=1000,
            pattern_type=PatternType.TABLE,
        )
        store.learn_from_page(caso1.id, sig1, result1)
        print("1. Case 1 learned: MARKER with conf=0.90")

        # Case 2: Uses PDFPLUMBER for similar tables (different context)
        caso2 = store.get_or_create_caso("caso2", "eproc")
        sig2 = SignatureVector(features=[0.51, 0.49, 0.5, 0.5, 0.5], hash="table2")
        result2 = ObservationResult(
            page_num=1,
            engine_used=EngineType.PDFPLUMBER,
            confidence=0.95,  # Higher confidence
            text_length=1200,
            pattern_type=PatternType.TABLE,
        )
        store.learn_from_page(caso2.id, sig2, result2)
        print("2. Case 2 learned: PDFPLUMBER with conf=0.95 (higher)")

        # When searching for Case 1, Case 1's pattern should be preferred
        print("\n3. Searching with Case 1 context...")
        hint = store.get_engine_hint_for_signature(
            signature_vector=[0.5, 0.5, 0.5, 0.5, 0.5],
            pattern_type=PatternType.TABLE,
            caso_id=caso1.id,  # Prioritize Case 1
        )

        if hint:
            print(f"   Result: {hint.suggested_engine.value}")
            print("   (Case-specific pattern has priority)")
            assert hint.suggested_engine == EngineType.MARKER
            print("   PASS: Correctly returned MARKER (case-specific)")
        else:
            print("   No hint found")


if __name__ == "__main__":
    demo_global_engine_hints()
    demo_orchestrator_integration()
    demo_case_specific_priority()

    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)
