# PLAN: Doc Assembler Frontend (React)

**Data:** 2025-12-17
**Prioridade:** ALTA (uso imediato necessário)
**Stack:** React + TypeScript + Vite + Dark Mode

---

## 1. Visão Geral

### Objetivo
Criar um frontend React para o Doc Assembler que permita:
1. **Upload de DOCX** - Carregar petição existente
2. **Visualização de texto** - Renderizar conteúdo do DOCX
3. **Seleção e marcação** - Selecionar trechos e transformá-los em campos Jinja
4. **Detecção automática** - Identificar padrões (CPF, nome, data) automaticamente
5. **Salvar template** - Gerar DOCX com placeholders `{{ campo }}`
6. **Gerenciar templates** - Listar, duplicar, reutilizar templates salvos

### Referências Visuais
- **VS Code** - Layout de painéis, dark theme
- **Obsidian** - Editor de texto, sidebar
- **GitHub** - Paleta de cores dark, componentes

---

## 2. Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                         TRAEFIK                                  │
│                      (reverse-proxy)                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   /          │   │  /api/doc    │   │  /api/stj    │
│  frontend    │   │ doc-assembler│   │   stj-api    │
│   (React)    │   │  (FastAPI)   │   │              │
│  Port 3000   │   │  Port 8002   │   │  Port 8000   │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │
        │                   │
        └───────────────────┘
              CORS/API calls
```

### Fluxo de Dados

```
DOCX Upload → Backend extrai texto → Frontend renderiza
                                            ↓
                                    Usuário seleciona trechos
                                            ↓
                                    Cria campos Jinja
                                            ↓
                            Backend gera DOCX com {{ placeholders }}
                                            ↓
                                    Salva + Download
```

---

## 3. Backend - Novos Endpoints

### 3.1 Template Builder API

Adicionar ao `doc-assembler/api/main.py`:

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/builder/upload` | POST | Upload DOCX, retorna texto extraído + metadados |
| `/api/v1/builder/patterns` | POST | Detecta padrões automáticos no texto |
| `/api/v1/builder/save` | POST | Salva template com campos marcados |
| `/api/v1/builder/templates` | GET | Lista templates salvos (builder) |
| `/api/v1/builder/templates/{id}` | GET | Detalhes de um template builder |
| `/api/v1/builder/templates/{id}/duplicate` | POST | Duplica template existente |

### 3.2 Modelos Pydantic

```python
class UploadResponse(BaseModel):
    """Resposta do upload de DOCX."""
    document_id: str  # UUID para referência
    text_content: str  # Texto extraído
    paragraphs: list[str]  # Parágrafos separados
    metadata: dict  # Info do documento (páginas, autor, etc)

class PatternMatch(BaseModel):
    """Padrão detectado no texto."""
    pattern_type: str  # "cpf", "name", "date", "currency", etc
    start: int  # Posição inicial no texto
    end: int  # Posição final
    value: str  # Valor encontrado
    suggested_field: str  # Nome sugerido para o campo

class PatternsResponse(BaseModel):
    """Resposta da detecção de padrões."""
    matches: list[PatternMatch]
    pattern_types_found: list[str]

class FieldAnnotation(BaseModel):
    """Anotação de campo feita pelo usuário."""
    field_name: str  # Nome do campo Jinja (ex: "nome_autor")
    start: int  # Posição inicial no texto
    end: int  # Posição final
    original_text: str  # Texto original selecionado

class SaveTemplateRequest(BaseModel):
    """Request para salvar template."""
    document_id: str  # Referência ao upload
    template_name: str  # Nome do template
    annotations: list[FieldAnnotation]  # Campos marcados
    description: str = ""  # Descrição opcional

class TemplateBuilderInfo(BaseModel):
    """Info de template salvo."""
    id: str
    name: str
    description: str
    field_count: int
    fields: list[str]  # Nomes dos campos
    created_at: str
    file_path: str
```

---

## 4. Frontend - Estrutura

### 4.1 Estrutura de Diretórios

