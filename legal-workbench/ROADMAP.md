# Legal Workbench - Roadmap

## ALERTA CRÍTICO: Drift de Funcionalidade (2025-12-11)

Durante a dockerização do projeto, os módulos do Streamlit Hub foram implementados com funcionalidades **INCORRETAS** que não correspondem ao propósito original das ferramentas backend.

### Divergências Identificadas

| Módulo | Implementado (ERRADO) | Propósito Real (CORRETO) |
|--------|----------------------|--------------------------|
| **Trello MCP** | Apenas criação de cartões | **EXTRAÇÃO** de dados de quadros e cartões existentes + criação |
| **STJ Dados Abertos** | Apenas consulta de jurisprudência | **DOWNLOAD retroativo completo** de toda jurisprudência + consulta local |
| **Legal Doc Assembler** | Geração de documentos com dados básicos (nome das partes, etc.) | **Sistema de templates**: usuário transforma .docx em template, sistema popula com dados (ex: do Trello) para gerar petições |

### Status do Backend: A VERIFICAR

As funções originais do backend podem ainda existir intactas. O problema pode estar:
1. **Apenas no frontend** - Streamlit não expõe as funções corretas
2. **No backend também** - Funções foram modificadas/removidas

---

## Fase 0: Correção de Funcionalidades (URGENTE)

### 0.1 Trello MCP
- [ ] Verificar se backend tem funções de extração (get boards, get cards, get lists)
- [ ] Corrigir frontend para expor:
  - Listar quadros do usuário
  - Extrair cartões de um quadro
  - Extrair dados estruturados (nome, descrição, labels, checklists, etc.)
  - Manter criação de cartões como funcionalidade secundária

### 0.2 STJ Dados Abertos
- [ ] Verificar se backend tem funções de download em massa
- [ ] Corrigir frontend para expor:
  - Download retroativo de jurisprudência (por período, por relator, por classe)
  - Sincronização incremental
  - Consulta local no banco DuckDB
  - Estatísticas do banco local

### 0.3 Legal Doc Assembler
- [ ] Verificar se backend tem sistema de templates
- [ ] Corrigir frontend para expor:
  - Upload de documento .docx base
  - Interface para definir placeholders/variáveis no template
  - Conexão com fontes de dados (Trello, manual, etc.)
  - Geração em lote de documentos a partir de dados

---

## Em Andamento

### 1. Integração Claude Code UI (wrapper Streamlit)

**Status:** Pendente
**Prioridade:** Alta

Debugar e corrigir o wrapper Streamlit arquivado (`ferramentas/_archived/claude-ui-streamlit/`) para integrar o Claude Code diretamente no Legal-Workbench.

**Problema atual:** O wrapper conecta ao Claude CLI mas não recebe resposta após enviar prompt.

**Objetivo:** Interface de chat integrada no dashboard, sem abrir nova aba.

**Arquivos:**
- `backend/wrapper.py` - subprocess manager
- `backend/parser.py` - output parser
- `frontend/app.py` - Streamlit UI

---

## Backlog

### 2. Módulo de Extração de Documentos
- Integrar legal-text-extractor como módulo do dashboard
- Upload de PDF, extração automática, preview

### 3. Módulo de Pesquisa de Jurisprudência
- Interface para busca em tribunais
- Integração com agentes de coleta

### 4. Módulo de Artigos de Lei
- Busca de artigos por citação
- Exibição formatada com contexto

### 5. Workspace de Caso
- Tela unificada para trabalhar um caso
- Documentos + pesquisa + agentes + chat

---

## Melhorias de Infraestrutura (Futuro)

### Docker
- [ ] Customização de porta HTTP (usar porta 80 para acesso sem especificar porta)
- [ ] Configuração de domínio local (ex: `legalworkbench.local`)
- [ ] Reverse proxy com nginx/traefik (opcional)
- [ ] HTTPS com certificados auto-assinados (desenvolvimento)

### Persistência
- [ ] Docker secrets para API keys (produção)
- [ ] Backup automático do DuckDB (STJ)
- [ ] Volume compartilhado para templates

---

## Concluído

- [x] Integração claudecodeui (siteboon) para acesso mobile via Tailscale
- [x] PM2 para persistência do serviço
- [x] Link na sidebar do dashboard
- [x] Dockerização completa com 6 serviços (2025-12-11)
- [x] Healthchecks funcionando em todos containers

---

## Notas de Implementação

### Princípios
1. **Fixes definitivos** - Nunca patches ou hot-fixes (ver CLAUDE.md seção 5)
2. **Backend-first** - Verificar que backend está correto antes de ajustar frontend
3. **UI-validation** - Toda alteração deve ser testada via Streamlit

### Referências Backend
- Trello: `ferramentas/trello-mcp/`
- STJ: `ferramentas/stj-dados-abertos/`
- Doc Assembler: `ferramentas/legal-doc-assembler/`
- Text Extractor: `ferramentas/legal-text-extractor/`

### Referências Frontend
- Modules: `modules/`
- Docker services: `docker/services/*/`

---

*Última atualização: 2025-12-11*
