# Agents

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

## Agentes Disponiveis (18)

### CORE DEVELOPMENT (6)

| Agent | Skills Relacionadas | Uso |
|-------|---------------------|-----|
| `frontend-developer` | frontend-dev-guidelines | React/TypeScript |
| `backend-architect` | backend-dev-guidelines, error-tracking | Node/Express |
| `ai-engineer` | backend-dev-guidelines | LLM/RAG systems |
| `test-writer-fixer` | route-tester | Testes automatizados |
| `code-refactor-master` | frontend-dev-guidelines, backend-dev-guidelines | Refatoracao |
| `devops-automator` | error-tracking | CI/CD, Docker |

### PLANNING & DOCS (4)

| Agent | Skills Relacionadas | Uso |
|-------|---------------------|-----|
| `documentation-architect` | writing-plans | Documentacao tecnica |
| `plan-with-skills` | brainstorming, writing-plans | Planejamento |
| `plan-reviewer` | writing-plans | Review de planos |
| `gemini-assistant` | (externa) | Context offloading |

### PROJECT-SPECIFIC (5)

| Agent | Skills Relacionadas | Uso |
|-------|---------------------|-----|
| `fasthtml-bff-developer` | backend-dev-guidelines | FastHTML/HTMX |
| `auth-route-debugger` | route-tester | Auth debugging |
| `analise-dados-legal` | (dominio) | Analise juridica |
| `legal-articles-finder` | (dominio) | Busca de artigos |
| `web-research-specialist` | (externa) | Pesquisa web |

### UTILITY (3)

| Agent | Skills Relacionadas | Uso |
|-------|---------------------|-----|
| `vibe-log-report-generator` | mem-search | Session reports |
| `qualidade-codigo` | backend-dev-guidelines, frontend-dev-guidelines | Code audits |

---

## Como Usar

```
Use the [agent-name] agent to [task]
```

---

## Adicionar Novo Agente

Crie em `.claude/agents/meu-agente.md`:

```markdown
---
name: meu-agente
description: O que o agente faz
---

# Instrucoes do Agente
...
```

**IMPORTANTE:** Reinicie a sessao para descobrir novos agentes.

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
