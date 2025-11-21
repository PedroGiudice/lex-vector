# Arquitetura de Base de Dados de Jurisprudência

## 📊 Sumário Executivo

Após investigação rigorosa das APIs públicas do CNJ, confirmamos:

**❌ DataJud NÃO permite:**
- Consulta por número de OAB
- Consulta por nome de advogado
- Acesso a textos completos de decisões/acórdãos

**✅ DJEN/PCP PERMITE:**
- Download de publicações completas em HTML
- Acesso a textos de acórdãos, sentenças e decisões
- Download de cadernos completos (PDF com TODAS as publicações do dia)
- Atualização diária automática

---

## 🎯 Nova Diretriz do Projeto

**FOCO:** Construir base de dados de jurisprudência local/offline com:
1. Download automático de publicações DJEN
2. Armazenamento estruturado em SQLite
3. Indexação semântica (RAG) para busca inteligente
4. Atualização incremental diária

**ABANDONAR:** Consulta por número de OAB (não viável com APIs públicas)

---

## 🏗️ Arquitetura Proposta

### Schema do Banco de Dados (SQLite)

```sql
-- ============================================================================
-- TABELA PRINCIPAL: Publicações jurídicas
-- ============================================================================
CREATE TABLE publicacoes (
    -- Identificadores
    id                  TEXT PRIMARY KEY,           -- UUID v4
    hash_conteudo       TEXT NOT NULL UNIQUE,       -- SHA256 do texto (deduplicação)

    -- Dados processuais
    numero_processo     TEXT,                       -- Formato CNJ (sem máscara)
    numero_processo_fmt TEXT,                       -- Com máscara
    tribunal            TEXT NOT NULL,              -- STJ, TJSP, TRF3, etc
    orgao_julgador      TEXT,                       -- Câmara, Turma, Vara

    -- Classificação
    tipo_publicacao     TEXT NOT NULL,              -- Acórdão, Sentença, Decisão, Intimação
    classe_processual   TEXT,                       -- Apelação, REsp, AgRg, etc
    assuntos            TEXT,                       -- JSON array de assuntos

    -- Conteúdo
    texto_html          TEXT NOT NULL,              -- HTML original do DJEN
    texto_limpo         TEXT NOT NULL,              -- Texto sem tags HTML
    ementa              TEXT,                       -- Ementa extraída (se aplicável)

    -- Metadados
    data_publicacao     TEXT NOT NULL,              -- ISO 8601 (YYYY-MM-DD)
    data_julgamento     TEXT,                       -- Data do julgamento (pode ser anterior)
    relator             TEXT,                       -- Nome do relator/juiz

    -- Controle
    data_insercao       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao    TEXT,
    fonte               TEXT NOT NULL,              -- 'DJEN', 'caderno-PDF'

    -- Full-text search
    texto_fts           TEXT                        -- Texto otimizado para FTS5
);

-- Índices para performance
CREATE INDEX idx_publicacoes_processo ON publicacoes(numero_processo);
CREATE INDEX idx_publicacoes_tribunal ON publicacoes(tribunal);
CREATE INDEX idx_publicacoes_data_pub ON publicacoes(data_publicacao);
CREATE INDEX idx_publicacoes_tipo ON publicacoes(tipo_publicacao);
CREATE INDEX idx_publicacoes_hash ON publicacoes(hash_conteudo);

-- Full-Text Search (FTS5)
CREATE VIRTUAL TABLE publicacoes_fts USING fts5(
    texto_limpo,
    ementa,
    assuntos,
    content='publicacoes',
    content_rowid='rowid'
);

-- Triggers para manter FTS sincronizado
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
-- TABELA: Embeddings (RAG/Busca Semântica)
-- ============================================================================
CREATE TABLE embeddings (
    publicacao_id       TEXT PRIMARY KEY,
    embedding           BLOB NOT NULL,              -- Float32Array serializado
    dimensao            INTEGER NOT NULL,           -- 384 (multilingual-e5-small)
    modelo              TEXT NOT NULL,              -- Nome do modelo usado
    versao_modelo       TEXT,
    data_criacao        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id) ON DELETE CASCADE
);

CREATE INDEX idx_embeddings_modelo ON embeddings(modelo);


-- ============================================================================
-- TABELA: Chunks (para textos longos)
-- ============================================================================
CREATE TABLE chunks (
    id                  TEXT PRIMARY KEY,
    publicacao_id       TEXT NOT NULL,
    chunk_index         INTEGER NOT NULL,           -- Posição do chunk (0, 1, 2...)
    texto               TEXT NOT NULL,              -- Texto do chunk
    tamanho_tokens      INTEGER,                    -- Aprox. tokens

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
-- TABELA: Metadados de Download
-- ============================================================================
CREATE TABLE downloads_historico (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tribunal            TEXT NOT NULL,
    data_publicacao     TEXT NOT NULL,              -- Data do caderno
    tipo_download       TEXT NOT NULL,              -- 'api' ou 'caderno-pdf'
    total_publicacoes   INTEGER,
    total_novas         INTEGER,
    total_duplicadas    INTEGER,
    tempo_processamento REAL,                       -- Segundos
    status              TEXT NOT NULL,              -- 'sucesso', 'falha', 'parcial'
    erro                TEXT,
    data_execucao       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(tribunal, data_publicacao, tipo_download, data_execucao)
);

CREATE INDEX idx_downloads_data ON downloads_historico(data_execucao);
CREATE INDEX idx_downloads_tribunal_data ON downloads_historico(tribunal, data_publicacao);


-- ============================================================================
-- TABELA: Temas/Categorias (para organização)
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
    relevancia          REAL DEFAULT 1.0,           -- 0.0 a 1.0

    PRIMARY KEY (publicacao_id, tema_id),
    FOREIGN KEY (publicacao_id) REFERENCES publicacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (tema_id) REFERENCES temas(id) ON DELETE CASCADE
);

CREATE INDEX idx_pub_temas_tema ON publicacoes_temas(tema_id);


-- ============================================================================
-- VIEWS úteis
-- ============================================================================

-- Estatísticas gerais
CREATE VIEW v_stats AS
SELECT
    COUNT(*) AS total_publicacoes,
    COUNT(DISTINCT tribunal) AS tribunais_unicos,
    COUNT(DISTINCT numero_processo) AS processos_unicos,
    MIN(data_publicacao) AS data_mais_antiga,
    MAX(data_publicacao) AS data_mais_recente
FROM publicacoes;

-- Publicações por tribunal
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

-- Publicações recentes (últimos 30 dias)
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

## 📥 Pipeline de Ingestão de Dados

### 1. Download Automático (Scheduler)

```python
# agentes/jurisprudencia-collector/scheduler.py

