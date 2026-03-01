# Design: CCUI "Claude Terroso"

**Data:** 2026-03-02
**Abordagem:** Linguagem visual do Claude + identidade terrosa (paleta + Instrument Serif)

---

## Decisoes aprovadas

### Layout e Grid

```
[Icon Strip 48px] [Side Panel 240px*] [Chat Container (flex-1)] [Detail Panel 320px*]
                   * colapsavel                                   * sob demanda
```

- Icon strip (48px): sempre visivel, indicador ativo com barra terracota lateral
- Side panel (240px): colapsavel via Cmd+B, transicao 200ms ease-out
- Chat container: flex-1, mensagens em max-width 720px centralizado
- Detail panel (320px): aparece ao clicar tool call/agent activity, fecha com Esc
- Breakpoints: >=1440px panel aberto default, 1024-1439 fechado default

### Tipografia

| Nivel | Fonte | Peso | Tamanho | Uso |
|-------|-------|------|---------|-----|
| Display | Instrument Serif | Regular italic | 24-28px | Titulos, logo, hero |
| Heading | Instrument Serif | Regular | 18-20px | Headings, case titles |
| Body | GoMono NF | Regular | 14-15px | Mensagens, texto corrido |
| Body bold | GoMono NF | Bold | 14-15px | Enfase, labels |
| Code | Monaspace Argon NF | Regular | 13px | Code blocks, tools, paths |
| UI small | GoMono NF | Regular | 12px | Status bar, timestamps |

- Line-height body: 1.65
- Line-height headings: 1.3
- Paragrafo spacing: 16px

### Cores de texto (contraste validado WCAG AA)

- Primary: `#e8ddd0` (13.47:1 vs base)
- Secondary: `#a89880` (6.42:1 vs base)
- Muted: `#9a8a78` (5.40:1 vs base) -- elevado de #6a5a4a
- Accent: `#c8784a` (5.36:1 vs base) -- elevado de #a0603a

### Cores de background (paleta elevada)

| Uso | Hex |
|-----|-----|
| Base | `#1c1510` |
| Header/footer | `#17120d` |
| Panels | `#211a14` |
| Cards elevados | `#291c15` |
| Borders | `#36241a` |

### Cores de agente

| Agente | Hex |
|--------|-----|
| Main (Terracota) | `#a0603a` |
| Agent 2 (Oliva) | `#7a8a4a` |
| Agent 3 (Teal) | `#4a7a8a` |
| Agent 4 (Malva) | `#8a5a7a` |
| Agent 5 (Musgo) | `#6a7a3a` |

### Mensagens

- Container: max-width 720px centralizado, gap 24px entre mensagens
- User: accent bar terracota 3px esquerda, bg `#211a14`, border-radius 0 8px 8px 0
- Assistant: sem bubble, texto direto no fundo base, icone + label acima
- Code blocks: bg `#17120d`, border `#36241a`, Monaspace Argon 13px, radius 8px
- Tool calls: chip inline (dot agente + tool name + status), click abre Detail Panel
- Pensando: tres dots terracota animados

### Sidebar

- Dupla colapsavel: icon strip permanente + panel recolhivel
- Default expandida em >=1440px
- Atalho Cmd+B para toggle

### Tool calls e Agent activity

- Resumo inline: chips compactos dentro do fluxo
- Detail panel lateral (320px) para output completo
- Hibrido: nao polui o chat, detalhes acessiveis

---

## Secoes pendentes (definir durante implementacao Penpot)

- Input area (campo, attachments, hints)
- Status bar
- Header
- Animacoes e transicoes
- Multi-agent: tab view, split view, agent indicators
- CaseSelector redesign
