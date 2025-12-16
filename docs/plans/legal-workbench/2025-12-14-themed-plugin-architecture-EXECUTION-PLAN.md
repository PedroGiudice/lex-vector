# THEMED PLUGIN ARCHITECTURE: Execution-Ready Implementation Plan

**Date:** 2025-12-14
**Status:** Ready for Execution
**Target:** FastHTML Modular System with Module-Specific Theming
**Location:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/`

---

## OVERVIEW

This plan creates a **production-ready FastHTML application** that combines:
1. **Dynamic Plugin System** — Modules loaded at runtime via ASGI mounting
2. **Module-Specific Theming** — Each module has distinct visual identity
3. **Theme Morphing** — Smooth CSS variable transitions on module switch

**Execution Time:** ~4-6 hours for complete implementation

---

## PHASE 0: PROJECT SETUP

### Step 0.1: Create Directory Structure

```bash
mkdir -p /home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench
cd /home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench
```

Create this exact structure:

```
fasthtml-workbench/
├── main.py                      # Shell application (entry point)
├── requirements.txt             # Dependencies
├── README.md                    # Documentation
├── .env.example                 # Environment template
│
├── core/                        # Core framework
│   ├── __init__.py
│   ├── loader.py                # PluginRegistry & dynamic loading
│   ├── middleware.py            # Theme injection middleware
│   └── config.py                # Global configuration
│
├── themes/                      # Theme system
│   ├── __init__.py              # Exports get_theme, THEMES
│   ├── base.py                  # BaseTheme dataclass + SHARED_THEME
│   ├── modules.py               # Module-specific themes
│   └── css_generator.py         # CSS generation from themes
│
├── shared/                      # Shared components
│   ├── __init__.py
│   ├── components.py            # Common UI components
│   └── layouts.py               # Page layouts
│
├── modules/                     # Plugin modules (auto-discovered)
│   ├── __init__.py
│   ├── stj/                     # STJ Dados Abertos module
│   │   ├── __init__.py          # Exports: app, meta
│   │   ├── routes.py            # Module routes
│   │   └── components.py        # Module-specific components
│   └── _template/               # Template for new modules
│       ├── __init__.py
│       ├── routes.py
│       └── components.py
│
└── static/                      # Static assets
    ├── theme-switcher.js        # Client-side theme transitions
    └── favicon.ico
```

### Step 0.2: Create requirements.txt

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/requirements.txt`

```
python-fasthtml>=0.12.0
uvicorn>=0.30.0
python-dotenv>=1.0.0
httpx>=0.27.0
```

### Step 0.3: Create .env.example

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/.env.example`

```env
# FastHTML Workbench Configuration
APP_NAME=Legal Workbench
APP_VERSION=3.0.0
DEBUG=true
PORT=5001

# Theme defaults
DEFAULT_THEME=shared

# Backend services (for modules that need them)
STJ_API_URL=http://localhost:8000
```

---

## PHASE 1: THEME SYSTEM

### Step 1.1: Create themes/__init__.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/themes/__init__.py`

```python
"""
Theme System for FastHTML Workbench.

Usage:
    from themes import get_theme, THEMES, generate_css

    theme = get_theme("stj")
    css = generate_css(theme)
"""

from .base import BaseTheme, SHARED_THEME
from .modules import (
    STJ_THEME,
    TEXT_EXTRACTOR_THEME,
    DOC_ASSEMBLER_THEME,
    TRELLO_THEME,
    THEMES,
    get_theme,
)
from .css_generator import generate_css, generate_css_variables

__all__ = [
    "BaseTheme",
    "SHARED_THEME",
    "STJ_THEME",
    "TEXT_EXTRACTOR_THEME",
    "DOC_ASSEMBLER_THEME",
    "TRELLO_THEME",
    "THEMES",
    "get_theme",
    "generate_css",
    "generate_css_variables",
]
```

### Step 1.2: Create themes/base.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/themes/base.py`

```python
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
```

### Step 1.3: Create themes/modules.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/themes/modules.py`

```python
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
```

### Step 1.4: Create themes/css_generator.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/themes/css_generator.py`

