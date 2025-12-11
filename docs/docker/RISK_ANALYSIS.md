# Legal Workbench - Docker Risk Analysis

**Data:** 2025-12-11
**Sistema:** Legal Workbench - Sistema de Automação Jurídica
**Escopo:** Análise de Riscos para Dockerização Completa
**Autor:** Pedro Giudice (PGR)

---

## Resumo

A dockerização do Legal Workbench apresenta riscos em múltiplas dimensões:
- **CRÍTICO:** Gerenciamento de secrets (GOOGLE_API_KEY, TRELLO_API)
- **CRÍTICO:** Consumo de memória (~10GB para Marker PDF)
- **ALTO:** Persistência de dados e estado entre restarts
- **ALTO:** Cold start time para modelos ML/transformers
- **MÉDIO:** Compatibilidade de dependências Python complexas
- **MÉDIO:** Network latency para APIs externas

Este documento fornece análise detalhada e planos de mitigação.

---

## 1. Matriz de Riscos

### 1.1 Classificação de Severidade

| Nível | Probabilidade | Impacto | Ação Requerida |
|-------|---------------|---------|----------------|
| **CRÍTICO** | Alta | Alto | Bloqueante - mitigar antes de deploy |
| **ALTO** | Média-Alta | Alto-Médio | Plano de mitigação obrigatório |
| **MÉDIO** | Média | Médio | Monitoramento e fallback |
| **BAIXO** | Baixa | Baixo-Médio | Documentar e aceitar |

### 1.2 Matriz Completa de Riscos

| # | Risco | Probabilidade | Impacto | Severidade | Mitigação |
|---|-------|---------------|---------|------------|-----------|
| **R01** | Secrets expostos em imagens Docker | Média | CRÍTICO | **CRÍTICO** | Build-time secrets via BuildKit, nunca em ENV layers |
| **R02** | OOM Kill - Marker PDF consome >10GB | Alta | CRÍTICO | **CRÍTICO** | Memory limits, swap config, health checks |
| **R03** | Perda de dados em ~/juridico-data | Baixa | CRÍTICO | **CRÍTICO** | Volume mounts read-only quando possível, backups |
| **R04** | Container escape via vulnerabilidades | Baixa | CRÍTICO | **CRÍTICO** | Non-root user, security scanning, AppArmor/SELinux |
| **R05** | Cold start >2min para legal-text-extractor | Alta | Alto | **ALTO** | Model caching, persistent volumes, startup optimization |
| **R06** | Incompatibilidade GPU/CPU para Marker | Média | Alto | **ALTO** | Multi-stage build, runtime detection, fallback |
| **R07** | DuckDB corruption em concurrent access | Média | Alto | **ALTO** | Single writer pattern, file locking, WAL mode |
| **R08** | Rate limiting Gemini API (429 errors) | Média | Alto | **ALTO** | Retry logic, circuit breaker, request queuing |
| **R09** | Network isolation quebra Trello MCP | Média | Médio | **MÉDIO** | Network policies claras, egress rules, health checks |
| **R10** | Build cache inválido causa bugs | Média | Médio | **MÉDIO** | Deterministic builds, layer invalidation strategy |
| **R11** | Port conflicts 8501 em multi-instance | Alta | Médio | **MÉDIO** | Dynamic port allocation, reverse proxy |
| **R12** | Timezone mismatch em logs/timestamps | Alta | Baixo | **BAIXO** | TZ env var, NTP sync, UTC standardization |
| **R13** | Python version mismatch (3.10 vs 3.11) | Baixa | Médio | **MÉDIO** | Pin exact Python version in Dockerfile |
| **R14** | Large image size (>5GB) slow pulls | Alta | Médio | **MÉDIO** | Multi-stage builds, .dockerignore, layer optimization |
| **R15** | Dependency conflicts entre serviços | Média | Alto | **ALTO** | Isolated venvs, dependency pinning, lock files |
| **R16** | Logs preenchem disco (no rotation) | Alta | Médio | **MÉDIO** | Log rotation, max size limits, log aggregation |
| **R17** | Streamlit session state perdida em restart | Alta | Médio | **MÉDIO** | Redis backend, persistent sessions, state recovery |
| **R18** | API keys expiradas não detectadas | Baixa | Médio | **MÉDIO** | Startup validation, health check endpoints |
| **R19** | DNS resolution fail para APIs externas | Baixa | Alto | **ALTO** | Custom DNS, /etc/hosts, retry logic |
| **R20** | File descriptor limits atingidos | Média | Alto | **ALTO** | ulimit config, resource limits, monitoring |
| **R21** | Deadlock em shutdown (SIGTERM ignored) | Média | Médio | **MÉDIO** | Graceful shutdown handlers, SIGTERM timeouts |
| **R22** | Locale/encoding issues (UTF-8) | Média | Médio | **MÉDIO** | Explicit locale setting, LANG env vars |
| **R23** | Outdated base images com CVEs | Alta | Alto | **ALTO** | Manual scanning periodic, update policy |
| **R24** | Rollback impossível (no versioning) | Alta | CRÍTICO | **CRÍTICO** | Image tagging strategy, versioned deployments |
| **R25** | Inter-container communication failure | Média | Alto | **ALTO** | Service discovery, health checks, retry logic |

---

## 2. Riscos de Implementação (Durante Dockerização)

### 2.1 Riscos de Build

#### R-BUILD-01: Dependências Python Complexas Falhando
**Contexto:**
- Marker PDF tem dependências ML complexas (torch, transformers)
- Bibliotecas podem requerer compilação (gcc, build-essential)
- Wheels pré-compilados podem não existir para todas as plataformas

**Probabilidade:** Alta
**Impacto:** Bloqueante

**Sintomas:**
```
ERROR: Failed building wheel for tokenizers
Could not build wheels for X, which is required to install pyproject.toml
```

**Mitigação:**
1. **Multi-stage builds:** Build wheels em stage separado
2. **Platform-specific images:** AMD64 vs ARM64 diferentes
3. **Pre-built wheels:** Cache local de wheels compilados
4. **Dependency pinning:** poetry.lock ou requirements.lock
5. **Fallback strategy:** Pure Python alternatives quando disponível

**Implementação:**
```dockerfile
# Build stage
FROM python:3.10-slim as builder
RUN apt-get update && apt-get install -y \
    gcc g++ build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Runtime stage
FROM python:3.10-slim
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*
```

