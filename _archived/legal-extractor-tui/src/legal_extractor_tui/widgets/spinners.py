"""Custom spinner definitions for TUI application.

This module provides custom spinner animations optimized for terminal display,
including Claude-style braille patterns, matrix effects, and modern pulse animations.
"""

from dataclasses import dataclass
from typing import Sequence


@dataclass
class SpinnerDefinition:
    """Definition of a spinner animation.
    
    Attributes:
        name: Unique identifier for the spinner
        frames: Sequence of characters/strings representing animation frames
        interval_ms: Milliseconds between frame transitions (default: 80)
    """
    name: str
    frames: Sequence[str]
    interval_ms: int = 80


# 1. claude - braille dots rotacionando (como Claude Code)
claude = SpinnerDefinition(
    name="claude",
    frames=["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    interval_ms=80
)

# 2. thinking - pontos crescentes
thinking = SpinnerDefinition(
    name="thinking",
    frames=[".   ", "..  ", "... ", "...."],
    interval_ms=150
)

# 3. pulse_bar - barra pulsante (blocos preenchendo)
pulse_bar = SpinnerDefinition(
    name="pulse_bar",
    frames=["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"],
    interval_ms=70
)

# 4. neon - circulos parciais
neon = SpinnerDefinition(
    name="neon",
    frames=["◜", "◠", "◝", "◞", "◡", "◟"],
    interval_ms=100
)

# 5. wave - onda vertical com blocos
wave = SpinnerDefinition(
    name="wave",
    frames=["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂", "▁"],
    interval_ms=90
)

# 6. matrix - caracteres japoneses
matrix = SpinnerDefinition(
    name="matrix",
    frames=["ｱ", "ｲ", "ｳ", "ｴ", "ｵ", "ｶ", "ｷ", "ｸ", "ｹ", "ｺ", "ｻ", "ｼ", "ｽ", "ｾ", "ｿ", "ﾀ", "ﾁ", "ﾂ", "ﾃ", "ﾄ"],
    interval_ms=60
)

# 7. processing - blocos pequenos
processing = SpinnerDefinition(
    name="processing",
    frames=["▖", "▘", "▝", "▗"],
    interval_ms=120
)

# 8. orbital - arco orbitando
orbital = SpinnerDefinition(
    name="orbital",
    frames=["◴", "◵", "◶", "◷"],
    interval_ms=100
)

# 9. dna - helix duplo
dna = SpinnerDefinition(
    name="dna",
    frames=["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"],
    interval_ms=150
)

# 10. minimal - ponto pulsante
minimal = SpinnerDefinition(
    name="minimal",
    frames=["⋅", "∘", "○", "◯", "○", "∘"],
    interval_ms=200
)

# 11. cyber - brackets expandindo
cyber = SpinnerDefinition(
    name="cyber",
    frames=["[    ]", "[=   ]", "[==  ]", "[=== ]", "[====]", "[ ===]", "[  ==]", "[   =]"],
    interval_ms=100
)

# Dictionary mapping spinner names to definitions
CUSTOM_SPINNERS = {
    spinner.name: spinner
    for spinner in [
        claude,
        thinking,
        pulse_bar,
        neon,
        wave,
        matrix,
        processing,
        orbital,
        dna,
        minimal,
        cyber,
    ]
}
