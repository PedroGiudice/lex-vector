"""
Programmatic Vision - Test Fixtures for Textual TUI Testing.

This module provides standardized pytest fixtures for headless TUI testing
using textual.pilot. It enables "Evidence-Based Commitment" where developers
must prove widgets render correctly, not just claim they do.

The Vision Pipeline:
    1. Retina (textual.pilot) - Headless app driving
    2. Optic Nerve (this file) - Standardized async fixtures
    3. Visual Cortex (vision-guide.md) - Geometry assertion patterns

Usage:
    @pytest.mark.parametrize("pilot_app", [LegalExtractorApp], indirect=True)
    async def test_widget_renders(pilot_app):
        pilot = pilot_app
        widget = pilot.app.query_one("#my-widget")
        assert widget.region.height > 0, "Widget collapsed to zero height!"
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
async def pilot_app(request):
    """
    Fixture that handles async pilot setup/teardown automatically.

    This is the "Optic Nerve" - it connects the test to the app's visual state.

    Usage:
        @pytest.mark.parametrize("pilot_app", [MyApp], indirect=True)
        async def test_something(pilot_app):
            pilot = pilot_app
            # pilot.app gives you the App instance
            # Use pilot.click(), pilot.press(), etc. for interaction

    Args:
        request: pytest request object containing the App class via parametrize

    Yields:
        Pilot instance with full DOM access
    """
    app_class = request.param
    app = app_class()
    async with app.run_test() as pilot:
        # Wait for any scheduled animations to complete
        await pilot.wait_for_scheduled_animations()
        yield pilot


@pytest.fixture
async def app_with_size(request):
    """
    Fixture for testing with specific terminal size.

    Usage:
        @pytest.mark.parametrize("app_with_size", [(MyApp, 120, 40)], indirect=True)
        async def test_responsive(app_with_size):
            pilot = app_with_size
            # Test with 120x40 terminal
    """
    app_class, width, height = request.param
    app = app_class()
    async with app.run_test(size=(width, height)) as pilot:
        await pilot.wait_for_scheduled_animations()
        yield pilot


def dump_tree(app, output_file: str = None) -> str:
    """
    Dump the DOM tree for debugging.

    This is the "Text-Based Screenshot" - when tests fail, this shows
    exactly how Textual sees the widget hierarchy.

    Args:
        app: The Textual App instance
        output_file: Optional path to write the dump

    Returns:
        String representation of the DOM tree (properly rendered)
    """
    from io import StringIO
    from rich.console import Console

    # app.tree returns a Rich Tree object, we need to render it to string
    tree = app.tree
    string_io = StringIO()
    console = Console(file=string_io, force_terminal=True, width=120)
    console.print(tree)
    tree_str = string_io.getvalue()

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        Path(output_file).write_text(tree_str)

    return tree_str


def assert_widget_visible(widget, name: str = "Widget"):
    """
    Assert that a widget has non-zero dimensions (is actually visible).

    This catches the most common TUI bug: CSS causing widgets to collapse
    to 0 height/width due to improper height: auto or missing constraints.

    Args:
        widget: The Textual widget to check
        name: Human-readable name for error messages

    Raises:
        AssertionError: If widget has zero dimensions
    """
    region = widget.region
    assert region.width > 0, f"{name} has zero width! CSS likely broken. Region: {region}"
    assert region.height > 0, f"{name} has zero height! CSS likely broken. Region: {region}"


def assert_widget_contains(parent, child_selector: str, parent_name: str = "Parent"):
    """
    Assert that a parent widget contains a child matching selector.

    Args:
        parent: Parent widget to search within
        child_selector: CSS selector for child (e.g., "#button", ".status")
        parent_name: Human-readable name for error messages

    Raises:
        AssertionError: If child not found in parent's DOM
    """
    try:
        child = parent.query_one(child_selector)
        assert child is not None
    except Exception as e:
        raise AssertionError(
            f"{parent_name} does not contain '{child_selector}'. "
            f"Available children: {[c.css_identifier for c in parent.children]}"
        ) from e


def assert_focus_reachable(app, widget_id: str):
    """
    Assert that a widget can receive focus (is interactive).

    This catches focus traps where layout blocks user interaction.

    Args:
        app: The Textual App instance
        widget_id: ID of widget that should be focusable

    Raises:
        AssertionError: If widget cannot be focused
    """
    widget = app.query_one(f"#{widget_id}")
    assert widget.can_focus, f"Widget #{widget_id} cannot receive focus!"


# Pytest configuration
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "vision: mark test as a visual/geometry verification test"
    )


# Hook to dump tree on test failure
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Dump DOM tree on test failure for debugging."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        # Try to get app from fixture
        if hasattr(item, "funcargs") and "pilot_app" in item.funcargs:
            pilot = item.funcargs["pilot_app"]
            if hasattr(pilot, "app"):
                log_path = Path("logs/vision_failure.log")
                log_path.parent.mkdir(parents=True, exist_ok=True)

                tree_dump = dump_tree(pilot.app)
                with open(log_path, "a") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"FAILED: {item.name}\n")
                    f.write(f"{'='*60}\n")
                    f.write(tree_dump)
                    f.write("\n")
