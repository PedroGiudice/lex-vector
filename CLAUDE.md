# CLAUDE.md

Instrucoes operacionais para Claude Code neste repositorio.

**Arquitetura:** `ARCHITECTURE.md` (North Star)
**Licoes:** `DISASTER_HISTORY.md`

---

## Regras Criticas

### 1. Sempre Usar venv
```bash
cd <projeto> && source .venv/bin/activate && python main.py
```

### 2. Nunca Commitar
- `.venv/`, `__pycache__/`, `*.pdf`, `*.log`

### 3. Paths Dinamicos
```python
from shared.utils.path_utils import get_data_dir
```

### 4. Skills
- `skills/` = custom (requer SKILL.md)
- `.claude/skills/` = managed (nao modificar)

### 5. Gemini para Context Offloading
**SEMPRE** usar `gemini-assistant` para:
- Arquivos > 500 linhas
- Multiplos arquivos simultaneos
- Logs extensos, diffs grandes

### 6. Bun OBRIGATÓRIO (nunca npm/yarn)
**SEMPRE** usar `bun` para Node.js. Dockerfiles, CI, local — tudo Bun:
```bash
bun install && bun run dev && bun run build
```
> npm/yarn proibidos. Não gerar `package-lock.json` ou `yarn.lock`.

### 7. mgrep em vez de grep
**SEMPRE** usar `mgrep` para buscas em código:
```bash
mgrep "pattern"           # em vez de grep -r "pattern"
mgrep "pattern" src/      # busca em diretório específico
```

---

## Estrutura

```
legal-workbench/   # Dashboard juridico (projeto ativo)
adk-agents/        # Agentes ADK
comandos/          # CLI utilitarios
shared/            # Codigo compartilhado
skills/            # Skills custom
.claude/           # Config (agents, hooks, skills managed)
```

---

## Debugging

Tecnica dos 5 Porques para bugs nao-triviais:
1. Sintoma → 2. Por que? → 3. Por que? → 4. Por que? → 5. **CAUSA RAIZ**

---

## Hooks

Validar apos mudancas:
```bash
tail -50 ~/.vibe-log/hooks.log
```
Red flags: `MODULE_NOT_FOUND`, `command not found`

---

## Agentes Discovery

Agentes de `.claude/agents/*.md` descobertos no inicio da sessao.
Novo agente? Reinicie a sessao.

---

## Breaking Changes Check

Ao iniciar sessao, verificar se ha mudancas importantes no repo:
1. Checar `git log -5 --oneline` para commits recentes
2. Se houver mudancas em `ARCHITECTURE.md`, `CLAUDE.md`, ou `.claude/`, informar usuario
3. Oferecer resumo das alteracoes relevantes

---

## Team

- **PGR** = Pedro (dono do projeto)
- **LGP** = Leo (contribuidor ativo, socio)
