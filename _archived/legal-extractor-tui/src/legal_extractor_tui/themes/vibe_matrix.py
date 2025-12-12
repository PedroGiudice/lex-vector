"""Vibe Matrix theme - Matrix/Cyberpunk green aesthetic."""

from textual.theme import Theme

VIBE_MATRIX_THEME = Theme(
    name="vibe-matrix",
    primary="#00ff00",      # Matrix green
    secondary="#003300",    # Dark green
    accent="#39ff14",       # Neon green
    foreground="#00ff00",   # Green text (Matrix style)
    background="#000000",   # Pure black
    surface="#001100",      # Very dark green
    panel="#001a00",        # Slightly lighter dark green
    success="#00ff00",      # Green
    warning="#ccff00",      # Yellow-green
    error="#ff3300",        # Orange-red (still visible on green)
    dark=True,
    variables={
        # CRITICAL: Explicit foreground for CSS variable resolution
        "foreground": "#f8f8f2",
        # Lighten/Darken variants
        "primary-lighten-1": "#33ff33",
        "primary-darken-1": "#00cc00",
        "secondary-lighten-1": "#004400",
        "secondary-darken-1": "#002200",
        "accent-lighten-1": "#66ff44",
        "accent-darken-1": "#2acc10",
        "success-lighten-1": "#33ff33",
        "success-darken-1": "#00cc00",
        "warning-lighten-1": "#ddff33",
        "warning-darken-1": "#aacc00",
        "error-lighten-1": "#ff6633",
        "error-darken-1": "#cc2200",
        # Original variables
        "block-cursor-background": "#00ff00",
        "block-cursor-foreground": "#000000",
        "block-cursor-text-style": "bold",
        "border": "#00ff00",
        "border-blurred": "#004400",
        "footer-background": "#001100",
        "footer-foreground": "#00ff00",
        "footer-key-foreground": "#39ff14",
        "scrollbar": "#003300",
        "scrollbar-hover": "#004400",
        "scrollbar-active": "#00ff00",
        "scrollbar-background": "#001100",
        "input-cursor-background": "#00ff00",
        "input-cursor-foreground": "#000000",
        "input-selection-background": "#003300 60%",
        "link-color": "#39ff14",
        "link-color-hover": "#00ff00",
        "button-foreground": "#00ff00",
        "button-focus-text-style": "bold reverse",
        # Text utilities
        "text-muted": "#006600",
        "text-disabled": "#003300",
    },
)
