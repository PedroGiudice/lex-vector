# SQLite Database Schema - Legal Data System

**Based on:** `docs/ARQUITETURA_JURISPRUDENCIA.md`
**Last Updated:** 2025-11-23

---

## Complete Schema

```sql
-- ============================================================================
-- MAIN TABLE: Legal Publications
-- ============================================================================
CREATE TABLE publicacoes (
    -- Identifiers
    id                  TEXT PRIMARY KEY,           -- UUID v4
    hash_conteudo       TEXT NOT NULL UNIQUE,       -- SHA256 of text (deduplication)

    -- Case data
    numero_processo     TEXT,                       -- CNJ format (no mask)
    numero_processo_fmt TEXT,                       -- With mask
    tribunal            TEXT NOT NULL,              -- STJ, TJSP, TRF3, etc
    orgao_julgador      TEXT,                       -- Chamber, Panel, Court

    -- Classification
    tipo_publicacao     TEXT NOT NULL,              -- Acórdão, Sentença, Decisão, Intimação
    classe_processual   TEXT,                       -- Apelação, REsp, AgRg, etc
    assuntos            TEXT,                       -- JSON array of subjects

    -- Content
    texto_html          TEXT NOT NULL,              -- Original DJEN HTML
    texto_limpo         TEXT NOT NULL,              -- Text without HTML tags
    ementa              TEXT,                       -- Extracted ementa (if applicable)

    -- Metadata
    data_publicacao     TEXT NOT NULL,              -- ISO 8601 (YYYY-MM-DD)
    data_julgamento     TEXT,                       -- Judgment date (may be earlier)
    relator             TEXT,                       -- Name of rapporteur/judge

    -- Control
    data_insercao       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao    TEXT,
    fonte               TEXT NOT NULL,              -- 'DJEN', 'caderno-PDF'

    -- Full-text search
    texto_fts           TEXT                        -- Text optimized for FTS5
);

-- Performance indexes
CREATE INDEX idx_publicacoes_processo ON publicacoes(numero_processo);
CREATE INDEX idx_publicacoes_tribunal ON publicacoes(tribunal);
CREATE INDEX idx_publicacoes_data_pub ON publicacoes(data_publicacao);
CREATE INDEX idx_publicacoes_tipo ON publicacoes(tipo_publicacao);
CREATE INDEX idx_publicacoes_hash ON publicacoes(hash_conteudo);

-- ============================================================================
-- FULL-TEXT SEARCH (FTS5)
-- ============================================================================
CREATE VIRTUAL TABLE publicacoes_fts USING fts5(
    texto_limpo,
    ementa,
    assuntos,
    content='publicacoes',
    content_rowid='rowid'
);

-- Triggers to keep FTS synchronized
CREATE TRIGGER publicacoes_ai AFTER INSERT ON publicacoes BEGIN
    INSERT INTO publicacoes_fts(rowid, texto_limpo, ementa, assuntos)
    VALUES (new.rowid, new.texto_limpo, new.ementa, new.assuntos);
END;

CREATE TRIGGER publicacoes_ad AFTER DELETE ON publicacoes BEGIN
    DELETE FROM publicacoes_fts WHERE rowid = old.rowid;
END;

CREATE TRIGGER publicacoes_au AFTER UPDATE ON publicacoes BEGIN
    UPDATE publicacoes_fts SET
        texto_limpo = new.texto_limpo,
        ementa = new.ementa,
        assuntos = new.assuntos
    WHERE rowid = new.rowid;
END;

-- ============================================================================
-- TABLE: Embeddings (RAG/Semantic Search)
-- ============================================================================
CREATE TABLE embeddings (
    publicacao_id       TEXT PRIMARY KEY,
    embedding           BLOB NOT NULL,              -- Float32Array serialized
    dimensao            INTEGER NOT NULL,           -- 384 (multilingual-e5-small)
    modelo              TEXT NOT NULL,              -- Model name used
    versao_modelo       TEXT,
    data_criacao        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id) ON DELETE CASCADE
);

CREATE INDEX idx_embeddings_modelo ON embeddings(modelo);

-- ============================================================================
-- TABLE: Chunks (for long texts)
-- ============================================================================
CREATE TABLE chunks (
    id                  TEXT PRIMARY KEY,
    publicacao_id       TEXT NOT NULL,
    chunk_index         INTEGER NOT NULL,           -- Chunk position (0, 1, 2...)
    texto               TEXT NOT NULL,              -- Chunk text
    tamanho_tokens      INTEGER,                    -- Approx. tokens

    FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id) ON DELETE CASCADE
);

CREATE INDEX idx_chunks_publicacao ON chunks(publicacao_id);

CREATE TABLE chunks_embeddings (
    chunk_id            TEXT PRIMARY KEY,
    embedding           BLOB NOT NULL,
    dimensao            INTEGER NOT NULL,
    modelo              TEXT NOT NULL,
    data_criacao        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);

-- ============================================================================
-- TABLE: Download Metadata
-- ============================================================================
CREATE TABLE downloads_historico (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tribunal            TEXT NOT NULL,
    data_publicacao     TEXT NOT NULL,              -- Caderno date
    tipo_download       TEXT NOT NULL,              -- 'api' or 'caderno-pdf'
    total_publicacoes   INTEGER,
    total_novas         INTEGER,
    total_duplicadas    INTEGER,
    tempo_processamento REAL,                       -- Seconds
    status              TEXT NOT NULL,              -- 'sucesso', 'falha', 'parcial'
    erro                TEXT,
    data_execucao       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(tribunal, data_publicacao, tipo_download, data_execucao)
);

CREATE INDEX idx_downloads_data ON downloads_historico(data_execucao);
CREATE INDEX idx_downloads_tribunal_data ON downloads_historico(tribunal, data_publicacao);

-- ============================================================================
-- TABLE: Themes/Categories (for organization)
-- ============================================================================
CREATE TABLE temas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                TEXT NOT NULL UNIQUE,
    descricao           TEXT,
    palavras_chave      TEXT,                       -- JSON array
    total_publicacoes   INTEGER DEFAULT 0
);

CREATE TABLE publicacoes_temas (
    publicacao_id       TEXT NOT NULL,
    tema_id             INTEGER NOT NULL,
    relevancia          REAL DEFAULT 1.0,           -- 0.0 to 1.0

    PRIMARY KEY (publicacao_id, tema_id),
    FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (tema_id) REFERENCES temas(id) ON DELETE CASCADE
);

CREATE INDEX idx_pub_temas_tema ON publicacoes_temas(tema_id);

-- ============================================================================
-- USEFUL VIEWS
-- ============================================================================

-- General statistics
CREATE VIEW v_stats AS
SELECT
    COUNT(*) AS total_publicacoes,
    COUNT(DISTINCT tribunal) AS tribunais_unicos,
    COUNT(DISTINCT numero_processo) AS processos_unicos,
    MIN(data_publicacao) AS data_mais_antiga,
    MAX(data_publicacao) AS data_mais_recente
FROM publicacoes;

-- Publications by tribunal
CREATE VIEW v_publicacoes_por_tribunal AS
SELECT
    tribunal,
    COUNT(*) AS total,
    COUNT(CASE WHEN tipo_publicacao = 'Acórdão' THEN 1 END) AS acordaos,
    COUNT(CASE WHEN tipo_publicacao = 'Sentença' THEN 1 END) AS sentencas,
    COUNT(CASE WHEN tipo_publicacao = 'Decisão' THEN 1 END) AS decisoes,
    MIN(data_publicacao) AS primeira_publicacao,
    MAX(data_publicacao) AS ultima_publicacao
FROM publicacoes
GROUP BY tribunal
ORDER BY total DESC;

-- Recent publications (last 30 days)
CREATE VIEW v_publicacoes_recentes AS
SELECT
    id,
    numero_processo_fmt,
    tribunal,
    tipo_publicacao,
    LEFT(texto_limpo, 200) AS preview,
    data_publicacao
FROM publicacoes
WHERE date(data_publicacao) >= date('now', '-30 days')
ORDER BY data_publicacao DESC;
```

