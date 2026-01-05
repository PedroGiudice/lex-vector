# Legal Workbench - Production-Grade Implementation Plan

> **Para Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans para implementar task-by-task.

**Goal:** Transformar Legal Workbench em produto production-ready, deploy real, zero shortcuts

**Critério de Sucesso:** Sistema que você apresentaria a investidores sem vergonha

---

## PRINCÍPIOS DESTE PLANO

1. **Zero local hosting** - Cloud-native from day 1
2. **Zero hardcoded secrets** - Vault ou managed secrets
3. **Zero manual deploy** - GitOps completo
4. **Testes antes de código** - TDD rigoroso
5. **Observabilidade first** - Se não tem métrica, não existe
6. **Security by default** - Não "depois a gente adiciona"

---

## FASE 1: FUNDAÇÃO DE QUALIDADE

### Task 1.1: Cobertura de Testes Frontend (80%+)

**Objetivo:** Nenhum merge sem cobertura mínima

**Files:**
- Create: `legal-workbench/frontend/vitest.config.ts`
- Create: `legal-workbench/frontend/src/**/*.test.tsx` (para cada componente)
- Modify: `legal-workbench/frontend/package.json`

**Step 1: Migrar de Jest para Vitest**

```bash
cd legal-workbench/frontend
bun remove jest ts-jest @types/jest
bun add -D vitest @vitest/coverage-v8 @testing-library/react @testing-library/user-event jsdom
```

**Step 2: Criar vitest.config.ts**

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'html'],
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        'src/main.tsx',
      ],
    },
  },
  resolve: {
    alias: { '@': '/src' },
  },
})
```

**Step 3: Criar setup de testes**

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})
```

**Step 4: Escrever testes para cada store**

```typescript
// src/store/__tests__/documentStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useDocumentStore } from '../documentStore'

describe('documentStore', () => {
  beforeEach(() => {
    useDocumentStore.setState({ documents: [], isLoading: false })
  })

  it('should add document to state', () => {
    const store = useDocumentStore.getState()
    store.addDocument({ id: '1', name: 'test.pdf' })
    expect(useDocumentStore.getState().documents).toHaveLength(1)
  })

  it('should handle loading state', () => {
    useDocumentStore.getState().setLoading(true)
    expect(useDocumentStore.getState().isLoading).toBe(true)
  })
})
```

**Step 5: Escrever testes para cada hook**

**Step 6: Escrever testes para componentes UI**

**Step 7: Adicionar scripts no package.json**

```json
{
  "scripts": {
    "test": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:ci": "vitest run --coverage --reporter=junit"
  }
}
```

**Step 8: Commit**

```bash
git add .
git commit -m "test: migrate to Vitest with 80% coverage threshold"
```

---

### Task 1.2: Testes E2E com Playwright

**Objetivo:** Testar fluxos críticos de usuário

**Files:**
- Create: `legal-workbench/frontend/playwright.config.ts`
- Create: `legal-workbench/frontend/e2e/*.spec.ts`
- Modify: `legal-workbench/frontend/package.json`

**Step 1: Instalar Playwright**

```bash
cd legal-workbench/frontend
bun add -D @playwright/test
npx playwright install --with-deps chromium
```

**Step 2: Configurar Playwright**

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'bun run preview',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

**Step 3: Escrever testes E2E para fluxos críticos**

```typescript
// e2e/navigation.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('should navigate to all modules from hub', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('Legal Workbench')

    // Navigate to each module
    const modules = ['trello', 'doc-assembler', 'stj', 'text-extractor', 'ledes-converter']
    for (const module of modules) {
      await page.click(`[href="/${module}"]`)
      await expect(page).toHaveURL(`/${module}`)
      await page.goBack()
    }
  })
})

// e2e/stj-search.spec.ts
test.describe('STJ Search', () => {
  test('should search and display results', async ({ page }) => {
    await page.goto('/stj')
    await page.fill('[data-testid="search-input"]', 'habeas corpus')
    await page.click('[data-testid="search-button"]')
    await expect(page.locator('[data-testid="results-list"]')).toBeVisible()
  })
})

// e2e/document-upload.spec.ts
test.describe('Document Upload', () => {
  test('should upload PDF and extract text', async ({ page }) => {
    await page.goto('/text-extractor')
    const fileChooserPromise = page.waitForEvent('filechooser')
    await page.click('[data-testid="upload-zone"]')
    const fileChooser = await fileChooserPromise
    await fileChooser.setFiles('./e2e/fixtures/sample.pdf')
    await expect(page.locator('[data-testid="extraction-result"]')).toBeVisible({ timeout: 30000 })
  })
})
```

