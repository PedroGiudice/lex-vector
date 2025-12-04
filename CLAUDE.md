# CLAUDE.md

Instrucoes operacionais para Claude Code neste repositorio.

**Arquitetura:** Ver `ARCHITECTURE.md` (North Star)
**Licoes:** Ver `DISASTER_HISTORY.md`

---

## Regras Criticas

### 1. Sempre Usar venv
```bash
cd agentes/<nome>
source .venv/bin/activate
python main.py
```

### 2. Nunca Commitar
- `.venv/`, `__pycache__/`
- Arquivos de dados (`*.pdf`, `*.log`)

### 3. Paths Dinamicos
```python
from shared.utils.path_utils import get_data_dir
data = get_data_dir('oab-watcher', 'downloads')
```

### 4. Skills Custom
- `skills/` = custom (requer SKILL.md)
- `.claude/skills/` = managed (nao modificar)

---

## Estrutura

```
agentes/           # Agentes Python (oab-watcher, djen-tracker, legal-lens)
comandos/          # Utilitarios (fetch-doc, parse-legal, validate-id)
mcp-servers/       # Servidores MCP (trello-mcp)
legal-extractor-*/ # Ferramentas de extracao PDF
shared/            # Codigo compartilhado
skills/            # Skills custom
.claude/           # Config Claude Code (agents, hooks, skills managed)
```

---

## MCP: trello-mcp

```bash
trello-ui  # alias em ~/.bashrc
```

Backend: `src/`, Frontend: `Trello-app.py`

---

## Debugging

Tecnica dos 5 Porques para bugs nao-triviais:
1. Sintoma
2. Por que? (imediato)
3. Por que? (profundo)
4. Por que? (mais profundo)
5. Por que? **CAUSA RAIZ** <- Corrigir apenas isto

---

## Hooks

Validar apos mudancas:
```bash
tail -50 ~/.vibe-log/hooks.log
```

Red flags: `MODULE_NOT_FOUND`, `command not found`, falhas silenciosas

---

## Agentes Discovery

Agentes descobertos de `.claude/agents/*.md` no inicio da sessao.
Novo agente? Reinicie a sessao.

---

**Ultima atualizacao:** 2025-12-04
- adicione à memória a causa raíz para o não acionamento do custom style