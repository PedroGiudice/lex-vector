# Claude Code UI - Backend

Backend Python para interface grafica do Claude Code CLI.

Este backend fornece uma camada de abstracao para comunicacao com o Claude Code CLI via subprocess, permitindo que um frontend (Streamlit, FastAPI, etc.) interaja com o CLI de forma programatica.

## Estrutura

```
backend/
├── __init__.py      # Exports publicos
├── wrapper.py       # Comunicacao com CLI via subprocess
├── parser.py        # Parse de output (codigo, thinking, tools)
├── statusline.py    # Captura dados da statusline
├── session.py       # Gestao de sessoes e historico
├── config.py        # Configuracao persistente
├── models.py        # Dataclasses e tipos
└── exceptions.py    # Excecoes customizadas
```

## Instalacao

```bash
cd ferramentas/claude-ui

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou: .venv\Scripts\activate  # Windows

# Instalar dependencias de desenvolvimento
pip install -r requirements.txt
```

## Uso Basico

```python
from backend import ClaudeCodeWrapper, OutputParser, SessionManager

# Criar wrapper para o CLI
wrapper = ClaudeCodeWrapper(
    project_path="/path/to/project",
    on_output=lambda text: print(text),
    on_state_change=lambda state: print(f"Estado: {state}"),
    skip_permissions=True
)

# Iniciar CLI
wrapper.start()

# Enviar mensagem
wrapper.send("Explique este codigo")

# Obter output (non-blocking)
while True:
    lines = wrapper.get_output(timeout=0.5)
    for line in lines:
        print(line)

    # Verificar estado
    if wrapper.get_state() == CLIState.IDLE:
        break

# Parar CLI
wrapper.stop()
```

## Componentes

### ClaudeCodeWrapper

Core do backend. Spawna o processo CLI e gerencia comunicacao.

```python
from backend import ClaudeCodeWrapper, CLIState

# Callbacks
def on_output(text):
    print(f"Output: {text}")

def on_state_change(state):
    print(f"Estado mudou para: {state.value}")

# Criar wrapper
wrapper = ClaudeCodeWrapper(
    project_path="/home/user/projeto",
    on_output=on_output,
    on_state_change=on_state_change,
    skip_permissions=True,      # --dangerously-skip-permissions
    auto_reconnect=True         # Reconecta se processo morrer
)

# Context manager support
with wrapper:
    wrapper.send("Hello Claude")
    output = wrapper.get_output(timeout=1.0)
```

**Estados do CLI:**
- `DISCONNECTED` - Processo nao iniciado
- `STARTING` - Iniciando processo
- `IDLE` - Aguardando input
- `THINKING` - Processando (modelo pensando)
- `EXECUTING` - Executando tool (bash, file, etc.)
- `ERROR` - Erro no processo

### OutputParser

Parse de output do CLI em blocos estruturados.

```python
from backend import OutputParser, ContentType

parser = OutputParser()

# Parse output completo
raw_output = """
Here is some code:
```python
print("hello")
```
Error: File not found
"""

blocks = parser.parse(raw_output)
for block in blocks:
    print(f"Tipo: {block.type.value}")
    print(f"Conteudo: {block.content}")
    if block.type == ContentType.CODE:
        print(f"Linguagem: {block.language}")

# Parse linha a linha (streaming)
block = parser.parse_line("Error: Something went wrong")
if block and block.type == ContentType.ERROR:
    print(f"Erro detectado: {block.content}")
```

**Tipos de bloco:**
- `TEXT` - Texto normal
- `CODE` - Bloco de codigo com linguagem
- `THINKING` - Raciocinio do modelo
- `TOOL_CALL` - Chamada de ferramenta
- `TOOL_RESULT` - Resultado de ferramenta
- `ERROR` - Mensagem de erro
- `SYSTEM` - Mensagem de sistema

### StatusLineParser

Parse dados da statusline do CLI (model, tokens, git, etc.).

```python
from backend import StatusLineParser

parser = StatusLineParser()

# Parse JSON de statusline
json_str = '{"model": {"name": "claude-sonnet-4"}, "context": {"percent": 45.2}}'
data = parser.parse_json(json_str)

print(f"Modelo: {data.model}")
print(f"Contexto usado: {data.context_percent}%")

# Extrair de output misto
output = "Texto...\n{\"model\": {...}}\nMais texto"
data = parser.extract_from_output(output)

# Formatar para exibicao
summary = parser.format_summary(data)
print(summary)  # "Model: Claude Sonnet 4 | Context: 45.2%"
```

