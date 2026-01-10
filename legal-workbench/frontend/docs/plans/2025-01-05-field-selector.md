# Plano: Trello Command Center - Field Selector

**Issue:** https://github.com/PedroGiudice/lex-vector/issues/120
**Data:** 2025-01-05
**Status:** Reviewed & Approved
**Revisão:** 2025-01-05 - Issues críticos corrigidos

---

## 0. Decisões da Revisão

| Questão | Decisão | Justificativa |
|---------|---------|---------------|
| Toast vs Alert | **Alert** | Consistência com código existente em ActionsPanel |
| desc na tabela | **Export-only** | Evitar complexidade de truncation/UX |
| Persistência | **Não** | Escopo mínimo, iteração futura |
| Tipos location | **trelloApi.ts** | Junto com Card interface |
| filteredCards | **Selector no store** | Reuso entre DataTable e ActionsPanel |

---

## 1. Contexto

### 1.1 Objetivo
Permitir que usuários selecionem quais campos dos cartões Trello desejam visualizar e exportar, com opção de copiar lista de títulos como texto.

### 1.2 Descobertas da Exploração

| Aspecto | Realidade |
|---------|-----------|
| UI Framework | **Tailwind CSS + Lucide** (não MUI) |
| State Management | Zustand (`trelloStore.ts`) |
| Export Location | `trelloApi.ts` (linhas 278-480) |
| Table Component | `DataTable.tsx` (231 linhas) |
| Actions Component | `ActionsPanel.tsx` (259 linhas) |

### 1.3 Campos Disponíveis

| Campo | Key | Default | Descrição |
|-------|-----|---------|-----------|
| Título | `name` | ✅ | Nome do cartão |
| Descrição | `desc` | ❌ | Texto descritivo |
| Etiquetas | `labels` | ❌ | Labels coloridas |
| Membros | `members` | ❌ | Pessoas atribuídas |
| Data de Entrega | `due` | ❌ | Due date |
| Lista | `idList` | ❌ | Coluna do board |

---

## 2. Arquitetura da Solução

### 2.1 Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│                     trelloStore.ts                          │
│  + selectedFields: Set<FieldKey>                            │
│  + setSelectedFields(fields)                                │
│  + toggleField(field)                                       │
│  + getFilteredCardData(card) → filtered object              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    ActionsPanel.tsx                         │
│  + FieldSelector component (checkboxes)                     │
│  + "Copiar Títulos" button                                  │
│  + Export usa selectedFields                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     DataTable.tsx                           │
│  + Colunas condicionais baseadas em selectedFields          │
│  + Mantém checkbox e name sempre visíveis                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     trelloApi.ts                            │
│  + exportData() recebe selectedFields                       │
│  + Filtra campos antes de gerar output                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Interface TypeScript

```typescript
// types/index.ts ou trelloStore.ts

type CardFieldKey = 'name' | 'desc' | 'labels' | 'members' | 'due' | 'idList';

interface FieldConfig {
  key: CardFieldKey;
  label: string;
  default: boolean;
}

const CARD_FIELDS: FieldConfig[] = [
  { key: 'name', label: 'Título', default: true },
  { key: 'desc', label: 'Descrição', default: false },
  { key: 'labels', label: 'Etiquetas', default: false },
  { key: 'members', label: 'Membros', default: false },
  { key: 'due', label: 'Data de Entrega', default: false },
  { key: 'idList', label: 'Lista', default: false },
];
```

---

## 3. Implementação Detalhada

### 3.1 Modificar `trelloStore.ts`

**Localização:** `/legal-workbench/frontend/src/store/trelloStore.ts`

**Adicionar ao state:**
```typescript
// Após linha ~45 (dentro de TrelloState interface)
selectedFields: Set<CardFieldKey>;

// Adicionar actions
setSelectedFields: (fields: Set<CardFieldKey>) => void;
toggleField: (field: CardFieldKey) => void;
resetFieldsToDefault: () => void;
```

