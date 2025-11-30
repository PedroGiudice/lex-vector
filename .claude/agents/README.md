# Agents

Specialized agents for complex, multi-step tasks.

**Total: 104 agents** organized into subdirectories (deduplicated, compliant with Anthropic naming conventions).

---

## Directory Structure

```
.claude/agents/
├── _meta/          (11)  # Meta-agents (organizers, reviewers, utilities)
├── _project/       (7)   # Custom project-specific agents (legal/Brazilian)
├── business/       (4)   # Product management, feedback
├── data-ai/        (8)   # ML, AI, data engineering, databases
├── design-ux/      (14)  # UI/UX design, accessibility, styling
├── development/    (15)  # Frontend, backend, fullstack, language-specific
├── infrastructure/ (12)  # DevOps, cloud, deployment, performance
├── marketing/      (7)   # Social media, growth, ASO
├── quality-testing/(14)  # Code review, QA, debugging, testing
├── research/       (4)   # Documentation, web research
├── routes-auth/    (2)   # Authentication/route testing
├── security/       (1)   # Security auditing
├── tui/            (5)   # Textual TUI specialists
```

---

## Naming Convention

All agent names follow **lowercase-hyphen** format (Anthropic best practice):
- ✅ `frontend-developer`
- ✅ `code-architecture-reviewer`
- ❌ ~~`Frontend Developer`~~ (spaces/capitals not allowed)

---

## Quick Reference by Category

### Development (`development/`)
- `frontend-developer.md` - React, TypeScript frontends
- `backend-architect.md` - API design, Node.js
- `rapid-prototyper.md` - Quick MVPs
- `react-pro-lst97.md` - React specialist
- `nextjs-pro-lst97.md` - Next.js specialist
- `typescript-pro-lst97.md` - TypeScript specialist
- `python-pro-lst97.md` - Python development
- `golang-pro-lst97.md` - Go development
- ... and more

### Quality & Testing (`quality-testing/`)
- `code-architecture-reviewer.md` - Architecture review
- `code-refactor-master.md` - Comprehensive refactoring
- `test-writer-fixer.md` - Test creation/fixing
- `frontend-error-fixer.md` - Frontend debugging
- `debugger-lst97.md` - General debugging
- `qa-expert-lst97.md` - QA specialist
- ... and more

### Data & AI (`data-ai/`)
- `ai-engineer.md` - AI/ML integration
- `ml-engineer-lst97.md` - Machine learning
- `data-scientist-lst97.md` - Data science
- `database-optimizer-lst97.md` - DB optimization
- `prompt-engineer-lst97.md` - Prompt engineering
- ... and more

### TUI (`tui/`)
- `tui-master.md` - Generalist Textual TUI
- `tui-architect.md` - TUI planning specialist
- `tui-designer.md` - TCSS/styling specialist
- `tui-developer.md` - Widget implementation
- `tui-debugger.md` - TUI debugging specialist

### Project-Specific (`_project/`)
- `legal-text-extractor.md` - Brazilian legal text extraction
- `legal-articles-finder.md` - Legal article lookup
- `planejamento-legal.md` - Legal planning
- `analise-dados-legal.md` - Legal data analysis
- `documentacao.md` - Portuguese documentation
- `desenvolvimento.md` - Portuguese development
- `qualidade-codigo.md` - Code quality (Portuguese)

---

## How to Use

### Invoke an Agent
```
Use the [agent-name] agent to [task]
```

Example:
```
Use the code-architecture-reviewer agent to review the new API endpoints
```

### Agent Discovery

Agents are auto-discovered recursively from `.claude/agents/**/*.md`.

Run discovery manually:
```bash
node .claude/hooks/lib/agent-auto-discovery.js --update
```

---

## Creating Custom Agents

Create a `.md` file with YAML frontmatter:

```markdown
---
name: my-agent
description: What this agent does
tools: Read, Write, Edit, Bash
---

# Agent Instructions

Your detailed instructions here...
```

Place in appropriate subdirectory and run discovery.

---

## Notes

- All agents inherit session model (no `model:` field needed)
- Agents in subdirectories are fully supported by Claude Code
- Deduplicated: each agent has exactly one authoritative file
- Agent names must be lowercase-hyphen format
- Run `node .claude/hooks/lib/agent-auto-discovery.js --update` after adding/modifying agents
