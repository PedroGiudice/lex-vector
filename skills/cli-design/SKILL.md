---
name: cli-design
description: Create professional, beautiful command-line interfaces (CLI) and Terminal User Interfaces (TUI) in Python. Use this skill when building terminal applications, interactive menus, or command-line tools that need excellent UX and visual appeal.
license: MIT
---

# CLI Design - Professional Terminal Interfaces

Create distinctive, production-grade command-line interfaces that combine exceptional UX with beautiful visual design. Avoid generic terminal applications - build CLIs that users actually enjoy using.

## When to Use This Skill

- Building interactive CLI applications
- Creating terminal dashboards and status displays
- Designing command-line tools for developers or end-users
- Improving existing CLI applications with better UX/UI

## Design Philosophy

Before coding, commit to a clear design direction:

- **Purpose**: What problem does this CLI solve? Who are the users?
- **Interaction Style**: Simple prompts? Interactive menus? Real-time dashboards?
- **Visual Identity**: Minimal and clean? Colorful and expressive? Retro terminal? Modern UI?
- **Memorable Feature**: What makes this CLI stand out?

**CRITICAL**: Match complexity to the use case. Admin tools need clarity over flash. Developer tools can embrace terminal aesthetics. User-facing tools prioritize intuitive interaction.

## Core Libraries (Python)

### 🎨 **Rich** - Beautiful Terminal Output
The foundation for all professional CLI design.

**Use for:**
- Colored text and styling
- Tables, panels, and boxes
- Progress bars and spinners
- Syntax highlighting
- Markdown rendering

**Example:**
```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Styled panels
console.print(Panel("Status: Connected", style="green"))

# Tables with auto-formatting
table = Table(show_header=True, header_style="bold cyan")
table.add_column("Metric")
table.add_column("Value", justify="right")
table.add_row("Users", "1,234")
console.print(table)
```

