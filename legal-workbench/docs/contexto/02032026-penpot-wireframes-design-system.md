# Contexto: Wireframes e Design System no Penpot via MCP

**Data:** 2026-03-02
**Sessao:** ccui-redesign-vibma
**Duracao:** ~2h

---

## O que foi feito

### 1. Design System -- Cores de Agente adicionadas

Adicionada secao "AGENT COLORS" ao board existente "Design System" na pagina homologa do Penpot. 5 cores auto-atribuidas por agente:

| Agente | Cor | Hex |
|--------|-----|-----|
| Main (Terracota) | Accent primario | `#a0603a` |
| Agent 2 (Oliva) | Verde oliva | `#7a8a4a` |
| Agent 3 (Teal) | Azul-esverdeado | `#4a7a8a` |
| Agent 4 (Malva) | Roxo suave | `#8a5a7a` |
| Agent 5 (Musgo) | Verde musgo | `#6a7a3a` |

### 2. Wireframes Multi-Agent (pagina "Wireframes - Multi-Agent")

Criados 3 boards:

- **WF-01 / Tab View** (0,0 1280x800) -- Layout com tab bar para alternar entre agentes. Sidebar esquerda (icon + panel), tabs com dot colorido por agente, chat area, input, status bar.
- **WF-02 / Split View** (0,950 1280x800) -- Main pane 70% + strip lateral 30% com 3 panes de teammates empilhados. Resize handle central. Cada pane com color bar, nome, status, output preview.
- **WF-03 / Tab States + Agent Indicators** (0,1900 1280x500) -- Detalhe de estados das tabs (active, inactive, notification), indicadores de status (thinking, tool use, idle, error, complete), view toggle component.

### 3. CaseSelector (pagina "CaseSelector")

Board completo "CaseSelector / Main" (1280x900):

- Header com logo Instrument Serif italic + avatar + status dot
- Hero: "Selecione um caso" + subtitle + search bar + filter pills
- Stats row: 4 metricas (total, em andamento, docs, ultima atividade)
- Grid 3x2 de case cards com: accent bar lateral colorida, ID, badge status, titulo serif, partes, tags, divider, docs count, progress bar, hover glow
- Footer: botoes "Novo Caso" + "Importar" + atalhos de teclado

### 4. SessionView (pagina "SessionView")

Board completo "SessionView / Main" (1440x900):

- Header: logo italic + case badge + modelo + view toggle + hora + avatar
- Icon sidebar (44px) com 4 icones + indicador ativo
- Sidebar panel (240px): label + new session btn + 5 sessoes listadas
- Chat area: mode toggle (Cliente/Dev), timestamp, user msg com accent bar, assistant msg com 2 tool calls (Read + Grep com status), analise em 3 pontos
- Input: campo arredondado + send btn + hints (/ comandos, @ mencoes)
- Status bar: online + ws url + modelo + branch + tokens + encoding + hora + custo

### 5. Paleta de cores ajustada (backgrounds mais claros)

Usando `mcp__coolors__generate_gradient` (lab interpolation) entre `#0d0a08` e `#a0603a`, definida nova escala de backgrounds que preserva o tom terroso mas evita displays escuros demais:

| Uso | Hex anterior | Hex novo |
|-----|-------------|----------|
| BG base | `#0d0a08` | `#1c1510` |
| Header/footer | `#0c0907` | `#17120d` |
| Panels | `#110e0b` | `#211a14` |
| Cards elevados | `#151210` | `#291c15` |
| Borders | `#231d15` | `#36241a` |

Aplicada na SessionView. Falta aplicar nas demais paginas.

### 6. Fontes custom uploadadas no Penpot

- **Monaspace Argon NF** (MonaspiceAr Nerd Font Mono) -- Regular, Bold, Medium. Copiada de `cmr-auto:/home/cmr-auto/.config/fonts/Monaspace/`
- **Monaspace Krypton NF** -- tambem disponivel
- **GoMono NF** -- upload feito pelo usuario, MAS nao apareceu nas custom fonts da API (pode precisar re-upload)

Fontes aplicadas no CaseSelector: Monaspace Argon NF substituiu Source Code Pro em 68 textos. Instrument Serif nos titulos/stats (13 textos).

## Estado do Penpot (arquivo "Novo arquivo 1")

| Pagina | Estado |
|--------|--------|
| Design System | Board existente (sessao anterior) + secao Agent Colors adicionada |
| CaseSelector | Board completo, fontes atualizadas, paleta original (nao atualizada) |
| SessionView | Board completo, fontes Monaspace, paleta atualizada (mais clara) |
| Wireframes - Multi-Agent | 3 boards (Tab, Split, Components), paleta original |

## Decisoes tomadas

- **Fontes:** Monaspace Argon NF como mono principal, Instrument Serif para titulos/display, GoMono pretendida para texto corrido (pendente upload funcional)
- **Paleta backgrounds:** subir ~2 tons usando gradiente LAB entre base e accent, mantendo tom terroso
- **Organizacao Penpot:** 1 board por pagina, elementos dentro do board (nao soltos no root)
- **API Penpot:** `penpot.root.children` retorna os shapes, nao `penpot.currentPage.children` (quirk da API)
- **Navegacao entre paginas:** requer fechamento/reabertura do plugin OU usuario navegar manualmente

## Pendencias

1. **Aplicar paleta clara no CaseSelector e Wireframes** -- so SessionView foi atualizada
2. **GoMono upload** -- nao apareceu nas custom fonts, precisa re-upload
3. **GoMono como fonte de texto principal** -- usuario quer essa fonte para body text
4. **Export PNG muito escuro** -- limitacao do Penpot export em resolucao baixa com paleta dark. Prints manuais sao necessarios para validacao visual
5. **Design System board** -- atualizar paleta de cores la tambem (ainda mostra cores antigas)

## Notas tecnicas do Penpot MCP

- Multiplas instancias do plugin causam erro "Multiple Penpot MCP Plugin instances"
- `penpot.openPage()` muda a pagina no UI mas nem sempre atualiza `currentPage` no contexto do plugin
- Nao ha API para mover shapes entre paginas
- `fontFamily` para Google Fonts funciona pelo nome; para custom fonts precisa de `fontId` explicito
- Textos criados com `fontFamily: "Georgia"` caem em fallback `sourcesanspro` -- precisa usar Instrument Serif com fontId
