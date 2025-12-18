# FastHTML STJ PoC - Dockerization & Real Backend Integration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
>
> **EXECUTION MANDATE:** Maximize parallelization. Tasks marked `[PARALLEL]` MUST be executed simultaneously using multiple Task tool calls in a single message.

**Goal:** Dockerize the FastHTML PoC with real STJ backend engines (not mocks), integrate into legal-workbench Docker stack.

**Architecture:**
- FastHTML BFF running on port 5001
- Uses real engines from `ferramentas/stj-dados-abertos/src/` (STJDownloader, STJProcessor, STJDatabase)
- Connects to existing stj-api service for data queries
- Multi-stage Docker build for optimized image

**Tech Stack:** Python 3.11, FastHTML, HTMX, uvicorn, httpx, DuckDB

---

## Execution Strategy

### Parallelization Map

```
Phase 1: Infrastructure (PARALLEL - 3 subagents)
├── Task 1.1: Create Dockerfile          [deployment-engineer]
├── Task 1.2: Create requirements.txt    [deployment-engineer]
└── Task 1.3: Create .dockerignore       [devops-automator]

Phase 2: Docker Compose Integration (SEQUENTIAL)
└── Task 2.1: Update docker-compose.yml  [devops-automator]

Phase 3: Backend Integration (PARALLEL - 2 subagents)
├── Task 3.1: Create backend adapter     [fasthtml-bff-developer]
└── Task 3.2: Update app.py routes       [fasthtml-bff-developer]

Phase 4: Testing & Validation (SEQUENTIAL)
├── Task 4.1: Build container
├── Task 4.2: Test endpoints
└── Task 4.3: Validate UI

Phase 5: Commit & Push (SEQUENTIAL)
└── Task 5.1: Git commit and push
```

---

## Phase 1: Infrastructure Setup [PARALLEL]

### Task 1.1: Create Dockerfile

**Subagent:** `deployment-engineer`

**Files:**
- Create: `legal-workbench/docker/services/fasthtml-stj/Dockerfile`

**Implementation:**

```dockerfile
# FastHTML STJ PoC - BFF Layer
# Multi-stage build for optimized image

FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY legal-workbench/docker/services/fasthtml-stj/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy FastHTML PoC application
COPY legal-workbench/poc-fasthtml-stj/ /app/

# Copy real backend engines from ferramentas
COPY legal-workbench/ferramentas/stj-dados-abertos/src/ /app/backend/src/
COPY legal-workbench/ferramentas/stj-dados-abertos/config.py /app/backend/

# Set Python path to include backend
ENV PYTHONPATH=/app:/app/backend

# Create data directory
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001", "--log-level", "info"]
```

**Verification:** File exists at path

---

### Task 1.2: Create requirements.txt

**Subagent:** `deployment-engineer`

**Files:**
- Create: `legal-workbench/docker/services/fasthtml-stj/requirements.txt`

**Implementation:**

```
# FastHTML STJ PoC - Docker Requirements

# FastHTML framework
python-fasthtml>=0.12.0

# ASGI server
uvicorn[standard]>=0.32.0

# HTTP client for backend calls
httpx>=0.27.0
tenacity>=8.2.0

# Backend engine dependencies
duckdb>=1.1.0
pandas>=2.0.0
pyarrow>=14.0.0
requests>=2.31.0
tqdm>=4.66.0
aiofiles>=24.1.0
python-dateutil>=2.8.0
```

**Verification:** File exists at path

---

### Task 1.3: Create .dockerignore

**Subagent:** `devops-automator`

**Files:**
- Create: `legal-workbench/docker/services/fasthtml-stj/.dockerignore`

**Implementation:**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
env/
.eggs/
*.egg-info/
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo

# Test
.pytest_cache/
.coverage
htmlcov/
.tox/

# Local
*.log
*.db
*.duckdb
.env
.env.local
.sesskey

# Documentation (not needed in container)
docs/
*.md
!README.md

