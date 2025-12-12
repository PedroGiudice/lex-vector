"""Vibe Synthwave theme - Retro 80s aesthetic with pink/purple/cyan."""

from textual.theme import Theme

VIBE_SYNTHWAVE_THEME = Theme(
    name="vibe-synthwave",
    primary="#ff00ff",      # Magenta
    secondary="#00ffff",    # Cyan
    accent="#ff6ec7",       # Hot pink
    foreground="#ffffff",   # White text
    background="#0d0221",   # Dark purple-black
    surface="#1a0533",      # Dark purple
    panel="#2a0a4a",        # Slightly lighter purple
    success="#00ff9f",      # Neon green-cyan
    warning="#ffff00",      # Yellow
    error="#ff0055",        # Hot red-pink
    dark=True,
    variables={
        # CRITICAL: Explicit foreground for CSS variable resolution
        "foreground": "#f8f8f2",
        # Lighten/Darken variants
        "primary-lighten-1": "#ff33ff",
        "primary-darken-1": "#cc00cc",
        "secondary-lighten-1": "#33ffff",
        "secondary-darken-1": "#00cccc",
        "accent-lighten-1": "#ff8ed7",
        "accent-darken-1": "#cc5aa0",
        "success-lighten-1": "#33ffb2",
        "success-darken-1": "#00cc7f",
        "warning-lighten-1": "#ffff33",
        "warning-darken-1": "#cccc00",
        "error-lighten-1": "#ff3377",
        "error-darken-1": "#cc0044",
        # Original variables
        "block-cursor-background": "#ff6ec7",
        "block-cursor-foreground": "#0d0221",
        "block-cursor-text-style": "bold",
        "border": "#ff00ff",
        "border-blurred": "#660066",
        "footer-background": "#1a0533",
        "footer-foreground": "#ffffff",
        "footer-key-foreground": "#00ffff",
        "scrollbar": "#660066",
        "scrollbar-hover": "#990099",
        "scrollbar-active": "#ff00ff",
        "scrollbar-background": "#1a0533",
        "input-cursor-background": "#ff6ec7",
        "input-cursor-foreground": "#0d0221",
        "input-selection-background": "#660066 60%",
        "link-color": "#00ffff",
        "link-color-hover": "#ff6ec7",
        "button-foreground": "#ffffff",
        "button-focus-text-style": "bold reverse",
        # Text utilities
        "text-muted": "#9966cc",
        "text-disabled": "#4d3366",
    },
)
