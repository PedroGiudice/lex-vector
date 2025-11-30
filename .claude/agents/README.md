# Agents

**Status:** Consolidados em `~/.claude/agents/` (global)

---

## Estrutura Atual

Todos os 59 agentes foram movidos para a pasta global do usuário:

```
~/.claude/agents/
├── tui-*.md           (5)  # TUI specialists
├── legal-*.md         (2)  # Legal extraction
├── *-legal.md         (5)  # Legal project (PT-BR)
├── *-lst97.md         (27) # LST97 collection
├── *-studio.md        (5)  # Studio collection
├── *-ui.md            (2)  # UI specialists
└── outros             (13) # Development, meta, etc
```

**Total: 59 agentes**

---

## Por que Global?

1. **Disponibilidade:** Agentes disponíveis em qualquer projeto Claude Code
2. **Manutenção:** Um único lugar para atualizar
3. **Descoberta:** Claude Code descobre automaticamente de `~/.claude/agents/`

---

## Categorias

### TUI (5)
- `tui-master` - Generalist
- `tui-architect` - Planning
- `tui-designer` - TCSS/styling
- `tui-developer` - Python
- `tui-debugger` - Diagnostics

### Legal/Project (7)
- `legal-text-extractor` - Text extraction
- `legal-articles-finder` - Article lookup
- `planejamento-legal` - Planning (PT-BR)
- `analise-dados-legal` - Data analysis (PT-BR)
- `documentacao` - Documentation (PT-BR)
- `desenvolvimento` - Development (PT-BR)
- `qualidade-codigo` - Code quality (PT-BR)

### Development (10)
- `frontend-developer`, `backend-architect`, `rapid-prototyper`
- `react-pro-lst97`, `nextjs-pro-lst97`, `typescript-pro-lst97`
- `python-pro-lst97`, `full-stack-developer-lst97`
- `dx-optimizer-lst97`, `legacy-modernizer-lst97`

### Quality & Testing (8)
- `code-reviewer-superpowers`, `code-refactor-master`
- `test-writer-fixer`, `debugger-lst97`, `qa-expert-lst97`
- `test-automator-lst97`, `architect-review-lst97`
- `security-auditor-lst97`

### Data & AI (8)
- `ai-engineer`, `ml-engineer-lst97`, `data-scientist-lst97`
- `data-engineer-lst97`, `database-optimizer-lst97`
- `postgres-pro-lst97`, `graphql-architect-lst97`
- `prompt-engineer-lst97`

### Infrastructure (6)
- `cloud-architect-lst97`, `devops-automator`
- `deployment-engineer-lst97`, `incident-responder-lst97`
- `devops-incident-responder-lst97`, `performance-engineer-lst97`

### Design/UX (4)
- `ui-designer`, `react-component-generator-ui`
- `ux-researcher-studio`

### Business/Product (4)
- `product-manager-lst97`, `sprint-prioritizer-studio`
- `trend-researcher-studio`, `feedback-synthesizer-studio`

### Meta/Utility (4)
- `agent-organizer-lst97`, `gemini-assistant`
- `plan-reviewer`, `refactor-planner`

### Research (2)
- `documentation-architect`, `web-research-specialist`

### Routes/Auth (2)
- `auth-route-debugger`, `auth-route-tester`

---

## Como Usar

```
Use the [agent-name] agent to [task]
```

Exemplo:
```
Use the tui-developer agent to create a new widget
```

---

## Adicionar Novo Agente

Crie em `~/.claude/agents/meu-agente.md`:

```markdown
---
name: meu-agente
description: O que o agente faz
tools: Read, Write, Edit, Bash
---

# Instruções do Agente
...
```

**IMPORTANTE:** Reinicie a sessão do Claude Code para descobrir novos agentes.

---

## Backup

Backup disponível em: `~/.claude/agents-backup-YYYYMMDD/`

---

**Consolidação:** 2025-11-30
**De:** 106 agentes (projeto) → **59 agentes** (global)
