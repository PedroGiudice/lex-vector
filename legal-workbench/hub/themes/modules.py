"""
Module-specific theme definitions.

Each module has a unique accent color that reflects its functional purpose:
- STJ: Observatory Purple (discovery, research)
- Text Extractor: Industrial Copper (processing, transformation)
- Doc Assembler: Blueprint Blue (construction, precision)
- Trello: Command Green (coordination, workflow)
"""

from typing import Dict
from .base import BaseTheme, SHARED_THEME


# ============================================================================
# STJ DADOS ABERTOS - Observatory Purple
# Purpose: Legal research, data exploration, analysis
# Mood: Discovery, insight, depth
# ============================================================================
STJ_THEME = BaseTheme(
    id="stj",
    name="STJ Dados Abertos",
    icon="🔭",
    tagline="Explore a jurisprudência do Superior Tribunal de Justiça",
    accent_primary="#8b5cf6",      # Violet-500
    accent_secondary="#7c3aed",    # Violet-600
    accent_muted="#6d28d9",        # Violet-700
    accent_glow="rgba(139, 92, 246, 0.15)",
)


# ============================================================================
# TEXT EXTRACTOR - Industrial Copper
# Purpose: Document transformation, extraction, processing
# Mood: Mechanical, reliable, transformative
# ============================================================================
TEXT_EXTRACTOR_THEME = BaseTheme(
    id="text_extractor",
    name="Text Extractor",
    icon="⚙️",
    tagline="Transforme documentos legais com extração inteligente",
    accent_primary="#d97706",      # Amber-600 (warm copper)
    accent_secondary="#b45309",    # Amber-700
    accent_muted="#92400e",        # Amber-800
    accent_glow="rgba(217, 119, 6, 0.15)",
)


# ============================================================================
# DOC ASSEMBLER - Blueprint Blue
# Purpose: Template-based document construction
# Mood: Precise, structured, creative
# ============================================================================
DOC_ASSEMBLER_THEME = BaseTheme(
    id="doc_assembler",
    name="Document Assembler",
    icon="📐",
    tagline="Construa documentos a partir de templates inteligentes",
    accent_primary="#0ea5e9",      # Sky-500 (blueprint blue)
    accent_secondary="#0284c7",    # Sky-600
    accent_muted="#0369a1",        # Sky-700
    accent_glow="rgba(14, 165, 233, 0.15)",
)


# ============================================================================
# TRELLO MCP - Command Green
# Purpose: Task management, coordination, workflow
# Mood: Operational, decisive, active
# ============================================================================
TRELLO_THEME = BaseTheme(
    id="trello",
    name="Trello MCP",
    icon="🎛️",
    tagline="Coordene tarefas e extraia dados do Trello",
    accent_primary="#10b981",      # Emerald-500 (command green)
    accent_secondary="#059669",    # Emerald-600
    accent_muted="#047857",        # Emerald-700
    accent_glow="rgba(16, 185, 129, 0.15)",
)


# ============================================================================
# THEME REGISTRY
# ============================================================================
THEMES: Dict[str, BaseTheme] = {
    "shared": SHARED_THEME,
    "stj": STJ_THEME,
    "text_extractor": TEXT_EXTRACTOR_THEME,
    "doc_assembler": DOC_ASSEMBLER_THEME,
    "trello": TRELLO_THEME,
}


def get_theme(theme_id: str) -> BaseTheme:
    """
    Get a theme by ID with fallback to shared theme.

    Args:
        theme_id: Theme identifier (e.g., "stj", "text_extractor")

    Returns:
        BaseTheme instance

    Example:
        >>> theme = get_theme("stj")
        >>> theme.accent_primary
        '#8b5cf6'
    """
    return THEMES.get(theme_id, SHARED_THEME)
