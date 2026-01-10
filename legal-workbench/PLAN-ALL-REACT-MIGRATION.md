# Plano de Migração All-React - Legal Workbench

**Data:** 2025-12-18
**Autor:** Technical Director (Claude)
**Aprovado por:** PGR

---

## Resumo Executivo

Migrar todo o frontend do Legal Workbench para React, eliminando o FastHTML Hub.

### Stack Atual
| Tecnologia | Versão |
|------------|--------|
| Vite | 5.0.8 |
| React | 18.2.0 |
| TypeScript | 5.2.2 |
| Zustand | 4.4.7 |
| Tailwind | 3.3.6 |
| **React Router** | **FALTANDO** |

### Estado Atual dos Módulos
| Módulo | Frontend Atual | Backend | Ação |
|--------|----------------|---------|------|
| Trello | React `/app` | `/api/trello` | Encapsular em rota |
| Doc Assembler | React (orphaned) | `/api/doc` | Ativar componentes |
| STJ | FastHTML | `/api/stj` | Migrar para React |
| Hub | FastHTML | N/A | Criar em React |

---

## FASE 0: Configuração Base (1h)

**Executor:** `frontend-developer` subagent

### Prompt:
```
# Setup React Router no Legal Workbench

## Contexto
O projeto está em `/home/cmr-auto/claude-work/repos/lex-vector/legal-workbench/frontend`.
Atualmente NÃO tem React Router. O Vite está configurado com `base: '/app/'`.

## Tarefas

### 1. Instalar React Router
cd /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench/frontend
npm install react-router-dom

### 2. Criar estrutura de rotas
Criar arquivo `src/routes.tsx`:

import { lazy, Suspense } from 'react';
import { createBrowserRouter, Outlet } from 'react-router-dom';
import { RootLayout } from '@/components/layout/RootLayout';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// Lazy loading dos módulos
const HubHome = lazy(() => import('@/pages/HubHome'));
const TrelloModule = lazy(() => import('@/pages/TrelloModule'));
const DocAssemblerModule = lazy(() => import('@/pages/DocAssemblerModule'));
const STJModule = lazy(() => import('@/pages/STJModule'));

// Wrapper para Suspense
const LazyPage = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<LoadingSpinner />}>{children}</Suspense>
);

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      { index: true, element: <LazyPage><HubHome /></LazyPage> },
      { path: 'trello', element: <LazyPage><TrelloModule /></LazyPage> },
      { path: 'doc-assembler', element: <LazyPage><DocAssemblerModule /></LazyPage> },
      { path: 'stj', element: <LazyPage><STJModule /></LazyPage> },
    ],
  },
], { basename: '/app' });

### 3. Atualizar main.tsx
Modificar para usar RouterProvider:

import { RouterProvider } from 'react-router-dom';
import { router } from './routes';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);

### 4. Criar RootLayout com Sidebar
Criar `src/components/layout/RootLayout.tsx`:
- Sidebar fixa à esquerda com navegação
- <Outlet /> para renderizar a página ativa
- Usar NavLink para highlighting de rota ativa

### 5. Criar LoadingSpinner
Componente simples de loading para Suspense fallback.

### 6. Criar páginas placeholder
- src/pages/HubHome.tsx
- src/pages/TrelloModule.tsx
- src/pages/DocAssemblerModule.tsx
- src/pages/STJModule.tsx

## Verificação
- npm run build deve passar sem erros
- Navegação entre rotas deve funcionar
```

---

## FASE 1: Ativar Trello no Router (30min)

**Executor:** `frontend-developer` subagent

### Prompt:
```
# Migrar Trello para o Router

## Contexto
O Trello já funciona. Precisamos encapsulá-lo em uma página roteável.

## Tarefas

### 1. Criar TrelloModule page
Criar `src/pages/TrelloModule.tsx`:

import { NavigationPanel } from '@/components/trello/NavigationPanel';
import { DataTable } from '@/components/trello/DataTable';
import { ActionsPanel } from '@/components/trello/ActionsPanel';
import { TrelloHeader } from '@/components/trello/TrelloHeader';
import { ToastContainer } from '@/components/ui/Toast';
import { useEffect } from 'react';
import useTrelloStore from '@/store/trelloStore';

export default function TrelloModule() {
  const { fetchInitialData } = useTrelloStore();

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  return (
    <div className="flex flex-col h-full">
      <TrelloHeader />
      <div className="flex flex-1 overflow-hidden">
        <NavigationPanel />
        <DataTable />
        <ActionsPanel />
      </div>
      <ToastContainer />
    </div>
  );
}

### 2. Extrair TrelloHeader
Mover o header do MainLayout.tsx atual para `src/components/trello/TrelloHeader.tsx`.

### 3. Testar
- Navegar para /app/trello
- Verificar que todas as funcionalidades do Trello funcionam
```

---

## FASE 2: Ativar Doc Assembler (1h)

**Executor:** `frontend-developer` subagent