import schedule
import time
from datetime import datetime, timedelta
from src.downloader import DJENDownloader

def job_download_diario():
    """Executa download diário de todos os tribunais prioritários."""
    downloader = DJENDownloader(config)

    # Tribunais prioritários para jurisprudência
    tribunais = ['STJ', 'STF', 'TST', 'TJSP', 'TJRJ', 'TJMG', 'TRF3', 'TRF4']

    data_hoje = datetime.now().strftime('%Y-%m-%d')

    for tribunal in tribunais:
        try:
            # Baixar via API (mais rápido)
            publicacoes = downloader.baixar_api(tribunal, data_hoje)

            # Se API falhar ou retornar muito pouco, tentar caderno
            if not publicacoes or len(publicacoes) < 10:
                publicacoes = downloader.baixar_caderno(tribunal, data_hoje)

            # Processar e inserir no banco
            processar_publicacoes(publicacoes, tribunal, data_hoje)

        except Exception as e:
            logger.error(f"Erro ao processar {tribunal}: {e}")

# Agendar para rodar todo dia às 8h (depois das publicações)
schedule.every().day.at("08:00").do(job_download_diario)

# Executar imediatamente na primeira vez
job_download_diario()

# Loop infinito
while True:
    schedule.run_pending()
    time.sleep(60)
```

### 2. Processamento de Texto

```python
# src/processador_texto.py

import re
from bs4 import BeautifulSoup
from typing import Dict, Optional
import hashlib

def processar_publicacao(raw_data: Dict) -> Dict:
    """Processa HTML do DJEN e extrai informações estruturadas."""

    # Limpar HTML
    soup = BeautifulSoup(raw_data['texto'], 'html.parser')
    texto_limpo = soup.get_text(separator='\n', strip=True)

    # Gerar hash para deduplicação
    hash_conteudo = hashlib.sha256(texto_limpo.encode()).hexdigest()

    # Extrair ementa (se for acórdão)
    ementa = extrair_ementa(texto_limpo)

    # Detectar relator
    relator = extrair_relator(texto_limpo)

    # Classificar tipo
    tipo_publicacao = classificar_tipo(raw_data.get('tipoComunicacao'), texto_limpo)

    return {
        'id': generate_uuid(),
        'hash_conteudo': hash_conteudo,
        'numero_processo': raw_data.get('numero_processo'),
        'numero_processo_fmt': raw_data.get('numeroprocessocommascara'),
        'tribunal': raw_data.get('siglaTribunal'),
        'orgao_julgador': raw_data.get('nomeOrgao'),
        'tipo_publicacao': tipo_publicacao,
        'classe_processual': raw_data.get('nomeClasse'),
        'texto_html': raw_data['texto'],
        'texto_limpo': texto_limpo,
        'ementa': ementa,
        'data_publicacao': raw_data.get('data_disponibilizacao'),
        'relator': relator,
        'fonte': 'DJEN'
    }

