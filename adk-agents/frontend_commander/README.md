# Frontend Commander

Agente autônomo ADK que detecta novos backends Docker e gera UI automaticamente.

## Conceito

```
┌─────────────────────────────────────────────────────────────┐
│                    DOCKER WATCHER                           │
│  Monitora: docker events --filter 'event=start'             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND COMMANDER (Gemini 3 Pro)              │
│                                                              │
│  1. Detecta novo container backend                          │
│  2. Analisa código + endpoints                              │
│  3. Pergunta: "Como deve ser a UI?"                         │
│  4. Gera FastHTML/React component                           │
│  5. Integra em legal-workbench                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    OUTPUT                                    │
│  legal-workbench/poc-fasthtml-stj/components/{service}.py   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Setup
cd adk-agents
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure API Key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 3. Run watcher (foreground)
python -m frontend-commander.watcher

# 3a. Run watcher (daemon mode)
python -m frontend-commander.watcher --daemon

# 3b. Check once
python -m frontend-commander.watcher --once
```

## Modos de Operação

| Modo | Comando | Uso |
|------|---------|-----|
| **Contínuo** | `python -m frontend-commander.watcher` | Polling a cada 30s |
| **Daemon** | `--daemon` | Real-time via docker events |
| **Once** | `--once` | Executa uma vez e sai |

## Modelo Selection Strategy

| Contexto | Modelo | Razão |
|----------|--------|-------|
| < 50k tokens | `gemini-3-pro-preview` | Melhor raciocínio |
| 50k-200k tokens | `gemini-2.5-flash` | Rápido, bom contexto |
| > 200k tokens | `gemini-2.5-pro` | Melhor long context |

## Tools Disponíveis

| Tool | Função |
|------|--------|
| `list_docker_containers` | Lista containers rodando |
| `inspect_container` | Detalhes de um container |
| `read_backend_code` | Lê código Python do backend |
| `read_openapi_spec` | Lê especificação OpenAPI |
| `list_existing_modules` | Lista módulos UI existentes |
| `write_frontend_module` | Escreve novo módulo |
| `get_service_endpoints` | Extrai endpoints da API |

## Estrutura

```
frontend-commander/
├── __init__.py          # Export do agente
├── agent.py             # Definição do agente ADK
├── tools.py             # Ferramentas customizadas
├── watcher.py           # Monitor de containers
└── README.md            # Esta documentação
```

## Integração com legal-workbench

O agente gera código em:
- **FastHTML**: `legal-workbench/poc-fasthtml-stj/components/`
- **Streamlit**: `legal-workbench/modules/`
- **React**: `legal-workbench/poc-react-stj/src/components/`

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
