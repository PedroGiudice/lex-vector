# Retomada: CCUI Frontend Redesign -- Penpot para Codigo

## Contexto rapido

Nas sessoes anteriores, desenhamos no Penpot o visual completo do CCUI "Claude Terroso" -- uma interface inspirada no app claude.ai com paleta terrosa editorial. Foram criadas 4 paginas: SessionView (chat principal), Design System (tokens), CaseSelector (selecao de caso), e Wireframes Multi-Agent (tab view + split view).

O design doc esta em `docs/plans/2026-03-02-ccui-claude-terroso-design.md` com todas as decisoes aprovadas (layout, tipografia, cores, componentes). O contexto detalhado das duas sessoes Penpot esta em `docs/contexto/02032026-penpot-claude-terroso-implementation.md`.

Agora o objetivo e **implementar o frontend React** que reflete o Penpot. O CCUI atual (`pages/CCuiV2Module.tsx`, 46 linhas) e um stub basico. O backend Rust (`ccui-backend/`) ja existe com WebSocket, sessoes, e team watcher.

## Arquivos principais

- `docs/plans/2026-03-02-ccui-claude-terroso-design.md` -- design doc completo (layout, tipografia, cores, componentes)
- `docs/contexto/02032026-penpot-claude-terroso-implementation.md` -- contexto das sessoes Penpot (paleta, quirks, IDs)
- `legal-workbench/frontend/src/pages/CCuiV2Module.tsx` -- stub atual (46 linhas, ponto de partida)
- `legal-workbench/frontend/src/styles/theme.ts` -- tema atual (precisa ser atualizado)
- `legal-workbench/ccui-backend/` -- backend Rust com WebSocket, sessoes, cases API

## Proximos passos (por prioridade)

### 1. Criar theme tokens Claude Terroso
**Onde:** `frontend/src/styles/theme.ts` (ou novo arquivo de design tokens)
**O que:** Definir todos os tokens de cor, tipografia e spacing conforme design doc:
- Backgrounds: base, header, panels, cards, borders
- Text: primary `#e8ddd0`, secondary `#a89880`, muted `#9a8a78`, accent `#c8784a`
- Agentes: terracota, oliva, teal, malva, musgo (5 cores)
- Tipografia: Instrument Serif (display/heading), MonaspiceAr ou GoMono (body/code)
- Spacing: message-gap 24px, paragraph 16px, line-height body 1.65
**Por que:** Tokens centralizados evitam cores hardcoded e facilitam consistencia
**Verificar:** `bun run build` compila sem erros

### 2. Implementar layout skeleton (3 panels + header + status bar)
**Onde:** Novo componente `frontend/src/components/ccui/Layout.tsx` (ou similar)
**O que:** Grid com 4 areas conforme design doc:
- Icon strip (48px fixo, esquerda)
- Side panel (240px, colapsavel Cmd+B)
- Chat container (flex-1, max-width 720px centralizado)
- Detail panel (320px, on-demand)
- Header (full-width, bg header)
- Status bar (full-width, bg header)
**Por que:** Estrutura base sobre a qual todos os componentes se encaixam
**Verificar:** Layout renderiza com areas visiveis em `bun run dev`

### 3. Implementar componentes de mensagem (user + assistant)
**Onde:** `frontend/src/components/ccui/Message.tsx`
**O que:**
- User message: accent bar 3px esquerda, bg panels, border-radius 0 8 8 0
- Assistant message: sem bubble, texto sobre base bg, icon + label acima
- Tool call chips: inline com dot de status, expand para detail panel
**Por que:** Componentes core da experiencia de chat
**Verificar:** Mensagens renderizam corretamente com dados mock

### 4. Conectar WebSocket ao backend existente
**Onde:** `frontend/src/services/` ou `frontend/src/hooks/useCCUIWebSocket.ts`
**O que:** Integrar com `ccui-backend` WebSocket (create_session, input, output, agent_joined/left)
**Por que:** Backend ja suporta multi-agent -- frontend precisa refletir
**Verificar:** `curl http://localhost:8005/health` + sessao WebSocket funcional

### 5. Implementar CaseSelector
**Onde:** `frontend/src/components/ccui/CaseSelector.tsx`
**O que:** Grid de cards com stats, search bar, filtros -- conforme wireframe Penpot
**Por que:** Entry point do fluxo: usuario seleciona caso antes de iniciar sessao
**Verificar:** Cards renderizam com dados de `GET /api/cases`

## Fontes a instalar

- **Instrument Serif**: Google Fonts (`@fontsource/instrument-serif` ou CDN)
- **MonaspiceAr Nerd Font Mono**: Ja uploadada no Penpot, precisa de `@font-face` local no frontend. Arquivos em `/home/opc/lex-vector/fonts/` (verificar se existem, senao baixar de Nerd Fonts)
- Alternativa body: GoMono NF (design doc original) -- decidir na implementacao

## Como verificar

```bash
cd legal-workbench/frontend
bun install
bun run dev          # Dev server
bun run build        # Build check
bun run lint         # Lint check

# Backend (se precisar testar integracao)
cd legal-workbench/ccui-backend
cargo run            # Porta 8005
```

## Referencia visual

Abrir Penpot e navegar para as paginas:
- **SessionView / Claude Terroso** -- layout completo do chat
- **Design System** -- todos os tokens visuais
- **CaseSelector / Main** -- tela de selecao de caso
- **Wireframes - Multi-Agent** -- WF-01 (Tab View), WF-02 (Split View), WF-03 (Tab States)
