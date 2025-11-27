# TUI Template Specification v1.0

> Template "maximalista" para criação de TUIs com Textual (Python)
> Baseado na estética VIBE-LOG / Cyberpunk com tema Dracula

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Estrutura de Diretórios](#2-estrutura-de-diretórios)
3. [Configuração do Projeto](#3-configuração-do-projeto)
4. [Sistema de Temas](#4-sistema-de-temas)
5. [Estilos CSS](#5-estilos-css)
6. [Widgets Customizados](#6-widgets-customizados)
7. [Screens](#7-screens)
8. [Sistema de Mensagens](#8-sistema-de-mensagens)
9. [Workers e Pipeline](#9-workers-e-pipeline)
10. [Modelos de Dados](#10-modelos-de-dados)
11. [Utilitários](#11-utilitários)
12. [Testes](#12-testes)
13. [Guia de Customização](#13-guia-de-customização)

---

## 1. Visão Geral

### 1.1 Propósito

Este template fornece uma base completa para criar TUIs profissionais com:

- **Estética VIBE-LOG**: Cores neon, bordas brilhantes, visual cyberpunk
- **Arquitetura Modular**: Separação clara entre UI, lógica e dados
- **Workers Assíncronos**: UI nunca trava, mesmo com operações pesadas
- **Sistema de Temas**: Troca de visual sem alterar código
- **Widgets Reutilizáveis**: Componentes prontos para logs, progresso, arquivos

### 1.2 Stack Tecnológico

| Componente | Tecnologia | Versão Mínima |
|------------|------------|---------------|
| Framework TUI | Textual | 0.80.0 |
| Rich Text | Rich | 13.0.0 |
| Validação | Pydantic | 2.0.0 |
| Python | CPython | 3.11 |

### 1.3 Filosofia de Design

```
┌─────────────────────────────────────────────────────────────┐
│                      MAXIMALISTA                            │
│                                                             │
│   "Inclua tudo. Remova o que não precisar."                │
│                                                             │
│   - Melhor ter e não usar do que precisar e não ter        │
│   - Código comentado é documentação viva                    │
│   - Cada widget é independente e reutilizável              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Estrutura de Diretórios

```
tui-template/
│
├── pyproject.toml                    # Configuração do projeto
├── README.md                         # Documentação principal
├── CHANGELOG.md                      # Histórico de versões
├── .gitignore                        # Ignores padrão
│
├── src/
│   └── tui_app/                      # Pacote principal
│       │
│       ├── __init__.py               # Metadata e versão
│       ├── __main__.py               # Entry point CLI
│       ├── app.py                    # Classe App principal
│       ├── config.py                 # Configurações e constantes
│       │
│       ├── screens/                  # Telas da aplicação
│       │   ├── __init__.py
│       │   ├── main_screen.py        # Dashboard principal
│       │   ├── log_screen.py         # Logs fullscreen
│       │   ├── settings_screen.py    # Configurações
│       │   └── help_screen.py        # Ajuda e keybindings
│       │
│       ├── widgets/                  # Widgets customizados
│       │   ├── __init__.py
│       │   ├── header.py             # Header com logo ASCII
│       │   ├── sidebar.py            # Menu lateral
│       │   ├── log_panel.py          # RichLog estilizado
│       │   ├── progress_panel.py     # Multi-progress
│       │   ├── status_bar.py         # CPU, RAM, tempo
│       │   ├── file_browser.py       # DirectoryTree filtrado
│       │   ├── result_viewer.py      # Markdown viewer
│       │   └── sparkline_panel.py    # Mini-gráficos
│       │
│       ├── components/               # Widgets compostos
│       │   ├── __init__.py
│       │   ├── pipeline_tracker.py   # Tracker de pipeline
│       │   └── action_bar.py         # Barra de ações
│       │
│       ├── themes/                   # Sistema de temas
│       │   ├── __init__.py           # Exporta temas
│       │   ├── base.py               # ThemeBase abstrato
│       │   ├── vibe_neon.py          # Cyberpunk (Dracula)
│       │   ├── vibe_matrix.py        # Matrix verde
│       │   ├── vibe_synthwave.py     # Rosa/roxo
│       │   ├── minimal_dark.py       # Minimalista escuro
│       │   └── minimal_light.py      # Minimalista claro
│       │
│       ├── styles/                   # CSS externo
│       │   ├── base.tcss             # Variáveis e reset
│       │   ├── layout.tcss           # Grid e containers
│       │   ├── widgets.tcss          # Estilos de widgets
│       │   ├── animations.tcss       # Spinners e transições
│       │   └── themes/               # CSS por tema
│       │       ├── vibe_neon.tcss
│       │       ├── vibe_matrix.tcss
│       │       └── ...
│       │
│       ├── workers/                  # Workers assíncronos
│       │   ├── __init__.py
│       │   ├── base_worker.py        # Classe base
│       │   └── pipeline_worker.py    # Executor de pipeline
│       │
│       ├── messages/                 # Custom messages
│       │   ├── __init__.py
│       │   ├── pipeline_messages.py  # Eventos de pipeline
│       │   └── system_messages.py    # Eventos de sistema
│       │
│       ├── models/                   # Modelos Pydantic
│       │   ├── __init__.py
│       │   ├── pipeline.py           # Config de pipeline
│       │   ├── log_entry.py          # Entrada de log
│       │   └── settings.py           # Configurações app
│       │
│       ├── services/                 # Lógica de negócio
│       │   ├── __init__.py
│       │   ├── pipeline_service.py   # Interface de pipeline
│       │   └── settings_service.py   # Persistência
│       │
│       ├── adapters/                 # Adaptadores IPC
│       │   ├── __init__.py
│       │   ├── local_adapter.py      # Via Workers
│       │   └── websocket_adapter.py  # Via WebSocket
│       │
│       └── utils/                    # Utilitários
│           ├── __init__.py
│           ├── ascii_art.py          # Logos ASCII
│           ├── formatting.py         # Formatação
│           └── validators.py         # Validação
│
├── assets/                           # Recursos estáticos
│   ├── fonts/
│   │   └── README.md                 # Instruções Nerd Fonts
│   └── logos/
│       ├── logo_small.txt
│       └── logo_large.txt
│
├── tests/                            # Testes
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_app.py
│   ├── test_widgets/
│   └── test_workers/
│
├── scripts/                          # Scripts auxiliares
│   ├── run_dev.sh
│   ├── run_prod.sh
│   └── generate_logo.py
│
└── docs/                             # Documentação
    ├── getting_started.md
    ├── customization.md
    └── architecture.md
```

---

## 3. Configuração do Projeto

### 3.1 pyproject.toml

```toml
[project]
name = "tui-template"
version = "0.1.0"
description = "Template maximalista para TUIs com Textual"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [
    {name = "Seu Nome", email = "email@exemplo.com"}
]
keywords = ["tui", "terminal", "textual", "cli"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Framework :: Textual",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Terminals",
]

dependencies = [
    "textual>=0.80.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "textual-dev>=1.0.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
websocket = [
    "websockets>=12.0",
    "httpx>=0.27.0",
]
all = [
    "tui-template[dev,websocket]",
]

[project.scripts]
tui-app = "tui_app.__main__:main"

[project.urls]
Homepage = "https://github.com/usuario/tui-template"
Documentation = "https://github.com/usuario/tui-template#readme"
Repository = "https://github.com/usuario/tui-template.git"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/tui_app"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=tui_app --cov-report=term-missing"
```

### 3.2 src/tui_app/__init__.py

```python
"""
TUI Template - Framework para criação de TUIs com Textual.

Este pacote fornece:
- Widgets customizados para logs, progresso, navegação
- Sistema de temas (VIBE neon, Matrix, Synthwave, etc.)
- Workers assíncronos para operações pesadas
- Arquitetura modular e extensível
"""

__version__ = "0.1.0"
__author__ = "Seu Nome"

from tui_app.app import TUIApp

__all__ = ["TUIApp", "__version__"]
```

### 3.3 src/tui_app/__main__.py

```python
"""
Entry point para execução via: python -m tui_app

Uso:
    python -m tui_app              # Execução normal
    python -m tui_app --dev        # Modo desenvolvimento
    python -m tui_app --theme nord # Tema específico
"""

import argparse
import sys

from tui_app.app import TUIApp


def parse_args() -> argparse.Namespace:
    """Parse argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        prog="tui-app",
        description="TUI Template Application",
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="vibe-neon",
        help="Tema inicial (vibe-neon, vibe-matrix, minimal-dark, etc.)",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Modo desenvolvimento (hot-reload CSS)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {TUIApp.__version__}",
    )
    return parser.parse_args()


def main() -> int:
    """Função principal."""
    args = parse_args()
    
    app = TUIApp(initial_theme=args.theme)
    app.run()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 3.4 src/tui_app/config.py

```python
"""
Configurações centralizadas da aplicação.

Usa paths absolutos baseados em __file__ para evitar erros no WSL2.
"""

from pathlib import Path
from typing import Final

# =============================================================================
# PATHS
# =============================================================================

# Raiz do pacote
PACKAGE_ROOT: Final[Path] = Path(__file__).parent.resolve()

# Diretórios de recursos
STYLES_DIR: Final[Path] = PACKAGE_ROOT / "styles"
THEMES_DIR: Final[Path] = STYLES_DIR / "themes"
ASSETS_DIR: Final[Path] = PACKAGE_ROOT.parent.parent / "assets"
LOGOS_DIR: Final[Path] = ASSETS_DIR / "logos"

# =============================================================================
# CONSTANTES DA APLICAÇÃO
# =============================================================================

APP_NAME: Final[str] = "TUI Template"
APP_VERSION: Final[str] = "0.1.0"

# =============================================================================
# CONFIGURAÇÕES DE UI
# =============================================================================

# Limites de log
MAX_LOG_LINES: Final[int] = 10_000
LOG_BUFFER_SIZE: Final[int] = 100

# Taxa de atualização (ms)
REFRESH_RATE_MS: Final[int] = 50  # 20 FPS

# Timeout para operações (segundos)
OPERATION_TIMEOUT_S: Final[int] = 300  # 5 minutos

# =============================================================================
# KEYBINDINGS PADRÃO
# =============================================================================

DEFAULT_BINDINGS: Final[dict[str, tuple[str, str]]] = {
    "quit": ("q", "Sair"),
    "help": ("?", "Ajuda"),
    "toggle_dark": ("d", "Tema"),
    "toggle_sidebar": ("b", "Sidebar"),
    "focus_log": ("l", "Logs"),
    "focus_progress": ("p", "Progresso"),
    "run": ("r", "Executar"),
    "cancel": ("escape", "Cancelar"),
    "command_palette": ("ctrl+p", "Comandos"),
}

# =============================================================================
# CORES (para referência rápida)
# =============================================================================

class Colors:
    """Paleta de cores padrão (Dracula-based)."""
    
    # Backgrounds
    VOID_BG = "#0d0d0d"
    SURFACE_BG = "#1a1a2e"
    PANEL_BG = "#16213e"
    ELEVATED_BG = "#1f2937"
    
    # Neon
    NEON_CYAN = "#8be9fd"
    NEON_MAGENTA = "#ff79c6"
    NEON_GREEN = "#50fa7b"
    NEON_YELLOW = "#f1fa8c"
    NEON_ORANGE = "#ffb86c"
    NEON_RED = "#ff5555"
    NEON_PURPLE = "#bd93f9"
    
    # Text
    TEXT_PRIMARY = "#f8f8f2"
    TEXT_MUTED = "#6272a4"
    TEXT_DISABLED = "#44475a"
    
    # Borders
    BORDER_GLOW = NEON_CYAN
    BORDER_MUTED = "#44475a"
```

### 3.5 src/tui_app/app.py

```python
"""
Aplicação TUI principal.

Esta é a classe App que coordena toda a aplicação:
- Registra e gerencia temas
- Define keybindings globais
- Gerencia screens
- Processa mensagens
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen

from tui_app.config import APP_NAME, APP_VERSION, STYLES_DIR
from tui_app.themes import (
    VIBE_NEON_THEME,
    VIBE_MATRIX_THEME,
    VIBE_SYNTHWAVE_THEME,
    MINIMAL_DARK_THEME,
    MINIMAL_LIGHT_THEME,
)
from tui_app.screens.main_screen import MainScreen
from tui_app.screens.help_screen import HelpScreen
from tui_app.messages.pipeline_messages import (
    PipelineStarted,
    StepStarted,
    StepProgress,
    StepCompleted,
    StepError,
    PipelineCompleted,
    PipelineAborted,
)
from tui_app.messages.system_messages import LogMessage


class TUIApp(App):
    """
    Aplicação TUI Template.
    
    Attributes:
        TITLE: Título exibido no header
        SUB_TITLE: Subtítulo com versão
        CSS_PATH: Lista de arquivos CSS a carregar
        BINDINGS: Keybindings globais
        SCREENS: Screens disponíveis
    """
    
    TITLE = APP_NAME
    SUB_TITLE = f"v{APP_VERSION}"
    
    CSS_PATH = [
        STYLES_DIR / "base.tcss",
        STYLES_DIR / "layout.tcss",
        STYLES_DIR / "widgets.tcss",
        STYLES_DIR / "animations.tcss",
    ]
    
    BINDINGS = [
        # Navegação
        Binding("q", "quit", "Sair", show=True, priority=True),
        Binding("?", "show_help", "Ajuda", show=True),
        Binding("d", "toggle_dark", "Tema", show=True),
        
        # Controle
        Binding("r", "run_pipeline", "Executar", show=True),
        Binding("escape", "cancel_operation", "Cancelar", show=False),
        
        # Navegação de painéis
        Binding("b", "toggle_sidebar", "Sidebar", show=False),
        Binding("l", "focus_log", "Logs", show=False),
        Binding("p", "focus_progress", "Progresso", show=False),
        
        # Sistema
        Binding("ctrl+p", "command_palette", "Comandos", show=False),
        Binding("ctrl+s", "screenshot", "Screenshot", show=False),
    ]
    
    SCREENS = {
        "main": MainScreen,
        "help": HelpScreen,
    }
    
    def __init__(self, initial_theme: str = "vibe-neon") -> None:
        """
        Inicializa a aplicação.
        
        Args:
            initial_theme: Nome do tema inicial
        """
        super().__init__()
        self._initial_theme = initial_theme
    
    def on_mount(self) -> None:
        """Configuração inicial ao montar a aplicação."""
        # Registra todos os temas disponíveis
        self.register_theme(VIBE_NEON_THEME)
        self.register_theme(VIBE_MATRIX_THEME)
        self.register_theme(VIBE_SYNTHWAVE_THEME)
        self.register_theme(MINIMAL_DARK_THEME)
        self.register_theme(MINIMAL_LIGHT_THEME)
        
        # Aplica tema inicial
        self.theme = self._initial_theme
        
        # Carrega screen principal
        self.push_screen("main")
    
    # =========================================================================
    # ACTIONS
    # =========================================================================
    
    def action_toggle_dark(self) -> None:
        """Alterna entre tema escuro e claro."""
        if self.theme in ("vibe-neon", "vibe-matrix", "vibe-synthwave", "minimal-dark"):
            self.theme = "minimal-light"
        else:
            self.theme = "vibe-neon"
    
    def action_show_help(self) -> None:
        """Exibe tela de ajuda."""
        self.push_screen("help")
    
    def action_toggle_sidebar(self) -> None:
        """Alterna visibilidade da sidebar."""
        screen = self.screen
        if hasattr(screen, "toggle_sidebar"):
            screen.toggle_sidebar()
    
    def action_focus_log(self) -> None:
        """Foca no painel de logs."""
        try:
            self.screen.query_one("#log-panel").focus()
        except Exception:
            pass
    
    def action_focus_progress(self) -> None:
        """Foca no painel de progresso."""
        try:
            self.screen.query_one("#progress-panel").focus()
        except Exception:
            pass
    
    def action_run_pipeline(self) -> None:
        """Inicia execução da pipeline."""
        screen = self.screen
        if hasattr(screen, "run_pipeline"):
            screen.run_pipeline()
    
    def action_cancel_operation(self) -> None:
        """Cancela operação em andamento."""
        screen = self.screen
        if hasattr(screen, "cancel_operation"):
            screen.cancel_operation()
    
    def action_screenshot(self) -> None:
        """Salva screenshot da aplicação."""
        self.save_screenshot()
    
    # =========================================================================
    # MESSAGE HANDLERS
    # =========================================================================
    
    def on_log_message(self, message: LogMessage) -> None:
        """Processa mensagem de log."""
        # Propaga para screen atual processar
        pass
    
    def on_pipeline_started(self, message: PipelineStarted) -> None:
        """Pipeline iniciou."""
        self.notify(f"Pipeline iniciada com {message.total_steps} etapas")
    
    def on_pipeline_completed(self, message: PipelineCompleted) -> None:
        """Pipeline completou com sucesso."""
        self.notify("Pipeline concluída com sucesso!", severity="information")
    
    def on_pipeline_aborted(self, message: PipelineAborted) -> None:
        """Pipeline foi abortada."""
        self.notify(f"Pipeline abortada: {message.reason}", severity="error")
    
    def on_step_error(self, message: StepError) -> None:
        """Erro em um step da pipeline."""
        self.notify(f"Erro no step {message.step}: {message.error}", severity="error")
```

---

## 4. Sistema de Temas

### 4.1 src/tui_app/themes/__init__.py

```python
"""
Sistema de temas do TUI Template.

Temas disponíveis:
- vibe-neon: Cyberpunk com cores Dracula (padrão)
- vibe-matrix: Verde matrix sobre preto
- vibe-synthwave: Rosa e roxo synthwave
- minimal-dark: Minimalista escuro
- minimal-light: Minimalista claro

Uso:
    from tui_app.themes import VIBE_NEON_THEME
    app.register_theme(VIBE_NEON_THEME)
    app.theme = "vibe-neon"
"""

from tui_app.themes.vibe_neon import VIBE_NEON_THEME
from tui_app.themes.vibe_matrix import VIBE_MATRIX_THEME
from tui_app.themes.vibe_synthwave import VIBE_SYNTHWAVE_THEME
from tui_app.themes.minimal_dark import MINIMAL_DARK_THEME
from tui_app.themes.minimal_light import MINIMAL_LIGHT_THEME

__all__ = [
    "VIBE_NEON_THEME",
    "VIBE_MATRIX_THEME",
    "VIBE_SYNTHWAVE_THEME",
    "MINIMAL_DARK_THEME",
    "MINIMAL_LIGHT_THEME",
]

# Mapa de temas por nome
THEMES = {
    "vibe-neon": VIBE_NEON_THEME,
    "vibe-matrix": VIBE_MATRIX_THEME,
    "vibe-synthwave": VIBE_SYNTHWAVE_THEME,
    "minimal-dark": MINIMAL_DARK_THEME,
    "minimal-light": MINIMAL_LIGHT_THEME,
}
```

### 4.2 src/tui_app/themes/vibe_neon.py

```python
"""
Tema VIBE Neon - Cyberpunk inspirado em Dracula.

Paleta de cores:
- Background: Preto profundo (#0d0d0d)
- Primary: Cyan neon (#8be9fd)
- Accent: Magenta neon (#ff79c6)
- Success: Verde neon (#50fa7b)
- Warning: Laranja (#ffb86c)
- Error: Vermelho (#ff5555)
"""

from textual.theme import Theme

VIBE_NEON_THEME = Theme(
    name="vibe-neon",
    
    # Cores principais
    primary="#8be9fd",      # Cyan neon (destaque principal)
    secondary="#bd93f9",    # Roxo (destaque secundário)
    accent="#ff79c6",       # Magenta neon (ações, links)
    
    # Texto
    foreground="#f8f8f2",   # Texto principal (quase branco)
    
    # Backgrounds (do mais escuro ao mais claro)
    background="#0d0d0d",   # Void black (fundo da tela)
    surface="#1a1a2e",      # Surface (fundo de widgets)
    panel="#16213e",        # Painéis elevados
    
    # Semânticas
    success="#50fa7b",      # Verde neon (sucesso)
    warning="#ffb86c",      # Laranja (aviso)
    error="#ff5555",        # Vermelho (erro)
    
    # Modo escuro
    dark=True,
    
    # Variáveis customizadas
    variables={
        # Cursor de bloco (OptionList, DataTable, etc.)
        "block-cursor-background": "#ff79c6",
        "block-cursor-foreground": "#0d0d0d",
        "block-cursor-text-style": "bold",
        "block-cursor-blurred-background": "#ff79c6 30%",
        "block-cursor-blurred-foreground": "#f8f8f2",
        "block-cursor-blurred-text-style": "none",
        "block-hover-background": "#44475a 30%",
        
        # Bordas
        "border": "#8be9fd",
        "border-blurred": "#44475a",
        
        # Footer
        "footer-background": "#1a1a2e",
        "footer-foreground": "#f8f8f2",
        "footer-key-foreground": "#50fa7b",
        "footer-key-background": "transparent",
        "footer-description-foreground": "#f8f8f2",
        "footer-description-background": "transparent",
        
        # Scrollbar
        "scrollbar": "#44475a",
        "scrollbar-hover": "#6272a4",
        "scrollbar-active": "#8be9fd",
        "scrollbar-background": "#0d0d0d",
        
        # Input
        "input-cursor-background": "#f8f8f2",
        "input-cursor-foreground": "#0d0d0d",
        "input-selection-background": "#44475a 60%",
        
        # Links
        "link-color": "#8be9fd",
        "link-color-hover": "#ff79c6",
        "link-style": "underline",
        "link-style-hover": "bold",
        
        # Botões
        "button-foreground": "#f8f8f2",
        "button-color-foreground": "#0d0d0d",
        "button-focus-text-style": "bold reverse",
    },
)
```

### 4.3 src/tui_app/themes/vibe_matrix.py

```python
"""
Tema VIBE Matrix - Verde clássico sobre preto.

Inspirado no visual do filme Matrix.
"""

from textual.theme import Theme

VIBE_MATRIX_THEME = Theme(
    name="vibe-matrix",
    
    primary="#00ff41",      # Verde matrix
    secondary="#008f11",    # Verde escuro
    accent="#00ff41",       # Verde brilhante
    foreground="#00ff41",   # Texto verde
    background="#000000",   # Preto puro
    surface="#0a0a0a",      # Quase preto
    panel="#111111",        # Cinza muito escuro
    success="#00ff41",      # Verde
    warning="#ffff00",      # Amarelo
    error="#ff0000",        # Vermelho
    
    dark=True,
    
    variables={
        "block-cursor-background": "#00ff41",
        "block-cursor-foreground": "#000000",
        "border": "#00ff41",
        "border-blurred": "#008f11",
        "footer-key-foreground": "#00ff41",
        "scrollbar": "#008f11",
        "scrollbar-hover": "#00ff41",
        "scrollbar-active": "#00ff41",
        "input-selection-background": "#00ff41 30%",
    },
)
```

### 4.4 src/tui_app/themes/vibe_synthwave.py

```python
"""
Tema VIBE Synthwave - Rosa e roxo neon.

Inspirado na estética synthwave/retrowave dos anos 80.
"""

from textual.theme import Theme

VIBE_SYNTHWAVE_THEME = Theme(
    name="vibe-synthwave",
    
    primary="#ff00ff",      # Magenta
    secondary="#00ffff",    # Cyan
    accent="#ff6ad5",       # Rosa
    foreground="#ffffff",   # Branco
    background="#1a0a2e",   # Roxo escuro
    surface="#2d1b4e",      # Roxo médio
    panel="#3d2a5c",        # Roxo mais claro
    success="#00ff87",      # Verde neon
    warning="#ffd700",      # Dourado
    error="#ff1493",        # Rosa choque
    
    dark=True,
    
    variables={
        "block-cursor-background": "#ff00ff",
        "block-cursor-foreground": "#000000",
        "border": "#ff00ff",
        "border-blurred": "#6b3a8c",
        "footer-key-foreground": "#00ffff",
        "scrollbar": "#6b3a8c",
        "scrollbar-hover": "#ff00ff",
        "scrollbar-active": "#ff6ad5",
        "input-selection-background": "#ff00ff 30%",
    },
)
```

### 4.5 src/tui_app/themes/minimal_dark.py

```python
"""
Tema Minimal Dark - Escuro e limpo.

Para quem prefere menos distração visual.
"""

from textual.theme import Theme

MINIMAL_DARK_THEME = Theme(
    name="minimal-dark",
    
    primary="#6699cc",      # Azul suave
    secondary="#99ccff",    # Azul claro
    accent="#6699cc",       # Azul
    foreground="#c0c5ce",   # Cinza claro
    background="#1b2b34",   # Azul muito escuro
    surface="#243b47",      # Azul escuro
    panel="#2d4a5a",        # Azul médio
    success="#99c794",      # Verde suave
    warning="#fac863",      # Amarelo suave
    error="#ec5f67",        # Vermelho suave
    
    dark=True,
    
    variables={
        "block-cursor-background": "#6699cc",
        "block-cursor-foreground": "#1b2b34",
        "border": "#6699cc",
        "border-blurred": "#4a6477",
        "footer-key-foreground": "#99c794",
        "scrollbar": "#4a6477",
        "scrollbar-hover": "#6699cc",
    },
)
```

### 4.6 src/tui_app/themes/minimal_light.py

```python
"""
Tema Minimal Light - Claro e limpo.

Para ambientes com muita luz ou preferência pessoal.
"""

from textual.theme import Theme

MINIMAL_LIGHT_THEME = Theme(
    name="minimal-light",
    
    primary="#1a73e8",      # Azul Google
    secondary="#5094ed",    # Azul claro
    accent="#1a73e8",       # Azul
    foreground="#202124",   # Quase preto
    background="#ffffff",   # Branco
    surface="#f8f9fa",      # Cinza muito claro
    panel="#e8eaed",        # Cinza claro
    success="#34a853",      # Verde Google
    warning="#fbbc04",      # Amarelo Google
    error="#ea4335",        # Vermelho Google
    
    dark=False,
    
    variables={
        "block-cursor-background": "#1a73e8",
        "block-cursor-foreground": "#ffffff",
        "border": "#1a73e8",
        "border-blurred": "#dadce0",
        "footer-background": "#f8f9fa",
        "footer-foreground": "#202124",
        "footer-key-foreground": "#1a73e8",
        "scrollbar": "#dadce0",
        "scrollbar-hover": "#bdc1c6",
    },
)
```

---

## 5. Estilos CSS

### 5.1 src/tui_app/styles/base.tcss

```css
/* ============================================================================
   BASE STYLES
   Variáveis globais, reset e estilos fundamentais
   ============================================================================ */

/* ----------------------------------------------------------------------------
   VARIÁVEIS NEON (complementam as variáveis do tema)
   ---------------------------------------------------------------------------- */

$neon-cyan: #8be9fd;
$neon-magenta: #ff79c6;
$neon-green: #50fa7b;
$neon-yellow: #f1fa8c;
$neon-orange: #ffb86c;
$neon-red: #ff5555;
$neon-purple: #bd93f9;

/* Backgrounds auxiliares */
$void-bg: #0d0d0d;
$surface-bg: #1a1a2e;
$panel-bg: #16213e;
$elevated-bg: #1f2937;

/* Bordas */
$border-glow: $neon-cyan;
$border-muted: #44475a;

/* Texto */
$text-bright: #ffffff;
$text-muted: #6272a4;
$text-dim: #44475a;

/* ----------------------------------------------------------------------------
   RESET E DEFAULTS GLOBAIS
   ---------------------------------------------------------------------------- */

Screen {
    background: $background;
    color: $foreground;
}

/* Scrollbars consistentes em toda a aplicação */
* {
    scrollbar-background: $background-darken-1;
    scrollbar-color: $panel;
    scrollbar-color-hover: $primary;
    scrollbar-color-active: $accent;
    scrollbar-size: 1 1;
}

/* Links */
.link {
    color: $primary;
    text-style: underline;
}

.link:hover {
    color: $accent;
    text-style: bold;
}

/* Texto muted */
.muted {
    color: $foreground-muted;
}

/* Texto de erro */
.error-text {
    color: $error;
}

/* Texto de sucesso */
.success-text {
    color: $success;
}

/* Texto de warning */
.warning-text {
    color: $warning;
}

/* ----------------------------------------------------------------------------
   CLASSES UTILITÁRIAS
   ---------------------------------------------------------------------------- */

/* Padding */
.p-0 { padding: 0; }
.p-1 { padding: 1; }
.p-2 { padding: 2; }

/* Margin */
.m-0 { margin: 0; }
.m-1 { margin: 1; }
.m-2 { margin: 2; }

/* Hidden */
.hidden {
    display: none;
}

/* Full width/height */
.full-width {
    width: 100%;
}

.full-height {
    height: 100%;
}

/* Centralization */
.center {
    align: center middle;
}

.center-horizontal {
    align: center top;
}

.center-vertical {
    align: left middle;
}
```

### 5.2 src/tui_app/styles/layout.tcss

```css
/* ============================================================================
   LAYOUT STYLES
   Grid, containers, dock e estrutura de telas
   ============================================================================ */

/* ----------------------------------------------------------------------------
   MAIN SCREEN LAYOUT
   ---------------------------------------------------------------------------- */

#main-screen {
    layout: grid;
    grid-size: 2 1;
    grid-columns: auto 1fr;
    grid-rows: 1fr;
}

/* Sidebar */
#sidebar {
    width: 30;
    height: 100%;
    dock: left;
    background: $surface;
    border-right: heavy $border;
}

#sidebar.collapsed {
    display: none;
}

/* Content area */
#content-area {
    width: 100%;
    height: 100%;
    layout: grid;
    grid-size: 1 2;
    grid-rows: auto 1fr;
}

/* Top section (progress) */
#top-section {
    height: auto;
    max-height: 15;
    padding: 1;
}

/* Bottom section (logs + results) */
#bottom-section {
    height: 100%;
    layout: grid;
    grid-size: 2 1;
    grid-columns: 1fr 1fr;
    padding: 1;
}

/* Single column mode (for smaller terminals) */
#bottom-section.single-column {
    grid-size: 1 1;
}

/* ----------------------------------------------------------------------------
   PANELS
   ---------------------------------------------------------------------------- */

.panel {
    border: heavy $border;
    border-title-color: $primary;
    border-title-style: bold;
    background: $surface;
    padding: 0 1;
}

.panel:focus {
    border: heavy $accent;
    border-title-color: $accent;
}

.panel:focus-within {
    border: heavy $primary-lighten-1;
}

/* Panel com glow effect */
.panel-glow {
    border: heavy $accent;
    border-title-color: $accent;
}

/* Panel elevado */
.panel-elevated {
    background: $panel;
}

/* ----------------------------------------------------------------------------
   HEADER & FOOTER
   ---------------------------------------------------------------------------- */

/* Custom header */
#custom-header {
    dock: top;
    height: auto;
    background: $surface;
    border-bottom: heavy $border;
    padding: 0 1;
}

/* Custom footer */
#custom-footer {
    dock: bottom;
    height: 1;
    background: $panel;
}

/* ----------------------------------------------------------------------------
   MODAL & OVERLAY
   ---------------------------------------------------------------------------- */

.modal-overlay {
    align: center middle;
    background: $background 80%;
}

.modal-container {
    width: 60%;
    height: auto;
    max-height: 80%;
    background: $surface;
    border: heavy $accent;
    padding: 1 2;
}

/* ----------------------------------------------------------------------------
   RESPONSIVE (based on terminal size)
   ---------------------------------------------------------------------------- */

/* Telas pequenas: single column */
@media (width < 100) {
    #bottom-section {
        grid-size: 1 2;
        grid-rows: 1fr 1fr;
        grid-columns: 1fr;
    }
    
    #sidebar {
        width: 25;
    }
}

/* Telas muito pequenas: sem sidebar */
@media (width < 80) {
    #sidebar {
        display: none;
    }
}
```

### 5.3 src/tui_app/styles/widgets.tcss

```css
/* ============================================================================
   WIDGET STYLES
   Estilos específicos para widgets customizados
   ============================================================================ */

/* ----------------------------------------------------------------------------
   LOG PANEL
   ---------------------------------------------------------------------------- */

LogPanel {
    border: heavy $border;
    border-title-color: $primary;
    background: $surface;
    padding: 0 1;
}

LogPanel:focus {
    border: heavy $accent;
    border-title-color: $accent;
}

/* Log levels */
.log-info {
    color: $primary;
}

.log-warning {
    color: $warning;
}

.log-error {
    color: $error;
    text-style: bold;
}

.log-success {
    color: $success;
}

.log-debug {
    color: $foreground-muted;
    text-style: italic;
}

/* Timestamp */
.log-timestamp {
    color: $foreground-muted;
}

/* ----------------------------------------------------------------------------
   PROGRESS PANEL
   ---------------------------------------------------------------------------- */

PipelineProgress {
    border: heavy $border;
    border-title-color: $primary;
    background: $surface;
    height: auto;
    padding: 1;
}

StageProgress {
    height: 3;
    padding: 0 1;
}

StageProgress .stage-label {
    text-style: bold;
    width: 100%;
}

StageProgress ProgressBar {
    width: 100%;
    padding-top: 1;
}

StageProgress ProgressBar > .bar--bar {
    color: $primary;
}

StageProgress ProgressBar > .bar--complete {
    color: $success;
}

/* Status classes */
StageProgress.pending .stage-label {
    color: $foreground-muted;
}

StageProgress.running .stage-label {
    color: $accent;
}

StageProgress.completed .stage-label {
    color: $success;
}

StageProgress.error .stage-label {
    color: $error;
}

/* ----------------------------------------------------------------------------
   SIDEBAR
   ---------------------------------------------------------------------------- */

Sidebar {
    width: 30;
    background: $surface;
    border-right: heavy $border;
}

Sidebar:focus-within {
    border-right: heavy $accent;
}

Sidebar #sidebar-title {
    text-align: center;
    text-style: bold;
    color: $accent;
    padding: 1;
    border-bottom: solid $border-blurred;
}

