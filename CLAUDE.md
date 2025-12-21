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

### 6. Bun em vez de npm
**SEMPRE** usar `bun` para comandos Node.js quando possível:
```bash
bun install    # em vez de npm install
bun run dev    # em vez de npm run dev
bun run build  # em vez de npm run build
```

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

## Team

- **PGR** = Pedro (dono do projeto)
- **LGP** = Leo (contribuidor ativo, socio)
