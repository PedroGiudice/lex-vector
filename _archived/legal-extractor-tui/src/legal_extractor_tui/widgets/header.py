"""Header widget with ASCII logo, title and status indicator.

Example:
    ```python
    from legal_extractor_tui.widgets.header import Header

    header = Header()
    header.set_status("Running", "green")
    ```
"""

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static


class Header(Container):
    """Header widget displaying logo, title and status.

    Attributes:
        DEFAULT_CSS: Inline CSS styling for the header
    """

    # CSS moved to widgets.tcss for centralized theme management

    def __init__(
        self,
        title: str = "TUI Template App",
        logo: str | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the header.

        Args:
            title: Application title to display
            logo: Optional custom ASCII logo (uses default if None)
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(name=name, id=id, classes=classes)
        self._title = title
        self._logo = logo or self._default_logo()
        self._status_text = ""
        self._status_style = ""

    def _default_logo(self) -> str:
        """Generate default ASCII logo - compact with neon gradient.

        Returns:
            Multi-line ASCII art logo string with Rich markup for gradient colors.
            Gradient: Pink (#ff79c6) -> Purple (#bd93f9)
        """
        # 4-line "LEGAL EXTRACTOR" in degradê neon (rosa -> roxo)
        # Estilo filled blocks, compacto, inspirado em Gemini CLI
        return """[#ff79c6]██╗     ███████╗ ██████╗  █████╗ ██╗         ███████╗██╗  ██╗████████╗██████╗  █████╗  ██████╗████████╗ ██████╗ ██████╗[/]
[#e77dba]██║     ██╔════╝██╔════╝ ██╔══██╗██║         ██╔════╝╚██╗██╔╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗[/]
[#cf7dae]██║     █████╗  ██║  ███╗███████║██║         █████╗   ╚███╔╝    ██║   ██████╔╝███████║██║        ██║   ██║   ██║██████╔╝[/]
[#b77da2]██║     ██╔══╝  ██║   ██║██╔══██║██║         ██╔══╝   ██╔██╗    ██║   ██╔══██╗██╔══██║██║        ██║   ██║   ██║██╔══██╗[/]
[#9f7d96]███████╗███████╗╚██████╔╝██║  ██║███████╗    ███████╗██╔╝ ██╗   ██║   ██║  ██║██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║[/]
[#bd93f9]╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝[/]"""

    def compose(self) -> ComposeResult:
        """Compose the header layout.

        Yields:
            Static widgets for logo, title and status
        """
        yield Static(self._logo, classes="logo")
        yield Static(self._title, classes="title")
        yield Static(self._status_text, classes="status", id="header-status")

    def set_status(self, status: str, style: str = "") -> None:
        """Update the status indicator.

        Args:
            status: Status text to display
            style: Rich markup style (e.g., "green", "red bold", "[cyan]text[/]")

        Example:
            ```python
            header.set_status("Ready", "green")
            header.set_status("Error", "red bold")
            header.set_status("[yellow]Warning[/]")
            ```
        """
        self._status_text = status
        self._status_style = style

        status_widget = self.query_one("#header-status", Static)
        if style and not style.startswith("["):
            # Wrap in Rich markup if not already formatted
            formatted_status = f"[{style}]{status}[/]"
        else:
            formatted_status = status

        status_widget.update(formatted_status)

    def set_title(self, title: str) -> None:
        """Update the title text.

        Args:
            title: New title to display
        """
        self._title = title
        title_widget = self.query_one(".title", Static)
        title_widget.update(title)