---

## Usage Examples

### Insert Publication

```python
import sqlite3
import hashlib
import uuid

def inserir_publicacao(db, publicacao: Dict) -> bool:
    """
    Inserts publication if it doesn't exist (via hash).

    Returns:
        True if new insertion, False if duplicate
    """
    cursor = db.cursor()

    try:
        cursor.execute("""
        INSERT INTO publicacoes (
            id, hash_conteudo, numero_processo, numero_processo_fmt,
            tribunal, orgao_julgador, tipo_publicacao, classe_processual,
            texto_html, texto_limpo, ementa, data_publicacao, relator, fonte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            publicacao['hash_conteudo'],
            publicacao['numero_processo'],
            publicacao['numero_processo_fmt'],
            publicacao['tribunal'],
            publicacao['orgao_julgador'],
            publicacao['tipo_publicacao'],
            publicacao['classe_processual'],
            publicacao['texto_html'],
            publicacao['texto_limpo'],
            publicacao['ementa'],
            publicacao['data_publicacao'],
            publicacao['relator'],
            publicacao['fonte']
        ))
        db.commit()
        return True

    except sqlite3.IntegrityError:
        # Hash already exists - duplicate
        return False
```

### Full-Text Search

```python
def buscar_full_text(db, query: str, limit: int = 50):
    cursor = db.cursor()

    cursor.execute("""
    SELECT
        p.id,
        p.numero_processo_fmt,
        p.tribunal,
        p.tipo_publicacao,
        p.ementa,
        snippet(publicacoes_fts, 0, '<mark>', '</mark>', '...', 64) AS snippet,
        p.data_publicacao,
        rank
    FROM publicacoes_fts
    JOIN publicacoes p ON publicacoes_fts.rowid = p.rowid
    WHERE publicacoes_fts MATCH ?
    ORDER BY rank
    LIMIT ?
    """, (query, limit))

    return cursor.fetchall()
```