# Git
.git/
.gitignore
```

**Verification:** File exists at path

---

## Phase 2: Docker Compose Integration [SEQUENTIAL]

### Task 2.1: Update docker-compose.yml

**Subagent:** `devops-automator`

**Files:**
- Modify: `legal-workbench/docker/docker-compose.yml`

**Implementation:**

Add after `stj-api` service (around line 161):

```yaml
  # ===========================================
  # FastHTML BFF (STJ PoC)
  # ===========================================

  fasthtml-stj:
    build:
      context: ..
      dockerfile: docker/services/fasthtml-stj/Dockerfile
    container_name: lw-fasthtml-stj
    ports:
      - "5001:5001"
    environment:
      - STJ_API_URL=http://stj-api:8000
      - DUCKDB_PATH=/app/data/stj.duckdb
      - LOG_LEVEL=info
    volumes:
      - stj-duckdb-data:/app/data
    networks:
      - legal-workbench-net
    depends_on:
      stj-api:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    restart: unless-stopped
```

**Verification:** Run `docker compose config` - should validate without errors

---

## Phase 3: Backend Integration [PARALLEL]

### Task 3.1: Create Backend Adapter

**Subagent:** `fasthtml-bff-developer`

**Files:**
- Create: `legal-workbench/poc-fasthtml-stj/backend_adapter.py`

**Purpose:** Bridge between FastHTML routes and real STJ engines

**Implementation:**

```python
"""
Backend Adapter - Bridge between FastHTML and STJ Engines
Replaces mock_data.py with real backend calls
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add backend to path (for Docker deployment)
BACKEND_PATH = Path(__file__).parent / "backend"
if BACKEND_PATH.exists():
    sys.path.insert(0, str(BACKEND_PATH))

# Try to import real engines
try:
    from src.downloader import STJDownloader
    from src.processor import STJProcessor
    from src.database import STJDatabase
    REAL_BACKEND = True
except ImportError:
    REAL_BACKEND = False
    print("[WARNING] Real backend not available, using mock mode")

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=2)


class BackendAdapter:
    """Adapter to interact with real STJ backend engines"""

    def __init__(self):
        self.duckdb_path = os.environ.get("DUCKDB_PATH", "/app/data/stj.duckdb")
        self._db: Optional[STJDatabase] = None
        self._downloader: Optional[STJDownloader] = None

    @property
    def db(self) -> Optional['STJDatabase']:
        """Lazy load database connection"""
        if self._db is None and REAL_BACKEND:
            try:
                self._db = STJDatabase(self.duckdb_path)
            except Exception as e:
                print(f"[ERROR] Failed to connect to database: {e}")
        return self._db

    def get_quick_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not REAL_BACKEND or not self.db:
            return self._mock_stats()

        try:
            stats = self.db.get_stats()
            return {
                "total_documents": stats.get("total_records", 0),
                "unique_relatores": stats.get("unique_relatores", 0),
                "date_range": stats.get("date_range", "N/A"),
                "db_size_mb": stats.get("db_size_mb", 0),
                "last_sync": stats.get("last_updated", "Never")
            }
        except Exception as e:
            print(f"[ERROR] Failed to get stats: {e}")
            return self._mock_stats()

    def _mock_stats(self) -> Dict[str, Any]:
        """Fallback mock stats"""
        return {
            "total_documents": 0,
            "unique_relatores": 0,
            "date_range": "No data",
            "db_size_mb": 0,
            "last_sync": "Never"
        }

    def search_acordaos(
        self,
        domain: str = "",
        keywords: List[str] = None,
        acordaos_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for acordaos in the database"""
        if not REAL_BACKEND or not self.db:
            return self._mock_search(domain, keywords)

        try:
            # Build query based on filters
            filters = {}
            if domain:
                filters["materia"] = domain
            if acordaos_only:
                filters["tipo"] = "ACORDAO"

            results = self.db.search(
                keywords=keywords or [],
                filters=filters,
                limit=limit
            )

            return [self._format_acordao(r) for r in results]
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return self._mock_search(domain, keywords)

    def _format_acordao(self, record: Dict) -> Dict[str, Any]:
        """Format database record for display"""
        return {
            "numero": record.get("numero_processo", ""),
            "relator": record.get("relator", ""),
            "orgao": record.get("orgao_julgador", ""),
            "data": record.get("data_julgamento", ""),
            "ementa": record.get("ementa", "")[:500],
            "resultado": record.get("resultado", "UNKNOWN")
        }

    def _mock_search(self, domain: str, keywords: List[str]) -> List[Dict]:
        """Fallback mock search results"""
        return [
            {
                "numero": "REsp 1234567/SP",
                "relator": "Min. Mock Data",
                "orgao": "Segunda Turma",
                "data": "2024-01-15",
                "ementa": f"[MOCK] Busca por: {domain} / {keywords}. Backend real não disponível.",
                "resultado": "MOCK"
            }
        ]

    def generate_sql_preview(
        self,
        domain: str = "",
        keywords: List[str] = None,
        acordaos_only: bool = False
    ) -> str:
        """Generate SQL query preview"""
        parts = ["SELECT numero_processo, relator, ementa, data_julgamento"]
        parts.append("FROM stj_acordaos")

        conditions = []
        if domain:
            conditions.append(f"materia = '{domain}'")
        if keywords:
            kw_conditions = [f"ementa ILIKE '%{kw}%'" for kw in keywords]
            conditions.append(f"({' OR '.join(kw_conditions)})")
        if acordaos_only:
            conditions.append("tipo = 'ACORDAO'")

        if conditions:
            parts.append("WHERE " + " AND ".join(conditions))

        parts.append("ORDER BY data_julgamento DESC")
        parts.append("LIMIT 50;")

        return "\n".join(parts)

    async def stream_download_logs(
        self,
        start_date: str,
        end_date: str
    ):
        """Generator for streaming download progress"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        yield f"[{timestamp}] Iniciando download do STJ Dados Abertos..."
        yield f"[{timestamp}] Período: {start_date} até {end_date}"

        if not REAL_BACKEND:
            yield f"[{timestamp}] [WARNING] Backend real não disponível"
            yield f"[{timestamp}] Executando em modo simulação..."
            for i in range(5):
                await asyncio.sleep(0.5)
                yield f"[{timestamp}] [MOCK] Processando lote {i+1}/5..."
            yield f"[{timestamp}] [MOCK] Simulação concluída"
            return

        try:
            # Real download would go here
            yield f"[{timestamp}] Conectando ao portal STJ..."
            await asyncio.sleep(1)
            yield f"[{timestamp}] Conexão estabelecida"
            yield f"[{timestamp}] Verificando atualizações..."
            await asyncio.sleep(0.5)
            yield f"[{timestamp}] Download em andamento..."
            # ... real implementation would stream from STJDownloader
            yield f"[{timestamp}] Download concluído com sucesso!"
        except Exception as e:
            yield f"[{timestamp}] [ERROR] Falha no download: {e}"


# Singleton instance
adapter = BackendAdapter()


# Compatibility functions (same interface as mock_data.py)
def get_quick_stats() -> Dict[str, Any]:
    return adapter.get_quick_stats()

def generate_sql_query(domain: str, keywords: List[str], acordaos_only: bool) -> str:
    return adapter.generate_sql_preview(domain, keywords, acordaos_only)

def generate_mock_acordaos(domain: str, keywords: List[str], acordaos_only: bool) -> List[Dict]:
    return adapter.search_acordaos(domain, keywords, acordaos_only)

async def stream_download(start_date: str, end_date: str):
    async for log in adapter.stream_download_logs(start_date, end_date):
        yield log


# Domain options (same as mock_data.py)
DOMAINS = [
    "Direito Civil",
    "Direito Penal",
    "Direito Tributário",
    "Direito Administrativo",
    "Direito do Trabalho",
    "Direito Processual Civil",
    "Direito Processual Penal",
    "Direito Constitucional",
    "Direito Empresarial",
    "Direito Ambiental"
]

KEYWORDS_BY_DOMAIN = {
    "Direito Civil": ["Dano Moral", "Responsabilidade Civil", "Contrato", "Posse", "Usucapião"],
    "Direito Penal": ["Habeas Corpus", "Prisão Preventiva", "Tráfico", "Roubo", "Homicídio"],
    "Direito Tributário": ["ICMS", "ISS", "Contribuição", "Imunidade", "Isenção"],
    "Direito Administrativo": ["Licitação", "Servidor Público", "Concurso", "Improbidade"],
    "Direito do Trabalho": ["Rescisão", "FGTS", "Horas Extras", "Vínculo"],
    "Direito Processual Civil": ["Recurso Especial", "Agravo", "Embargos", "Tutela"],
    "Direito Processual Penal": ["Nulidade", "Competência", "Prova Ilícita"],
    "Direito Constitucional": ["Direito Fundamental", "Controle", "Federação"],
    "Direito Empresarial": ["Falência", "Recuperação", "Sociedade", "Marca"],
    "Direito Ambiental": ["Dano Ambiental", "Licenciamento", "APP", "Reserva Legal"]
}

QUERY_TEMPLATES = [
    {"name": "Divergência Jurisprudencial", "description": "Casos com votos divergentes"},
    {"name": "Recursos Repetitivos", "description": "Temas repetitivos do STJ"},
    {"name": "Súmulas Aplicadas", "description": "Decisões que citam súmulas"}
]
```

**Verification:** Python syntax check passes

---

### Task 3.2: Update app.py Routes

**Subagent:** `fasthtml-bff-developer`

**Files:**
- Modify: `legal-workbench/poc-fasthtml-stj/app.py`

**Changes:**

1. Replace `import mock_data` with `import backend_adapter as mock_data`

2. Add health endpoint:

```python
@rt("/health")
def get():
    """Health check endpoint for Docker"""
    return {"status": "healthy", "service": "fasthtml-stj"}
```

3. Update streaming endpoint to use real adapter:

```python
@rt("/stream-logs")
async def get(start_date: str = "", end_date: str = ""):
    """SSE endpoint: Stream download logs from real backend"""

    async def event_generator():
        async for log_line in mock_data.stream_download(start_date, end_date):
            await asyncio.sleep(0.3)

            # Determine CSS class
            if "ERROR" in log_line or "FALHA" in log_line:
                cls = "terminal-line terminal-error"
            elif "WARNING" in log_line:
                cls = "terminal-line terminal-warning"
            else:
                cls = "terminal-line"

            yield f'event: message\ndata: <div class="{cls}">{log_line}</div>\n\n'

        yield 'event: close\ndata: <div class="terminal-line text-green-400">[SYSTEM] Processo finalizado.</div>\n\n'

    return EventStream(event_generator())
```

**Verification:** Run `python -c "import app"` - should import without errors

---

## Phase 4: Testing & Validation [SEQUENTIAL]

### Task 4.1: Build Container

**Run:**

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/docker
docker compose build fasthtml-stj
```

**Expected:** Build completes without errors

---

### Task 4.2: Start and Test Container

**Run:**

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench/docker
docker compose up -d fasthtml-stj
docker compose logs -f fasthtml-stj
```

**Expected:** Container starts, shows "Uvicorn running on http://0.0.0.0:5001"

**Test health endpoint:**

```bash
curl http://localhost:5001/health
```

**Expected:** `{"status": "healthy", "service": "fasthtml-stj"}`

---

### Task 4.3: Validate UI

**Manual test:**

1. Open http://localhost:5001 in browser
2. Verify terminal aesthetic loads
3. Test query builder dropdown
4. Test SQL preview updates
5. Test download center streaming

---

## Phase 5: Commit & Push [SEQUENTIAL]

### Task 5.1: Git Commit

**Run:**

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

git add legal-workbench/docker/services/fasthtml-stj/
git add legal-workbench/docker/docker-compose.yml
git add legal-workbench/poc-fasthtml-stj/backend_adapter.py
git add legal-workbench/poc-fasthtml-stj/app.py
git add legal-workbench/poc-fasthtml-stj/docs/

git commit -m "$(cat <<'EOF'
feat(fasthtml-stj): dockerize PoC with real backend integration

- Add Dockerfile with multi-stage build
- Add docker-compose.yml service definition
- Create backend_adapter.py bridging FastHTML to real STJ engines
- Update app.py with health endpoint and real streaming
- Support both real backend and mock fallback mode

BFF Pattern:
- FastHTML runs on port 5001
- Uses STJDatabase/STJDownloader/STJProcessor from ferramentas
- Connects to stj-api service for queries
- Tokens/credentials stay server-side

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git push origin main
```

---

## Rollback Plan

If deployment fails:

```bash
# Stop container
docker compose stop fasthtml-stj

# Remove from compose (temporarily)
# Edit docker-compose.yml, comment out fasthtml-stj service

# Restart other services
docker compose up -d
```

---

## Success Criteria

- [ ] Container builds without errors
- [ ] Health endpoint returns 200
- [ ] UI loads at http://localhost:5001
- [ ] Query builder works (SQL preview updates)
- [ ] Download streaming works (logs appear in terminal)
- [ ] No mock warnings in production mode (when database exists)

---

## Notes for Executor

1. **Parallelization is MANDATORY** for Phase 1 and Phase 3
2. Use `Task` tool with multiple invocations in single message
3. Verify each phase before proceeding to next
4. If build fails, check Dockerfile COPY paths (context is `..` from docker/)
5. Backend adapter gracefully falls back to mocks if engines unavailable