```python
"""
CSS generation from theme configurations.

Generates:
1. CSS custom properties (:root variables)
2. Base component styles (using variables)
3. Utility classes

The generated CSS uses CSS custom properties (variables) so themes
can be switched at runtime by updating :root values via JavaScript.
"""

from .base import BaseTheme


def generate_css_variables(theme: BaseTheme) -> str:
    """
    Generate CSS custom properties for a theme.

    This is the lightweight version - only variables, no component styles.
    Use for theme switching without full CSS regeneration.
    """
    vars_dict = theme.to_css_vars()
    vars_css = "\n".join(f"    {k}: {v};" for k, v in vars_dict.items())

    return f"""
:root {{
{vars_css}
}}
"""


def generate_css(theme: BaseTheme) -> str:
    """
    Generate complete CSS stylesheet from a theme.

    Includes:
    - CSS custom properties
    - Reset/normalization
    - Component styles (buttons, cards, badges, etc.)
    - Utility classes
    - Animations
    """

    return f"""<style>
/* ============================================================================
   THEME: {theme.name}
   Generated CSS - Do not edit manually
   ============================================================================ */

/* ----------------------------------------------------------------------------
   CSS Custom Properties (Theme Variables)
   ---------------------------------------------------------------------------- */
:root {{
    /* Backgrounds */
    --bg-primary: {theme.bg_primary};
    --bg-secondary: {theme.bg_secondary};
    --bg-tertiary: {theme.bg_tertiary};
    --bg-hover: {theme.bg_hover};

    /* Text */
    --text-primary: {theme.text_primary};
    --text-secondary: {theme.text_secondary};
    --text-muted: {theme.text_muted};

    /* Accent (module-specific) */
    --accent: {theme.accent_primary};
    --accent-secondary: {theme.accent_secondary};
    --accent-muted: {theme.accent_muted};
    --accent-glow: {theme.accent_glow};

    /* Semantic */
    --success: {theme.success};
    --danger: {theme.danger};
    --warning: {theme.warning};
    --info: {theme.info};

    /* Borders */
    --border: {theme.border_default};
    --border-hover: {theme.border_hover};
    --border-focus: {theme.border_focus};

    /* Typography */
    --font-mono: {theme.font_mono};
    --font-sans: {theme.font_sans};

    /* Transitions */
    --transition-fast: 150ms ease;
    --transition-normal: 200ms ease;
    --transition-slow: 300ms ease;
}}

/* Smooth theme transitions */
:root {{
    transition:
        --accent var(--transition-normal),
        --accent-secondary var(--transition-normal),
        --accent-glow var(--transition-normal);
}}

/* ----------------------------------------------------------------------------
   Base Reset & Normalization
   ---------------------------------------------------------------------------- */
*, *::before, *::after {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

html {{
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

body {{
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: var(--font-sans);
    line-height: 1.6;
    min-height: 100vh;
}}

/* Custom Scrollbar */
::-webkit-scrollbar {{
    width: 8px;
    height: 8px;
}}

::-webkit-scrollbar-track {{
    background: var(--bg-secondary);
}}

::-webkit-scrollbar-thumb {{
    background: var(--bg-hover);
    border-radius: 4px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: var(--border-hover);
}}

/* ----------------------------------------------------------------------------
   Layout Components
   ---------------------------------------------------------------------------- */
.container {{
    width: 100%;
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 1rem;
}}

.grid-2 {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
}}

@media (max-width: 768px) {{
    .grid-2 {{
        grid-template-columns: 1fr;
    }}
}}

/* ----------------------------------------------------------------------------
   Cards
   ---------------------------------------------------------------------------- */
.card {{
    background-color: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
}}

.card-header {{
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(90deg, var(--accent-glow) 0%, transparent 100%);
}}

.card-header h2,
.card-header h3 {{
    color: var(--accent);
    font-family: var(--font-mono);
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}

.card-body {{
    padding: 1.25rem;
}}

.card-footer {{
    padding: 1rem 1.25rem;
    border-top: 1px solid var(--border);
    background-color: var(--bg-tertiary);
}}

/* ----------------------------------------------------------------------------
   Buttons
   ---------------------------------------------------------------------------- */
.btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.625rem 1.25rem;
    font-family: var(--font-sans);
    font-size: 0.875rem;
    font-weight: 500;
    border-radius: 6px;
    border: 1px solid transparent;
    cursor: pointer;
    transition: all var(--transition-fast);
    text-decoration: none;
}}

.btn:disabled {{
    opacity: 0.5;
    cursor: not-allowed;
}}

.btn-primary {{
    background-color: var(--accent);
    color: var(--bg-primary);
    border-color: var(--accent);
}}

.btn-primary:hover:not(:disabled) {{
    background-color: var(--accent-secondary);
    border-color: var(--accent-secondary);
}}

.btn-secondary {{
    background-color: transparent;
    color: var(--text-secondary);
    border-color: var(--border);
}}

.btn-secondary:hover:not(:disabled) {{
    background-color: var(--bg-hover);
    color: var(--text-primary);
    border-color: var(--border-hover);
}}

.btn-ghost {{
    background-color: transparent;
    color: var(--text-secondary);
    border-color: transparent;
}}

.btn-ghost:hover:not(:disabled) {{
    background-color: var(--bg-hover);
    color: var(--accent);
}}

/* ----------------------------------------------------------------------------
   Form Elements
   ---------------------------------------------------------------------------- */
.input-field {{
    width: 100%;
    padding: 0.625rem 0.875rem;
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: var(--font-sans);
    font-size: 0.875rem;
    transition: all var(--transition-fast);
}}

.input-field:hover {{
    border-color: var(--border-hover);
}}

.input-field:focus {{
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
}}

.input-field::placeholder {{
    color: var(--text-muted);
}}

/* Select dropdown */
select.input-field {{
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0.75rem center;
    background-size: 1rem;
    padding-right: 2.5rem;
}}

/* Toggle Switch */
.toggle-switch {{
    position: relative;
    display: inline-block;
    width: 44px;
    height: 24px;
}}

.toggle-switch input {{
    opacity: 0;
    width: 0;
    height: 0;
}}

.toggle-slider {{
    position: absolute;
    cursor: pointer;
    inset: 0;
    background-color: var(--bg-hover);
    border-radius: 24px;
    transition: var(--transition-fast);
}}

.toggle-slider::before {{
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: var(--text-secondary);
    border-radius: 50%;
    transition: var(--transition-fast);
}}

input:checked + .toggle-slider {{
    background-color: var(--accent);
}}

input:checked + .toggle-slider::before {{
    transform: translateX(20px);
    background-color: var(--bg-primary);
}}

/* Pills (multi-select) */
.pill {{
    display: inline-flex;
    align-items: center;
    padding: 0.375rem 0.75rem;
    background-color: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border);
    border-radius: 9999px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all var(--transition-fast);
}}

.pill:hover {{
    border-color: var(--accent);
    color: var(--accent);
}}

.pill.selected {{
    background-color: var(--accent);
    color: var(--bg-primary);
    border-color: var(--accent);
}}

/* ----------------------------------------------------------------------------
   Badges
   ---------------------------------------------------------------------------- */
.badge {{
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}

.badge-provido {{
    background-color: rgba(34, 197, 94, 0.15);
    color: var(--success);
    border: 1px solid var(--success);
}}

.badge-desprovido {{
    background-color: rgba(220, 38, 38, 0.15);
    color: var(--danger);
    border: 1px solid var(--danger);
}}

.badge-parcial {{
    background-color: rgba(234, 179, 8, 0.15);
    color: var(--warning);
    border: 1px solid var(--warning);
}}

.badge-info {{
    background-color: rgba(59, 130, 246, 0.15);
    color: var(--info);
    border: 1px solid var(--info);
}}

.badge-accent {{
    background-color: var(--accent-glow);
    color: var(--accent);
    border: 1px solid var(--accent);
}}

/* ----------------------------------------------------------------------------
   Terminal / Code Display
   ---------------------------------------------------------------------------- */
.terminal {{
    background-color: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem;
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    line-height: 1.5;
    max-height: 400px;
    overflow-y: auto;
}}

.terminal-line {{
    padding: 0.125rem 0;
    color: var(--accent);
}}

.terminal-error {{
    color: var(--danger);
}}

.terminal-warning {{
    color: var(--warning);
}}

.terminal-success {{
    color: var(--success);
}}

.sql-preview {{
    background-color: rgba(0, 0, 0, 0.3);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem;
    font-family: var(--font-mono);
    font-size: 0.8125rem;
    color: var(--accent);
    white-space: pre-wrap;
    overflow-x: auto;
}}

/* ----------------------------------------------------------------------------
   Tables
   ---------------------------------------------------------------------------- */
.results-table {{
    width: 100%;
    border-collapse: collapse;
}}

.results-table th {{
    background-color: var(--bg-tertiary);
    color: var(--text-secondary);
    font-weight: 600;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 0.75rem 1rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
}}

.results-table td {{
    padding: 0.875rem 1rem;
    border-bottom: 1px solid var(--border);
    vertical-align: top;
}}

.results-table tr:hover td {{
    background-color: var(--bg-hover);
}}

/* ----------------------------------------------------------------------------
   Module Header
   ---------------------------------------------------------------------------- */
.module-header {{
    background: linear-gradient(90deg, var(--accent-glow) 0%, transparent 100%);
    border-left: 3px solid var(--accent);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}}

.module-header h1 {{
    font-family: var(--font-mono);
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}}

.module-header .tagline {{
    color: var(--text-secondary);
    font-size: 0.875rem;
}}

/* ----------------------------------------------------------------------------
   Sidebar Navigation
   ---------------------------------------------------------------------------- */
.sidebar {{
    width: 240px;
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border);
    min-height: 100vh;
    padding: 1rem 0;
}}

.sidebar-header {{
    padding: 0 1rem 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}}

.sidebar-title {{
    font-family: var(--font-mono);
    font-size: 1rem;
    font-weight: 700;
    color: var(--accent);
}}

.sidebar-item {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all var(--transition-fast);
    position: relative;
    cursor: pointer;
    border: none;
    background: none;
    width: 100%;
    text-align: left;
    font-size: 0.875rem;
}}

.sidebar-item:hover {{
    background-color: var(--bg-hover);
    color: var(--text-primary);
}}

.sidebar-item.active {{
    color: var(--accent);
    background-color: var(--accent-glow);
}}

.sidebar-item.active::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background-color: var(--accent);
}}

.sidebar-icon {{
    font-size: 1.125rem;
}}

/* ----------------------------------------------------------------------------
   Loading States
   ---------------------------------------------------------------------------- */
.loading {{
    display: inline-block;
    width: 1rem;
    height: 1rem;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}}

@keyframes spin {{
    to {{ transform: rotate(360deg); }}
}}

.htmx-indicator {{
    display: none;
}}

.htmx-request .htmx-indicator {{
    display: inline-block;
}}

.htmx-request.htmx-indicator {{
    display: inline-block;
}}

/* Skeleton loading */
.skeleton {{
    background: linear-gradient(
        90deg,
        var(--bg-tertiary) 25%,
        var(--bg-hover) 50%,
        var(--bg-tertiary) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
}}

@keyframes shimmer {{
    0% {{ background-position: 200% 0; }}
    100% {{ background-position: -200% 0; }}
}}

/* ----------------------------------------------------------------------------
   App Layout
   ---------------------------------------------------------------------------- */
.app-layout {{
    display: flex;
    min-height: 100vh;
}}

.app-main {{
    flex: 1;
    padding: 1.5rem;
    overflow-y: auto;
}}

.app-header {{
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--border);
    background-color: var(--bg-secondary);
}}

/* ----------------------------------------------------------------------------
   Workspace (HTMX target area)
   ---------------------------------------------------------------------------- */
#workspace {{
    min-height: calc(100vh - 4rem);
}}

#workspace.htmx-swapping {{
    opacity: 0.5;
    transition: opacity var(--transition-fast);
}}

#workspace.htmx-settling {{
    opacity: 1;
    transition: opacity var(--transition-fast);
}}
</style>"""
```