**Step 4: Commit**

```bash
git commit -m "test: add Playwright E2E tests for critical flows"
```

---

### Task 1.3: Testes de Contrato para APIs

**Objetivo:** Garantir que APIs cumprem contrato esperado

**Files:**
- Create: `legal-workbench/docker/services/*/tests/`
- Create: `legal-workbench/docker/services/*/pytest.ini`

**Step 1: Adicionar pytest a cada serviço**

```txt
# requirements.txt (cada serviço)
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.25.0
pytest-cov>=4.1.0
```

**Step 2: Escrever testes de contrato**

```python
# docker/services/stj-api/tests/test_api_contract.py
import pytest
from httpx import AsyncClient
from main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_search_returns_valid_schema(client):
    response = await client.get("/api/v1/search", params={"q": "test"})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert isinstance(data["results"], list)

@pytest.mark.asyncio
async def test_search_pagination(client):
    response = await client.get("/api/v1/search", params={"q": "test", "page": 1, "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 10
```

**Step 3: Commit**

```bash
git commit -m "test: add API contract tests with pytest"
```

---

## FASE 2: CI/CD PIPELINE

### Task 2.1: GitHub Actions - CI Pipeline

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Criar workflow completo**

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'
  PYTHON_VERSION: '3.11'

jobs:
  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v1
      - run: cd legal-workbench/frontend && bun install
      - run: cd legal-workbench/frontend && bun run lint
      - run: cd legal-workbench/frontend && bun run type-check

  frontend-test:
    runs-on: ubuntu-latest
    needs: frontend-lint
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v1
      - run: cd legal-workbench/frontend && bun install
      - run: cd legal-workbench/frontend && bun run test:ci
      - uses: codecov/codecov-action@v3
        with:
          files: ./legal-workbench/frontend/coverage/lcov.info
          flags: frontend

  frontend-e2e:
    runs-on: ubuntu-latest
    needs: frontend-test
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v1
      - run: cd legal-workbench/frontend && bun install
      - run: npx playwright install --with-deps chromium
      - run: cd legal-workbench/frontend && bun run build
      - run: cd legal-workbench/frontend && bun run test:e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: legal-workbench/frontend/playwright-report/

  backend-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [stj-api, text-extractor, doc-assembler, ledes-converter, trello-mcp, ccui-ws]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: |
          cd legal-workbench/docker/services/${{ matrix.service }}
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx
          pytest --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3
        with:
          files: ./legal-workbench/docker/services/${{ matrix.service }}/coverage.xml
          flags: ${{ matrix.service }}

  docker-build:
    runs-on: ubuntu-latest
    needs: [frontend-test, backend-test]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - run: |
          cd legal-workbench
          docker compose build --parallel

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
```

**Step 2: Commit**

```bash
git commit -m "ci: add comprehensive GitHub Actions pipeline"
```

---

### Task 2.2: GitHub Actions - CD Pipeline

**Files:**
- Create: `.github/workflows/deploy.yml`

**Step 1: Criar workflow de deploy**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ghcr.io/${{ github.repository_owner }}/legal-workbench

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    strategy:
      matrix:
        service: [frontend, stj-api, text-extractor, doc-assembler, ledes-converter, trello-mcp, ccui-ws]
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v5
        with:
          context: ./legal-workbench
          file: ./legal-workbench/docker/services/${{ matrix.service }}/Dockerfile
          push: true
          tags: |
            ${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:${{ github.sha }}
            ${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Oracle Cloud
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.OCI_HOST }}
          username: opc
          key: ${{ secrets.OCI_SSH_KEY }}
          script: |
            cd /home/opc/legal-workbench
            git pull origin main
            docker compose pull
            docker compose up -d --remove-orphans
            docker system prune -f

      - name: Verify deployment
        run: |
          sleep 30
          curl -f https://${{ secrets.PRODUCTION_DOMAIN }}/health || exit 1

      - name: Notify on success
        uses: slackapi/slack-github-action@v1.24.0
        with:
          payload: |
            {
              "text": "✅ Legal Workbench deployed to production",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "Commit: ${{ github.sha }}\nBy: ${{ github.actor }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

**Step 2: Commit**

```bash
git commit -m "ci: add CD pipeline with Oracle Cloud deployment"
```

---

## FASE 3: SEGURANÇA

### Task 3.1: Secrets Management com HashiCorp Vault

**Objetivo:** Zero secrets em código ou environment variables plaintext

**Files:**
- Create: `infra/vault/config.hcl`
- Modify: `legal-workbench/docker-compose.yml`
- Create: `legal-workbench/docker/scripts/vault-init.sh`

**Step 1: Adicionar Vault ao docker-compose**

```yaml
# docker-compose.yml
services:
  vault:
    image: hashicorp/vault:1.15
    container_name: vault
    cap_add:
      - IPC_LOCK
    volumes:
      - vault-data:/vault/data
      - ./infra/vault/config.hcl:/vault/config/config.hcl
    ports:
      - "8200:8200"
    environment:
      VAULT_ADDR: 'http://0.0.0.0:8200'
    command: server -config=/vault/config/config.hcl
    networks:
      - legal-network
    healthcheck:
      test: ["CMD", "vault", "status"]
      interval: 10s
      timeout: 5s
      retries: 3
