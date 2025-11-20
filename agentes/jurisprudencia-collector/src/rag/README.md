# Módulo RAG - Busca Semântica de Jurisprudência

Sistema de **Retrieval-Augmented Generation (RAG)** para busca semântica em publicações jurídicas usando embeddings transformer e similaridade de cosseno.

## Componentes

### 1. **Embedder** (`embedder.py`)
Geração de embeddings usando modelos transformer otimizados para português.

**Modelos suportados:**
- `neuralmind/bert-base-portuguese-cased` (768 dim) - **Padrão** - Alta qualidade
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dim) - Leve e rápido
- `sentence-transformers/distiluse-base-multilingual-cased-v2` (512 dim) - Balanço qualidade/velocidade

**Funcionalidades:**
- ✅ Encoding single e batch
- ✅ Cache local de modelos (~420-480 MB)
- ✅ Suporte a GPU/CPU/MPS (Apple Silicon)
- ✅ Serialização para SQLite (BLOB)
- ✅ Normalização L2 automática

**Exemplo:**
```python
from src.rag import Embedder

embedder = Embedder(modelo='neuralmind/bert-base-portuguese-cased')

# Single text
embedding = embedder.encode("Texto de uma publicação jurídica")

# Batch processing
embeddings = embedder.encode_batch([
    "Apelação cível conhecida e provida.",
    "Recurso especial não conhecido.",
    "Habeas corpus deferido."
], batch_size=32)

# Serializar para SQLite
blob = embedder.serializar_embedding(embedding)
```

---

### 2. **Chunker** (`chunker.py`)
Divisão de textos longos em chunks (pedaços) menores com sobreposição.

**Estratégias:**
- `paragrafo` (padrão) - Prefere quebrar em parágrafos (`\n\n`)
- `sentenca` - Prefere quebrar em sentenças (`.`, `!`, `?`)
- `rigido` - Quebra em posição fixa (sem considerar estrutura)

**Configuração padrão:**
- Tamanho: 500 tokens (~2000 caracteres)
- Sobreposição: 50 tokens (10%)
- Heurística: 4.0 chars/token (português)

**Exemplo:**
```python
from src.rag import Chunker

chunker = Chunker(tamanho_chunk=500, overlap=50)

# Dividir texto longo
chunks = chunker.dividir_texto(texto_longo, estrategia="paragrafo")

for chunk in chunks:
    print(f"Chunk {chunk.chunk_index}: {chunk.tamanho_tokens} tokens")

# Com metadata para DB
chunks_db = chunker.dividir_com_metadata(
    texto=texto_longo,
    publicacao_id="abc123-def456",
    estrategia="paragrafo",
    metadata_adicional={"tribunal": "TJSP", "tipo": "Acórdão"}
)
```

---

### 3. **SemanticSearch** (`search.py`)
Busca por similaridade de cosseno entre embeddings.

**Funcionalidades:**
- ✅ Busca semântica (similaridade de cosseno)
- ✅ Busca híbrida (semântica + textual FTS5)
- ✅ Filtros por tribunal, data, tipo
- ✅ Busca em publicações completas ou chunks
- ✅ Threshold configurável (padrão: 0.7)

**Exemplo:**
```python
from src.rag import Embedder, SemanticSearch

embedder = Embedder()
search = SemanticSearch(db_path="jurisprudencia.db", threshold_similaridade=0.7)

# Gerar embedding da consulta
query_embedding = embedder.encode("responsabilidade civil acidente de trânsito")

# Buscar publicações similares
resultados = search.buscar(
    query_embedding=query_embedding,
    top_k=10,
    filtros={"tribunal": "TJSP", "tipo_publicacao": "Acórdão"},
    incluir_chunks=False
)

for r in resultados:
    print(f"{r['numero_processo_fmt']} - Score: {r['score_similaridade']:.4f}")

# Buscar publicações similares a uma publicação específica
similares = search.buscar_similar_por_id(
    publicacao_id="abc123-def456",
    top_k=5,
    excluir_propria=True
)

# Busca híbrida (semântica + textual)
resultados_hibridos = search.buscar_hibrida(
    query_text="responsabilidade civil",
    query_embedding=query_embedding,
    top_k=10,
    peso_semantico=0.7  # 70% semântico, 30% textual
)
```