---

## PHASE 2: CORE FRAMEWORK

### Step 2.1: Create core/__init__.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/core/__init__.py`

```python
"""
Core framework for FastHTML Workbench.

Exports:
- PluginRegistry: Dynamic module loader
- Config: Application configuration
"""

from .loader import PluginRegistry, PluginInfo
from .config import Config

__all__ = ["PluginRegistry", "PluginInfo", "Config"]
```

### Step 2.2: Create core/config.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/core/config.py`

```python
"""
Application configuration.

Loads settings from environment variables with sensible defaults.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class Config:
    """Application configuration loaded from environment."""

    # App identity
    APP_NAME: str = os.getenv("APP_NAME", "Legal Workbench")
    APP_VERSION: str = os.getenv("APP_VERSION", "3.0.0")

    # Server
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    PORT: int = int(os.getenv("PORT", "5001"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    MODULES_DIR: Path = BASE_DIR / "modules"
    STATIC_DIR: Path = BASE_DIR / "static"

    # Theme
    DEFAULT_THEME: str = os.getenv("DEFAULT_THEME", "shared")

    # Backend services
    STJ_API_URL: str = os.getenv("STJ_API_URL", "http://localhost:8000")

    @classmethod
    def validate(cls) -> "Config":
        """Validate configuration and return instance."""
        config = cls()

        # Ensure required directories exist
        config.MODULES_DIR.mkdir(parents=True, exist_ok=True)
        config.STATIC_DIR.mkdir(parents=True, exist_ok=True)

        return config


# Global config instance
config = Config.validate()
```

