---
name: legal-api
description: This skill should be used when working with the Legal-API DJEN ecosystem (API DJEN/CNJ, agentes jurisprudencia-collector/djen-tracker/legal-lens, or MCP server djen-mcp-server). Provides expert guidance on API limitations, performance optimization, database schema, RAG implementation, and debugging common issues with Brazilian legal data systems.
---

# Legal-API Skill

## Overview

Provides comprehensive guidance for developing, debugging, and optimizing systems that interact with the DJEN (Diário de Justiça Eletrônico Nacional) API and related legal data infrastructure. This skill covers:

- API DJEN integration and known limitations
- Three specialized agents (djen-tracker, jurisprudencia-collector, legal-lens)
- MCP server (djen-mcp-server) for Claude Desktop integration
- Database schema design (SQLite with RAG)
- Performance optimization techniques
- Common pitfalls and debugging strategies

## Core Capabilities

### 1. API DJEN Integration

**Endpoint:** `https://comunicaapi.pje.jus.br/api/v1/comunicacao`

**Critical Known Issues** (see `references/known-issues.md` for details):
- ❌ **OAB filter does NOT work** - API returns ALL publications regardless of `numeroOab` parameter
- ⚠️ **Rate limiting:** 21 requests per 5-second sliding window (HTTP 429 after exceeding)
- ✅ **Workarounds:** Download all PDFs and filter locally OR use RAG semantic search

**Best Practices:**
```python
# ✅ CORRECT - No offset parameter
publicacoes = downloader.baixar_api(
    tribunal='STJ',
    data='2025-11-20',
    limit=100,
    max_pages=10  # Pagination handled internally
)

# ❌ WRONG - offset does not exist
publicacoes = downloader.baixar_api(
    tribunal='STJ',
    data='2025-11-20',
    offset=200  # TypeError!
)
```

### 2. Performance Optimization

**Rate Limiting (Adaptive Window):**
```python
# Conservative buffer for reliability
downloader = DJENDownloader(
    requests_per_minute=144,  # Sustainable rate (12 req/5s)
    adaptive_rate_limit=True  # Sliding window detection
)
```

**Batch Commits (535x speedup):**
```python
# ✅ CORRECT - Batch commits every 100 records
BATCH_SIZE = 100
for i, pub in enumerate(publicacoes, start=1):
    inserir_publicacao(conn, pub)
    if i % BATCH_SIZE == 0:
        conn.commit()
conn.commit()  # Final commit

# ❌ WRONG - Individual commits (535x slower!)
for pub in publicacoes:
    inserir_publicacao(conn, pub)
    conn.commit()  # N+1 problem
```

**Real Performance Gains:**
- **Before:** 30 req/min → **After:** 144 req/min (4.8x faster)
- **Before:** 117 writes/sec → **After:** 62,894 writes/sec (535x speedup via batch commits)
- **Download time (6 months):** ~100h → **~21h**

### 3. Database Schema & Deduplication

**Hash-Based Deduplication:**
```python
import hashlib

# ✅ CORRECT - Hash content, not API ID
hash_conteudo = hashlib.sha256(texto_html.encode()).hexdigest()

# Schema includes:
# CREATE UNIQUE INDEX idx_hash ON publicacoes(hash_conteudo)
```

**Schema Reference:** See `references/schema.md` for complete SQLite schema including:
- Publicações table (main data)
- Embeddings table (RAG vectors)
- Chunks table (long texts)
- FTS5 virtual table (full-text search)
- Views for statistics

### 4. Text Processing & Normalization

**Case-Insensitive Type Filtering:**
```python
import unicodedata

def normalizar_tipo_publicacao(tipo: str) -> str:
    if not tipo:
        return ""
    # Remove accents
    sem_acentos = unicodedata.normalize('NFD', tipo)
    sem_acentos = ''.join(c for c in sem_acentos
                         if unicodedata.category(c) != 'Mn')
    return sem_acentos.lower().strip()

# Comparison:
if normalizar_tipo_publicacao(pub['tipo']) == 'acordao':
    # Matches: 'Acórdão', 'ACÓRDÃO', '  Acórdão\n'
```