**Implementação:**
```typescript
// Após outras inicializações de state
selectedFields: new Set(['name']), // default: só título

// Actions
setSelectedFields: (fields) => set({ selectedFields: fields }),

toggleField: (field) => set((state) => {
  const newFields = new Set(state.selectedFields);
  if (field === 'name') return state; // name sempre ativo
  if (newFields.has(field)) {
    newFields.delete(field);
  } else {
    newFields.add(field);
  }
  return { selectedFields: newFields };
}),

resetFieldsToDefault: () => set({ selectedFields: new Set(['name']) }),
```

### 3.2 Criar Componente `FieldSelector.tsx`

**Localização:** `/legal-workbench/frontend/src/components/trello/FieldSelector.tsx`

```typescript
import React from 'react';
import { Check } from 'lucide-react';
import { useTrelloStore } from '../../store/trelloStore';

const CARD_FIELDS = [
  { key: 'name' as const, label: 'Título', locked: true },
  { key: 'desc' as const, label: 'Descrição', locked: false },
  { key: 'labels' as const, label: 'Etiquetas', locked: false },
  { key: 'members' as const, label: 'Membros', locked: false },
  { key: 'due' as const, label: 'Data de Entrega', locked: false },
  { key: 'idList' as const, label: 'Lista', locked: false },
];

export const FieldSelector: React.FC = () => {
  const { selectedFields, toggleField } = useTrelloStore();

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-text-secondary uppercase tracking-wider">
        Campos Visíveis
      </h4>
      <div className="space-y-1">
        {CARD_FIELDS.map((field) => (
          <label
            key={field.key}
            className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer
              ${field.locked ? 'opacity-60 cursor-not-allowed' : 'hover:bg-bg-input'}
              ${selectedFields.has(field.key) ? 'text-text-primary' : 'text-text-secondary'}`}
          >
            <div className={`w-4 h-4 rounded border flex items-center justify-center
              ${selectedFields.has(field.key)
                ? 'bg-accent-indigo border-accent-indigo'
                : 'border-border-default'}`}
            >
              {selectedFields.has(field.key) && (
                <Check className="w-3 h-3 text-white" />
              )}
            </div>
            <input
              type="checkbox"
              checked={selectedFields.has(field.key)}
              onChange={() => !field.locked && toggleField(field.key)}
              disabled={field.locked}
              className="sr-only"
            />
            <span className="text-sm">{field.label}</span>
            {field.locked && (
              <span className="text-xxs text-text-muted">(obrigatório)</span>
            )}
          </label>
        ))}
      </div>
    </div>
  );
};
```

### 3.3 Modificar `ActionsPanel.tsx`

**Localização:** `/legal-workbench/frontend/src/components/trello/ActionsPanel.tsx`

**Importar e adicionar:**
```typescript
// Adicionar import
import { FieldSelector } from './FieldSelector';
import { Copy, ListChecks } from 'lucide-react';

// Adicionar função de copiar títulos (dentro do componente)
const handleCopyTitles = async () => {
  const titles = filteredCards.map(card => card.name).join('\n');
  await navigator.clipboard.writeText(titles);
  // Mostrar toast de sucesso
};

// No JSX, adicionar seção antes de "Export Options":
<div className="border-t border-border-default pt-4">
  <FieldSelector />
</div>

<div className="border-t border-border-default pt-4 mt-4">
  <button
    onClick={handleCopyTitles}
    disabled={filteredCards.length === 0}
    className="w-full flex items-center justify-center gap-2 px-3 py-2
      bg-bg-input hover:bg-bg-panel border border-border-default rounded
      text-sm text-text-primary disabled:opacity-50 disabled:cursor-not-allowed"
  >
    <ListChecks className="w-4 h-4" />
    Copiar Títulos ({filteredCards.length})
  </button>
