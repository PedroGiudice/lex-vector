# Text Extractor Fix - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Corrigir bug que trava extracao em 10% e adicionar modo debug/verbose.

**Architecture:** Aplicar configuracoes otimizadas do Marker, implementar timeout interno, e melhorar logging para observabilidade.

> **NOTA:** Task de limite de memoria removida - VM OCI tem 24GB, suficiente para Marker (~10GB).

**Tech Stack:** Python 3.11, FastAPI, Celery, Marker, Redis, Docker Compose

---

## Contexto da Auditoria

**Documento de referencia:** `legal-workbench/docs/AUDITORIA_TECNICA.md`

### Problemas Identificados

| ID | Severidade | Problema | Arquivo |
|----|------------|----------|---------|
| TE-01 | CRITICO | Config otimizada do Marker NAO esta sendo usada | `celery_worker.py:82-97` |
| ~~TE-02~~ | ~~CRITICO~~ | ~~Sem limite de memoria~~ | REMOVIDO: VM tem 24GB |
| TE-03 | ALTO | Pool=solo bloqueia worker | `celery_worker.py:334` |
| TE-04 | ALTO | Sem timeout interno | `celery_worker.py` |
| TE-05 | MEDIO | Logging usa print() em vez de logging | `celery_worker.py` |
| TE-06 | MEDIO | Logs nao chegam ao frontend | `textExtractorStore.ts` |

---

## FASE 1: Fixes Criticos (Backend Only)

### Task 1: Aplicar Config Otimizada do Marker

**Files:**
- Modify: `legal-workbench/docker/services/text-extractor/celery_worker.py:82-117`

**Step 1: Adicionar config dict antes do converter**

No arquivo `celery_worker.py`, substituir a funcao `extract_with_marker`:

```python
def extract_with_marker(pdf_path: str, options: Dict[str, Any]) -> tuple[str, int, Dict]:
    """Extract text using Marker engine with optimized config."""
    try:
        from marker.converters.pdf import PdfConverter
        from marker.config.parser import ConfigParser
        from marker.output import text_from_rendered

        # Get Marker model artifacts
        artifact_dict = get_marker_artifacts()

        print(f"Starting Marker extraction for: {pdf_path}")

        # OTIMIZACAO: Config igual ao marker_engine.py
        config_dict = {
            "output_format": "markdown",
            "paginate_output": True,
            "disable_image_extraction": True,  # CRITICO: evita 80MB de base64
            "disable_links": True,
            "drop_repeated_text": True,
            "keep_pageheader_in_output": False,
            "keep_pagefooter_in_output": False,
        }

        # Create config parser
        config_parser = ConfigParser(config_dict)

        # Create converter with optimized config
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=artifact_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
        )

        # Convert PDF
        rendered = converter(pdf_path)

        # Extract text from rendered output
        full_text = rendered.markdown if hasattr(rendered, 'markdown') else ""

        # Fallback for older Marker API
        if not full_text:
            full_text, _, images = text_from_rendered(rendered)

        # Get metadata from rendered document
        pages_processed = len(rendered.children) if hasattr(rendered, 'children') else 1

        extraction_metadata = {
            "ocr_applied": True,
            "file_size_bytes": os.path.getsize(pdf_path),
            "config_applied": config_dict,
        }

        print(f"Marker extraction completed: {pages_processed} pages")

        return full_text, pages_processed, extraction_metadata

    except Exception as e:
        print(f"Marker extraction failed: {e}")
        raise
```

**Step 2: Verificar imports no topo do arquivo**

Adicionar se nao existir:
```python
from marker.config.parser import ConfigParser
```

**Step 3: Commit**

```bash
git add legal-workbench/docker/services/text-extractor/celery_worker.py
git commit -m "fix(lw-text-extractor): apply optimized Marker config

BREAKING: Now uses disable_image_extraction=True
This prevents 80MB+ base64 bloat in output.

Refs: AUDITORIA_TECNICA.md TE-01"
```

---

### Task 2: Implementar Timeout Interno com Signal

**Files:**
- Modify: `legal-workbench/docker/services/text-extractor/celery_worker.py`

**Step 1: Adicionar import de signal no topo**

```python
import signal
```

**Step 2: Adicionar timeout handler**

Apos os imports, adicionar:

```python
class MarkerTimeoutError(Exception):
    """Raised when Marker extraction exceeds timeout."""
    pass


def marker_timeout_handler(signum, frame):
    """Handle timeout signal for Marker extraction."""
    raise MarkerTimeoutError("Marker extraction timed out after 5 minutes")
```

**Step 3: Envolver chamada do converter com timeout**

Na funcao `extract_with_marker`, envolver a chamada do converter:

```python
        # Set timeout for Marker extraction (5 minutes)
        MARKER_TIMEOUT = 300
        original_handler = signal.signal(signal.SIGALRM, marker_timeout_handler)
        signal.alarm(MARKER_TIMEOUT)

        try:
            # Convert PDF
            rendered = converter(pdf_path)
        finally:
            # Always restore original handler and cancel alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)
```

**Step 4: Commit**

```bash
git add legal-workbench/docker/services/text-extractor/celery_worker.py
git commit -m "fix(lw-text-extractor): add 5min internal timeout for Marker

Uses signal.SIGALRM to enforce timeout even if Celery's
soft_time_limit fails to interrupt blocked I/O.

Refs: AUDITORIA_TECNICA.md TE-04"
```

---

### Task 3: Substituir print() por logging

**Files:**
- Modify: `legal-workbench/docker/services/text-extractor/celery_worker.py`

**Step 1: Adicionar import e configurar logger no topo**

```python
import logging

# Configure logger
logger = logging.getLogger("celery_worker")
log_level = logging.DEBUG if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG" else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
```

