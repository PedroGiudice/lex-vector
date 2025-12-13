# STJ Jurisprudence Lab - Quick Start Guide

## Installation & Run (30 seconds)

```bash
# 1. Navigate to project
cd /home/user/Claude-Code-Projetos/legal-workbench/poc-reflex-stj

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Run the app (compilation happens automatically)
reflex run
```

**That's it!** The app will be available at http://localhost:3000

## First Run

The first `reflex run` will:
1. Compile Python code to React (takes ~20-30 seconds)
2. Start backend server on port 8000
3. Start frontend dev server on port 3000
4. Open browser automatically

## What to Test

### 1. **Live SQL Preview** (Key Feature)
- Select "Direito Civil" from dropdown → SQL updates instantly
- Click "Dano Moral" button → SQL adds LIKE clause
- Toggle "Somente Acórdãos" → SQL adds type filter
- **All changes are reactive - no button press needed!**

### 2. **Template System**
- Click "Divergência Turmas" → Auto-fills query for jurisprudence divergence
- Click "Recursos Repetitivos" → Tax law template with ICMS/ISS
- Click "Súmulas Recentes" → Recent legal summaries

### 3. **Query Execution**
- Click "EXECUTAR QUERY" → See mock results
- Results show outcome badges (Provido=green, Desprovido=red, Parcial=yellow)
- Badge count updates with filtered results

### 4. **Multi-Select Triggers**
- Click multiple trigger words → They stack (OR logic in SQL)
- Click again to deselect → SQL updates immediately
- Orange badge shows count of selected triggers

## Terminal Aesthetic Features

✅ Dark background (#0a0f1a)
✅ Amber/orange accents (#f59e0b)
✅ Monospace fonts for data
✅ No unicode emoji (text badges only)
✅ Clean borders and cards
✅ Syntax-highlighted SQL preview

## Development Mode

```bash
# Run with auto-reload on code changes
reflex run --loglevel debug
```

Edit `/home/user/Claude-Code-Projetos/legal-workbench/poc-reflex-stj/poc_reflex_stj/poc_reflex_stj.py` and save - changes appear instantly in browser.

## Production Build

```bash
# Create optimized production build
reflex export

# Files will be in .web/_static/
```

## Troubleshooting

### Port Already in Use
```bash
pkill -f reflex
reflex run
```

### Clear Cache
```bash
rm -rf .web/
reflex init
reflex run
```

## Comparison Points vs React

**Demonstrated Advantages:**
1. ✅ Pure Python - single language for full stack
2. ✅ Reactive state with zero boilerplate (see `sql_preview` computed var)
3. ✅ Type safety with Python type hints
4. ✅ No build config needed (no webpack, vite, etc.)

**Trade-offs:**
1. ⚠️ Compilation step (but similar to Next.js)
2. ⚠️ Less ecosystem/libraries than React
3. ⚠️ Learning curve for Reflex patterns

## Key Code Patterns

### Reactive State
```python
@rx.var
def sql_preview(self) -> str:
    # Auto-updates when self.legal_domain or self.trigger_words change
    return generate_sql()
```

### Two-Way Binding
```python
rx.select(
    STJState.domains,
    value=STJState.legal_domain,  # Current value
    on_change=STJState.set_legal_domain,  # Setter
)
```

### Conditional Rendering
```python
rx.cond(
    STJState.show_results,  # If true
    results_section(),      # Show this
    rx.fragment(),          # Else show nothing
)
```

## Next Steps

If Reflex is chosen for Legal Workbench:
1. Add Download Center module (file upload, terminal logs)
2. Real SQLite integration
3. Advanced filtering (date ranges, relator selection)
4. CSV/Excel export
5. User authentication and saved queries

---

**Built with Reflex 0.8.22** | **Python 3.11+**
