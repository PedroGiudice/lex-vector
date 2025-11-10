# Legal RAG System

Sistema de Retrieval-Augmented Generation para consultas jurisprudenciais brasileiras.

## Visão Geral

Este agente implementa um sistema RAG (Retrieval-Augmented Generation) especializado em jurisprudência brasileira, capaz de:

- **Indexar** acórdãos de múltiplos tribunais (STF, STJ, TRFs, TJs)
- **Recuperar** decisões relevantes usando busca híbrida (densa + esparsa)
- **Gerar** respostas fundamentadas em jurisprudência real
- **Analisar** estrutura e conteúdo de decisões judiciais

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTE: legal-rag                        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Indexação   │    │  Retrieval   │    │  Generation  │
│   Pipeline   │    │    Engine    │    │   Pipeline   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Vector Store │    │ Reranker     │    │   LLM API    │
│  (Chroma)    │    │ (BGE-M3)     │    │  (Claude)    │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Instalação

### Pré-requisitos

- Python 3.10+
- UV (ultra-fast package installer) - opcional mas recomendado
- 8GB+ RAM
- GPU CUDA (opcional, mas recomendado para performance)

### Setup com UV (Recomendado)

```bash
# Navegar para o diretório do agente
cd agentes/legal-rag

# Criar ambiente virtual
uv venv

# Ativar ambiente (Linux/Mac)
source .venv/bin/activate

# Ativar ambiente (Windows)
.venv\Scripts\activate

# Instalar dependências
uv pip install -e .

# Instalar dependências GPU (se CUDA disponível)
uv pip install -e ".[gpu]"

# Instalar dependências de desenvolvimento
uv pip install -e ".[dev]"
```

### Setup com pip tradicional

```bash
cd agentes/legal-rag
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -e .
```

### Baixar modelos spaCy

```bash
python -m spacy download pt_core_news_lg
```

### Configurar API Keys

```bash
# Criar arquivo .env
cat > .env << EOF
ANTHROPIC_API_KEY=sua_chave_anthropic_aqui
CLAUDE_DATA_ROOT=/caminho/para/dados  # opcional
EOF
```

## Configuração

O sistema é configurado via `config.json`. As principais seções são:

- **paths**: Diretórios de dados (corpus, vector store, cache, logs)
- **embeddings**: Configuração do modelo de embeddings
- **retrieval**: Pesos para busca híbrida, reranking
- **llm**: Configurações do Claude (modelo, temperatura, etc)
- **indexing**: Batch size, workers paralelos
- **chunking**: Tamanho de chunks, overlap, separadores

Veja `config.json` para detalhes completos.

## Estrutura de Diretórios

```
legal-rag/
├── config/              # Configurações
│   ├── settings.py      # Carregamento de config
│   └── embeddings_models.py  # Modelos de embeddings
├── indexing/            # Pipeline de indexação
│   ├── models.py        # Modelos de dados
│   ├── pipeline.py      # Indexador principal
│   └── semantic_chunker.py  # Chunking semântico
├── retrieval/           # Engine de busca
│   ├── hybrid_retriever.py  # Busca híbrida
│   └── reranker.py      # Reranking neural
├── generation/          # Geração de respostas
│   ├── rag_generator.py # Gerador RAG
│   └── prompts.py       # Templates de prompts
├── analysis/            # Análise jurisprudencial
│   ├── analyzer.py      # Analisador de acórdãos
│   └── ner.py           # NER jurídico
├── tests/               # Testes
└── config.json          # Configuração principal
```

## Uso Básico

### 1. Indexar Corpus

```python
from indexing.pipeline import JurisprudenciaIndexer
from indexing.models import AcordaoMetadata
from datetime import datetime
from pathlib import Path

# Criar indexador
indexer = JurisprudenciaIndexer(
    vector_store_path=Path("data/chroma_db")
)

# Preparar metadata
metadata = AcordaoMetadata(
    tribunal="STF",
    processo_numero="0000001-00.2024.1.00.0000",
    classe_processual="RE",
    relator="Min. Luís Roberto Barroso",
    data_julgamento=datetime(2024, 1, 15),
    data_publicacao=datetime(2024, 1, 20),
    orgao_julgador="Plenário",
    area_direito="Constitucional",
    assunto_principal="Direitos Fundamentais",
    ementa="Recurso extraordinário sobre liberdade de expressão..."
)

# Indexar acórdão
texto_acordao = "..."  # Texto completo
stats = indexer.index_acordao(texto_acordao, metadata)

print(f"Chunks indexados: {stats['chunks_indexed']}")
```

### 2. Fazer Consultas (RAG)

