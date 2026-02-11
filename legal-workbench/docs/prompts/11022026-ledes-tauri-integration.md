# Retomada: LEDES Converter -- Integração Tauri e Pendências

## Contexto rápido

O LEDES Converter (conversor de invoices jurídicos para formato LEDES 1998B) tem backend completo (120 testes, 6 endpoints, MatterStore SQLite) e frontend reescrito (2 abas: Upload DOCX / Colar Texto, dropdown de matters, validação inline). Tudo na branch `work/session-20260210-123818` (9 commits + 3 mudanças uncommitted).

Na última sessão, buildamos o AppImage Tauri e instalamos na máquina do usuário (cmr-auto). Encontramos e corrigimos 3 bugs de integração: (1) DATA_PATH genérico poluindo o MatterStore, (2) CORS bloqueando requests do Tauri webview, (3) API_BASE_URL relativo não resolvendo em modo Tauri.

Pendências críticas: IP backend hardcoded no frontend, dados do Tauri Store perdidos na refatoração, docker-compose.yml desatualizado com DATA_PATH antigo.

## Arquivos principais

- `ferramentas/ledes-converter/api/main.py` -- Rotas FastAPI (6 endpoints)
- `ferramentas/ledes-converter/api/matter_store.py` -- CRUD SQLite (fix LEDES_DATA_PATH uncommitted)
- `frontend/src/services/ledesConverterApi.ts` -- API client (fix Tauri URL uncommitted)
- `frontend/src/pages/LedesConverterModule.tsx` -- Componente React (~500 linhas, 2 tabs)
- `frontend/src/store/ledesConverterStore.ts` -- Zustand store multi-modo
- `docker-compose.yml` -- Precisa atualizar env var DATA_PATH -> LEDES_DATA_PATH
- `docs/contexto/11022026-ledes-tauri-integration.md` -- Contexto detalhado

## Próximos passos (por prioridade)

### 1. Resolver dados perdidos do Tauri Store
**Onde:** Investigar o que estava no localStorage/Tauri Store da versão anterior
**O que:** O usuário mencionou que dados da versão anterior sumiram. Provavelmente config LEDES (client_id, law_firm_id, etc.) salva em localStorage via STORAGE_KEY que foi removido na refatoração. Verificar se o Tauri Store plugin (`tauri-plugin-store`) persistiu dados que podem ser recuperados.
**Por que:** Módulo de cobrança de honorários -- dados do usuário são críticos
**Verificar:** `ssh cmr-auto@100.102.249.9 'find ~/.local/share/com.legal-workbench -type f 2>/dev/null || find ~/.config/com.legal-workbench -type f 2>/dev/null'`

### 2. Tornar API_BASE_URL configurável em modo Tauri
**Onde:** `frontend/src/services/ledesConverterApi.ts:9-10`
**O que:** Substituir IP hardcoded (`100.98.38.32:8003`) por config persistente. Opções: (a) Tauri Store plugin para settings do usuário, (b) variável VITE_API_URL no build, (c) settings page no app. Opção (a) é a mais robusta.
**Por que:** IP Tailscale é específico da infra atual e mudaria se a VM mudar
**Verificar:** Abrir app Tauri, ir a settings, configurar URL, fazer request

### 3. Atualizar docker-compose.yml
**Onde:** `legal-workbench/docker-compose.yml` linhas ~259-260
**O que:** Trocar `DATA_PATH=/data` para `LEDES_DATA_PATH=/data` no serviço `api-ledes-converter`
**Por que:** A mudança de env var no matter_store.py quebrou a referência no Docker
**Verificar:** `docker compose config | grep LEDES_DATA_PATH`

### 4. Fix GET /matters/{name} com barras
**Onde:** `ferramentas/ledes-converter/api/main.py`, rota `@app.get("/matters/{matter_name}")`
**O que:** Usar `@app.get("/matters/{matter_name:path}")` para aceitar barras no nome, ou URL-encode no frontend
**Por que:** Nomes de matters como `BRA/STLandATDIL/CRM/Governance` causam 404
**Verificar:** `curl http://localhost:8003/matters/BRA%2FSTLandATDIL%2FCRM%2FGovernance`

### 5. Commitar correções e merge para main
**Onde:** 3 arquivos uncommitted (matter_store.py, main.py, ledesConverterApi.ts)
**O que:** Commitar os fixes, resolver pendências 1-4, merge branch para main
**Por que:** Branch tem 9 commits + 3 mudanças. Precisa ir para main.
**Verificar:** `git log main --oneline -5` deve incluir os commits do LEDES

### 6. Build com glib compatível (opcional, baixa prioridade)
**Onde:** Tauri build na VM GCP
**O que:** Considerar build em container Ubuntu 24.04 para eliminar warnings de glib. Ou adicionar `--appimage-extract-and-run` para evitar FUSE issues.
**Por que:** Warnings `undefined symbol: g_task_set_static_name` podem afetar file dialogs nativos
**Verificar:** Abrir file dialog nativo no app (botão "Selecionar Arquivo")

## Skills úteis

- /verification-before-completion -- Antes de declarar qualquer fix pronto
- /tauri-native-apis -- Para Tauri Store e dialogs
- /tauri-core -- Para IPC e configuração Tauri
- /executing-plans -- Para execução sequencial das pendências

## Como verificar

```bash
# Backend
cd legal-workbench/ferramentas/ledes-converter
uv run python -m pytest tests/ -q
uv run uvicorn api.main:app --host 0.0.0.0 --port 8003 &
sleep 3
curl -sf http://localhost:8003/health
curl -sf http://localhost:8003/matters | python3 -c "import sys,json; print(len(json.load(sys.stdin)), 'matters')"

# Frontend
cd legal-workbench/frontend
bun run build
bunx eslint src/services/ledesConverterApi.ts src/pages/LedesConverterModule.tsx

# Git
git status --short  # 3 arquivos M + docs
git log --oneline work/session-20260210-123818 --not main  # 9 commits
```