### Step 2.3: Create core/loader.py (Plugin Registry)

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/core/loader.py`

```python
"""
Dynamic Plugin Loader for FastHTML Workbench.

Scans the modules/ directory and loads valid plugins at runtime.
Each plugin must export:
- app: FastHTML application instance
- meta: dict with name, icon, description, theme_id (optional)

Usage:
    registry = PluginRegistry()
    registry.discover()

    for plugin in registry.plugins:
        main_app.mount(f"/m/{plugin.id}", plugin.app)
"""

import importlib
import importlib.util
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from .config import config

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """
    Information about a loaded plugin.

    Attributes:
        id: Unique identifier (directory name)
        name: Display name
        icon: Emoji or icon character
        description: Short description
        theme_id: Theme to use (defaults to plugin id)
        app: FastHTML application instance
        mount_path: URL path where plugin is mounted
    """
    id: str
    name: str
    icon: str
    description: str
    theme_id: str
    app: Any  # FastHTML app
    mount_path: str = field(init=False)

    def __post_init__(self):
        self.mount_path = f"/m/{self.id}"


class PluginRegistry:
    """
    Registry for dynamically loaded plugins.

    Scans the modules/ directory for valid plugin packages and
    loads them into memory. Invalid plugins are logged but don't
    crash the application.
    """

    def __init__(self, modules_dir: Optional[Path] = None):
        self.modules_dir = modules_dir or config.MODULES_DIR
        self._plugins: Dict[str, PluginInfo] = {}
        self._errors: List[str] = []

    @property
    def plugins(self) -> List[PluginInfo]:
        """Get list of all loaded plugins."""
        return list(self._plugins.values())

    @property
    def errors(self) -> List[str]:
        """Get list of loading errors."""
        return self._errors.copy()

    def get(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)

    def discover(self) -> "PluginRegistry":
        """
        Discover and load all plugins from modules directory.

        Returns self for chaining.
        """
        logger.info(f"Discovering plugins in {self.modules_dir}")

        if not self.modules_dir.exists():
            logger.warning(f"Modules directory does not exist: {self.modules_dir}")
            return self

        for path in self.modules_dir.iterdir():
            # Skip non-directories and hidden/special directories
            if not path.is_dir():
                continue
            if path.name.startswith("_") or path.name.startswith("."):
                continue

            # Try to load as plugin
            self._load_plugin(path)

        logger.info(f"Loaded {len(self._plugins)} plugins, {len(self._errors)} errors")
        return self

    def _load_plugin(self, path: Path) -> None:
        """
        Load a single plugin from a directory.

        Args:
            path: Path to plugin directory
        """
        plugin_id = path.name
        init_file = path / "__init__.py"

        if not init_file.exists():
            logger.debug(f"Skipping {plugin_id}: no __init__.py")
            return

        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(
                f"modules.{plugin_id}",
                init_file
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {plugin_id}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Validate required exports
            if not hasattr(module, "app"):
                raise AttributeError(f"Plugin {plugin_id} missing 'app' export")
            if not hasattr(module, "meta"):
                raise AttributeError(f"Plugin {plugin_id} missing 'meta' export")

            meta = module.meta

            # Validate meta structure
            required_keys = {"name", "icon"}
            if not required_keys.issubset(meta.keys()):
                missing = required_keys - set(meta.keys())
                raise ValueError(f"Plugin {plugin_id} meta missing keys: {missing}")

            # Create plugin info
            plugin = PluginInfo(
                id=plugin_id,
                name=meta["name"],
                icon=meta["icon"],
                description=meta.get("description", ""),
                theme_id=meta.get("theme_id", plugin_id),
                app=module.app,
            )

            self._plugins[plugin_id] = plugin
            logger.info(f"Loaded plugin: {plugin.icon} {plugin.name} ({plugin_id})")

        except Exception as e:
            error_msg = f"Failed to load plugin {plugin_id}: {e}"
            logger.error(error_msg)
            self._errors.append(error_msg)

    def mount_all(self, main_app: Any) -> None:
        """
        Mount all plugins to a FastHTML app.

        Args:
            main_app: The main FastHTML application
        """
        for plugin in self.plugins:
            main_app.mount(plugin.mount_path, plugin.app)
            logger.info(f"Mounted {plugin.name} at {plugin.mount_path}")
```

### Step 2.4: Create core/middleware.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/core/middleware.py`

```python
"""
Middleware for theme injection and request processing.

The theme middleware adds HX-Trigger headers to module load responses,
enabling client-side theme switching without full page reloads.
"""

import json
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def create_theme_trigger(theme_id: str) -> str:
    """
    Create an HX-Trigger header value for theme switching.

    Args:
        theme_id: The theme identifier to switch to

    Returns:
        JSON string for HX-Trigger header
    """
    return json.dumps({
        "themeSwitch": {"theme": theme_id}
    })


class ThemeContext:
    """
    Context manager for tracking active theme in request scope.

    Usage in routes:
        @rt("/m/{module}/")
        def module_index(module: str):
            ThemeContext.set_active(module)
            return ModuleContent()
    """

    _active_theme: Optional[str] = None

    @classmethod
    def set_active(cls, theme_id: str) -> None:
        """Set the active theme for current request."""
        cls._active_theme = theme_id

    @classmethod
    def get_active(cls) -> Optional[str]:
        """Get the active theme for current request."""
        return cls._active_theme

    @classmethod
    def clear(cls) -> None:
        """Clear the active theme."""
        cls._active_theme = None
```

---

## PHASE 3: SHARED COMPONENTS

### Step 3.1: Create shared/__init__.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/shared/__init__.py`

```python
"""
Shared components and layouts for FastHTML Workbench.
"""

from .components import (
    outcome_badge,
    loading_spinner,
    empty_state,
    module_header,
)
from .layouts import (
    app_shell,
    sidebar,
    workspace,
)

__all__ = [
    "outcome_badge",
    "loading_spinner",
    "empty_state",
    "module_header",
    "app_shell",
    "sidebar",
    "workspace",
]
```

### Step 3.2: Create shared/components.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/shared/components.py`

```python
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
```

### Step 3.3: Create shared/layouts.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/shared/layouts.py`

```python
"""
Page layouts for FastHTML Workbench.

Provides the shell layout with sidebar navigation and workspace area.
"""

from fasthtml.common import *
from typing import List, Optional
from core.loader import PluginInfo


def sidebar_item(
    plugin: PluginInfo,
    is_active: bool = False,
) -> FT:
    """
    Render a single sidebar navigation item.

    Uses HTMX to load module content into workspace.
    """
    active_cls = " active" if is_active else ""

    return Button(
        Span(plugin.icon, cls="sidebar-icon"),
        Span(plugin.name),
        cls=f"sidebar-item{active_cls}",
        hx_get=f"{plugin.mount_path}/",
        hx_target="#workspace",
        hx_swap="innerHTML transition:true",
        hx_push_url=plugin.mount_path,
        # Trigger theme switch before content loads
        hx_on__htmx_before_request=f"preloadTheme('{plugin.theme_id}')",
    )


def sidebar(
    plugins: List[PluginInfo],
    active_id: Optional[str] = None,
    app_name: str = "Legal Workbench",
) -> FT:
    """
    Render the sidebar navigation.

    Args:
        plugins: List of loaded plugins
        active_id: Currently active plugin ID
        app_name: Application name for header

    Returns:
        Sidebar nav element
    """
    return Nav(
        # Header
        Div(
            Div(app_name, cls="sidebar-title"),
            cls="sidebar-header",
        ),
        # Navigation items
        Div(
            *[
                sidebar_item(p, is_active=(p.id == active_id))
                for p in plugins
            ],
        ),
        cls="sidebar",
    )


def workspace(
    content: Optional[FT] = None,
) -> FT:
    """
    Render the main workspace area.

    This is the HTMX target for module content.
    """
    default_content = Div(
        Div("⚖️", cls="text-6xl mb-4"),
        H2("Bem-vindo ao Legal Workbench", cls="text-xl font-semibold mb-2"),
        P(
            "Selecione uma ferramenta no menu lateral para começar.",
            cls="text-secondary",
        ),
        cls="text-center py-24",
    )

    return Main(
        content if content else default_content,
        id="workspace",
        cls="app-main",
    )


def app_shell(
    plugins: List[PluginInfo],
    content: Optional[FT] = None,
    active_id: Optional[str] = None,
    app_name: str = "Legal Workbench",
) -> FT:
    """
    Render the complete application shell.

    Args:
        plugins: List of loaded plugins
        content: Initial workspace content
        active_id: Currently active plugin ID
        app_name: Application name

    Returns:
        Complete page HTML
    """
    return Div(
        sidebar(plugins, active_id, app_name),
        workspace(content),
        cls="app-layout",
    )
```

---

## PHASE 4: STATIC ASSETS

### Step 4.1: Create static/theme-switcher.js

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/static/theme-switcher.js`

```javascript
/**
 * Theme Switcher for FastHTML Workbench
 *
 * Handles smooth theme transitions via CSS custom properties.
 * Listens for HTMX events to switch themes when modules load.
 */

// Theme definitions (accent colors per module)
const THEMES = {
    shared: {
        accent: '#f59e0b',
        accentSecondary: '#d97706',
        accentGlow: 'rgba(245, 158, 11, 0.15)',
    },
    stj: {
        accent: '#8b5cf6',
        accentSecondary: '#7c3aed',
        accentGlow: 'rgba(139, 92, 246, 0.15)',
    },
    text_extractor: {
        accent: '#d97706',
        accentSecondary: '#b45309',
        accentGlow: 'rgba(217, 119, 6, 0.15)',
    },
    doc_assembler: {
        accent: '#0ea5e9',
        accentSecondary: '#0284c7',
        accentGlow: 'rgba(14, 165, 233, 0.15)',
    },
    trello: {
        accent: '#10b981',
        accentSecondary: '#059669',
        accentGlow: 'rgba(16, 185, 129, 0.15)',
    },
};

// Current theme tracking
let currentTheme = 'shared';

/**
 * Apply a theme by updating CSS custom properties.
 * @param {string} themeId - Theme identifier
 */
function applyTheme(themeId) {
    const theme = THEMES[themeId] || THEMES.shared;
    const root = document.documentElement;

    // Update CSS variables
    root.style.setProperty('--accent', theme.accent);
    root.style.setProperty('--accent-secondary', theme.accentSecondary);
    root.style.setProperty('--accent-glow', theme.accentGlow);
    root.style.setProperty('--border-focus', theme.accent);

    currentTheme = themeId;
    console.log(`[Theme] Switched to: ${themeId}`);
}

/**
 * Preload theme before HTMX request completes.
 * Called from hx-on--htmx-before-request attribute.
 * @param {string} themeId - Theme identifier
 */
function preloadTheme(themeId) {
    // Add slight delay for visual effect
    requestAnimationFrame(() => {
        applyTheme(themeId);
    });
}

/**
 * Update sidebar active state.
 * @param {string} moduleId - Active module identifier
 */
function updateSidebarActive(moduleId) {
    // Remove active from all items
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
    });

    // Add active to matching item
    const activeItem = document.querySelector(
        `.sidebar-item[hx-get*="/m/${moduleId}/"]`
    );
    if (activeItem) {
        activeItem.classList.add('active');
    }
}