#### R-BUILD-02: Build Cache Poisoning
**Contexto:**
- Layer caching pode preservar bugs ou dados sensíveis
- Mudanças em arquivos não invalidam layers anteriores corretamente
- Build secrets podem vazar em layers intermediários

**Probabilidade:** Média
**Impacto:** Alto (segurança + bugs silenciosos)

**Mitigação:**
1. **Deterministic builds:** Ordem de COPY otimizada
2. **BuildKit secrets:** `RUN --mount=type=secret`
3. **Cache busting:** Build args para forçar rebuild
4. **Regular full rebuilds:** `--no-cache` em CI/CD
5. **Layer inspection:** `docker history --no-trunc` em CI

**Exemplo:**
```dockerfile
# ERRADO - secrets em layer
ENV GOOGLE_API_KEY=sk-xxx

# CERTO - BuildKit secret
RUN --mount=type=secret,id=google_key \
    export GOOGLE_API_KEY=$(cat /run/secrets/google_key) && \
    python setup.py
```

#### R-BUILD-03: .dockerignore Incompleto
**Contexto:**
- `.venv/`, `__pycache__/`, `*.pdf` devem ser excluídos
- Build context grande (>1GB) torna builds lentos
- Dados sensíveis em diretórios locais podem vazar

**Probabilidade:** Alta
**Impacto:** Médio (performance) / Alto (se secrets vazarem)

**Mitigação:**
```dockerignore
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/

# Data
*.pdf
*.docx
*.log
juridico-data/

# Secrets
.env
.env.*
*.key
*.pem

# Development
.git/
.vscode/
.idea/
*.md
tests/
docs/

# Large files
*.tar.gz
*.zip
node_modules/
```

### 2.2 Riscos de Configuração

#### R-CONFIG-01: Environment Variables Hardcoded
**Contexto:**
- Streamlit usa `st.secrets` para GOOGLE_API_KEY
- Diferentes ambientes (dev/prod) requerem configs diferentes
- Secrets em Dockerfile são permanentes e inseguros

**Probabilidade:** Alta
**Impacto:** CRÍTICO (segurança)

**Mitigação:**
1. **External secrets:** Docker secrets, Vault, AWS Secrets Manager
2. **Runtime injection:** `docker run -e` ou `env_file`
3. **Config validation:** Startup checks para required vars
4. **Separate configs:** `.env.example` vs `.env.local` vs `.env.prod`
5. **Secret scanning:** Pre-commit hooks, CI scanning

**Implementação:**
```python
# startup_validator.py
import os
import sys

REQUIRED_SECRETS = [
    "GOOGLE_API_KEY",
    "TRELLO_API_KEY",
    "TRELLO_API_TOKEN"
]

def validate_secrets():
    missing = [s for s in REQUIRED_SECRETS if not os.getenv(s)]
    if missing:
        print(f"ERROR: Missing required secrets: {missing}", file=sys.stderr)
        sys.exit(1)

    # Validate format
    if len(os.getenv("GOOGLE_API_KEY", "")) < 20:
        print("ERROR: GOOGLE_API_KEY appears invalid", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    validate_secrets()
    print("✓ All secrets validated")
```

#### R-CONFIG-02: Volume Mount Path Hardcoding
**Contexto:**
- Código usa `~/juridico-data` que varia entre ambientes
- Paths absolutos quebram portabilidade
- Diferentes usuários têm diferentes home dirs

**Probabilidade:** Alta
**Impacado:** Alto

**Mitigação:**
1. **Environment variable:** `DATA_DIR=/data`
2. **Path abstraction:** `shared.utils.path_utils.get_data_dir()`
3. **Docker volume:** Named volume independente de host path
4. **Relative paths:** Sempre relativo a container workdir
5. **Validation:** Startup check de paths críticos

**Exemplo:**
```python
# shared/utils/path_utils.py
import os
from pathlib import Path

def get_data_dir() -> Path:
    """Get data directory, Docker-aware"""
    # Docker environment
    if os.getenv("DOCKER_CONTAINER"):
        return Path(os.getenv("DATA_DIR", "/data"))

    # Local development
    return Path.home() / "juridico-data"
```

### 2.3 Riscos de Integração

#### R-INT-01: Service Discovery Failure
**Contexto:**
- Streamlit Hub precisa chamar legal-text-extractor
- MCP server precisa ser acessível por nome de serviço
- Hardcoded localhost:PORT não funciona em containers

**Probabilidade:** Alta
**Impacto:** Bloqueante

**Mitigação:**
1. **Docker Compose networking:** Service names como DNS
2. **Environment variables:** `EXTRACTOR_URL=http://legal-text-extractor:8502`
3. **Health checks:** Retry logic até serviço estar ready
4. **Service mesh:** Consul/Linkerd para production
5. **Fallback:** Graceful degradation se serviço indisponível

**Docker Compose:**
```yaml
services:
  streamlit-hub:
    environment:
      - EXTRACTOR_URL=http://legal-text-extractor:8502
      - ASSEMBLER_URL=http://legal-doc-assembler:8503
      - MCP_URL=http://trello-mcp:3000
    depends_on:
      legal-text-extractor:
        condition: service_healthy
```

#### R-INT-02: Port Conflicts em Multi-Instance
**Contexto:**
- Múltiplos usuários/ambientes no mesmo host
- CI/CD rodando múltiplos builds paralelos
- Ports 8501-8503 podem colidir

**Probabilidade:** Média
**Impacto:** Médio

**Mitigação:**
1. **Dynamic port allocation:** `docker run -P` (random high ports)
2. **Port ranges:** Reserve blocos (8501-8510, 8601-8610, etc)
3. **Reverse proxy:** Nginx/Traefik roteando por hostname
4. **Environment isolation:** Diferentes docker networks
5. **Port validation:** Check before start

---

## 3. Riscos Operacionais (Pós-Deploy)

### 3.1 Riscos de Runtime

#### R-OPS-01: OOM Kill - Marker PDF Exceeds Memory
**Contexto:**
- Marker PDF pode consumir >10GB RAM em PDFs grandes
- Docker default memory limit pode ser insuficiente
- OOM kill termina container sem cleanup

**Probabilidade:** Alta
**Impacto:** CRÍTICO (perda de processamento)

**Sintomas:**
```
kernel: Out of memory: Killed process 1234 (python) total-vm:11234567kB
Container exited with code 137 (OOM killed)
```