Sidebar OptionList {
    background: transparent;
    padding: 0;
}

Sidebar OptionList > .option-list--option {
    padding: 0 1;
}

Sidebar OptionList > .option-list--option-highlighted {
    background: $primary 20%;
}

/* ----------------------------------------------------------------------------
   FILE BROWSER
   ---------------------------------------------------------------------------- */

FileBrowser {
    border: heavy $border;
    border-title-color: $primary;
    background: $surface;
}

FileBrowser:focus {
    border: heavy $accent;
}

FileBrowser DirectoryTree {
    background: transparent;
    padding: 0 1;
}

FileBrowser .directory-tree--folder {
    color: $primary;
}

FileBrowser .directory-tree--file {
    color: $foreground;
}

FileBrowser .directory-tree--extension {
    color: $foreground-muted;
}

/* Highlight para arquivos PDF */
FileBrowser .file-pdf {
    color: $error;
    text-style: bold;
}

/* ----------------------------------------------------------------------------
   RESULT VIEWER
   ---------------------------------------------------------------------------- */

ResultViewer {
    border: heavy $border;
    border-title-color: $primary;
    background: $surface;
}

ResultViewer:focus {
    border: heavy $accent;
}

ResultViewer Markdown {
    background: transparent;
    padding: 1;
}

