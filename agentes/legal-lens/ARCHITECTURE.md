# Legal Lens - Arquitetura

## Visão Geral

O Legal Lens é um sistema RAG (Retrieval-Augmented Generation) especializado em documentos jurídicos brasileiros. Ele processa PDFs de diários de justiça, indexa em um vector database e permite busca semântica e extração estruturada de jurisprudência.

## Componentes Principais

### 1. PDFProcessor (`src/pdf_processor.py`)

Responsável por extrair texto de PDFs jurídicos e dividir em chunks.

**Funcionalidades:**
- Extração de texto via PyPDF2 (rápido) ou pdfplumber (preciso)
- Divisão em chunks com overlap configurável
- Extração de metadata (tribunal, data, página)
- Processamento batch de múltiplos PDFs

**Métodos principais:**
```python
extract_text_pdfplumber(pdf_path) -> List[Dict]
extract_metadata(pdf_path) -> Dict
chunk_text(text, metadata) -> List[DocumentChunk]
process_pdf(pdf_path, method) -> List[DocumentChunk]
batch_process_pdfs(pdf_paths) -> List[DocumentChunk]
```

**Output:** `List[DocumentChunk]` com texto, metadata e posição

### 2. RAGEngine (`src/rag_engine.py`)

Motor de busca semântica baseado em embeddings e vector database.

**Funcionalidades:**
- Geração de embeddings com Sentence-Transformers
- Indexação no ChromaDB (vector database persistente)
- Busca semântica por similaridade de cosseno
- Filtros de metadata (tribunal, data, etc)
- Estatísticas da collection

**Tecnologias:**
- **ChromaDB:** Vector database SQLite + HNSW index
- **Sentence-Transformers:** Modelo multilíngue `paraphrase-multilingual-mpnet-base-v2`
- **Cosine Similarity:** Medida de similaridade entre embeddings

**Métodos principais:**
```python
generate_embedding(text) -> List[float]
add_documents(chunks) -> int
search(query, top_k, filter_metadata) -> List[Dict]
search_by_theme(theme, top_k) -> List[Dict]
get_collection_stats() -> Dict
```

**Fluxo de indexação:**
1. Recebe chunks do PDFProcessor
2. Gera embeddings para cada chunk
3. Salva no ChromaDB com metadata
4. Persiste em disco (SQLite)

**Fluxo de busca:**
1. Recebe query de texto
2. Gera embedding da query
3. Busca no ChromaDB por similaridade
4. Aplica filtros de metadata
5. Retorna top-k resultados acima do threshold

### 3. JurisprudenceExtractor (`src/jurisprudence_extractor.py`)

Extrai informações estruturadas de decisões judiciais.

**Funcionalidades:**
- Classificação automática por tema jurídico
- Extração de campos estruturados via regex:
  - Número de processo
  - Tribunal e vara
  - Tipo de decisão
  - Partes do processo
  - Ementa e dispositivo
- Confidence scoring
- Relatórios consolidados

**Métodos principais:**
```python
extract_from_text(text, metadata, theme) -> JurisprudenceEntry
extract_by_theme(theme, top_k) -> List[JurisprudenceEntry]
extract_all_themes(top_k_per_theme) -> Dict[str, List[JurisprudenceEntry]]
generate_report(theme_entries) -> Dict
```

**Output:** `JurisprudenceEntry` (dataclass) com campos estruturados

### 4. Main Menu (`main.py`)

Interface CLI interativa com menu de opções.

**Funcionalidades:**
- 10+ opções de menu
- Indexação de PDFs
- Busca semântica
- Extração de jurisprudência
- Estatísticas e relatórios
- Exportação JSON

## Fluxo de Dados

```
┌─────────────────┐
│   oab-watcher   │
│  (baixa PDFs)   │
└────────┬────────┘
         │
         │ PDFs
         ▼
┌─────────────────┐
│  PDFProcessor   │
│   (extrai texto)│
└────────┬────────┘
         │
         │ DocumentChunks
         ▼
┌─────────────────┐
│   RAGEngine     │
│ (indexa embeddings)│
└────────┬────────┘
         │
         │ Vector DB
         ▼
┌─────────────────┐
│ Jurisprudence   │
│   Extractor     │
│ (classifica e   │
│  estrutura)     │
└────────┬────────┘
         │
         │ JurisprudenceEntry
         ▼
┌─────────────────┐
│  JSON Output    │
│  (relatórios)   │
└─────────────────┘
```

## Modelos de Dados

### DocumentChunk

```python
@dataclass
class DocumentChunk:
    text: str                # Texto do chunk
    page_number: int         # Número da página
    source_file: str         # Nome do arquivo PDF
    metadata: Dict           # Metadata adicional
```

### JurisprudenceEntry

