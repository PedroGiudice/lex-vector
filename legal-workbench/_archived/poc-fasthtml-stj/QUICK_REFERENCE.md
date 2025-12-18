# Design System Quick Reference

**Copy-paste ready code snippets for common UI patterns**

---

## Color Palette

### Backgrounds
```python
'#0B0F19'  # bg_primary - Main background
'#141825'  # bg_secondary - Cards
'#1A1F2E'  # bg_tertiary - Hover states
'#1E2433'  # bg_elevated - Modals
```

### Text
```python
'#F8FAFC'  # text_primary - High contrast
'#CBD5E1'  # text_secondary - Body text
'#94A3B8'  # text_tertiary - Muted
'#64748B'  # text_disabled - Disabled
```

### Accents
```python
'#3B82F6'  # accent_primary - Trust blue
'#F59E0B'  # accent_secondary - Amber
'#10B981'  # success - Green (PROVIDO)
'#EF4444'  # error - Red (DESPROVIDO)
```

---

## Common Components

### Basic Card
```python
Div(
    Div("Card Title", cls="card-header"),
    P("Card content goes here", cls="text-secondary"),
    cls="card"
)
```

### Button (Primary)
```python
Button(
    "Click Me",
    cls="btn btn-primary",
    hx_get="/endpoint"
)
```

### Button (Secondary)
```python
Button(
    "Cancel",
    cls="btn btn-secondary"
)
```

### Input Field
```python
Input(
    type="text",
    placeholder="Enter text...",
    cls="input-field"
)
```

### Select Dropdown
```python
Select(
    Option("Choose...", value=""),
    Option("Option 1", value="1"),
    Option("Option 2", value="2"),
    cls="input-field"
)
```

### Status Badge (PROVIDO)
```python
Span("PROVIDO", cls="badge badge-provido")
```

### Status Badge (DESPROVIDO)
```python
Span("DESPROVIDO", cls="badge badge-desprovido")
```

### Status Badge (PARCIAL)
```python
Span("PARCIAL", cls="badge badge-parcial")
```

### Warning Badge
```python
Span("WARNING", cls="badge badge-warning")
```

### Interactive Pill (Unselected)
```python
Label(
    Input(type="checkbox", name="filter", value="option", cls="hidden"),
    Span("Option", cls="pill"),
    cls="cursor-pointer"
)
```

### Interactive Pill (Selected)
```python
Label(
    Input(type="checkbox", name="filter", value="option", checked=True, cls="hidden"),
    Span("Option", cls="pill selected"),
    cls="cursor-pointer"
)
```

### Toggle Switch
```python
Label(
    Input(type="checkbox", name="toggle", id="my-toggle"),
    Span(cls="toggle-slider"),
    cls="toggle-switch"
)
```

### Loading Spinner
```python
Span(cls="loading")
```

### Loading Spinner (Large)
```python
Span(cls="loading loading-lg")
```

### Loading Dots
```python
Div(
    Span(), Span(), Span(),
    cls="loading-dots"
)
```

### Progress Bar
```python
Div(
    Div(style="width: 75%", cls="progress-bar-fill"),
    cls="progress-bar"
)
```

### SQL Preview
```python
Pre(
    "SELECT * FROM decisoes WHERE tipo = 'ACORDAO'",
    cls="sql-preview"
)
```

### Terminal Output
```python
Div(
    Div("Processing documents...", cls="terminal-line"),
    Div("Extracting text...", cls="terminal-line"),
    Div("Complete!", cls="terminal-line"),
    cls="terminal"
)
```

### Terminal with Error
```python
Div(
    Div("Starting process...", cls="terminal-line"),
    Div("ERROR: File not found", cls="terminal-line terminal-error"),
    cls="terminal"
)
```

### Table
```python
Table(
    Thead(
        Tr(
            Th("Processo"),
            Th("Data"),
            Th("Status")
        )
    ),
    Tbody(
        Tr(
            Td("REsp 123456"),
            Td("2024-01-15"),
            Td(Span("PROVIDO", cls="badge badge-provido"))
        )
    ),
    cls="results-table"
)
```

### Toast Notification (Success)
```python
Div(
    "Operation completed successfully!",
    cls="toast toast-success"
)
```

### Toast Notification (Error)
```python
Div(
    "An error occurred. Please try again.",
    cls="toast toast-error"
)
```

### Empty State
```python
Div(
    Div("📋", cls="empty-state-icon"),
    Div("No Results Found", cls="empty-state-title"),
    Div("Try adjusting your search filters", cls="empty-state-description"),
    cls="empty-state"
)
```

---

## Layout Patterns

### Container
```python
Div(
    # Content here
    cls="container"
)
```

### Two-Column Grid
```python
Div(
    Div("Column 1", cls="card"),
    Div("Column 2", cls="card"),
    cls="grid-2"
)
```

### Three-Column Grid
```python
Div(
    Div("Column 1", cls="card"),
    Div("Column 2", cls="card"),
    Div("Column 3", cls="card"),
    cls="grid-3"
)
```

