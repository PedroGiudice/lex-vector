# Retomada: CCUI Redesign Terroso -- Finalizar Design no Penpot

## Contexto rapido

O frontend do CCUI foi completamente reescrito com uma estetica editorial escura e tons terrosos (terracota, mogno, cafe, tabaco). Os 3 arquivos React (CCuiLayout, CCuiChatInterface, CCuiV2Module) estao prontos mas uncommitted no worktree `wrapper-legal-agents-front`. Build passa sem erros.

O Penpot MCP esta funcional (porta 4401/SSE), o plugin conecta via browser. Porem o design no Penpot esta desatualizado (paleta antiga) e as telas CaseSelector/SessionView estao vazias. Os agentes frontend-developer e fullstack-ops agora tem tools de Penpot, Coolors, Color Scheme e Design Critique.

O usuario tambem mencionou o Vibma MCP (bridge para Figma -- https://github.com/ufira-ai/Vibma/tree/main) cujas tools estao disponiveis como deferred tools (`mcp__Vibma__*`). Precisa ser explorado.

## Arquivos principais

- `legal-workbench/frontend/src/components/ccui-v2/CCuiChatInterface.tsx` -- interface de chat reescrita (paleta terrosa)
- `legal-workbench/frontend/src/components/ccui-v2/CCuiLayout.tsx` -- layout com sidebar colapsavel (paleta terrosa)
- `legal-workbench/frontend/src/pages/CCuiV2Module.tsx` -- modulo principal CCUI
- `~/.claude/agents/frontend-developer.md` -- agente com tools Penpot + Coolors + Color Scheme + Design Critique
- `~/.claude/agents/fullstack-ops.md` -- idem
- `legal-workbench/docs/contexto/01032026-ccui-redesign-terroso.md` -- contexto detalhado

## Paleta terrosa (referencia)

```
Base:       #0d0a08  (marrom-negro)
Paineis:    #110e0b  (cafe escuro)
Borders:    #231d15  (mogno)
Accent:     #a0603a  (terracota)
Acao:       #b85a30  (ocre queimado)
Texto:      #c0a880  (areia quente)
Body:       #c8b088  (pergaminho)
Muted:      #5a4a32  (tabaco)
Dim:        #3e3222  (folha seca)
Sucesso:    #5a7a3a  (musgo)
Erro:       #8a3028  (tijolo)
```

## Proximos passos (por prioridade)

### 1. Commitar mudancas pendentes
**Onde:** worktree `wrapper-legal-agents-front` e repo `~/.claude`
**O que:** `git add` e commit dos 3 arquivos React + 2 arquivos de agents
**Por que:** proteger trabalho feito, nada foi commitado nesta sessao
**Verificar:** `git status` mostra clean

### 2. Atualizar Design System no Penpot com paleta terrosa
**Onde:** Penpot, pagina "Design System"
**O que:** trocar os color tokens da paleta antiga (coral #d97757) para a nova terrosa, completar message bubbles
**Por que:** o design no Penpot diverge do codigo -- precisa estar sincronizado
**Verificar:** `mcp__penpot__export_shape` do Design System board mostra cores terrosas

### 3. Criar tela CaseSelector no Penpot (1280x800)
**Onde:** Penpot, pagina "CaseSelector"
**O que:** frame 1280x800 com header, busca, lista de case cards, usando paleta terrosa
**Por que:** referencia visual para o frontend
**Verificar:** `mcp__penpot__export_shape` da tela criada

### 4. Criar tela SessionView no Penpot (1280x800)
**Onde:** Penpot, pagina "SessionView"
**O que:** frame 1280x800 com header + sidebar + chat area + input bar, usando paleta terrosa
**Por que:** referencia visual para o frontend
**Verificar:** `mcp__penpot__export_shape` da tela criada

### 5. Explorar Vibma MCP
**Onde:** deferred tools `mcp__Vibma__*`
**O que:** testar `mcp__Vibma__ping`, ver se conecta a algum projeto Figma, avaliar utilidade vs Penpot MCP
**Por que:** usuario indicou como ferramenta instalada, pode ser mais estavel que Penpot MCP para design
**Verificar:** `ToolSearch("Vibma")` retorna tools e `ping` responde

### 6. Usar frontend-developer para alinhar design <-> codigo
**Onde:** subagente frontend-developer (Opus)
**O que:** pedir ao agente para ver o design no Penpot (export_shape), comparar com o codigo, e ajustar detalhes
**Por que:** garantir fidelidade 1:1 entre design e implementacao
**Verificar:** `bun run build` passa + visual no browser bate com Penpot

## Como verificar

```bash
# Build do frontend
cd legal-workbench/frontend && bun run build

# Penpot MCP ativo
curl -s -X POST http://localhost:4401/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' | head -1

# Penpot UI no browser
# http://100.123.73.128:9001
```