```

**Step 2: Configurar Vault**

```hcl
# infra/vault/config.hcl
storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1  # Enable TLS in production!
}

api_addr = "http://vault:8200"
ui = true
```

**Step 3: Script de inicialização**

```bash
#!/bin/bash
# docker/scripts/vault-init.sh

# Initialize Vault
vault operator init -key-shares=5 -key-threshold=3 > /vault/init-keys.txt

# Unseal
vault operator unseal $(grep 'Unseal Key 1' /vault/init-keys.txt | awk '{print $4}')
vault operator unseal $(grep 'Unseal Key 2' /vault/init-keys.txt | awk '{print $4}')
vault operator unseal $(grep 'Unseal Key 3' /vault/init-keys.txt | awk '{print $4}')

# Login
export VAULT_TOKEN=$(grep 'Initial Root Token' /vault/init-keys.txt | awk '{print $4}')
vault login $VAULT_TOKEN

# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Store secrets
vault kv put secret/legal-workbench \
  trello_api_key="$TRELLO_API_KEY" \
  trello_api_token="$TRELLO_API_TOKEN" \
  redis_password="$(openssl rand -base64 32)"

# Create policy
vault policy write legal-workbench - <<EOF
path "secret/data/legal-workbench" {
  capabilities = ["read"]
}
EOF

# Create AppRole for services
vault auth enable approle
vault write auth/approle/role/legal-workbench \
  token_policies="legal-workbench" \
  token_ttl=1h \
  token_max_ttl=4h
```

**Step 4: Modificar serviços para ler do Vault**

```python
# Cada serviço Python - config.py
import hvac
import os

def get_secrets():
    client = hvac.Client(url=os.getenv('VAULT_ADDR', 'http://vault:8200'))
    client.auth.approle.login(
        role_id=os.getenv('VAULT_ROLE_ID'),
        secret_id=os.getenv('VAULT_SECRET_ID')
    )
    return client.secrets.kv.v2.read_secret_version(
        path='legal-workbench'
    )['data']['data']

