# Claude Code Projetos

Sistema de automacao juridica brasileira. Monitoramento de publicacoes, extracao de documentos, analise NLP e RAG juridico.

## Stack

- **Runtime:** Python 3.11, Node.js v22
- **Ambiente:** Ubuntu 24.04 (WSL2)
- **Orquestracao:** Claude Code com hooks e skills

## Estrutura do Projeto

| Diretorio | Proposito | Quando Usar |
|-----------|-----------|-------------|
| `legal-workbench/` | Dashboard juridico (projeto ativo) | UI, ferramentas integradas |
| `adk-agents/` | Agentes Google ADK | Orquestracao multi-agente |
| `comandos/` | CLI scripts | Operacoes atomicas (fetch, parse, validate) |
| `shared/` | Codigo compartilhado | Utils, path helpers, memoria |
| `skills/` | Skills custom | Guidelines especializadas |
| `.claude/` | Config Claude Code | Agents, hooks, skills managed |

## Comandos Essenciais

```bash
# Executar projeto Python
cd <projeto> && source .venv/bin/activate && python main.py

# Validar hooks
tail -50 ~/.vibe-log/hooks.log

# Legal Workbench
cd legal-workbench && source .venv/bin/activate && streamlit run app.py
```

## Documentacao

| Arquivo | Conteudo |
|---------|----------|
| `CLAUDE.md` | Regras operacionais para Claude Code |
| `ARCHITECTURE.md` | North Star (principios inviolaveis) |
| `DISASTER_HISTORY.md` | Licoes aprendidas de falhas |

## Task Execution Patterns

- **Swarm**: Medium-complex tasks with parallel subagents
- **Breakdown**: Decompose large tasks into atomic units before execution

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
