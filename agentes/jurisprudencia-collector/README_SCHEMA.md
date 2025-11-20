# Schema do Banco de Dados de Jurisprudência

## Visão Geral

Sistema de armazenamento local/offline de publicações jurídicas brasileiras (acórdãos, sentenças, decisões) com suporte a:

- **Busca textual rápida** (FTS5 - Full-Text Search)
- **Busca semântica** (RAG - Retrieval-Augmented Generation via embeddings)
- **Deduplicação automática** (SHA256 hash)
- **Atualização incremental** (scheduler diário)

**Fonte de dados:** DJEN (Diário de Justiça Eletrônico Nacional)
**SGBD:** SQLite 3.x
**Capacidade estimada:** ~73 GB/ano (15 tribunais)

---

## Estrutura do Schema

### Tabelas Principais

| Tabela | Descrição | Registros Estimados |
|--------|-----------|---------------------|
| `publicacoes` | Textos completos de publicações | ~500k/ano |
| `embeddings` | Vetores semânticos (768 dim) | ~500k/ano |
| `chunks` | Segmentos de textos longos | Variável |
| `publicacoes_fts` | Índice FTS5 (busca textual) | Automático |
| `temas` | Categorias jurídicas | ~50 |
| `downloads_historico` | Log de atualizações | ~5.5k/ano |

### Views Úteis

- `v_stats` - Estatísticas gerais
- `v_publicacoes_por_tribunal` - Distribuição por tribunal
- `v_publicacoes_recentes` - Últimos 30 dias
- `v_downloads_resumo` - Resumo de downloads (7 dias)
- `v_temas_ranking` - Temas mais frequentes

---

## Instalação

### 1. Criar Banco de Dados

```bash
cd agentes/jurisprudencia-collector
sqlite3 jurisprudencia.db < schema.sql
```

### 2. Validar Schema

```bash
python3 validate_schema.py
```

**Saída esperada:**
```
✅ SCHEMA VÁLIDO!
📊 TABELAS (13)
👁️  VIEWS (5)
🔍 ÍNDICES (20)
⚡ TRIGGERS (5)
✅ TODOS OS TESTES PASSARAM!
```

### 3. Executar Exemplo de Uso

```bash
python3 example_usage.py
```

Cria banco de exemplo (`jurisprudencia_exemplo.db`) com:
- 1 publicação (acórdão STJ)
- Busca FTS5 demonstrativa
- Estatísticas completas

---

## Uso Básico

### Inserir Publicação

```python
import sqlite3
import hashlib
import uuid

conn = sqlite3.connect('jurisprudencia.db')
cursor = conn.cursor()

# Dados da publicação
texto_limpo = "Texto completo da decisão..."
hash_conteudo = hashlib.sha256(texto_limpo.encode()).hexdigest()

cursor.execute("""
    INSERT INTO publicacoes (
        id, hash_conteudo, tribunal, tipo_publicacao,
        texto_html, texto_limpo, data_publicacao, fonte
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    str(uuid.uuid4()),
    hash_conteudo,
    'STJ',
    'Acórdão',
    '<p>HTML original...</p>',
    texto_limpo,
    '2025-11-20',
    'DJEN'
))

conn.commit()
conn.close()
```

### Buscar por FTS5 (Busca Textual)

```python
cursor.execute("""
    SELECT
        p.numero_processo_fmt,
        p.tribunal,
        p.ementa,
        snippet(publicacoes_fts, 0, '<mark>', '</mark>', '...', 64) AS snippet
    FROM publicacoes_fts
    JOIN publicacoes p ON publicacoes_fts.rowid = p.rowid
    WHERE publicacoes_fts MATCH 'responsabilidade civil'
    ORDER BY rank
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"Processo: {row[0]}")
    print(f"Snippet: {row[3]}\n")
```

### Buscar por Similaridade Semântica (RAG)

```python
# 1. Gerar embedding da query
query = "contratos de compra e venda com defeito no produto"
query_embedding = embedder.gerar_embedding(query)

# 2. Buscar embeddings similares no banco
cursor.execute("SELECT publicacao_id, embedding FROM embeddings")

resultados = []
for pub_id, emb_bytes in cursor.fetchall():
    embedding = np.frombuffer(emb_bytes, dtype=np.float32)

    # Similaridade de cosseno
    similarity = np.dot(query_embedding, embedding) / (
        np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
    )

    if similarity > 0.7:  # Threshold
        resultados.append((pub_id, similarity))

# 3. Ordenar por similaridade
resultados.sort(key=lambda x: x[1], reverse=True)
```