### Prompt:
```
# Ativar Doc Assembler no Router

## Contexto
Os componentes existem mas estão orphaned. Conectar ao router.

Componentes disponíveis:
- src/components/document/DocumentViewer.tsx
- src/components/document/AnnotationList.tsx
- src/components/upload/DropZone.tsx
- src/components/templates/TemplateList.tsx
- src/store/documentStore.ts

## Tarefas

### 1. Criar DocAssemblerModule page
Criar `src/pages/DocAssemblerModule.tsx`:

import { DropZone } from '@/components/upload/DropZone';
import { DocumentViewer } from '@/components/document/DocumentViewer';
import { AnnotationList } from '@/components/document/AnnotationList';
import { TemplateList } from '@/components/templates/TemplateList';
import useDocumentStore from '@/store/documentStore';
import { useEffect } from 'react';

export default function DocAssemblerModule() {
  const { document, fetchTemplates } = useDocumentStore();

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  return (
    <div className="flex flex-col h-full">
      <header className="h-12 border-b border-border-default flex items-center px-4">
        <h1 className="text-lg font-bold text-accent-violet">Doc Assembler</h1>
      </header>
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-72 border-r border-border-default p-4">
          <DropZone />
          <TemplateList />
        </aside>
        <main className="flex-1">
          {document ? <DocumentViewer /> : <EmptyState />}
        </main>
        <aside className="w-80 border-l border-border-default">
          <AnnotationList />
        </aside>
      </div>
    </div>
  );
}

### 2. Testar E2E com qa_commander
- Upload de arquivo
- Visualização do documento
- Criação de anotações
```

---

## FASE 3: Migrar STJ do FastHTML (2-3h)

**Executor:** `frontend-developer` subagent

### Prompt:
```
# Migrar STJ de FastHTML para React

## Contexto
O STJ está em FastHTML (hub/modules/stj/).
O backend já existe em /api/stj.

## Análise Prévia
Ler os arquivos FastHTML para entender a UI:
- hub/modules/stj/routes.py

## Tarefas

### 1. Criar STJ store
Criar `src/store/stjStore.ts`:
- Estado: query, results, loading, error, filters
- Actions: search, setFilters, clearResults

### 2. Criar STJ API service
Criar `src/services/stjApi.ts`:
- GET /api/stj/search
- GET /api/stj/document/:id

### 3. Criar componentes
- src/components/stj/SearchForm.tsx
- src/components/stj/ResultsList.tsx
- src/components/stj/ResultCard.tsx
- src/components/stj/Filters.tsx

### 4. Criar STJModule page
Criar `src/pages/STJModule.tsx`:
- Layout: sidebar com filtros, main com resultados
- Tema "observatory purple" (accent-violet)

### 5. Testar com qa_commander
```

---

## FASE 4: Hub Home Page (1h)

**Executor:** `frontend-developer` subagent

### Prompt:
```
# Criar Hub Home Page

## Tarefas

### 1. Criar HubHome page
Criar `src/pages/HubHome.tsx`:

import { Link } from 'react-router-dom';

const modules = [
  { id: 'trello', name: 'Trello Command Center', icon: '📋', color: 'accent-indigo' },
  { id: 'doc-assembler', name: 'Doc Assembler', icon: '📄', color: 'accent-violet' },
  { id: 'stj', name: 'STJ Dados Abertos', icon: '🔭', color: 'status-emerald' },
];

export default function HubHome() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-8">Legal Workbench</h1>
      <div className="grid grid-cols-3 gap-6">
        {modules.map(mod => (
          <Link to={`/${mod.id}`} key={mod.id}>
            <ModuleCard {...mod} />
          </Link>
        ))}
      </div>
    </div>
  );
}

### 2. Implementar RootLayout sidebar
- Logo "Legal Workbench"
- NavLink para cada módulo
- Settings no footer
```

---

## FASE 5: Cleanup e Deploy (1h)

**Executor:** Technical Director + `test-writer-fixer`

### Prompt:
```
# Cleanup e Validação Final

## Tarefas

### 1. Remover FastHTML
- Deletar hub/ directory
- Remover frontend-hub do docker-compose

### 2. Atualizar Traefik
frontend-react serve em / (priority=1)

### 3. Testes E2E
qa_commander em cada módulo:
- Hub Home
- Trello
- Doc Assembler
- STJ

### 4. Commit
git commit -m "feat(legal-workbench): migrate to All-React architecture"
```

---

## Cronograma

| Fase | Tempo | Executor |
|------|-------|----------|
| 0. Setup Router | 1h | frontend-developer |
| 1. Ativar Trello | 30min | frontend-developer |
| 2. Ativar Doc Assembler | 1h | frontend-developer |
| 3. Migrar STJ | 2-3h | frontend-developer |
| 4. Hub Home | 1h | frontend-developer |
| 5. Cleanup | 1h | test-writer-fixer |

**Total:** 6-8 horas

---

## Notas

### Edge-cases conhecidos (qa_commander)
- Export com undefined labels/members arrays
- Large datasets export performance
- Concurrent card selection scenarios

### Commits relacionados
- e8969ce: feat(trello+adk): redesign UI
- 81d99b0: feat(doc-assembler): React frontend
- 27917cf: feat(qa_commander): E2E testing agent
