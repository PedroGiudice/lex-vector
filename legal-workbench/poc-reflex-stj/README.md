# STJ Jurisprudence Lab - Reflex PoC

**Proof of Concept** for the STJ module of Legal Workbench using [Reflex](https://reflex.dev/) - a Python framework that compiles to React.

## Overview

This PoC demonstrates Reflex's reactive capabilities with a terminal-aesthetic query builder for STJ (Superior Tribunal de Justiça) jurisprudence search.

### Key Features Demonstrated

1. **Reactive State Management** - Live SQL preview updates automatically as user changes inputs
2. **Python-to-React** - No JavaScript needed, pure Python implementation
3. **Terminal Aesthetic** - Dark theme with hacker/data-driven visual language
4. **Complex UI Components** - Multi-select, dropdowns, toggles, badges, code preview
5. **Template System** - Quick-apply query templates
6. **Dynamic Filtering** - Mock results filtered based on query parameters

## Architecture

```
poc-reflex-stj/
├── .venv/                          # Virtual environment (not committed)
├── poc_reflex_stj/                 # Main app package
│   ├── __init__.py
│   └── poc_reflex_stj.py          # App logic + UI components
├── rxconfig.py                     # Reflex configuration
├── .gitignore
└── README.md
```

## Installation & Setup

### 1. Activate Virtual Environment

```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/poc-reflex-stj
source .venv/bin/activate
```

### 2. Initialize Reflex (First Run Only)

```bash
reflex init
```

This creates the `.web/` directory with the compiled React frontend.

### 3. Run the App

```bash
reflex run
```

The app will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

## How to Use

### Query Builder Interface

1. **Select Legal Domain** - Choose from Direito Civil, Penal, Tributário, or Administrativo
2. **Add Trigger Words** - Click words to toggle selection (multi-select)
3. **Toggle "Somente Acórdãos"** - Filter for acórdãos only (shows red warning badge)
4. **Watch SQL Preview** - The SQL updates **reactively** as you change inputs
5. **Use Templates** - Quick-apply common query patterns
6. **Execute Query** - See mock results with outcome badges

### Template Quick Buttons

- **Divergência Turmas** - Sets up query for divergent rulings
- **Recursos Repetitivos** - Tax law repetitive appeals template
- **Súmulas Recentes** - Recent legal summaries search

### Live SQL Preview

The **key demonstration** of Reflex's reactive system. The SQL preview is a `@rx.var` computed property that:
- Updates automatically when any input changes
- Requires zero manual wiring or event handlers
- Demonstrates Reflex's declarative approach

## Color Palette (Terminal Aesthetic)

| Element | Hex | Usage |
|---------|-----|-------|
| Background | `#0a0f1a` | Main background (near-black blue) |
| Card Background | `#0f172a` | Component containers |
| Text | `#e2e8f0` | Primary text (cool gray) |
| Accent 1 | `#f59e0b` | Highlights, actions (amber/orange) |
| Accent 2 | `#dc2626` | Warnings, "Desprovido" badges (red) |
| Accent 3 | `#22c55e` | Success, "Provido" badges (green) |
| Borders | `#334155` | Component borders (slate) |

## Reflex-Specific Implementation Highlights

### State Management

```python
class STJState(rx.State):
    legal_domain: str = ""
    trigger_words: List[str] = []
    only_acordaos: bool = False

    @rx.var
    def sql_preview(self) -> str:
        """Computed property - auto-updates on state changes"""
        # SQL generation logic
```

### Reactive UI Binding

```python
rx.select(
    STJState.domains,
    value=STJState.legal_domain,  # Two-way binding
    on_change=STJState.set_legal_domain,  # Auto-generated setter
)
```

### Conditional Rendering

```python
rx.cond(
    STJState.show_results,  # Condition
    result_section(),        # If true
    rx.fragment(),          # If false
)
```

## Mock Data

The PoC includes 4 sample results:
- 2x Provido (green badges)
- 1x Desprovido (red badge)
- 1x Parcial (yellow badge)

Results are filtered dynamically based on:
- Selected legal domain
- Trigger words
- Current query state

## Performance Notes

Reflex compiles to optimized React code, so:
- Initial compilation takes ~10-20 seconds
- Hot reload on code changes (in dev mode)
- Production build uses Next.js optimization

## Comparison Points (vs React Implementation)

### Advantages
✅ Pure Python - no context switching
✅ Automatic state reactivity
✅ Less boilerplate code
✅ Built-in component library
✅ Python type hints for safety

### Trade-offs
⚠️ Less control over React output
⚠️ Smaller ecosystem than React
⚠️ Additional compilation step
⚠️ Learning curve for Reflex patterns

## Next Steps (If Moving Forward with Reflex)

1. **Add Download Center module** - File upload, terminal logs, progress tracking
2. **Real SQLite integration** - Replace mock data with actual queries
3. **Advanced filters** - Date ranges, relator selection, outcome filtering
4. **Export functionality** - CSV/Excel export of results
5. **Authentication** - User sessions and saved queries
6. **Deployment** - Reflex hosting or custom deployment

## Troubleshooting

### Port Already in Use
```bash
# Kill processes on ports 3000/8000
pkill -f reflex
```

### Module Not Found
```bash
# Ensure virtual environment is activated
source .venv/bin/activate
pip install reflex
```

### Compilation Errors
```bash
# Clear Reflex cache and rebuild
rm -rf .web/
reflex init
reflex run
```

## Developer Notes

- **No Unicode Emoji** - Using text badges only (per requirements)
- **Monospace Font** - JetBrains Mono loaded via Google Fonts
- **Responsive** - Max-width 1200px, centered layout
- **Accessibility** - High contrast colors, clear visual hierarchy

## Resources

- [Reflex Documentation](https://reflex.dev/docs/)
- [Reflex GitHub](https://github.com/reflex-dev/reflex)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

**Built with Reflex 0.8.22** | **Python 3.11+** | **MIT License**
