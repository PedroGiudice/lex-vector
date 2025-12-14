# Legal Workbench

Dashboard integrado para ferramentas juridicas.

## Quick Start

```bash
# Iniciar Legal-Workbench (Streamlit)
lw

# Verificar ClaudeCodeUI (PM2)
ccui-status
```

## Acesso

| Servico | Local | Mobile (Tailscale) |
|---------|-------|-------------------|
| Legal-Workbench | http://localhost:8501 | http://100.76.94.104:8501 |
| ClaudeCodeUI | http://localhost:3001 | http://100.76.94.104:3001 |

**Nota:** ClaudeCodeUI requer autenticacao (criar usuario no primeiro acesso via localhost).

## Modulos (v2.6.0)

| Modulo | ID | Status | Backend |
|--------|-----|--------|---------|
| Dashboard | - | System | app.py |
| Text Extractor | text_extractor | Active | ferramentas/legal-text-extractor |
| Document Assembler | doc_assembler | Active | ferramentas/legal-doc-assembler |
| STJ Dados Abertos | stj | Active | ferramentas/stj-dados-abertos |
| Trello MCP | trello | Active | ferramentas/trello-mcp |

**Principio:** Separacao absoluta entre frontend (`modules/`) e backend (`ferramentas/src/`).

## Tools

- **Claude Code UI** - Interface web para Claude CLI (via sidebar)

## Mobile

1. Instale Tailscale no celular
2. Autentique com mesma conta (GitHub)
3. Acesse `http://100.76.94.104:3001`
4. Faca login com credenciais criadas no localhost
5. Adicione a home screen (PWA)

## Aliases

```bash
lw              # Inicia Legal-Workbench
ccui-status     # Status do PM2
ccui-logs       # Logs do claudecodeui
ccui-restart    # Reinicia claudecodeui
```

## Arquitetura

```
legal-workbench/
├── app.py              # Hub principal (routing + sidebar)
├── config.yaml         # Registro de modulos
├── modules/            # UI wrappers (Streamlit) - FRONTEND
│   ├── text_extractor.py
│   ├── doc_assembler.py
│   ├── stj.py
│   └── trello.py
└── ferramentas/        # Backend logic (pure Python)
    ├── legal-text-extractor/src/
    ├── legal-doc-assembler/src/
    ├── stj-dados-abertos/src/
    └── trello-mcp/src/
```

**Fluxo:** `app.py` carrega modulos de `modules/` via `config.yaml`. Cada modulo importa APENAS a logica de `ferramentas/*/src/`.

## Servicos Externos

- **ClaudeCodeUI** (siteboon/claudecodeui v1.12.0) - Gerenciado via PM2
  - Porta: 3001
  - Config: `~/pm2-ecosystem.config.js`
  - Logs: `~/.pm2/logs/claude-code-ui-*.log`
  - Update: `npm update -g @siteboon/claude-code-ui && pm2 restart claude-code-ui`

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
