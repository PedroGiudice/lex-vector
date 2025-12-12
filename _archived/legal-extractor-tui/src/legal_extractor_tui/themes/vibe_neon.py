"""Vibe Neon theme - Dracula/Cyberpunk aesthetic."""

from textual.theme import Theme

VIBE_NEON_THEME = Theme(
    name="vibe-neon",
    primary="#8be9fd",      # Cyan (Dracula cyan)
    secondary="#bd93f9",    # Purple (Dracula purple)
    accent="#ff79c6",       # Pink (Dracula pink)
    foreground="#f8f8f2",   # Light gray (Dracula foreground)
    background="#000000",   # Pure black for maximum contrast
    surface="#0d0d0d",      # Near black for subtle depth
    panel="#0d0d0d",        # Near black - consistent dark base
    success="#50fa7b",
    warning="#ffb86c",
    error="#ff5555",
    dark=True,
    variables={
        # CRITICAL: Explicit foreground for CSS variable resolution
        "foreground": "#f8f8f2",
        # Lighten/Darken variants
        "primary-lighten-1": "#a8f0ff",
        "primary-darken-1": "#6ec8db",
        "secondary-lighten-1": "#d0b0ff",
        "secondary-darken-1": "#9a75d4",
        "accent-lighten-1": "#ff9ad6",
        "accent-darken-1": "#d960a8",
        "success-lighten-1": "#7cff9e",
        "success-darken-1": "#40c862",
        "warning-lighten-1": "#ffcc99",
        "warning-darken-1": "#d99650",
        "error-lighten-1": "#ff8080",
        "error-darken-1": "#cc4444",
        # Original variables
        "block-cursor-background": "#ff79c6",
        "block-cursor-foreground": "#0d0d0d",
        "block-cursor-text-style": "bold",
        "border": "#8be9fd",
        "border-blurred": "#44475a",
        "footer-background": "#1e1e2e",
        "footer-foreground": "#f8f8f2",
        "footer-key-foreground": "#50fa7b",
        "scrollbar": "#44475a",
        "scrollbar-hover": "#6272a4",
        "scrollbar-active": "#8be9fd",
        "scrollbar-background": "#0d0d0d",
        "input-cursor-background": "#f8f8f2",
        "input-cursor-foreground": "#0d0d0d",
        "input-selection-background": "#44475a 60%",
        "link-color": "#8be9fd",
        "link-color-hover": "#ff79c6",
        "button-foreground": "#f8f8f2",
        "button-focus-text-style": "bold reverse",
        # Text utilities - CRITICAL for visibility
        "text": "#f8f8f2",            # Base text color (same as foreground)
        "text-muted": "#6272a4",      # Dracula comment color
        "text-disabled": "#44475a",   # Even more muted
        # Semantic text colors for auto-contrast
        "text-primary": "#8be9fd",
        "text-secondary": "#bd93f9",
        "text-accent": "#ff79c6",
        "text-success": "#50fa7b",
        "text-warning": "#ffb86c",
        "text-error": "#ff5555",
    },
)
