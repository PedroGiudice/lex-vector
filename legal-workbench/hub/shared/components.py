"""
Reusable UI components for all modules.

All components return FastHTML FT objects and use CSS classes
defined in themes/css_generator.py.
"""

from fasthtml.common import *
from typing import Optional, List


def outcome_badge(outcome: str) -> FT:
    """
    Render an outcome badge (PROVIDO/DESPROVIDO/PARCIAL).

    Args:
        outcome: The outcome text

    Returns:
        Styled badge span
    """
    badge_map = {
        "PROVIDO": "badge-provido",
        "DESPROVIDO": "badge-desprovido",
        "PARCIAL": "badge-parcial",
        "PROVIMENTO": "badge-provido",
        "DESPROVIMENTO": "badge-desprovido",
    }
    cls = badge_map.get(outcome.upper(), "badge-info")
    return Span(outcome, cls=f"badge {cls}")


def loading_spinner(size: str = "md") -> FT:
    """
    Render a loading spinner.

    Args:
        size: Size variant (sm, md, lg)

    Returns:
        Spinner div
    """
    size_classes = {
        "sm": "w-4 h-4",
        "md": "w-6 h-6",
        "lg": "w-8 h-8",
    }
    return Div(cls=f"loading {size_classes.get(size, 'w-6 h-6')}")


def empty_state(
    icon: str = "📭",
    title: str = "Nenhum resultado",
    message: str = "Tente ajustar seus filtros de busca.",
    action: Optional[FT] = None,
) -> FT:
    """
    Render an empty state placeholder.

    Args:
        icon: Emoji or icon character
        title: Main heading
        message: Description text
        action: Optional action button

    Returns:
        Empty state container
    """
    return Div(
        Div(icon, cls="text-4xl mb-4"),
        H3(title, cls="text-lg font-semibold mb-2"),
        P(message, cls="text-sm text-secondary mb-4"),
        action if action else "",
        cls="text-center py-12 text-muted",
    )


def module_header(
    icon: str,
    name: str,
    tagline: str = "",
) -> FT:
    """
    Render a module header with icon and title.

    Args:
        icon: Module emoji/icon
        name: Module name
        tagline: Short description

    Returns:
        Header container
    """
    return Div(
        H1(f"{icon} {name}"),
        P(tagline, cls="tagline") if tagline else "",
        cls="module-header",
    )


def card(
    title: str,
    *content,
    footer: Optional[FT] = None,
    header_extra: Optional[FT] = None,
) -> FT:
    """
    Render a card container.

    Args:
        title: Card title
        content: Card body content
        footer: Optional footer content
        header_extra: Extra content in header (e.g., badge)

    Returns:
        Card container
    """
    header = Div(
        H3(title),
        header_extra if header_extra else "",
        cls="card-header",
    )

    body = Div(*content, cls="card-body")

    foot = Div(footer, cls="card-footer") if footer else ""

    return Div(header, body, foot, cls="card")


def terminal_output(
    lines: List[str],
    title: str = "Output",
) -> FT:
    """
    Render a terminal-style output display.

    Args:
        lines: List of output lines
        title: Terminal title

    Returns:
        Terminal container
    """
    def format_line(line: str) -> FT:
        if "ERROR" in line or "ERRO" in line:
            cls = "terminal-line terminal-error"
        elif "WARNING" in line or "AVISO" in line:
            cls = "terminal-line terminal-warning"
        elif "SUCCESS" in line or "SUCESSO" in line:
            cls = "terminal-line terminal-success"
        else:
            cls = "terminal-line"
        return Div(line, cls=cls)

    return Div(
        Div(title, cls="text-xs text-muted mb-2 font-mono"),
        Div(
            *[format_line(line) for line in lines],
            cls="terminal",
        ),
    )