### Consultar Estatísticas

```sql
-- Estatísticas gerais
SELECT * FROM v_stats;

-- Publicações por tribunal
SELECT * FROM v_publicacoes_por_tribunal;

-- Publicações recentes (30 dias)
SELECT * FROM v_publicacoes_recentes LIMIT 20;

-- Temas mais frequentes
SELECT * FROM v_temas_ranking LIMIT 10;
```

---

## Otimizações de Performance

### Configurações Aplicadas

```sql
PRAGMA journal_mode = WAL;              -- Write-Ahead Logging
PRAGMA synchronous = NORMAL;            -- Balanço performance/segurança
PRAGMA cache_size = -64000;             -- Cache de 64MB
PRAGMA temp_store = MEMORY;             -- Ops temporárias em RAM
PRAGMA mmap_size = 30000000000;         -- Memory-mapped I/O (30GB)
```

### Índices Criados

- **Busca por processo:** `idx_publicacoes_processo`
- **Filtro por tribunal:** `idx_publicacoes_tribunal`
- **Ordenação por data:** `idx_publicacoes_data_pub` (DESC)
- **Filtro por tipo:** `idx_publicacoes_tipo`
- **Deduplicação:** `idx_publicacoes_hash`
- **Composto:** `idx_publicacoes_tribunal_data_tipo`

### Quando Otimizar

```sql
-- Após muitas inserções/deleções
VACUUM;

-- Atualizar estatísticas de índices
ANALYZE;

-- Verificar integridade
PRAGMA integrity_check;
```

---

## Deduplicação

O schema impede duplicatas usando **hash SHA256** do texto limpo:

```python
hash_conteudo = hashlib.sha256(texto_limpo.encode()).hexdigest()

try:
    cursor.execute("INSERT INTO publicacoes (..., hash_conteudo, ...) VALUES (...)")
    print("✅ Nova publicação inserida")
except sqlite3.IntegrityError:
    print("⚠️  Publicação duplicada (hash já existe)")
```

**Constraint:** `UNIQUE(hash_conteudo)`

---

## Busca Full-Text (FTS5)

### Sintaxe de Busca

```sql
-- Busca simples
WHERE publicacoes_fts MATCH 'responsabilidade civil'

-- Operadores booleanos
WHERE publicacoes_fts MATCH 'responsabilidade AND civil'
WHERE publicacoes_fts MATCH 'responsabilidade OR contrato'
WHERE publicacoes_fts MATCH 'responsabilidade NOT penal'

-- Frase exata
WHERE publicacoes_fts MATCH '"dano moral"'

-- Proximidade (palavras próximas)
WHERE publicacoes_fts MATCH 'NEAR(responsabilidade civil, 10)'

-- Prefixo
WHERE publicacoes_fts MATCH 'responsab*'
```

### Snippet (Destacar Termos)

```sql
SELECT snippet(publicacoes_fts, 0, '<mark>', '</mark>', '...', 64) AS snippet
```

**Parâmetros:**
- `0` - Coluna (0 = texto_limpo)
- `<mark>` - Tag de abertura
- `</mark>` - Tag de fechamento
- `'...'` - Elipse
- `64` - Tokens ao redor

---

## Triggers Automáticos

### Sincronização FTS5

Mantém `publicacoes_fts` sincronizado com `publicacoes`:

```sql
-- Após INSERT
CREATE TRIGGER publicacoes_ai AFTER INSERT ON publicacoes BEGIN
    INSERT INTO publicacoes_fts(rowid, texto_limpo, ementa, assuntos)
    VALUES (new.rowid, new.texto_limpo, new.ementa, new.assuntos);
END;

-- Após DELETE
CREATE TRIGGER publicacoes_ad AFTER DELETE ON publicacoes BEGIN
    DELETE FROM publicacoes_fts WHERE rowid = old.rowid;
END;

-- Após UPDATE
CREATE TRIGGER publicacoes_au AFTER UPDATE ON publicacoes BEGIN
    UPDATE publicacoes_fts SET ... WHERE rowid = new.rowid;
END;
```

### Atualização de Contadores

Atualiza `temas.total_publicacoes` automaticamente:

```sql
-- Incrementar ao associar tema
CREATE TRIGGER temas_incrementar AFTER INSERT ON publicacoes_temas BEGIN
    UPDATE temas SET total_publicacoes = total_publicacoes + 1 WHERE id = new.tema_id;
END;

-- Decrementar ao remover tema
CREATE TRIGGER temas_decrementar AFTER DELETE ON publicacoes_temas BEGIN
    UPDATE temas SET total_publicacoes = total_publicacoes - 1 WHERE id = old.tema_id;
END;
```

