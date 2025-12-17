# ADK Agents

Agentes Python autônomos usando Google ADK (Agent Development Kit) + Gemini.

## Quick Start

```bash
cd adk-agents

# Setup automático
./setup.sh

# OU manual:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edite .env e adicione GOOGLE_API_KEY
```

## API Key

1. Obtenha em: https://aistudio.google.com/apikey
2. Adicione em `adk-agents/.env`:
   ```
   GOOGLE_API_KEY=sua_key_aqui
   ```

## Agentes Disponíveis

| Agente | Função | Modelo | Status |
|--------|--------|--------|--------|
| `frontend-commander` | Gera UI para novos backends | Dinâmico (3 Pro default) | ✅ Ready |
| `legal-tech-frontend-specialist` | React/TS para legal tech | Dinâmico (3 Pro default) | ✅ Ready |
| `ai-engineer` | LLM/RAG systems | Dinâmico (3 Pro default) | ✅ Ready |
| `backend-architect` | Design de backend | Dinâmico (3 Pro default) | ✅ Ready |
| `code-reviewer-superpowers` | Code review | Dinâmico (3 Pro default) | ✅ Ready |
| `devops-automator` | CI/CD, infra | Dinâmico (3 Pro default) | ✅ Ready |
| `documentation-architect` | Documentação | Dinâmico (3 Pro default) | ✅ Ready |
| `dpp-agent` | Pré-processamento forense | Dinâmico (3 Pro default) | ✅ Ready |
| `gemini-assistant` | Context offloading | **Flash Fixo** | ✅ Ready |
| `refactor-planner` | Planos de refatoração | Dinâmico (3 Pro default) | ✅ Ready |
| `streamlit-frontend-specialist` | UIs Streamlit | Dinâmico (3 Pro default) | ✅ Ready |
| `test-writer-fixer` | Testes automatizados | Dinâmico (3 Pro default) | ✅ Ready |

### Seleção de Modelo

Todos os agentes (exceto `gemini-assistant`) usam **seleção dinâmica**:
- **<50k tokens**: Gemini 3 Pro (melhor raciocínio)
- **50k-200k tokens**: Gemini 2.5 Flash (velocidade)
- **>200k tokens**: Gemini 2.5 Pro (contexto longo)

Cada agente expõe `get_agent_for_large_context()` para operações com contexto extenso:

```python
from ai_engineer.agent import root_agent, get_agent_for_large_context

# Default: Gemini 3 Pro
agent = root_agent

# Para contexto grande: modelo selecionado automaticamente
agent = get_agent_for_large_context(file_paths=["large1.py", "large2.py"])
```

O `gemini-assistant` usa **Flash fixo** porque sua função é context offloading - velocidade é prioridade.

## Modelos Gemini (Dez 2025)

| Modelo | ID | Uso |
|--------|-----|-----|
| **Gemini 3 Pro** | `gemini-3-pro-preview` | Raciocínio, agentes (default) |
| **Gemini 2.5 Pro** | `gemini-2.5-pro` | Long context (>200k tokens) |
| **Gemini 2.5 Flash** | `gemini-2.5-flash` | Fast, bulk (50k-200k tokens) |
| **Embedding** | `gemini-embedding-001` | RAG, semantic search |

## Seleção Dinâmica de Modelo

```python
from shared.model_selector import get_model_for_context

# Automático baseado em tamanho
model = get_model_for_context(file_path="large_file.py")

# Ou direto
from shared.config import Config
model = Config.MODELS.GEMINI_3_PRO
```

## Executando Agentes

### Via ADK CLI
```bash
source .venv/bin/activate
adk run frontend-commander
```

### Via Python
```bash
source .venv/bin/activate
python -m frontend-commander.watcher --once
```

### Via Import
```python
from google.adk import Runner
from frontend_commander.agent import root_agent

runner = Runner(agent=root_agent)
result = runner.run("Analise o backend stj-api")
```

## Estrutura

```
adk-agents/
├── shared/                  # Utilitários compartilhados
│   ├── config.py           # Modelos e thresholds
│   └── model_selector.py   # Seleção dinâmica
├── frontend-commander/      # Gerador de UI autônomo
├── legal-tech-frontend-specialist/
├── ai-engineer/
├── ... outros agentes
├── requirements.txt
├── .env.example
└── setup.sh
```

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota

---

## Sources

- [Google ADK Docs](https://google.github.io/adk-docs/)
- [Google ADK Python](https://github.com/google/adk-python)
- [Gemini API Models](https://ai.google.dev/gemini-api/docs/models)
- [Gemini Embedding](https://developers.googleblog.com/en/gemini-embedding-available-gemini-api/)
