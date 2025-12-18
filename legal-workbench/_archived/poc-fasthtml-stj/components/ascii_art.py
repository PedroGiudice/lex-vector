"""
ASCII Art Empty States for Legal Workbench STJ Module
Terminal/scientific aesthetic matching the dark theme
"""

from fasthtml.common import *

# ============================================
# ASCII ART OPTIONS
# ============================================

EMPTY_STATE_SEARCH = '''
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    │            [ SEARCH RETURNED NULL ]             │
    │                                                 │
    │        Try broadening your query terms          │
    │        or adjusting date range filters          │
    │                                                 │
    └─────────────────────────────────────────────────┘
'''

EMPTY_STATE_TERMINAL = '''
    $ query --filter="current_params" --count
    > Scanning database...
    > Applying filters...
    >
    > [!] No matches found (0 results)
    >
    > Suggestions:
    >   • Check filter parameters
    >   • Broaden date range
    >   • Review query syntax
'''

EMPTY_STATE_SCIENTIFIC = '''
    ╔════════════════════════════════════════╗
    ║  QUERY EXECUTION: COMPLETE             ║
    ║  MATCHES FOUND: 0                      ║
    ║  STATUS: NULL_SET                      ║
    ╠════════════════════════════════════════╣
    ║  → Modify search parameters            ║
    ║  → Verify data availability            ║
    ╚════════════════════════════════════════╝
'''

EMPTY_STATE_GRID = '''
    ┏━━━┳━━━┳━━━┓
    ┃   ┃   ┃   ┃   No results match
    ┣━━━╋━━━╋━━━┫   your current filters
    ┃   ┃   ┃   ┃
    ┣━━━╋━━━╋━━━┫   Refine search criteria
    ┃   ┃   ┃   ┃   or reset to defaults
    ┗━━━┻━━━┻━━━┛
'''

EMPTY_STATE_MINIMAL = '''

         ▓▓░░░░░░░░░░░░░░░░░░░░░░░░▓▓

              0 documents found

         ▓▓░░░░░░░░░░░░░░░░░░░░░░░░▓▓

'''

EMPTY_STATE_RADAR = '''
              ┌───────┐
            ╱           ╲
          │      · ·      │
          │    ·     ·    │   NO TARGETS DETECTED
          │      · ·      │
            ╲           ╱
              └───────┘

        Expand search radius or
        adjust detection parameters
'''

# Default for STJ module
EMPTY_STATE_DEFAULT = EMPTY_STATE_TERMINAL


def empty_state_display(variant: str = "terminal", message: str = None) -> FT:
    """
    Display ASCII art empty state.

    Args:
        variant: One of "search", "terminal", "scientific", "grid", "minimal", "radar"
        message: Optional custom message to display below the art

    Returns:
        FT component with styled ASCII art
    """
    states = {
        "search": EMPTY_STATE_SEARCH,
        "terminal": EMPTY_STATE_TERMINAL,
        "scientific": EMPTY_STATE_SCIENTIFIC,
        "grid": EMPTY_STATE_GRID,
        "minimal": EMPTY_STATE_MINIMAL,
        "radar": EMPTY_STATE_RADAR,
    }

    ascii_art = states.get(variant, EMPTY_STATE_DEFAULT)

    return Div(
        Div(
            Pre(ascii_art, cls="ascii-art"),
            cls="ascii-container"
        ),
        Div(
            message or "Nenhum resultado encontrado",
            cls="ascii-subtitle"
        ) if message else None,
        cls="empty-state-container"
    )
