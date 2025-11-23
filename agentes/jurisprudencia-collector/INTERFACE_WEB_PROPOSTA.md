# Proposta: Interface Web de Busca de Jurisprudência

**Data:** 2025-11-20
**Status:** 📋 Proposta (não implementado)
**Autor:** Claude Code (Sonnet 4.5)

## 🎯 Objetivo

Criar uma aplicação web que permita **buscar, visualizar e analisar jurisprudência** da base de dados local construída pelo sistema de coleta DJEN.

---

## 📊 Visão Geral

### O que é uma Interface Web de Busca?

Uma interface web de busca é uma aplicação que roda no navegador (browser) e permite que usuários:

1. **Busquem** publicações jurídicas usando texto livre ou filtros
2. **Visualizem** resultados de forma organizada e legível
3. **Filtrem** por tribunal, data, tipo de publicação, etc
4. **Exportem** resultados para PDF, Word ou planilhas
5. **Analisem** tendências e estatísticas

### Exemplos Comparáveis

Similar a:
- **Google Acadêmico** - busca de artigos científicos
- **Jusbrasil** - busca de jurisprudência brasileira
- **JurisWay** - pesquisa de decisões judiciais
- **LexML** - portal de legislação do Senado

---

## 🏗️ Arquitetura Proposta

### Stack Tecnológica

#### **Backend (API REST)**
- **Linguagem:** Python 3.12
- **Framework:** FastAPI (moderno, rápido, documentação automática)
- **Banco:** SQLite (já existente no sistema)
- **Busca semântica:** Sistema RAG já implementado (`src/rag/`)
- **Servidor:** Uvicorn (ASGI server)

#### **Frontend (Interface do Usuário)**
- **Framework:** React + TypeScript (moderno, componentizado)
- **UI Library:** shadcn/ui + Tailwind CSS (design system profissional)
- **Estado:** TanStack Query (gerenciamento de cache e requisições)
- **Build:** Vite (rápido, moderno)

#### **Deployment**
- **Desenvolvimento:** localhost (127.0.0.1:3000 frontend, :8000 backend)
- **Produção:** Docker Compose (frontend + backend + nginx)
- **Alternativa:** Render.com / Railway.app (hosting gratuito)

---

## 📐 Estrutura de Diretórios

```
agentes/jurisprudencia-collector/
├── backend/                    # ← NOVO: API REST
│   ├── main.py                 # FastAPI app
│   ├── api/
│   │   ├── routes/
│   │   │   ├── search.py       # Endpoint de busca
│   │   │   ├── tribunais.py    # Filtros por tribunal
│   │   │   ├── stats.py        # Estatísticas
│   │   │   └── export.py       # Exportação de dados
│   │   ├── models/
│   │   │   ├── publicacao.py   # Pydantic models
│   │   │   └── filters.py      # Filtros de busca
│   │   └── dependencies.py     # Conexão DB, auth, etc
│   ├── services/
│   │   ├── search_service.py   # Lógica de busca (RAG + FTS)
│   │   ├── stats_service.py    # Estatísticas
│   │   └── export_service.py   # PDF/DOCX generation
│   └── tests/
│       └── test_api.py         # Testes automatizados
│
├── frontend/                   # ← NOVO: Interface React
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.tsx       # Barra de busca
│   │   │   ├── ResultCard.tsx      # Card de resultado
│   │   │   ├── Filters.tsx         # Sidebar de filtros
│   │   │   ├── ExportButton.tsx    # Botão de exportação
│   │   │   └── StatsChart.tsx      # Gráficos de estatísticas
│   │   ├── pages/
│   │   │   ├── Home.tsx            # Página inicial
│   │   │   ├── Search.tsx          # Página de busca
│   │   │   ├── Details.tsx         # Detalhes da publicação
│   │   │   └── Stats.tsx           # Dashboard de estatísticas
│   │   ├── hooks/
│   │   │   ├── useSearch.ts        # Hook de busca
│   │   │   └── useFilters.ts       # Hook de filtros
│   │   ├── lib/
│   │   │   └── api.ts              # Cliente da API
│   │   └── App.tsx                 # App principal
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml          # ← NOVO: Orquestração Docker
├── nginx.conf                  # ← NOVO: Proxy reverso
│
└── [arquivos existentes]
```

