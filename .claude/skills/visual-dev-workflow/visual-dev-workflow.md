---
name: visual-dev-workflow
description: Workflow para desenvolvimento visual com subagente e verificacao periodica
invoke: /visual-dev
---

# Visual Dev Workflow

Workflow automatizado para desenvolvimento frontend/UI com:
1. Dev server em background
2. Subagente especializado trabalhando
3. Verificacao visual periodica via Chrome MCP

## Quando Usar

- Desenvolvimento de UI/frontend
- Quando quer ver o resultado enquanto trabalha
- Melhorias visuais iterativas
- "Max out" de estetica

## Workflow

### Passo 1: Iniciar Dev Server

```bash
# Encontrar porta livre
PORT=5180

# Iniciar em background
cd $PROJECT_DIR && bun run dev --port $PORT --host &
```

### Passo 2: Preparar Chrome

Usar as ferramentas Chrome MCP:
1. `mcp__claude-in-chrome__tabs_context_mcp` - obter contexto
2. `mcp__claude-in-chrome__tabs_create_mcp` - criar nova tab
3. `mcp__claude-in-chrome__navigate` - navegar para localhost:PORT

### Passo 3: Delegar para Subagente

Use o Task tool com `subagent_type: frontend-developer`:

```
Task:
  subagent_type: frontend-developer
  prompt: |
    [Descricao detalhada do trabalho]

    Dev server rodando em http://localhost:PORT

    Instrucoes:
    1. Faca as mudancas no codigo
    2. O HMR vai atualizar automaticamente
    3. Commite mudancas significativas
```

### Passo 4: Verificacao Visual Periodica

A cada mudanca significativa ou quando quiser validar:

```
mcp__claude-in-chrome__computer:
  action: screenshot
  tabId: [tab do dev server]
```

Analisar o screenshot e dar feedback ao subagente se necessario.

## Ferramentas Chrome MCP Uteis

| Tool | Uso |
|------|-----|
| `tabs_context_mcp` | Ver tabs disponiveis |
| `navigate` | Navegar para URL |
| `computer` (screenshot) | Capturar tela |
| `computer` (scroll) | Scroll na pagina |
| `read_page` | Ler accessibility tree |
| `find` | Encontrar elementos |

## Exemplo de Prompt

```
Usuario: "Melhore a UI do formulario de login com animacoes"

Claude:
1. Identificar projeto e porta
2. Iniciar dev server
3. Abrir Chrome na URL
4. Tirar screenshot inicial
5. Delegar para frontend-developer com contexto
6. Verificar resultado
7. Iterar se necessario
```

## Troubleshooting

### Dev server nao inicia
- Verificar se porta esta livre: `lsof -i :PORT`
- Matar processo: `kill -9 PID`
- Usar porta diferente

### Chrome MCP nao responde
- Verificar se extensao esta instalada
- Tentar `tabs_context_mcp` primeiro
- Criar nova tab se necessario

### Service worker cacheado
- Usar porta diferente
- Hard refresh (Ctrl+Shift+R)
- Limpar cache do navegador

## Integracao com Subagentes

O subagente `frontend-developer` tem acesso a:
- Todas as ferramentas de arquivo (Read, Write, Edit)
- Chrome MCP tools
- Context7 para documentacao
- Bash para comandos
- Magic component builder

Ele pode fazer verificacoes visuais independentes durante o trabalho.