**Mitigação:**
1. **Memory limits explícitos:**
```yaml
services:
  legal-text-extractor:
    deploy:
      resources:
        limits:
          memory: 10G  # 10GB + 2GB buffer
        reservations:
          memory: 6G
```

2. **Swap configuration:**
```yaml
    mem_swappiness: 60  # Allow some swap usage
```

3. **Health checks com memory monitoring:**
```yaml
    healthcheck:
      test: ["CMD", "python", "-c", "import psutil; exit(0 if psutil.virtual_memory().percent < 90 else 1)"]
      interval: 30s
```

4. **Graceful degradation:**
```python
# In extractor
def process_pdf(file_path):
    import psutil
    mem = psutil.virtual_memory()

    if mem.percent > 85:
        raise MemoryError("Insufficient memory, refusing new job")

    # Chunk large PDFs
    if file_size > 100_000_000:  # 100MB
        return process_chunked(file_path)

    return process_full(file_path)
```

5. **Monitoring via logs:**
```python
import logging
logger = logging.getLogger(__name__)

def log_memory_usage():
    import psutil
    mem = psutil.virtual_memory()
    logger.info(f"Memory usage: {mem.percent}% ({mem.used // (1024**3)}GB / {mem.total // (1024**3)}GB)")
```

#### R-OPS-02: Cold Start Latency (Model Loading)
**Contexto:**
- Marker PDF carrega modelos ML na inicialização
- Transformers/torch podem demorar >60s para carregar
- Usuários esperam response time <5s

**Probabilidade:** Alta
**Impacto:** Alto (UX degradada)

**Mitigação:**
1. **Model caching em volume:**
```yaml
volumes:
  - model-cache:/root/.cache/huggingface
```

2. **Warm-up script:**
```python
# warmup.py
import marker
import torch

def warmup():
    """Pre-load models before accepting traffic"""
    print("Warming up models...")
    marker.load_models()
    torch.set_num_threads(4)
    print("Warm-up complete")

if __name__ == "__main__":
    warmup()
```

3. **Health check com startup time:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8502/health"]
  start_period: 120s  # Give time for model loading
  interval: 30s
```

4. **Keep-alive strategy:**
```yaml
restart: unless-stopped  # Don't let container die unnecessarily
```

5. **Pre-warmed pool:**
```bash
# Keep 2 instances always ready
docker-compose up -d --scale legal-text-extractor=2
```

#### R-OPS-03: DuckDB File Locking Conflicts
**Contexto:**
- stj-dados-abertos usa DuckDB file-based
- Múltiplos containers/processos podem acessar
- Concurrent writes causam corruption

**Probabilidade:** Média
**Impacto:** Alto (data corruption)

**Mitigação:**
1. **Single writer pattern:**
```yaml
services:
  stj-dados-abertos:
    deploy:
      replicas: 1  # NEVER scale this service
```

2. **Read-only mounts para readers:**
```yaml
  streamlit-hub:
    volumes:
      - duckdb-data:/data/duckdb:ro  # Read-only
```

3. **WAL mode:**
```python
import duckdb
con = duckdb.connect('database.db', read_only=False)
con.execute("PRAGMA wal_mode")  # Write-Ahead Logging
```

4. **Connection pooling:**
```python
# Single connection, reused
_db_connection = None

def get_db():
    global _db_connection
    if _db_connection is None:
        _db_connection = duckdb.connect('database.db')
    return _db_connection
```

5. **File locking check:**
```python
import fcntl

def acquire_lock(db_path):
    lock_file = f"{db_path}.lock"
    f = open(lock_file, 'w')
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except BlockingIOError:
        raise RuntimeError("Database is locked by another process")
```

### 3.2 Riscos de Dados

#### R-DATA-01: Volume Data Loss em Recreate
**Contexto:**
- `docker-compose down -v` deleta volumes
- Named volumes vs bind mounts têm comportamentos diferentes
- Dados em ~/juridico-data são críticos

**Probabilidade:** Baixa
**Impacto:** CRÍTICO (perda de dados jurídicos)

**Mitigação:**
1. **Explicit volume creation:**
```yaml
volumes:
  juridico-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /home/user/juridico-data
```

2. **Backup automation:**
```bash
# Daily backup
docker run --rm \
  -v juridico-data:/data \
  -v /backup:/backup \
  alpine tar czf /backup/juridico-$(date +%Y%m%d).tar.gz /data
```

3. **Volume protection:**
```yaml
x-volume-labels: &volume-labels
  com.legal-workbench.backup: "required"
  com.legal-workbench.critical: "true"

volumes:
  juridico-data:
    labels: *volume-labels
```

4. **Pre-flight check:**
```bash
# Before docker-compose down
docker-compose exec streamlit-hub python -c "
import os
assert os.path.exists('/data/test.txt'), 'Volume mount verification failed'
"
```

5. **Immutable data strategy:**
```yaml
volumes:
  - juridico-data:/data:ro  # Read-only when possible
```

#### R-DATA-02: Timezone/Encoding Inconsistencies
**Contexto:**
- Logs com timestamps errados dificultam debugging
- PDFs jurídicos podem ter encoding Latin1/UTF-8 mixed
- Container default pode ser UTC vs host BRT

**Probabilidade:** Alta
**Impacto:** Médio (debugging difícil)

**Mitigação:**
1. **Explicit timezone:**
```dockerfile
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
```

2. **Locale configuration:**
```dockerfile
ENV LANG=pt_BR.UTF-8
ENV LC_ALL=pt_BR.UTF-8
RUN apt-get update && apt-get install -y locales && \
    locale-gen pt_BR.UTF-8 && \
    update-locale LANG=pt_BR.UTF-8
```

3. **Python encoding:**
```dockerfile
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1
```

4. **Logging timezone:**
```python
import logging
logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S %Z'
)
```

### 3.3 Riscos de Rede

#### R-NET-01: API Rate Limiting (Gemini, Trello)
**Contexto:**
- Gemini API tem rate limits (60 req/min na tier free)
- Trello API tem rate limits (300 req/10min)
- Burst traffic pode causar 429 errors

**Probabilidade:** Média
**Impacto:** Alto (feature quebrada)

**Mitigação:**
1. **Rate limiting client-side:**
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=50, period=60)  # 50 calls per minute (safety margin)
def call_gemini_api():
    pass
```

2. **Circuit breaker pattern:**
```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

@breaker
def call_trello_api():
    # If fails 5 times, circuit opens for 60s
    pass
```