---

## 🔍 Funcionalidades

### 1. **Busca Inteligente**

#### **Busca Semântica (RAG)**
```
Usuário digita: "responsabilidade civil por dano moral"

Sistema:
1. Gera embedding do texto com modelo BERT português
2. Busca no índice vetorial (src/rag/)
3. Retorna publicações semanticamente similares
4. Score de relevância: 0-100%
```

**Exemplo de resultado:**
```
1. Acórdão STJ - AgInt no REsp 2.154.789 (Relevância: 94%)
   "AGRAVO INTERNO. RESPONSABILIDADE CIVIL. DANO MORAL..."
   📍 STJ | 📅 2025-11-15 | ⚖️ Acórdão

2. Acórdão TJSP - Apelação 1002345-67.2024 (Relevância: 89%)
   "APELAÇÃO CÍVEL. INDENIZAÇÃO POR DANOS MORAIS..."
   📍 TJSP | 📅 2025-11-10 | ⚖️ Acórdão
```

#### **Busca Textual (FTS5)**
```sql
-- Busca full-text tradicional
SELECT * FROM publicacoes_fts
WHERE publicacoes_fts MATCH 'dano AND moral'
ORDER BY rank
LIMIT 20
```

#### **Busca Híbrida (Combinada)**
- 70% weight para busca semântica (RAG)
- 30% weight para busca textual (FTS5)
- Melhor de ambos os mundos

### 2. **Filtros Avançados**

#### **Sidebar de Filtros**
```
┌─────────────────────────┐
│ 🔍 Filtros              │
├─────────────────────────┤
│ 📅 Data de Publicação   │
│  ▸ Último mês           │
│  ▸ Último ano           │
│  ▸ Personalizado        │
│    [___] até [___]      │
├─────────────────────────┤
│ ⚖️ Tribunal             │
│  ☑ STJ (234)            │
│  ☑ STF (89)             │
│  ☑ TJSP (1,245)         │
│  ☐ TST (156)            │
│  + Ver mais             │
├─────────────────────────┤
│ 📋 Tipo de Publicação   │
│  ☑ Acórdão (567)        │
│  ☑ Decisão (890)        │
│  ☐ Sentença (234)       │
│  ☐ Intimação (1,456)    │
├─────────────────────────┤
│ 👤 Relator              │
│  [Digite para buscar__] │
├─────────────────────────┤
│ 🏛️ Instância            │
│  ☑ Superior (345)       │
│  ☑ 2ª Instância (789)   │
│  ☐ 1ª Instância (234)   │
└─────────────────────────┘
```

### 3. **Visualização de Resultados**

#### **Card de Resultado**
```
┌──────────────────────────────────────────────────────────┐
│ 📄 Acórdão - STJ                              🔖 Favorito │
│ AgInt no REsp 2.154.789/SP                                │
├──────────────────────────────────────────────────────────┤
│                                                            │
│ EMENTA: AGRAVO INTERNO NO RECURSO ESPECIAL.               │
│ RESPONSABILIDADE CIVIL. DANO MORAL. QUANTUM              │
│ INDENIZATÓRIO. REVISÃO. IMPOSSIBILIDADE. SÚMULA 7/STJ.   │
│ [...]                                                      │
│                                                            │
├──────────────────────────────────────────────────────────┤
│ 📍 Tribunal: STJ - Superior                                │
│ 📅 Publicação: 15/11/2025                                 │
│ 👤 Relator: Min. Nancy Andrighi                           │
│ 💯 Relevância: 94%                                        │
├──────────────────────────────────────────────────────────┤
│ [Ver completo] [Exportar] [Compartilhar] [Citar]        │
└──────────────────────────────────────────────────────────┘
```

### 4. **Detalhes da Publicação**

Ao clicar em "Ver completo":

