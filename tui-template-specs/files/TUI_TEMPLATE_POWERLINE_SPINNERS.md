# TUI Template - Powerline & Spinners Extension

> Extensão do TUI Template com elementos visuais avançados:
> Separadores Powerline, Spinners customizados e Cursores animados

---

## Sumário

1. [Requisitos de Fonte](#1-requisitos-de-fonte)
2. [Caracteres Powerline](#2-caracteres-powerline)
3. [Spinners Disponíveis](#3-spinners-disponíveis)
4. [Spinners Customizados](#4-spinners-customizados)
5. [Cursor Blinker (Bash Style)](#5-cursor-blinker-bash-style)
6. [Widgets Powerline](#6-widgets-powerline)
7. [Integração com Template](#7-integração-com-template)

---

## 1. Requisitos de Fonte

### 1.1 Nerd Fonts (Recomendado)

Para os caracteres Powerline funcionarem corretamente, o terminal deve usar uma **Nerd Font**.

**Fontes recomendadas:**
| Fonte | Estilo | Download |
|-------|--------|----------|
| JetBrainsMono Nerd Font | Moderno, legível | nerdfonts.com |
| FiraCode Nerd Font | Ligaduras, popular | nerdfonts.com |
| Hack Nerd Font | Clássico dev | nerdfonts.com |
| CascadiaCode Nerd Font | Microsoft, moderno | nerdfonts.com |

**Instalação no WSL2 (Ubuntu):**
```bash
# Criar diretório de fontes
mkdir -p ~/.local/share/fonts

# Baixar JetBrainsMono Nerd Font
cd ~/.local/share/fonts
wget https://github.com/ryanoasis/nerd-fonts/releases/download/v3.1.1/JetBrainsMono.zip
unzip JetBrainsMono.zip
rm JetBrainsMono.zip

# Atualizar cache de fontes
fc-cache -fv
```

**Configuração no Windows Terminal:**
```json
{
    "profiles": {
        "defaults": {
            "font": {
                "face": "JetBrainsMono Nerd Font",
                "size": 12
            }
        }
    }
}
```

### 1.2 Fallback sem Nerd Fonts

Se Nerd Fonts não estiver disponível, o template oferece caracteres ASCII alternativos:

```python
# Configuração com fallback
POWERLINE_ENABLED = True  # False para usar ASCII

# Com Nerd Font
SEPARATORS = {
    "left_solid": "\uE0B0",      # 
    "left_thin": "\uE0B1",       # 
    "right_solid": "\uE0B2",     # 
    "right_thin": "\uE0B3",      # 
    "left_round": "\uE0B4",      # 
    "right_round": "\uE0B6",     # 
}

# Fallback ASCII
SEPARATORS_ASCII = {
    "left_solid": "▶",
    "left_thin": "│",
    "right_solid": "◀",
    "right_thin": "│",
    "left_round": ")",
    "right_round": "(",
}
```

---

## 2. Caracteres Powerline

### 2.1 Separadores Básicos

| Código | Caractere | Nome | Uso |
|--------|-----------|------|-----|
| `\uE0B0` |  | Left solid | Separador principal esquerda→direita |
| `\uE0B1` |  | Left thin | Separador secundário |
| `\uE0B2` |  | Right solid | Separador principal direita→esquerda |
| `\uE0B3` |  | Right thin | Separador secundário |
| `\uE0B4` |  | Left round | Separador arredondado |
| `\uE0B6` |  | Right round | Separador arredondado |
| `\uE0B8` |  | Lower left | Diagonal inferior |
| `\uE0BA` |  | Lower right | Diagonal inferior |
| `\uE0BC` |  | Upper left | Diagonal superior |
| `\uE0BE` |  | Upper right | Diagonal superior |

### 2.2 Símbolos de Status

| Código | Caractere | Nome | Uso |
|--------|-----------|------|-----|
| `\uE0A0` |  | Branch | Git branch |
| `\uE0A1` |  | Line number | Número de linha |
| `\uE0A2` |  | Lock | Read-only |
| `\uE0A3` |  | Column number | Número de coluna |

### 2.3 Ícones Comuns (Material Design / Nerd Fonts)

| Código | Caractere | Nome |
|--------|-----------|------|
| `\uF015` |  | Home |
| `\uF07B` |  | Folder |
| `\uF07C` |  | Folder open |
| `\uF1C1` |  | File PDF |
| `\uF121` |  | Code |
| `\uF013` |  | Settings |
| `\uF00C` |  | Check |
| `\uF00D` |  | X / Close |
| `\uF071` |  | Warning |
| `\uF05A` |  | Info |
| `\uF06A` |  | Error |
| `\uF017` |  | Clock |
| `\uF0E7` |  | Lightning |
| `\uF240` |  | Battery full |
| `\uF244` |  | Battery empty |

---

## 3. Spinners Disponíveis

### 3.1 Spinners Built-in do Rich

O Rich (base do Textual) inclui 80+ spinners do `cli-spinners`. Use com:

```python
from rich.spinner import Spinner, SPINNERS

# Ver todos disponíveis
print(list(SPINNERS.keys()))

# Criar spinner
spinner = Spinner("dots", style="cyan")
```

**Spinners mais úteis para TUIs:**

| Nome | Frames | Visual | Uso recomendado |
|------|--------|--------|-----------------|
| `dots` | ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏ | Braille circular | **Padrão, muito usado** |
| `dots2` | ⣾⣽⣻⢿⡿⣟⣯⣷ | Braille cheio | Carregamento pesado |
| `dots8Bit` | ⠀⠁⠂⠃⠄⠅⠆⠇... | Braille crescente | Progress indeterminado |
| `line` | -\|/ | Clássico | Compatibilidade ASCII |
| `line2` | ⠂-–—–-⠂ | Linha animada | Minimalista |
| `arc` | ◜◠◝◞◡◟ | Arco | Elegante |
| `circle` | ◡⊙◠ | Círculo | Simples |
| `bouncingBar` | [    ][=   ]... | Barra | Progress loading |
| `bouncingBall` | ( ●    )(  ●   )... | Bola | Divertido |
| `aesthetic` | ▰▱▱▱▱▱▱ | Barra estética | **Muito bonito** |
| `material` | █▁▂▃▄▅▆▇ | Wave | Material design |
| `moon` | 🌑🌒🌓🌔🌕🌖🌗🌘 | Fases da lua | Temático |
| `earth` | 🌍🌎🌏 | Terra | Global |
| `clock` | 🕛🕐🕑🕒... | Relógio | Tempo |
| `runner` | 🚶🏃 | Corredor | Processo |
| `toggle` | ⊶⊷ | Toggle | On/Off |
| `arrow` | ←↖↑↗→↘↓↙ | Setas | Direção |
| `point` | ∙∙∙●∙∙∙ | Ponto | Foco |
| `layer` | ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁ | Layers | Volume/intensidade |
| `betaWave` | ρβ | Beta wave | Científico |
| `noise` | ▓▒░ | Noise | Processamento |

### 3.2 Comparação Visual de Spinners Populares

```
dots:        ⠋ → ⠙ → ⠹ → ⠸ → ⠼ → ⠴ → ⠦ → ⠧ → ⠇ → ⠏
dots2:       ⣾ → ⣽ → ⣻ → ⢿ → ⡿ → ⣟ → ⣯ → ⣷
arc:         ◜ → ◠ → ◝ → ◞ → ◡ → ◟
circle:      ◡ → ⊙ → ◠
line:        - → \ → | → /
aesthetic:   ▰▱▱▱▱▱▱ → ▰▰▱▱▱▱▱ → ▰▰▰▱▱▱▱ → ...
material:    █▁▁▁▁▁▁▁ → █▂▁▁▁▁▁▁ → █▃▂▁▁▁▁▁ → ...
bouncingBar: [=   ] → [ =  ] → [  = ] → [   =] → [  = ] → ...
```

---

## 4. Spinners Customizados

### 4.1 Definição de Spinner Custom

```python
# src/tui_app/widgets/spinners.py

"""
Spinners customizados para o TUI Template.
"""

from dataclasses import dataclass
from typing import Sequence


@dataclass
class SpinnerDefinition:
    """Definição de um spinner customizado."""
    name: str
    frames: Sequence[str]
    interval_ms: int = 80


# ============================================================================
# SPINNERS CUSTOMIZADOS
# ============================================================================

# Spinner estilo Claude Code (braille dots rotacionando)
CLAUDE_SPINNER = SpinnerDefinition(
    name="claude",
    frames=["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
    interval_ms=80,
)

# Spinner de pontos crescentes (similar ao thinking do Claude)
THINKING_SPINNER = SpinnerDefinition(
    name="thinking",
    frames=[".", "..", "...", "....", ".....", "......"],
    interval_ms=200,
)

# Spinner de barra pulsante
PULSE_BAR_SPINNER = SpinnerDefinition(
    name="pulse_bar",
    frames=[
        "█▒▒▒▒▒▒▒▒▒",
        "██▒▒▒▒▒▒▒▒",
        "███▒▒▒▒▒▒▒",
        "████▒▒▒▒▒▒",
        "█████▒▒▒▒▒",
        "██████▒▒▒▒",
        "███████▒▒▒",
        "████████▒▒",
        "█████████▒",
        "██████████",
        "█████████▒",
        "████████▒▒",
        "███████▒▒▒",
        "██████▒▒▒▒",
        "█████▒▒▒▒▒",
        "████▒▒▒▒▒▒",
        "███▒▒▒▒▒▒▒",
        "██▒▒▒▒▒▒▒▒",
    ],
    interval_ms=50,
)

# Spinner neon (para tema VIBE)
NEON_SPINNER = SpinnerDefinition(
    name="neon",
    frames=["◐", "◓", "◑", "◒"],
    interval_ms=100,
)

# Spinner de wave vertical
WAVE_SPINNER = SpinnerDefinition(
    name="wave",
    frames=[
        "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁",
        "▂▃▄▅▆▇█▇▆▅▄▃▂▁▁",
        "▃▄▅▆▇█▇▆▅▄▃▂▁▁▂",
        "▄▅▆▇█▇▆▅▄▃▂▁▁▂▃",
        "▅▆▇█▇▆▅▄▃▂▁▁▂▃▄",
        "▆▇█▇▆▅▄▃▂▁▁▂▃▄▅",
        "▇█▇▆▅▄▃▂▁▁▂▃▄▅▆",
        "█▇▆▅▄▃▂▁▁▂▃▄▅▆▇",
    ],
    interval_ms=80,
)

# Spinner Matrix (caracteres caindo)
MATRIX_SPINNER = SpinnerDefinition(
    name="matrix",
    frames=["ﾊ", "ﾐ", "ﾋ", "ｰ", "ｳ", "ｼ", "ﾅ", "ﾓ", "ﾆ", "ｻ"],
    interval_ms=100,
)

# Spinner de processamento (blocos)
PROCESSING_SPINNER = SpinnerDefinition(
    name="processing",
    frames=["▖", "▘", "▝", "▗"],
    interval_ms=100,
)

# Spinner orbital
ORBITAL_SPINNER = SpinnerDefinition(
    name="orbital",
    frames=[
        "◜ ",
        " ◝",
        " ◞",
        "◟ ",
    ],
    interval_ms=120,
)

# Spinner de DNA/helix
DNA_SPINNER = SpinnerDefinition(
    name="dna",
    frames=[
        "⠋⠁",
        "⠙⠂",
        "⠹⠄",
        "⢸⡀",
        "⣰⣀",
        "⣤⣄",
        "⣆⣤",
        "⡇⣤",
        "⠏⣤",
        "⠋⢤",
        "⠙⠤",
        "⠹⠠",
        "⢸⠐",
        "⣰⠈",
    ],
    interval_ms=80,
)

# Spinner minimalista (ponto pulsante)
MINIMAL_SPINNER = SpinnerDefinition(
    name="minimal",
    frames=["●", "○"],
    interval_ms=500,
)

# Spinner cyberpunk
CYBER_SPINNER = SpinnerDefinition(
    name="cyber",
    frames=[
        "⟨⟩",
        "⟨=⟩",
        "⟨==⟩",
        "⟨===⟩",
        "⟨====⟩",
        "⟨=====⟩",
        "⟨====⟩",
        "⟨===⟩",
        "⟨==⟩",
        "⟨=⟩",
    ],
    interval_ms=80,
)


# Registro de todos os spinners customizados
CUSTOM_SPINNERS = {
    "claude": CLAUDE_SPINNER,
    "thinking": THINKING_SPINNER,
    "pulse_bar": PULSE_BAR_SPINNER,
    "neon": NEON_SPINNER,
    "wave": WAVE_SPINNER,
    "matrix": MATRIX_SPINNER,
    "processing": PROCESSING_SPINNER,
    "orbital": ORBITAL_SPINNER,
    "dna": DNA_SPINNER,
    "minimal": MINIMAL_SPINNER,
    "cyber": CYBER_SPINNER,
}
```

### 4.2 Widget de Spinner Universal

```python
# src/tui_app/widgets/spinner_widget.py

"""
Widget de spinner universal com suporte a Rich spinners e customizados.
"""

from typing import Literal
from rich.spinner import Spinner as RichSpinner, SPINNERS as RICH_SPINNERS
from rich.text import Text
from textual.widgets import Static
from textual.reactive import reactive

from tui_app.widgets.spinners import CUSTOM_SPINNERS, SpinnerDefinition


SpinnerStyle = Literal["rich", "custom", "braille", "ascii"]


class SpinnerWidget(Static):
    """
    Widget de spinner animado.
    
    Suporta:
    - Spinners built-in do Rich (80+)
    - Spinners customizados definidos em spinners.py
    - Criação dinâmica de spinners
    
    Uso:
        # Rich spinner
        yield SpinnerWidget("dots", style="cyan")
        
        # Custom spinner
        yield SpinnerWidget("claude", source="custom", style="magenta")
        
        # Spinner com texto
        yield SpinnerWidget("dots", text="Carregando...", style="green")
    """
    
    DEFAULT_CSS = """
    SpinnerWidget {
        width: auto;
        height: 1;
    }
    
    SpinnerWidget.running {
        /* Pode adicionar efeitos visuais */
    }
    
    SpinnerWidget.paused {
        color: $foreground-muted;
    }
    """
    
    is_spinning: reactive[bool] = reactive(True)
    
    def __init__(
        self,
        spinner_name: str = "dots",
        *,
        source: SpinnerStyle = "rich",
        text: str = "",
        style: str = "cyan",
        speed: float = 1.0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Inicializa spinner.
        
        Args:
            spinner_name: Nome do spinner
            source: Origem ("rich" para built-in, "custom" para customizados)
            text: Texto exibido ao lado do spinner
            style: Cor/estilo Rich
            speed: Fator de velocidade (1.0 = normal)
        """
        super().__init__(name=name, id=id, classes=classes)
        
        self._spinner_name = spinner_name
        self._source = source
        self._text = text
        self._style = style
        self._speed = speed
        self._frame_index = 0
        self._interval_update = None
        
        # Determinar frames e intervalo
        if source == "rich" and spinner_name in RICH_SPINNERS:
            self._spinner = RichSpinner(spinner_name, text=text, style=style, speed=speed)
            self._use_rich = True
        elif source == "custom" and spinner_name in CUSTOM_SPINNERS:
            definition = CUSTOM_SPINNERS[spinner_name]
            self._frames = definition.frames
            self._interval_ms = definition.interval_ms / speed
            self._use_rich = False
        else:
            # Fallback para dots
            self._spinner = RichSpinner("dots", text=text, style=style, speed=speed)
            self._use_rich = True
    
    def on_mount(self) -> None:
        """Inicia animação ao montar."""
        if self._use_rich:
            self._interval_update = self.set_interval(1/60, self._update_rich)
        else:
            interval_s = self._interval_ms / 1000
            self._interval_update = self.set_interval(interval_s, self._update_custom)
        
        self.add_class("running")
    
    def _update_rich(self) -> None:
        """Atualiza spinner Rich."""
        if self.is_spinning:
            self.update(self._spinner)
    
    def _update_custom(self) -> None:
        """Atualiza spinner customizado."""
        if self.is_spinning:
            frame = self._frames[self._frame_index]
            
            if self._text:
                display = f"[{self._style}]{frame}[/] {self._text}"
            else:
                display = f"[{self._style}]{frame}[/]"
            
            self.update(display)
            self._frame_index = (self._frame_index + 1) % len(self._frames)
    
    def pause(self) -> None:
        """Pausa animação."""
        self.is_spinning = False
        self.remove_class("running")
        self.add_class("paused")
    
    def resume(self) -> None:
        """Retoma animação."""
        self.is_spinning = True
        self.remove_class("paused")
        self.add_class("running")
    
    def set_text(self, text: str) -> None:
        """Atualiza texto do spinner."""
        self._text = text
        if self._use_rich:
            self._spinner = RichSpinner(
                self._spinner_name,
                text=text,
                style=self._style,
                speed=self._speed,
            )
```

---

## 5. Cursor Blinker (Bash Style)

### 5.1 Cursor Piscante

O "bash blinker" é um cursor que pisca para indicar input ativo ou processamento.

```python
# src/tui_app/widgets/blinker.py

"""
Cursor piscante estilo bash/terminal.
"""

from textual.widgets import Static
from textual.reactive import reactive


class Blinker(Static):
    """
    Cursor piscante.
    
    Tipos disponíveis:
    - "block": █ (bloco sólido)
    - "line": │ (linha vertical)
    - "underscore": _ (underscore)
    - "pipe": | (pipe)
    - "beam": ▎ (beam fino)
    
    Uso:
        yield Blinker(style="block", color="cyan")
    """
    
    DEFAULT_CSS = """
    Blinker {
        width: 1;
        height: 1;
    }
    """
    
    CURSOR_CHARS = {
        "block": ("█", " "),
        "block_half": ("▌", " "),
        "line": ("│", " "),
        "underscore": ("_", " "),
        "pipe": ("|", " "),
        "beam": ("▎", " "),
        "dot": ("●", "○"),
        "square": ("■", "□"),
    }
    
    visible: reactive[bool] = reactive(True)
    
    def __init__(
        self,
        style: str = "block",
        color: str = "cyan",
        blink_rate_ms: int = 530,  # Típico do terminal
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._style = style
        self._color = color
        self._blink_rate = blink_rate_ms
        self._chars = self.CURSOR_CHARS.get(style, self.CURSOR_CHARS["block"])
    
    def on_mount(self) -> None:
        """Inicia blinking."""
        self.set_interval(self._blink_rate / 1000, self._toggle)
        self._update_display()
    
    def _toggle(self) -> None:
        """Alterna visibilidade."""
        self.visible = not self.visible
    
    def watch_visible(self, visible: bool) -> None:
        """Atualiza display quando visibilidade muda."""
        self._update_display()
    
    def _update_display(self) -> None:
        """Atualiza o caractere exibido."""
        char = self._chars[0] if self.visible else self._chars[1]
        self.update(f"[{self._color}]{char}[/]")


class InputCursor(Static):
    """
    Cursor de input com texto dinâmico.
    
    Uso:
        cursor = InputCursor(prompt=">>> ")
        cursor.set_input("hello")  # Exibe: >>> hello█
    """
    
    DEFAULT_CSS = """
    InputCursor {
        width: 100%;
        height: 1;
    }
    """
    
    cursor_visible: reactive[bool] = reactive(True)
    input_text: reactive[str] = reactive("")
    
    def __init__(
        self,
        prompt: str = "$ ",
        prompt_style: str = "green bold",
        input_style: str = "white",
        cursor_style: str = "cyan",
        cursor_char: str = "█",
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._prompt = prompt
        self._prompt_style = prompt_style
        self._input_style = input_style
        self._cursor_style = cursor_style
        self._cursor_char = cursor_char
    
    def on_mount(self) -> None:
        """Inicia cursor blinking."""
        self.set_interval(0.53, self._toggle_cursor)
        self._update_display()
    
    def _toggle_cursor(self) -> None:
        """Alterna cursor."""
        self.cursor_visible = not self.cursor_visible
    
    def watch_cursor_visible(self, visible: bool) -> None:
        """Reage à mudança de visibilidade."""
        self._update_display()
    
    def watch_input_text(self, text: str) -> None:
        """Reage à mudança de texto."""
        self._update_display()
    
    def _update_display(self) -> None:
        """Renderiza prompt + input + cursor."""
        cursor = self._cursor_char if self.cursor_visible else " "
        
        display = (
            f"[{self._prompt_style}]{self._prompt}[/]"
            f"[{self._input_style}]{self.input_text}[/]"
            f"[{self._cursor_style}]{cursor}[/]"
        )
        self.update(display)
    
    def set_input(self, text: str) -> None:
        """Define texto do input."""
        self.input_text = text
    
    def append(self, char: str) -> None:
        """Adiciona caractere ao input."""
        self.input_text += char
    
    def backspace(self) -> None:
        """Remove último caractere."""
        self.input_text = self.input_text[:-1]
    
    def clear(self) -> None:
        """Limpa input."""
        self.input_text = ""
```

---

## 6. Widgets Powerline

### 6.1 Barra de Status Powerline

```python
# src/tui_app/widgets/powerline_status.py

"""
Barra de status com separadores Powerline.
"""

from dataclasses import dataclass
from textual.app import ComposeResult
from textual.widgets import Static
from textual.widget import Widget


# Caracteres Powerline
PL_LEFT_SOLID = "\uE0B0"      # 
PL_LEFT_THIN = "\uE0B1"       # 
PL_RIGHT_SOLID = "\uE0B2"     # 
PL_RIGHT_THIN = "\uE0B3"      # 
PL_LEFT_ROUND = "\uE0B4"      # 
PL_RIGHT_ROUND = "\uE0B6"     # 

# Fallback ASCII
PL_LEFT_SOLID_ASCII = "▶"
PL_LEFT_THIN_ASCII = "│"
PL_RIGHT_SOLID_ASCII = "◀"
PL_RIGHT_THIN_ASCII = "│"


@dataclass
class PowerlineSegment:
    """Segmento da barra Powerline."""
    text: str
    fg: str = "white"
    bg: str = "blue"
    icon: str | None = None


class PowerlineBar(Widget):
    """
    Barra de status com separadores Powerline.
    
    Uso:
        bar = PowerlineBar([
            PowerlineSegment("MAIN", fg="black", bg="cyan", icon=""),
            PowerlineSegment("file.py", fg="white", bg="blue"),
            PowerlineSegment("UTF-8", fg="black", bg="green"),
        ])
    """
    
    DEFAULT_CSS = """
    PowerlineBar {
        height: 1;
        width: 100%;
        background: $background;
    }
    """
    
    def __init__(
        self,
        segments: list[PowerlineSegment] | None = None,
        *,
        use_powerline_fonts: bool = True,
        align: str = "left",  # "left", "right", "both"
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._segments = segments or []
        self._use_powerline = use_powerline_fonts
        self._align = align
    
    def compose(self) -> ComposeResult:
        yield Static(self._render(), id="powerline-content")
    
    def _render(self) -> str:
        """Renderiza a barra Powerline."""
        if not self._segments:
            return ""
        
        sep = PL_LEFT_SOLID if self._use_powerline else PL_LEFT_SOLID_ASCII
        parts = []
        
        for i, segment in enumerate(self._segments):
            # Ícone + texto
            content = f" {segment.icon} " if segment.icon else " "
            content += f"{segment.text} "
            
            # Estilo do segmento
            styled = f"[{segment.fg} on {segment.bg}]{content}[/]"
            parts.append(styled)
            
            # Separador (exceto no último)
            if i < len(self._segments) - 1:
                next_bg = self._segments[i + 1].bg
                separator = f"[{segment.bg} on {next_bg}]{sep}[/]"
                parts.append(separator)
            else:
                # Separador final
                final_sep = f"[{segment.bg}]{sep}[/]"
                parts.append(final_sep)
        
        return "".join(parts)
    
    def update_segments(self, segments: list[PowerlineSegment]) -> None:
        """Atualiza segmentos."""
        self._segments = segments
        content = self.query_one("#powerline-content", Static)
        content.update(self._render())
    
    def set_segment(self, index: int, segment: PowerlineSegment) -> None:
        """Atualiza um segmento específico."""
        if 0 <= index < len(self._segments):
            self._segments[index] = segment
            content = self.query_one("#powerline-content", Static)
            content.update(self._render())


class PowerlineHeader(Widget):
    """
    Header estilizado com Powerline.
    
    ┌─────────────────────────────────────────────────────────────┐
    │  APP NAME │ v1.0.0 │ ● Connected │            │ 12:34:56 │
    └─────────────────────────────────────────────────────────────┘
    """
    
    DEFAULT_CSS = """
    PowerlineHeader {
        dock: top;
        height: 1;
        background: $surface;
    }
    """
    
    def __init__(
        self,
        app_name: str = "TUI App",
        version: str = "1.0.0",
        *,
        show_time: bool = True,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._app_name = app_name
        self._version = version
        self._show_time = show_time
        self._status = "Ready"
        self._status_style = "success"
    
    def compose(self) -> ComposeResult:
        left_segments = [
            PowerlineSegment(self._app_name, fg="black", bg="cyan", icon=""),
            PowerlineSegment(f"v{self._version}", fg="white", bg="blue"),
        ]
        
        yield PowerlineBar(left_segments, id="header-left")
        
        if self._show_time:
            yield Static("", id="header-time")
    
    def on_mount(self) -> None:
        """Inicia timer."""
        if self._show_time:
            self.set_interval(1.0, self._update_time)
            self._update_time()
    
    def _update_time(self) -> None:
        """Atualiza relógio."""
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        time_widget = self.query_one("#header-time", Static)
        time_widget.update(f"[dim]{time_str}[/]")
    
    def set_status(self, status: str, style: str = "success") -> None:
        """Define status exibido."""
        self._status = status
        self._status_style = style
        # Atualizar renderização...


class PowerlineFooter(Widget):
    """
    Footer estilizado com Powerline (separadores da direita para esquerda).
    
    │ ln 42 │ col 10 │ UTF-8 │ Python │ INSERT │
    """
    
    DEFAULT_CSS = """
    PowerlineFooter {
        dock: bottom;
        height: 1;
        background: $panel;
    }
    """
    
    def __init__(
        self,
        segments: list[PowerlineSegment] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._segments = segments or [
            PowerlineSegment("Ready", fg="black", bg="green"),
        ]
    
    def compose(self) -> ComposeResult:
        yield Static(self._render_right(), id="footer-content")
    
    def _render_right(self) -> str:
        """Renderiza da direita para esquerda."""
        if not self._segments:
            return ""
        
        sep = PL_RIGHT_SOLID
        parts = []
        
        # Inverte para processar da direita
        segments = list(reversed(self._segments))
        
        for i, segment in enumerate(segments):
            content = f" {segment.text} "
            
            if i == 0:
                # Primeiro da direita: separador inicial
                parts.append(f"[{segment.bg}]{sep}[/]")
            
            styled = f"[{segment.fg} on {segment.bg}]{content}[/]"
            parts.append(styled)
            
            if i < len(segments) - 1:
                next_bg = segments[i + 1].bg
                separator = f"[{next_bg} on {segment.bg}]{sep}[/]"
                parts.append(separator)
        
        # Inverte resultado para ordem correta
        return "".join(reversed(parts))
```

### 6.2 Breadcrumb Powerline

```python
# src/tui_app/widgets/powerline_breadcrumb.py

"""
Breadcrumb com estilo Powerline para navegação.
"""

from textual.widgets import Static
from textual.widget import Widget
from textual.app import ComposeResult
from textual.message import Message


class PowerlineBreadcrumb(Widget):
    """
    Breadcrumb navegável com separadores Powerline.
    
    Exibe:
        Home  Documents  Projects  current-file.py
    
    Uso:
        yield PowerlineBreadcrumb(["Home", "Documents", "Projects"])
    """
    
    DEFAULT_CSS = """
    PowerlineBreadcrumb {
        height: 1;
        width: 100%;
    }
    
    PowerlineBreadcrumb .crumb {
        /* Cada item do breadcrumb */
    }
    
    PowerlineBreadcrumb .crumb-active {
        text-style: bold;
    }
    """
    
    class CrumbClicked(Message):
        """Emitida quando um item é clicado."""
        def __init__(self, index: int, name: str) -> None:
            self.index = index
            self.name = name
            super().__init__()
    
    def __init__(
        self,
        items: list[str] | None = None,
        *,
        separator: str = "\uE0B1",  #  (thin separator)
        base_color: str = "blue",
        active_color: str = "cyan",
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._items = items or []
        self._separator = separator
        self._base_color = base_color
        self._active_color = active_color
    
    def compose(self) -> ComposeResult:
        yield Static(self._render(), id="breadcrumb-content")
    
    def _render(self) -> str:
        """Renderiza breadcrumb."""
        if not self._items:
            return ""
        
        parts = []
        for i, item in enumerate(self._items):
            is_last = i == len(self._items) - 1
            color = self._active_color if is_last else self._base_color
            style = "bold" if is_last else ""
            
            parts.append(f"[{color} {style}] {item} [/]")
            
            if not is_last:
                parts.append(f"[dim]{self._separator}[/]")
        
        return "".join(parts)
    
    def set_items(self, items: list[str]) -> None:
        """Atualiza items."""
        self._items = items
        content = self.query_one("#breadcrumb-content", Static)
        content.update(self._render())
    
    def push(self, item: str) -> None:
        """Adiciona item ao breadcrumb."""
        self._items.append(item)
        self.set_items(self._items)
    
    def pop(self) -> str | None:
        """Remove último item."""
        if self._items:
            item = self._items.pop()
            self.set_items(self._items)
            return item
        return None
```

---

## 7. Integração com Template

### 7.1 Adições ao `__init__.py` de widgets

```python
# Adicionar ao src/tui_app/widgets/__init__.py

from tui_app.widgets.spinners import (
    CUSTOM_SPINNERS,
    CLAUDE_SPINNER,
    THINKING_SPINNER,
    NEON_SPINNER,
    WAVE_SPINNER,
)
from tui_app.widgets.spinner_widget import SpinnerWidget
from tui_app.widgets.blinker import Blinker, InputCursor
from tui_app.widgets.powerline_status import (
    PowerlineSegment,
    PowerlineBar,
    PowerlineHeader,
    PowerlineFooter,
)
from tui_app.widgets.powerline_breadcrumb import PowerlineBreadcrumb

__all__ = [
    # ... widgets anteriores ...
    
    # Spinners
    "CUSTOM_SPINNERS",
    "CLAUDE_SPINNER",
    "THINKING_SPINNER",
    "NEON_SPINNER",
    "WAVE_SPINNER",
    "SpinnerWidget",
    
    # Blinkers
    "Blinker",
    "InputCursor",
    
    # Powerline
    "PowerlineSegment",
    "PowerlineBar",
    "PowerlineHeader",
    "PowerlineFooter",
    "PowerlineBreadcrumb",
]
```

### 7.2 CSS Adicional para Powerline

```css
/* Adicionar ao src/tui_app/styles/widgets.tcss */

/* ----------------------------------------------------------------------------
   POWERLINE WIDGETS
   ---------------------------------------------------------------------------- */

PowerlineBar {
    height: 1;
    background: transparent;
}

PowerlineHeader {
    dock: top;
    height: 1;
    layout: horizontal;
}

PowerlineHeader #header-left {
    width: auto;
}

PowerlineHeader #header-time {
    width: 1fr;
    text-align: right;
    padding-right: 1;
}

PowerlineFooter {
    dock: bottom;
    height: 1;
}

PowerlineFooter #footer-content {
    width: 100%;
    text-align: right;
}

PowerlineBreadcrumb {
    height: 1;
    padding: 0 1;
}

/* ----------------------------------------------------------------------------
   SPINNER WIDGETS
   ---------------------------------------------------------------------------- */

SpinnerWidget {
    width: auto;
    height: 1;
    padding: 0 1;
}

SpinnerWidget.centered {
    width: 100%;
    text-align: center;
}

/* ----------------------------------------------------------------------------
   BLINKER / CURSOR
   ---------------------------------------------------------------------------- */

Blinker {
    width: 1;
    height: 1;
}

InputCursor {
    height: 1;
    padding: 0 1;
}
```

### 7.3 Exemplo de Uso Completo

```python
# Exemplo: main_screen.py com Powerline e Spinners

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Vertical, Horizontal

from tui_app.widgets import (
    PowerlineHeader,
    PowerlineFooter,
    PowerlineSegment,
    PowerlineBreadcrumb,
    SpinnerWidget,
    LogPanel,
    PipelineProgress,
)


class MainScreen(Screen):
    """Tela principal com elementos Powerline."""
    
    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }
    
    #content {
        height: 1fr;
    }
    
    #status-row {
        height: 1;
        layout: horizontal;
    }
    """
    
    def compose(self) -> ComposeResult:
        # Header Powerline
        yield PowerlineHeader(
            app_name="VIBE-LOG",
            version="0.8.5",
            show_time=True,
        )
        
        # Breadcrumb
        yield PowerlineBreadcrumb(
            items=["Home", "Documents", "projeto.pdf"],
        )
        
        # Conteúdo principal
        with Vertical(id="content"):
            # Linha de status com spinners
            with Horizontal(id="status-row"):
                yield SpinnerWidget(
                    "claude",
                    source="custom",
                    text="Processando...",
                    style="cyan",
                )
            
            # Widgets principais
            yield PipelineProgress(
                stages=["Cartógrafo", "Saneador", "Extrator", "Bibliotecário"],
            )
            yield LogPanel()
        
        # Footer Powerline
        yield PowerlineFooter(
            segments=[
                PowerlineSegment("Ready", fg="black", bg="green"),
                PowerlineSegment("UTF-8", fg="white", bg="blue"),
                PowerlineSegment("Python", fg="black", bg="yellow"),
            ]
        )
```

---

## Referência Rápida de Spinners

### Por Categoria

**Braille (Claude-style):**
- `dots` - ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏
- `dots2` - ⣾⣽⣻⢿⡿⣟⣯⣷
- `claude` (custom) - ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏

**Barras:**
- `aesthetic` - ▰▱▱▱▱▱▱
- `bouncingBar` - [=   ]
- `pulse_bar` (custom) - █▒▒▒▒▒▒▒▒▒

**Geométricos:**
- `arc` - ◜◠◝◞◡◟
- `circle` - ◡⊙◠
- `neon` (custom) - ◐◓◑◒

**Waves:**
- `material` - █▁▂▃▄▅▆▇
- `wave` (custom) - ▁▂▃▄▅▆▇█

**Clássicos:**
- `line` - -\|/
- `toggle` - ⊶⊷

---

## Checklist de Implementação

- [ ] Instalar Nerd Font no sistema
- [ ] Configurar Windows Terminal com a fonte
- [ ] Adicionar arquivos de spinners ao projeto
- [ ] Adicionar arquivos de blinker ao projeto  
- [ ] Adicionar arquivos de powerline ao projeto
- [ ] Atualizar `__init__.py` com exports
- [ ] Adicionar CSS para novos widgets
- [ ] Testar renderização de caracteres Powerline
- [ ] Verificar fallback para terminais sem Nerd Fonts

---

*Extensão do TUI Template v1.0*
*Requer Nerd Fonts para caracteres Powerline*
