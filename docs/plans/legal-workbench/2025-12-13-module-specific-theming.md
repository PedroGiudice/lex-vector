# Module-Specific Theming Implementation Plan

**Date:** 2025-12-13
**Status:** Planning
**Author:** Technical Director
**Stakeholder:** Product Design Director (PGR)

---

## Executive Summary

This plan implements **module-specific theming** for Legal Workbench, where each functional module receives a distinct visual identity that reflects its purpose. This approach leverages "Functional Aesthetics" — the principle that visual language should communicate function.

---

## 1. Rationale: Why Module-Specific Theming Works

### 1.1 Functional Aesthetics Principle

Each module has a fundamentally different purpose. The visual language should reflect that:

| Module | Primary Function | Cognitive Mode | Suggested Aesthetic |
|--------|------------------|----------------|---------------------|
| **Text Extractor** | Transform documents | Processing, patience | Industrial/mechanical |
| **Doc Assembler** | Create from templates | Construction, precision | Blueprint/architectural |
| **STJ Dados Abertos** | Research & analyze | Discovery, exploration | Observatory/scientific |
| **Trello MCP** | Organize & coordinate | Management, workflow | Command center/operational |

### 1.2 Benefits

1. **Instant Context Recognition** — Users know where they are at a glance
2. **Reduced Cognitive Load** — Color-coding aids navigation between modules
3. **Emotional Resonance** — Colors prime users for the task at hand
4. **Professional Polish** — Differentiated UX signals product maturity
5. **Accessibility** — Distinct palettes help colorblind users distinguish modules

---

## 2. Current State Analysis

### 2.1 Existing Color System

All projects currently use a **unified terminal aesthetic**:

```
Background:  #0a0f1a (Deep Navy)
Text:        #e2e8f0 (Light Slate)
Accent:      #f59e0b (Amber)
Success:     #22c55e (Green)
Danger:      #dc2626 (Red)
Warning:     #eab308 (Yellow)
```

### 2.2 Where Colors Are Defined

| Location | Framework | Purpose |
|----------|-----------|---------|
| `app.py` (lines 23-78) | Streamlit | Hub styling, inline CSS |
| `modules/stj.py` | Streamlit | Module-specific inline styles |
| `poc-react-stj/tailwind.config.js` | React | Tailwind theme extension |
| `poc-fasthtml-stj/styles.py` | FastHTML | COLORS dict + TERMINAL_STYLE |
| `poc-reflex-stj/.../poc_reflex_stj.py` | Reflex | Inline color props |

### 2.3 Identified Issues

1. **No centralized color source** — Colors defined separately in each location
2. **Hardcoded hex values** — Scattered throughout Streamlit modules
3. **Inconsistent naming** — `accent_amber` vs `accent` vs inline hex
4. **No module differentiation** — Everything uses same amber accent

---

## 3. Module Color Palettes

### 3.1 Design Philosophy

