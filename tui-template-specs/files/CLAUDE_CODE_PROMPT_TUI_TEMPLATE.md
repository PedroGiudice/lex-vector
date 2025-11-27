# PROMPT PARA CLAUDE CODE: Criar TUI Template Maximalista

## USO

Copie todo o conteúdo abaixo (a partir de `<context>`) e cole diretamente no Claude Code CLI.

---

<context>
Projeto: TUI Template Maximalista para aplicações de terminal em Python.

Este é um template reutilizável baseado no framework Textual para criar TUIs profissionais com estética VIBE-LOG/Cyberpunk usando tema Dracula. O template segue a filosofia "maximalista": inclui todos os componentes possíveis para que o desenvolvedor remova o que não precisar, em vez de adicionar incrementalmente.

Ambiente: WSL2 Ubuntu 24.04, Python 3.11+
Diretório de trabalho: /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/tui-template
</context>

<architecture>
Sistema modular com separação clara entre UI, lógica e dados:

```
tui-template/
├── pyproject.toml                    # Configuração do projeto (hatchling)
├── README.md                         # Documentação principal
├── CHANGELOG.md                      # Histórico de versões
├── .gitignore                        # Ignores padrão Python
│
├── src/
│   └── tui_app/                      # Pacote principal
│       ├── __init__.py               # Metadata e versão
│       ├── __main__.py               # Entry point CLI
│       ├── app.py                    # Classe App principal
│       ├── config.py                 # Configurações e constantes
│       │
│       ├── screens/                  # Telas da aplicação
│       │   ├── __init__.py
│       │   ├── main_screen.py        # Dashboard principal
│       │   └── help_screen.py        # Ajuda e keybindings
│       │
│       ├── widgets/                  # Widgets customizados
│       │   ├── __init__.py
│       │   ├── header.py             # Header com logo ASCII
│       │   ├── sidebar.py            # Menu lateral
│       │   ├── log_panel.py          # RichLog estilizado
│       │   ├── progress_panel.py     # Multi-progress pipeline
│       │   ├── status_bar.py         # CPU, RAM, tempo
│       │   ├── file_browser.py       # DirectoryTree filtrado
│       │   ├── result_viewer.py      # Markdown viewer
│       │   ├── spinners.py           # Definições de spinners
│       │   ├── spinner_widget.py     # Widget de spinner universal
│       │   ├── blinker.py            # Cursor piscante
│       │   ├── powerline_status.py   # Barras Powerline
│       │   └── powerline_breadcrumb.py # Breadcrumb navegável
│       │
│       ├── themes/                   # Sistema de temas
│       │   ├── __init__.py           # Exporta temas
│       │   ├── vibe_neon.py          # Cyberpunk (Dracula)
│       │   ├── vibe_matrix.py        # Matrix verde
│       │   ├── vibe_synthwave.py     # Rosa/roxo
│       │   ├── minimal_dark.py       # Minimalista escuro
│       │   └── minimal_light.py      # Minimalista claro
│       │
│       ├── styles/                   # CSS externo (TCSS)
│       │   ├── base.tcss             # Variáveis e reset
│       │   ├── layout.tcss           # Grid e containers
│       │   ├── widgets.tcss          # Estilos de widgets
│       │   └── animations.tcss       # Spinners e transições
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
│       └── utils/                    # Utilitários
│           ├── __init__.py
│           ├── ascii_art.py          # Logos ASCII
│           └── formatting.py         # Formatação
│
├── assets/                           # Recursos estáticos
│   └── logos/
│       └── logo_small.txt
│
├── tests/                            # Testes
│   ├── __init__.py
│   ├── conftest.py
│   └── test_app.py
│
└── scripts/                          # Scripts auxiliares
    └── run_dev.sh
```

Componentes principais:
1. **App (app.py)**: Coordenador central, registra temas, define keybindings globais
2. **MainScreen**: Dashboard com sidebar, progress panel, log panel, result viewer
3. **Widgets**: Componentes reutilizáveis independentes
4. **Themes**: Sistema de temas via Textual Theme API
5. **Workers**: Execução assíncrona de pipelines sem travar UI
6. **Messages**: Comunicação desacoplada entre componentes
</architecture>

<implementation_plan>
Execute na ordem exata. Cada task deve ser completada antes de prosseguir.

## FASE 1: ESTRUTURA BASE

### Task 1: Criar estrutura de diretórios
```bash
mkdir -p tui-template/src/tui_app/{screens,widgets,themes,styles,workers,messages,models,utils}
mkdir -p tui-template/{assets/logos,tests,scripts}
cd tui-template
```

### Task 2: Criar pyproject.toml
- name: "tui-template"
- version: "0.1.0"
- dependencies: textual>=0.80.0, rich>=13.0.0, pydantic>=2.0.0, pydantic-settings>=2.0.0
- dev dependencies: textual-dev, pytest, pytest-asyncio, pytest-cov, ruff, mypy
- entry point: tui-app = "tui_app.__main__:main"
- build-backend: hatchling

