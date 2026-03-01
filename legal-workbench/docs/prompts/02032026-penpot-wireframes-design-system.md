# Retomada: Aprimoramento visual do CCUI no Penpot

## Contexto rapido

Sessao anterior criou wireframes e design system no Penpot via MCP para o CCUI multi-agent. Existem 4 paginas no Penpot: Design System, CaseSelector, SessionView, Wireframes - Multi-Agent. Todas com boards completos. A paleta foi elevada (backgrounds mais claros, tom terroso preservado) mas so na SessionView. Fontes custom foram uploadadas (Monaspace Argon NF, Monaspace Krypton NF). GoMono foi uploadada mas nao reconhecida pela API -- pode precisar re-upload. O usuario quer a estetica do app do Claude como direcao de aprimoramento. Sessao requer brainstorming.

## Arquivos principais

- `docs/contexto/02032026-penpot-wireframes-design-system.md` -- contexto detalhado
- `docs/contexto/01032026-ccui-agent-teams-design.md` -- decisoes de design multi-agent (tab+split, cores, Zustand)
- `docs/prompts/01032026-ccui-agent-teams-design.md` -- prompt anterior sobre agent teams
- `legal-workbench/frontend/src/components/ccui-v2/CCuiLayout.tsx` -- layout atual implementado
- `legal-workbench/frontend/src/components/ccui-v2/CCuiChatInterface.tsx` -- chat atual (~1200 linhas)

## Direcao da proxima sessao

O usuario quer aprimorar o design visual inspirando-se na **estetica do app do Claude** (claude.ai). Nao sabe exatamente o que quer -- precisa de brainstorming. Pontos a explorar:

- Analise visual do app do Claude (tipografia, espacamento, message bubbles, input area, sidebar)
- Contraste entre a estetica terrosa editorial atual e elementos do Claude
- Quais aspectos do Claude adaptar vs. manter a identidade terrosa
- Fontes: GoMono para body text (re-upload necessario), Monaspace Argon para labels/mono

## Proximos passos (por prioridade)

### 1. Brainstorming sobre direcao visual
**Onde:** Penpot, todas as paginas
**O que:** Usar `superpowers:brainstorming` para explorar o que do app do Claude inspiraria o CCUI. Capturar screenshots do claude.ai como referencia. Identificar: message rendering, input field style, sidebar behavior, animations, spacing.
**Por que:** Usuario tem direcao mas nao especificacao; brainstorming estruturado e obrigatorio.

### 2. Aplicar paleta clara nas paginas restantes
**Onde:** Penpot -- CaseSelector, Wireframes - Multi-Agent, Design System
**O que:** Mesmo mapeamento ja feito na SessionView: base `#1c1510`, panels `#211a14`, cards `#291c15`, borders `#36241a`
**Verificar:** Export PNG dos boards -- deve mostrar mais contraste

### 3. Re-upload GoMono
**Onde:** Penpot UI (Assets > Fonts)
**O que:** Arquivos em `/tmp/gomono/` na VM ou diretamente do PC do usuario
**Verificar:** `penpot.fonts.all.filter(f => f.name.includes("Go"))` deve retornar a fonte

### 4. Aplicar GoMono como fonte de texto corrido
**Onde:** Todos os boards no Penpot
**O que:** Trocar body text (mensagens, descricoes) de Monaspace Argon para GoMono. Manter Monaspace para labels/mono tecnico.

## Como verificar

```bash
# Branch
git checkout ccui-redesign-vibma

# Penpot acessivel em
# http://100.123.73.128:9001

# Fontes custom no PC Linux
ssh cmr-auto@100.102.249.9 "ls ~/.local/share/fonts/Go-Mono/"
ssh cmr-auto@100.102.249.9 "ls ~/.config/fonts/Monaspace/"
```

## Quirks do Penpot MCP

- Abrir plugin em UMA instancia so (multiplas = erro)
- Trocar de pagina: usuario navega manualmente, depois o plugin ve a pagina certa
- Shapes acessiveis via `penpot.root.children`, nao `penpot.currentPage.children`
- Custom fonts precisam de `fontId` explicito alem de `fontFamily`
- Export PNG e muito escuro com paleta dark -- usar prints manuais para validacao