**Ementa Extraction:**
```python
def extrair_ementa(texto: str) -> Optional[str]:
    patterns = [
        r'EMENTA\s*[:\-]?\s*(.+?)(?=ACÓRDÃO|VOTO|$)',
        r'E\s*M\s*E\s*N\s*T\s*A\s*[:\-]?\s*(.+?)(?=ACÓRDÃO|VOTO|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()[:2000]
    return None
```

### 5. Agent Architecture

**Three Specialized Agents:**

**djen-tracker** (`agentes/djen-tracker/`):
- Downloads cadernos from 65 tribunais
- OAB filtering (13+ regex patterns)
- Parallel processing (200 PDFs/min with cache)
- Checkpoint system (resume after Ctrl+C)
- Export formats: JSON, Markdown, Excel, HTML

**jurisprudencia-collector** (`agentes/jurisprudencia-collector/`):
- Processes DJEN API publications
- Extracts ementas (~100% success rate for STJ acordãos)
- SQLite storage with deduplication
- RAG embeddings generation
- Scheduled daily updates

**legal-lens** (`agentes/legal-lens/`):
- RAG (Retrieval-Augmented Generation) system
- Semantic search via ChromaDB
- Theme-based jurisprudence extraction (13 legal themes)
- Multilingual embeddings (Portuguese-optimized)
- Interactive CLI interface

**MCP Server** (`mcp-servers/djen-mcp-server/`):
- Claude Desktop integration
- Tools: buscar_publicacoes, busca_semantica, historico_processo
- SQLite backend with embeddings
- Monitored processes tracking

### 6. RAG Implementation

**Embeddings Generation:**
```python
from transformers import AutoTokenizer, AutoModel
import torch

class JurisprudenciaEmbedder:
    def __init__(self, model_name='neuralmind/bert-base-portuguese-cased'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def gerar_embedding(self, texto: str, max_tokens=512) -> np.ndarray:
        inputs = self.tokenizer(
            texto,
            max_length=max_tokens,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
            return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
```

**Semantic Search:**
```python
# Cosine similarity search with filters
results = rag.buscar_similares(
    query="responsabilidade civil por dano moral",
    top_k=10,
    threshold=0.7,
    filtros={
        'tribunal': 'STJ',
        'tipo_publicacao': 'Acórdão',
        'data_inicio': '2024-01-01'
    }
)
```

## Workflow Decision Tree

When user asks about legal data systems, determine the appropriate path:

```
User mentions DJEN API issues?
├─ Yes → Check references/known-issues.md
│         ├─ Rate limiting → Adaptive rate limiter
│         ├─ Slow performance → Batch commits + profiling
│         └─ Filter not working → Local filtering or RAG
│
User needs to download cadernos?
├─ Yes → Use djen-tracker agent
│         └─ Guide through: Download modes (ALL/PRIORITARIOS/CUSTOM)
│
User needs jurisprudence database?
├─ Yes → Use jurisprudencia-collector
│         └─ Guide through: Scheduler setup, retroactive download
│
User needs semantic search?
├─ Yes → Use legal-lens or MCP server
│         └─ Guide through: Indexing PDFs, semantic queries
│
User debugging performance?
├─ Yes → Use scripts/diagnostic.py
│         └─ Profiling, bottleneck identification
│
User needs database schema?
└─ Yes → Show references/schema.md
          └─ SQLite design with FTS5 + RAG
```

## Common Tasks

### Diagnosing Performance Issues

Use `scripts/diagnostic.py` to profile and identify bottlenecks:
```bash
python skills/legal-api/scripts/diagnostic.py \
    --tribunal STJ \
    --data 2025-11-20 \
    --profile
```

Output identifies:
- API latency (network)
- HTML parsing time
- Database write speed
- Rate limiting delays

### Debugging Rate Limiting

**Symptoms:**
```
[ERROR] Recebido 429 Too Many Requests
[INFO] Backoff exponencial: aguardando 60s...
```