// Listen for HTMX theme switch events
document.body.addEventListener('themeSwitch', (event) => {
    const { theme } = event.detail;
    if (theme) {
        applyTheme(theme);
        updateSidebarActive(theme);
    }
});

// Listen for HTMX after-swap to handle theme from response headers
document.body.addEventListener('htmx:afterSwap', (event) => {
    // Check for theme in HX-Trigger header
    const trigger = event.detail.xhr?.getResponseHeader('HX-Trigger');
    if (trigger) {
        try {
            const parsed = JSON.parse(trigger);
            if (parsed.themeSwitch?.theme) {
                applyTheme(parsed.themeSwitch.theme);
                updateSidebarActive(parsed.themeSwitch.theme);
            }
        } catch (e) {
            // Not JSON or no theme, ignore
        }
    }
});

// Handle browser back/forward navigation
window.addEventListener('popstate', () => {
    const path = window.location.pathname;
    const match = path.match(/^\/m\/([^/]+)/);
    if (match) {
        const moduleId = match[1];
        applyTheme(moduleId);
        updateSidebarActive(moduleId);
    } else {
        applyTheme('shared');
    }
});

// Initialize theme based on current URL
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    const match = path.match(/^\/m\/([^/]+)/);
    if (match) {
        applyTheme(match[1]);
        updateSidebarActive(match[1]);
    }
});
```

---

## PHASE 5: MAIN APPLICATION

### Step 5.1: Create main.py (Shell Application)

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/main.py`