/* ----------------------------------------------------------------------------
   STATUS BAR
   ---------------------------------------------------------------------------- */

StatusBar {
    height: 1;
    background: $panel;
    color: $foreground;
    padding: 0 1;
}

StatusBar .status-item {
    margin-right: 2;
}

StatusBar .status-label {
    color: $foreground-muted;
}

StatusBar .status-value {
    color: $primary;
    text-style: bold;
}

StatusBar .status-warning {
    color: $warning;
}

StatusBar .status-error {
    color: $error;
}

/* ----------------------------------------------------------------------------
   SPARKLINE
   ---------------------------------------------------------------------------- */

SparklinePanel {
    height: 4;
    border: solid $border-blurred;
    padding: 0 1;
}

SparklinePanel .sparkline-label {
    color: $foreground-muted;
}

SparklinePanel Sparkline {
    width: 100%;
}

/* ----------------------------------------------------------------------------
   BUTTONS
   ---------------------------------------------------------------------------- */

Button {
    min-width: 16;
    height: 3;
    background: $panel;
    color: $foreground;
    border: tall $border;
}

Button:hover {
    background: $primary 20%;
    border: tall $primary;
}

Button:focus {
    background: $primary 30%;
    border: tall $accent;
    text-style: bold;
}

Button.-primary {
    background: $primary;
    color: $background;
    border: tall $primary-lighten-1;
}