---

## Instalação

### 1. Instalar dependências
```bash
cd agentes/jurisprudencia-collector
source .venv/bin/activate  # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
```

**Dependências adicionadas:**
- `transformers>=4.30.0` - Modelos transformer (HuggingFace)
- `torch>=2.0.0` - Backend PyTorch
- `sentence-transformers>=2.2.0` - Modelos otimizados para embeddings
- `numpy>=1.24.0` - Operações vetoriais

### 2. Download do modelo
Na primeira execução, o modelo será baixado automaticamente (~420 MB):
```python
embedder = Embedder()  # Download automático para ~/.cache/huggingface
```

---

## Uso Completo

### Exemplo 1: Processar Publicação e Armazenar Embedding

```python
import sqlite3
from src.rag import Embedder

# Inicializar embedder
embedder = Embedder(modelo='neuralmind/bert-base-portuguese-cased')

# Texto da publicação
texto = """
APELAÇÃO CÍVEL. DIREITO DO CONSUMIDOR. RESPONSABILIDADE CIVIL.
Danos morais. Inscrição indevida em cadastros de inadimplentes.
Recurso conhecido e não provido.
"""

# Gerar embedding
embedding = embedder.encode(texto, normalizar=True)

# Serializar para SQLite
blob = embedder.serializar_embedding(embedding)

# Inserir no banco
conn = sqlite3.connect("jurisprudencia.db")
cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO embeddings (publicacao_id, embedding, dimensao, modelo)
    VALUES (?, ?, ?, ?)
    """,
    ("abc123-def456", blob, embedder.dimensao, embedder.modelo_nome)
)

conn.commit()
conn.close()
```

### Exemplo 2: Processar Publicação Longa (com Chunks)

```python
from src.rag import Embedder, Chunker

embedder = Embedder()
chunker = Chunker(tamanho_chunk=500, overlap=50)

# Texto longo (ex: acórdão completo com 10.000+ caracteres)
texto_longo = """..."""  # Texto completo

# Dividir em chunks
chunks_metadata = chunker.dividir_com_metadata(
    texto=texto_longo,
    publicacao_id="abc123-def456",
    estrategia="paragrafo"
)

# Gerar embeddings em batch
textos_chunks = [c['texto'] for c in chunks_metadata]
embeddings = embedder.encode_batch(textos_chunks, batch_size=32)

# Inserir no banco (chunks + embeddings)
conn = sqlite3.connect("jurisprudencia.db")
cursor = conn.cursor()

for chunk_meta, embedding in zip(chunks_metadata, embeddings):
    # Inserir chunk
    cursor.execute(
        "INSERT INTO chunks (id, publicacao_id, chunk_index, texto, tamanho_tokens) VALUES (?, ?, ?, ?, ?)",
        (chunk_meta['id'], chunk_meta['publicacao_id'], chunk_meta['chunk_index'], chunk_meta['texto'], chunk_meta['tamanho_tokens'])
    )

    # Inserir embedding do chunk
    blob = embedder.serializar_embedding(embedding)
    cursor.execute(
        "INSERT INTO chunks_embeddings (chunk_id, embedding, dimensao, modelo) VALUES (?, ?, ?, ?)",
        (chunk_meta['id'], blob, embedder.dimensao, embedder.modelo_nome)
    )

conn.commit()
conn.close()
```

### Exemplo 3: Buscar Publicações Similares

```python
from src.rag import Embedder, SemanticSearch

embedder = Embedder()
search = SemanticSearch(db_path="jurisprudencia.db", threshold_similaridade=0.7)

# Consulta do usuário
query = "responsabilidade civil por acidente de trânsito com danos morais"

# Gerar embedding da consulta
query_embedding = embedder.encode(query, normalizar=True)

# Buscar publicações similares
resultados = search.buscar(
    query_embedding=query_embedding,
    top_k=10,
    filtros={
        "tribunal": ["TJSP", "STJ"],
        "tipo_publicacao": "Acórdão",
        "data_inicio": "2023-01-01",
        "data_fim": "2024-12-31"
    }
)

# Exibir resultados
for i, r in enumerate(resultados, 1):
    print(f"\n{i}. {r['numero_processo_fmt']}")
    print(f"   Tribunal: {r['tribunal']} | Tipo: {r['tipo_publicacao']}")
    print(f"   Data: {r['data_publicacao']}")
    print(f"   Score: {r['score_similaridade']:.4f}")
    print(f"   Ementa: {r['ementa'][:200]}...")
```