### App Header
```python
Div(
    H1("STJ Jurisprudência", cls="app-title"),
    P("Sistema de Busca de Decisões", cls="app-subtitle"),
    cls="app-header"
)
```

---

## Typography

### Gradient Text (Blue)
```python
H1("Premium Title", cls="text-gradient-blue")
```

### Gradient Text (Amber)
```python
H2("Important Note", cls="text-gradient-amber")
```

### Monospace Text
```python
Code("SELECT * FROM decisoes", cls="font-mono")
```

---

## Utility Classes

### Flexbox
```python
cls="flex items-center justify-between gap-4"
```

### Spacing
```python
cls="mb-4"  # margin-bottom: 1rem
cls="mt-6"  # margin-top: 1.5rem
cls="p-4"   # padding: 1rem
```

### Text Sizes
```python
cls="text-xs"    # 12px
cls="text-sm"    # 14px
cls="text-base"  # 16px
cls="text-lg"    # 18px
```

### Font Weights
```python
cls="font-normal"    # 400
cls="font-medium"    # 500
cls="font-semibold"  # 600
cls="font-bold"      # 700
```

### Border Radius
```python
cls="rounded"      # 6px
cls="rounded-lg"   # 8px
cls="rounded-xl"   # 12px
cls="rounded-full" # 9999px
```

### Width/Height
```python
cls="w-full"  # width: 100%
cls="h-full"  # height: 100%
```

---

## HTMX Patterns

### Button with Loading
```python
Button(
    Span("Search", id="search-text"),
    Span(cls="loading htmx-indicator ml-2"),
    cls="btn btn-primary",
    hx_get="/search",
    hx_target="#results",
    hx_indicator=".htmx-indicator"
)
```

### Auto-updating Content
```python
Div(
    "Initial content",
    id="live-updates",
    hx_get="/updates",
    hx_trigger="every 5s",
    hx_swap="innerHTML"
)
```

### Form with Validation
```python
Form(
    Input(cls="input-field", name="query"),
    Button("Submit", cls="btn btn-primary"),
    hx_post="/validate",
    hx_target="#errors"
)
```

---

## Animation Classes

### Fade In
```python
cls="htmx-settling"  # Auto-applied by HTMX
```

### Skeleton Loading
```python
Div(cls="skeleton-row")
```

### Pulse Animation (for badges)
```python
cls="badge badge-warning"  # Has built-in pulse
```

---

## Accessibility

### Screen Reader Only
```python
Span("Loading results...", cls="sr-only")
```

### Focus Visible
```python
# Automatic on all interactive elements
# Custom: add focus:outline-blue-500
```

---

## Color-Coded Examples

### Legal Decision Badges

**PROVIDO (Green)**
```python
Span("PROVIDO", cls="badge badge-provido")
```

**DESPROVIDO (Red)**
```python
Span("DESPROVIDO", cls="badge badge-desprovido")
```

**PARCIALMENTE PROVIDO (Amber)**
```python
Span("PARCIAL", cls="badge badge-parcial")
```

---

## Full Page Example

```python
from fasthtml.common import *
from styles import PREMIUM_STYLE

def home_page():
    return Div(
        # Header
        Div(
            H1("STJ Jurisprudência", cls="app-title"),
            P("Sistema de Busca de Decisões", cls="app-subtitle"),
            cls="app-header"
        ),

        # Main Content
        Div(
            # Search Card
            Div(
                Div("Busca Avançada", cls="card-header"),

                # Input
                Div(
                    Label("Termo de Busca", cls="text-sm font-semibold mb-2 text-blue-400"),
                    Input(
                        type="text",
                        placeholder="Digite palavras-chave...",
                        cls="input-field"
                    ),
                    cls="mb-4"
                ),

                # Button
                Button(
                    "Executar Busca",
                    cls="btn btn-primary w-full",
                    hx_get="/search",
                    hx_target="#results"
                ),

                cls="card"
            ),

            # Results Card
            Div(
                Div("Resultados", cls="card-header"),
                Div(id="results",
                    Div(
                        Div("📋", cls="empty-state-icon"),
                        Div("Nenhum resultado ainda", cls="empty-state-title"),
                        Div("Execute uma busca para ver os resultados", cls="empty-state-description"),
                        cls="empty-state"
                    )
                ),
                cls="card"
            ),

            cls="container"
        )
    )
```

---

## CSS Custom Properties (for theming)

To customize colors programmatically:

```python
Style("""
    :root {
        --color-primary: #3B82F6;
        --color-secondary: #F59E0B;
        --color-success: #10B981;
        --color-error: #EF4444;
    }
""")
```

---

**Quick Tip:** Most classes are composable. Combine utility classes with component classes:

```python
Button(
    "Action",
    cls="btn btn-primary w-full mt-4"
    #   ↑        ↑       ↑      ↑
    #   base   variant  width  margin
)
```

---

**File Location:** `/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-workbench/poc-fasthtml-stj/styles.py`
