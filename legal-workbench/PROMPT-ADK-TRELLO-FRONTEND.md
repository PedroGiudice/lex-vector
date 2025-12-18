# PROMPT: Finalizar Trello Command Center Frontend

## Contexto do Projeto

O **Trello Command Center** é um frontend React/TypeScript para extração de dados do Trello. O foco principal é **EXTRAÇÃO DE DADOS** (não operações de edição).

### Stack Técnica
- React 18 + TypeScript + Vite
- Zustand (state management)
- Tailwind CSS (dark theme)
- API Backend: FastAPI em `/api/trello/api/v1`

### Arquivos Principais
```
legal-workbench/frontend/src/
├── services/trelloApi.ts      # API client + export functions
├── store/trelloStore.ts       # Zustand store
├── components/
│   ├── layout/MainLayout.tsx  # Layout principal
│   └── trello/
│       ├── DataTable.tsx      # Tabela de cards
│       ├── ActionsPanel.tsx   # Painel de ações (export focus)
│       ├── FilterSidebar.tsx  # Filtros
│       └── MoveCardsModal.tsx # Modal batch move
```

---

## Decisões de Design

### 1. Foco em EXTRAÇÃO DE DADOS
O frontend prioriza extrair dados do Trello. Operações de edição são secundárias.

### 2. Single Mode vs Batch Mode
- **Single Mode**: Selecionar 1 card → "Open in Trello" link + export individual
- **Batch Mode**: Selecionar N cards → Operações em lote + export múltiplo

### 3. Export com Enriquecimento
Os dados exportados incluem:
- `listName` (nome da lista, não apenas ID)
- `labelNames` (array com nome e cor das labels)
- `memberNames` (array com fullName e username)

### 4. Formatos de Export
- JSON (estruturado)
- CSV (para planilhas)
- Markdown (para documentação)
- Plain Text

---

## O Que Já Foi Implementado

### Backend (100% funcional)
- `/api/trello/api/v1/boards` - Lista boards
- `/api/trello/api/v1/boards/{id}` - Retorna board + lists + cards em uma chamada
- Pydantic models com `extra='ignore'` para flexibilidade

### Frontend (80% implementado)

**Funcional:**
- Layout 3 colunas (sidebar, data table, actions panel)
- Zustand store com estado completo
- API client com todas as funções
- Export real com download de arquivo
- Copy to clipboard
- Seleção de cards (single + multi)
- Filtro por lista

**Faltando:**
1. **Labels e Members não carregam** - Backend não retorna no endpoint atual
2. **Filtros avançados** - Due date, status, labels (UI existe mas não funciona)
3. **Busca avançada** - Endpoint `/search` não implementado no backend
4. **Cores das labels** - Mostrar cor real das labels na tabela
5. **Avatars dos members** - Mostrar iniciais ou avatar

---

## O Que Precisa Ser Feito

### Prioridade 1: Corrigir Carregamento de Dados
```typescript
// trelloStore.ts - fetchBoardData não retorna labels/members
// Backend retorna: { board, lists, cards }
// Falta: labels, members

// OPÇÃO A: Criar endpoints separados no backend
// GET /api/trello/api/v1/boards/{id}/labels
// GET /api/trello/api/v1/boards/{id}/members

// OPÇÃO B: Expandir endpoint existente para incluir labels/members
```

### Prioridade 2: Labels na Tabela
```typescript
// DataTable.tsx linha 110-114
// Atualmente mostra placeholder vermelho para todas as labels
// Precisa: resolver label ID → nome + cor
```

### Prioridade 3: Filtros Funcionais
```typescript
// FilterSidebar.tsx precisa conectar filtros ao store
// Filtros definidos em trelloStore:
// - labelFilterIds: Set<string>
// - dueFilter: 'all' | 'today' | 'week' | 'overdue' | 'none'
// - statusFilter: 'open' | 'archived' | 'all'
// - memberFilterIds: Set<string>
```