Button.-primary:hover {
    background: $primary-lighten-1;
}

Button.-success {
    background: $success;
    color: $background;
    border: tall $success-lighten-1;
}

Button.-error {
    background: $error;
    color: $background;
    border: tall $error-lighten-1;
}

/* ----------------------------------------------------------------------------
   INPUT
   ---------------------------------------------------------------------------- */

Input {
    border: tall $border;
    background: $surface;
    padding: 0 1;
}

Input:focus {
    border: tall $accent;
}

Input.-invalid {
    border: tall $error;
}

/* ----------------------------------------------------------------------------
   HEADER LOGO
   ---------------------------------------------------------------------------- */

#header-logo {
    color: $accent;
    text-style: bold;
    text-align: center;
    padding: 0;
}

#header-logo .logo-char-1 { color: $neon-cyan; }
#header-logo .logo-char-2 { color: $neon-green; }
#header-logo .logo-char-3 { color: $neon-magenta; }
#header-logo .logo-char-4 { color: $neon-yellow; }
```

### 5.4 src/tui_app/styles/animations.tcss

```css
/* ============================================================================
   ANIMATION STYLES
   Spinners, transições e efeitos animados
   ============================================================================ */

/* ----------------------------------------------------------------------------
   LOADING INDICATOR
   ---------------------------------------------------------------------------- */

LoadingIndicator {
    color: $accent;
    background: transparent;
}

/* Indicator pulsante */
.loading-pulse {
    /* Textual não suporta keyframes, mas podemos usar color cycling */
    color: $accent;
}

/* ----------------------------------------------------------------------------
   SPINNER CUSTOM
   ---------------------------------------------------------------------------- */

.spinner {
    width: 3;
    height: 1;
    content-align: center middle;
    color: $accent;
}

.spinner-dots {
    /* Animação de dots será feita via código Python */
    color: $primary;
}

/* ----------------------------------------------------------------------------
   PROGRESS BAR ANIMATIONS
   ---------------------------------------------------------------------------- */

ProgressBar {
    /* Smooth transitions (se suportado) */
}

ProgressBar > .bar--bar {
    color: $primary;
}

ProgressBar > .bar--complete {
    color: $success;
}

ProgressBar > .bar--indeterminate {
    color: $accent;
}

/* ----------------------------------------------------------------------------
   NOTIFICATION TOAST
   ---------------------------------------------------------------------------- */

Toast {
    padding: 1 2;
    margin: 1;
    background: $surface;
    border: solid $border;
}

Toast.-information {
    border: solid $primary;
    border-title-color: $primary;
}

Toast.-warning {
    border: solid $warning;
    border-title-color: $warning;
}

Toast.-error {
    border: solid $error;
    border-title-color: $error;
}

ToastRack {
    align: right top;
    padding: 1;
}

/* ----------------------------------------------------------------------------
   GLOW EFFECTS (simulados)
   ---------------------------------------------------------------------------- */

/* Borda com "glow" (usa cor brilhante + contraste) */
.glow-border {
    border: heavy $accent;
}

.glow-border:focus {
    border: double $accent;
}

/* Text glow (usa bold + cor brilhante) */
.glow-text {
    color: $accent;
    text-style: bold;
}

/* ----------------------------------------------------------------------------
   TRANSITION HELPERS
   ---------------------------------------------------------------------------- */

/* 
   Nota: Textual tem suporte limitado a transições.
   Estas classes são placeholders para futura expansão
   ou para indicar onde transições seriam aplicadas.
*/

.transition-fast {
    /* 100ms */
}

.transition-normal {
    /* 200ms */
}

.transition-slow {
    /* 400ms */
}
```

---

## 6. Widgets Customizados

### 6.1 src/tui_app/widgets/__init__.py

```python
"""
Widgets customizados do TUI Template.

Widgets disponíveis:
- Header: Header com logo ASCII
- Sidebar: Menu lateral navegável
- LogPanel: RichLog estilizado com filtros
- PipelineProgress: Multi-progress para pipelines
- StatusBar: Barra de status com métricas
- FileBrowser: DirectoryTree com filtros
- ResultViewer: Markdown viewer
- SparklinePanel: Mini-gráficos
"""

from tui_app.widgets.header import Header
from tui_app.widgets.sidebar import Sidebar
from tui_app.widgets.log_panel import LogPanel
from tui_app.widgets.progress_panel import PipelineProgress, StageProgress
from tui_app.widgets.status_bar import StatusBar
from tui_app.widgets.file_browser import FileBrowser
from tui_app.widgets.result_viewer import ResultViewer
from tui_app.widgets.sparkline_panel import SparklinePanel

__all__ = [
    "Header",
    "Sidebar",
    "LogPanel",
    "PipelineProgress",
    "StageProgress",
    "StatusBar",
    "FileBrowser",
    "ResultViewer",
    "SparklinePanel",
]
```

### 6.2 src/tui_app/widgets/header.py

```python
"""
Header customizado com logo ASCII e status.
"""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static
from textual.widget import Widget


class Header(Widget):
    """
    Header customizado com logo ASCII.
    
    Exibe:
    - Logo ASCII colorido (esquerda)
    - Título e subtítulo (centro)
    - Status/versão (direita)
    """
    
    DEFAULT_CSS = """
    Header {
        dock: top;
        height: auto;
        background: $surface;
        border-bottom: heavy $border;
    }
    
    Header #header-content {
        height: auto;
        padding: 0 1;
    }
    
    Header #logo-section {
        width: auto;
        height: auto;
    }
    
    Header #title-section {
        width: 1fr;
        height: auto;
        content-align: center middle;
    }
    
    Header #status-section {
        width: auto;
        height: auto;
        content-align: right middle;
    }
    
    Header .header-title {
        text-style: bold;
        color: $accent;
    }
    
    Header .header-subtitle {
        color: $foreground-muted;
    }
    
    Header .header-status {
        color: $success;
    }
    """
    
    def __init__(
        self,
        logo: str | None = None,
        title: str = "TUI App",
        subtitle: str = "",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._logo = logo or self._default_logo()
        self._title = title
        self._subtitle = subtitle
    
    def _default_logo(self) -> str:
        """Logo ASCII padrão."""
        return """╔╦╗╦ ╦╦
 ║ ║ ║║
 ╩ ╚═╝╩"""
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="header-content"):
            yield Static(self._logo, id="logo-section")
            with Horizontal(id="title-section"):
                yield Static(self._title, classes="header-title")
                if self._subtitle:
                    yield Static(f" {self._subtitle}", classes="header-subtitle")
            yield Static("● Ready", id="status-section", classes="header-status")
    
    def set_status(self, status: str, style: str = "success") -> None:
        """
        Atualiza o status no header.
        
        Args:
            status: Texto do status
            style: Estilo CSS (success, warning, error)
        """
        status_widget = self.query_one("#status-section", Static)
        status_widget.update(status)
        status_widget.remove_class("success", "warning", "error")
        status_widget.add_class(style)
```

### 6.3 src/tui_app/widgets/sidebar.py

```python
"""
Sidebar navegável com menu de opções.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option, Separator
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message


class Sidebar(Widget):
    """
    Menu lateral navegável.
    
    Emite mensagem SidebarOptionSelected quando uma opção é selecionada.
    """
    
    DEFAULT_CSS = """
    Sidebar {
        width: 30;
        height: 100%;
        background: $surface;
        border-right: heavy $border;
    }
    
    Sidebar:focus-within {
        border-right: heavy $accent;
    }
    
    Sidebar #sidebar-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        padding: 1;
        border-bottom: solid $border-blurred;
    }
    
    Sidebar OptionList {
        background: transparent;
        height: 1fr;
        padding: 1 0;
    }
    """
    
    collapsed: reactive[bool] = reactive(False)
    
    class OptionSelected(Message):
        """Emitida quando uma opção é selecionada."""
        
        def __init__(self, option_id: str) -> None:
            self.option_id = option_id
            super().__init__()
    
    def __init__(
        self,
        title: str = "Menu",
        options: list[tuple[str, str]] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """
        Inicializa sidebar.
        
        Args:
            title: Título do menu
            options: Lista de (id, label) para as opções
        """
        super().__init__(name=name, id=id, classes=classes)
        self._title = title
        self._options = options or [
            ("files", "📁 Arquivos"),
            ("progress", "📊 Progresso"),
            ("logs", "📋 Logs"),
            ("---", ""),
            ("settings", "⚙️ Configurações"),
            ("help", "❓ Ajuda"),
        ]
    
    def compose(self) -> ComposeResult:
        yield Static(self._title, id="sidebar-title")
        
        option_list = OptionList(id="sidebar-options")
        for opt_id, label in self._options:
            if opt_id == "---":
                option_list.add_option(Separator())
            else:
                option_list.add_option(Option(label, id=opt_id))
        
        yield option_list
    
    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Propaga seleção como mensagem da Sidebar."""
        if event.option.id:
            self.post_message(self.OptionSelected(event.option.id))
    
    def watch_collapsed(self, collapsed: bool) -> None:
        """Controla visibilidade."""
        if collapsed:
            self.add_class("collapsed")
        else:
            self.remove_class("collapsed")
    
    def toggle(self) -> None:
        """Alterna estado collapsed."""
        self.collapsed = not self.collapsed
```

### 6.4 src/tui_app/widgets/log_panel.py

```python
"""
Painel de logs estilizado com filtros e níveis.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from textual.widgets import RichLog
from textual.reactive import reactive


class LogLevel(str, Enum):
    """Níveis de log."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


# Mapeamento de nível para estilo Rich
LOG_STYLES = {
    LogLevel.DEBUG: "[dim]DEBUG[/]",
    LogLevel.INFO: "[cyan]INFO[/]",
    LogLevel.WARNING: "[yellow]WARN[/]",
    LogLevel.ERROR: "[red bold]ERROR[/]",
    LogLevel.SUCCESS: "[green]OK[/]",
}


