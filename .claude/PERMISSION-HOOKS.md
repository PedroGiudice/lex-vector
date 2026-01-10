# Permission Hooks Architecture

Sistema de auto-aprovação e bloqueio de permissões para Claude Code.

## Objetivo

Permitir que subagentes trabalhem **autonomamente em background** sem travar esperando aprovação manual, mantendo proteções críticas.

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PermissionRequest Flow                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   1. block-commit-main.js (contextual)                                   │
│      ├── Só processa: Bash com "git commit"                              │
│      ├── Verifica branch atual: git branch --show-current                │
│      └── Se main/master → DENY                                           │
│                                                                          │
│   2. hookify-permission-engine.js (declarativo)                          │
│      ├── Carrega regras: .claude/hookify.*.md (event: permission)        │
│      ├── Ordena por priority (maior primeiro)                            │
│      └── Primeira match → retorna action (allow/deny/ask)                │
│                                                                          │
│   Regras hookify (em ordem de priority):                                 │
│   ┌──────────────────────────────────────────────────────────────────┐  │
│   │ 100: block-dangerous-bash                                         │  │
│   │      Pattern: rm -rf, force push, DROP TABLE, etc.                │  │
│   │      Action: DENY                                                 │  │
│   ├──────────────────────────────────────────────────────────────────┤  │
│   │ 1: auto-approve-safe-tools                                        │  │
│   │      Tool: * (todas)                                              │  │
│   │      Action: ALLOW                                                │  │
│   └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Camadas de Proteção

| Camada | Hook | Evento | Proteção |
|--------|------|--------|----------|
| 1 | `auto-branch.sh` | SessionStart | Cria branch automática se em main |
| 2 | `block-commit-main.js` | PermissionRequest | Bloqueia git commit em main |
| 3 | `block-dangerous-bash` | PermissionRequest | Bloqueia rm -rf, force push, etc. |
| 4 | `auto-approve-safe-tools` | PermissionRequest | Aprova todo o resto |

---

## Arquivos

### Hooks Contextuais (scripts)

| Arquivo | Localização | Função |
|---------|-------------|--------|
| `auto-branch.sh` | `.claude/hooks/` | Cria branch de trabalho |
| `block-commit-main.js` | `.claude/hooks/` | Bloqueia commit em main |
| `hookify-permission-engine.js` | `.claude/hooks/` | Engine declarativo |

### Regras Hookify (declarativas)

| Arquivo | Priority | Action | Descrição |
|---------|----------|--------|-----------|
| `hookify.permission-block-dangerous-bash.md` | 100 | deny | Comandos destrutivos |
| `hookify.permission-auto-approve.md` | 1 | allow | Catch-all para o resto |

---

## Como Adicionar Nova Regra

### Regra Declarativa (hookify)

Criar arquivo `.claude/hookify.<nome>.md`:

```yaml
---
name: minha-regra
enabled: true
event: permission
tool: Bash|Edit|Write|*
action: allow|deny|ask
priority: 50
pattern: regex-para-bash (opcional)
---

Mensagem mostrada quando bloqueado (markdown)
```

### Regra Contextual (script)

Para lógica que precisa verificar estado (branch atual, arquivos existentes, etc.):

1. Criar script em `.claude/hooks/meu-hook.js`
2. Adicionar em `settings.json` → `hooks.PermissionRequest`
3. O script recebe JSON via stdin:
   ```json
   {"toolName": "Bash", "toolInput": {"command": "..."}}
   ```
4. Retornar via stdout:
   ```json
   {"behavior": "allow|deny|ask", "message": "..."}
   ```

---

## Debug

```bash
# Testar hook contextual
echo '{"toolName":"Bash","toolInput":{"command":"git commit -m test"}}' | DEBUG=1 node .claude/hooks/block-commit-main.js

# Testar hookify engine
echo '{"toolName":"Bash","toolInput":{"command":"rm -rf /"}}' | HOOKIFY_DEBUG=1 bun run .claude/hooks/hookify-permission-engine.js
```

---

## Histórico

| Data | Mudança |
|------|---------|
| 2026-01-09 | Migração para hookify + hook contextual. Removido `permissions.allow[]` (330 linhas) |
| 2025-12-xx | Sistema inicial com `permissions.allow[]` manual |
