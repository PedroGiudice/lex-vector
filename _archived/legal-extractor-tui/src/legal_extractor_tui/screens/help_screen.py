"""Help screen with keybindings and usage instructions.

This module provides a modal help screen displaying keybindings,
features, and usage instructions.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Markdown, Static

HELP_CONTENT = """# TUI Template Help

## Keybindings

### Global
- **?** - Show this help screen
- **q** / **Ctrl+C** - Quit application
- **Escape** - Cancel running operation / Close help

### Main Screen
- **b** - Toggle sidebar visibility
- **r** - Run demo pipeline
- **Ctrl+L** - Clear log panel
- **Tab** / **Shift+Tab** - Navigate between widgets

### Sidebar
- **Up** / **Down** - Navigate options
- **Enter** - Select option
- **Space** - Toggle option (if applicable)

### Log Panel
- **1-5** - Filter by log level (1=DEBUG, 2=INFO, 3=WARNING, 4=ERROR, 5=SUCCESS)
- **0** - Show all logs
- **c** - Clear logs

### File Browser
- **Enter** - Select file/expand directory
- **Backspace** - Go to parent directory
- **/** - Focus search/filter
- **Escape** - Clear filter

## Features

### Pipeline Execution
Execute multi-step workflows with real-time progress tracking:
1. Press **r** to run demo pipeline
2. Watch progress in Pipeline Progress widget
3. View logs in Log Panel
4. Press **Escape** to cancel if needed

### Log Management
- Real-time log display with color-coded levels
- Filter logs by severity level (DEBUG, INFO, WARNING, ERROR, SUCCESS)
- Timestamps and structured formatting
- Clear logs with **c** or Ctrl+L

### Results Viewer
- Markdown rendering for results
- Syntax highlighting for code blocks
- Collapsible sections
- Export results (coming soon)

### File Browser
- Navigate directory tree
- Filter files by pattern
- Select files for processing
- Preview file metadata

## Status Bar

The status bar shows:
- Current operation status
- Active filters
- Pipeline state
- System metrics

## Tips

- Use **Tab** to quickly navigate between widgets
- Check the footer for context-sensitive keybindings
- Log levels: DEBUG < INFO < WARNING < ERROR < SUCCESS
- Press **Escape** at any time to cancel operations

## About

**TUI Template** is a production-ready template for building
terminal user interfaces with Textual.

Features:
- Multi-stage pipeline execution
- Real-time progress tracking
- Structured logging
- File browsing
- Markdown results viewer
- Theme support
- Responsive layout

For more information, visit the project repository.

---

Press **Escape** or **q** to close this help screen.
"""


class HelpScreen(ModalScreen):
    """Modal help screen with keybindings and instructions.

    Displays comprehensive help content including:
        - Keybindings for all screens and widgets
        - Feature descriptions
        - Usage tips
        - About information

    Keybindings:
        - Escape: Close help screen
        - q: Close help screen
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=True),
        Binding("q", "dismiss", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose help screen layout.

        Yields:
            Centered modal with help content and close button
        """
        with Center():
            with Middle():
                with Vertical(id="help-dialog"):
                    yield Static("Help", id="help-title")
                    yield Markdown(HELP_CONTENT, id="help-content")
                    yield Button("Close [Esc]", id="close-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle close button press.

        Args:
            event: Button pressed event
        """
        if event.button.id == "close-btn":
            self.dismiss()

    def action_dismiss(self) -> None:
        """Close the help screen."""
        self.dismiss()