```
┌──────────────────────────────────────────────────────────┐
│ ← Voltar    AgInt no REsp 2.154.789/SP            ⋮ Ações │
├──────────────────────────────────────────────────────────┤
│ 📋 Metadados                                               │
│                                                            │
│  Tribunal:        Superior Tribunal de Justiça (STJ)      │
│  Processo:        2154789-67.2025.8.26.0000               │
│  Classe:          Agravo Interno no Recurso Especial      │
│  Órgão Julgador:  Terceira Turma                          │
│  Relator:         Ministra Nancy Andrighi                 │
│  Data Julgamento: 10/11/2025                              │
│  Data Publicação: 15/11/2025                              │
│  Fonte:           DJEN                                     │
│                                                            │
├──────────────────────────────────────────────────────────┤
│ 📄 Ementa                                                  │
│                                                            │
│  AGRAVO INTERNO NO RECURSO ESPECIAL. RESPONSABILIDADE     │
│  CIVIL. DANO MORAL. QUANTUM INDENIZATÓRIO. REVISÃO.       │
│  IMPOSSIBILIDADE. SÚMULA 7/STJ. AGRAVO NÃO PROVIDO.       │
│                                                            │
│  1. A revisão do quantum fixado a título de dano moral    │
│  demanda necessariamente o reexame de provas, o que é     │
│  vedado em recurso especial, nos termos da Súmula 7/STJ.  │
│                                                            │
│  2. Agravo interno não provido.                           │
│                                                            │
├──────────────────────────────────────────────────────────┤
│ 📄 Texto Completo                                          │
│                                                            │
│  [Conteúdo HTML renderizado formatado]                    │
│                                                            │
├──────────────────────────────────────────────────────────┤
│ 🔗 Publicações Relacionadas                                │
│                                                            │
│  • REsp 1.844.000/SP - Dano moral, quantum (91%)          │
│  • AgRg no AREsp 2.100.345/RJ - Revisão... (89%)          │
│  • REsp 1.923.456/MG - Súmula 7/STJ (87%)                 │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

### 5. **Dashboard de Estatísticas**

#### **Visão Geral**
```
┌──────────────────────────────────────────────────────────┐
│ 📊 Dashboard - Estatísticas da Base                       │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  💾 Total de Publicações: 125,478                         │
│  📅 Última atualização: 20/11/2025 08:15                  │
│  ⏱️ Downloads hoje: 15 tribunais, 2.345 publicações       │
│                                                            │
├──────────────────────────────────────────────────────────┤
│ 📈 Publicações por Tribunal                                │
│                                                            │
│  STJ  ████████████████████ 34,567 (28%)                   │
│  TJSP ██████████████ 28,901 (23%)                         │
│  STF  ██████████ 15,234 (12%)                             │
│  TST  ████████ 12,456 (10%)                               │
│  TJRJ ██████ 8,901 (7%)                                   │
│  ...                                                       │
│                                                            │
├──────────────────────────────────────────────────────────┤
│ 📊 Tipos de Publicação                                     │
│                                                            │
│   🟢 Acórdão: 45,678 (36%)                                │
│   🔵 Decisão: 38,901 (31%)                                │
│   🟡 Intimação: 28,456 (23%)                              │
│   🟣 Sentença: 12,443 (10%)                               │
│                                                            │
├──────────────────────────────────────────────────────────┤
│ 📅 Publicações nos Últimos 30 Dias                        │
│                                                            │
│   [Gráfico de linha mostrando tendência]                  │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

### 6. **Exportação**

#### **Formatos Disponíveis**
- **PDF** - Documento formatado para impressão
- **DOCX** - Word (edição)
- **CSV** - Planilha (análise quantitativa)
- **JSON** - Dados estruturados (integração)

#### **Exemplo de Exportação**
```
Usuário:
1. Faz busca: "direito civil contratos"
2. Seleciona 5 resultados
3. Clica em "Exportar" → "PDF"

Sistema gera:
┌─────────────────────────────────┐
│ Relatório de Jurisprudência     │
│ Data: 20/11/2025                │
│ Busca: direito civil contratos  │
│ Resultados: 5 publicações       │
├─────────────────────────────────┤
│ 1. Acórdão STJ - REsp 1.234.567 │
│    [Ementa completa]             │
│    [Metadados]                   │
│                                  │
│ 2. Acórdão TJSP - Ap 2.345.678  │
│    [Ementa completa]             │
│    [Metadados]                   │
│ ...                              │
└─────────────────────────────────┘
```

---

## 🎨 Wireframes (Mockups)