```
legal-workbench/frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css          # Tailwind/CSS global
│   ├── vite-env.d.ts
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── MainLayout.tsx
│   │   │
│   │   ├── document/
│   │   │   ├── DocumentViewer.tsx       # Renderiza texto do DOCX
│   │   │   ├── TextSelection.tsx        # Lógica de seleção
│   │   │   ├── FieldAnnotation.tsx      # Marca campo selecionado
│   │   │   └── AnnotationList.tsx       # Lista de anotações
│   │   │
│   │   ├── upload/
│   │   │   ├── DropZone.tsx             # Drag & drop upload
│   │   │   └── UploadProgress.tsx
│   │   │
│   │   ├── templates/
│   │   │   ├── TemplateList.tsx         # Lista templates salvos
│   │   │   ├── TemplateCard.tsx
│   │   │   └── TemplatePreview.tsx
│   │   │
│   │   └── ui/                          # Componentes base
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Modal.tsx
│   │       └── Toast.tsx
│   │
│   ├── hooks/
│   │   ├── useTextSelection.ts          # Hook para window.getSelection()
│   │   ├── useAnnotations.ts            # Gerencia lista de anotações
│   │   └── useDocumentUpload.ts         # Upload + estado
│   │
│   ├── services/
│   │   └── api.ts                       # Chamadas ao backend
│   │
│   ├── store/
│   │   └── documentStore.ts             # Zustand store
│   │
│   ├── types/
│   │   └── index.ts                     # TypeScript interfaces
│   │
│   └── styles/
│       └── theme.ts                     # Dark mode config
│
└── Dockerfile
```

### 4.2 Componentes Principais

#### DocumentViewer.tsx
- Renderiza texto do DOCX em parágrafos
- Suporta seleção de texto (window.getSelection)
- Destaca campos já anotados
- Mostra padrões detectados automaticamente

#### TextSelection.tsx
- Captura seleção do usuário
- Mostra popup para nomear o campo
- Valida nome (snake_case, sem duplicatas)

#### AnnotationList.tsx
- Lista lateral de campos marcados
- Permite editar/remover anotações
- Mostra preview do template Jinja

#### TemplateList.tsx
- Grid de templates salvos
- Busca/filtro
- Ações: duplicar, editar, usar

### 4.3 Estado (Zustand)

```typescript
interface DocumentState {
  // Upload
  documentId: string | null;
  textContent: string;
  paragraphs: string[];
  isUploading: boolean;

  // Annotations
  annotations: FieldAnnotation[];
  selectedText: string | null;
  selectionRange: { start: number; end: number } | null;

  // Patterns
  detectedPatterns: PatternMatch[];
  showPatterns: boolean;

  // Actions
  uploadDocument: (file: File) => Promise<void>;
  addAnnotation: (annotation: FieldAnnotation) => void;
  removeAnnotation: (fieldName: string) => void;
  updateAnnotation: (fieldName: string, updates: Partial<FieldAnnotation>) => void;
  applyPattern: (pattern: PatternMatch, fieldName: string) => void;
  saveTemplate: (name: string, description?: string) => Promise<void>;
  clearDocument: () => void;
}
```

---

## 5. UX/UI - Dark Mode

### 5.1 Paleta de Cores (GitHub Dark)

```css
:root {
  /* Backgrounds */
  --bg-primary: #0d1117;       /* Fundo principal */
  --bg-secondary: #161b22;     /* Painéis, cards */
  --bg-tertiary: #21262d;      /* Hover, selected */

  /* Text */
  --text-primary: #c9d1d9;     /* Texto principal */
  --text-secondary: #8b949e;   /* Texto secundário */
  --text-muted: #6e7681;       /* Texto desabilitado */

  /* Accent */
  --accent-primary: #58a6ff;   /* Links, botões */
  --accent-success: #3fb950;   /* Sucesso */
  --accent-warning: #d29922;   /* Aviso */
  --accent-danger: #f85149;    /* Erro */

  /* Borders */
  --border-default: #30363d;
  --border-muted: #21262d;

  /* Highlight (seleção) */
  --highlight-bg: #388bfd33;   /* Background de seleção */
  --highlight-border: #58a6ff;
}
```