def extrair_ementa(texto: str) -> Optional[str]:
    """Extrai ementa de acórdão usando regex."""
    patterns = [
        r'EMENTA\s*[:\-]?\s*(.+?)(?=ACÓRDÃO|VOTO|$)',
        r'E\s*M\s*E\s*N\s*T\s*A\s*[:\-]?\s*(.+?)(?=ACÓRDÃO|VOTO|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)
        if match:
            ementa = match.group(1).strip()
            # Limitar tamanho
            return ementa[:2000] if len(ementa) > 2000 else ementa

    return None

def extrair_relator(texto: str) -> Optional[str]:
    """Extrai nome do relator."""
    patterns = [
        r'RELATOR\s*[:\-]?\s*(.+?)(?=\n|REQUERENTE)',
        r'Rel\.\s*[:\-]?\s*(.+?)(?=\n)',
        r'MINISTRO\s+([A-ZÀ-Ú\s]+)',
        r'DESEMBARGADOR\s+([A-ZÀ-Ú\s]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:200]

    return None

def classificar_tipo(tipo_comunicacao: str, texto: str) -> str:
    """Classifica tipo de publicação baseado em heurísticas."""
    texto_lower = texto.lower()

    # Prioridade 1: Acórdão
    if 'acórdão' in texto_lower or 'acordão' in texto_lower:
        return 'Acórdão'

    # Prioridade 2: Sentença
    if 'sentença' in texto_lower:
        return 'Sentença'

    # Prioridade 3: Decisão
    if 'decisão' in texto_lower or tipo_comunicacao == 'Decisão':
        return 'Decisão'

    # Prioridade 4: Tipo original
    return tipo_comunicacao or 'Intimação'
```

### 3. Geração de Embeddings (RAG)

```python
# src/rag/embedder.py

from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from typing import List

class JurisprudenciaEmbedder:
    def __init__(self, model_name='neuralmind/bert-base-portuguese-cased'):
        """Modelo otimizado para português jurídico."""
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def gerar_embedding(self, texto: str, max_tokens=512) -> np.ndarray:
        """Gera embedding de texto."""
        # Tokenizar
        inputs = self.tokenizer(
            texto,
            max_length=max_tokens,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        # Gerar embedding
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Mean pooling
            embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

        return embedding

    def gerar_chunks(self, texto: str, chunk_size=500, overlap=50) -> List[str]:
        """Divide texto longo em chunks sobrepostos."""
        palavras = texto.split()
        chunks = []

        for i in range(0, len(palavras), chunk_size - overlap):
            chunk = ' '.join(palavras[i:i + chunk_size])
            if len(chunk) > 50:  # Ignorar chunks muito pequenos
                chunks.append(chunk)

        return chunks
```

### 4. Busca Semântica

```python
# src/rag/search.py

import numpy as np
from typing import List, Tuple
import sqlite3

class JurisprudenciaSearch:
    def __init__(self, db_path: str, embedder):
        self.db_path = db_path
        self.embedder = embedder

    def buscar_similares(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.7,
        filtros: dict = None
    ) -> List[Tuple[str, float, dict]]:
        """
        Busca publicações similares usando similaridade de cosseno.

        Returns:
            Lista de tuplas (publicacao_id, score, metadata)
        """
        # Gerar embedding da query
        query_embedding = self.embedder.gerar_embedding(query)

        # Buscar todos os embeddings do banco
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query com filtros opcionais
        where_clauses = []
        params = []

        if filtros:
            if 'tribunal' in filtros:
                where_clauses.append("p.tribunal = ?")
                params.append(filtros['tribunal'])
            if 'tipo_publicacao' in filtros:
                where_clauses.append("p.tipo_publicacao = ?")
                params.append(filtros['tipo_publicacao'])
            if 'data_inicio' in filtros:
                where_clauses.append("p.data_publicacao >= ?")
                params.append(filtros['data_inicio'])
            if 'data_fim' in filtros:
                where_clauses.append("p.data_publicacao <= ?")
                params.append(filtros['data_fim'])

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query_sql = f"""
        SELECT
            e.publicacao_id,
            e.embedding,
            p.numero_processo_fmt,
            p.tribunal,
            p.tipo_publicacao,
            p.ementa,
            p.texto_limpo,
            p.data_publicacao,
            p.relator
        FROM embeddings e
        JOIN publicacoes p ON e.publicacao_id = p.id
        {where_sql}
        """

        cursor.execute(query_sql, params)

        # Calcular similaridade para cada embedding
        resultados = []
        for row in cursor.fetchall():
            # Deserializar embedding
            embedding_bytes = row['embedding']
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

            # Similaridade de cosseno
            similarity = np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
            )

            if similarity >= threshold:
                metadata = {
                    'numero_processo': row['numero_processo_fmt'],
                    'tribunal': row['tribunal'],
                    'tipo': row['tipo_publicacao'],
                    'ementa': row['ementa'],
                    'texto_preview': row['texto_limpo'][:500],
                    'data': row['data_publicacao'],
                    'relator': row['relator']
                }
                resultados.append((row['publicacao_id'], float(similarity), metadata))

        conn.close()

        # Ordenar por similaridade e retornar top_k
        resultados.sort(key=lambda x: x[1], reverse=True)
        return resultados[:top_k]

    def buscar_full_text(
        self,
        query: str,
        limit: int = 50
    ) -> List[dict]:
        """Busca tradicional usando FTS5."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

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

        return [dict(row) for row in cursor.fetchall()]
```

---

## 🔄 Estratégia de Atualização Incremental

### Frequência

- **Diariamente:** Download de cadernos de todos os tribunais prioritários
- **Tempo:** 8:00 AM (após publicações oficiais)
- **Duração estimada:** ~30 minutos para 15 tribunais

### Deduplicação

```python
def inserir_publicacao(db, publicacao: Dict) -> bool:
    """
    Insere publicação se não existir (via hash).

    Returns:
        True se foi nova inserção, False se duplicata
    """
    cursor = db.cursor()

    try:
        cursor.execute("""
        INSERT INTO publicacoes (
            id, hash_conteudo, numero_processo, tribunal, tipo_publicacao,
            texto_html, texto_limpo, ementa, data_publicacao, relator, fonte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            publicacao['id'],
            publicacao['hash_conteudo'],
            publicacao['numero_processo'],
            publicacao['tribunal'],
            publicacao['tipo_publicacao'],
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
        # Hash já existe - duplicata
        logger.debug(f"Publicação duplicada: {publicacao['hash_conteudo'][:16]}...")
        return False
```

### Monitoramento

```python
def gerar_relatorio_atualizacao(db, data_execucao: str):
    """Gera relatório de atualização."""
    cursor = db.cursor()

    cursor.execute("""
    SELECT
        tribunal,
        tipo_download,
        total_publicacoes,
        total_novas,
        total_duplicadas,
        tempo_processamento,
        status
    FROM downloads_historico
    WHERE date(data_execucao) = date(?)
    ORDER BY tribunal
    """, (data_execucao,))

    print(f"\n📊 RELATÓRIO DE ATUALIZAÇÃO - {data_execucao}")
    print("="*80)
    for row in cursor.fetchall():
        print(f"{row[0]:8} | {row[1]:12} | Total: {row[2]:5} | Novas: {row[3]:4} | "
              f"Duplicadas: {row[4]:4} | Tempo: {row[5]:.1f}s | Status: {row[6]}")
```

---

## 📊 Estimativa de Armazenamento

### Por Publicação

- Texto HTML: ~5 KB
- Texto limpo: ~3 KB
- Embedding (768 dim): 3 KB
- Metadados: 1 KB
- **Total: ~12 KB por publicação**

### Por Tribunal/Dia

- **STJ:** ~1.000 publicações/dia = 12 MB
- **TJSP:** ~5.000 publicações/dia = 60 MB
- **Total (15 tribunais):** ~200 MB/dia

### Anual

- **Total:** 200 MB × 365 dias = **~73 GB/ano**
- **Com índices:** ~100 GB/ano
- **Viável:** HD externo de 1 TB comporta ~10 anos

---

## 🚀 Próximos Passos

1. ✅ **Confirmar foco:** Abandonar consulta por OAB, focar em jurisprudência
2. ⏳ **Implementar schema:** Criar banco SQLite com schema proposto
3. ⏳ **Implementar downloader:** Integrar com DJEN API e cadernos
4. ⏳ **Implementar processador:** Parser de HTML e extração de ementas
5. ⏳ **Implementar RAG:** Gerar embeddings e busca semântica
6. ⏳ **Implementar scheduler:** Atualização automática diária
7. ⏳ **Criar interface:** CLI ou web para consulta local

---

**Última atualização:** 2025-11-20
**Autor:** Claude Code (Sonnet 4.5)