class LogPanel(RichLog):
    """
    RichLog customizado com suporte a níveis e filtros.
    
    Features:
    - Níveis de log coloridos (DEBUG, INFO, WARNING, ERROR, SUCCESS)
    - Timestamps automáticos
    - Filtros por nível
    - Limite de linhas (virtualização)
    """
    
    DEFAULT_CSS = """
    LogPanel {
        border: heavy $border;
        border-title-color: $primary;
        background: $surface;
        padding: 0 1;
    }
    
    LogPanel:focus {
        border: heavy $accent;
        border-title-color: $accent;
    }
    """
    
    # Filtros reativos
    show_debug: reactive[bool] = reactive(False)
    show_info: reactive[bool] = reactive(True)
    show_warning: reactive[bool] = reactive(True)
    show_error: reactive[bool] = reactive(True)
    show_timestamps: reactive[bool] = reactive(True)
    
    def __init__(
        self,
        *,
        max_lines: int = 10000,
        highlight: bool = True,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(
            max_lines=max_lines,
            highlight=highlight,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
        )
        self.border_title = "Logs"
    
    def _format_message(self, level: LogLevel, message: str) -> str:
        """Formata mensagem com timestamp e nível."""
        parts = []
        
        if self.show_timestamps:
            timestamp = datetime.now().strftime("%H:%M:%S")
            parts.append(f"[dim]{timestamp}[/]")
        
        parts.append(LOG_STYLES[level])
        parts.append(message)
        
        return " ".join(parts)
    
    def _should_show(self, level: LogLevel) -> bool:
        """Verifica se o nível deve ser exibido."""
        filters = {
            LogLevel.DEBUG: self.show_debug,
            LogLevel.INFO: self.show_info,
            LogLevel.WARNING: self.show_warning,
            LogLevel.ERROR: self.show_error,
            LogLevel.SUCCESS: True,  # Sempre mostra
        }
        return filters.get(level, True)
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """
        Adiciona log com nível específico.
        
        Args:
            message: Mensagem de log
            level: Nível do log
        """
        if self._should_show(level):
            formatted = self._format_message(level, message)
            self.write(formatted)
    
    def debug(self, message: str) -> None:
        """Log de debug."""
        self.log(message, LogLevel.DEBUG)
    
    def info(self, message: str) -> None:
        """Log de informação."""
        self.log(message, LogLevel.INFO)
    
    def warning(self, message: str) -> None:
        """Log de aviso."""
        self.log(message, LogLevel.WARNING)
    
    def error(self, message: str) -> None:
        """Log de erro."""
        self.log(message, LogLevel.ERROR)
    
    def success(self, message: str) -> None:
        """Log de sucesso."""
        self.log(message, LogLevel.SUCCESS)
    
    def separator(self, char: str = "─", length: int = 40) -> None:
        """Adiciona linha separadora."""
        self.write(f"[dim]{char * length}[/]")
    
    def header(self, text: str) -> None:
        """Adiciona header destacado."""
        self.write(f"\n[bold cyan]═══ {text} ═══[/]\n")
```

### 6.5 src/tui_app/widgets/progress_panel.py

```python
"""
Painel de progresso multi-estágio para pipelines.
"""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, ProgressBar
from textual.widget import Widget
from textual.reactive import reactive


class StageProgress(Widget):
    """
    Widget de progresso para um estágio individual.
    
    Exibe:
    - Label do estágio
    - Barra de progresso
    - Status (pending, running, completed, error)
    """
    
    DEFAULT_CSS = """
    StageProgress {
        height: 3;
        padding: 0 1;
        layout: vertical;
    }
    
    StageProgress .stage-header {
        height: 1;
        layout: horizontal;
    }
    
    StageProgress .stage-label {
        width: 1fr;
        text-style: bold;
    }
    
    StageProgress .stage-status {
        width: auto;
        text-align: right;
    }
    
    StageProgress ProgressBar {
        width: 100%;
        height: 1;
    }
    
    /* Status styles */
    StageProgress.pending .stage-label {
        color: $foreground-muted;
    }
    StageProgress.pending .stage-status {
        color: $foreground-muted;
    }
    
    StageProgress.running .stage-label {
        color: $accent;
    }
    StageProgress.running .stage-status {
        color: $accent;
    }
    
    StageProgress.completed .stage-label {
        color: $success;
    }
    StageProgress.completed .stage-status {
        color: $success;
    }
    
    StageProgress.error .stage-label {
        color: $error;
    }
    StageProgress.error .stage-status {
        color: $error;
    }
    """
    
    progress: reactive[float] = reactive(0.0)
    status: reactive[str] = reactive("pending")
    
    STATUS_ICONS = {
        "pending": "○",
        "running": "◐",
        "completed": "●",
        "error": "✗",
    }
    
    def __init__(
        self,
        label: str,
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes="pending")
        self._label = label
    
    def compose(self) -> ComposeResult:
        with Horizontal(classes="stage-header"):
            yield Static(self._label, classes="stage-label")
            yield Static(self.STATUS_ICONS["pending"], classes="stage-status")
        yield ProgressBar(total=100, show_eta=False, show_percentage=True)
    
    def watch_progress(self, value: float) -> None:
        """Atualiza barra de progresso."""
        try:
            bar = self.query_one(ProgressBar)
            bar.update(progress=value)
        except Exception:
            pass
    
    def watch_status(self, value: str) -> None:
        """Atualiza status visual."""
        # Remove classes antigas
        self.remove_class("pending", "running", "completed", "error")
        # Adiciona nova classe
        self.add_class(value)
        # Atualiza ícone
        try:
            status_widget = self.query_one(".stage-status", Static)
            status_widget.update(self.STATUS_ICONS.get(value, "?"))
        except Exception:
            pass


# Import necessário para Horizontal
from textual.containers import Horizontal


class PipelineProgress(Vertical):
    """
    Tracker visual de pipeline com múltiplos estágios.
    
    Uso:
        progress = PipelineProgress([
            "Cartógrafo",
            "Saneador", 
            "Extrator",
            "Bibliotecário",
        ])
        
        progress.start_stage(1)
        progress.update_stage(1, 50.0)
        progress.complete_stage(1)
    """
    
    DEFAULT_CSS = """
    PipelineProgress {
        border: heavy $border;
        border-title-color: $primary;
        background: $surface;
        height: auto;
        padding: 1;
    }
    
    PipelineProgress:focus {
        border: heavy $accent;
    }
    """
    
    def __init__(
        self,
        stages: list[str],
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._stages = stages
        self.border_title = "Pipeline"
    
    def compose(self) -> ComposeResult:
        for i, stage in enumerate(self._stages, 1):
            yield StageProgress(f"{i}. {stage}", id=f"stage-{i}")
    
    def _get_stage(self, stage_num: int) -> StageProgress:
        """Obtém widget do estágio."""
        return self.query_one(f"#stage-{stage_num}", StageProgress)
    
    def start_stage(self, stage_num: int) -> None:
        """Marca estágio como em execução."""
        stage = self._get_stage(stage_num)
        stage.status = "running"
        stage.progress = 0.0
    
    def update_stage(self, stage_num: int, progress: float) -> None:
        """Atualiza progresso do estágio."""
        stage = self._get_stage(stage_num)
        stage.progress = min(100.0, max(0.0, progress))
    
    def complete_stage(self, stage_num: int) -> None:
        """Marca estágio como completo."""
        stage = self._get_stage(stage_num)
        stage.progress = 100.0
        stage.status = "completed"
    
    def error_stage(self, stage_num: int) -> None:
        """Marca estágio com erro."""
        stage = self._get_stage(stage_num)
        stage.status = "error"
    
    def reset(self) -> None:
        """Reseta todos os estágios."""
        for i in range(1, len(self._stages) + 1):
            stage = self._get_stage(i)
            stage.status = "pending"
            stage.progress = 0.0
```

### 6.6 src/tui_app/widgets/file_browser.py

```python
"""
Browser de arquivos com filtro por extensão.
"""

from pathlib import Path
from typing import Iterable

from textual.app import ComposeResult
from textual.widgets import DirectoryTree, Static
from textual.widget import Widget
from textual.message import Message


class FilteredDirectoryTree(DirectoryTree):
    """DirectoryTree com filtro de extensões."""
    
    def __init__(
        self,
        path: str | Path,
        extensions: set[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(path, **kwargs)
        self._extensions = extensions or set()
    
    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        """Filtra paths por extensão."""
        for path in paths:
            # Sempre mostra diretórios
            if path.is_dir():
                yield path
            # Filtra arquivos por extensão
            elif not self._extensions or path.suffix.lower() in self._extensions:
                yield path


class FileBrowser(Widget):
    """
    Browser de arquivos com filtro e seleção.
    
    Features:
    - Filtro por extensões
    - Exibe path atual
    - Emite evento ao selecionar arquivo
    """
    
    DEFAULT_CSS = """
    FileBrowser {
        border: heavy $border;
        border-title-color: $primary;
        background: $surface;
        height: 100%;
    }
    
    FileBrowser:focus-within {
        border: heavy $accent;
    }
    
    FileBrowser #current-path {
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $foreground-muted;
    }
    
    FileBrowser DirectoryTree {
        height: 1fr;
        padding: 0 1;
        background: transparent;
    }
    """
    
    class FileSelected(Message):
        """Emitida quando um arquivo é selecionado."""
        
        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()
    
    def __init__(
        self,
        path: str | Path = ".",
        extensions: set[str] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        """
        Inicializa browser.
        
        Args:
            path: Diretório inicial
            extensions: Set de extensões permitidas (ex: {".pdf", ".txt"})
        """
        super().__init__(name=name, id=id)
        self._path = Path(path).resolve()
        self._extensions = extensions
        self.border_title = "Arquivos"
    
    def compose(self) -> ComposeResult:
        yield Static(str(self._path), id="current-path")
        yield FilteredDirectoryTree(
            self._path,
            extensions=self._extensions,
            id="dir-tree",
        )
    
    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Propaga seleção de arquivo."""
        self.post_message(self.FileSelected(event.path))
        # Atualiza path exibido
        path_widget = self.query_one("#current-path", Static)
        path_widget.update(str(event.path))
    
    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        """Atualiza path ao entrar em diretório."""
        path_widget = self.query_one("#current-path", Static)
        path_widget.update(str(event.path))
    
    def set_path(self, path: str | Path) -> None:
        """Navega para um novo diretório."""
        self._path = Path(path).resolve()
        tree = self.query_one("#dir-tree", FilteredDirectoryTree)
        tree.path = self._path
        
        path_widget = self.query_one("#current-path", Static)
        path_widget.update(str(self._path))
```

### 6.7 src/tui_app/widgets/result_viewer.py

```python
"""
Visualizador de resultados em Markdown.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Markdown, Static
from textual.widget import Widget


class ResultViewer(Widget):
    """
    Visualizador de conteúdo Markdown.
    
    Features:
    - Renderiza Markdown com syntax highlighting
    - Scroll automático
    - Carrega de arquivo ou string
    """
    
    DEFAULT_CSS = """
    ResultViewer {
        border: heavy $border;
        border-title-color: $primary;
        background: $surface;
        height: 100%;
    }
    
    ResultViewer:focus-within {
        border: heavy $accent;
    }
    
    ResultViewer #result-header {
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $foreground-muted;
    }
    
    ResultViewer VerticalScroll {
        height: 1fr;
    }
    
    ResultViewer Markdown {
        padding: 1;
        background: transparent;
    }
    
    ResultViewer .empty-message {
        color: $foreground-muted;
        text-align: center;
        padding: 2;
    }
    """
    
    def __init__(
        self,
        content: str = "",
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._content = content
        self._source: str | None = None
        self.border_title = "Resultado"
    
    def compose(self) -> ComposeResult:
        yield Static("Nenhum arquivo carregado", id="result-header")
        with VerticalScroll():
            if self._content:
                yield Markdown(self._content, id="result-content")
            else:
                yield Static(
                    "Selecione um arquivo ou execute a pipeline para ver resultados.",
                    classes="empty-message",
                )
    
    def load_content(self, content: str, source: str | None = None) -> None:
        """
        Carrega conteúdo Markdown.
        
        Args:
            content: Conteúdo Markdown
            source: Descrição da origem (exibido no header)
        """
        self._content = content
        self._source = source
        
        # Atualiza header
        header = self.query_one("#result-header", Static)
        header.update(source or "Conteúdo carregado")
        
        # Atualiza ou cria Markdown widget
        scroll = self.query_one(VerticalScroll)
        scroll.remove_children()
        scroll.mount(Markdown(content, id="result-content"))
    
    def load_file(self, path: str | Path) -> None:
        """
        Carrega conteúdo de arquivo.
        
        Args:
            path: Caminho do arquivo Markdown
        """
        path = Path(path)
        if path.exists():
            content = path.read_text(encoding="utf-8")
            self.load_content(content, source=str(path))
        else:
            self.load_content(
                f"**Erro:** Arquivo não encontrado: `{path}`",
                source="Erro"
            )
    
    def clear(self) -> None:
        """Limpa o conteúdo."""
        self._content = ""
        self._source = None
        
        header = self.query_one("#result-header", Static)
        header.update("Nenhum arquivo carregado")
        
        scroll = self.query_one(VerticalScroll)
        scroll.remove_children()
        scroll.mount(Static(
            "Selecione um arquivo ou execute a pipeline para ver resultados.",
            classes="empty-message",
        ))
```

### 6.8 src/tui_app/widgets/status_bar.py

```python
"""
Barra de status com métricas do sistema.
"""

import psutil
from datetime import datetime

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static
from textual.widget import Widget
from textual.reactive import reactive


class StatusBar(Widget):
    """
    Barra de status com métricas.
    
    Exibe:
    - Uso de CPU
    - Uso de RAM
    - Tempo de execução
    - Status customizado
    """
    
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $panel;
        padding: 0 1;
    }
    
    StatusBar Horizontal {
        height: 1;
        width: 100%;
    }
    
    StatusBar .status-item {
        width: auto;
        padding: 0 1;
    }
    
    StatusBar .status-label {
        color: $foreground-muted;
    }
    
    StatusBar .status-value {
        color: $primary;
    }
    
    StatusBar .status-spacer {
        width: 1fr;
    }
    
    StatusBar .status-time {
        color: $foreground-muted;
    }
    """
    
    cpu_percent: reactive[float] = reactive(0.0)
    ram_percent: reactive[float] = reactive(0.0)
    custom_status: reactive[str] = reactive("")
    
    def __init__(
        self,
        *,
        show_cpu: bool = True,
        show_ram: bool = True,
        show_time: bool = True,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._show_cpu = show_cpu
        self._show_ram = show_ram
        self._show_time = show_time
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            # Custom status (esquerda)
            yield Static("", id="custom-status", classes="status-item")
            
            # Spacer
            yield Static("", classes="status-spacer")
            
            # Métricas (direita)
            if self._show_cpu:
                yield Static(
                    "[dim]CPU:[/] [cyan]0%[/]",
                    id="cpu-status",
                    classes="status-item",
                )
            
            if self._show_ram:
                yield Static(
                    "[dim]RAM:[/] [cyan]0%[/]",
                    id="ram-status",
                    classes="status-item",
                )
            
            if self._show_time:
                yield Static(
                    datetime.now().strftime("%H:%M:%S"),
                    id="time-status",
                    classes="status-item status-time",
                )
    
    def on_mount(self) -> None:
        """Inicia timer de atualização."""
        self.set_interval(1.0, self._update_metrics)
    
    def _update_metrics(self) -> None:
        """Atualiza métricas periodicamente."""
        # CPU
        if self._show_cpu:
            try:
                cpu = psutil.cpu_percent()
                cpu_widget = self.query_one("#cpu-status", Static)
                color = "green" if cpu < 50 else "yellow" if cpu < 80 else "red"
                cpu_widget.update(f"[dim]CPU:[/] [{color}]{cpu:.0f}%[/]")
            except Exception:
                pass
        
        # RAM
        if self._show_ram:
            try:
                ram = psutil.virtual_memory().percent
                ram_widget = self.query_one("#ram-status", Static)
                color = "green" if ram < 50 else "yellow" if ram < 80 else "red"
                ram_widget.update(f"[dim]RAM:[/] [{color}]{ram:.0f}%[/]")
            except Exception:
                pass
        
        # Time
        if self._show_time:
            try:
                time_widget = self.query_one("#time-status", Static)
                time_widget.update(datetime.now().strftime("%H:%M:%S"))
            except Exception:
                pass
    
    def watch_custom_status(self, status: str) -> None:
        """Atualiza status customizado."""
        try:
            widget = self.query_one("#custom-status", Static)
            widget.update(status)
        except Exception:
            pass
    
    def set_status(self, status: str) -> None:
        """Define status customizado."""
        self.custom_status = status
```

---

## 7. Screens

### 7.1 src/tui_app/screens/__init__.py

```python
"""
Screens da aplicação TUI.

Screens disponíveis:
- MainScreen: Dashboard principal
- LogScreen: Visualização de logs em tela cheia
- SettingsScreen: Configurações da aplicação
- HelpScreen: Ajuda e keybindings
"""

from tui_app.screens.main_screen import MainScreen
from tui_app.screens.help_screen import HelpScreen

__all__ = [
    "MainScreen",
    "HelpScreen",
]
```

### 7.2 src/tui_app/screens/main_screen.py

```python
"""
Tela principal (Dashboard) da aplicação.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer

from tui_app.widgets import (
    Header,
    Sidebar,
    LogPanel,
    PipelineProgress,
    FileBrowser,
    ResultViewer,
    StatusBar,
)
from tui_app.messages.pipeline_messages import (
    PipelineStarted,
    StepStarted,
    StepProgress,
    StepCompleted,
    StepError,
    PipelineCompleted,
    PipelineAborted,
)


class MainScreen(Screen):
    """
    Dashboard principal.
    
    Layout:
    ┌─────────────────────────────────────────────────────┐
    │                     HEADER                          │
    ├──────────┬──────────────────────────────────────────┤
    │          │            PROGRESS PANEL                │
    │          ├──────────────────────────────────────────┤
    │ SIDEBAR  │                                          │
    │          │    LOG PANEL    │    RESULT VIEWER       │
    │          │                 │                        │
    ├──────────┴──────────────────────────────────────────┤
    │                    STATUS BAR                       │
    └─────────────────────────────────────────────────────┘
    """
    
    DEFAULT_CSS = """
    MainScreen {
        layout: grid;
        grid-size: 1 1;
    }
    
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    #content-area {
        width: 1fr;
        height: 100%;
        layout: vertical;
    }
    
    #top-section {
        height: auto;
        max-height: 15;
        padding: 1;
    }
    
    #bottom-section {
        height: 1fr;
        layout: horizontal;
        padding: 1;
    }
    
    #log-panel {
        width: 1fr;
        height: 100%;
        margin-right: 1;
    }
    
    #result-viewer {
        width: 1fr;
        height: 100%;
    }
    """
    
    BINDINGS = [
        ("b", "toggle_sidebar", "Sidebar"),
    ]
    
    def __init__(
        self,
        pipeline_stages: list[str] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._pipeline_stages = pipeline_stages or [
            "Cartógrafo",
            "Saneador",
            "Extrator",
            "Bibliotecário",
        ]
        self._selected_file: Path | None = None
    
    def compose(self) -> ComposeResult:
        yield Header(
            title="TUI Template",
            subtitle="v0.1.0",
        )
        
        with Horizontal(id="main-container"):
            yield Sidebar(
                title="Menu",
                options=[
                    ("files", "📁 Arquivos"),
                    ("run", "▶️ Executar"),
                    ("---", ""),
                    ("settings", "⚙️ Config"),
                    ("help", "❓ Ajuda"),
                ],
                id="sidebar",
            )
            
            with Vertical(id="content-area"):
                # Seção superior: Progress
                with Vertical(id="top-section"):
                    yield PipelineProgress(
                        self._pipeline_stages,
                        id="progress-panel",
                    )
                
                # Seção inferior: Logs + Results
                with Horizontal(id="bottom-section"):
                    yield LogPanel(id="log-panel")
                    yield ResultViewer(id="result-viewer")
        
        yield StatusBar(id="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        """Setup inicial."""
        log = self.query_one("#log-panel", LogPanel)
        log.header("Sistema Inicializado")
        log.info("Selecione um arquivo e pressione [R] para executar")
    
    # =========================================================================
    # ACTIONS
    # =========================================================================
    
    def action_toggle_sidebar(self) -> None:
        """Alterna sidebar."""
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.toggle()
    
    def run_pipeline(self) -> None:
        """Inicia execução da pipeline."""
        log = self.query_one("#log-panel", LogPanel)
        progress = self.query_one("#progress-panel", PipelineProgress)
        
        if not self._selected_file:
            log.warning("Nenhum arquivo selecionado")
            return
        
        log.header(f"Iniciando pipeline: {self._selected_file.name}")
        progress.reset()
        
        # TODO: Iniciar worker de pipeline aqui
        # self.run_worker(self._execute_pipeline())
    
    def cancel_operation(self) -> None:
        """Cancela operação em andamento."""
        log = self.query_one("#log-panel", LogPanel)
        log.warning("Operação cancelada pelo usuário")
    
    # =========================================================================
    # MESSAGE HANDLERS
    # =========================================================================
    
    def on_sidebar_option_selected(self, event: Sidebar.OptionSelected) -> None:
        """Processa seleção no sidebar."""
        log = self.query_one("#log-panel", LogPanel)
        
        if event.option_id == "run":
            self.run_pipeline()
        elif event.option_id == "help":
            self.app.action_show_help()
        elif event.option_id == "files":
            log.info("Navegue pela árvore de arquivos")
    
    def on_file_browser_file_selected(self, event: FileBrowser.FileSelected) -> None:
        """Processa seleção de arquivo."""
        self._selected_file = event.path
        log = self.query_one("#log-panel", LogPanel)
        log.info(f"Arquivo selecionado: {event.path.name}")
        
        # Atualiza status
        status = self.query_one("#status-bar", StatusBar)
        status.set_status(f"📄 {event.path.name}")
    
    def on_step_started(self, event: StepStarted) -> None:
        """Step iniciou."""
        log = self.query_one("#log-panel", LogPanel)
        progress = self.query_one("#progress-panel", PipelineProgress)
        
        log.info(f"Iniciando {event.name}...")
        progress.start_stage(event.step)
    
    def on_step_progress(self, event: StepProgress) -> None:
        """Atualização de progresso."""
        progress = self.query_one("#progress-panel", PipelineProgress)
        progress.update_stage(event.step, event.progress)
        
        if event.message:
            log = self.query_one("#log-panel", LogPanel)
            log.debug(event.message)
    
    def on_step_completed(self, event: StepCompleted) -> None:
        """Step completou."""
        log = self.query_one("#log-panel", LogPanel)
        progress = self.query_one("#progress-panel", PipelineProgress)
        
        log.success(f"Step {event.step} concluído")
        progress.complete_stage(event.step)
    
    def on_step_error(self, event: StepError) -> None:
        """Step falhou."""
        log = self.query_one("#log-panel", LogPanel)
        progress = self.query_one("#progress-panel", PipelineProgress)
        
        log.error(f"Erro no step {event.step}: {event.error}")
        progress.error_stage(event.step)
    
    def on_pipeline_completed(self, event: PipelineCompleted) -> None:
        """Pipeline completou."""
        log = self.query_one("#log-panel", LogPanel)
        result_viewer = self.query_one("#result-viewer", ResultViewer)
        
        log.header("Pipeline Concluída")
        log.success("Todos os estágios completados com sucesso")
        
        # TODO: Carregar resultado no viewer
        # result_viewer.load_content(...)
```

### 7.3 src/tui_app/screens/help_screen.py

```python
"""
Tela de ajuda com keybindings e documentação.
"""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static, Markdown
from textual.binding import Binding


HELP_CONTENT = """
# Ajuda - TUI Template

## Atalhos de Teclado

### Navegação
| Tecla | Ação |
|-------|------|
| `Q` | Sair da aplicação |
| `?` | Mostrar esta ajuda |
| `B` | Alternar sidebar |
| `Tab` | Próximo painel |
| `Shift+Tab` | Painel anterior |

### Controle
| Tecla | Ação |
|-------|------|
| `R` | Executar pipeline |
| `Escape` | Cancelar operação |
| `D` | Alternar tema claro/escuro |

### Painéis
| Tecla | Ação |
|-------|------|
| `L` | Focar painel de logs |
| `P` | Focar painel de progresso |

### Sistema
| Tecla | Ação |
|-------|------|
| `Ctrl+P` | Paleta de comandos |
| `Ctrl+S` | Screenshot |

## Sobre

TUI Template v0.1.0

Template maximalista para criação de TUIs com Textual.

Pressione `Escape` ou `Q` para fechar esta tela.
"""


class HelpScreen(ModalScreen):
    """
    Tela modal de ajuda.
    """
    
    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    
    HelpScreen #help-container {
        width: 70%;
        height: 80%;
        background: $surface;
        border: heavy $accent;
        border-title-color: $accent;
        padding: 1 2;
    }
    
    HelpScreen Markdown {
        padding: 1;
    }
    """
    
    BINDINGS = [
        Binding("escape", "dismiss", "Fechar"),
        Binding("q", "dismiss", "Fechar"),
    ]
    
    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-container"):
            yield Markdown(HELP_CONTENT)
    
    def on_mount(self) -> None:
        """Setup."""
        container = self.query_one("#help-container")
        container.border_title = "Ajuda"
```

---

## 8. Sistema de Mensagens

### 8.1 src/tui_app/messages/__init__.py

```python
"""
Sistema de mensagens customizadas.

Mensagens são usadas para comunicação desacoplada entre widgets,
screens e workers.
"""

from tui_app.messages.pipeline_messages import (
    PipelineStarted,
    StepStarted,
    StepProgress,
    StepCompleted,
    StepError,
    PipelineCompleted,
    PipelineAborted,
)
from tui_app.messages.system_messages import (
    LogMessage,
    StatusUpdate,
    FileLoaded,
)

__all__ = [
    # Pipeline
    "PipelineStarted",
    "StepStarted",
    "StepProgress",
    "StepCompleted",
    "StepError",
    "PipelineCompleted",
    "PipelineAborted",
    # System
    "LogMessage",
    "StatusUpdate",
    "FileLoaded",
]
```

### 8.2 src/tui_app/messages/pipeline_messages.py

```python
"""
Mensagens relacionadas à execução de pipelines.
"""

from dataclasses import dataclass
from typing import Any

from textual.message import Message


@dataclass
class PipelineStarted(Message):
    """Emitida quando uma pipeline inicia execução."""
    total_steps: int
    pipeline_id: str | None = None


@dataclass
class StepStarted(Message):
    """Emitida quando um step da pipeline inicia."""
    step: int
    name: str
    

@dataclass
class StepProgress(Message):
    """Emitida para atualizar progresso de um step."""
    step: int
    progress: float  # 0.0 a 100.0
    message: str | None = None


@dataclass
class StepCompleted(Message):
    """Emitida quando um step completa com sucesso."""
    step: int
    result: dict[str, Any] | None = None
    duration_ms: int | None = None


@dataclass
class StepError(Message):
    """Emitida quando um step falha."""
    step: int
    error: str
    traceback: str | None = None


@dataclass
class PipelineCompleted(Message):
    """Emitida quando toda a pipeline completa com sucesso."""
    results: dict[str, Any]
    total_duration_ms: int | None = None


@dataclass
class PipelineAborted(Message):
    """Emitida quando a pipeline é abortada (erro ou cancelamento)."""
    reason: str
    step: int | None = None  # Step onde ocorreu o abort
```

### 8.3 src/tui_app/messages/system_messages.py

```python
"""
Mensagens de sistema gerais.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from textual.message import Message


LogLevel = Literal["debug", "info", "warning", "error", "success"]


@dataclass
class LogMessage(Message):
    """Mensagem de log para exibição."""
    message: str
    level: LogLevel = "info"
    source: str | None = None


@dataclass
class StatusUpdate(Message):
    """Atualização de status para a barra de status."""
    status: str
    style: Literal["normal", "success", "warning", "error"] = "normal"


@dataclass
class FileLoaded(Message):
    """Emitida quando um arquivo é carregado."""
    path: Path
    size_bytes: int
    

@dataclass
class ThemeChanged(Message):
    """Emitida quando o tema é alterado."""
    theme_name: str
    is_dark: bool
```

---

## 9. Workers e Pipeline

### 9.1 src/tui_app/workers/__init__.py

```python
"""
Sistema de workers para tarefas assíncronas.

Workers permitem executar operações longas sem bloquear a UI.
Comunicação via Messages do Textual.
"""

from tui_app.workers.base_worker import BaseWorker
from tui_app.workers.pipeline_worker import PipelineWorker

__all__ = [
    "BaseWorker",
    "PipelineWorker",
]
```

### 9.2 src/tui_app/workers/base_worker.py

```python
"""
Classe base para workers.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable

from textual.app import App


class BaseWorker(ABC):
    """
    Classe base abstrata para workers.
    
    Workers executam tarefas longas em threads separadas,
    comunicando progresso via Messages.
    """
    
    def __init__(self, app: App) -> None:
        """
        Inicializa worker.
        
        Args:
            app: Instância da App para postar mensagens
        """
        self.app = app
        self._cancelled = False
    
    @property
    def is_cancelled(self) -> bool:
        """Verifica se worker foi cancelado."""
        return self._cancelled
    
    def cancel(self) -> None:
        """Cancela execução do worker."""
        self._cancelled = True
    
    def reset(self) -> None:
        """Reseta estado do worker."""
        self._cancelled = False
    
    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Executa a tarefa do worker.
        
        Deve ser implementado pelas subclasses.
        """
        pass
    
    def post_message(self, message: Any) -> None:
        """
        Posta mensagem para a App.
        
        Args:
            message: Mensagem a ser postada
        """
        self.app.post_message(message)
```

### 9.3 src/tui_app/workers/pipeline_worker.py

```python
"""
Worker para execução de pipelines multi-estágio.
"""

import time
from typing import Any, Callable, TypeAlias

from textual.app import App
from textual.worker import work

from tui_app.workers.base_worker import BaseWorker
from tui_app.messages.pipeline_messages import (
    PipelineStarted,
    StepStarted,
    StepProgress,
    StepCompleted,
    StepError,
    PipelineCompleted,
    PipelineAborted,
)


# Type alias para função de step
# Recebe: context (dict), progress_callback (Callable[[float, str], None])
# Retorna: dict com resultados
StepFunction: TypeAlias = Callable[[dict, Callable[[float, str | None], None]], dict]


class PipelineWorker(BaseWorker):
    """
    Executor de pipelines em worker thread.
    
    Uso:
        worker = PipelineWorker(app)
        
        steps = [
            ("Cartógrafo", step_01_function),
            ("Saneador", step_02_function),
            ("Extrator", step_03_function),
        ]
        
        results = await worker.run(steps, initial_context={})
    """
    
    def __init__(self, app: App) -> None:
        super().__init__(app)
        self._current_step = 0
    
    @work(exclusive=True, thread=True)
    async def run(
        self,
        steps: list[tuple[str, StepFunction]],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Executa pipeline de steps.
        
        Args:
            steps: Lista de (nome, função) para executar
            context: Contexto inicial passado entre steps
        
        Returns:
            Dict com resultados consolidados de todos os steps
        """
        context = context or {}
        results: dict[str, Any] = {}
        start_time = time.perf_counter()
        
        # Notifica início
        self.post_message(PipelineStarted(total_steps=len(steps)))
        
        for i, (name, step_fn) in enumerate(steps, 1):
            self._current_step = i
            
            # Verifica cancelamento
            if self.is_cancelled:
                self.post_message(PipelineAborted(
                    reason="Cancelado pelo usuário",
                    step=i,
                ))
                return results
            
            # Notifica início do step
            self.post_message(StepStarted(step=i, name=name))
            step_start = time.perf_counter()
            
            try:
                # Callback para progresso
                def progress_callback(pct: float, msg: str | None = None) -> None:
                    if not self.is_cancelled:
                        self.post_message(StepProgress(
                            step=i,
                            progress=pct,
                            message=msg,
                        ))
                
                # Executa step
                result = step_fn(context, progress_callback)
                
                # Armazena resultado
                results[name] = result
                
                # Atualiza contexto para próximo step
                if isinstance(result, dict):
                    context.update(result)
                
                # Calcula duração
                step_duration = int((time.perf_counter() - step_start) * 1000)
                
                # Notifica conclusão
                self.post_message(StepCompleted(
                    step=i,
                    result=result,
                    duration_ms=step_duration,
                ))
                
            except Exception as e:
                import traceback
                
                self.post_message(StepError(
                    step=i,
                    error=str(e),
                    traceback=traceback.format_exc(),
                ))
                
                self.post_message(PipelineAborted(
                    reason=f"Erro no step {i}: {name}",
                    step=i,
                ))
                
                return results
        
        # Calcula duração total
        total_duration = int((time.perf_counter() - start_time) * 1000)
        
        # Notifica conclusão da pipeline
        self.post_message(PipelineCompleted(
            results=results,
            total_duration_ms=total_duration,
        ))
        
        return results
```

---

## 10. Modelos de Dados

### 10.1 src/tui_app/models/__init__.py

```python
"""
Modelos de dados Pydantic.
"""

from tui_app.models.log_entry import LogEntry, LogLevel
from tui_app.models.pipeline import PipelineConfig, StepConfig, StepResult
from tui_app.models.settings import AppSettings

__all__ = [
    "LogEntry",
    "LogLevel",
    "PipelineConfig",
    "StepConfig",
    "StepResult",
    "AppSettings",
]
```

### 10.2 src/tui_app/models/log_entry.py

```python
"""
Modelo para entradas de log.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Níveis de log."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class LogEntry(BaseModel):
    """
    Entrada de log estruturada.
    
    Attributes:
        timestamp: Data/hora do log
        level: Nível do log
        message: Mensagem de log
        source: Origem do log (módulo/função)
        metadata: Dados adicionais
    """
    timestamp: datetime = Field(default_factory=datetime.now)
    level: LogLevel = LogLevel.INFO
    message: str
    source: str | None = None
    metadata: dict | None = None
    
    def format_rich(self) -> str:
        """Formata para exibição com Rich markup."""
        colors = {
            LogLevel.DEBUG: "dim",
            LogLevel.INFO: "cyan",
            LogLevel.WARNING: "yellow",
            LogLevel.ERROR: "red bold",
            LogLevel.SUCCESS: "green",
        }
        
        time_str = self.timestamp.strftime("%H:%M:%S")
        color = colors.get(self.level, "white")
        level_str = self.level.value.upper()
        
        parts = [
            f"[dim]{time_str}[/]",
            f"[{color}]{level_str}[/]",
        ]
        
        if self.source:
            parts.append(f"[dim]{self.source}:[/]")
        
        parts.append(self.message)
        
        return " ".join(parts)
```

### 10.3 src/tui_app/models/pipeline.py

```python
"""
Modelos para configuração e resultados de pipeline.
"""

from typing import Any

from pydantic import BaseModel, Field


class StepConfig(BaseModel):
    """
    Configuração de um step da pipeline.
    
    Attributes:
        name: Nome do step
        enabled: Se o step está habilitado
        timeout_s: Timeout em segundos
        params: Parâmetros customizados
    """
    name: str
    enabled: bool = True
    timeout_s: int = 300
    params: dict[str, Any] = Field(default_factory=dict)


class PipelineConfig(BaseModel):
    """
    Configuração completa da pipeline.
    
    Attributes:
        name: Nome da pipeline
        steps: Lista de configurações de steps
        stop_on_error: Parar em caso de erro
    """
    name: str = "Pipeline"
    steps: list[StepConfig] = Field(default_factory=list)
    stop_on_error: bool = True


class StepResult(BaseModel):
    """
    Resultado de execução de um step.
    
    Attributes:
        step: Número do step
        name: Nome do step
        success: Se completou com sucesso
        duration_ms: Duração em ms
        output: Dados de saída
        error: Mensagem de erro (se falhou)
    """
    step: int
    name: str
    success: bool
    duration_ms: int | None = None
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
```

### 10.4 src/tui_app/models/settings.py

```python
"""
Modelo para configurações persistentes da aplicação.
"""

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class UISettings(BaseModel):
    """Configurações de interface."""
    theme: str = "vibe-neon"
    show_sidebar: bool = True
    show_timestamps: bool = True
    max_log_lines: int = 10000


class PipelineSettings(BaseModel):
    """Configurações de pipeline."""
    timeout_s: int = 300
    stop_on_error: bool = True


class AppSettings(BaseSettings):
    """
    Configurações da aplicação.
    
    Carrega de variáveis de ambiente com prefixo TUI_.
    """
    
    # Paths
    work_dir: Path = Field(default=Path.cwd())
    output_dir: Path = Field(default=Path.cwd() / "outputs")
    
    # UI
    ui: UISettings = Field(default_factory=UISettings)
    
    # Pipeline
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    
    class Config:
        env_prefix = "TUI_"
        env_nested_delimiter = "__"
```

---

## 11. Utilitários

### 11.1 src/tui_app/utils/__init__.py

```python
"""
Utilitários diversos.
"""

from tui_app.utils.ascii_art import get_logo, LOGOS
from tui_app.utils.formatting import (
    format_bytes,
    format_duration,
    format_percentage,
    truncate_path,
)

__all__ = [
    "get_logo",
    "LOGOS",
    "format_bytes",
    "format_duration",
    "format_percentage",
    "truncate_path",
]
```

### 11.2 src/tui_app/utils/ascii_art.py

```python
"""
Logos e ASCII art.
"""

# Logo pequeno (3 linhas)
LOGO_SMALL = r"""
╔╦╗╦ ╦╦
 ║ ║ ║║
 ╩ ╚═╝╩
""".strip()

# Logo médio (5 linhas)
LOGO_MEDIUM = r"""
████████╗██╗   ██╗██╗
╚══██╔══╝██║   ██║██║
   ██║   ██║   ██║██║
   ██║   ██║   ██║██║
   ██║   ╚██████╔╝██║
   ╚═╝    ╚═════╝ ╚═╝
""".strip()

# Logo estilo VIBE-LOG (como na imagem de referência)
LOGO_VIBE = r"""
██╗   ██╗██╗██████╗ ███████╗      ██╗      ██████╗  ██████╗ 
██║   ██║██║██╔══██╗██╔════╝      ██║     ██╔═══██╗██╔════╝ 
██║   ██║██║██████╔╝█████╗  █████╗██║     ██║   ██║██║  ███╗
╚██╗ ██╔╝██║██╔══██╗██╔══╝  ╚════╝██║     ██║   ██║██║   ██║
 ╚████╔╝ ██║██████╔╝███████╗      ███████╗╚██████╔╝╚██████╔╝
  ╚═══╝  ╚═╝╚═════╝ ╚══════╝      ╚══════╝ ╚═════╝  ╚═════╝ 
""".strip()

# Dicionário de logos
LOGOS = {
    "small": LOGO_SMALL,
    "medium": LOGO_MEDIUM,
    "vibe": LOGO_VIBE,
}


def get_logo(name: str = "small") -> str:
    """
    Obtém logo por nome.
    
    Args:
        name: Nome do logo (small, medium, vibe)
    
    Returns:
        String com ASCII art do logo
    """
    return LOGOS.get(name, LOGO_SMALL)


def colorize_logo(logo: str, colors: list[str] | None = None) -> str:
    """
    Adiciona cores Rich ao logo.
    
    Args:
        logo: String do logo
        colors: Lista de cores para aplicar às linhas
    
    Returns:
        Logo com markup Rich
    """
    if not colors:
        colors = ["cyan", "green", "magenta", "yellow"]
    
    lines = logo.split("\n")
    colored_lines = []
    
    for i, line in enumerate(lines):
        color = colors[i % len(colors)]
        colored_lines.append(f"[{color}]{line}[/]")
    
    return "\n".join(colored_lines)
```

### 11.3 src/tui_app/utils/formatting.py

```python
"""
Funções de formatação.
"""

from pathlib import Path


def format_bytes(size: int) -> str:
    """
    Formata tamanho em bytes para formato legível.
    
    Args:
        size: Tamanho em bytes
    
    Returns:
        String formatada (ex: "1.5 MB")
    """
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_duration(ms: int) -> str:
    """
    Formata duração em milissegundos.
    
    Args:
        ms: Duração em milissegundos
    
    Returns:
        String formatada (ex: "1m 30s")
    """
    if ms < 1000:
        return f"{ms}ms"
    
    seconds = ms / 1000
    
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes}m {secs}s"
    
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Formata valor como porcentagem.
    
    Args:
        value: Valor (0.0 a 100.0)
        decimals: Casas decimais
    
    Returns:
        String formatada (ex: "75.5%")
    """
    return f"{value:.{decimals}f}%"


def truncate_path(path: Path | str, max_length: int = 40) -> str:
    """
    Trunca path mantendo início e fim.
    
    Args:
        path: Path a truncar
        max_length: Comprimento máximo
    
    Returns:
        Path truncado (ex: "/home/.../file.pdf")
    """
    path_str = str(path)
    
    if len(path_str) <= max_length:
        return path_str
    
    # Mantém início e fim
    keep = (max_length - 3) // 2
    return f"{path_str[:keep]}...{path_str[-keep:]}"


def sanitize_filename(name: str) -> str:
    """
    Sanitiza string para uso como nome de arquivo.
    
    Args:
        name: Nome original
    
    Returns:
        Nome sanitizado
    """
    # Remove caracteres inválidos
    invalid = '<>:"/\\|?*'
    for char in invalid:
        name = name.replace(char, "_")
    
    # Remove espaços extras
    name = " ".join(name.split())
    
    # Limita tamanho
    if len(name) > 200:
        name = name[:200]
    
    return name
```

---

## 12. Testes

### 12.1 tests/conftest.py

```python
"""
Fixtures compartilhadas para testes.
"""

import pytest
from textual.pilot import Pilot

from tui_app.app import TUIApp


@pytest.fixture
def app() -> TUIApp:
    """Fixture que cria instância da App."""
    return TUIApp()


@pytest.fixture
async def pilot(app: TUIApp) -> Pilot:
    """Fixture que cria Pilot para testes."""
    async with app.run_test() as pilot:
        yield pilot
```

### 12.2 tests/test_app.py

```python
"""
Testes da aplicação principal.
"""

import pytest
from textual.pilot import Pilot

from tui_app.app import TUIApp


@pytest.mark.asyncio
async def test_app_starts():
    """Testa se app inicia sem erros."""
    app = TUIApp()
    async with app.run_test() as pilot:
        assert app.is_running


@pytest.mark.asyncio
async def test_app_has_main_screen():
    """Testa se main screen é carregada."""
    app = TUIApp()
    async with app.run_test() as pilot:
        assert app.screen.name == "main"


@pytest.mark.asyncio
async def test_theme_toggle():
    """Testa alternância de tema."""
    app = TUIApp()
    async with app.run_test() as pilot:
        initial_theme = app.theme
        await pilot.press("d")
        assert app.theme != initial_theme


@pytest.mark.asyncio
async def test_help_screen():
    """Testa abertura da tela de ajuda."""
    app = TUIApp()
    async with app.run_test() as pilot:
        await pilot.press("?")
        assert "help" in str(type(app.screen)).lower()
```

---

## 13. Guia de Customização

### 13.1 Renomeando o Template

1. Renomear diretório `tui_app` para nome do seu projeto
2. Atualizar `pyproject.toml`:
   - `name`
   - `project.scripts`
   - `tool.hatch.build.targets.wheel.packages`
3. Atualizar imports em todos os arquivos
4. Atualizar `APP_NAME` em `config.py`

### 13.2 Adicionando Novo Widget

```python
# src/tui_app/widgets/meu_widget.py

from textual.widget import Widget
from textual.app import ComposeResult

class MeuWidget(Widget):
    """Descrição do widget."""
    
    DEFAULT_CSS = """
    MeuWidget {
        border: heavy $border;
        background: $surface;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield ...
```

### 13.3 Adicionando Novo Tema

```python
# src/tui_app/themes/meu_tema.py

from textual.theme import Theme

MEU_TEMA = Theme(
    name="meu-tema",
    primary="#...",
    secondary="#...",
    # ...
)
```

Registrar em `themes/__init__.py` e `app.py`.

### 13.4 Integrando Pipeline Real

1. Implementar funções de step no formato:
   ```python
   def meu_step(context: dict, progress: Callable) -> dict:
       # Sua lógica aqui
       progress(50.0, "Metade concluída")
       return {"resultado": "..."}
   ```

2. Passar steps para o PipelineWorker:
   ```python
   steps = [
       ("Step 1", step_1_fn),
       ("Step 2", step_2_fn),
   ]
   await worker.run(steps, context={})
   ```

### 13.5 Removendo Componentes

Se não precisar de algum componente:

1. Delete o arquivo
2. Remova do `__init__.py` correspondente
3. Remova imports onde usado
4. Remova CSS relacionado

---

## Apêndice A: Paletas de Cores

### Dracula (base do vibe-neon)
```
Background:  #282a36
Current:     #44475a
Foreground:  #f8f8f2
Comment:     #6272a4
Cyan:        #8be9fd
Green:       #50fa7b
Orange:      #ffb86c
Pink:        #ff79c6
Purple:      #bd93f9
Red:         #ff5555
Yellow:      #f1fa8c
```

### Nord
```
Polar Night: #2e3440, #3b4252, #434c5e, #4c566a
Snow Storm:  #d8dee9, #e5e9f0, #eceff4
Frost:       #8fbcbb, #88c0d0, #81a1c1, #5e81ac
Aurora:      #bf616a, #d08770, #ebcb8b, #a3be8c, #b48ead
```

### Catppuccin Mocha
```
Base:        #1e1e2e
Mantle:      #181825
Crust:       #11111b
Text:        #cdd6f4
Subtext:     #a6adc8
Overlay:     #6c7086
Surface:     #313244
Blue:        #89b4fa
Green:       #a6e3a1
Mauve:       #cba6f7
Red:         #f38ba8
Yellow:      #f9e2af
```

---

## Apêndice B: Referência de Keybindings

| Tecla | Ação | Escopo |
|-------|------|--------|
| `q` | Sair | Global |
| `?` | Ajuda | Global |
| `d` | Toggle tema | Global |
| `b` | Toggle sidebar | MainScreen |
| `r` | Executar | MainScreen |
| `escape` | Cancelar | Global |
| `l` | Focar logs | MainScreen |
| `p` | Focar progresso | MainScreen |
| `ctrl+p` | Paleta de comandos | Global |
| `ctrl+s` | Screenshot | Global |
| `tab` | Próximo widget | Global |
| `shift+tab` | Widget anterior | Global |

---

*Documento gerado para TUI Template v1.0*
*Compatível com Textual 0.80.0+*