```python
"""
FastHTML Workbench - Main Application Shell

A modular legal tools platform with dynamic plugin loading
and module-specific theming.

Usage:
    python main.py

    Or with uvicorn:
    uvicorn main:app --reload --port 5001
"""

import logging
from fasthtml.common import *

from core import PluginRegistry, Config
from core.config import config
from core.middleware import create_theme_trigger
from themes import get_theme, generate_css, SHARED_THEME
from shared.layouts import app_shell

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# Plugin Discovery
# ============================================================================
registry = PluginRegistry()
registry.discover()

# Log any loading errors
for error in registry.errors:
    logger.warning(error)

# ============================================================================
# FastHTML App Setup
# ============================================================================

# Generate base CSS from shared theme
base_css = generate_css(SHARED_THEME)

# Initialize FastHTML with dependencies
app, rt = fast_app(
    debug=config.DEBUG,
    live=config.DEBUG,  # Live reload in debug mode
    hdrs=(
        # Tailwind CSS (for utility classes)
        Script(src="https://cdn.tailwindcss.com"),
        # HTMX (hypermedia interactions)
        Script(src="https://unpkg.com/htmx.org@2.0.3"),
        # HTMX SSE extension (for streaming)
        Script(src="https://unpkg.com/htmx-ext-sse@2.2.2/sse.js"),
        # Theme CSS (base styles)
        NotStr(base_css),
        # Theme switcher JS
        Script(src="/static/theme-switcher.js", defer=True),
        # Meta
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Meta(charset="utf-8"),
    ),
)

# Mount static files
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

# Mount all discovered plugins
registry.mount_all(app)

# ============================================================================
# Shell Routes
# ============================================================================

@rt("/")
def index():
    """
    Main landing page - renders the app shell with sidebar.
    """
    return Title(f"{config.APP_NAME}"), app_shell(
        plugins=registry.plugins,
        app_name=config.APP_NAME,
    )


@rt("/m/{module_id}/")
def module_redirect(module_id: str):
    """
    Handle direct module URL access.

    Returns the full shell with the module pre-loaded.
    """
    plugin = registry.get(module_id)
    if not plugin:
        return Response("Module not found", status_code=404)

    # Get the module's index content
    # Note: This assumes the module's app has a "/" route
    # We'll render the shell and let HTMX load the content
    return Title(f"{plugin.name} - {config.APP_NAME}"), app_shell(
        plugins=registry.plugins,
        active_id=module_id,
        app_name=config.APP_NAME,
    )


@rt("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "plugins": len(registry.plugins),
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found(request, exc):
    """Custom 404 page."""
    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 - Não Encontrado</title>
            <style>
                body {{
                    background: #0a0f1a;
                    color: #e2e8f0;
                    font-family: system-ui, sans-serif;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                }}
                .container {{
                    text-align: center;
                }}
                h1 {{
                    font-size: 4rem;
                    color: #f59e0b;
                    margin-bottom: 1rem;
                }}
                p {{
                    color: #94a3b8;
                    margin-bottom: 2rem;
                }}
                a {{
                    color: #f59e0b;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>404</h1>
                <p>A página que você procura não foi encontrada.</p>
                <a href="/">← Voltar ao início</a>
            </div>
        </body>
        </html>
        """,
        status_code=404,
    )


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    logger.info(f"Loaded plugins: {[p.name for p in registry.plugins]}")
    logger.info(f"Server running at http://{config.HOST}:{config.PORT}")

    serve(host=config.HOST, port=config.PORT)
```

---

## PHASE 6: EXAMPLE MODULE (STJ)

### Step 6.1: Create modules/__init__.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/modules/__init__.py`

```python
"""
Plugin modules for FastHTML Workbench.

Each subdirectory is a self-contained module that exports:
- app: FastHTML application instance
- meta: dict with name, icon, description, theme_id

Modules are auto-discovered at startup.
"""
```

### Step 6.2: Create modules/stj/__init__.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/modules/stj/__init__.py`

```python
"""
STJ Dados Abertos Module

A jurisprudence research tool for querying Brazilian Supreme Court decisions.
Uses observatory purple theme to evoke discovery and exploration.
"""

from .routes import app

# Plugin metadata (required for auto-discovery)
meta = {
    "name": "STJ Dados Abertos",
    "icon": "🔭",
    "description": "Explore a jurisprudência do Superior Tribunal de Justiça",
    "theme_id": "stj",
}

__all__ = ["app", "meta"]
```