**Resources:**
- [Building Beautiful CLIs with Rich](https://thelinuxcode.com/building-beautiful-command-line-interfaces-with-python-rich/)
- [Rich Documentation](https://rich.readthedocs.io/)

---

### 🎯 **Questionary** - Interactive Prompts
For interactive input and menus.

**Use for:**
- Multiple choice selection
- Checkbox lists
- Text input with validation
- Confirmation prompts
- Autocomplete

**Example:**
```python
import questionary
from questionary import Style

custom_style = Style([
    ('qmark', 'fg:#00ff00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#00ffff bold'),
    ('pointer', 'fg:#00ff00 bold'),
])

choice = questionary.select(
    "What would you like to do?",
    choices=[
        "📥 Download data",
        "📊 View statistics",
        "⚙️  Settings",
        "🚪 Exit"
    ],
    style=custom_style
).ask()
```

---

### ⚡ **Typer** - CLI Framework with Type Hints
For building command-line applications with subcommands.

**Use for:**
- Multi-command CLI tools
- Argument parsing
- Help text generation
- Rich integration

**Example:**
```python
import typer
from rich import print

app = typer.Typer()

@app.command()
def download(
    days: int = typer.Option(7, help="Number of days"),
    tribunal: str = typer.Option("STJ", help="Tribunal code")
):
    """Download jurisprudence data."""
    print(f"[green]Downloading {days} days from {tribunal}[/green]")

if __name__ == "__main__":
    app()
```

**Resources:**
- [Interactive CLIs with Typer and Rich](https://pybash.medium.com/interactive-cli-1-40bc1df37df9)

---

### 🖥️ **Textual** - Full TUI Framework (Advanced)
For complex, GUI-like terminal applications.

**Use for:**
- Real-time dashboards
- File managers
- Code editors in terminal
- Complex multi-panel interfaces

**Example:**
```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static

class DashboardApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Real-time metrics here")
        yield Footer()

if __name__ == "__main__":
    app = DashboardApp()
    app.run()
```

**Resources:**
- [Python Textual Tutorial](https://realpython.com/python-textual/)
- [Textual Framework Guide](https://www.arjancodes.com/blog/textual-python-library-for-creating-interactive-terminal-applications/)

---

## Design Guidelines (clig.dev)

Follow best practices from [Command Line Interface Guidelines](https://clig.dev/):

### 1. **Basics**
- Use POSIX-style arguments (`--flag`, `-f`)
- Provide `--help` and `--version`
- Exit codes: 0 = success, non-zero = error
- Write to stderr for errors, stdout for output

### 2. **Output**
- Human-readable by default
- Machine-readable with `--json` or `--format`
- Use colors sparingly (check if terminal supports it)
- Progress indicators for long operations

### 3. **Interactivity**
- Prompt for dangerous operations
- Support `--yes` flag to skip prompts (automation)
- Clear, actionable error messages
- Suggest fixes when possible

### 4. **Robustness**
- Validate input early
- Fail fast with clear messages
- Support Ctrl+C gracefully
- Handle edge cases (empty input, network failures)

---

## Visual Design Patterns

### 📊 **Status Panels**
```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

# Status with nested table
status = Table(show_header=False, box=None)
status.add_column(style="cyan")
status.add_column(style="green")
status.add_row("✓ Database:", "Connected")
status.add_row("  Records:", "12,345")

console.print(Panel(status, title="📊 STATUS", border_style="cyan"))
```

### 🎨 **ASCII Art Logos**
```python
logo = """
 ██████╗██╗     ██╗
██╔════╝██║     ██║
██║     ██║     ██║
██║     ██║     ██║
╚██████╗███████╗██║
 ╚═════╝╚══════╝╚═╝
"""
console.print(logo, style="bold green")
```

Use tools like [patorjk.com/software/taag](http://patorjk.com/software/taag/) for ASCII art.

### 🔄 **Progress Indicators**
```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

with Progress(
    SpinnerColumn(style="green"),
    TextColumn("[bold cyan]{task.description}"),
    BarColumn(style="green"),
    console=console
) as progress:
    task = progress.add_task("Processing...", total=100)
    for i in range(100):
        progress.update(task, advance=1)
        time.sleep(0.01)
```

### 📋 **Interactive Menus**
```python
choices = [
    questionary.Choice("📥 Download", value="download"),
    questionary.Choice("📊 Stats", value="stats"),
    questionary.Separator(),
    questionary.Choice("🚪 Exit", value="exit"),
]

action = questionary.select(
    "What would you like to do?",
    choices=choices,
    instruction="(↑↓ navigate • ⏎ select)"
).ask()
```

---

## Anti-Patterns to Avoid

❌ **Generic AI-generated CLIs:**
- Plain white text on black
- No visual hierarchy
- Wall of text output
- Unclear next steps

❌ **Poor UX:**
- Cryptic error messages
- No progress feedback
- Inconsistent argument naming
- No help text

❌ **Over-engineering:**
- Complex menus for simple tasks
- Unnecessary animations
- Too many colors (rainbow soup)
- Bloated dependencies

---

## Color Palettes for Terminal

### Professional (Subtle)
```python
COLORS = {
    'primary': 'cyan',
    'success': 'green',
    'warning': 'yellow',
    'error': 'red',
    'info': 'blue',
    'muted': 'dim'
}
```

### Vibrant (Expressive)
```python
COLORS = {
    'primary': 'bright_cyan',
    'success': 'bright_green',
    'warning': 'bright_yellow',
    'error': 'bright_red',
    'accent': 'magenta'
}
```

### Dark Mode Friendly
- Avoid pure white (#FFFFFF) - use #E0E0E0
- Prefer bright colors over dark ones
- Test with both light and dark terminal themes

---

## Testing & Validation

1. **Cross-platform testing:**
   - Linux (bash, zsh)
   - macOS (Terminal, iTerm2)
   - Windows (PowerShell, WSL, CMD)

2. **Terminal compatibility:**
   - Check color support: `python -m rich.diagnose`
   - Test Unicode rendering
   - Verify terminal width handling

3. **UX Testing:**
   - Can users complete tasks without help?
   - Are error messages actionable?
   - Is progress feedback clear?

---

## Example: Professional CLI Structure

```python
#!/usr/bin/env python3
"""
Professional CLI Application Template
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import questionary
from questionary import Style

console = Console()

# Custom style
cli_style = Style([
    ('qmark', 'fg:#00ff00 bold'),
    ('pointer', 'fg:#00ff00 bold'),
    ('highlighted', 'fg:#00ff00 bold'),
    ('answer', 'fg:#00ffff bold'),
])

def show_logo():
    """Display ASCII art logo."""
    logo = """
    ▄▄▄▄▄▄▄ ▄▄▄     ▄▄▄
    █       █   █   █   █
    █       █   █   █   █
    █     ▄▄█   █   █   █
    █    █  █   █   █   █
    █    █▄▄█   █▄▄▄█   █
    █▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄█
    """
    console.print(logo, style="bold green")
    console.print("Command Line Tool v1.0.0\n", style="dim", justify="center")

def show_status():
    """Display system status."""
    status = Table(show_header=False, box=None, padding=(0, 1))
    status.add_column(style="cyan")
    status.add_column(style="green")

    status.add_row("✓ Status:", "Ready")
    status.add_row("  Version:", "1.0.0")

    console.print(Panel(status, title="📊 SYSTEM", border_style="cyan"))

def main_menu():
    """Interactive main menu."""
    choices = [
        "🚀 Start process",
        "📊 View stats",
        "⚙️  Settings",
        questionary.Separator(),
        "🚪 Exit"
    ]

    return questionary.select(
        "What would you like to do?",
        choices=choices,
        style=cli_style,
        instruction="(↑↓ navigate • ⏎ select)"
    ).ask()

def main():
    """Main application loop."""
    try:
        while True:
            console.clear()
            show_logo()
            show_status()

            choice = main_menu()

            if choice == "🚪 Exit" or choice is None:
                console.print("\n[bold green]👋 Goodbye![/bold green]\n")
                break

            # Handle other choices...
            console.print(f"\n[yellow]Feature coming soon: {choice}[/yellow]")
            questionary.press_any_key_to_continue().ask()

    except KeyboardInterrupt:
        console.print("\n\n[bold green]👋 Goodbye![/bold green]\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
```

---

## Resources

### Documentation
- [Command Line Interface Guidelines](https://clig.dev/)
- [Rich Library Documentation](https://rich.readthedocs.io/)
- [Textual Framework](https://textual.textualize.io/)
- [Questionary](https://questionary.readthedocs.io/)

### Curated Lists
- [Awesome TUIs](https://github.com/rothgar/awesome-tuis) - Examples of beautiful terminal UIs
- [Awesome CLI Frameworks](https://github.com/shadawck/awesome-cli-frameworks) - CLI tools across languages

### Tutorials
- [Python Textual Tutorial - Real Python](https://realpython.com/python-textual/)
- [Interactive CLIs with Typer and Rich](https://pybash.medium.com/interactive-cli-1-40bc1df37df9)
- [Building Beautiful CLIs](https://thelinuxcode.com/building-beautiful-command-line-interfaces-with-python-rich/)
- [Textual Guide - ArjanCodes](https://www.arjancodes.com/blog/textual-python-library-for-creating-interactive-terminal-applications/)
- [10 Best Python TUI Libraries](https://medium.com/towards-data-engineering/10-best-python-text-user-interface-tui-libraries-for-2025-79f83b6ea16e)

### Design Inspiration
- [Vibe-log CLI](https://github.com/vibelogai/vibe-log) - Beautiful productivity CLI
- [GitHub CLI](https://cli.github.com/) - Clean, professional
- [HTTPie](https://httpie.io/) - Colorful, user-friendly
- [Lazy Git](https://github.com/jesseduffield/lazygit) - Interactive TUI

---

## Implementation Checklist

When building a CLI with this skill:

- [ ] Choose appropriate libraries (Rich + Questionary minimum)
- [ ] Design ASCII logo or header
- [ ] Define color palette (3-5 colors max)
- [ ] Create status/info panels
- [ ] Implement interactive menus
- [ ] Add progress indicators for long operations
- [ ] Write clear help text
- [ ] Handle Ctrl+C gracefully
- [ ] Test cross-platform
- [ ] Provide `--help` and `--version`
- [ ] Support `--yes` for automation
- [ ] Clear, actionable error messages

---

**Remember:** Great CLI design balances aesthetics with functionality. Beautiful output means nothing if the UX is confusing. Prioritize clarity, then add visual polish.