### Semantic Search (RAG)

```python
import numpy as np

def buscar_similares(db, query_embedding, threshold=0.7, top_k=10):
    cursor = db.cursor()

    cursor.execute("""
    SELECT
        e.publicacao_id,
        e.embedding,
        p.numero_processo_fmt,
        p.tribunal,
        p.tipo_publicacao,
        p.ementa
    FROM embeddings e
    JOIN publicacoes p ON e.publicacao_id = p.id
    """)

    results = []
    for row in cursor.fetchall():
        embedding = np.frombuffer(row['embedding'], dtype=np.float32)

        # Cosine similarity
        similarity = np.dot(query_embedding, embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
        )

        if similarity >= threshold:
            results.append({
                'id': row['publicacao_id'],
                'similarity': float(similarity),
                'processo': row['numero_processo_fmt'],
                'tribunal': row['tribunal'],
                'tipo': row['tipo_publicacao'],
                'ementa': row['ementa']
            })

    # Sort by similarity
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]
```

### Statistics Report

```python
def gerar_estatisticas(db):
    cursor = db.cursor()

    # Overall stats
    cursor.execute("SELECT * FROM v_stats")
    stats = cursor.fetchone()

    print(f"Total publications: {stats['total_publicacoes']}")
    print(f"Unique tribunals: {stats['tribunais_unicos']}")
    print(f"Unique cases: {stats['processos_unicos']}")
    print(f"Date range: {stats['data_mais_antiga']} to {stats['data_mais_recente']}")

    # By tribunal
    print("\nPublications by tribunal:")
    cursor.execute("SELECT * FROM v_publicacoes_por_tribunal")
    for row in cursor.fetchall():
        print(f"  {row['tribunal']:8} | Total: {row['total']:6} | "
              f"Acórdãos: {row['acordaos']:4} | Sentenças: {row['sentencas']:4}")
```

---

## Storage Estimates

### Per Publication
- HTML text: ~5 KB
- Clean text: ~3 KB
- Embedding (768 dim): 3 KB
- Metadata: 1 KB
- **Total: ~12 KB per publication**

### Per Tribunal/Day
- **STJ:** ~1,000 publications/day = 12 MB
- **TJSP:** ~5,000 publications/day = 60 MB
- **Total (15 tribunals):** ~200 MB/day

### Annual
- **Total:** 200 MB × 365 days = **~73 GB/year**
- **With indexes:** ~100 GB/year
- **Feasible:** 1 TB external HD holds ~10 years

---

## Optimization Tips

1. **Use WAL mode** for better write concurrency:
   ```sql
   PRAGMA journal_mode=WAL;
   ```

2. **Batch commits** (535x speedup):
   ```python
   BATCH_SIZE = 100
   for i, pub in enumerate(pubs, 1):
       insert(pub)
       if i % BATCH_SIZE == 0:
           conn.commit()
   conn.commit()
   ```

3. **Analyze periodically** for query optimization:
   ```sql
   ANALYZE;
   ```

4. **Vacuum occasionally** to reclaim space:
   ```sql
   VACUUM;
   ```

---

## Migrations

When schema changes are needed:

```python
def migrate_v1_to_v2(db):
    cursor = db.cursor()

    # Add new column
    cursor.execute("ALTER TABLE publicacoes ADD COLUMN nova_coluna TEXT")

    # Update version
    cursor.execute("PRAGMA user_version = 2")

    db.commit()
```

---

**Reference:** See `docs/ARQUITETURA_JURISPRUDENCIA.md` for complete architectural documentation.
