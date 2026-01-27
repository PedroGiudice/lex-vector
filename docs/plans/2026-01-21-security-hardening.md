# Security Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Corrigir 5 issues de seguranca (1 critica, 4 altas) identificadas pela auditoria Gemini do Legal Workbench.

**Architecture:** Mover credenciais Basic Auth para arquivo `.htpasswd` separado, adicionar USER nao-root ao CCUI-WS, corrigir volume de templates no doc-assembler, e padronizar healthchecks no docker-compose.yml.

**Tech Stack:** Docker Compose, Traefik v3.6.5, FastAPI, htpasswd (Apache utils)

---

## Issues a Corrigir

| Severidade | Issue | Arquivo |
|------------|-------|---------|
| CRITICO | Basic Auth hardcoded no docker-compose.yml | `legal-workbench/docker-compose.yml:35` |
| ALTO | CCUI-WS rodando como root | `legal-workbench/docker/services/ccui-ws/Dockerfile` |
| ALTO | Volume sobrescreve templates do doc-assembler | `legal-workbench/docker-compose.yml:154` |
| ALTO | Healthchecks faltando em servicos (docker-compose) | `legal-workbench/docker-compose.yml` |
| INFO | Docker socket com :ro (risco mitigado) | N/A - ja esta readonly |

**Nota:** Docker socket com `:ro` ja mitiga o risco. Proxy seria overkill para este ambiente.

---

## Task 1: Criar arquivo .htpasswd para Basic Auth

**Files:**
- Create: `legal-workbench/docker/traefik/.htpasswd`
- Modify: `legal-workbench/.gitignore`

**Step 1: Criar arquivo .htpasswd com credenciais atuais**

O arquivo deve conter os usuarios atuais (extraidos do docker-compose.yml linha 35):
- PGR
- MCBS
- ABP

Formato htpasswd (ja no formato correto, apenas remover escape de `$`):
```
PGR:$apr1$srv7aVBj$lh5oVstYMwaEi5vB6ppgC/
MCBS:$apr1$tFXQKb/8$EfbMbctlMOT5RsYlUkDtI/
ABP:$apr1$kvqG8i1i$RE9g6iKuWL/VoPnNOTQmU1
```

**Step 2: Adicionar .htpasswd ao .gitignore**

Adicionar ao final de `legal-workbench/.gitignore`:
```
# Basic Auth credentials (sensitive)
docker/traefik/.htpasswd
```

**Step 3: Commit**

```bash
git add legal-workbench/docker/traefik/.htpasswd legal-workbench/.gitignore
git commit -m "feat(security): add .htpasswd file for Basic Auth credentials"
```

---

## Task 2: Atualizar Traefik para usar .htpasswd

**Files:**
- Modify: `legal-workbench/docker-compose.yml:27-35`

**Step 1: Adicionar volume para .htpasswd**

Na secao `volumes` do servico `reverse-proxy` (linha 27-30), adicionar:
```yaml
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./docker/traefik:/etc/traefik/dynamic:ro
      - ./docker/traefik/letsencrypt:/letsencrypt
      - ./docker/traefik/.htpasswd:/etc/traefik/.htpasswd:ro
```

**Step 2: Atualizar middleware auth para usar arquivo**

Na secao `labels` do servico `reverse-proxy` (linha 35), substituir:
```yaml
# DE:
      - "traefik.http.middlewares.auth.basicauth.users=PGR:$$apr1$$srv7aVBj$$lh5oVstYMwaEi5vB6ppgC/,MCBS:$$apr1$$tFXQKb/8$$EfbMbctlMOT5RsYlUkDtI/,ABP:$$apr1$$kvqG8i1i$$RE9g6iKuWL/VoPnNOTQmU1"
# PARA:
      - "traefik.http.middlewares.auth.basicauth.usersfile=/etc/traefik/.htpasswd"
```

**Step 3: Commit**

```bash
git add legal-workbench/docker-compose.yml
git commit -m "feat(security): use .htpasswd file instead of hardcoded credentials"
```

---

## Task 3: Adicionar USER nao-root ao CCUI-WS Dockerfile

**Files:**
- Modify: `legal-workbench/docker/services/ccui-ws/Dockerfile`

**Step 1: Adicionar criacao de usuario e ajustar permissoes**

O Dockerfile atual:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY docker/services/ccui-ws/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/services/ccui-ws/main.py .
COPY shared/ /app/shared/

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
```

Substituir por:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck and create non-root user
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

COPY docker/services/ccui-ws/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/services/ccui-ws/main.py .
COPY shared/ /app/shared/

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
```

**Step 2: Commit**

```bash
git add legal-workbench/docker/services/ccui-ws/Dockerfile
git commit -m "feat(security): run ccui-ws as non-root user"
```

---

## Task 4: Corrigir volume de templates no doc-assembler

**Files:**
- Modify: `legal-workbench/docker-compose.yml:152-154`

**Step 1: Entender o problema**

O Dockerfile do doc-assembler (linha 41) copia templates:
```dockerfile
COPY ferramentas/legal-doc-assembler/templates/ ./templates/
```

Mas o docker-compose.yml (linha 154) monta um volume vazio em cima:
```yaml
    volumes:
      - shared-data:/data
      - templates:/app/templates  # PROBLEMA: sobrescreve templates copiados
```

**Step 2: Alterar path do volume para custom-templates**

No docker-compose.yml, alterar:
```yaml
# DE (linhas 152-154):
    volumes:
      - shared-data:/data
      - templates:/app/templates

# PARA:
    volumes:
      - shared-data:/data
      - templates:/app/custom-templates
```

