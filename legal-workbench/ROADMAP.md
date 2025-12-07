# Legal Workbench - Roadmap

## Em Andamento

### 1. Integracao Claude Code UI (wrapper Streamlit)

**Status:** Pendente
**Prioridade:** Alta

Debugar e corrigir o wrapper Streamlit arquivado (`ferramentas/_archived/claude-ui-streamlit/`) para integrar o Claude Code diretamente no Legal-Workbench.

**Problema atual:** O wrapper conecta ao Claude CLI mas nao recebe resposta apos enviar prompt.

**Objetivo:** Interface de chat integrada no dashboard, sem abrir nova aba.

**Arquivos:**
- `backend/wrapper.py` - subprocess manager
- `backend/parser.py` - output parser
- `frontend/app.py` - Streamlit UI

---

## Backlog

### 2. Modulo de Extracao de Documentos
- Integrar legal-text-extractor como modulo do dashboard
- Upload de PDF, extracao automatica, preview

### 3. Modulo de Pesquisa de Jurisprudencia
- Interface para busca em tribunais
- Integracao com agentes de coleta

### 4. Modulo de Artigos de Lei
- Busca de artigos por citacao
- Exibicao formatada com contexto

### 5. Workspace de Caso
- Tela unificada para trabalhar um caso
- Documentos + pesquisa + agentes + chat

---

## Concluido

- [x] Integracao claudecodeui (siteboon) para acesso mobile via Tailscale
- [x] PM2 para persistencia do servico
- [x] Link na sidebar do dashboard

---

Ultima atualizacao: 2025-12-07