### Prioridade 4: Polish
- Loading states melhores
- Error handling visual
- Responsividade
- Keyboard shortcuts (Ctrl+A, Ctrl+C)

---

## Endpoints Backend Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/boards` | GET | Lista todos os boards |
| `/boards/{id}` | GET | Board + lists + cards |
| `/cards` | POST | Criar card |
| `/cards/{id}` | PUT | Atualizar card |
| `/cards/{id}` | DELETE | Deletar card |
| `/cards/{id}/actions/comments` | POST | Adicionar comentário |

---

## Paleta de Cores (Tailwind)

```css
/* Definido em tailwind.config.js */
bg-main: #0D1117        /* Fundo principal */
bg-panel: #161B22       /* Painéis */
bg-input: #21262D       /* Inputs */
text-primary: #E6EDF3   /* Texto principal */
text-secondary: #8B949E /* Texto secundário */
accent-blue: #58A6FF    /* Accent */
success-green: #3FB950  /* Sucesso */
danger-red: #F85149     /* Perigo */
```

---

## Como Rodar

```bash
cd legal-workbench

# Start all services
TRELLO_API_KEY="..." TRELLO_API_TOKEN="..." docker compose up -d

# Frontend em http://localhost:80/app
# API em http://localhost:80/api/trello/api/v1
```

---

## Referência Visual

O layout segue o wireframe:
```
┌────────────────────────────────────────────────────────────────┐
│ ⚡ Trello Command Center           [Board Selector] [Sync] [⚙️]│
├──────────┬─────────────────────────────────┬───────────────────┤
│ SIDEBAR  │         DATA TABLE              │   ACTIONS PANEL   │
│          │                                 │                   │
│ Boards   │ [☑] CARD    LIST    DUE  LABELS │ 📤 Extract Data   │
│ > Board1 │ [☐] Card1   Todo    15/12  🔴   │ Format: [JSON ▼]  │
│   Board2 │ [☑] Card2   Doing   -      🟢   │ [Copy] [Download] │
│          │ [☐] Card3   Done    20/12  🔵   │                   │
│ Filters  │                                 │ Quick Access      │
│ Due: All │                                 │ [Open in Trello]  │
│ Status   │                                 │                   │
│          │                                 │ Batch Operations  │
│          │ Sel: 2 | Total: 50 | Filt: 10  │ [Move] [Labels]   │
└──────────┴─────────────────────────────────┴───────────────────┘
```

---

## Critérios de Aceite

1. **Export funciona** - Selecionar 1+ cards e exportar em qualquer formato
2. **Filtros funcionam** - Filtrar por lista, due date, status
3. **Labels visíveis** - Ver cores reais das labels na tabela
4. **UI responsiva** - Funcionar em diferentes tamanhos de tela
5. **Build passa** - `npm run build` sem erros TypeScript

---

## FASE FINAL: Testes Visuais com Playwright

**IMPORTANTE**: Após implementação, usar agente `test-writer-fixer` ou Playwright MCP para validação visual completa.

### Checklist de Testes E2E

