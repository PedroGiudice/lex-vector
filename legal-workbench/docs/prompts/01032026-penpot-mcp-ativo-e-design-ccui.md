# Retomada: Continuar Design CCUI no Penpot

## Contexto rápido

O MCP do Penpot está funcionando no Claude Code. A ferramenta `mcp__penpot__execute_code`
está disponível (registrada em `~/.claude.json` via `claude mcp add --scope user`).
O Penpot self-hosted roda em `http://100.123.73.128:9001`.

No Penpot foi criado um arquivo com 3 páginas para o design do ccui-app:
- **Design System** — tokens de cor, tipografia e componentes (parcialmente pronto; faltam message bubbles)
- **CaseSelector** — tela de seleção de caso (em branco)
- **SessionView** — tela principal de chat (em branco)

**Atenção Penpot API:** `Text.width` é read-only. Para controlar largura: `text.resize(w, h)` seguido de `text.growType = "fixed"`.

## Arquivos principais

- `/home/opc/.local/bin/penpot-mcp-proxy` — wrapper que inicia o MCP
- `~/.claude.json` — contém `mcpServers.penpot` (não mexer em `settings.json`)
- `legal-workbench/ccui-app/src/styles.css` — tokens de design (fonte de verdade)
- `legal-workbench/ccui-app/src/components/CaseSelector.tsx` — layout da tela 1
- `legal-workbench/ccui-app/src/components/SessionView.tsx` — layout da tela 2
- `legal-workbench/ccui-app/src/components/ChatView.tsx` — bubbles e mensagens
- `docs/contexto/01032026-penpot-mcp-ativo-e-design-ccui.md` — contexto detalhado

## Verificar estado inicial

```bash
# Serviços Penpot rodando?
lsof -ti:4401 && echo "MCP ok" || echo "MCP DOWN"
lsof -ti:4400 && echo "plugin-ui ok" || echo "plugin-ui DOWN"
```

Se DOWN, reiniciar conforme o documento de contexto.

Depois verificar com `ToolSearch("penpot")` — deve retornar `mcp__penpot__execute_code`.

## Próximos passos (por prioridade)

### 1. Completar Design System — Message Bubbles

**Onde:** Penpot, página "Design System", board "Design System"
**O que:** Adicionar os dois tipos de bubble na seção "MESSAGE BUBBLES" (y≈1004)

```javascript
// Padrão correto para texto com largura fixa:
const t = penpot.createText("conteúdo");
t.resize(300, 40);          // primeiro resize
t.growType = "fixed";       // depois fixar
t.fills = [{ fillColor: "#ede9e3" }];
t.x = 76; t.y = 1012;
board.insertChild(board.children.length, t);
```

- User bubble: fundo `#1f1109`, borda-radius 12, alinhado à direita
- Assistant bubble: fundo `#101010`, borda-radius 12, alinhado à esquerda

**Verificar:** `mcp__penpot__export_shape` com o shapeId do board DS para ver resultado

### 2. Criar tela CaseSelector (1280×800)

**Onde:** Penpot, página "CaseSelector"
**O que:** Board 1280×800 com:
- Header: `bg-surface` (#101010), "LexVector / Selecionar caso", borda inferior `#1e1e1e`
- Main: centralizado max 560px, título + 2 CaseCards ready + 1 incomplete
- Usar tokens do CSS: `#080808` bg, `#d97757` accent, `#ede9e3` text

**Estrutura de referência:** `CaseSelector.tsx`

### 3. Criar tela SessionView (1280×800)

**Onde:** Penpot, página "SessionView"
**O que:** Board 1280×800 com:
- Header: Briefcase icon + case ID + ModeToggle + ConnectionStatus + Encerrar
- Chat area: 3 mensagens (1 user, 2 assistant com tool_use pill)
- Input: textarea + send button, borda accent no focus

**Estrutura de referência:** `SessionView.tsx` + `ChatView.tsx`

### 4. Merge dos bugfixes ccui-app para main

**Onde:** repo lex-vector, branch wrapper-legal-agents-front
**O que:**
```bash
cd /home/opc/lex-vector
git checkout main
git merge --ff-only wrapper-legal-agents-front
```
**Commits a mergear:** `a3799a6` (deduplicar chat_start + suprimir pills)

## Tokens de Design (referência rápida)

```
bg-base:      #080808    accent:       #d97757
bg-surface:   #101010    accent-dim:   #1f1109 (aprox)
bg-elevated:  #161616    text-primary: #ede9e3
border:       #1e1e1e    text-sec:     #6b6560
border-mid:   #2a2a2a    text-muted:   #3a3735
radius: sm=6 md=10 lg=14
```
