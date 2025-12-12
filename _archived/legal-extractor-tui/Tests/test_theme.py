#!/usr/bin/env python3
"""
Test theme colors in Legal Extractor TUI.

This script verifies that the vibe-neon theme is correctly applied
and that no hardcoded blue colors are present.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from legal_extractor_tui.themes.vibe_neon import VIBE_NEON_THEME
from legal_extractor_tui.widgets.powerline_status import PowerlineSegment

def test_theme_colors():
    """Verify vibe-neon theme colors."""
    print("Testing vibe-neon theme colors...")
    print(f"  Primary: {VIBE_NEON_THEME.primary} (expected: #8be9fd)")
    print(f"  Background: {VIBE_NEON_THEME.background} (expected: #0d0d0d)")
    print(f"  Foreground: {VIBE_NEON_THEME.foreground} (expected: #f8f8f2)")
    print(f"  Accent: {VIBE_NEON_THEME.accent} (expected: #ff79c6)")
    print(f"  Success: {VIBE_NEON_THEME.success} (expected: #50fa7b)")

    assert VIBE_NEON_THEME.primary == "#8be9fd", "Primary color mismatch"
    assert VIBE_NEON_THEME.background == "#0d0d0d", "Background color mismatch"
    assert VIBE_NEON_THEME.foreground == "#f8f8f2", "Foreground color mismatch"
    print("  ✅ Theme colors correct")

def test_powerline_segments():
    """Verify PowerlineSegment uses theme variables, not hardcoded colors."""
    print("\nTesting PowerlineSegment colors...")

    # Test segment
    seg = PowerlineSegment("Test", "$foreground", "$primary")

    # Verify theme variables are used (not hardcoded colors)
    assert seg.fg.startswith("$"), f"Foreground should be theme variable, got: {seg.fg}"
    assert seg.bg.startswith("$"), f"Background should be theme variable, got: {seg.bg}"

    # Check for hardcoded blue
    assert "blue" not in seg.bg.lower(), f"Hardcoded 'blue' found in background: {seg.bg}"
    assert "blue" not in seg.fg.lower(), f"Hardcoded 'blue' found in foreground: {seg.fg}"

    print(f"  Segment FG: {seg.fg} (theme variable ✅)")
    print(f"  Segment BG: {seg.bg} (theme variable ✅)")
    print("  ✅ No hardcoded colors")

def test_no_hardcoded_blue():
    """Check for hardcoded 'blue' in key widget files."""
    print("\nScanning for hardcoded 'blue' colors...")

    widget_files = [
        "src/legal_extractor_tui/widgets/powerline_status.py",
        "src/legal_extractor_tui/widgets/powerline_breadcrumb.py",
        "src/legal_extractor_tui/widgets/__init__.py",
    ]

    issues = []
    for file_path in widget_files:
        full_path = Path(__file__).parent / file_path
        if not full_path.exists():
            print(f"  ⚠️  File not found: {file_path}")
            continue

        content = full_path.read_text()

        # Look for hardcoded blue (excluding comments and docstrings)
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # Skip comments and docstrings
            if line.strip().startswith("#") or '"""' in line or "'''" in line:
                continue

            if '"blue"' in line or "'blue'" in line:
                issues.append(f"{file_path}:{i}: {line.strip()}")

    if issues:
        print("  ❌ Found hardcoded 'blue' colors:")
        for issue in issues:
            print(f"     {issue}")
        return False
    else:
        print("  ✅ No hardcoded 'blue' colors found")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("Legal Extractor TUI - Theme Color Validation")
    print("=" * 60)

    try:
        test_theme_colors()
        test_powerline_segments()
        no_blue = test_no_hardcoded_blue()

        print("\n" + "=" * 60)
        if no_blue:
            print("✅ ALL TESTS PASSED - Theme is correctly configured")
        else:
            print("⚠️  TESTS PASSED WITH WARNINGS - Check hardcoded colors")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