### Página Inicial (Home)
```
┌────────────────────────────────────────────────────────────┐
│ JurisSearch - Base Local de Jurisprudência    [⚙️] [👤]    │
├────────────────────────────────────────────────────────────┤
│                                                              │
│                  🔍 Busca Inteligente                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Buscar jurisprudência...                    🔍     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  💡 Exemplos de busca:                                      │
│  • "responsabilidade civil dano moral"                      │
│  • "contrato de trabalho rescisão indireta"                 │
│  • "prisão preventiva fundamento"                           │
│                                                              │
├────────────────────────────────────────────────────────────┤
│ 📊 Estatísticas Rápidas                                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 125,478      │  │ 15           │  │ 2,345        │     │
│  │ Publicações  │  │ Tribunais    │  │ Hoje         │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
├────────────────────────────────────────────────────────────┤
│ 🔥 Tópicos em Alta                                          │
│                                                              │
│  1. Dano moral - indenização (234 publicações)              │
│  2. Prisão preventiva (189 publicações)                     │
│  3. Rescisão contratual (156 publicações)                   │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

### Página de Busca (Search)
```
┌────────────────────────────────────────────────────────────┐
│ ← Home  "responsabilidade civil"    [⚙️ Filtros] [👤]      │
├─────────────┬──────────────────────────────────────────────┤
│ 🔍 Filtros  │ 📋 Resultados (1,234)                         │
│             │                                                │
│ 📅 Data     │ ┌────────────────────────────────────────┐   │
│  ○ Último   │ │ 📄 Acórdão STJ - REsp 2.154.789      │   │
│    mês      │ │ RESPONSABILIDADE CIVIL. DANO MORAL.  │   │
│  ● Último   │ │ QUANTUM INDENIZATÓRIO...              │   │
│    ano      │ │ 📍 STJ | 📅 15/11/25 | 💯 94%        │   │
│  ○ Tudo     │ │ [Ver] [Exportar] [+]                  │   │
│             │ └────────────────────────────────────────┘   │
│ ⚖️ Tribunal │                                                │
│  ☑ STJ      │ ┌────────────────────────────────────────┐   │
│  ☑ STF      │ │ 📄 Acórdão TJSP - Ap 1.002.345       │   │
│  ☐ TJSP     │ │ APELAÇÃO CÍVEL. INDENIZAÇÃO POR...    │   │
│  ☐ TST      │ │ 📍 TJSP | 📅 10/11/25 | 💯 89%       │   │
│             │ │ [Ver] [Exportar] [+]                  │   │
│ 📋 Tipo     │ └────────────────────────────────────────┘   │
│  ☑ Acórdão  │                                                │
│  ☑ Decisão  │ ┌────────────────────────────────────────┐   │
│  ☐ Intimação│ │ ...                                    │   │
│             │ └────────────────────────────────────────┘   │
│             │                                                │
│ [Limpar]    │ [1] 2 3 4 ... 50 [→]                          │
└─────────────┴──────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### **Busca**
```bash
# Busca simples
GET /api/search?q=responsabilidade+civil&limit=20&page=1

# Busca com filtros
POST /api/search
{
  "query": "responsabilidade civil",
  "filters": {
    "tribunais": ["STJ", "STF"],
    "tipos": ["Acórdão", "Decisão"],
    "data_inicio": "2025-01-01",
    "data_fim": "2025-11-20"
  },
  "limit": 20,
  "page": 1
}

# Resposta
{
  "total": 1234,
  "page": 1,
  "limit": 20,
  "results": [
    {
      "id": "17a7fcf7-d718-47bf-b4fc-93e0063f1bcd",
      "tribunal": "STJ",
      "tipo_publicacao": "Acórdão",
      "numero_processo": "2154789-67.2025.8.26.0000",
      "ementa": "AGRAVO INTERNO NO RECURSO ESPECIAL...",
      "data_publicacao": "2025-11-15",
      "relator": "Min. Nancy Andrighi",
      "relevancia_score": 94.5
    },
    ...
  ]
}
```

### **Detalhes**
```bash
GET /api/publicacao/{id}

# Resposta
{
  "id": "17a7fcf7-d718-47bf-b4fc-93e0063f1bcd",
  "tribunal": "STJ",
  "numero_processo": "2154789-67.2025.8.26.0000",
  "tipo_publicacao": "Acórdão",
  "texto_html": "<html>...",
  "texto_limpo": "AGRAVO INTERNO...",
  "ementa": "AGRAVO INTERNO NO RECURSO ESPECIAL...",
  "data_publicacao": "2025-11-15",
  "relator": "Min. Nancy Andrighi",
  "orgao_julgador": "Terceira Turma",
  "relacionadas": [
    {
      "id": "...",
      "titulo": "REsp 1.844.000/SP",
      "relevancia": 91.2
    }
  ]
}
```