```gherkin
Feature: Trello Command Center - Data Extraction

  Background:
    Given I navigate to http://localhost:80/app
    And I wait for boards to load

  # ============================================
  # TESTE 1: Carregamento Inicial
  # ============================================
  Scenario: Page loads with data
    Then I should see "Trello Command Center" header
    And Board selector should be enabled
    And Data table should show cards
    And "Extract Data" panel should be visible

  # ============================================
  # TESTE 2: Single Card Selection
  # ============================================
  Scenario: Select single card
    When I click on a card row
    Then The card should be highlighted
    And Checkbox should be checked
    And "Open in Trello" button should appear
    And Selection count should show "1"

  # ============================================
  # TESTE 3: Batch Selection
  # ============================================
  Scenario: Select multiple cards
    When I click checkbox on 3 different cards
    Then All 3 cards should be highlighted
    And Selection count should show "3"
    And "Batch Operations" section should appear
    And "Move Selected" button should be visible

  # ============================================
  # TESTE 4: Select All
  # ============================================
  Scenario: Select all cards
    When I click the header checkbox
    Then All visible cards should be selected
    And Selection count should match total count

  # ============================================
  # TESTE 5: Export JSON (Single)
  # ============================================
  Scenario: Export single card as JSON
    When I select 1 card
    And I select "JSON" format
    And I click "Download"
    Then A file "trello-export-*.json" should download
    And File should contain card data with enriched fields

  # ============================================
  # TESTE 6: Export CSV (Batch)
  # ============================================
  Scenario: Export multiple cards as CSV
    When I select 5 cards
    And I select "CSV" format
    And I click "Download"
    Then A file "trello-export-*.csv" should download
    And CSV should have headers: ID,Name,Description,List,Labels,Members,Due Date,Status,URL

  # ============================================
  # TESTE 7: Copy to Clipboard
  # ============================================
  Scenario: Copy cards to clipboard
    When I select 2 cards
    And I select "Markdown" format
    And I click "Copy"
    Then Success message should appear
    And Clipboard should contain markdown content

  # ============================================
  # TESTE 8: Filter by List
  # ============================================
  Scenario: Filter cards by list
    When I click on a list in the sidebar
    Then Only cards from that list should be visible
    And "Filtered" count should update

  # ============================================
  # TESTE 9: Open in Trello
  # ============================================
  Scenario: Open card in Trello
    When I select 1 card
    And I click "Open in Trello"
    Then A new tab should open with Trello card URL

  # ============================================
  # TESTE 10: Change Board
  # ============================================
  Scenario: Switch between boards
    When I select a different board from dropdown
    Then Data table should reload
    And Cards from new board should appear
    And Selection should be cleared
```

### Comandos Playwright para Testes

```typescript
// Usar com MCP Playwright ou test-writer-fixer agent

// 1. Navegar e aguardar carregamento
await page.goto('http://localhost:80/app');
await page.waitForSelector('table tbody tr');

// 2. Selecionar card
await page.click('table tbody tr:first-child');

// 3. Verificar seleção
const isSelected = await page.locator('table tbody tr:first-child').evaluate(
  el => el.classList.contains('bg-selection-bg')
);

// 4. Exportar
await page.selectOption('select', 'json');
await page.click('button:has-text("Download")');

// 5. Screenshot para validação visual
await page.screenshot({ path: 'trello-test-export.png' });
```

### Matriz de Testes por Funcionalidade

| Funcionalidade | Single Mode | Batch Mode | Esperado |
|----------------|-------------|------------|----------|
| Seleção | ✅ 1 card | ✅ N cards | Highlight + checkbox |
| Export JSON | ✅ | ✅ | Download arquivo |
| Export CSV | ✅ | ✅ | Download arquivo |
| Export Markdown | ✅ | ✅ | Download arquivo |
| Copy Clipboard | ✅ | ✅ | Alert de sucesso |
| Open in Trello | ✅ | ❌ (não aplicável) | Nova aba |
| Move Cards | ❌ | ✅ | Modal aparece |
| Bulk Labels | ❌ | ✅ | Modal aparece |
| Filter by List | N/A | N/A | Tabela filtra |
| Change Board | N/A | N/A | Dados recarregam |

### Screenshots de Referência

Após cada teste, capturar screenshot para validação:

```bash
# Diretório para screenshots
legal-workbench/test-screenshots/
├── 01-initial-load.png
├── 02-single-selection.png
├── 03-batch-selection.png
├── 04-export-panel.png
├── 05-filter-active.png
└── 06-board-changed.png
```

### Critérios de Sucesso dos Testes

- [ ] Todos os 10 cenários passam
- [ ] Nenhum erro no console do browser
- [ ] Tempo de carregamento < 3s
- [ ] Export gera arquivos válidos
- [ ] UI mantém consistência visual