SECRETS = get_secrets()
TRELLO_API_KEY = SECRETS['trello_api_key']
TRELLO_API_TOKEN = SECRETS['trello_api_token']
```

**Step 5: Commit**

```bash
git commit -m "security: add HashiCorp Vault for secrets management"
```

---

### Task 3.2: Rate Limiting e WAF

**Files:**
- Modify: `legal-workbench/docker-compose.yml` (Traefik middleware)
- Create: `legal-workbench/traefik/dynamic.yml`

**Step 1: Configurar rate limiting no Traefik**

```yaml
# traefik/dynamic.yml
http:
  middlewares:
    rate-limit:
      rateLimit:
        average: 100
        period: 1s
        burst: 200

    security-headers:
      headers:
        browserXssFilter: true
        contentTypeNosniff: true
        frameDeny: true
        sslRedirect: true
        stsIncludeSubdomains: true
        stsPreload: true
        stsSeconds: 31536000
        customFrameOptionsValue: "SAMEORIGIN"
        contentSecurityPolicy: "default-src 'self'"

    ip-whitelist:
      ipWhiteList:
        sourceRange:
          - "10.0.0.0/8"
          - "172.16.0.0/12"
          - "192.168.0.0/16"
```

**Step 2: Aplicar middlewares às rotas**

```yaml
# docker-compose.yml - labels dos serviços
labels:
  - "traefik.http.routers.api-stj.middlewares=rate-limit@file,security-headers@file"
```

**Step 3: Commit**

```bash
git commit -m "security: add rate limiting and security headers via Traefik"
```

---

### Task 3.3: HTTPS com Let's Encrypt

**Files:**
- Modify: `legal-workbench/docker-compose.yml`

**Step 1: Configurar Traefik para HTTPS automático**

```yaml
# docker-compose.yml
services:
  reverse-proxy:
    image: traefik:v3.0
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt
    labels:
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
```

**Step 2: Commit**

```bash
git commit -m "security: add automatic HTTPS with Let's Encrypt"
```

---

## FASE 4: OBSERVABILIDADE

### Task 4.1: Logging Estruturado

**Objetivo:** Logs JSON, correlacionados, queryable

**Files:**
- Create: `legal-workbench/shared/logging_config.py`
- Modify: Cada serviço `main.py`

**Step 1: Criar configuração de logging compartilhada**

```python
# shared/logging_config.py
import logging
import json
import sys
from datetime import datetime
import uuid

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": getattr(record, 'service', 'unknown'),
            "request_id": getattr(record, 'request_id', None),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging(service_name: str):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    logger = logging.getLogger()
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)

    # Add service name to all logs
    old_factory = logging.getLogRecordFactory()
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record
    logging.setLogRecordFactory(record_factory)

    return logger
```

**Step 2: Middleware para request_id**

```python
# shared/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
import logging

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add to logging context
        logger = logging.getLogger()
        for handler in logger.handlers:
            handler.addFilter(lambda record: setattr(record, 'request_id', request_id) or True)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

**Step 3: Commit**

```bash
git commit -m "observability: add structured JSON logging with request correlation"
```

---

### Task 4.2: Métricas com Prometheus

**Files:**
- Modify: Cada serviço `main.py`
- Create: `legal-workbench/docker/prometheus/prometheus.yml`
- Modify: `legal-workbench/docker-compose.yml`

**Step 1: Adicionar métricas a cada serviço FastAPI**

```python
# Cada main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

**Step 2: Adicionar Prometheus ao docker-compose**

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:v2.47.0
    volumes:
      - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - legal-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prometheus.rule=Host(`prometheus.${DOMAIN}`)"
      - "traefik.http.services.prometheus.loadbalancer.server.port=9090"
```

**Step 3: Configurar Prometheus**

```yaml
# docker/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'legal-workbench'
    static_configs:
      - targets:
        - 'api-stj:8000'
        - 'api-text-extractor:8001'
        - 'api-doc-assembler:8002'
        - 'api-ledes-converter:8003'
        - 'api-trello:8004'
        - 'api-ccui-ws:8005'
    metrics_path: /metrics

  - job_name: 'traefik'
    static_configs:
      - targets: ['reverse-proxy:8080']
```

**Step 4: Commit**

```bash
git commit -m "observability: add Prometheus metrics collection"
```

---

### Task 4.3: Dashboards com Grafana

**Files:**
- Create: `legal-workbench/docker/grafana/provisioning/`
- Modify: `legal-workbench/docker-compose.yml`

**Step 1: Adicionar Grafana**

