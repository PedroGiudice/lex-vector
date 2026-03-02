# Contexto: Frontend CCUI Claude Terroso -- Penpot para Codigo

**Data:** 2026-03-02
**Sessao:** ccui-redesign-vibma (terceira sessao do dia)
**Duracao:** ~1.5h

---

## O que foi feito

### 1. Design tokens Claude Terroso em CSS custom properties

Atualizou `ccui-app/src/styles.css` substituindo a paleta antiga (preta/cinza `#080808`) pelos tokens Claude Terroso validados contra o Penpot Design System board.

Tokens implementados:
- **Backgrounds:** `--bg-base` (#1c1510), `--bg-header` (#17120d), `--bg-panels` (#211a14), `--bg-cards` (#291c15), `--bg-borders` (#36241a)
- **Text (WCAG AA):** `--text-primary` (#e8ddd0, 13.47:1), `--text-secondary` (#a89880, 6.42:1), `--text-muted` (#9a8a78, 5.40:1)
- **Accent:** `--accent` (#c8784a, 5.36:1)
- **Agent colors:** terracota/oliva/teal/malva/musgo
- **Tipografia:** `--font-display` (Instrument Serif), `--font-ui` e `--font-mono` (MonaspiceAr NF)
- **Spacing:** message-gap 24px, chat-max-width 720px, icon-strip 48px, side-panel 240px, detail-panel 320px
- **Radius:** sm 4px, md 8px, lg 20px (pill para inputs)

Instrument Serif importado via Google Fonts CDN. MonaspiceAr nao disponivel localmente -- fallback para JetBrains Mono.

### 2. CaseSelector redesenhado conforme Penpot

Reescrito completamente seguindo o board "CaseSelector / Main" do Penpot (1280x900):

- Header: "Lex Vector" (Instrument Serif italic) / caso (mono) + avatar PGR
- Titulo: "Selecione um caso" (Instrument Serif italic 32px)
- Search bar (500px, pill shape radius 20px) + 4 filter pills (Todos, Em andamento, Concluidos, Recentes)
- Stats row: TOTAL / EM ANDAMENTO / DOCUMENTOS / ULTIMA ATIVIDADE (numeros em Instrument Serif italic)
- Grid 3 colunas de case cards (accent bar 4px esquerda, tags, progress bar, tempo relativo)
- Footer: botoes + NOVO CASO / IMPORTAR + keyboard hints (Enter/N///?)
- Keyboard navigation: setas para navegar cards, Enter para abrir, / para focar busca, Esc para limpar

Adicionados campos opcionais em `CaseInfo`: `title`, `parties`, `tags`, `progress`.

### 3. SessionView com layout 3-panel

Reescrito seguindo WF-01 Tab View do Penpot:

- **Icon strip** (48px, esquerda): 4 botoes (sessoes/arquivos/busca/config) com indicador ativo (accent bar lateral)
- **Side panel** (240px, colapsavel Cmd+B): placeholder "Em breve"
- **Agent tabs** no header: dots coloridos por agente (Main/researcher/case-analyst/strategist) -- dados mock por enquanto
- **Status bar** (24px): ONLINE/OFFLINE + modelo (Opus 4.5) + branch + agentes ativos + relogio

### 4. ChatView atualizado

Mensagens redesenhadas conforme Penpot:
- **User:** accent bar 3px esquerda, bg panels, border-radius 0 8px 8px 0
- **Assistant:** sem bubble, texto sobre base bg, dot + label "assistant" acima
- **Tool calls:** chips inline com dot colorido (nao mais card expandido)
- **Code blocks:** bg header, border borders, radius 8px
- Container centralizado com max-width 720px
- Estado vazio: "Chat do agente ativo" em Instrument Serif italic

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `ccui-app/src/styles.css` | Modificado -- tokens Claude Terroso + Google Fonts import |
| `ccui-app/src/components/CaseSelector.tsx` | Reescrito -- design Penpot completo |
| `ccui-app/src/components/SessionView.tsx` | Reescrito -- layout 3-panel + agent tabs + status bar |
| `ccui-app/src/components/ChatView.tsx` | Reescrito -- mensagens estilo Claude Terroso |
| `ccui-app/src/types/protocol.ts` | Modificado -- campos opcionais em CaseInfo |

## Commits desta sessao

```
5f7f496 feat(ccui-app): redesign frontend Claude Terroso conforme Penpot
```

## Problemas de ambiente

- **Node 18 na VM** -- Vite 7 requer Node >= 20.19. `bun x vite build` falha. tsc falha por `@types/react` nao resolvido (deps instaladas para Node 20+). Codigo esta sintaticamente correto, validacao visual pendente.
- **MonaspiceAr Nerd Font Mono** nao disponivel localmente. Fallback funciona mas visual nao sera identico ao Penpot.

## Pendencias identificadas

1. **Instalar Node 20+** para que `bun run build` funcione -- prioridade alta
2. **View toggle TAB/SPLIT** (Ctrl+\) com split view 70/30 para multi-agent -- WF-02 do Penpot
3. **Conexao real dos agent tabs** com WebSocket (agent_joined/left events) -- dados mock atualmente
4. **Sidebar funcional** -- historico de sessoes, file tree, busca
5. **MonaspiceAr font** -- baixar de Nerd Fonts e configurar @font-face
6. **Testes unitarios** para CaseSelector, SessionView, ChatView
7. **Validacao visual** -- rodar dev server e comparar com exports do Penpot
8. **Inicio no ccui-v2 (frontend/)** -- foi editado por engano no inicio da sessao, revertido. Precisa decidir se ccui-v2 morre ou coexiste

## Decisoes tomadas

- **ccui-app/ e o frontend correto** (Tauri 2 + React 19), nao frontend/ (SPA Vite antigo)
- **CSS custom properties** em vez de Tailwind config para tokens (Tailwind v4 nao usa config file)
- **Agent tabs como mock** por enquanto -- dados reais virao do WebSocket
- **Keyboard shortcuts no CaseSelector** -- Enter/arrows/slash/Esc implementados nativamente
- **Progress bar** adicionada nos cards (campo opcional, backend pode nao enviar ainda)
