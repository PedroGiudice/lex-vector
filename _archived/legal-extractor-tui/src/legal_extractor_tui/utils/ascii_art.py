"""ASCII art and logos for TUI Template.

Pre-defined ASCII art for branding and visual elements.
"""

from rich.text import Text

# Compact logo for header bars
LOGO_SMALL = '''╔╦╗╦ ╦╦
 ║ ║ ║║
 ╩ ╚═╝╩'''

# Vibe-inspired large logo
LOGO_VIBE = '''██╗   ██╗██╗██████╗ ███████╗
██║   ██║██║██╔══██╗██╔════╝
██║   ██║██║██████╔╝█████╗
╚██╗ ██╔╝██║██╔══██╗██╔══╝
 ╚████╔╝ ██║██████╔╝███████╗
  ╚═══╝  ╚═╝╚═════╝ ╚══════╝'''

# Alternative compact logo
LOGO_BOX = '''┌─┐┬ ┬┬
├─┤├─┤│
┴ ┴┴ ┴┴'''

# Available logo styles
LOGOS = {
    "small": LOGO_SMALL,
    "vibe": LOGO_VIBE,
    "box": LOGO_BOX,
}


def get_logo(name: str = "small") -> str:
    """Get logo by name.

    Args:
        name: Logo name ('small', 'vibe', or 'box')

    Returns:
        ASCII art string

    Raises:
        KeyError: If logo name not found
    """
    if name not in LOGOS:
        raise KeyError(f"Logo '{name}' not found. Available: {list(LOGOS.keys())}")
    return LOGOS[name]


def colorize_logo(logo: str, color: str = "cyan") -> Text:
    """Colorize logo using Rich styling.

    Args:
        logo: ASCII art string
        color: Rich color name or hex code

    Returns:
        Rich Text object with colored logo

    Example:
        >>> from rich.console import Console
        >>> console = Console()
        >>> logo = get_logo("small")
        >>> console.print(colorize_logo(logo, "magenta"))
    """
    return Text(logo, style=f"bold {color}")


def render_logo(name: str = "small", color: str = "cyan") -> Text:
    """Get and colorize logo in one call.

    Args:
        name: Logo name ('small', 'vibe', or 'box')
        color: Rich color name or hex code

    Returns:
        Colored Rich Text object

    Example:
        >>> from textual.widgets import Static
        >>> logo = render_logo("vibe", "magenta")
        >>> widget = Static(logo)
    """
    return colorize_logo(get_logo(name), color)


# Decorative separators
SEPARATOR_THIN = "─" * 80
SEPARATOR_THICK = "━" * 80
SEPARATOR_DOUBLE = "═" * 80

# Box drawing characters
BOX_CHARS = {
    "tl": "┌",  # top-left
    "tr": "┐",  # top-right
    "bl": "└",  # bottom-left
    "br": "┘",  # bottom-right
    "h": "─",   # horizontal
    "v": "│",   # vertical
    "lt": "├",  # left tee
    "rt": "┤",  # right tee
    "tt": "┬",  # top tee
    "bt": "┴",  # bottom tee
    "x": "┼",   # cross
}


def make_box(text: str, width: int | None = None, padding: int = 1) -> str:
    """Create a box around text using box-drawing characters.

    Args:
        text: Text to box
        width: Box width (auto-calculated if None)
        padding: Horizontal padding inside box

    Returns:
        Multi-line string with boxed text

    Example:
        >>> print(make_box("Hello World", padding=2))
        ┌───────────────┐
        │  Hello World  │
        └───────────────┘
    """
    lines = text.split("\n")
    max_len = max(len(line) for line in lines)

    if width is None:
        width = max_len + (padding * 2)

    # Top border
    result = [f"{BOX_CHARS['tl']}{BOX_CHARS['h'] * (width + 2)}{BOX_CHARS['tr']}"]

    # Content lines
    for line in lines:
        padded = line.ljust(max_len)
        result.append(f"{BOX_CHARS['v']} {' ' * padding}{padded}{' ' * padding} {BOX_CHARS['v']}")

    # Bottom border
    result.append(f"{BOX_CHARS['bl']}{BOX_CHARS['h'] * (width + 2)}{BOX_CHARS['br']}")

    return "\n".join(result)