### Step 6.3: Create modules/stj/routes.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/modules/stj/routes.py`

```python
"""
STJ Module Routes

All routes are relative to the module mount point (/m/stj/).
Returns Components (not full pages) for HTMX integration.
"""

from fasthtml.common import *
from .components import (
    stj_index,
    search_form,
    search_results,
    quick_stats,
)

# Create module-specific FastHTML app
app = FastHTML()
rt = app.route


@rt("/")
def index():
    """
    Module index page.

    Returns a Component (not full HTML) because this
    will be loaded into the shell's workspace via HTMX.
    """
    # Add HX-Trigger header for theme switch
    return stj_index(), {"HX-Trigger": '{"themeSwitch": {"theme": "stj"}}'}


@rt("/search")
def search(
    termo: str = "",
    orgao: str = "",
    dias: int = 365,
):
    """
    Execute search and return results.
    """
    # In real implementation, this would query the STJ API
    return search_results(termo, orgao, dias)


@rt("/stats")
def stats():
    """
    Return quick stats card.
    """
    return quick_stats()
```

### Step 6.4: Create modules/stj/components.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/modules/stj/components.py`

```python
"""
STJ Module Components

UI components specific to the STJ jurisprudence search module.
"""

from fasthtml.common import *
from shared.components import module_header, card, outcome_badge, empty_state


def stj_index() -> FT:
    """
    Main module index component.
    """
    return Div(
        module_header(
            icon="🔭",
            name="STJ Dados Abertos",
            tagline="Explore a jurisprudência do Superior Tribunal de Justiça",
        ),
        Div(
            quick_stats(),
            cls="mb-6",
        ),
        Div(
            search_form(),
            Div(
                id="results-container",
                cls="mt-6",
            ),
            cls="grid-2",
        ),
    )


def quick_stats() -> FT:
    """
    Quick statistics card.
    """
    # Mock data - would come from API
    stats = {
        "total": "15,847",
        "mes": "342",
        "atualizado": "14/12/2024",
    }

    return Div(
        Div(
            Div("Total de Acórdãos", cls="text-xs text-muted mb-1"),
            Div(stats["total"], cls="text-2xl font-bold"),
            cls="text-center",
        ),
        Div(
            Div("Últimos 30 dias", cls="text-xs text-muted mb-1"),
            Div(stats["mes"], cls="text-2xl font-bold"),
            cls="text-center",
        ),
        Div(
            Div("Última Atualização", cls="text-xs text-muted mb-1"),
            Div(stats["atualizado"], cls="text-sm"),
            cls="text-center",
        ),
        cls="grid grid-cols-3 gap-4 p-4 bg-secondary rounded-lg border border-default",
        style="background-color: var(--bg-secondary); border-color: var(--border);",
    )


def search_form() -> FT:
    """
    Search form with filters.
    """
    # Legal domains
    domains = [
        ("", "Todas as áreas"),
        ("civil", "Direito Civil"),
        ("penal", "Direito Penal"),
        ("tributario", "Direito Tributário"),
        ("administrativo", "Direito Administrativo"),
        ("trabalho", "Direito do Trabalho"),
    ]

    return card(
        "Buscar Jurisprudência",
        Form(
            # Search term
            Div(
                Label("Termo de busca", cls="block text-sm font-medium mb-2"),
                Input(
                    name="termo",
                    type="text",
                    placeholder="Ex: dano moral, responsabilidade civil...",
                    cls="input-field",
                ),
                cls="mb-4",
            ),
            # Domain filter
            Div(
                Label("Área do Direito", cls="block text-sm font-medium mb-2"),
                Select(
                    *[Option(label, value=value) for value, label in domains],
                    name="orgao",
                    cls="input-field",
                ),
                cls="mb-4",
            ),
            # Period filter
            Div(
                Label("Período", cls="block text-sm font-medium mb-2"),
                Select(
                    Option("Último ano", value="365"),
                    Option("Últimos 6 meses", value="180"),
                    Option("Últimos 30 dias", value="30"),
                    Option("Todo o período", value="9999"),
                    name="dias",
                    cls="input-field",
                ),
                cls="mb-4",
            ),
            # Submit button
            Button(
                Span("Buscar", cls="mr-2"),
                Span(cls="loading htmx-indicator"),
                type="submit",
                cls="btn btn-primary w-full",
            ),
            hx_get="/m/stj/search",
            hx_target="#results-container",
            hx_indicator=".htmx-indicator",
        ),
    )


def search_results(termo: str, orgao: str, dias: int) -> FT:
    """
    Search results display.
    """
    if not termo:
        return empty_state(
            icon="🔍",
            title="Digite um termo de busca",
            message="Use o formulário ao lado para pesquisar jurisprudência.",
        )

    # Mock results - would come from API
    results = [
        {
            "processo": "REsp 1.234.567/SP",
            "relator": "Min. João Silva",
            "turma": "3ª Turma",
            "data": "12/12/2024",
            "ementa": "CIVIL. RESPONSABILIDADE CIVIL. DANO MORAL. Comprovada a conduta ilícita...",
            "resultado": "PROVIDO",
        },
        {
            "processo": "REsp 9.876.543/RJ",
            "relator": "Min. Maria Santos",
            "turma": "4ª Turma",
            "data": "10/12/2024",
            "ementa": "CIVIL. CONTRATOS. RESCISÃO CONTRATUAL. Ausência de justa causa...",
            "resultado": "DESPROVIDO",
        },
        {
            "processo": "AgInt 5.555.555/MG",
            "relator": "Min. Pedro Costa",
            "turma": "2ª Turma",
            "data": "08/12/2024",
            "ementa": "TRIBUTÁRIO. ICMS. BASE DE CÁLCULO. Inclusão de valores...",
            "resultado": "PARCIAL",
        },
    ]

    return Div(
        # Results header
        Div(
            Span(f"{len(results)} resultados", cls="text-sm text-muted"),
            Span(f" para '{termo}'", cls="text-sm"),
            cls="mb-4",
        ),
        # Results table
        Table(
            Thead(
                Tr(
                    Th("Processo"),
                    Th("Resultado"),
                    Th("Relator/Turma"),
                    Th("Ementa"),
                ),
            ),
            Tbody(
                *[
                    Tr(
                        Td(
                            Div(r["processo"], cls="font-mono text-sm"),
                            Div(r["data"], cls="text-xs text-muted"),
                        ),
                        Td(outcome_badge(r["resultado"])),
                        Td(
                            Div(r["relator"], cls="text-sm"),
                            Div(r["turma"], cls="text-xs text-muted"),
                        ),
                        Td(
                            P(r["ementa"][:150] + "...", cls="text-sm"),
                        ),
                    )
                    for r in results
                ],
            ),
            cls="results-table",
        ),
    )
```