```yaml
# docker-compose.yml
services:
  grafana:
    image: grafana/grafana:10.2.0
    volumes:
      - grafana-data:/var/lib/grafana
      - ./docker/grafana/provisioning:/etc/grafana/provisioning
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: 'false'
    networks:
      - legal-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.${DOMAIN}`)"
      - "traefik.http.routers.grafana.tls.certresolver=letsencrypt"
```

**Step 2: Provisionar datasource**

```yaml
# docker/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

**Step 3: Criar dashboard JSON**

```json
// docker/grafana/provisioning/dashboards/legal-workbench.json
{
  "title": "Legal Workbench Overview",
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "sum(rate(http_requests_total[5m])) by (service)",
          "legendFormat": "{{service}}"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) by (service)",
          "legendFormat": "{{service}}"
        }
      ]
    },
    {
      "title": "P99 Latency",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))",
          "legendFormat": "{{service}}"
        }
      ]
    }
  ]
}
```

**Step 4: Commit**

```bash
git commit -m "observability: add Grafana dashboards for monitoring"
```

---

### Task 4.4: Alerting

**Files:**
- Create: `legal-workbench/docker/prometheus/alerts.yml`

**Step 1: Criar regras de alerta**

```yaml
# docker/prometheus/alerts.yml
groups:
  - name: legal-workbench
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"

      - alert: HighLatency
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P99 latency above 2 seconds"

      - alert: DiskSpaceLow
        expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space below 10%"
```

**Step 2: Commit**

```bash
git commit -m "observability: add Prometheus alerting rules"
```

---

## FASE 5: INFRAESTRUTURA ORACLE CLOUD

### Task 5.1: Terraform para OCI

**Files:**
- Create: `infra/oracle/main.tf`
- Create: `infra/oracle/variables.tf`
- Create: `infra/oracle/network.tf`
- Create: `infra/oracle/compute.tf`
- Create: `infra/oracle/outputs.tf`

**Step 1: Provider e variáveis**

```hcl
# infra/oracle/main.tf
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket   = "terraform-state"
    key      = "legal-workbench/terraform.tfstate"
    region   = "us-ashburn-1"
    endpoint = "https://<namespace>.compat.objectstorage.us-ashburn-1.oraclecloud.com"
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# infra/oracle/variables.tf
variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "region" { default = "us-ashburn-1" }
variable "compartment_ocid" {}
variable "ssh_public_key" {}
variable "domain" {}
```

**Step 2: Network**

```hcl
# infra/oracle/network.tf
resource "oci_core_vcn" "legal_workbench" {
  compartment_id = var.compartment_ocid
  cidr_block     = "10.0.0.0/16"
  display_name   = "legal-workbench-vcn"
  dns_label      = "legalworkbench"
}

resource "oci_core_subnet" "public" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.legal_workbench.id
  cidr_block        = "10.0.1.0/24"
  display_name      = "public-subnet"
  dns_label         = "public"
  security_list_ids = [oci_core_security_list.public.id]
  route_table_id    = oci_core_route_table.public.id
}

resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.legal_workbench.id
  display_name   = "internet-gateway"
}

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.legal_workbench.id
  display_name   = "public-route-table"
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.igw.id
  }
}

resource "oci_core_security_list" "public" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.legal_workbench.id
  display_name   = "public-security-list"

  ingress_security_rules {
    protocol = "6"  # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 80
      max = 80
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 443
      max = 443
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}
```

**Step 3: Compute**

```hcl
# infra/oracle/compute.tf
data "oci_core_images" "oracle_linux" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Standard.A1.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_instance" "legal_workbench" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  shape               = "VM.Standard.A1.Flex"
  display_name        = "legal-workbench-prod"

  shape_config {
    ocpus         = 4
    memory_in_gbs = 24
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux.images[0].id
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public.id
    assign_public_ip = true
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(<<-EOF
      #!/bin/bash
      # Install Docker
      dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
      dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
      systemctl enable --now docker
      usermod -aG docker opc

      # Clone repository
      git clone https://github.com/YOUR_ORG/legal-workbench.git /home/opc/legal-workbench
      chown -R opc:opc /home/opc/legal-workbench
    EOF
    )
  }
}

resource "oci_core_volume" "data" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "legal-workbench-data"
  size_in_gbs         = 100
}

resource "oci_core_volume_attachment" "data" {
  attachment_type = "paravirtualized"
  instance_id     = oci_core_instance.legal_workbench.id
  volume_id       = oci_core_volume.data.id
  device          = "/dev/oracleoci/oraclevdb"
}
```