### **Estatísticas**
```bash
GET /api/stats

# Resposta
{
  "total_publicacoes": 125478,
  "ultima_atualizacao": "2025-11-20T08:15:00Z",
  "por_tribunal": {
    "STJ": 34567,
    "TJSP": 28901,
    "STF": 15234,
    ...
  },
  "por_tipo": {
    "Acórdão": 45678,
    "Decisão": 38901,
    "Intimação": 28456,
    "Sentença": 12443
  },
  "por_mes": {
    "2025-11": 12345,
    "2025-10": 11234,
    ...
  }
}
```

### **Exportação**
```bash
POST /api/export/pdf
{
  "publicacao_ids": ["id1", "id2", "id3"],
  "formato": "pdf",
  "opcoes": {
    "incluir_texto_completo": true,
    "incluir_metadados": true
  }
}

# Resposta
{
  "download_url": "/downloads/relatorio_20251120_143022.pdf",
  "expires_at": "2025-11-20T18:30:22Z"
}
```

---

## 🚀 Implementação

### Fase 1: MVP (Minimum Viable Product) - 2-3 semanas

**Backend:**
- ✅ API REST com FastAPI
- ✅ Endpoint de busca simples (FTS5 apenas)
- ✅ Endpoint de detalhes de publicação
- ✅ Endpoint de estatísticas básicas

**Frontend:**
- ✅ Página de busca simples
- ✅ Lista de resultados
- ✅ Detalhes de publicação
- ✅ Filtros básicos (tribunal, data, tipo)

**Deployment:**
- ✅ Docker Compose (backend + frontend + nginx)
- ✅ Localhost only

### Fase 2: Busca Inteligente - 1-2 semanas

**Backend:**
- ✅ Integração com RAG (busca semântica)
- ✅ Busca híbrida (RAG + FTS5)
- ✅ Publicações relacionadas

**Frontend:**
- ✅ Score de relevância na UI
- ✅ Highlight de termos buscados
- ✅ Sugestões de busca

### Fase 3: Features Avançadas - 2-3 semanas

**Backend:**
- ✅ Exportação (PDF, DOCX, CSV)
- ✅ API de estatísticas avançadas

**Frontend:**
- ✅ Dashboard completo
- ✅ Gráficos interativos
- ✅ Filtros avançados
- ✅ Favoritos / Listas

### Fase 4: Produção - 1 semana

**DevOps:**
- ✅ Deploy em servidor (Render.com / Railway)
- ✅ CI/CD (GitHub Actions)
- ✅ Monitoring (logs, errors)
- ✅ Backups automáticos

---

## 💰 Custo Estimado

### Desenvolvimento
- **Tempo:** 6-8 semanas (1 desenvolvedor full-stack)
- **Custo:** R$ 0 (desenvolvimento interno) ou R$ 15.000-25.000 (terceirizado)

### Infraestrutura (Produção)

**Opção 1: Hosting Gratuito**
- **Render.com Free Tier:**
  - Backend: 750h/mês gratuito
  - Frontend: Static site gratuito
  - Banco SQLite: Armazenado no backend (max 10GB)
  - **Custo:** R$ 0/mês
  - **Limitação:** Sleep após 15min inatividade

**Opção 2: Hosting Pago (Recomendado)**
- **Render.com / Railway:**
  - Backend: $7-15/mês
  - Frontend: $0 (static site)
  - Banco: Incluído
  - **Custo:** R$ 35-75/mês
  - **Benefício:** 24/7 online, sem sleep

**Opção 3: VPS Dedicado**
- **DigitalOcean / Linode:**
  - Droplet 2GB RAM: $12/mês
  - Backup: $2/mês
  - **Custo:** R$ 70/mês
  - **Benefício:** Controle total, performance

---

## 🎓 Tecnologias Detalhadas

### Backend: FastAPI