**Solution:**
1. Check current rate: `requests_per_minute` in config
2. Reduce to conservative 120 req/min (10 req/5s)
3. Enable adaptive limiting: `adaptive_rate_limit=True`
4. Monitor HTTP 429 rate (should be <1%)

### Setting Up Retroactive Download

Download historical data efficiently:
```bash
cd agentes/jurisprudencia-collector
source .venv/bin/activate

# Last 30 days (default)
python run_retroativo.py --yes

# Specific range
python run_retroativo.py \
    --inicio 2025-01-01 \
    --fim 2025-03-31 \
    --tribunais STJ TJSP \
    --yes
```

**Expected time:**
- 30 days × 8 tribunais: ~2-4 hours
- 6 months × 8 tribunais: ~20-25 hours (with optimizations)

### Creating RAG Index

Index PDFs for semantic search:
```bash
cd agentes/legal-lens
source .venv/bin/activate
python main.py

# Select option 1: "Indexar PDFs no vector database"
# Wait for completion (~50-100 PDFs/hour)
```

Then perform semantic queries:
```bash
# Select option 4: "Busca semântica livre"
# Example query: "responsabilidade médica erro cirúrgico"
```

## Anti-Patterns (What NOT to Do)

**❌ Using `offset` parameter:**
```python
# Does NOT exist in baixar_api()
publicacoes = downloader.baixar_api(..., offset=100)  # TypeError!
```

**❌ Individual commits:**
```python
for pub in pubs:
    insert(pub)
    conn.commit()  # 535x slower than batch!
```

**❌ Trusting API ID for deduplication:**
```python
# API can return same content with different IDs
pub_id = item['id']  # UNRELIABLE
```

**❌ Case-sensitive type filtering:**
```python
if pub['tipo'] == 'Acórdão':  # Fails with 'ACÓRDÃO'
```

**❌ Ignoring rate limits:**
```python
# Burst requests without adaptive limiting = HTTP 429
for i in range(1000):
    api.get(...)  # Will get blocked
```

## Troubleshooting Checklist

Before asking for help, verify:

- [ ] Read `references/known-issues.md` for documented problems
- [ ] Checked API signature (no `offset` parameter)
- [ ] Rate limiting enabled (`adaptive_rate_limit=True`)
- [ ] Using batch commits (`BATCH_SIZE = 100`)
- [ ] Normalizing types before comparison
- [ ] Using hash for deduplication (not API ID)
- [ ] Testing with recent dates (<30 days)
- [ ] Logs set to appropriate level (DEBUG for troubleshooting)

## Resources

### scripts/
- `diagnostic.py` - Performance profiling and bottleneck analysis
- `example_download.py` - Complete example of API integration
- `example_rag.py` - RAG search implementation example

### references/
- `known-issues.md` - Complete list of API quirks and pitfalls
- `schema.md` - SQLite database schema with indexes and triggers
- `api-reference.md` - DJEN API documentation and examples
- `architecture.md` - System architecture overview

### assets/
- None (this skill is code/documentation-focused)

## Additional Notes

**Environment Setup:**
- Always use virtual environment (`.venv/`)
- Python 3.12+ recommended
- Node.js 18+ for MCP server
- Visual Studio Build Tools required (Windows) for `better-sqlite3`

**Data Storage:**
- Code: `~/claude-work/repos/Claude-Code-Projetos/`
- Data: External drive recommended (E:\ or ~/claude-code-data/)
- Separation critical (see CLAUDE.md for disaster history)

**Legal Themes Supported:**
1. Direito Civil
2. Direito Penal
3. Direito Trabalhista
4. Direito Tributário
5. Direito Administrativo
6. Direito Constitucional
7. Direito Processual Civil
8. Direito Processual Penal
9. Responsabilidade Civil
10. Contratos
11. Família e Sucessões
12. Consumidor
13. Propriedade Intelectual

**When in Doubt:**
- Consult `references/known-issues.md` FIRST
- Run `scripts/diagnostic.py` for performance issues
- Check agent README files for specific features
- Review CLAUDE.md for project architecture guidelines
