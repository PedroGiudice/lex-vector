# Legal Workbench - Roadmap

## Em Andamento

### 1. Integracao Claude Code UI (wrapper Streamlit)

**Status:** Arquivado (baixa prioridade)
**Prioridade:** Baixa

Wrapper Streamlit arquivado em `ferramentas/_archived/claude-ui-streamlit/`.

**Problema conhecido:** O wrapper conecta ao Claude CLI mas nao recebe resposta apos enviar prompt.

**Solucao atual:** Usando claudecodeui (siteboon) via sidebar link. Funciona bem para acesso mobile.

**Arquivos (arquivados):**
- `backend/wrapper.py` - subprocess manager
- `backend/parser.py` - output parser
- `frontend/app.py` - Streamlit UI

---

## Backlog

### 2. UI para Prompt Library
- Criar modulo Streamlit para `ferramentas/prompt-library`
- Interface para busca, preview e renderizacao de prompts

### 3. Workspace de Caso
- Tela unificada para trabalhar um caso
- Documentos + pesquisa + agentes + chat

### 4. CLI Reference para STJ Dados Abertos
- Documentar comandos CLI (stj-init, stj-download-periodo, etc.)

---

## Concluido

- [x] Integracao claudecodeui (siteboon) para acesso mobile via Tailscale
- [x] PM2 para persistencia do servico
- [x] Link na sidebar do dashboard
- [x] **Modulo Text Extractor** - Upload de PDF, extracao automatica, preview
- [x] **Modulo Document Assembler** - Templates DOCX com merge de dados
- [x] **Modulo STJ Dados Abertos** - Interface para busca em jurisprudencia STJ (DuckDB)
- [x] **Modulo Trello MCP** - Integracao MCP para gestao de tarefas
- [x] **Prompt Library** - Backend para gerenciamento de templates de prompts (sem UI)

---

Ultima atualizacao: 2025-12-10