### 5.2 Layout Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo] Doc Assembler - Template Builder          [Dark/Light]  │
├─────────────────────────────────────────────────────────────────┤
│         │                                        │              │
│ SIDEBAR │          DOCUMENT VIEWER               │  ANNOTATIONS │
│         │                                        │              │
│ Upload  │  [Texto do documento aqui]             │  Campo 1     │
│ ──────  │  O autor, {{nome_autor}}, residente    │  nome_autor  │
│         │  em {{endereco}}, vem...               │  ──────────  │
│ Templates│                                       │  Campo 2     │
│ ──────  │  [Seleção: highlight azul]             │  endereco    │
│ - T1    │                                        │  ──────────  │
│ - T2    │                                        │              │
│         │                                        │  [+ Padrões] │
│ Padrões │                                        │              │
│ ──────  │                                        │ ─────────────│
│ [x] CPF │                                        │ [Salvar]     │
│ [x] Data│                                        │ [Download]   │
│         │                                        │              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Integração com Traefik

### 6.1 docker-compose.yml (adição)

```yaml
# Adicionar ao docker-compose.yml existente
frontend:
  build: ./frontend
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.frontend.rule=PathPrefix(`/app`)"
    - "traefik.http.routers.frontend.entrypoints=web"
    - "traefik.http.routers.frontend.priority=5"
    - "traefik.http.middlewares.frontend-strip.stripprefix.prefixes=/app"
    - "traefik.http.routers.frontend.middlewares=frontend-strip"
    - "traefik.http.services.frontend.loadbalancer.server.port=3000"
  networks:
    - legal-network
```

### 6.2 Acessos

| URL | Serviço |
|-----|---------|
| `http://localhost/app` | Frontend React |
| `http://localhost/api/doc` | Doc Assembler API |
| `http://localhost:8080` | Traefik Dashboard |

---

## 7. Fases de Implementação

### Fase 1: Infraestrutura (1-2h)
- [ ] Criar estrutura `frontend/` com Vite + React + TS
- [ ] Configurar Tailwind CSS com dark mode
- [ ] Criar Dockerfile
- [ ] Adicionar ao docker-compose.yml
- [ ] Testar build e roteamento via Traefik

### Fase 2: Backend Endpoints (2-3h)
- [ ] Implementar `/api/v1/builder/upload`
- [ ] Implementar `/api/v1/builder/patterns`
- [ ] Implementar `/api/v1/builder/save`
- [ ] Implementar `/api/v1/builder/templates`
- [ ] Testar endpoints com curl/Postman

### Fase 3: Upload e Visualização (2-3h)
- [ ] Componente DropZone para upload
- [ ] Integração com API de upload
- [ ] DocumentViewer para renderizar texto
- [ ] Zustand store básico

### Fase 4: Seleção e Anotação (3-4h) [CORE]
- [ ] Hook useTextSelection
- [ ] Componente TextSelection (popup)
- [ ] Destaque visual de seleções
- [ ] AnnotationList com edição
- [ ] Validação de nomes de campos

### Fase 5: Detecção Automática (1-2h)
- [ ] Integração com API de padrões
- [ ] UI para aceitar/rejeitar sugestões
- [ ] Toggle de tipos de padrões

### Fase 6: Salvar e Gerenciar (2h)
- [ ] Modal de salvar template
- [ ] Lista de templates salvos
- [ ] Duplicar template
- [ ] Download de template

### Fase 7: Polish e Testes (2h)
- [ ] Ajustes de UX/responsividade
- [ ] Tratamento de erros
- [ ] Loading states
- [ ] Testes básicos

**Estimativa Total: 13-18 horas de desenvolvimento**

---

## 8. Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Seleção de texto cross-browser | Alto | Usar biblioteca (rangy ou similar) |
| Preservar formatação DOCX | Médio | Trabalhar com texto plano inicialmente |
| Performance com docs grandes | Médio | Virtualização de parágrafos |
| Conflito de anotações sobrepostas | Alto | Validação no frontend + backend |

---

## 9. Dependências React

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^7.0.2",
    "zustand": "^5.0.2",
    "axios": "^1.7.9",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.14",
    "@types/react-dom": "^18.3.2",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "~5.6.2",
    "vite": "^6.0.3",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20"
  }
}
```

---

## 10. Checklist de Aprovação

Antes de iniciar implementação, confirmar:

- [ ] Estrutura de diretórios aprovada?
- [ ] Endpoints de backend aprovados?
- [ ] Paleta de cores dark mode aprovada?
- [ ] Layout aprovado?
- [ ] Fases de implementação fazem sentido?
- [ ] Prioridade de features correta?

---

**Próximo Passo:** Após aprovação deste plano, acionar o agente ADK `legal-tech-frontend-specialist` para implementação.
