"""Base widgets for TUI applications.

This module provides a collection of reusable Textual widgets for building
terminal user interfaces.

Available Widgets:
    - Header: Application header with logo, title and status
    - Sidebar: Collapsible navigation sidebar with OptionList
    - LogPanel: Rich log panel with colored levels and timestamps
    - PipelineProgress: Multi-stage progress tracking for pipelines
    - StatusBar: System metrics and runtime information
    - FileBrowser: Directory tree browser with filtering
    - ResultViewer: Markdown viewer for results and documentation
    - PowerlineBar: Powerline-style status bar with segments
    - PowerlineHeader: Powerline header with app info and clock
    - PowerlineFooter: Powerline footer with right-aligned segments
    - PowerlineBreadcrumb: Clickable breadcrumb navigation
    - SpinnerWidget: Universal spinner (Rich + custom animations)
    - Blinker: Simple blinking cursor
    - InputCursor: Terminal-style input with blinking cursor

Example:
    ```python
    from legal_extractor_tui.widgets import (
        Header,
        Sidebar,
        LogPanel,
        PipelineProgress,
        StatusBar,
        FileBrowser,
        ResultViewer,
        PowerlineBar,
        PowerlineSegment,
        PowerlineBreadcrumb,
        SpinnerWidget,
        Blinker,
        InputCursor,
    )

    # Create widgets
    header = Header(title="My App")
    sidebar = Sidebar()
    log_panel = LogPanel()
    pipeline = PipelineProgress(["Download", "Process", "Upload"])
    status_bar = StatusBar()
    file_browser = FileBrowser(path="./data")
    result_viewer = ResultViewer()

    # Powerline widgets
    powerline = PowerlineBar([
        PowerlineSegment("Status", "$foreground", "$primary"),
        PowerlineSegment("Ready", "$foreground", "$success")
    ])
    breadcrumb = PowerlineBreadcrumb(["Home", "Projects", "TUI"])

    # Spinners and cursors
    spinner = SpinnerWidget("claude", source="custom", text="Loading...")
    cursor = InputCursor(prompt="$ ", cursor_type="block")
    ```
"""

from legal_extractor_tui.widgets.blinker import Blinker, InputCursor
from legal_extractor_tui.widgets.file_browser import FileBrowser, FileSelected, FilteredDirectoryTree
from legal_extractor_tui.widgets.header import Header
from legal_extractor_tui.widgets.log_panel import LogPanel
from legal_extractor_tui.widgets.powerline_breadcrumb import PowerlineBreadcrumb
from legal_extractor_tui.widgets.powerline_status import (
    PowerlineBar,
    PowerlineFooter,
    PowerlineHeader,
    PowerlineSegment,
)
from legal_extractor_tui.widgets.progress_panel import PipelineProgress, StageProgress
from legal_extractor_tui.widgets.result_viewer import ResultViewer
from legal_extractor_tui.widgets.sidebar import OptionSelected, Sidebar
from legal_extractor_tui.widgets.spinner_widget import SpinnerWidget
from legal_extractor_tui.widgets.spinners import CUSTOM_SPINNERS
from legal_extractor_tui.widgets.status_bar import StatusBar

__all__ = [
    # Core widgets
    "Header",
    "Sidebar",
    "LogPanel",
    "PipelineProgress",
    "StatusBar",
    "FileBrowser",
    "ResultViewer",
    # Powerline widgets
    "PowerlineBar",
    "PowerlineHeader",
    "PowerlineFooter",
    "PowerlineSegment",
    "PowerlineBreadcrumb",
    # Spinner and cursor widgets
    "SpinnerWidget",
    "Blinker",
    "InputCursor",
    # Sub-components
    "StageProgress",
    "FilteredDirectoryTree",
    # Messages
    "OptionSelected",
    "FileSelected",
    # Constants
    "CUSTOM_SPINNERS",
]

# Legal extractor specific widgets
from legal_extractor_tui.widgets.config_panel import ConfigPanel
from legal_extractor_tui.widgets.extraction_progress import ExtractionProgress
from legal_extractor_tui.widgets.file_selector import FileSelector
from legal_extractor_tui.widgets.results_panel import ResultsPanel
from legal_extractor_tui.widgets.system_selector import (
    SystemSelector,
    JUDICIAL_SYSTEMS,
    SYSTEM_NAMES,
)

# Add to exports
__all__.extend([
    "FileSelector",
    "SystemSelector",
    "ExtractionProgress",
    "ResultsPanel",
    "ConfigPanel",
    "JUDICIAL_SYSTEMS",
    "SYSTEM_NAMES",
])
