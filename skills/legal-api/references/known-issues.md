# Known Issues - API DJEN (CNJ)

**Last Updated:** 2025-11-23
**Source:** Based on agentes/jurisprudencia-collector/KNOWN_ISSUES_API_DJEN.md and agentes/legal-lens/DJEN_API_ISSUES.md

---

## ⚠️ CRITICAL - Read Before Writing API Code

This document contains **lessons learned** from real errors made during development. **Always consult this file** before writing code that interacts with the DJEN API.

---

## 1. Paginação Automática - NO `offset` Parameter

### ❌ COMMON ERROR:
```python
# ❌ WRONG - offset does not exist!
publicacoes = downloader.baixar_api(
    tribunal='STJ',
    data='2025-11-20',
    limit=100,
    offset=200  # TypeError: unexpected keyword argument 'offset'
)
```

### ✅ CORRECT:
```python
# ✅ CORRECT - automatic pagination with max_pages
publicacoes = downloader.baixar_api(
    tribunal='STJ',
    data='2025-11-20',
    limit=100,
    max_pages=10  # Limits to 10 pages (optional)
)
```

### 📝 Explanation:
- The `baixar_api()` method already performs automatic pagination internally
- Iterates `page=1, 2, 3...` in the URL until no more results
- **Does NOT accept** `offset` parameter (SQL-style)
- Use `max_pages` to limit how many pages to download

### 🔍 Correct Signature:
```python
def baixar_api(
    self,
    tribunal: str,
    data: str,
    limit: int = 100,
    max_pages: Optional[int] = None
) -> List[PublicacaoRaw]
```

**Source:** `agentes/jurisprudencia-collector/src/downloader.py:209-215`

---

## 2. OAB Filter Does NOT Work

### ⚠️ CRITICAL ISSUE:

The DJEN API has a **filtering bug** that returns **ALL documents** from the period, ignoring OAB number or lawyer name filters.

### Affected Endpoints:
```
GET /api/v1/comunicacao
```

### Expected Behavior:
```http
GET /api/v1/comunicacao?numeroOab=129021&ufOab=SP&dataInicio=2025-01-01&dataFim=2025-01-31
```

**Should return:** Only publications related to OAB 129021/SP

### Actual Behavior:
**Returns:** ALL publications from the period (2025-01-01 to 2025-01-31), regardless of OAB number

### Impact:
- **Data volume:** Downloads hundreds of MB instead of KB
- **Performance:** Queries 100-1000x slower
- **Manual filtering:** Must process all documents locally
- **Costs:** Unnecessary bandwidth

### Evidence:

**Test 1: Search for specific OAB**
```bash
curl "https://comunicaapi.pje.jus.br/api/v1/comunicacao?numeroOab=129021&ufOab=SP&dataInicio=2025-01-07&dataFim=2025-01-07&siglaTribunal=TJSP"
```
**Result:** 15,432 publications (ALL from the day, not just OAB 129021/SP)

**Test 2: Search without OAB filter**
```bash
curl "https://comunicaapi.pje.jus.br/api/v1/comunicacao?dataInicio=2025-01-07&dataFim=2025-01-07&siglaTribunal=TJSP"
```
**Result:** 15,432 publications (SAME RESULT!)

### Conclusion:
The `numeroOab` parameter is **ignored** by the API.

### Workarounds:

**Option 1: Local Filtering (djen-tracker)**
```python
# Download ALL documents and filter locally
response = api_client.get('/api/v1/comunicacao', params={
    'dataInicio': data_inicio,
    'dataFim': data_fim,
    'siglaTribunal': tribunal
    # numeroOab is removed because it doesn't work
})

# Filter locally
items_filtrados = [
    item for item in response['items']
    if numero_oab in item.get('advogados', [])
]
```

**Option 2: RAG Semantic Search (legal-lens)**
```python
# Index ALL documents in vector database
all_chunks = pdf_processor.batch_process_pdfs(all_pdfs)
rag_engine.add_documents(all_chunks)

# Search semantically by OAB or theme
results = rag_engine.search(
    query="OAB 129021/SP advogado João Silva",
    top_k=50
)
```

**Source:** `agentes/legal-lens/DJEN_API_ISSUES.md`

---

## 3. Rate Limiting - Sliding Window (21 req/window)

### ⚠️ REAL API LIMIT:
- **21 requests** per ~5-second window
- HTTP 429 after exceeding
- Header `Retry-After: 2` indicates wait time

### ❌ COMMON ERROR:
```python
# ❌ WRONG - Fixed delay doesn't respect window
time.sleep(2)  # Too simplistic, doesn't work at high rate
```

### ✅ CORRECT:
```python
# ✅ CORRECT - Adaptive rate limiting (implemented)
downloader = DJENDownloader(
    data_root=DATA_ROOT,
    requests_per_minute=144,  # Sustainable rate (12 req/5s)
    adaptive_rate_limit=True  # Sliding window automatic
)
```

### 📝 Explanation:
- API uses **sliding window**, not fixed counter
- 21 requests in 5s → HTTP 429
- Current system uses conservative buffer (12 req/5s) for reliability
- Automatic retry with `Retry-After` header

**Source:** `agentes/jurisprudencia-collector/diagnostico_performance.py:196-207`

---

## 4. Database - N+1 Problem with Commits

### ❌ COMMON ERROR:
```python
# ❌ WRONG - Commit on each INSERT (535x slower!)
for pub in publicacoes:
    inserir_publicacao(conn, pub)
    conn.commit()  # N+1 commits = VERY SLOW
```