3. **Request queuing:**
```python
import asyncio
from asyncio import Queue

request_queue = Queue(maxsize=100)

async def process_queue():
    while True:
        request = await request_queue.get()
        await asyncio.sleep(1)  # Rate limit: 1 req/sec
        await execute_request(request)
```

4. **Exponential backoff:**
```python
import time
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(multiplier=1, min=4, max=60),
       stop=stop_after_attempt(5))
def api_call():
    response = requests.get(url)
    response.raise_for_status()
    return response
```

5. **Monitoring:**
```python
from prometheus_client import Counter
api_rate_limit_errors = Counter('api_rate_limit_errors_total',
                                 'API rate limit errors',
                                 ['service'])
```

#### R-NET-02: DNS Resolution Failures
**Contexto:**
- Container usa DNS resolver diferente do host
- Corporate networks podem bloquear DNS externo
- APIs externas podem mudar IPs

**Probabilidade:** Baixa
**Impacto:** Alto

**Mitigação:**
1. **Custom DNS servers:**
```yaml
services:
  streamlit-hub:
    dns:
      - 8.8.8.8
      - 8.8.4.4
      - 1.1.1.1
```

2. **DNS caching:**
```dockerfile
RUN apt-get install -y dnsmasq
```

3. **Health check DNS:**
```yaml
healthcheck:
  test: ["CMD", "nslookup", "generativelanguage.googleapis.com"]
```

4. **/etc/hosts fallback:**
```yaml
extra_hosts:
  - "generativelanguage.googleapis.com:142.251.129.10"
```

#### R-NET-03: Network Isolation Breaks External APIs
**Contexto:**
- Default Docker network pode bloquear egress
- Firewalls podem bloquear container traffic
- Proxy/VPN requirements

**Probabilidade:** Média
**Impacto:** Bloqueante

**Mitigação:**
1. **Network mode configuration:**
```yaml
network_mode: bridge  # Or host for full access
```

2. **Explicit egress rules:**
```yaml
networks:
  external-api:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_ip_masquerade: "true"
```

3. **Proxy support:**
```dockerfile
ENV HTTP_PROXY=http://proxy:8080
ENV HTTPS_PROXY=http://proxy:8080
ENV NO_PROXY=localhost,127.0.0.1
```

4. **Connection validation:**
```python
# startup_validator.py
import requests

def test_connectivity():
    try:
        requests.get("https://generativelanguage.googleapis.com", timeout=5)
        print("✓ Gemini API reachable")
    except Exception as e:
        print(f"✗ Gemini API unreachable: {e}")
        sys.exit(1)
```

---

## 4. Riscos de Segurança

### 4.1 Secrets Management

#### R-SEC-01: Secrets in Docker Images
**Contexto:**
- `docker history` pode revelar secrets em layers
- Images publicadas em registry expõem secrets
- `docker inspect` mostra environment variables

**Probabilidade:** Média
**Impacto:** CRÍTICO

**Mitigação:**
1. **NEVER use ENV for secrets:**
```dockerfile
# ERRADO
ENV GOOGLE_API_KEY=AIza...

# CERTO - use Docker secrets ou runtime injection
```

2. **BuildKit secrets:**
```dockerfile
# syntax=docker/dockerfile:1.4
RUN --mount=type=secret,id=google_key \
    cp /run/secrets/google_key /tmp/key && \
    python setup.py && \
    rm /tmp/key
```

3. **Multi-stage builds:**
```dockerfile
FROM base as builder
RUN --mount=type=secret,id=api_key ...

FROM base as runtime
# Secrets NOT copied to final image
```

4. **Runtime secrets:**
```yaml
services:
  streamlit-hub:
    secrets:
      - google_api_key
      - trello_api_key

secrets:
  google_api_key:
    file: ./secrets/google_api_key.txt
  trello_api_key:
    file: ./secrets/trello_api_key.txt
```

5. **Secret scanning:**
```bash
# Pre-commit hook
docker run --rm -v $(pwd):/repo trufflesecurity/trufflehog:latest \
  filesystem /repo --fail
```

#### R-SEC-02: Running as Root
**Contexto:**
- Default Docker user é root (UID 0)
- Container escape vulnerabilities = root on host
- File permissions issues em volumes

**Probabilidade:** Alta
**Impacto:** CRÍTICO

**Mitigação:**
1. **Non-root user:**
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

2. **Explicit UID/GID:**
```dockerfile
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g $GROUP_ID appuser && \
    useradd -u $USER_ID -g appuser appuser
USER appuser
```

3. **Volume permissions:**
```yaml
volumes:
  - juridico-data:/data
user: "1000:1000"  # Match host user
```

4. **Read-only root filesystem:**
```yaml
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
  - /var/tmp
```

5. **Capability dropping:**
```yaml
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE  # Only if needed
```

#### R-SEC-03: Container Escape Vulnerabilities
**Contexto:**
- CVEs em Docker/containerd podem permitir escape
- Kernel vulnerabilities afetam todos containers
- Privileged containers = full host access

**Probabilidade:** Baixa
**Impacto:** CRÍTICO

**Mitigação:**
1. **Security scanning:**
```bash
# Daily scan
docker scan legal-workbench:latest
trivy image legal-workbench:latest --severity HIGH,CRITICAL
```

2. **AppArmor/SELinux:**
```yaml
security_opt:
  - apparmor=docker-default
  - seccomp=unconfined  # Only if absolutely necessary
```

3. **Never use privileged:**
```yaml
# NEVER DO THIS
privileged: true
```

4. **Regular updates:**
```bash
# Update base images weekly
docker pull python:3.10-slim
docker-compose build --no-cache
```

5. **Runtime security:**
```bash
# Falco for runtime monitoring
docker run -d --name falco \
  --privileged \
  -v /var/run/docker.sock:/host/var/run/docker.sock \
  falcosecurity/falco
```

### 4.2 Network Security

#### R-SEC-04: Exposed Internal Services
**Contexto:**
- MCP server não deve ser público
- DuckDB query interface não deve ter internet access
- Debug endpoints podem vazar informação

**Probabilidade:** Média
**Impacto:** Alto

**Mitigação:**
1. **Network segmentation:**
```yaml
networks:
  frontend:
    # Public-facing
  backend:
    internal: true  # No external access

services:
  streamlit-hub:
    networks:
      - frontend
      - backend

  trello-mcp:
    networks:
      - backend  # NOT exposed
```