---

## Estimativa de Armazenamento

### Por Publicação

| Componente | Tamanho |
|------------|---------|
| Texto HTML | ~5 KB |
| Texto limpo | ~3 KB |
| Embedding (768 dim) | 3 KB |
| Metadados | 1 KB |
| **Total** | **~12 KB** |

### Por Tribunal/Dia

| Tribunal | Publicações/dia | Tamanho/dia |
|----------|-----------------|-------------|
| STJ | ~1.000 | 12 MB |
| TJSP | ~5.000 | 60 MB |
| **Total (15 tribunais)** | **~16.500** | **~200 MB** |

### Anual

- **Total:** 200 MB × 365 dias = **~73 GB/ano**
- **Com índices:** ~100 GB/ano
- **HD 1 TB:** comporta ~10 anos de histórico

---

## Manutenção

### Backup

```bash
# Backup completo
sqlite3 jurisprudencia.db ".backup jurisprudencia_backup.db"

# Dump SQL
sqlite3 jurisprudencia.db ".dump" | gzip > backup.sql.gz
```

### Verificar Integridade

```sql
PRAGMA integrity_check;        -- Verificar corrupção
PRAGMA foreign_key_check;      -- Verificar FKs órfãs
```

### Compactar Banco

```sql
VACUUM;  -- Remove espaço não utilizado (pode demorar)
```

### Estatísticas de Tabelas

```sql
-- Tamanho de cada tabela
SELECT
    name,
    SUM(pgsize) / 1024 / 1024 AS size_mb
FROM dbstat
WHERE name IN ('publicacoes', 'embeddings', 'publicacoes_fts')
GROUP BY name;
```

---

## Segurança

### Proteção contra SQL Injection

**Sempre use parâmetros:**

```python
# ✅ CORRETO
cursor.execute("SELECT * FROM publicacoes WHERE tribunal = ?", (tribunal,))

# ❌ ERRADO (SQL Injection)
cursor.execute(f"SELECT * FROM publicacoes WHERE tribunal = '{tribunal}'")
```

### Validação de Constraints

O schema inclui constraints para validar dados:

```sql
CHECK (length(id) = 36)                 -- UUID válido
CHECK (length(hash_conteudo) = 64)      -- SHA256 válido
CHECK (tribunal IN ('STF', 'STJ', ...)) -- Tribunal conhecido
CHECK (tipo_publicacao IN (...))        -- Tipo válido
```

---

## Temas Pré-definidos

O schema inicializa com 10 temas do Direito Brasileiro:

1. **Direito Civil** - Relações entre particulares
2. **Direito Penal** - Crimes e penas
3. **Direito Processual Civil** - Processo civil
4. **Direito Processual Penal** - Processo penal
5. **Direito do Trabalho** - Relações trabalhistas
6. **Direito Tributário** - Tributos e impostos
7. **Direito Administrativo** - Administração Pública
8. **Direito Constitucional** - Constituição Federal
9. **Direito do Consumidor** - Relações de consumo
10. **Direito Empresarial** - Empresas e sociedades

---

## Troubleshooting

### Problema: FTS5 não encontra resultados

```sql
-- Verificar se FTS5 está populado
SELECT COUNT(*) FROM publicacoes_fts;

-- Reindexar (se necessário)
INSERT INTO publicacoes_fts(publicacoes_fts) VALUES('rebuild');
```

### Problema: Foreign key constraint failed

```sql
-- Verificar se FK está habilitada
PRAGMA foreign_keys;  -- Deve retornar 1

-- Habilitar FK (necessário em cada conexão)
PRAGMA foreign_keys = ON;
```

### Problema: Banco muito lento

```sql
-- Analisar estatísticas
ANALYZE;

-- Verificar configuração
PRAGMA journal_mode;     -- Deve ser WAL
PRAGMA cache_size;       -- Deve ser negativo (KB)
```

---

## Referências

- **Especificação completa:** `docs/ARQUITETURA_JURISPRUDENCIA.md`
- **SQLite FTS5:** https://www.sqlite.org/fts5.html
- **SQLite Triggers:** https://www.sqlite.org/lang_createtrigger.html
- **Python sqlite3:** https://docs.python.org/3/library/sqlite3.html

---

**Última atualização:** 2025-11-20
**Autor:** Claude Code (Sonnet 4.5)
