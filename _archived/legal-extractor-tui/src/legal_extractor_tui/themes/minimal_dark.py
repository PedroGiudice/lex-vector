"""Minimal Dark theme - Clean and professional dark theme."""

from textual.theme import Theme

MINIMAL_DARK_THEME = Theme(
    name="minimal-dark",
    primary="#ffffff",      # White
    secondary="#888888",    # Gray
    accent="#4a9eff",       # Soft blue
    foreground="#e0e0e0",   # Light gray text
    background="#1a1a1a",   # Dark gray (not pure black)
    surface="#242424",      # Slightly lighter dark gray
    panel="#2d2d2d",        # Panel background
    success="#4caf50",      # Material green
    warning="#ff9800",      # Material orange
    error="#f44336",        # Material red
    dark=True,
    variables={
        # CRITICAL: Explicit foreground for CSS variable resolution
        "foreground": "#f8f8f2",
        # Lighten/Darken variants
        "primary-lighten-1": "#ffffff",
        "primary-darken-1": "#cccccc",
        "secondary-lighten-1": "#aaaaaa",
        "secondary-darken-1": "#666666",
        "accent-lighten-1": "#7ab8ff",
        "accent-darken-1": "#3a7ecc",
        "success-lighten-1": "#6fbf73",
        "success-darken-1": "#3d8c40",
        "warning-lighten-1": "#ffad33",
        "warning-darken-1": "#cc7a00",
        "error-lighten-1": "#f6685e",
        "error-darken-1": "#c3352b",
        # Original variables
        "block-cursor-background": "#4a9eff",
        "block-cursor-foreground": "#1a1a1a",
        "block-cursor-text-style": "bold",
        "border": "#444444",
        "border-blurred": "#333333",
        "footer-background": "#242424",
        "footer-foreground": "#e0e0e0",
        "footer-key-foreground": "#4a9eff",
        "scrollbar": "#444444",
        "scrollbar-hover": "#555555",
        "scrollbar-active": "#4a9eff",
        "scrollbar-background": "#242424",
        "input-cursor-background": "#e0e0e0",
        "input-cursor-foreground": "#1a1a1a",
        "input-selection-background": "#444444 60%",
        "link-color": "#4a9eff",
        "link-color-hover": "#7ab8ff",
        "button-foreground": "#e0e0e0",
        "button-focus-text-style": "bold reverse",
        # Text utilities
        "text-muted": "#888888",
        "text-disabled": "#555555",
    },
)
