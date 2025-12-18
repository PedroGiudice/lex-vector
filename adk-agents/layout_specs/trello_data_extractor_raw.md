# Trello Data Extractor Layout Specification

> **Aesthetic**: Raw Data Interface
> **Purpose**: Extract, view, and export Trello data for case management

## Design Philosophy

### Core Principle: Data First
- **Zero friction** between user and data
- **Copy-friendly** - every piece of data easily selectable/copiable
- **Dense information** - maximize data visibility per screen
- **Scannable** - hierarchical structure, clear labels
- **Actionable** - one-click export, batch operations

### NOT This
- No decorative elements that don't serve data clarity
- No excessive padding/whitespace
- No hidden information requiring hover/click to reveal
- No animations that slow down interaction

## Visual Style

### Inspiration
- Terminal/CLI interfaces (clarity, density)
- Spreadsheet applications (data tables, bulk selection)
- VS Code's Output panel (raw, scannable)
- Notion databases (structured, exportable)

### Color Palette

| Element | Color | Purpose |
|---------|-------|---------|
| Background | `#0d1117` | Maximum contrast for text |
| Surface | `#161b22` | Cards, panels |
| Border | `#30363d` | Subtle separation |
| Text Primary | `#e6edf3` | High readability |
| Text Secondary | `#8b949e` | Labels, metadata |
| Accent | `#58a6ff` | Links, actions |
| Success | `#3fb950` | Completed, exported |
| Warning | `#d29922` | Pending, attention |
| Data Highlight | `#1f6feb` | Selected rows/items |

### Typography

```css
/* ALL text is monospace for alignment and copy-friendliness */
--font-data: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
--font-size-data: 13px;
--font-size-label: 11px;
--font-size-heading: 14px;
--line-height: 1.4;  /* Dense but readable */
```

## Layout Structure

### Single Panel Focus
```
┌──────────────────────────────────────────────────────────┐
│ [Board ▼] [List ▼] [Filter ▼]  [Export ▼] [Copy All]    │  ← Toolbar
├──────────────────────────────────────────────────────────┤
│ ☐ | Card Name          | Labels    | Due      | Members │  ← Table Header
├──────────────────────────────────────────────────────────┤
│ ☑ | Case #1234 - Silva | Urgente   | 15/12    | PGR     │
│ ☐ | Case #5678 - Costa | Em andamento | 20/12 | LGP     │
│ ☑ | Case #9012 - Lima  | Concluído | -        | PGR     │
│   |                    |           |          |         │
│   | ... more rows ...  |           |          |         │
└──────────────────────────────────────────────────────────┘
│ Selected: 2 | Total: 47 | [Export Selected] [Copy JSON] │  ← Status Bar
└──────────────────────────────────────────────────────────┘
```

### Key Areas

1. **Toolbar** (sticky top)
   - Board/List selectors (dropdowns)
   - Quick filters
   - Bulk actions (Export, Copy)

2. **Data Table** (main area)
   - Checkbox column for selection
   - Sortable columns
   - Resizable columns
   - Infinite scroll or pagination

3. **Status Bar** (sticky bottom)
   - Selection count
   - Total items
   - Quick actions for selected

## Components

### Data Table

| Feature | Implementation |
|---------|----------------|
| Selection | Checkbox per row + Select All |
| Sorting | Click header to sort (asc/desc) |
| Copy Row | Right-click or Ctrl+C on selection |
| Expand | Click row to show full card details |
| Columns | Configurable, drag to reorder |

### Card Detail Panel (Expanded Row)
```
┌─────────────────────────────────────────────────────────┐
│ Case #1234 - Silva vs. Estado                      [×]  │
├─────────────────────────────────────────────────────────┤
│ Description:                                            │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Ação de indenização por danos morais...             │ │
│ │ Valor da causa: R$ 50.000,00                        │ │
│ │ Foro: Brasília/DF                                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Checklist: Documentos (3/5)                             │
│   ☑ Procuração                                          │
│   ☑ Petição inicial                                     │
│   ☑ Comprovante de residência                           │
│   ☐ RG/CPF                                              │
│   ☐ Comprovante de renda                                │
│                                                         │
│ Attachments:                                            │
│   📎 contrato.pdf (2.3 MB)                              │
│   📎 fotos_evidencia.zip (15 MB)                        │
│                                                         │
│ [Copy All] [Export JSON] [Export CSV]                   │
└─────────────────────────────────────────────────────────┘
```

### Export Options

| Format | Use Case |
|--------|----------|
| **JSON** | API integration, automation |
| **CSV** | Spreadsheet import |
| **Markdown** | Documentation, reports |
| **Plain Text** | Quick paste anywhere |
| **Clipboard** | Instant copy of selected data |

### Filter Panel
```
┌─────────────────────────┐
│ Filters                 │
├─────────────────────────┤
│ Labels:                 │
│   ☑ Urgente             │
│   ☑ Em andamento        │
│   ☐ Concluído           │
│   ☐ Arquivado           │
├─────────────────────────┤
│ Due Date:               │
│   ○ All                 │
│   ○ Overdue             │
│   ● This week           │
│   ○ This month          │
├─────────────────────────┤
│ Members:                │
│   ☑ PGR                 │
│   ☑ LGP                 │
├─────────────────────────┤
│ [Apply] [Clear]         │
└─────────────────────────┘
```

## Interactions

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+A` | Select all visible |
| `Ctrl+C` | Copy selected |
| `Ctrl+Shift+C` | Copy as JSON |
| `Ctrl+E` | Export selected |
| `Space` | Toggle row selection |
| `Enter` | Expand row details |
| `Esc` | Close panel / Clear selection |
| `↑↓` | Navigate rows |
| `/` | Focus search |

### Click Behaviors

| Action | Result |
|--------|--------|
| Click row | Select single row |
| Ctrl+Click | Toggle row selection |
| Shift+Click | Range selection |
| Double-click | Expand row details |
| Right-click | Context menu (Copy, Export, Open in Trello) |

### Copy Behaviors

- **Single cell**: Click cell → Ctrl+C → copies cell value
- **Row**: Select row → Ctrl+C → copies tab-separated values
- **Multiple rows**: Select → Ctrl+C → copies as table
- **JSON**: Ctrl+Shift+C → copies as JSON array

## Responsive

### Desktop (> 1024px)
- Full table with all columns visible
- Side panel for expanded details

### Tablet (768px - 1024px)
- Reduced columns (essential only)
- Full-screen expanded view

### Mobile (< 768px)
- Card list view instead of table
- Swipe actions for quick operations

## Data Display Rules

### Text Truncation
- Card names: 50 chars + ellipsis
- Descriptions: 100 chars in table, full in expanded
- Show full on hover (tooltip)

### Date Formatting
- Relative for recent: "Today", "Yesterday", "3 days ago"
- Absolute for older: "15/12/2024"
- Color coding: Red if overdue, Orange if due soon

### Status Indicators
```
● Active (green)
◐ In Progress (yellow)
○ Pending (gray)
✓ Completed (blue)
⚠ Overdue (red)
```

## Performance

### Requirements
- Load 100+ cards without lag
- Instant filtering (client-side for loaded data)
- Progressive loading for large boards
- Debounced search (300ms)

### Caching
- Cache board/list structure
- Cache card data with TTL
- Background refresh option

## Accessibility

- High contrast text (WCAG AAA)
- Keyboard fully navigable
- Screen reader: announce selection changes
- Focus visible on all interactive elements

---

*Aesthetic: Raw Data Interface*
*Version 1.0 - 2024-12-17*
