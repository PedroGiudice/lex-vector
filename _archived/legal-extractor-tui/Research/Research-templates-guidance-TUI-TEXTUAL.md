# Textual TUI design resources: templates, showcase apps, and styling techniques

**No official cookiecutter template exists for Textual** — but the framework's rich ecosystem compensates with exemplary showcase apps, a powerful CSS-based theming system, and an active community producing third-party widgets. Developers should use Hatch scaffolding combined with official reference projects like `textual-calculator-hatch` to start new projects, then study high-profile apps like Harlequin (SQL IDE) and Posting (API client) for sophisticated design patterns.

The framework's design system centers on **11 base theme colors** that generate CSS variables for consistent styling. Combined with TCSS files (Textual's CSS dialect), this enables dark/light mode switching, custom themes like Dracula or Catppuccin, and live CSS hot-reloading during development.

---

## Getting started without official templates

Textual lacks a dedicated cookiecutter or copier template — a notable gap in the ecosystem. However, the recommended workflow uses Python's Hatch build tool:

```bash
hatch new "my-textual-app"    # Scaffold project structure
pip install -e .               # Install in dev mode
textual run --dev my_app.py   # Live CSS reloading
```

The **official reference structure** comes from `textual-calculator-hatch` (https://github.com/Textualize/textual-calculator-hatch), demonstrating:

- `src/` layout with `pyproject.toml` entry points
- Separate `.tcss` files for styles
- `__about__.py` for version management
- Test directory structure

**Development tools** ship via `textual-dev` (https://github.com/Textualize/textual-dev), providing `textual run --dev` for hot-reloading, `textual console` for debugging, and `textual serve` for browser-based testing. The package installs via `pip install 'textual[dev]'`.

Community-curated lists help discover existing projects: **awesome-textualize-projects** (https://github.com/oleksis/awesome-textualize-projects), **transcendent-textual** (https://github.com/davep/transcendent-textual), and **awesome-textual** (https://github.com/Kludex/awesome-textual) collectively catalog **50+ applications** and widget libraries.

---

## Showcase applications demonstrating professional design

Eight standout applications serve as design references for sophisticated TUI development:

**Harlequin** (https://github.com/tconbeer/harlequin, **3,500+ stars**) — A full SQL IDE supporting DuckDB, SQLite, PostgreSQL and dozens of adapters. Demonstrates collapsible data catalog sidebars, tabbed query editors with Tree Sitter syntax highlighting, DataTable results viewers, and fuzzy-match autocomplete. Its plugin architecture shows how to build extensible Textual apps.

**Posting** (https://github.com/darrenburns/posting, **5,000+ stars**) — Modern HTTP client rivaling Postman. Features multi-panel layouts (collection browser, request editor, response viewer), **9+ built-in themes** with custom theming system, compact/standard spacing modes, and keyboard-centric navigation. Version 3.0 uses Textual 3.0 with scripting support.

**Dolphie** (https://github.com/charles-001/dolphie, **3,500+ stars**) — Real-time MySQL/MariaDB monitor showcasing dashboard design. Includes live sparkline graphs, multi-tab database connections, toggleable panels, and **real-time metrics visualization** — essential reference for data-heavy interfaces.

**Toolong** (https://github.com/Textualize/toolong, **3,600+ stars**) — Log viewer demonstrating efficient large file handling, live tailing with realtime updates, log merging by timestamp, and JSONL pretty-printing. Key reference for **performance optimization patterns**.

**Elia** (https://github.com/darrenburns/elia, **1,800+ stars**) — LLM chat client supporting ChatGPT, Claude, Llama. Shows streaming response display, Markdown rendering, code syntax highlighting, and SQLite persistence. Multiple themes (nebula, cobalt, twilight, hacker, alpine, galaxy).

**Frogmouth** (https://github.com/Textualize/frogmouth, **2,400+ stars**) — Markdown browser with browser-like navigation patterns: back/forward history, table of contents sidebar, bookmarks, and vim-style scrolling.

**Memray** (https://github.com/bloomberg/memray, **13,000+ stars**) — Bloomberg's Python memory profiler with Textual TUI mode. Enterprise-grade tooling showing tree reporters for allocation call stacks, thread-based views, and stats modals.

**Trogon** (https://github.com/Textualize/trogon, **2,470+ stars**) — Auto-generates TUI from Click/Typer CLIs with just 2 lines of code. Demonstrates schema-driven UI generation and dynamic form creation.

---

## CSS theming with the Theme class system

Textual's theming centers on **11 base colors** defined via the `Theme` class:

```python
from textual.theme import Theme

custom_theme = Theme(
    name="custom",
    primary="#88C0D0",      # Branding, titles, strong emphasis
    secondary="#81A1C1",    # Alternative branding
    accent="#B48EAD",       # Draw attention, contrast with primary
    foreground="#D8DEE9",   # Default text
    background="#2E3440",   # Screen background  
    surface="#3B4252",      # Widget backgrounds
    panel="#434C5E",        # UI section differentiation
    success="#A3BE8C", warning="#EBCB8B", error="#BF616A",
    dark=True,
)
```

These base colors **auto-generate CSS variables**: `$primary`, `$primary-lighten-1/2/3`, `$primary-darken-1/2/3`, `$primary-muted`, plus semantic text colors like `$text-primary` that adapt for contrast.

**No official Dracula or Catppuccin themes exist** — but creating them is straightforward:

```python
catppuccin_mocha = Theme(
    name="catppuccin-mocha",
    primary="#89B4FA", secondary="#CBA6F7", accent="#F5C2E7",
    foreground="#CDD6F4", background="#1E1E2E", 
    surface="#313244", panel="#45475A",
    success="#A6E3A1", warning="#F9E2AF", error="#F38BA8",
    dark=True,
)
```

Built-in themes include `textual-dark`, `textual-light`, `nord`, and `gruvbox`. Switch themes programmatically with `self.theme = "nord"` or via Command Palette (Ctrl+P).

Preview colors with `textual colors` from the command line.

---

## Layout patterns for complex multi-panel interfaces

**Docking** creates fixed headers, footers, and sidebars:
```tcss
#header { dock: top; height: 3; }
#sidebar { dock: left; width: 25; background: $surface; }
#footer { dock: bottom; height: 3; }
```

**Grid layouts** power complex arrangements:
```tcss
Screen {
    layout: grid;
    grid-size: 3 4;           /* 3 columns, 4 rows */
    grid-columns: 2fr 1fr 1fr;
    grid-gutter: 1 2;
}
#sidebar { row-span: 3; column-span: 2; }
```

**TabbedContent** handles multi-view interfaces:
```python
with TabbedContent(initial="tab1"):
    with TabPane("Dashboard", id="tab1"):
        yield DashboardContent()
    with TabPane("Settings", id="tab2"):
        yield SettingsForm()
```

**Responsive patterns** use fractional units (`1fr`), percentages (`50%`), viewport units (`50vh`), and Python-side resize handling:
```python
def on_resize(self, event):
    sidebar = self.query_one("#sidebar")
    sidebar.display = self.size.width >= 60  # Hide on small terminals
```

---

## Widget-specific styling solutions

### DataTable for document data
```python
table = DataTable(cursor_type="row", zebra_stripes=True)
table.add_column("Status", key="status", width=8)
table.add_column("Document", key="name")

# Rich-styled cells
from rich.text import Text
status = Text("✓", style="bold green", justify="center")
table.add_row(status, "Contract.pdf")

# Sorting
table.sort("date", key=lambda d: d, reverse=True)
```

Component classes enable CSS targeting: `datatable--cursor`, `datatable--header`, `datatable--even-row`. For **millions of rows**, use `textual-fastdatatable` with Apache Arrow/Parquet backends.

### Tree widget customization
```python
class DocTree(Tree[Document]):
    ICON_NODE = "📁 "
    ICON_NODE_EXPANDED = "📂 "
```

Style guide lines and cursors via CSS:
```tcss
Tree .tree--guides { color: $primary-darken-3; }
Tree .tree--cursor { background: $accent; }
```

Implement lazy loading by populating children in `on_tree_node_expanded`.

### Modal dialogs via ModalScreen
```python
from textual.screen import ModalScreen

class ConfirmDialog(ModalScreen[bool]):
    def compose(self):
        with Grid():
            yield Label("Delete item?")
            yield Button("Confirm", id="confirm")
            yield Button("Cancel", id="cancel")
    
    def on_button_pressed(self, event):
        self.dismiss(event.button.id == "confirm")

# Usage
result = await self.push_screen_wait(ConfirmDialog())
```

### Toast notifications
```python
self.notify("File saved!", title="Success")
self.notify("Error occurred", severity="error", timeout=10)
```

---

## Third-party widget ecosystem

| Package | Purpose |
|---------|---------|
| **textual-fastdatatable** | Arrow/Parquet backend for massive datasets |
| **textology** | Dash-like callbacks, MultiSelect, observation patterns |
| **textual-autocomplete** | Input autocompletion |
| **textual-plotext** | Terminal plotting/graphing |
| **textual-fspicker** | File/directory picker modals |
| **textual-window** | Floating, draggable, resizable windows |
| **textual-image** | Image display via TGP/Sixel |
| **zandev-textual-widgets** | MenuBar, context menus, file selectors |

The **transcendent-textual** repository (https://github.com/davep/transcendent-textual) maintains the most comprehensive catalog of extensions.

---

## Essential documentation links

- **CSS Guide**: https://textual.textualize.io/guide/CSS/
- **Theme/Design System**: https://textual.textualize.io/guide/design/
- **Layout Guide**: https://textual.textualize.io/guide/layout/
- **Animation**: https://textual.textualize.io/guide/animation/
- **Widget Gallery**: https://textual.textualize.io/widget_gallery/
- **Screens/Modals**: https://textual.textualize.io/guide/screens/
- **How-To: Package with Hatch**: https://textual.textualize.io/how-to/package-with-hatch/

---

## Conclusion

Textual's strength lies not in templates but in its **exemplary showcase applications** and **powerful CSS-based styling system**. The absence of a cookiecutter template is offset by Hatch scaffolding plus the `textual-calculator-hatch` reference project. For design inspiration, studying Harlequin's multi-panel SQL IDE layout, Posting's theming system, and Dolphie's real-time dashboards provides production-quality patterns.

The theme system's **11-color foundation** generating semantic CSS variables enables consistent theming — creating Dracula or Catppuccin themes requires only mapping their palettes to Textual's color slots. For complex document interfaces, combining `DataTable` with zebra stripes, Rich-styled cells, and `ModalScreen` dialogs covers most legal/document use cases. When built-in widgets fall short, packages like `textual-fastdatatable` and `textual-autocomplete` extend capabilities significantly.