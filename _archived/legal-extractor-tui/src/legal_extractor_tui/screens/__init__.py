"""Screen definitions for Legal Extractor TUI.

This package contains all screen classes for the application,
including the main screen and modal screens.

Available Screens:
    - MainScreen: Primary application screen with full UI
    - HelpScreen: Modal help screen with keybindings and instructions
    - FileBrowserScreen: Modal screen for selecting PDF files
    - PreviewModalScreen: Modal screen for previewing extracted text

Example:
    ```python
    from legal_extractor_tui.screens import (
        MainScreen,
        HelpScreen,
        FileBrowserScreen,
        PreviewModalScreen,
    )

    # Install main screen
    app.install_screen(MainScreen(), name="main")

    # Push help screen as modal
    app.push_screen(HelpScreen())

    # Push file browser and handle result
    def handle_selected_file(path: Path | None) -> None:
        if path:
            print(f"Selected: {path}")

    app.push_screen(FileBrowserScreen(), callback=handle_selected_file)

    # Push preview modal with extracted text
    app.push_screen(PreviewModalScreen(text="Extracted content...", metadata={"filename": "doc.pdf"}))
    ```
"""

from legal_extractor_tui.screens.file_browser_screen import FileBrowserScreen
from legal_extractor_tui.screens.help_screen import HelpScreen
from legal_extractor_tui.screens.main_screen import MainScreen
from legal_extractor_tui.screens.preview_modal_screen import PreviewModalScreen

__all__ = [
    "MainScreen",
    "HelpScreen",
    "FileBrowserScreen",
    "PreviewModalScreen",
]
