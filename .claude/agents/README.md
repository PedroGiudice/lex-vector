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

## Agentes Disponiveis (29)

### TUI (5)
- `tui-master` - Generalist
- `tui-architect` - Planning
- `tui-designer` - TCSS/styling
- `tui-developer` - Python
- `tui-debugger` - Diagnostics

### Legal/Project (6)
- `legal-articles-finder` - Busca artigos de leis
- `planejamento-legal` - Planning (PT-BR)
- `analise-dados-legal` - Data analysis (PT-BR)
- `documentacao` - Documentation (PT-BR)
- `desenvolvimento` - Development (PT-BR)
- `qualidade-codigo` - Code quality (PT-BR)

### Development (6)
- `frontend-developer` - React/TypeScript
- `backend-architect` - Backend design
- `rapid-prototyper` - MVPs
- `ai-engineer` - LLM/RAG systems
- `react-component-generator-ui` - React components
- `devops-automator` - CI/CD

### Quality & Review (5)
- `code-reviewer-superpowers` - Code review
- `code-refactor-master` - Refactoring
- `test-writer-fixer` - Testing
- `refactor-planner` - Refactor planning
- `plan-reviewer` - Plan review

### Research & Docs (3)
- `documentation-architect` - Documentation
- `web-research-specialist` - Web research
- `gemini-assistant` - Gemini CLI wrapper

### Routes/Auth (2)
- `auth-route-debugger` - Auth debugging
- `auth-route-tester` - Route testing

### UI Design (2)
- `ui-designer` - UI/UX design
- `plan-with-skills` - Planning with skills

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
