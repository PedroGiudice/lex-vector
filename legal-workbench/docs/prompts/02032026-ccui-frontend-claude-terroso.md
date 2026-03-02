# Retomada: Frontend CCUI Claude Terroso -- Validacao e Proximos Passos

## Contexto rapido

Na sessao anterior, transformamos o design Penpot "Claude Terroso" em codigo React no `ccui-app/` (Tauri 2 + React 19 + Tailwind 4). Foram reescritos 4 componentes: CaseSelector (grid 3 colunas, search, filters, stats, keyboard nav), SessionView (layout 3-panel com icon strip + sidebar + agent tabs + status bar), ChatView (user msg com accent bar, assistant sem bubble, max-width 720px), e styles.css (tokens completos da paleta terrosa). Agent tabs usam dados mock. Build nao foi validado porque a VM tem Node 18 e Vite 7 requer Node 20+.

O design doc esta em `docs/plans/2026-03-02-ccui-claude-terroso-design.md`. O contexto detalhado da sessao Penpot anterior esta em `docs/contexto/02032026-penpot-claude-terroso-implementation.md`. O contexto desta sessao esta em `docs/contexto/02032026-ccui-frontend-claude-terroso.md`.

## Arquivos principais

- `legal-workbench/ccui-app/src/styles.css` -- tokens CSS Claude Terroso (fonte de verdade para cores/tipografia)
- `legal-workbench/ccui-app/src/components/CaseSelector.tsx` -- tela de selecao de caso
- `legal-workbench/ccui-app/src/components/SessionView.tsx` -- layout 3-panel com chat
- `legal-workbench/ccui-app/src/components/ChatView.tsx` -- mensagens user/assistant
- `legal-workbench/ccui-app/src/types/protocol.ts` -- tipos CaseInfo com campos novos
- `docs/plans/2026-03-02-ccui-claude-terroso-design.md` -- design doc aprovado

## Proximos passos (por prioridade)

### 1. Resolver ambiente de build (Node 20+)
**Onde:** VM Contabo, configuracao de ambiente
**O que:** Instalar Node 20+ para que `bun run build` (tsc + vite build) funcione. Vite 7 exige Node >= 20.19.
**Por que:** Sem build funcional, nao da para validar se o codigo compila ou rodar o dev server
**Verificar:** `cd legal-workbench/ccui-app && bun run build` completa sem erros

### 2. Validacao visual contra Penpot
**Onde:** Browser, comparando com exports do Penpot
**O que:** Rodar `bun run dev`, abrir no browser, comparar CaseSelector e SessionView com os boards do Penpot. Ajustar espacamentos, cores, tamanhos que nao batam.
**Por que:** A implementacao foi feita lendo medidas do Penpot, mas ajustes finos sao inevitaveis
**Verificar:** Screenshots do app vs exports do Penpot lado a lado

### 3. Instalar MonaspiceAr Nerd Font Mono
**Onde:** `ccui-app/public/fonts/` + `styles.css` @font-face
**O que:** Baixar MonaspiceAr NF de https://github.com/ryanoasis/nerd-fonts/releases, adicionar @font-face no CSS
**Por que:** Design usa MonaspiceAr para body/code, atualmente fallback para JetBrains Mono
**Verificar:** Textos mono no app usam MonaspiceAr (inspecionar font-family no DevTools)

### 4. Conectar agent tabs ao WebSocket
**Onde:** `SessionView.tsx` -- substituir array mock `agents` por dados reais
**O que:** Consumir eventos `agent_joined` e `agent_left` do WebSocket (ja suportados pelo ccui-backend) para popular as tabs dinamicamente
**Por que:** Agent tabs sao mock estatico -- precisam refletir agentes reais da sessao
**Verificar:** Iniciar sessao com team, tabs aparecem conforme agentes entram

### 5. Implementar split view (WF-02)
**Onde:** `SessionView.tsx` -- novo modo de visualizacao
**O que:** Toggle TAB/SPLIT (Ctrl+\) conforme WF-03 do Penpot. No modo split, chat principal ocupa 70% e painel direito (320px) mostra output dos agentes secundarios empilhados
**Por que:** Wireframe WF-02 define essa visualizacao como alternativa ao tab view
**Verificar:** Ctrl+\ alterna entre tab e split, painel direito mostra agentes

### 6. Sidebar funcional
**Onde:** `SessionView.tsx` -- conteudo do side panel
**O que:** Tab "sessoes" lista sessoes ativas (GET /api/sessions), tab "arquivos" mostra file tree do caso
**Por que:** Sidebar esta com placeholder "Em breve"
**Verificar:** Sessoes ativas aparecem na sidebar, file tree do caso carrega

## Como verificar

```bash
cd legal-workbench/ccui-app

# Instalar deps (se necessario)
bun install

# Dev server (requer Node 20+)
bun run dev

# Build check
bun run build

# TypeScript check
bun x tsc --noEmit

# Backend (para testar integracao)
cd ../ccui-backend && cargo run  # Porta 8005
```

## IDs do Penpot (referencia)

| Board | ID |
|-------|-----|
| Design System | `c7ae26d6-5cdb-80c1-8007-a57a7fa6621b` |
| CaseSelector / Main | `fd9022fd-dc98-8089-8007-a623acdf560b` |
| WF-01 Tab View | `fd9022fd-dc98-8089-8007-a622aa76d3c2` |
| WF-02 Split View | `fd9022fd-dc98-8089-8007-a622c2d8508f` |
| WF-03 Tab States | `fd9022fd-dc98-8089-8007-a622e3136d2e` |