**Step 2: Substituir todas as chamadas print() por logger**

| Antes | Depois |
|-------|--------|
| `print(f"Loading...")` | `logger.info("Loading...")` |
| `print(f"Starting...")` | `logger.info("Starting...")` |
| `print(f"...failed: {e}")` | `logger.error("...failed: %s", e)` |

**Step 3: Adicionar logs debug detalhados**

Na funcao `extract_with_marker`, adicionar:

```python
        logger.debug("Marker config: %s", config_dict)
        logger.debug("PDF path: %s, size: %d bytes", pdf_path, os.path.getsize(pdf_path))
```

**Step 4: Commit**

```bash
git add legal-workbench/docker/services/text-extractor/celery_worker.py
git commit -m "refactor(lw-text-extractor): replace print() with logging

Enables LOG_LEVEL=DEBUG for verbose output.

Refs: AUDITORIA_TECNICA.md TE-05"
```

---

## FASE 2: Observabilidade (Backend)

### Task 4: Adicionar Endpoint de Logs

**Files:**
- Modify: `legal-workbench/docker/services/text-extractor/api/main.py`
- Modify: `legal-workbench/docker/services/text-extractor/api/models.py`

**Step 1: Adicionar modelo LogEntry em models.py**

```python
class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str


class JobLogsResponse(BaseModel):
    job_id: str
    logs: List[LogEntry]
```

**Step 2: Adicionar coluna logs na tabela jobs**

Na funcao `init_db()`:

```python
        await db.execute("""
            CREATE TABLE IF NOT EXISTS job_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        """)
```

**Step 3: Adicionar endpoint GET /api/v1/jobs/{job_id}/logs**

```python
@app.get("/api/v1/jobs/{job_id}/logs", response_model=JobLogsResponse)
async def get_job_logs(job_id: str, since: Optional[datetime] = None):
    """Get logs for a specific job."""
    query = "SELECT timestamp, level, message FROM job_logs WHERE job_id = ?"
    params = [job_id]

    if since:
        query += " AND timestamp > ?"
        params.append(since.isoformat())

    query += " ORDER BY timestamp ASC"

    async with aiosqlite.connect(JOBS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()

    logs = [
        LogEntry(
            timestamp=datetime.fromisoformat(row["timestamp"]),
            level=row["level"],
            message=row["message"]
        )
        for row in rows
    ]

    return JobLogsResponse(job_id=job_id, logs=logs)
```

**Step 4: Commit**

```bash
git add legal-workbench/docker/services/text-extractor/api/
git commit -m "feat(lw-text-extractor): add /jobs/{id}/logs endpoint

Enables frontend to fetch detailed job logs.

Refs: AUDITORIA_TECNICA.md TE-06"
```

---

### Task 5: Implementar Log Writer no Celery Worker

**Files:**
- Modify: `legal-workbench/docker/services/text-extractor/celery_worker.py`

**Step 1: Adicionar funcao para salvar logs no DB**

```python
def save_job_log(job_id: str, level: str, message: str):
    """Save log entry to job_logs table."""
    db_path = Path(JOBS_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(JOBS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO job_logs (job_id, timestamp, level, message) VALUES (?, ?, ?, ?)",
            (job_id, datetime.utcnow().isoformat(), level, message)
        )
        conn.commit()
```

**Step 2: Adicionar chamadas save_job_log nos pontos chave**

Na funcao `extract_pdf`:

```python
        save_job_log(job_id, "INFO", f"Job started with engine: {engine}")
        # ...
        save_job_log(job_id, "INFO", f"File validated: {pdf_path}")
        # ...
        save_job_log(job_id, "INFO", f"Extraction completed: {pages_processed} pages")
```

**Step 3: Commit**

```bash
git add legal-workbench/docker/services/text-extractor/celery_worker.py
git commit -m "feat(lw-text-extractor): persist job logs to database

Logs are now queryable via /jobs/{id}/logs endpoint.

Refs: AUDITORIA_TECNICA.md TE-06"
```

---

## FASE 3: Frontend (Sessao Separada)

> **NOTA:** Esta fase deve ser executada em sessao separada conforme regra de CLAUDE.md:
> "NUNCA trabalhar em multiplos modulos simultaneamente"

### Task 6: Adicionar Toggle Debug no ConfigPanel

**Files:**
- Modify: `legal-workbench/frontend/src/store/textExtractorStore.ts`
- Modify: `legal-workbench/frontend/src/components/text-extractor/ConfigPanel.tsx`

### Task 7: Implementar Polling de Logs

**Files:**
- Modify: `legal-workbench/frontend/src/services/textExtractorApi.ts`
- Modify: `legal-workbench/frontend/src/store/textExtractorStore.ts`

### Task 8: Exibir Logs Detalhados no ConsolePanel

**Files:**
- Modify: `legal-workbench/frontend/src/components/text-extractor/ConsolePanel.tsx`

---

## Verificacao Final

Apos completar Fase 1 e 2:

```bash
# 1. Rebuild container
cd legal-workbench
docker compose build api-text-extractor

# 2. Restart
docker compose up -d api-text-extractor

# 3. Verificar logs
docker logs legal-workbench-api-text-extractor-1 --tail 50

# 4. Testar extracao via curl
curl -X POST http://localhost/api/text/api/v1/extract \
  -F "file=@test.pdf" \
  -F "engine=marker"

# 5. Verificar logs do job
curl http://localhost/api/text/api/v1/jobs/{job_id}/logs
```

---

## Rollback

Se algo der errado:

```bash
git revert HEAD~N  # onde N = numero de commits a reverter
docker compose build api-text-extractor
docker compose up -d api-text-extractor
```

---

*Plano criado em: 2026-01-17*
*Baseado em: AUDITORIA_TECNICA.md*