```python
from retrieval.hybrid_retriever import HybridJurisprudenciaRetriever
from generation.rag_generator import JurisprudenciaRAGGenerator
import anthropic

# Criar retriever
retriever = HybridJurisprudenciaRetriever(
    vector_store_path=Path("data/chroma_db")
)

# Criar gerador
client = anthropic.Anthropic()
generator = JurisprudenciaRAGGenerator(
    retriever=retriever,
    llm_client=client
)

# Fazer pergunta
response = generator.generate(
    query="Quais os requisitos para prisão preventiva segundo o STF?",
    template_name="consulta_simples",
    top_k=10
)

print(response['resposta'])
print("\nFontes:")
for fonte in response['fontes']:
    print(f"- {fonte['tribunal']} {fonte['processo']}")
```

### 3. Analisar Acórdão

```python
from analysis.analyzer import JurisprudenciaAnalyzer

analyzer = JurisprudenciaAnalyzer()

# Analisar
resultado = analyzer.analisar_acordao(texto_acordao)

print(f"Decisão: {resultado['tipo_decisao'].value}")
print(f"Entidades: {len(resultado['entidades'])}")
print(f"Teses: {len(resultado['teses'])}")
print(f"Fundamentação: {resultado['fundamentacao']}")
```

## Modelos de Embeddings

O sistema suporta múltiplos modelos de embeddings otimizados para português:

| Config | Modelo | Tokens | Dimensão | Uso |
|--------|--------|--------|----------|-----|
| `production` | BGE-M3 | 8192 | 1024 | Produção (balanceado) |
| `portuguese` | BERTimbau | 512 | 1024 | Máxima precisão PT-BR |
| `fast` | Paraphrase-XLM | 128 | 768 | Prototipagem rápida |
| `balanced` | BGE-Large-PT | 512 | 1024 | Balanço speed/quality |

Selecionar modelo:

```python
from config.embeddings_models import get_embedding_model

model = get_embedding_model("production", device="cuda")
```

## Performance

### Targets

- **Retrieval latency**: < 3s (p95)
- **Generation latency**: < 5s (p95)
- **Recall@10**: > 0.80
- **Precision@10**: > 0.70
- **MRR**: > 0.70
- **Faithfulness**: > 0.85
- **Answer Relevancy**: > 0.80

### Otimizações

- Busca híbrida (dense + sparse) com Reciprocal Rank Fusion
- Reranking neural para refinar top-K
- Caching de retrievals frequentes
- Batching de embeddings
- Processamento paralelo na indexação

## Tribunais Suportados

- **Superiores**: STF, STJ, TST, TSE, STM
- **Federais**: TRF1-6
- **Estaduais**: TJSP, TJRJ, TJMG, TJRS, TJPR, TJSC, TJBA, TJPE, TJCE, etc.

## Áreas do Direito

Civil, Penal, Trabalhista, Tributário, Administrativo, Constitucional, Processual Civil, Processual Penal, Empresarial, Consumidor, Ambiental, Eleitoral, Previdenciário, Família e Sucessões, Internacional, Digital.

## Testes

```bash
# Rodar todos os testes
pytest

# Com coverage
pytest --cov=. --cov-report=term-missing

# Teste específico
pytest tests/test_indexing.py::test_indexacao_simples
```

## Avaliação

O sistema inclui métricas de avaliação automática:

```python
from evaluation.rag_evaluator import RAGEvaluator

evaluator = RAGEvaluator()

# Avaliar retrieval
retrieval_metrics = evaluator.evaluate_retrieval(
    queries=test_queries,
    ground_truth=ground_truth_docs,
    retrieved=retrieved_docs
)

# Avaliar geração (RAGAS)
generation_metrics = evaluator.evaluate_generation(
    questions=questions,
    answers=generated_answers,
    contexts=contexts
)
```

## Logging

Logs são salvos em:
- **Console**: Nível INFO, colorizado
- **Arquivo**: `data/logs/legal-rag.log`, rotação 500MB, retenção 30 dias

Configurar nível de log:

```python
from config.settings import get_settings

settings = get_settings()
settings.logging['level'] = 'DEBUG'
settings.setup_logging()
```

## Troubleshooting

### GPU não detectada

```python
from config.embeddings_models import _detect_device
print(_detect_device())  # Deve retornar 'cuda' se GPU disponível
```

### ChromaDB muito lento

- Verifique se está usando SSD para vector store
- Considere aumentar `batch_size` na indexação
- Use `top_k` menor no retrieval

### Respostas sem fundamentação

- Aumente `top_k` no retrieval
- Ajuste pesos dense/sparse no `config.json`
- Verifique qualidade do corpus indexado

## Roadmap

- [ ] Fine-tuning de embeddings para domínio jurídico BR
- [ ] Integração com DJEN/OAB watchers
- [ ] API REST para consultas
- [ ] Interface web
- [ ] Suporte a GraphRAG
- [ ] Expansão corpus para 100k+ acórdãos

## Referências

- **Especificação técnica**: Ver documento de especificação completo
- **JurisMiner**: Pacote R de análise jurisprudencial (inspiração para normalização)
- **LangChain**: Framework RAG
- **ChromaDB**: Vector store
- **Anthropic Claude**: LLM para geração

## Licença

MIT

## Contato

Pedro Giudice - C.M. Rodrigues Advogados
