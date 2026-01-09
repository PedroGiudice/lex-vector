# Subagentes

> **IMPORTANTE:** Estes sao **Subagentes** (Task tools executados via Claude Code), NAO "Agentes ADK".
> Agentes ADK autonomos (Gemini/Python) estao no repositorio [claude-experiments](https://github.com/PedroGiudice/claude-experiments).

**Status:** Fonte da verdade em `.claude/agents/` (repo), sync automatico para global

---

## Arquitetura

```
.claude/agents/           (FONTE - versionado no git)
    ↓ sync-agents.sh
~/.claude/agents/         (DERIVADO - global, auto-discovery)
```

Sincronizacao automatica no inicio de cada sessao.

---

## Subagentes Disponiveis (18)

### CORE DEVELOPMENT (6)

| Subagent | Skills Relacionadas | Uso |
|----------|---------------------|-----|
| `frontend-developer` | frontend-dev-guidelines | React/TypeScript |
| `backend-architect` | backend-dev-guidelines, error-tracking | Node/Express |
| `ai-engineer` | backend-dev-guidelines | LLM/RAG systems |
| `test-writer-fixer` | route-tester | Testes automatizados |
| `code-refactor-master` | frontend-dev-guidelines, backend-dev-guidelines | Refatoracao |
| `devops-automator` | error-tracking | CI/CD, Docker |

### PLANNING & DOCS (4)

| Subagent | Skills Relacionadas | Uso |
|----------|---------------------|-----|
| `documentation-architect` | writing-plans | Documentacao tecnica |
| `plan-with-skills` | brainstorming, writing-plans | Planejamento |
| `plan-reviewer` | writing-plans | Review de planos |
| `gemini-assistant` | (externa) | Context offloading |

### PROJECT-SPECIFIC (5)

| Subagent | Skills Relacionadas | Uso |
|----------|---------------------|-----|
| `fasthtml-bff-developer` | backend-dev-guidelines | FastHTML/HTMX |
| `auth-route-debugger` | route-tester | Auth debugging |
| `analise-dados-legal` | (dominio) | Analise juridica |
| `legal-articles-finder` | (dominio) | Busca de artigos |
| `web-research-specialist` | (externa) | Pesquisa web |

### UTILITY (3)

| Subagent | Skills Relacionadas | Uso |
|----------|---------------------|-----|
| `vibe-log-report-generator` | mem-search | Session reports |
| `qualidade-codigo` | backend-dev-guidelines, frontend-dev-guidelines | Code audits |

---

## Como Usar

```
Use the [subagent-name] subagent to [task]
```

---

## Adicionar Novo Subagente

Crie em `.claude/agents/meu-subagente.md`:

```markdown
---
name: meu-subagente
description: O que o subagente faz
---

# Instrucoes do Subagente
...
```

**IMPORTANTE:** Reinicie a sessao para descobrir novos subagentes.

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