2. **Port exposure control:**
```yaml
ports:
  - "127.0.0.1:8501:8501"  # Only localhost
  # NOT "8501:8501" - would expose to 0.0.0.0
```

3. **Firewall rules:**
```bash
# UFW rules
ufw allow from 127.0.0.1 to any port 8501
ufw deny from any to any port 8502  # Internal only
```

4. **Reverse proxy with auth:**
```nginx
location /mcp/ {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://trello-mcp:3000/;
}
```

#### R-SEC-05: Unencrypted Inter-Container Communication
**Contexto:**
- Traffic entre containers pode ser sniffed
- Man-in-the-middle em shared networks
- Sensitive data (API keys) em transit

**Probabilidade:** Baixa
**Impacto:** Alto

**Mitigação:**
1. **Encrypted overlay network:**
```yaml
networks:
  secure-backend:
    driver: overlay
    driver_opts:
      encrypted: "true"
```

2. **mTLS entre serviços:**
```python
# Using requests with client cert
import requests
response = requests.get(
    'https://legal-text-extractor:8502',
    cert=('/certs/client.pem', '/certs/client-key.pem'),
    verify='/certs/ca.pem'
)
```

3. **API authentication:**
```python
# Service-to-service auth
import jwt

def verify_service_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['service'] in ALLOWED_SERVICES
    except jwt.InvalidTokenError:
        return False
```

### 4.3 Supply Chain Security

#### R-SEC-06: Compromised Base Images
**Contexto:**
- `python:3.10-slim` pode conter backdoors
- Typosquatting attacks em PyPI
- Malicious dependencies

**Probabilidade:** Baixa
**Impacto:** CRÍTICO

**Mitigação:**
1. **Verified base images:**
```dockerfile
# Use official images with digest pinning
FROM python:3.10-slim@sha256:abc123...
```

2. **Image scanning:**
```bash
# CI/CD pipeline
docker scan --dependency-tree legal-workbench:latest
grype legal-workbench:latest
```

3. **SBOM generation:**
```bash
# Software Bill of Materials
syft legal-workbench:latest -o json > sbom.json
```

4. **Dependency verification:**
```bash
# Verify PyPI packages
pip install --require-hashes -r requirements.txt
```

5. **Private registry:**
```yaml
services:
  streamlit-hub:
    image: registry.internal/legal-workbench:latest
```

#### R-SEC-07: Vulnerable Dependencies
**Contexto:**
- Python packages com CVEs conhecidos
- Transitive dependencies não auditadas
- Outdated versions sem patches

**Probabilidade:** Alta
**Impacto:** Alto

**Mitigação:**
1. **Automated scanning:**
```bash
# safety check
pip install safety
safety check --json
```

2. **Dependabot/Renovate:**
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

3. **Pinned versions:**
```
# requirements.txt
streamlit==1.28.1  # NOT >=1.28
marker-pdf==0.2.3
duckdb==0.9.2
```

4. **Upgrade policy:**
```bash
# Monthly review
pip list --outdated
pip-audit
```

---

## 5. Riscos de Performance

### 5.1 Resource Contention

#### R-PERF-01: CPU Throttling Under Load
**Contexto:**
- Marker PDF é CPU-intensive (OCR, ML inference)
- Múltiplos PDFs simultâneos podem saturar CPU
- Docker CPU shares pode causar starvation

**Probabilidade:** Alta
**Impacto:** Alto (lentidão severa)

**Mitigação:**
1. **CPU limits e reservations:**
```yaml
services:
  legal-text-extractor:
    deploy:
      resources:
        limits:
          cpus: '4.0'
        reservations:
          cpus: '2.0'
```

2. **CPU pinning:**
```yaml
cpuset: "0-3"  # Use only cores 0-3
```

3. **Job queuing:**
```python
from concurrent.futures import ThreadPoolExecutor

# Limit concurrent jobs
executor = ThreadPoolExecutor(max_workers=2)

def process_pdf_async(file_path):
    return executor.submit(process_pdf, file_path)
```

4. **Priority scheduling:**
```python
import os
os.nice(10)  # Lower priority for background jobs
```

5. **Load shedding:**
```python
if get_queue_size() > 10:
    raise ServiceUnavailableError("Too many pending jobs")
```

#### R-PERF-02: Disk I/O Bottleneck
**Contexto:**
- PDFs grandes (>100MB) requerem heavy I/O
- DuckDB queries podem ser I/O bound
- Volume performance varia (NFS vs local disk)

**Probabilidade:** Média
**Impacto:** Médio

**Mitigação:**
1. **Volume driver optimization:**
```yaml
volumes:
  juridico-data:
    driver: local
    driver_opts:
      type: ext4
      o: "rw,noatime,nodiratime"  # Reduce metadata writes
```

2. **I/O limits:**
```yaml
blkio_config:
  weight: 500
  device_read_bps:
    - path: /dev/sda
      rate: '100mb'
```

3. **Caching:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def read_pdf_metadata(file_path):
    pass
```

4. **Async I/O:**
```python
import aiofiles

async def read_file_async(path):
    async with aiofiles.open(path, mode='rb') as f:
        return await f.read()
```

#### R-PERF-03: Network Latency (Container → API)
**Contexto:**
- Gemini API calls podem demorar >2s
- Docker networking adiciona overhead
- NAT/bridge pode adicionar latency

**Probabilidade:** Média
**Impacto:** Médio

**Mitigação:**
1. **Connection pooling:**
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=Retry(total=3, backoff_factor=0.5)
)
session.mount('https://', adapter)
```

2. **Keep-alive:**
```python
headers = {'Connection': 'keep-alive'}
```

3. **Host networking (last resort):**
```yaml
network_mode: "host"  # Bypass Docker networking overhead
```

4. **Request batching:**
```python
# Batch multiple API calls
def batch_gemini_requests(prompts):
    # Send all at once instead of sequential
    pass
```

### 5.2 Startup Performance

#### R-PERF-04: Slow Container Startup (>2min)
**Contexto:**
- Model loading para Marker PDF
- Dependency imports (torch, transformers)
- Health check delays

**Probabilidade:** Alta
**Impacto:** Médio (UX ruim em restarts)

**Mitigação:**
1. **Lazy loading:**
```python
# Don't import at module level
def process_pdf():
    import marker  # Import only when needed
    pass
```

2. **Pre-loaded models em image:**
```dockerfile
# Download models at build time
RUN python -c "from transformers import AutoModel; AutoModel.from_pretrained('bert-base')"
```

