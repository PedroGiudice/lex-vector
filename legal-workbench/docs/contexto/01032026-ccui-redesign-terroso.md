# Contexto: Redesign CCUI -- Estetica Terrosa + Penpot/Vibma MCP

**Data:** 2026-03-01
**Sessao:** wrapper-legal-agents-front
**Duracao:** ~2h

---

## O que foi feito

### 1. Redesign completo do CCUI frontend (Opus)

O frontend-developer (Opus) reescreveu os 3 arquivos principais do CCUI com uma nova
estetica chamada "Briefing Room de Inteligencia Juridica":

- **Tipografia:** Instrument Serif (italic) para titulos, Geist Mono para labels/codigo, DM Sans como body
- **Layout:** grid de blueprint com linhas a 0.012 opacidade, noise texture SVG, sidebar colapsavel (Ctrl+B)
- **Componentes:** barra lateral dourada 2px em mensagens assistant (sem avatar redondo), input retangular sem border-radius, labels caixa alta com tracking largo

### 2. Troca de paleta para tons terrosos

Paleta inicial era azul-negro + dourado. PD pediu tons terrosos, sem azul nem amarelo.
Opus reescreveu completamente os 3 arquivos com a nova paleta:

| Papel | Cor hex |
|-------|---------|
| Base | `#0d0a08` (marrom-negro) |
| Paineis | `#110e0b` (cafe escuro) |
| Borders | `#231d15` (mogno) |
| Accent primario | `#a0603a` (terracota/argila queimada) |
| Accent acao | `#b85a30` (ocre queimado) |
| Texto principal | `#c0a880` (areia quente) |
| Texto body | `#c8b088` (pergaminho) |
| Texto muted | `#5a4a32` (tabaco) |
| Texto dim | `#3e3222` (folha seca) |
| Sucesso | `#5a7a3a` (musgo) |
| Erro | `#8a3028` (tijolo escuro) |
| Grid overlay | `rgba(160,96,58,0.018)` (argila) |

### 3. Configuracao de tools MCP para agentes

Adicionadas tools do Penpot, Coolors, Color Scheme e Design Critique aos agentes:
- `frontend-developer.md` -- 5 tools Penpot + 17 Coolors + 8 Color Scheme + 6 Design Critique
- `fullstack-ops.md` -- mesmas tools

### 4. Penpot MCP -- estado

O Penpot MCP server esta funcional (porta 4401, SSE). O plugin esta instalado no browser.
O projeto CCUI no Penpot tem 3 paginas:
- "Design System" -- parcialmente completo (cores/tipografia/componentes da paleta ANTIGA, message bubbles incompletos)
- "CaseSelector" -- VAZIA
- "SessionView" -- VAZIA

Tentamos delegar a criacao do design no Penpot a subagentes, mas:
- O agente Sonnet travou no high_level_overview
- O fullstack-ops nao tinha tools do Penpot (resolvido agora)
- Nenhum design novo foi criado no Penpot nesta sessao

### 5. Vibma MCP (Figma bridge)

O usuario mencionou a tool Vibma (https://github.com/ufira-ai/Vibma/tree/main) como ferramenta
instalada. Nao foi utilizada nesta sessao, mas deve ser explorada na proxima.
As tools `mcp__Vibma__*` aparecem na lista de deferred tools do sistema.

## Estado dos arquivos

### Repo lex-vector (worktree wrapper-legal-agents-front)

| Arquivo | Status |
|---------|--------|
| `legal-workbench/frontend/src/components/ccui-v2/CCuiChatInterface.tsx` | Reescrito -- nova estetica terrosa |
| `legal-workbench/frontend/src/components/ccui-v2/CCuiLayout.tsx` | Reescrito -- layout com sidebar, grid, noise |
| `legal-workbench/frontend/src/pages/CCuiV2Module.tsx` | Modificado -- alinhado com nova paleta |

### Repo .claude (agents)

| Arquivo | Status |
|---------|--------|
| `agents/frontend-developer.md` | Modificado -- +36 tools (Penpot, Coolors, Color Scheme, Design Critique) |
| `agents/fullstack-ops.md` | Modificado -- +36 tools (mesmas) |

## Pendencias identificadas

1. **Design System no Penpot desatualizado** -- ainda usa paleta antiga (coral #d97757), precisa atualizar para terrosa
2. **Telas CaseSelector e SessionView no Penpot vazias** -- precisam ser criadas
3. **Message Bubbles no Design System incompletos** -- so tem placeholder
4. **Commits dos agents nao feitos** -- as mudancas em frontend-developer.md e fullstack-ops.md estao uncommitted no repo .claude
5. **Commits do frontend nao feitos** -- as reescritas estao uncommitted no worktree
6. **Merge para main pendente** -- branch wrapper-legal-agents-front tem commits anteriores (bugfixes ccui-app) + redesign
7. **Vibma MCP nao explorado** -- tools disponiveis mas nao testadas

## Decisoes tomadas

- **Paleta terrosa sem azul/amarelo:** PD vetou tons frios e dourados. Terracota (#a0603a) como accent primario
- **Tipografia editorial:** Instrument Serif italic para titulos, Geist Mono para dados, DM Sans body
- **Reescrita total vs incremental:** Opus optou por reescrever arquivos inteiros em vez de editar pontualmente -- mais consistente
- **Agentes com tools de design:** frontend-developer e fullstack-ops agora tem acesso a Penpot + Coolors + Color Scheme + Design Critique para trabalho de design