### ✅ CORRECT:
```python
# ✅ CORRECT - Batch commits (implemented)
BATCH_SIZE = 100
for i, pub in enumerate(publicacoes, start=1):
    inserir_publicacao(conn, pub)

    if i % BATCH_SIZE == 0:
        conn.commit()  # Commit every 100

conn.commit()  # Final commit
```

### 📝 Explanation:
- SQLite is single-writer, each commit does fsync to disk
- Individual commit: 117 writes/sec
- Batch commits (100): 62,894 writes/sec (**535x speedup**)

**Source:** `agentes/jurisprudencia-collector/diagnostico_performance.py:64-79`

---

## 5. Deduplication - SHA256 Hash (not API ID)

### ⚠️ IMPORTANT:
API can return same publication with different IDs in subsequent requests.

### ❌ COMMON ERROR:
```python
# ❌ WRONG - API ID doesn't guarantee uniqueness
pub_id = item['id']  # Can change between requests
```

### ✅ CORRECT:
```python
# ✅ CORRECT - Hash of content (implemented)
import hashlib
hash_conteudo = hashlib.sha256(texto_html.encode()).hexdigest()
```

### 📝 Explanation:
- Hash of `texto_html` guarantees real uniqueness
- Detects republications (same content, different ID)
- UNIQUE index in DB: `CREATE UNIQUE INDEX idx_hash ON publicacoes(hash_conteudo)`

**Source:** `agentes/jurisprudencia-collector/src/downloader.py:_gerar_hash()`

---

## 6. Timeout and Retry - Exponential Backoff

### ❌ COMMON ERROR:
```python
# ❌ WRONG - Fixed retry without backoff
for i in range(3):
    try:
        response = requests.get(url, timeout=5)
        break
    except Timeout:
        pass  # Immediate retry = worse
```

### ✅ CORRECT:
```python
# ✅ CORRECT - Exponential backoff (implemented)
for attempt in range(max_retries):
    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 2))
            time.sleep(retry_after)
            continue

        return response

    except Timeout:
        backoff = 2 ** attempt  # 1s, 2s, 4s
        time.sleep(backoff)
```

### 📝 Explanation:
- Short timeout (5s) causes unnecessary failures
- Immediate retry overloads API
- Exponential backoff: 1s → 2s → 4s
- HTTP 429: use `Retry-After` header

**Source:** `agentes/jurisprudencia-collector/src/downloader.py:_fazer_requisicao()`

---

## 7. Type Filter - Case-Insensitive and No Accents

### ⚠️ IMPORTANT:
API returns `tipo_publicacao` with variations:
- `"Acórdão"`, `"ACÓRDÃO"`, `"  Acórdão\n"`
- Direct comparison fails!

### ❌ COMMON ERROR:
```python
# ❌ WRONG - Case-sensitive and with accents
if pub['tipo_publicacao'] == 'Acórdão':  # Fails with 'ACÓRDÃO'
```

### ✅ CORRECT:
```python
# ✅ CORRECT - Normalization (implemented)
import unicodedata

def normalizar_tipo_publicacao(tipo: str) -> str:
    if not tipo:
        return ""
    # Remove accents
    sem_acentos = unicodedata.normalize('NFD', tipo)
    sem_acentos = ''.join(c for c in sem_acentos if unicodedata.category(c) != 'Mn')
    return sem_acentos.lower().strip()

# Comparison:
if normalizar_tipo_publicacao(pub['tipo_publicacao']) == 'acordao':
```

### 📝 Explanation:
- Normalizes: removes accents, lowercase, trim
- `'Acórdão'` → `'acordao'`
- `'ACÓRDÃO  '` → `'acordao'`
- Robust comparison

**Source:** `agentes/jurisprudencia-collector/scheduler.py:normalizar_tipo_publicacao()`

---

## 8. Test Data - Use Recent Dates

### ⚠️ IMPORTANT:
Old dates (>30 days) frequently return 0 publications.

### ❌ COMMON ERROR:
```python
# ❌ WRONG - Tests with old empty dates
data_teste = '2024-01-01'  # Probably empty
```

### ✅ CORRECT:
```python
# ✅ CORRECT - Tests with recent data
from datetime import datetime, timedelta
data_teste = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
```

### 📝 Explanation:
- API retains recent data with more consistency
- Tests with dates >30 days may return empty (not error)
- For profiling: vary last 20 days

---

## 📚 QUICK REFERENCES

| Concept | File | Function/Line |
|---------|------|--------------|
| `baixar_api()` signature | `src/downloader.py` | 209-215 |
| Adaptive rate limiting | `src/downloader.py` | `_check_rate_limit()` |
| Batch commits | `scheduler.py` | `processar_publicacoes()` |
| Type normalization | `scheduler.py` | `normalizar_tipo_publicacao()` |
| Hash deduplication | `src/downloader.py` | `_gerar_hash()` |
| HTTP 429 handling | `src/downloader.py` | `_fazer_requisicao()` |

---

## ✅ CHECKLIST - Before Modifying API Code

- [ ] Read this document completely
- [ ] Verified `baixar_api()` method signature
- [ ] NOT using `offset` parameter (does not exist!)
- [ ] Adaptive rate limiting is enabled
- [ ] Commits are batched (not individual)
- [ ] Retry has exponential backoff
- [ ] Type filters are normalized
- [ ] Tests use recent dates (<30 days)
- [ ] Logging uses appropriate levels

---

**Last Revision:** 2025-11-23
**Maintainer:** Development Team
**Contact:** See CLAUDE.md