</div>
```

### 3.4 Modificar `DataTable.tsx`

**Localização:** `/legal-workbench/frontend/src/components/trello/DataTable.tsx`

**Alterar colunas para serem condicionais:**
```typescript
// Adicionar ao destructuring do store
const { selectedFields, ... } = useTrelloStore();

// No header da tabela
<thead>
  <tr className="border-b border-border-default">
    <th>...</th> {/* checkbox sempre visível */}
    <th>CARD NAME</th> {/* sempre visível */}
    {selectedFields.has('idList') && <th>LIST</th>}
    {selectedFields.has('due') && <th>DUE DATE</th>}
    {selectedFields.has('labels') && <th>LABELS</th>}
    {selectedFields.has('members') && <th>MEMBERS</th>}
  </tr>
</thead>

// No body da tabela, mesma lógica condicional
```

### 3.5 Modificar `trelloApi.ts`

**Localização:** `/legal-workbench/frontend/src/services/trelloApi.ts`

**Alterar `exportData` para aceitar fields:**
```typescript
export const exportData = async (
  cards: Card[],
  format: 'json' | 'csv' | 'markdown' | 'text',
  filename: string,
  lists: TrelloList[] = [],
  labels: Label[] = [],
  members: Member[] = [],
  selectedFields?: Set<string> // NOVO PARÂMETRO
) => {
  const enrichedCards = enrichCardsForExport(cards, lists, labels, members);

  // Filtrar campos se selectedFields fornecido
  const filteredCards = selectedFields
    ? enrichedCards.map(card => filterCardFields(card, selectedFields))
    : enrichedCards;

  // ... resto da função usando filteredCards
};

// Função auxiliar
const filterCardFields = (card: EnrichedCard, fields: Set<string>) => {
  const filtered: Partial<EnrichedCard> = { id: card.id }; // id sempre incluído

  if (fields.has('name')) filtered.name = card.name;
  if (fields.has('desc')) filtered.desc = card.desc;
  if (fields.has('labels')) filtered.labelNames = card.labelNames;
  if (fields.has('members')) filtered.memberNames = card.memberNames;
  if (fields.has('due')) filtered.due = card.due;
  if (fields.has('idList')) filtered.listName = card.listName;

  return filtered;
};
```

---

## 4. Checklist de Implementação

- [ ] **4.1** Adicionar tipos em `trelloStore.ts`
- [ ] **4.2** Adicionar state `selectedFields` no store
- [ ] **4.3** Adicionar actions `toggleField`, `setSelectedFields`
- [ ] **4.4** Criar componente `FieldSelector.tsx`
- [ ] **4.5** Integrar `FieldSelector` em `ActionsPanel.tsx`
- [ ] **4.6** Adicionar botão "Copiar Títulos" em `ActionsPanel.tsx`
- [ ] **4.7** Modificar `DataTable.tsx` para colunas condicionais
- [ ] **4.8** Modificar `exportData` em `trelloApi.ts`
- [ ] **4.9** Testar export JSON com campos filtrados
- [ ] **4.10** Testar copy titles
- [ ] **4.11** Build e validação visual

---

## 5. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Breaking change no export JSON | Média | `selectedFields` é opcional, default = todos campos |
| Performance com muitos cards | Baixa | Filtro é O(n), memoizar se necessário |
| UX confusa se muitos campos ocultos | Baixa | Indicador visual de campos ocultos |

---

## 6. Critérios de Aceitação

1. ✅ Checkbox para cada campo (name locked)
2. ✅ Tabela reflete campos selecionados
3. ✅ Export JSON/CSV respeita seleção
4. ✅ Botão "Copiar Títulos" funciona
5. ✅ Compatibilidade retroativa (sem selectedFields = todos campos)
6. ✅ Build sem erros

---

## 7. Estimativa

| Fase | Esforço |
|------|---------|
| Store + Types | Pequeno |
| FieldSelector | Pequeno |
| ActionsPanel | Pequeno |
| DataTable | Médio |
| trelloApi | Pequeno |
| Testes | Médio |
| **Total** | ~2-3h |