---

## Scripts de Exemplo

### 1. **`exemplo_rag.py`** - Exemplo Completo
Script demonstrativo com fluxo completo de processamento e busca.

```bash
# Busca semântica
python exemplo_rag.py --query "responsabilidade civil" --top-k 10 --tribunal TJSP

# Busca híbrida
python exemplo_rag.py --query "responsabilidade civil" --modo hibrido --top-k 10
```

### 2. **`teste_performance_rag.py`** - Benchmark
Mede tempo de processamento para diferentes operações.

```bash
# Processar 100 textos
python teste_performance_rag.py --num-textos 100

# Testar modelo alternativo
python teste_performance_rag.py --num-textos 100 --modelo sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

**Benchmarks inclusos:**
1. Encoding single (chamadas sequenciais)
2. Encoding batch (processamento em lote)
3. Chunking de textos longos
4. Serialização/deserialização
5. Similaridade de cosseno
6. End-to-end (chunking + encoding)

---

## Performance Esperada

### Hardware de Referência
- **CPU:** Intel i7 ou AMD Ryzen 7
- **RAM:** 16 GB
- **GPU:** Opcional (acelera ~5-10x)

### Métricas (neuralmind/bert-base-portuguese-cased, CPU)
- **Encoding single:** ~50-100ms por texto (2000 chars)
- **Encoding batch (32):** ~30-50ms por texto
- **Chunking:** ~1-5ms por texto (10.000 chars)
- **Similaridade de cosseno:** ~0.01ms por comparação
- **End-to-end (100 publicações):** ~120-180s (~1.5-3min)

### Otimizações
- ✅ Usar batch processing (5-10x mais rápido que single)
- ✅ Usar GPU se disponível (5-10x mais rápido que CPU)
- ✅ Usar modelo leve para produção (paraphrase-multilingual-MiniLM-L12-v2)
- ✅ Processar embeddings offline (não em tempo real)

---

## Estrutura do Banco de Dados

### Tabela: `embeddings`
```sql
CREATE TABLE embeddings (
    publicacao_id TEXT PRIMARY KEY,
    embedding BLOB NOT NULL,          -- Float32Array serializado
    dimensao INTEGER NOT NULL,        -- 768 ou 384
    modelo TEXT NOT NULL,             -- Nome do modelo
    versao_modelo TEXT,
    data_criacao TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id) ON DELETE CASCADE
);
```

### Tabela: `chunks`
```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,              -- UUID v4
    publicacao_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,     -- 0, 1, 2...
    texto TEXT NOT NULL,
    tamanho_tokens INTEGER,
    FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id) ON DELETE CASCADE,
    UNIQUE(publicacao_id, chunk_index)
);
```

### Tabela: `chunks_embeddings`
```sql
CREATE TABLE chunks_embeddings (
    chunk_id TEXT PRIMARY KEY,
    embedding BLOB NOT NULL,
    dimensao INTEGER NOT NULL,
    modelo TEXT NOT NULL,
    data_criacao TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);
```

---

## Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'transformers'`
```bash
pip install transformers torch sentence-transformers numpy
```

### Erro: `CUDA out of memory`
Reduzir `batch_size` ou usar CPU:
```python
embedder = Embedder(device="cpu")
```

### Erro: `Model download timeout`
Download manual:
```bash
python -c "from transformers import AutoModel; AutoModel.from_pretrained('neuralmind/bert-base-portuguese-cased')"
```

### Performance lenta
- Use batch processing
- Use GPU se disponível
- Considere modelo leve (384 dim) para produção

---

## Referências

- **HuggingFace Transformers:** https://huggingface.co/docs/transformers
- **Sentence Transformers:** https://www.sbert.net/
- **NeuralMind BERT Portuguese:** https://huggingface.co/neuralmind/bert-base-portuguese-cased
- **Cosine Similarity:** https://en.wikipedia.org/wiki/Cosine_similarity

---

**Última atualização:** 2025-11-20
**Versão:** 1.0.0
