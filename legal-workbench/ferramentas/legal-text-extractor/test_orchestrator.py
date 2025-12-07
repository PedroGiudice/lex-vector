#!/usr/bin/env python3
"""
Quick test script for PipelineOrchestrator.

Tests basic integration without actually running extraction
(since we don't have real PDFs in test environment).
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import PipelineOrchestrator, PipelineResult


def test_orchestrator_initialization():
    """Test that orchestrator can be initialized."""
    print("Testing PipelineOrchestrator initialization...\n")

    # Test 1: Without ContextStore (one-off mode)
    print("1. Testing one-off mode (no learning):")
    orchestrator = PipelineOrchestrator()
    assert orchestrator.context_store is None
    assert orchestrator.caso is None
    print("   ✓ One-off orchestrator initialized successfully")

    # Test 2: With ContextStore but no caso_info
    print("\n2. Testing with ContextStore (no case info):")
    db_path = Path("/tmp/test_context.db")
    orchestrator = PipelineOrchestrator(context_db_path=db_path)
    assert orchestrator.context_store is not None
    assert orchestrator.caso is None
    print("   ✓ Orchestrator with ContextStore initialized")

    # Test 3: With ContextStore AND caso_info
    print("\n3. Testing with ContextStore and case info:")
    caso_info = {
        "numero_cnj": "1234567-89.2024.8.26.0100",
        "sistema": "pje"
    }
    orchestrator = PipelineOrchestrator(
        context_db_path=db_path,
        caso_info=caso_info
    )
    assert orchestrator.context_store is not None
    assert orchestrator.caso is not None
    assert orchestrator.caso.numero_cnj == caso_info["numero_cnj"]
    assert orchestrator.caso.sistema == caso_info["sistema"]
    print(f"   ✓ Case loaded: {orchestrator.caso.numero_cnj} (id={orchestrator.caso.id})")

    # Test 4: Verify components are initialized
    print("\n4. Verifying integrated components:")
    assert orchestrator.layout_analyzer is not None
    print("   ✓ LayoutAnalyzer initialized")
    assert orchestrator.engine_selector is not None
    print("   ✓ EngineSelector initialized")

    print("\n✅ All initialization tests passed!")


def test_pipeline_result():
    """Test PipelineResult dataclass."""
    print("\nTesting PipelineResult...\n")

    result = PipelineResult(
        text="Extracted text here",
        total_pages=5,
        success=True,
        metadata={"doc_id": "test"},
        patterns_learned=3,
        processing_time_ms=1500,
        warnings=["Warning 1"],
    )

    assert result.text == "Extracted text here"
    assert result.total_pages == 5
    assert result.success is True
    assert result.patterns_learned == 3
    assert result.processing_time_ms == 1500
    assert len(result.warnings) == 1

    print("✅ PipelineResult works correctly!")


def main():
    print("=" * 60)
    print("PipelineOrchestrator Integration Test")
    print("=" * 60)

    try:
        test_pipeline_result()
        test_orchestrator_initialization()

        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Test with actual PDF file (once available)")
        print("2. Verify ContextStore learning loop")
        print("3. Test pattern hint usage")
        print("4. Test engine selection logic")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
