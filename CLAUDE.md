# CLAUDE.md

Instrucoes operacionais para Claude Code neste repositorio.

**Arquitetura:** Ver `ARCHITECTURE.md` (North Star)
**Licoes:** Ver `DISASTER_HISTORY.md`

---

## Regras Criticas

### 1. Sempre Usar venv
```bash
cd agentes/<nome>      # ou ferramentas/<nome>
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

### 5. Gemini para Context Offloading (OBRIGATORIO)
**SEMPRE** usar o agente Gemini (`gemini-assistant`) para:
- Arquivos > 500 linhas
- Multiplos arquivos (mesmo pequenos)
- Logs extensos, diffs grandes, exploracao de diretorios

```bash
# Exemplo: resumir arquivo grande
cat arquivo_grande.py | gemini -m gemini-2.5-flash "Resuma em 5 bullets"

# Exemplo: mapear multiplos arquivos
find src/ -name "*.py" | xargs cat | gemini -m gemini-2.5-flash "Liste classes e funcoes principais"
```

**Por que:** Poupa tokens, mantem contexto limpo, acelera analise.

---

## Estrutura

```
agentes/           # Agentes Python autonomos (oab-watcher, djen-tracker, legal-lens)
ferramentas/       # Ferramentas Python sob demanda (legal-text-extractor, stj-dados-abertos)
comandos/          # Utilitarios (fetch-doc, parse-legal, validate-id)
mcp-servers/       # Servidores MCP (trello-mcp)
legal-extractor-*/ # CLI/TUI extracao PDF
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

**Ultima atualizacao:** 2025-12-07
- Consolidacao: `legal-text-extractor` e `stj-dados-abertos` movidos de `agentes/` para `ferramentas/` (ADR-005)
- `stj-dados-abertos`: Data Lakehouse Dashboard funcional (Streamlit + DuckDB) - download retroativo 2022-hoje
- Regra 5: Gemini obrigatorio para context offloading (>500 linhas ou multiplos arquivos)