**Por que FastAPI?**
- ✅ Rápido (performance comparável a Node.js)
- ✅ Type hints nativos (TypeScript do Python)
- ✅ Documentação automática (Swagger UI)
- ✅ Async/await nativo
- ✅ Validação automática (Pydantic)

**Exemplo de código:**
```python
# backend/api/routes/search.py
from fastapi import APIRouter, Query
from ..models import SearchRequest, SearchResponse
from ..services import search_service

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Busca publicações usando RAG + FTS5.
    """
    results = await search_service.search(
        query=request.query,
        filters=request.filters,
        limit=request.limit,
        page=request.page
    )
    return results
```

### Frontend: React + TypeScript

**Por que React?**
- ✅ Componentização (reutilização de código)
- ✅ Ecosystem maduro (milhões de bibliotecas)
- ✅ Performance (Virtual DOM)
- ✅ Suporte TypeScript nativo

**Exemplo de componente:**
```tsx
// frontend/src/components/ResultCard.tsx
interface ResultCardProps {
  publicacao: Publicacao;
  onViewDetails: (id: string) => void;
}

export function ResultCard({ publicacao, onViewDetails }: ResultCardProps) {
  return (
    <div className="border rounded-lg p-4 shadow-sm hover:shadow-md">
      <h3 className="font-semibold text-lg">{publicacao.titulo}</h3>

      <p className="text-gray-600 text-sm mt-2 line-clamp-3">
        {publicacao.ementa}
      </p>

      <div className="flex gap-2 mt-3 text-sm text-gray-500">
        <span>📍 {publicacao.tribunal}</span>
        <span>📅 {formatDate(publicacao.data_publicacao)}</span>
        <span>💯 {publicacao.relevancia_score}%</span>
      </div>

      <button
        onClick={() => onViewDetails(publicacao.id)}
        className="mt-3 px-4 py-2 bg-blue-600 text-white rounded"
      >
        Ver completo
      </button>
    </div>
  );
}
```

---

## 📚 Documentação de Referência

### Tutoriais Recomendados

**Backend (FastAPI):**
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [FastAPI + SQLAlchemy](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [FastAPI + Docker](https://fastapi.tiangolo.com/deployment/docker/)

**Frontend (React):**
- [React Official Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [shadcn/ui Components](https://ui.shadcn.com/)

**Busca Semântica:**
- [Sentence Transformers](https://www.sbert.net/)
- [FAISS Vector Search](https://github.com/facebookresearch/faiss)

---

## 🔮 Roadmap Futuro

### Curto Prazo (3 meses)
- [ ] Implementar MVP (Fases 1-2)
- [ ] Testes com usuários reais
- [ ] Deploy em produção

### Médio Prazo (6 meses)
- [ ] Features avançadas (Fase 3)
- [ ] Mobile app (React Native)
- [ ] API pública para integrações

### Longo Prazo (1 ano)
- [ ] Análise de tendências (ML)
- [ ] Sumarização automática (LLM)
- [ ] Alertas personalizados
- [ ] Integração com sistemas de processo eletrônico

---

## ✅ Checklist de Implementação

### Preparação
- [ ] Definir stack tecnológica final
- [ ] Configurar ambiente de desenvolvimento
- [ ] Criar repositório Git

### Backend
- [ ] Inicializar projeto FastAPI
- [ ] Criar schemas Pydantic
- [ ] Implementar endpoints de busca
- [ ] Integrar com banco SQLite existente
- [ ] Integrar com sistema RAG
- [ ] Adicionar testes automatizados
- [ ] Documentação da API (Swagger)

### Frontend
- [ ] Inicializar projeto React + Vite
- [ ] Configurar Tailwind CSS + shadcn/ui
- [ ] Criar componentes base
- [ ] Implementar páginas principais
- [ ] Integrar com API backend
- [ ] Adicionar testes (Jest/Vitest)
- [ ] Responsividade mobile

### Deployment
- [ ] Criar Dockerfile (backend)
- [ ] Criar Dockerfile (frontend)
- [ ] Configurar docker-compose.yml
- [ ] Configurar nginx
- [ ] Deploy em staging
- [ ] Deploy em produção
- [ ] Configurar CI/CD

---

**Última atualização:** 2025-11-20
**Próximos passos:** Aprovação da proposta → Início da Fase 1 (MVP)