E atualizar o environment para apontar para o novo path (se necessario):
```yaml
    environment:
      - DATA_PATH=/data
      - TEMPLATES_PATH=/app/templates
      - CUSTOM_TEMPLATES_PATH=/app/custom-templates
      - SENTRY_DSN=${SENTRY_DSN:-}
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - APP_VERSION=${APP_VERSION:-1.0.0}
```

**Step 3: Commit**

```bash
git add legal-workbench/docker-compose.yml
git commit -m "fix(doc-assembler): prevent volume from overwriting built-in templates"
```

---

## Task 5: Adicionar healthchecks faltantes ao docker-compose.yml

**Files:**
- Modify: `legal-workbench/docker-compose.yml`

**Analise do estado atual:**

| Servico | Healthcheck no docker-compose | Healthcheck no Dockerfile |
|---------|------------------------------|---------------------------|
| reverse-proxy | NAO | Traefik built-in |
| frontend-react | NAO | SIM (curl) |
| api-stj | NAO | SIM (python httpx) |
| api-text-extractor | NAO | SIM (curl) |
| api-doc-assembler | NAO | SIM (curl) |
| api-trello | NAO | SIM (python httpx) |
| api-ledes-converter | SIM | SIM |
| api-ccui-ws | SIM | SIM |
| redis | SIM | N/A |
| prometheus | SIM | N/A |
| grafana | SIM | N/A |

**Decisao:** Os healthchecks ja estao definidos nos Dockerfiles. O docker-compose.yml pode herda-los automaticamente. Para consistencia visual e controle explicito, vamos adicionar `healthcheck:` nos servicos que tem Dockerfile com healthcheck.

**Step 1: Adicionar healthcheck ao reverse-proxy**

Apos linha 31 (antes de `networks:`), adicionar:
```yaml
    healthcheck:
      test: ["CMD", "traefik", "healthcheck"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**Step 2: Adicionar healthcheck ao frontend-react**

Apos linha 50 (antes de `networks:`), adicionar:
```yaml
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**Step 3: Adicionar healthcheck ao api-stj**

Apos linha 84 (antes de `networks:`), adicionar:
```yaml
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8000/health', timeout=5).raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Step 4: Adicionar healthcheck ao api-text-extractor**

Apos linha 129 (antes de `networks:`), adicionar:
```yaml
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

**Step 5: Adicionar healthcheck ao api-doc-assembler**

Apos linha 160 (antes de `networks:`), adicionar:
```yaml
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**Step 6: Adicionar healthcheck ao api-trello**

Apos linha 186 (antes de `networks:`), adicionar:
```yaml
    healthcheck:
      test: ["CMD", "python", "-c", "import httpx; httpx.get('http://localhost:8004/health').raise_for_status()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

**Step 7: Commit**

```bash
git add legal-workbench/docker-compose.yml
git commit -m "feat(docker): add explicit healthchecks to all services"
```

---

## Task 6: Deploy e Verificacao

**Step 1: Criar arquivo .htpasswd na VM (antes do rsync)**

SSH na VM e criar o arquivo manualmente (pois esta no .gitignore):
```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "mkdir -p /home/opc/lex-vector/legal-workbench/docker/traefik && cat > /home/opc/lex-vector/legal-workbench/docker/traefik/.htpasswd << 'EOF'
PGR:\$apr1\$srv7aVBj\$lh5oVstYMwaEi5vB6ppgC/
MCBS:\$apr1\$tFXQKb/8\$EfbMbctlMOT5RsYlUkDtI/
ABP:\$apr1\$kvqG8i1i\$RE9g6iKuWL/VoPnNOTQmU1
EOF"
```

**Step 2: Sincronizar repositorio com VM**

```bash
rsync -avz --delete \
  --exclude=node_modules --exclude=.git --exclude='.env*' --exclude='docker/traefik/letsencrypt/acme.json' \
  -e "ssh -i ~/.ssh/oci_lw" \
  legal-workbench/ opc@137.131.201.119:/home/opc/lex-vector/legal-workbench/
```

**Step 3: Rebuild e reiniciar containers**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "cd /home/opc/lex-vector/legal-workbench && \
  docker compose build --no-cache reverse-proxy api-ccui-ws api-doc-assembler && \
  docker compose up -d"
```

**Step 4: Verificar healthchecks**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

Esperado: Todos os containers com status `healthy`

**Step 5: Verificar autenticacao Basic Auth**

```bash
# Sem credenciais - deve retornar 401
curl -s -o /dev/null -w "%{http_code}" https://legalworkbench.duckdns.org/

# Com credenciais - deve retornar 200
curl -s -o /dev/null -w "%{http_code}" -u "PGR:senha" https://legalworkbench.duckdns.org/
```

**Step 6: Verificar CCUI-WS rodando como non-root**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "docker exec legal-workbench-api-ccui-ws-1 whoami"
```

Esperado: `appuser`

**Step 7: Commit final (se necessario ajustes)**

Se tudo estiver funcionando, criar commit de documentacao:
```bash
git add -A
git commit -m "docs: update security hardening status"
```

---

## Verificacao Final

| Check | Comando | Esperado |
|-------|---------|----------|
| Basic Auth funciona | `curl -u PGR:senha https://legalworkbench.duckdns.org/` | 200 OK |
| CCUI-WS non-root | `docker exec ... whoami` | appuser |
| Healthchecks ativos | `docker ps` | healthy em todos |
| Templates preservados | `docker exec api-doc-assembler ls /app/templates` | Arquivos presentes |

---

*Plano criado: 2026-01-21*
*Estimativa: 6 tasks, ~30 minutos*