```python
@dataclass
class JurisprudenceEntry:
    numero_processo: Optional[str]
    tribunal: str
    vara: Optional[str]
    data_publicacao: str
    tipo_decisao: Optional[str]
    tema: str
    ementa: Optional[str]
    dispositivo: Optional[str]
    partes: List[str]
    texto_completo: str
    source_file: str
    page_number: int
    confidence: float
```

## Configuração

Todo o sistema é configurado via `config.json`:

```json
{
  "rag": {
    "embedding_model": "...",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "vector_db_type": "chromadb",
    "top_k_results": 5,
    "similarity_threshold": 0.7
  },
  "extraction": {
    "temas_interesse": [...],
    "min_confidence": 0.6,
    "extract_fields": [...]
  }
}
```

## Persistência

### Vector Database (ChromaDB)

```
E:\claude-code-data\agentes\legal-lens\vector_db\
└── chroma.sqlite3  # SQLite database com HNSW index
```

**Características:**
- Persistente (sobrevive a reinicializações)
- HNSW index para busca rápida (log N)
- Suporta filtros de metadata
- Tamanho escalável (GB de documentos)

### Outputs

```
E:\claude-code-data\agentes\legal-lens\outputs\
├── jurisprudencia_<tema>_<timestamp>.json
└── relatorio_completo_<timestamp>.json
```

## Performance

### Indexação

- **Extração de texto:** ~2-5 seg/PDF (pdfplumber)
- **Geração de embeddings:** ~0.1-0.5 seg/chunk
- **Throughput:** ~50-100 PDFs/hora (hardware médio)

**Gargalos:**
- I/O de disco (leitura de PDFs)
- Geração de embeddings (CPU)
- Escrita no ChromaDB (I/O)

**Otimizações:**
- Batch processing de chunks
- Caching de embeddings
- Paralelização (futura)

### Busca

- **Latência:** <1 segundo para 10k documentos
- **Complexidade:** O(log N) com HNSW index
- **Throughput:** ~100 queries/segundo

## Escalabilidade

### Limites Atuais

- **Documentos:** ~100k chunks (testado)
- **Tamanho do DB:** ~500 MB a 2 GB
- **RAM:** ~2-4 GB durante indexação

### Escalabilidade Futura

Para escalar além:
1. **Particionamento:** Múltiplas collections por tribunal/ano
2. **Vector DB distribuído:** FAISS, Milvus, Qdrant
3. **Embeddings mais eficientes:** Quantização, PCA
4. **Paralelização:** Multiprocessing para indexação

## Extensibilidade

### Adicionar Novo Tema

Editar `config.json`:

```json
{
  "extraction": {
    "temas_interesse": [
      ...,
      "novo tema"
    ]
  }
}
```

### Adicionar Novo Campo de Extração

1. Atualizar `JurisprudenceEntry` dataclass
2. Adicionar regex pattern em `JurisprudenceExtractor.patterns`
3. Implementar método `extract_<campo>()`
4. Chamar em `extract_from_text()`

### Trocar Embedding Model

Editar `config.json`:

```json
{
  "rag": {
    "embedding_model": "sentence-transformers/novo-modelo"
  }
}
```

**Requer:** Re-indexação de todos os documentos

## Segurança e Privacy

- **Dados locais:** Tudo armazenado em E:\ (não cloud)
- **Sem telemetria:** ChromaDB com `anonymized_telemetry=False`
- **Sem API calls:** Embeddings gerados localmente
- **Git:** Dados NUNCA comitados (.gitignore)

## Testes

```
tests/
├── test_pdf_processor.py
├── test_rag_engine.py  (futuro)
└── test_jurisprudence_extractor.py
```

Executar:
```powershell
pytest tests/ -v
```

## Logging

Todas as operações são logadas:

```
E:\claude-code-data\agentes\legal-lens\logs\
└── legal_lens_<timestamp>.log
```

**Níveis:**
- DEBUG: Detalhes internos
- INFO: Operações principais
- WARNING: Problemas não-críticos
- ERROR: Erros com stack trace

## Dependências Principais

```
chromadb>=0.4.22          # Vector database
sentence-transformers     # Embeddings
pdfplumber>=0.10.0       # PDF processing
PyPDF2>=3.0.0            # PDF processing (alternativo)
langchain>=0.1.0         # RAG framework (opcional)
```

## Roadmap

### v1.0 (Atual) ✅
- Sistema RAG básico
- Extração de jurisprudência
- CLI interativa

### v1.1 (Planejado)
- [ ] Suporte a LLM para análise (GPT-4, Claude)
- [ ] Sumarização automática de decisões
- [ ] API REST
- [ ] Dashboard web

### v2.0 (Futuro)
- [ ] Detecção de jurisprudência repetida
- [ ] Análise de tendências temporais
- [ ] Grafos de citações entre decisões
- [ ] Alertas automáticos para novos precedentes

## Autor

PedroGiudice - 2025