### Task 3: Criar .gitignore
- Python: __pycache__, *.pyc, .mypy_cache, .pytest_cache
- Virtual env: venv/, .venv/
- IDE: .vscode/, .idea/
- Build: dist/, build/, *.egg-info

### Task 4: Criar README.md básico
- Título, descrição do template
- Requisitos (Python 3.11+, Nerd Fonts recomendado)
- Instalação e uso

## FASE 2: CONFIGURAÇÃO E CORE

### Task 5: Criar src/tui_app/__init__.py
- __version__ = "0.1.0"
- __author__
- Export TUIApp

### Task 6: Criar src/tui_app/config.py
- PACKAGE_ROOT, STYLES_DIR usando Path(__file__).parent
- APP_NAME, APP_VERSION
- MAX_LOG_LINES = 10_000
- REFRESH_RATE_MS = 50
- DEFAULT_BINDINGS dict
- Colors class com paleta Dracula

### Task 7: Criar src/tui_app/__main__.py
- argparse: --theme, --dev, --version
- main() que instancia e executa TUIApp

## FASE 3: SISTEMA DE TEMAS

### Task 8: Criar themes/vibe_neon.py (Tema padrão Dracula)
```python
from textual.theme import Theme

VIBE_NEON_THEME = Theme(
    name="vibe-neon",
    primary="#8be9fd",      # Cyan neon
    secondary="#bd93f9",    # Roxo
    accent="#ff79c6",       # Magenta neon
    foreground="#f8f8f2",   # Texto claro
    background="#0d0d0d",   # Void black
    surface="#1a1a2e",      # Surface
    panel="#16213e",        # Painéis
    success="#50fa7b",      # Verde neon
    warning="#ffb86c",      # Laranja
    error="#ff5555",        # Vermelho
    dark=True,
    variables={
        "block-cursor-background": "#ff79c6",
        "block-cursor-foreground": "#0d0d0d",
        "border": "#8be9fd",
        "border-blurred": "#44475a",
        "footer-key-foreground": "#50fa7b",
        "scrollbar": "#44475a",
        "scrollbar-hover": "#6272a4",
        "scrollbar-active": "#8be9fd",
    },
)
```