---

## PHASE 7: MODULE TEMPLATE

### Step 7.1: Create modules/_template/__init__.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/modules/_template/__init__.py`

```python
"""
Module Template

Copy this directory to create a new module.

Required exports:
- app: FastHTML application instance
- meta: dict with module metadata

Steps to create a new module:
1. Copy this directory: cp -r _template my_module
2. Update meta dict with your module info
3. Implement routes in routes.py
4. Add components in components.py
5. Restart the server

The module will be auto-discovered and mounted at /m/my_module/
"""

from .routes import app

# UPDATE THIS with your module info
meta = {
    "name": "My Module",                    # Display name
    "icon": "📦",                           # Emoji icon
    "description": "Description here",      # Short description
    "theme_id": "shared",                   # Theme ID (or your custom theme)
}

__all__ = ["app", "meta"]
```

### Step 7.2: Create modules/_template/routes.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/modules/_template/routes.py`

```python
"""
Module Routes Template

Define your module's routes here.
All routes are relative to the module mount point.
"""

from fasthtml.common import *
from .components import module_index

app = FastHTML()
rt = app.route


@rt("/")
def index():
    """Module index - returns Component for HTMX."""
    return module_index()


# Add more routes as needed:
# @rt("/action")
# def action():
#     return ActionResult()
```

### Step 7.3: Create modules/_template/components.py

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/modules/_template/components.py`

```python
"""
Module Components Template

Define your module's UI components here.
"""

from fasthtml.common import *
from shared.components import module_header, card


def module_index() -> FT:
    """Main module index component."""
    return Div(
        module_header(
            icon="📦",
            name="My Module",
            tagline="Module description here",
        ),
        card(
            "Getting Started",
            P("Edit components.py to customize this module."),
            P("Edit routes.py to add functionality."),
        ),
    )
```

---

## PHASE 8: README

### Step 8.1: Create README.md

**File:** `/home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench/README.md`

```markdown
# FastHTML Workbench

A modular legal tools platform built with FastHTML, featuring dynamic plugin loading and module-specific theming.

## Features

- **Dynamic Plugin System**: Drop modules into `modules/` and they appear automatically
- **Module-Specific Theming**: Each tool has its own color identity
- **HTMX Integration**: Smooth, SPA-like navigation without JavaScript frameworks
- **Terminal Aesthetic**: Professional dark theme with accent colors

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

Visit http://localhost:5001

## Creating a New Module

1. Copy the template:
   ```bash
   cp -r modules/_template modules/my_module
   ```

2. Edit `modules/my_module/__init__.py`:
   ```python
   meta = {
       "name": "My Module",
       "icon": "🔧",
       "description": "What it does",
       "theme_id": "shared",  # Or add custom theme
   }
   ```

3. Implement routes in `routes.py`
4. Add components in `components.py`
5. Restart the server

Your module will appear at `/m/my_module/`

## Adding a Custom Theme

1. Edit `themes/modules.py`:
   ```python
   MY_MODULE_THEME = BaseTheme(
       id="my_module",
       name="My Module",
       icon="🔧",
       accent_primary="#your_color",
       # ...
   )

   THEMES["my_module"] = MY_MODULE_THEME
   ```

2. Update `static/theme-switcher.js` with the new colors
3. Set `theme_id` in your module's meta dict

## Project Structure

```
fasthtml-workbench/
├── main.py              # Entry point
├── core/                # Framework
│   ├── loader.py        # Plugin discovery
│   └── config.py        # Configuration
├── themes/              # Theme system
│   ├── base.py          # Base theme
│   ├── modules.py       # Module themes
│   └── css_generator.py # CSS generation
├── shared/              # Shared components
├── modules/             # Plugin modules
│   ├── stj/             # Example module
│   └── _template/       # Module template
└── static/              # Static assets
```

## Module Protocol

Each module must export:
- `app`: FastHTML application instance
- `meta`: Dictionary with:
  - `name` (required): Display name
  - `icon` (required): Emoji icon
  - `description`: Short description
  - `theme_id`: Theme to use (defaults to module id)

## License

MIT
```

---

## VERIFICATION CHECKLIST

After implementation, verify:

- [ ] `python main.py` starts without errors
- [ ] http://localhost:5001 shows the shell with sidebar
- [ ] Clicking STJ module loads content via HTMX
- [ ] Theme switches to purple when STJ loads
- [ ] Browser back/forward maintains theme state
- [ ] Creating new module from template works
- [ ] `/health` endpoint returns JSON status

---

## EXECUTION COMMANDS

```bash
# Navigate to project
cd /home/user/Claude-Code-Projetos/legal-workbench/fasthtml-workbench

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p static modules

# Run the application
python main.py
```

---

**END OF EXECUTION PLAN**

This plan is complete and ready for implementation. Each file has exact content that can be copied directly. No architectural decisions remain to be made.
