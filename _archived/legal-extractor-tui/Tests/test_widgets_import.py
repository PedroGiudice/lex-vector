#!/usr/bin/env python3
"""Test that all custom widgets can be imported successfully."""

from legal_extractor_tui.widgets import (
    ConfigPanel,
    ExtractionProgress,
    FileSelector,
    ResultsPanel,
    SystemSelector,
    JUDICIAL_SYSTEMS,
    SYSTEM_NAMES,
)

from legal_extractor_tui.messages import (
    ConfigChanged,
    ExportRequested,
    ExtractionCancelled,
    ExtractionCompleted,
    ExtractionError,
    ExtractionProgress as ExtractionProgressMsg,
    ExtractionStarted,
    FileSelected,
    SystemChanged,
)


def test_imports():
    """Test that all imports work."""
    print("Testing widget imports...")

    # Test widget classes exist
    assert FileSelector is not None
    assert SystemSelector is not None
    assert ExtractionProgress is not None
    assert ResultsPanel is not None
    assert ConfigPanel is not None

    print("  - FileSelector: OK")
    print("  - SystemSelector: OK")
    print("  - ExtractionProgress: OK")
    print("  - ResultsPanel: OK")
    print("  - ConfigPanel: OK")

    # Test constants
    assert len(JUDICIAL_SYSTEMS) == 7
    assert len(SYSTEM_NAMES) == 7
    assert "auto" in JUDICIAL_SYSTEMS
    assert "pje" in JUDICIAL_SYSTEMS

    print("  - JUDICIAL_SYSTEMS: OK")
    print("  - SYSTEM_NAMES: OK")

    # Test message classes exist
    assert FileSelected is not None
    assert SystemChanged is not None
    assert ConfigChanged is not None
    assert ExportRequested is not None
    assert ExtractionStarted is not None
    assert ExtractionProgressMsg is not None
    assert ExtractionCompleted is not None
    assert ExtractionError is not None
    assert ExtractionCancelled is not None

    print("\nTesting message imports...")
    print("  - FileSelected: OK")
    print("  - SystemChanged: OK")
    print("  - ConfigChanged: OK")
    print("  - ExportRequested: OK")
    print("  - ExtractionStarted: OK")
    print("  - ExtractionProgress: OK")
    print("  - ExtractionCompleted: OK")
    print("  - ExtractionError: OK")
    print("  - ExtractionCancelled: OK")

    print("\n✅ All imports successful!")


if __name__ == "__main__":
    test_imports()