### Task 9: Criar themes/vibe_matrix.py, vibe_synthwave.py, minimal_dark.py, minimal_light.py
- Matrix: verde (#00ff41) sobre preto
- Synthwave: magenta/cyan sobre roxo escuro
- Minimal dark: azul suave sobre azul escuro
- Minimal light: azul Google sobre branco

### Task 10: Criar themes/__init__.py
- Exportar todos os temas
- Dict THEMES mapeando nome para Theme

## FASE 4: ESTILOS CSS (TCSS)

### Task 11: Criar styles/base.tcss
- Variáveis $neon-cyan, $neon-magenta, etc.
- Reset: Screen background/color
- Scrollbar styling
- Classes utilitárias: .muted, .error-text, .success-text, .hidden

### Task 12: Criar styles/layout.tcss
- #main-screen grid layout
- #sidebar, #content-area, #top-section, #bottom-section
- .panel base styling
- Modal overlay
- Media queries para terminais pequenos

### Task 13: Criar styles/widgets.tcss
- LogPanel, PipelineProgress, StageProgress
- Sidebar, FileBrowser, ResultViewer
- StatusBar, SpinnerWidget, Blinker
- PowerlineBar, PowerlineHeader, PowerlineFooter
- Button, Input styling

### Task 14: Criar styles/animations.tcss
- LoadingIndicator
- ProgressBar styling
- Toast notifications
- Glow effects simulados

## FASE 5: MESSAGES

### Task 15: Criar messages/pipeline_messages.py
```python
from dataclasses import dataclass
from textual.message import Message

@dataclass
class PipelineStarted(Message):
    total_steps: int

@dataclass
class StepStarted(Message):
    step: int
    name: str

@dataclass
class StepProgress(Message):
    step: int
    progress: float
    message: str | None = None

@dataclass
class StepCompleted(Message):
    step: int
    result: dict | None = None

@dataclass
class StepError(Message):
    step: int
    error: str

@dataclass
class PipelineCompleted(Message):
    results: dict

@dataclass
class PipelineAborted(Message):
    reason: str
    step: int | None = None
```

### Task 16: Criar messages/system_messages.py
- LogMessage(message, level, source)
- StatusUpdate(status, style)
- FileLoaded(path, size_bytes)

### Task 17: Criar messages/__init__.py
- Exportar todas as messages

## FASE 6: MODELS

### Task 18: Criar models/log_entry.py
- LogLevel enum (DEBUG, INFO, WARNING, ERROR, SUCCESS)
- LogEntry Pydantic model com format_rich()

### Task 19: Criar models/pipeline.py
- StepConfig(name, enabled, timeout_s, params)
- PipelineConfig(name, steps, stop_on_error)
- StepResult(step, name, success, duration_ms, output, error)

### Task 20: Criar models/settings.py
- UISettings(theme, show_sidebar, show_timestamps)
- PipelineSettings(timeout_s, stop_on_error)
- AppSettings usando pydantic-settings

### Task 21: Criar models/__init__.py

## FASE 7: UTILS

### Task 22: Criar utils/ascii_art.py
- LOGO_SMALL, LOGO_MEDIUM, LOGO_VIBE
- get_logo(name) function
- colorize_logo(logo, colors) function

### Task 23: Criar utils/formatting.py
- format_bytes(size)
- format_duration(ms)
- format_percentage(value, decimals)
- truncate_path(path, max_length)
- sanitize_filename(name)

### Task 24: Criar utils/__init__.py

## FASE 8: WIDGETS BASE

### Task 25: Criar widgets/header.py
- Header widget com logo ASCII
- Seções: logo, título, status
- set_status(status, style) method

### Task 26: Criar widgets/sidebar.py
- Sidebar com OptionList
- collapsed reactive
- OptionSelected message
- toggle() method

### Task 27: Criar widgets/log_panel.py
- LogPanel extends RichLog
- Níveis coloridos: debug, info, warning, error, success
- show_timestamps reactive
- Métodos: log(), debug(), info(), warning(), error(), success()
- separator(), header() para formatação

### Task 28: Criar widgets/progress_panel.py
- StageProgress widget (label + ProgressBar + status)
- PipelineProgress container
- Status classes: pending, running, completed, error
- Métodos: start_stage, update_stage, complete_stage, error_stage, reset

### Task 29: Criar widgets/status_bar.py
- StatusBar com métricas
- cpu_percent, ram_percent reactives
- Timer para atualização automática (psutil)
- set_status() method

### Task 30: Criar widgets/file_browser.py
- FilteredDirectoryTree com filtro de extensões
- FileBrowser wrapper
- FileSelected message
- set_path() method

### Task 31: Criar widgets/result_viewer.py
- ResultViewer com Markdown widget
- load_content(content, source)
- load_file(path)
- clear()

## FASE 9: WIDGETS AVANÇADOS (SPINNERS/POWERLINE)

### Task 32: Criar widgets/spinners.py
- SpinnerDefinition dataclass
- Spinners customizados: claude, thinking, pulse_bar, neon, wave, matrix, processing, orbital, dna, minimal, cyber
- CUSTOM_SPINNERS dict

### Task 33: Criar widgets/spinner_widget.py
- SpinnerWidget universal
- Suporte a Rich spinners e customizados
- is_spinning reactive
- pause(), resume(), set_text()

### Task 34: Criar widgets/blinker.py
- Blinker cursor piscante
- CURSOR_CHARS: block, line, underscore, pipe, beam, dot, square
- InputCursor com prompt + input + cursor

### Task 35: Criar widgets/powerline_status.py
- PowerlineSegment dataclass
- PowerlineBar widget
- PowerlineHeader (app_name, version, time)
- PowerlineFooter

### Task 36: Criar widgets/powerline_breadcrumb.py
- PowerlineBreadcrumb navegável
- CrumbClicked message
- set_items(), push(), pop()

### Task 37: Criar widgets/__init__.py
- Exportar todos os widgets

## FASE 10: WORKERS

### Task 38: Criar workers/base_worker.py
- BaseWorker ABC
- app reference, _cancelled flag
- cancel(), reset(), post_message()
- Abstract run() method

### Task 39: Criar workers/pipeline_worker.py
- PipelineWorker extends BaseWorker
- StepFunction type alias
- @work decorator com thread=True
- run(steps, context) executa pipeline
- Emite todas as messages de pipeline

### Task 40: Criar workers/__init__.py

## FASE 11: SCREENS

### Task 41: Criar screens/main_screen.py
- MainScreen com layout:
  - Header (topo)
  - Sidebar (esquerda, collapsible)
  - Content area:
    - PipelineProgress (top)
    - LogPanel + ResultViewer (bottom, side by side)
  - StatusBar (bottom)
  - Footer
- action_toggle_sidebar()
- run_pipeline(), cancel_operation()
- Handlers para todas as pipeline messages
- Handler para Sidebar.OptionSelected, FileBrowser.FileSelected

### Task 42: Criar screens/help_screen.py
- HelpScreen modal
- HELP_CONTENT markdown com keybindings
- Dismiss com Escape ou Q

### Task 43: Criar screens/__init__.py

## FASE 12: APP PRINCIPAL

### Task 44: Criar app.py
- TUIApp extends App
- TITLE, SUB_TITLE
- CSS_PATH lista de arquivos .tcss
- BINDINGS: q, ?, d, r, escape, b, l, p, ctrl+p, ctrl+s
- SCREENS dict
- on_mount(): registra temas, aplica tema inicial, push main screen
- Actions: toggle_dark, show_help, toggle_sidebar, focus_log, focus_progress, run_pipeline, cancel_operation, screenshot
- Handlers para pipeline messages

## FASE 13: TESTES E FINALIZAÇÃO

### Task 45: Criar tests/conftest.py
- Fixture app() -> TUIApp
- Fixture pilot(app) async

### Task 46: Criar tests/test_app.py
- test_app_starts()
- test_app_has_main_screen()
- test_theme_toggle()
- test_help_screen()

### Task 47: Criar scripts/run_dev.sh
```bash
#!/bin/bash
cd "$(dirname "$0")/.."
pip install -e ".[dev]" --break-system-packages
textual run --dev src/tui_app/app.py
```

### Task 48: Criar assets/logos/logo_small.txt
```
╔╦╗╦ ╦╦
 ║ ║ ║║
 ╩ ╚═╝╩
```

### Task 49: Criar CHANGELOG.md
- v0.1.0: Initial release

### Task 50: Verificação final
```bash
# Instalar em modo dev
pip install -e ".[dev]" --break-system-packages

# Verificar sintaxe
ruff check src/

# Executar testes
pytest tests/ -v

# Executar app
python -m tui_app
```
</implementation_plan>

<technical_specifications>
## Versões Exatas
- Python: 3.11+
- Textual: >=0.80.0
- Rich: >=13.0.0
- Pydantic: >=2.0.0
- pydantic-settings: >=2.0.0

## Padrões de Código
- Type hints em todas as funções públicas
- Docstrings Google style
- Line length: 100
- Imports ordenados (ruff)

## Paleta de Cores (Dracula Base)
```
Background:  #0d0d0d (void black)
Surface:     #1a1a2e
Panel:       #16213e
Foreground:  #f8f8f2
Muted:       #6272a4
Disabled:    #44475a
Cyan:        #8be9fd
Green:       #50fa7b
Magenta:     #ff79c6
Yellow:      #f1fa8c
Orange:      #ffb86c
Red:         #ff5555
Purple:      #bd93f9
```

## Keybindings Padrão
| Tecla | Ação |
|-------|------|
| q | Sair |
| ? | Ajuda |
| d | Toggle tema |
| b | Toggle sidebar |
| r | Executar |
| escape | Cancelar |
| l | Focar logs |
| p | Focar progresso |
| ctrl+p | Paleta de comandos |
| ctrl+s | Screenshot |
</technical_specifications>

<constraints>
1. NÃO usar emojis em nenhum arquivo de código ou documentação
2. Todos os paths devem usar Path do pathlib, nunca strings hardcoded
3. Todos os arquivos Python devem ter encoding UTF-8
4. CSS usa variáveis do tema ($primary, $surface, etc.) para permitir temas
5. Widgets devem ter DEFAULT_CSS inline para funcionarem standalone
6. Messages devem ser dataclasses para facilitar serialização
7. Workers devem verificar is_cancelled em loops longos
8. Não instalar nada globalmente - usar --break-system-packages quando necessário
</constraints>

<success_criteria>
1. `pip install -e ".[dev]"` executa sem erros
2. `ruff check src/` passa sem erros
3. `python -m tui_app` inicia e exibe a interface
4. Tecla `?` abre tela de ajuda
5. Tecla `d` alterna entre tema claro e escuro
6. Tecla `b` mostra/esconde sidebar
7. Tecla `q` fecha a aplicação
8. `pytest tests/` passa todos os testes
9. Todos os widgets renderizam corretamente no tema padrão
</success_criteria>

<verification_protocol>
Após cada fase, execute:

```bash
# Verificar sintaxe
ruff check src/ --fix

# Verificar tipos (opcional, pode ter warnings)
mypy src/ --ignore-missing-imports

# Se fase inclui testes
pytest tests/ -v
```

Após Task 50 (final):
```bash
# Verificação completa
pip install -e ".[dev]" --break-system-packages
ruff check src/
pytest tests/ -v
python -m tui_app --help
python -m tui_app
```
</verification_protocol>

<claude_code_directives>
- Trabalhe em: /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/tui-template
- Crie progress.json para rastrear estado de conclusão
- Após cada fase completada, atualize progress.json
- Se algum step falhar, documente em errors.log antes de parar
- Ao completar, gere IMPLEMENTATION_REPORT.md com resumo do que foi construído
- Use `git init` no início e faça commits após cada fase
- Mensagens de commit em português: "Fase N: descrição"
</claude_code_directives>
