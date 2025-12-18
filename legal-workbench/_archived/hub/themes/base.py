"""
Base theme definitions and shared color palette.

The BaseTheme dataclass defines all color slots that can be customized.
SHARED_THEME provides the default terminal aesthetic used across all modules.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class BaseTheme:
    """
    Immutable theme configuration.

    All colors use hex format (#RRGGBB).
    Module themes override accent colors while inheriting backgrounds/text.
    """

    # Identity
    id: str
    name: str
    icon: str = "📦"
    tagline: str = ""

    # Backgrounds (consistent across modules)
    bg_primary: str = "#0a0f1a"      # Main app background
    bg_secondary: str = "#0f172a"    # Cards, containers
    bg_tertiary: str = "#1a2332"     # Elevated surfaces
    bg_hover: str = "#2d3748"        # Interactive hover states

    # Text (consistent across modules)
    text_primary: str = "#e2e8f0"    # Main content
    text_secondary: str = "#94a3b8"  # Subtitles, labels
    text_muted: str = "#64748b"      # Placeholders, hints

    # Accent (MODULE-SPECIFIC - override these)
    accent_primary: str = "#f59e0b"     # Primary action color
    accent_secondary: str = "#d97706"   # Hover/active state
    accent_muted: str = "#92400e"       # Disabled/subtle
    accent_glow: str = "rgba(245, 158, 11, 0.15)"  # Focus rings, shadows

    # Semantic (universal meaning - don't change per module)
    success: str = "#22c55e"    # PROVIDO, success states
    danger: str = "#dc2626"     # DESPROVIDO, errors
    warning: str = "#eab308"    # PARCIAL, warnings
    info: str = "#3b82f6"       # Information, tips

    # Borders
    border_default: str = "#1e293b"   # Standard borders
    border_hover: str = "#334155"     # Border on hover
    border_focus: str = field(init=False)  # Computed from accent

    # Typography
    font_mono: str = "'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace"
    font_sans: str = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

    def __post_init__(self):
        # Set border_focus to accent_primary if not explicitly set
        object.__setattr__(self, 'border_focus', self.accent_primary)

    def to_css_vars(self) -> dict:
        """Convert theme to CSS custom property dictionary."""
        return {
            "--bg-primary": self.bg_primary,
            "--bg-secondary": self.bg_secondary,
            "--bg-tertiary": self.bg_tertiary,
            "--bg-hover": self.bg_hover,
            "--text-primary": self.text_primary,
            "--text-secondary": self.text_secondary,
            "--text-muted": self.text_muted,
            "--accent": self.accent_primary,
            "--accent-secondary": self.accent_secondary,
            "--accent-muted": self.accent_muted,
            "--accent-glow": self.accent_glow,
            "--success": self.success,
            "--danger": self.danger,
            "--warning": self.warning,
            "--info": self.info,
            "--border": self.border_default,
            "--border-hover": self.border_hover,
            "--border-focus": self.border_focus,
            "--font-mono": self.font_mono,
            "--font-sans": self.font_sans,
        }


# Default shared theme (amber accent - terminal aesthetic)
SHARED_THEME = BaseTheme(
    id="shared",
    name="Legal Workbench",
    icon="⚖️",
    tagline="Ferramentas jurídicas inteligentes",
)