**Step 4: Outputs**

```hcl
# infra/oracle/outputs.tf
output "instance_public_ip" {
  value = oci_core_instance.legal_workbench.public_ip
}

output "instance_id" {
  value = oci_core_instance.legal_workbench.id
}

output "ssh_command" {
  value = "ssh opc@${oci_core_instance.legal_workbench.public_ip}"
}
```

**Step 5: Commit**

```bash
git commit -m "infra: add Terraform configuration for Oracle Cloud"
```

---

### Task 5.2: Backup Automático para Object Storage

**Files:**
- Create: `legal-workbench/docker/scripts/backup.sh`
- Create: `infra/oracle/object-storage.tf`

**Step 1: Criar bucket**

```hcl
# infra/oracle/object-storage.tf
resource "oci_objectstorage_bucket" "backups" {
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "legal-workbench-backups"
  access_type    = "NoPublicAccess"
  versioning     = "Enabled"

  lifecycle_rule {
    name      = "delete-old-backups"
    action    = "DELETE"
    time_unit = "DAYS"
    time_amount = 30
  }
}
```

**Step 2: Script de backup**

```bash
#!/bin/bash
# docker/scripts/backup.sh
set -euo pipefail

BACKUP_DIR="/backup/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# Backup DuckDB
docker exec api-stj cp /app/db/stj.duckdb /tmp/stj.duckdb
docker cp api-stj:/tmp/stj.duckdb "$BACKUP_DIR/"

# Backup Redis
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb "$BACKUP_DIR/"

# Backup volumes
docker run --rm \
  -v shared-data:/source:ro \
  -v "$BACKUP_DIR:/backup" \
  alpine tar czf /backup/shared-data.tar.gz -C /source .

# Upload to OCI Object Storage
oci os object put \
  --bucket-name legal-workbench-backups \
  --file "$BACKUP_DIR/stj.duckdb" \
  --name "$(date +%Y-%m-%d)/stj.duckdb"

oci os object put \
  --bucket-name legal-workbench-backups \
  --file "$BACKUP_DIR/dump.rdb" \
  --name "$(date +%Y-%m-%d)/redis-dump.rdb"

oci os object put \
  --bucket-name legal-workbench-backups \
  --file "$BACKUP_DIR/shared-data.tar.gz" \
  --name "$(date +%Y-%m-%d)/shared-data.tar.gz"

# Cleanup local
rm -rf "$BACKUP_DIR"

echo "Backup completed: $(date)"
```

**Step 3: Crontab**

```cron
# Backup diário às 3h
0 3 * * * /home/opc/legal-workbench/docker/scripts/backup.sh >> /var/log/backup.log 2>&1
```

**Step 4: Commit**

```bash
git commit -m "infra: add automated backup to OCI Object Storage"
```

---

## CHECKLIST FINAL

### Antes do Go-Live

- [ ] Todos os testes passando (unit, integration, E2E)
- [ ] Cobertura de testes > 80%
- [ ] CI/CD pipeline funcionando
- [ ] Secrets no Vault (nenhum hardcoded)
- [ ] HTTPS configurado com Let's Encrypt
- [ ] Rate limiting ativo
- [ ] Prometheus coletando métricas
- [ ] Grafana dashboards configurados
- [ ] Alertas configurados e testados
- [ ] Backup automático funcionando
- [ ] Terraform aplicado com sucesso
- [ ] Domínio apontando para IP público
- [ ] Smoke test em produção OK

### Métricas de Sucesso

| Métrica | Target |
|---------|--------|
| Uptime | 99.9% |
| P99 Latency | < 500ms |
| Error Rate | < 0.1% |
| Test Coverage | > 80% |
| Deploy Time | < 10 min |
| MTTR | < 1 hora |

---

**Documento criado:** 2025-12-31
**Autor:** Technical Director
**Status:** Production-Grade Plan - Aguardando Execução