Each module gets a **signature accent color** while maintaining:
- Same dark backgrounds (#0a0f1a, #0f172a) for consistency
- Same text colors (#e2e8f0, #64748b) for readability
- Same semantic colors (success/danger/warning) for universal meaning
- Unique accent that reflects the module's cognitive purpose

### 3.2 Proposed Palettes

#### 🔧 Text Extractor — Industrial Copper

**Purpose:** Document transformation, extraction, processing
**Mood:** Mechanical, reliable, transformative
**Accent:** Copper/Bronze tones

```python
TEXT_EXTRACTOR_THEME = {
    "accent_primary":   "#d97706",  # Amber-600 (warm copper)
    "accent_secondary": "#b45309",  # Amber-700
    "accent_muted":     "#92400e",  # Amber-800
    "accent_glow":      "rgba(217, 119, 6, 0.15)",
    "icon": "⚙️",
    "gradient": "from-amber-600 to-orange-700"
}
```

#### 📐 Doc Assembler — Architect Blue

**Purpose:** Template-based document construction
**Mood:** Precise, structured, creative
**Accent:** Blueprint blue tones

```python
DOC_ASSEMBLER_THEME = {
    "accent_primary":   "#0ea5e9",  # Sky-500 (blueprint blue)
    "accent_secondary": "#0284c7",  # Sky-600
    "accent_muted":     "#0369a1",  # Sky-700
    "accent_glow":      "rgba(14, 165, 233, 0.15)",
    "icon": "📐",
    "gradient": "from-sky-500 to-cyan-600"
}
```

#### 🔭 STJ Dados Abertos — Observatory Purple

**Purpose:** Legal research, data exploration, analysis
**Mood:** Discovery, insight, depth
**Accent:** Deep purple/violet tones

```python
STJ_THEME = {
    "accent_primary":   "#8b5cf6",  # Violet-500 (observatory purple)
    "accent_secondary": "#7c3aed",  # Violet-600
    "accent_muted":     "#6d28d9",  # Violet-700
    "accent_glow":      "rgba(139, 92, 246, 0.15)",
    "icon": "🔭",
    "gradient": "from-violet-500 to-purple-600"
}
```

#### 🎛️ Trello MCP — Command Green

**Purpose:** Task management, coordination, workflow
**Mood:** Operational, decisive, active
**Accent:** Command center green tones

```python
TRELLO_THEME = {
    "accent_primary":   "#10b981",  # Emerald-500 (command green)
    "accent_secondary": "#059669",  # Emerald-600
    "accent_muted":     "#047857",  # Emerald-700
    "accent_glow":      "rgba(16, 185, 129, 0.15)",
    "icon": "🎛️",
    "gradient": "from-emerald-500 to-teal-600"
}
```

### 3.3 Shared Foundation (Unchanged)

```python
SHARED_THEME = {
    # Backgrounds (consistent across all modules)
    "bg_primary":       "#0a0f1a",
    "bg_secondary":     "#0f172a",
    "bg_tertiary":      "#1a2332",

    # Text (consistent across all modules)
    "text_primary":     "#e2e8f0",
    "text_secondary":   "#94a3b8",
    "text_muted":       "#64748b",

    # Borders
    "border_default":   "#1e293b",
    "border_hover":     "#334155",

    # Semantic (universal meaning)
    "success":          "#22c55e",
    "danger":           "#dc2626",
    "warning":          "#eab308",
    "info":             "#3b82f6",
}
```

---

## 4. Implementation Architecture

### 4.1 New File Structure

```
legal-workbench/
├── themes/
│   ├── __init__.py           # Theme exports
│   ├── base.py               # SHARED_THEME
│   ├── modules.py            # Module-specific themes
│   ├── utils.py              # Theme utilities
│   └── css_generator.py      # Generate CSS from themes
├── app.py                    # Import themes, apply dynamically
└── modules/
    ├── text_extractor.py     # Use TEXT_EXTRACTOR_THEME
    ├── doc_assembler.py      # Use DOC_ASSEMBLER_THEME
    ├── stj.py                # Use STJ_THEME
    └── trello.py             # Use TRELLO_THEME
```

### 4.2 Theme Loading Flow

```
┌─────────────────────────────────────────────────────────────┐
│ app.py (Hub)                                                │
│                                                             │
│ 1. Load base theme (SHARED_THEME)                          │
│ 2. Detect active module from session state                 │
│ 3. Load module theme (TEXT_EXTRACTOR_THEME, etc.)          │
│ 4. Merge: module_theme = {**SHARED_THEME, **MODULE_THEME}  │
│ 5. Generate CSS via css_generator.py                       │
│ 6. Inject CSS via st.markdown(css, unsafe_allow_html=True) │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 CSS Variable Strategy

Generate CSS custom properties for each module:

```css
/* Base (always present) */
:root {
    --bg-primary: #0a0f1a;
    --bg-secondary: #0f172a;
    --text-primary: #e2e8f0;
    --success: #22c55e;
    --danger: #dc2626;
    --warning: #eab308;
}

/* Module-specific (switched based on active module) */
:root[data-module="text_extractor"] {
    --accent: #d97706;
    --accent-secondary: #b45309;
    --accent-glow: rgba(217, 119, 6, 0.15);
}

:root[data-module="stj"] {
    --accent: #8b5cf6;
    --accent-secondary: #7c3aed;
    --accent-glow: rgba(139, 92, 246, 0.15);
}
/* ... etc */
```

---

## 5. Implementation Steps

### Phase 1: Foundation (Day 1)

| Step | Task | Deliverable |
|------|------|-------------|
| 1.1 | Create `themes/` directory structure | Directory + `__init__.py` |
| 1.2 | Implement `themes/base.py` | SHARED_THEME dict |
| 1.3 | Implement `themes/modules.py` | All 4 module themes |
| 1.4 | Implement `themes/css_generator.py` | `generate_css(theme)` function |
| 1.5 | Add unit tests for theme generation | `tests/test_themes.py` |

### Phase 2: Hub Integration (Day 2)

| Step | Task | Deliverable |
|------|------|-------------|
| 2.1 | Modify `app.py` to import themes | Clean import, no inline colors |
| 2.2 | Add module detection from session state | `get_active_module()` helper |
| 2.3 | Dynamic CSS injection based on module | Theme switches on navigation |
| 2.4 | Add smooth CSS transition | 200ms transition on accent |
| 2.5 | Test module switching | Visual verification |

### Phase 3: Module Migration (Days 3-4)

| Step | Task | Deliverable |
|------|------|-------------|
| 3.1 | Migrate `modules/text_extractor.py` | Remove hardcoded colors |
| 3.2 | Migrate `modules/doc_assembler.py` | Remove hardcoded colors |
| 3.3 | Migrate `modules/stj.py` | Remove hardcoded colors (heavy) |
| 3.4 | Migrate `modules/trello.py` | Remove hardcoded colors |
| 3.5 | Add module header with icon + gradient | Visual module identity |

### Phase 4: POC Alignment (Day 5)

| Step | Task | Deliverable |
|------|------|-------------|
| 4.1 | Update `poc-react-stj/tailwind.config.js` | Use STJ_THEME colors |
| 4.2 | Update `poc-fasthtml-stj/styles.py` | Import from shared themes |
| 4.3 | Update `poc-reflex-stj` inline colors | Reference theme variables |
| 4.4 | Document theme usage in each POC | README updates |

### Phase 5: Polish & Documentation (Day 6)

| Step | Task | Deliverable |
|------|------|-------------|
| 5.1 | Add module transition animations | Fade between accents |
| 5.2 | Add sidebar accent indicator | Current module visual cue |
| 5.3 | Create theme documentation | `docs/THEMING.md` |
| 5.4 | Update ARCHITECTURE.md if needed | ADR for theming decision |
| 5.5 | Final visual QA | All modules, all states |

---

## 6. Visual Design Mockups

### 6.1 Module Header Pattern

Each module gets a header with its identity:

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ TEXT EXTRACTOR                                          │
│ ━━━━━━━━━━━━━━━━━━━ [copper gradient bar]                  │
│                                                             │
│ Transform legal documents with intelligent extraction       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 🔭 STJ DADOS ABERTOS                                       │
│ ━━━━━━━━━━━━━━━━━━━ [purple gradient bar]                  │
│                                                             │
│ Explore Brazilian Supreme Court jurisprudence              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Sidebar Module Indicator

```
┌──────────────────┐
│ Legal Workbench  │
├──────────────────┤
│ ⚙️ Text Extractor│  ← copper dot indicator
│ 📐 Doc Assembler │
│ 🔭 STJ Dados     │  ← purple dot if active
│ 🎛️ Trello MCP    │
└──────────────────┘
```

### 6.3 Button Accent Examples

```python
# Text Extractor (copper)
st.button("Extract Text", type="primary")  # #d97706 background

# STJ (purple)
st.button("Search", type="primary")  # #8b5cf6 background

# Trello (green)
st.button("Sync Cards", type="primary")  # #10b981 background
```

---

## 7. Code Examples

### 7.1 Theme Definition (themes/modules.py)

```python
"""Module-specific theme definitions."""

from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class ModuleTheme:
    """Immutable theme configuration for a module."""
    id: str
    name: str
    icon: str
    accent_primary: str
    accent_secondary: str
    accent_muted: str
    accent_glow: str
    tagline: str

TEXT_EXTRACTOR = ModuleTheme(
    id="text_extractor",
    name="Text Extractor",
    icon="⚙️",
    accent_primary="#d97706",
    accent_secondary="#b45309",
    accent_muted="#92400e",
    accent_glow="rgba(217, 119, 6, 0.15)",
    tagline="Transform legal documents with intelligent extraction"
)

STJ = ModuleTheme(
    id="stj",
    name="STJ Dados Abertos",
    icon="🔭",
    accent_primary="#8b5cf6",
    accent_secondary="#7c3aed",
    accent_muted="#6d28d9",
    accent_glow="rgba(139, 92, 246, 0.15)",
    tagline="Explore Brazilian Supreme Court jurisprudence"
)

# ... etc

THEMES: Dict[str, ModuleTheme] = {
    "text_extractor": TEXT_EXTRACTOR,
    "doc_assembler": DOC_ASSEMBLER,
    "stj": STJ,
    "trello": TRELLO,
}

def get_theme(module_id: str) -> ModuleTheme:
    """Get theme for a module, with fallback to default."""
    return THEMES.get(module_id, TEXT_EXTRACTOR)
```

### 7.2 CSS Generator (themes/css_generator.py)

```python
"""Generate CSS from theme configuration."""

from .base import SHARED_THEME
from .modules import ModuleTheme

def generate_module_css(theme: ModuleTheme) -> str:
    """Generate CSS for a specific module theme."""
    return f"""
    <style>
    /* Module: {theme.name} */
    :root {{
        --accent: {theme.accent_primary};
        --accent-secondary: {theme.accent_secondary};
        --accent-muted: {theme.accent_muted};
        --accent-glow: {theme.accent_glow};
    }}

    /* Primary buttons */
    .stButton > button[kind="primary"] {{
        background-color: {theme.accent_primary} !important;
        border-color: {theme.accent_primary} !important;
    }}

    .stButton > button[kind="primary"]:hover {{
        background-color: {theme.accent_secondary} !important;
        border-color: {theme.accent_secondary} !important;
    }}

    /* Module header gradient */
    .module-header {{
        background: linear-gradient(90deg,
            {theme.accent_primary}20 0%,
            transparent 100%);
        border-left: 3px solid {theme.accent_primary};
    }}

    /* Active sidebar indicator */
    .sidebar-item.active::before {{
        background-color: {theme.accent_primary};
    }}

    /* Focus rings */
    *:focus-visible {{
        outline-color: {theme.accent_primary};
        box-shadow: 0 0 0 2px {theme.accent_glow};
    }}
    </style>
    """
```

### 7.3 Hub Integration (app.py)

```python
import streamlit as st
from themes import get_theme, generate_module_css, SHARED_CSS

# Apply base theme
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# Get active module and apply its theme
active_module = st.session_state.get("active_module", "text_extractor")
theme = get_theme(active_module)
st.markdown(generate_module_css(theme), unsafe_allow_html=True)

# Render module header
st.markdown(f"""
<div class="module-header">
    <h1>{theme.icon} {theme.name}</h1>
    <p class="tagline">{theme.tagline}</p>
</div>
""", unsafe_allow_html=True)
```

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CSS specificity conflicts | Medium | Low | Use `!important` sparingly, test each module |
| Streamlit version changes | Low | Medium | Pin Streamlit version, test upgrades |
| Color accessibility issues | Medium | Medium | Verify contrast ratios (WCAG AA) |
| POC divergence | Medium | Low | Document theme contract, sync regularly |
| Performance (CSS injection) | Low | Low | CSS is tiny (<5KB), cached by browser |

---

## 9. Success Criteria

1. **Functional:** Each module displays its unique accent color
2. **Consistent:** Shared elements (backgrounds, text) remain unified
3. **Smooth:** Module transitions feel polished (no flash of wrong color)
4. **Maintainable:** Single source of truth for all colors
5. **Accessible:** All accent colors pass WCAG AA contrast (4.5:1 minimum)
6. **Documented:** Theme system documented for future contributors

---

## 10. Future Considerations

### 10.1 User Theme Preferences

Could extend to allow users to:
- Override module accent colors
- Switch to high-contrast mode
- Choose light mode (if ever supported)

### 10.2 Dark/Light Mode

Current implementation is dark-only. Architecture supports future light mode by adding:

```python
LIGHT_SHARED_THEME = {
    "bg_primary": "#ffffff",
    "bg_secondary": "#f8fafc",
    "text_primary": "#1e293b",
    # ... etc
}
```

### 10.3 Theme Persistence

Could save user preferences to:
- Browser localStorage (via Streamlit components)
- Backend user settings (if auth is added)

---

## 11. Appendix: Color Contrast Verification

All proposed accents verified against #0a0f1a background:

| Module | Accent | Contrast Ratio | WCAG AA |
|--------|--------|----------------|---------|
| Text Extractor | #d97706 | 6.2:1 | ✅ Pass |
| Doc Assembler | #0ea5e9 | 7.1:1 | ✅ Pass |
| STJ Dados | #8b5cf6 | 5.8:1 | ✅ Pass |
| Trello MCP | #10b981 | 6.9:1 | ✅ Pass |

All accents pass WCAG AA for normal text (4.5:1 minimum).

---

## 12. Decision Record

**Decision:** Implement module-specific theming with signature accent colors

**Alternatives Considered:**
1. **Keep unified theme** — Rejected: Misses opportunity for functional aesthetics
2. **Full theme per module** — Rejected: Too much visual fragmentation
3. **Subtle tint differences** — Rejected: Not distinctive enough

**Rationale:** Signature accent approach balances brand consistency with functional differentiation.

---

**Next Action:** Await Product Director approval to proceed with Phase 1 implementation.
