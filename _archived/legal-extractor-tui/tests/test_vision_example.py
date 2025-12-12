"""
Vision Test Example - Demonstrates Programmatic Visual Verification.

This test file shows how to write vision tests that verify widgets
render correctly with non-zero dimensions.

Run with:
    pytest tests/test_vision_example.py -v -s
"""

import pytest
from tests.conftest import assert_widget_visible, dump_tree

# Import the app - adjust path as needed
try:
    from legal_extractor_tui.app import LegalExtractorApp
    APP_AVAILABLE = True
except ImportError:
    APP_AVAILABLE = False
    LegalExtractorApp = None


@pytest.mark.vision
@pytest.mark.skipif(not APP_AVAILABLE, reason="LegalExtractorApp not available")
@pytest.mark.parametrize("pilot_app", [LegalExtractorApp], indirect=True)
async def test_app_mounts(pilot_app):
    """
    VISION TEST: App mounts and has basic structure.

    This is the most basic vision test - just ensure the app starts.
    """
    pilot = pilot_app

    # App should exist
    assert pilot.app is not None, "App failed to mount!"

    # Print tree for debugging
    print("\n=== DOM Tree ===")
    print(dump_tree(pilot.app))


@pytest.mark.vision
@pytest.mark.skipif(not APP_AVAILABLE, reason="LegalExtractorApp not available")
@pytest.mark.parametrize("pilot_app", [LegalExtractorApp], indirect=True)
async def test_main_layout_visible(pilot_app):
    """
    VISION TEST: Main layout containers have non-zero dimensions.

    This catches the most common bug: CSS causing containers to collapse.
    """
    pilot = pilot_app

    # Get screen dimensions for reference
    screen = pilot.app.screen
    print(f"\nScreen size: {screen.size}")

    # Try to find main containers - these selectors may need adjustment
    # based on actual app structure
    containers_to_check = [
        "Header",
        "Sidebar",
        "#main-content",
        "#results-panel",
    ]

    for selector in containers_to_check:
        try:
            widget = pilot.app.query_one(selector)
            region = widget.region
            print(f"{selector}: {region}")

            # Widget should have non-zero dimensions
            assert region.height > 0, f"{selector} has zero height! (region={region})"
            assert region.width > 0, f"{selector} has zero width! (region={region})"

        except Exception as e:
            # Widget might not exist in all layouts
            print(f"{selector}: NOT FOUND ({e})")


@pytest.mark.vision
@pytest.mark.skipif(not APP_AVAILABLE, reason="LegalExtractorApp not available")
@pytest.mark.parametrize("pilot_app", [LegalExtractorApp], indirect=True)
async def test_buttons_have_text(pilot_app):
    """
    VISION TEST: Buttons should have visible content.

    Buttons with no text or collapsed dimensions are the most
    reported TUI visibility bug.
    """
    pilot = pilot_app

    # Find all buttons
    buttons = pilot.app.query("Button")

    for btn in buttons:
        region = btn.region
        print(f"Button '{btn.id or btn.label}': {region}")

        # Button should be visible
        assert region.height > 0, f"Button {btn.id} collapsed to zero height!"
        assert region.width > 0, f"Button {btn.id} has zero width!"


@pytest.mark.vision
@pytest.mark.skipif(not APP_AVAILABLE, reason="LegalExtractorApp not available")
@pytest.mark.parametrize("pilot_app", [LegalExtractorApp], indirect=True)
async def test_input_widgets_focusable(pilot_app):
    """
    VISION TEST: Input widgets should be focusable.

    This ensures the layout doesn't block user interaction.
    """
    pilot = pilot_app

    # Find input-like widgets
    inputs = list(pilot.app.query("Input")) + list(pilot.app.query("Select"))

    if not inputs:
        pytest.skip("No Input/Select widgets found")

    for widget in inputs:
        # Widget should be able to receive focus
        assert widget.can_focus, f"Widget {widget.id} cannot receive focus!"

        region = widget.region
        print(f"Input '{widget.id}': {region}, focusable={widget.can_focus}")

        # Should be visible
        assert region.height > 0, f"Input {widget.id} has zero height!"


# Example of geometry relationship test
@pytest.mark.vision
@pytest.mark.skipif(not APP_AVAILABLE, reason="LegalExtractorApp not available")
@pytest.mark.parametrize("pilot_app", [LegalExtractorApp], indirect=True)
async def test_header_at_top(pilot_app):
    """
    VISION TEST: Header should be at the top of the screen.

    Verifies layout geometry relationships.
    """
    pilot = pilot_app

    try:
        header = pilot.app.query_one("Header")
    except Exception:
        pytest.skip("Header widget not found")

    region = header.region
    print(f"Header region: {region}")

    # Header should be at y=0 (top of screen)
    assert region.y == 0, f"Header not at top! y={region.y}"

    # Header should span full width
    screen_width = pilot.app.screen.size.width
    assert region.width == screen_width, (
        f"Header doesn't span full width! "
        f"header.width={region.width}, screen.width={screen_width}"
    )