### SessionManager

Gestao de sessoes com persistencia em disco.

```python
from backend import SessionManager, Message

manager = SessionManager()  # Default: ~/.claude-ui/sessions/

# Criar nova sessao
session = manager.create_session("/home/user/projeto")
print(f"Sessao ID: {session.id}")

# Adicionar mensagem
message = Message(
    role="user",
    content="Hello Claude"
)
manager.add_message(session, message)

# Listar sessoes
sessions = manager.list_sessions()
for s in sessions:
    print(f"{s.id}: {s.project_path} ({len(s.messages)} msgs)")

# Carregar sessao existente
session = manager.get_session("uuid-da-sessao")

# Deletar sessao
manager.delete_session("uuid-da-sessao")
```

### ConfigManager

Configuracao persistente.

```python
from backend import ConfigManager

config_mgr = ConfigManager()  # Default: ~/.claude-ui/config.json

# Obter configuracao
config = config_mgr.get()
print(f"Tema: {config.theme}")
print(f"Skip permissions: {config.skip_permissions}")

# Atualizar configuracao
config_mgr.update(theme="light", font_size=16)

# Acessar valores especificos
show_model = config_mgr.get_value("statusline.show_model")

# Resetar para defaults
config_mgr.reset()
```

## Testes

```bash
cd ferramentas/claude-ui

# Rodar todos os testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=backend --cov-report=html

# Testes especificos
pytest tests/test_wrapper.py -v
pytest tests/test_parser.py -v
pytest tests/test_statusline.py -v
```

## Configuracao

Arquivos criados em `~/.claude-ui/`:

```
~/.claude-ui/
├── config.json       # Configuracoes gerais
└── sessions/         # Historico de sessoes
    ├── uuid1.json
    └── uuid2.json
```

### config.json

```json
{
  "default_project": "",
  "skip_permissions": true,
  "auto_reconnect": true,
  "theme": "dark",
  "font_family": "OpenDyslexic",
  "font_size": 14,
  "statusline": {
    "show_model": true,
    "show_path": true,
    "show_git": true,
    "show_context": true,
    "show_cost": true,
    "color_model": "#c084fc"
  }
}
```

## Requisitos

- Python 3.11+
- Claude Code CLI instalado (`npm install -g @anthropic-ai/claude-code`)

## Arquitetura

```
┌──────────────────────────────────────────────────┐
│                   Frontend                        │
│              (Streamlit/FastAPI)                  │
└─────────────────────┬────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────┐
│                   Backend                         │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │
│  │   Wrapper   │  │   Parser    │  │ Session  │  │
│  │ (subprocess)│  │(ANSI,blocks)│  │ Manager  │  │
│  └──────┬──────┘  └─────────────┘  └──────────┘  │
│         │         ┌─────────────┐  ┌──────────┐  │
│         │         │ StatusLine  │  │  Config  │  │
│         │         │   Parser    │  │ Manager  │  │
│         │         └─────────────┘  └──────────┘  │
└─────────┼────────────────────────────────────────┘
          │
┌─────────▼────────────────────────────────────────┐
│               Claude Code CLI                     │
│         (subprocess: stdin/stdout)                │
└──────────────────────────────────────────────────┘
```

## Licenca

MIT License

## Frontend

### Execucao

```bash
cd ferramentas/claude-ui
streamlit run frontend/app.py --server.port 8501
```

### Com acesso remoto (Tailscale)

```bash
# WSL
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0

# Windows PowerShell (Admin)
tailscale funnel 8501
```

### Estrutura

```
frontend/
├── app.py              # Entry point
├── components/
│   ├── chat.py         # Chat interface
│   ├── sidebar.py      # Sidebar controls
│   ├── statusline.py   # Footer status bar
│   └── file_explorer.py
├── styles/
│   └── theme.py        # CSS + colors
└── utils/
    └── helpers.py      # SVG icons
```

### Integracao com Backend

O frontend utiliza o backend para:
- `ClaudeCodeWrapper`: Comunicacao com o CLI via subprocess
- `OutputParser`: Parse de output em blocos estruturados
- `StatusLineParser`: Extracao de dados da statusline
- `SessionManager`: Persistencia de sessoes
- `ConfigManager`: Configuracoes persistentes em ~/.claude-ui/

### Dependencias

Frontend requer:
- Python 3.11+
- streamlit >= 1.28.0
- Backend instalado (somente stdlib)