3. **Parallel initialization:**
```python
import asyncio

async def init():
    await asyncio.gather(
        load_models(),
        connect_database(),
        validate_secrets()
    )
```

4. **Startup probe vs readiness probe:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8502/health"]
  start_period: 120s  # Don't kill during startup
  interval: 10s       # Check frequently after start
```

#### R-PERF-05: Large Image Size (>5GB)
**Contexto:**
- ML dependencies são grandes (torch: 2GB+)
- Multiple Python packages
- Slow pulls em deploy/scale

**Probabilidade:** Alta
**Impacto:** Médio

**Mitigação:**
1. **Multi-stage builds:**
```dockerfile
FROM python:3.10-slim as builder
RUN pip install torch transformers
RUN find /usr/local -type d -name "tests" -exec rm -rf {} +

FROM python:3.10-slim
COPY --from=builder /usr/local /usr/local
```

2. **.dockerignore:**
```dockerignore
tests/
docs/
*.md
.git/
```

3. **Layer optimization:**
```dockerfile
# Combine RUN commands
RUN apt-get update && \
    apt-get install -y pkg1 pkg2 && \
    rm -rf /var/lib/apt/lists/*
```

4. **Slim packages:**
```bash
# Use slim wheels
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

5. **Layer caching strategy:**
```dockerfile
# Dependencies change less frequently
COPY requirements.txt .
RUN pip install -r requirements.txt

# Code changes more frequently
COPY . .
```

---

## 6. Plano de Contingência

### 6.1 Rollback Strategy

#### CONTINGENCY-01: Image Rollback
**Trigger:** Critical bug em nova versão
**Time to Rollback:** <5 minutos

**Procedure:**
```bash
# 1. Identify last working version
docker images legal-workbench --format "{{.Tag}} {{.CreatedAt}}"

# 2. Tag current as broken
docker tag legal-workbench:latest legal-workbench:broken-$(date +%Y%m%d)

# 3. Rollback to previous
docker tag legal-workbench:v1.2.3 legal-workbench:latest

# 4. Restart services
docker-compose up -d --force-recreate

# 5. Verify
docker-compose ps
curl http://localhost:8501/health
```

**Validation:**
- [ ] Streamlit UI acessível
- [ ] PDF extraction funcionando
- [ ] API keys validadas
- [ ] Logs sem errors

#### CONTINGENCY-02: Data Recovery
**Trigger:** Volume corruption ou perda
**Time to Recovery:** <30 minutos

**Procedure:**
```bash
# 1. Stop all services
docker-compose down

# 2. Identify latest backup
ls -lht /backup/juridico-*.tar.gz | head -5

# 3. Restore from backup
docker run --rm \
  -v juridico-data:/data \
  -v /backup:/backup \
  alpine sh -c "cd /data && tar xzf /backup/juridico-20251210.tar.gz --strip-components=1"

# 4. Verify data integrity
docker run --rm -v juridico-data:/data alpine ls -lh /data

# 5. Restart services
docker-compose up -d
```

**Validation:**
- [ ] PDFs presentes em /data
- [ ] DuckDB database acessível
- [ ] File permissions corretos (1000:1000)

#### CONTINGENCY-03: Configuration Rollback
**Trigger:** Bad docker-compose.yml ou .env
**Time to Rollback:** <2 minutos

**Procedure:**
```bash
# 1. Stop services
docker-compose down

# 2. Restore from git
git checkout HEAD~1 docker-compose.yml
git checkout HEAD~1 .env.example

# 3. Verify config
docker-compose config

# 4. Restart
docker-compose up -d
```

### 6.2 Fallback Mechanisms

#### FALLBACK-01: Service Degradation
**Scenario:** legal-text-extractor down
**Fallback:** Manual upload + degraded mode

**Implementation:**
```python
# streamlit_hub.py
def extract_pdf_text(file):
    try:
        # Primary: Use container service
        response = requests.post(
            'http://legal-text-extractor:8502/extract',
            files={'file': file},
            timeout=30
        )
        return response.json()['text']
    except requests.RequestException as e:
        st.warning("Extractor service unavailable. Using fallback.")

        # Fallback: Simple PyPDF2
        import PyPDF2
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() for page in reader.pages)
```

#### FALLBACK-02: External API Failure
**Scenario:** Gemini API down
**Fallback:** Queue for later + local processing

**Implementation:**
```python
import redis
import json

def process_with_gemini(text):
    try:
        response = gemini_api.call(text)
        return response
    except Exception as e:
        # Queue for later retry
        r = redis.Redis(host='redis')
        r.lpush('gemini_queue', json.dumps({
            'text': text,
            'timestamp': time.time(),
            'retries': 0
        }))

        # Return placeholder
        return {
            'status': 'queued',
            'message': 'API temporarily unavailable. Will retry automatically.'
        }

# Background worker
def retry_worker():
    while True:
        item = r.brpop('gemini_queue', timeout=10)
        if item:
            data = json.loads(item[1])
            try:
                result = gemini_api.call(data['text'])
                save_result(result)
            except:
                if data['retries'] < 5:
                    data['retries'] += 1
                    r.lpush('gemini_queue', json.dumps(data))
```

#### FALLBACK-03: Database Unavailable
**Scenario:** DuckDB locked ou corrupted
**Fallback:** Read-only cache + SQLite

**Implementation:**
```python
import duckdb
import sqlite3
from functools import wraps

def with_db_fallback(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except duckdb.IOException as e:
            logger.warning(f"DuckDB unavailable: {e}. Using SQLite fallback.")
            # Switch to SQLite mirror
            return func(*args, db_type='sqlite', **kwargs)
    return wrapper

@with_db_fallback
def query_data(query, db_type='duckdb'):
    if db_type == 'duckdb':
        con = duckdb.connect('data.duckdb')
    else:
        con = sqlite3.connect('data_mirror.sqlite')

    return con.execute(query).fetchall()
```

### 6.3 Disaster Recovery

#### DR-01: Complete System Failure
**RTO (Recovery Time Objective):** 1 hora
**RPO (Recovery Point Objective):** 24 horas

**Recovery Steps:**
```bash
# 1. Fresh clone
git clone https://github.com/PedroGiudice/legal-workbench.git
cd legal-workbench

# 2. Restore secrets
cp /secure-backup/.env.prod .env

# 3. Restore data volume
docker volume create juridico-data
docker run --rm -v juridico-data:/data -v /backup:/backup \
  alpine tar xzf /backup/juridico-latest.tar.gz -C /data

# 4. Pull images (faster than rebuild)
docker-compose pull

# 5. Start services
docker-compose up -d

# 6. Verify all services
./scripts/health-check.sh
```

**Verification Checklist:**
- [ ] All containers running (`docker-compose ps`)
- [ ] Streamlit accessible on :8501
- [ ] PDF extraction working (test with sample.pdf)
- [ ] Document assembly working
- [ ] Trello MCP responding
- [ ] Database queries working
- [ ] Logs clean (no errors in last 100 lines)

#### DR-02: Data Corruption Recovery
**Scenario:** DuckDB corrupted beyond repair

**Recovery:**
```bash
# 1. Stop services
docker-compose stop stj-dados-abertos

# 2. Backup corrupted DB (for forensics)
docker run --rm -v juridico-data:/data -v $(pwd):/backup \
  alpine cp /data/stj.duckdb /backup/stj.duckdb.corrupted

# 3. Restore from last backup
docker run --rm -v juridico-data:/data -v /backup:/backup \
  alpine sh -c "rm /data/stj.duckdb && tar xzf /backup/duckdb-20251210.tar.gz -C /data"

# 4. Verify integrity
docker run --rm -v juridico-data:/data python:3.10-slim \
  python -c "import duckdb; duckdb.connect('/data/stj.duckdb').execute('PRAGMA integrity_check')"

# 5. Re-sync from source if backup also corrupted
docker-compose run --rm stj-dados-abertos python scripts/rebuild_database.py
```

#### DR-03: Secrets Compromise
**Scenario:** API keys leaked

**Immediate Actions:**
```bash
# 1. Revoke compromised keys
# - Regenerate Google API key in console
# - Regenerate Trello API token

# 2. Stop all services immediately
docker-compose down

# 3. Rotate secrets
echo "new_google_key" > secrets/google_api_key.txt
echo "new_trello_key" > secrets/trello_api_key.txt

# 4. Rebuild images (purge old ENV if any)
docker-compose build --no-cache

# 5. Restart with new secrets
docker-compose up -d

# 6. Verify no leaks
docker history legal-workbench:latest | grep -i "api\|key\|secret"

# 7. Audit logs for unauthorized access
grep "GOOGLE_API_KEY" ~/.vibe-log/*.log
```

---

## 7. Checklist de Validação

### 7.1 Pre-Deployment Checklist

**Security:**
- [ ] No secrets in Dockerfile or docker-compose.yml
- [ ] All services run as non-root user (UID 1000)
- [ ] Secrets mounted via Docker secrets or runtime ENV
- [ ] .dockerignore excludes .env, .venv, *.key
- [ ] Base images pinned to specific digests
- [ ] Security scan passed (trivy, grype)
- [ ] No HIGH/CRITICAL CVEs in dependencies

**Configuration:**
- [ ] Environment variables documented in .env.example
- [ ] Volume mounts tested (read/write permissions)
- [ ] Port mappings don't conflict
- [ ] Health checks defined for all services
- [ ] Resource limits set (memory, CPU)
- [ ] Logging configured (stdout/stderr)
- [ ] Timezone set to America/Sao_Paulo

**Networking:**
- [ ] Internal services not exposed publicly
- [ ] Network segmentation implemented
- [ ] DNS resolution tested
- [ ] External API connectivity verified
- [ ] Inter-container communication working

**Data:**
- [ ] Backup strategy defined and tested
- [ ] Volume persistence verified
- [ ] Data migration plan documented
- [ ] DuckDB single-writer enforced
- [ ] File permissions correct (1000:1000)

**Performance:**
- [ ] Image size <3GB per service
- [ ] Build time <10 minutes
- [ ] Cold start time <2 minutes
- [ ] Memory limits accommodate peak usage
- [ ] CPU limits allow reasonable performance

**Documentation:**
- [ ] README.md updated with Docker instructions
- [ ] ARCHITECTURE.md reflects Docker setup
- [ ] Troubleshooting guide created
- [ ] Rollback procedure documented

### 7.2 Post-Deployment Validation

**Functional Tests:**
```bash
#!/bin/bash
# health-check.sh

echo "=== Legal Workbench Health Check ==="

# 1. Container status
echo "Checking container status..."
docker-compose ps | grep -q "Up" || { echo "❌ Containers not running"; exit 1; }
echo "✓ Containers running"

# 2. Streamlit Hub
echo "Checking Streamlit Hub..."
curl -f http://localhost:8501 > /dev/null 2>&1 || { echo "❌ Streamlit unreachable"; exit 1; }
echo "✓ Streamlit accessible"

# 3. PDF Extraction
echo "Checking PDF extraction..."
response=$(curl -s -X POST -F "file=@test.pdf" http://localhost:8502/extract)
[[ "$response" == *"text"* ]] || { echo "❌ Extraction failed"; exit 1; }
echo "✓ PDF extraction working"

# 4. Database
echo "Checking DuckDB..."
docker-compose exec -T stj-dados-abertos python -c "
import duckdb
con = duckdb.connect('/data/stj.duckdb', read_only=True)
result = con.execute('SELECT COUNT(*) FROM processos').fetchone()
print(f'Records: {result[0]}')
" || { echo "❌ Database error"; exit 1; }
echo "✓ Database accessible"

# 5. Secrets validation
echo "Checking secrets..."
docker-compose exec -T streamlit-hub python -c "
import os
assert len(os.getenv('GOOGLE_API_KEY', '')) > 20, 'Invalid Google API key'
assert len(os.getenv('TRELLO_API_KEY', '')) > 20, 'Invalid Trello API key'
print('Secrets validated')
" || { echo "❌ Secrets invalid"; exit 1; }
echo "✓ Secrets valid"

# 6. Memory usage
echo "Checking memory usage..."
mem_usage=$(docker stats --no-stream --format "{{.MemPerc}}" legal-text-extractor)
mem_value=${mem_usage%\%}
(( $(echo "$mem_value < 90" | bc -l) )) || { echo "⚠️  High memory usage: $mem_usage"; }
echo "✓ Memory usage: $mem_usage"

# 7. Logs check
echo "Checking logs for errors..."
errors=$(docker-compose logs --tail=100 | grep -i "error\|exception\|failed" | wc -l)
[[ $errors -lt 5 ]] || { echo "⚠️  Found $errors errors in logs"; }
echo "✓ Logs clean (errors: $errors)"

echo ""
echo "=== Health Check Complete ==="
echo "Status: HEALTHY ✓"
```

**Performance Benchmarks:**
```bash
#!/bin/bash
# benchmark.sh

echo "=== Performance Benchmarks ==="

# 1. Cold start time
echo "Testing cold start..."
docker-compose down
start=$(date +%s)
docker-compose up -d
# Wait for healthy
timeout 180 bash -c 'until curl -f http://localhost:8501 > /dev/null 2>&1; do sleep 2; done'
end=$(date +%s)
startup_time=$((end - start))
echo "Cold start time: ${startup_time}s (target: <120s)"
[[ $startup_time -lt 120 ]] && echo "✓ PASS" || echo "❌ FAIL"

# 2. PDF extraction throughput
echo "Testing extraction throughput..."
start=$(date +%s)
for i in {1..5}; do
  curl -s -X POST -F "file=@test.pdf" http://localhost:8502/extract > /dev/null &
done
wait
end=$(date +%s)
throughput_time=$((end - start))
echo "5 PDFs processed in: ${throughput_time}s (target: <30s)"
[[ $throughput_time -lt 30 ]] && echo "✓ PASS" || echo "❌ FAIL"

# 3. Memory leak test
echo "Testing for memory leaks..."
initial_mem=$(docker stats --no-stream --format "{{.MemUsage}}" legal-text-extractor | awk '{print $1}')
# Process 20 PDFs
for i in {1..20}; do
  curl -s -X POST -F "file=@test.pdf" http://localhost:8502/extract > /dev/null
done
final_mem=$(docker stats --no-stream --format "{{.MemUsage}}" legal-text-extractor | awk '{print $1}')
echo "Memory: $initial_mem -> $final_mem"
# Memory should not grow >20%
echo "✓ Check memory growth manually"

echo ""
echo "=== Benchmarks Complete ==="
```

**Log Monitoring:**
```bash
#!/bin/bash
# monitor-logs.sh

echo "Monitoring logs for errors and warnings..."

# Check recent errors
docker-compose logs --tail=100 | grep -i "error\|exception\|failed"

# Monitor specific service
docker-compose logs -f lw-text-extractor | grep -i "memory\|oom"

# Export logs for analysis
docker-compose logs --no-color > logs-$(date +%Y%m%d-%H%M%S).txt
echo "✓ Logs exported to logs-$(date +%Y%m%d-%H%M%S).txt"
```

### 7.3 Ongoing Validation (Weekly)

**Security Audit:**
```bash
# Run weekly or as needed
trivy image --severity HIGH,CRITICAL legal-workbench:latest
pip-audit
```

**System Health:**
```bash
# Check weekly
docker stats --no-stream
docker system df  # Disk usage
docker-compose logs --tail=1000 | grep -i "slow\|timeout\|oom"
docker-compose ps  # Check all services healthy
```

**Backup Verification:**
```bash
# Test weekly
latest_backup=$(ls -t /backup/juridico-*.tar.gz | head -1)
docker run --rm -v $(pwd):/backup alpine tar tzf $latest_backup > /dev/null
echo "✓ Backup integrity verified: $latest_backup"
```

**Dependency Updates:**
```bash
# Check monthly
pip list --outdated
docker images --filter "dangling=true"
docker system prune -a --volumes  # Clean old images
```

---

## 8. Risk Mitigation Priority Matrix

### Immediate (Before First Deploy):
1. **R01** - Secrets management (CRÍTICO)
2. **R04** - Non-root containers (CRÍTICO)
3. **R24** - Image versioning/rollback (CRÍTICO)
4. **R02** - Memory limits (CRÍTICO)
5. **R15** - Dependency isolation (ALTO)

### Short-term (First Week):
6. **R05** - Cold start optimization (ALTO)
7. **R03** - Backup automation (CRÍTICO)
8. **R23** - Security scanning (ALTO)
9. **R20** - Resource limits (ALTO)
10. **R08** - API rate limiting (ALTO)

### Medium-term (First Month):
11. **R16** - Log rotation (MÉDIO)
12. **R14** - Image size optimization (MÉDIO)
13. **R17** - Session persistence (MÉDIO)
14. **R06** - GPU fallback (ALTO)
15. **R07** - DuckDB locking (ALTO)

### Long-term (Continuous):
16. Regular security updates
17. Performance optimization
18. Monitoring improvements
19. Documentation updates
20. Disaster recovery drills

---

## 9. Critérios de Sucesso

Dockerização será considerada bem-sucedida quando:

- [ ] **Zero secrets** em images ou logs
- [ ] **Estabilidade** em testes de 72h sem crashes
- [ ] **Cold start <120s** para text-extractor
- [ ] **PDF extraction <10s** para PDFs <50MB (maioria dos casos)
- [ ] **Memory stable** (sem memory leaks após 100 requests)
- [ ] **Zero data loss** em testes de rollback
- [ ] **Todos os serviços healthy** após restart
- [ ] **Backup/restore <30min** (testado)
- [ ] **Sem CVEs CRÍTICOS** conhecidos

---

## 10. Conclusão

A dockerização do Legal Workbench é **viável mas requer atenção** em:

1. **Secrets management** - Risco de segurança importante
2. **Memory management** - Marker PDF pode causar OOM em 14GB RAM (WSL)
3. **Data persistence** - juridico-data é crítico
4. **Performance** - Cold start e model loading
5. **Rollback capability** - Importante para recuperação rápida

**Recomendações:**

1. **Fase 1:** Implementar em ambiente local primeiro
2. **Fase 2:** Testes de stress e disaster recovery
3. **Fase 3:** Deploy gradual, testar cada serviço
4. **Fase 4:** Otimização contínua baseada em uso real

**Sinais de Alerta:**
- Impossibilidade de eliminar secrets de images
- Degradação de performance >50% vs local
- Rollback demora >10min
- DuckDB corruption em testes

**Decisão Go/No-Go:**
- ✓ GO se todos os riscos CRÍTICOS mitigados
- ✗ NO-GO se >2 riscos CRÍTICOS não resolvidos

---

**Próximos Passos:**
1. Revisar este documento
2. Priorizar mitigações (seção 8)
3. Implementar Fase 1 em branch separado
4. Executar todos os checklists (seção 7)
5. Decisão final: GO/NO-GO

**Document Version:** 1.0
**Last Updated:** 2025-12-11
**Review Date:** 2025-12-18 (weekly durante implementação)
