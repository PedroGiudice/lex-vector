# HTTPS Legal Workbench - Complete Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Configurar HTTPS com Let's Encrypt para legalworkbench.duckdns.org, integrar Claude Code UI ao docker-compose.yml, e estabelecer sincronia permanente Repo-VM.

**Architecture:** Traefik v3.6.5 como reverse proxy com Let's Encrypt HTTP-01 challenge, redirect automatico HTTP->HTTPS, todos os servicos via websecure entrypoint, deploy via rsync + docker compose.

**Tech Stack:** Traefik v3, Let's Encrypt, Docker Compose, rsync, SSH

**Constraints:**
- Todas as modificacoes no REPO local (nunca na VM diretamente)
- Deploy via rsync sincroniza repo -> VM
- Rebuild containers apos deploy para aplicar labels

---

## Pre-requisitos Verificados

| Item | Status |
|------|--------|
| DNS legalworkbench.duckdns.org -> 137.131.201.119 | OK |
| SSH acesso opc@137.131.201.119 | OK |
| Docker Compose na VM | OK |
| Modulo shared/ no repo | OK |

---

## Task 1: Criar estrutura Traefik no repo

**Files:**
- Create: `legal-workbench/docker/traefik/dynamic.yml`
- Create: `legal-workbench/docker/traefik/.gitkeep` (para letsencrypt/)

**Step 1: Criar diretorio traefik**

```bash
mkdir -p /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench/docker/traefik
```

**Step 2: Criar dynamic.yml para servicos externos (Ollama)**

```yaml
# Traefik Dynamic Configuration for External Services
# This file configures routers for services outside Docker Compose

http:
  routers:
    # Ollama API - For HotCocoa personalization
    ollama:
      rule: "PathPrefix(`/api/ollama`)"
      entryPoints:
        - websecure
      priority: 15
      service: ollama
      middlewares:
        - ollama-strip
        - ollama-auth
        - auth
      tls:
        certResolver: letsencrypt

  middlewares:
    ollama-strip:
      stripPrefix:
        prefixes:
          - "/api/ollama"

    ollama-auth:
      basicAuth:
        users:
          - "hotcocoa:$apr1$VbOqcKRh$nTLOfydOQFwadT.2xtsRY1"

  services:
    ollama:
      loadBalancer:
        servers:
          - url: "http://172.18.0.1:11434"
```

**Step 3: Criar .gitkeep para diretorio letsencrypt**

```bash
mkdir -p /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench/docker/traefik/letsencrypt
touch /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench/docker/traefik/letsencrypt/.gitkeep
```

**Step 4: Adicionar letsencrypt ao .gitignore**

Adicionar em `legal-workbench/.gitignore`:
```
# Let's Encrypt certificates (generated on server)
docker/traefik/letsencrypt/acme.json
```

**Step 5: Commit**

```bash
git add legal-workbench/docker/traefik/
git add legal-workbench/.gitignore
git commit -m "feat(traefik): add dynamic config structure for HTTPS"
```

---

## Task 2: Criar servico CCUI WebSocket no repo

**Files:**
- Create: `legal-workbench/docker/services/ccui-ws/Dockerfile`
- Create: `legal-workbench/docker/services/ccui-ws/main.py`
- Create: `legal-workbench/docker/services/ccui-ws/requirements.txt`

**Step 1: Criar diretorio ccui-ws**

```bash
mkdir -p /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench/docker/services/ccui-ws
```

**Step 2: Criar Dockerfile**

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

**Step 3: Criar requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
websockets==14.1
sentry-sdk[fastapi]>=1.40.0
```

**Step 4: Criar main.py**

O arquivo main.py completo com WebSocket backend para Claude Code UI (copiado do container existente, ~300 linhas).

**Step 5: Commit**

```bash
git add legal-workbench/docker/services/ccui-ws/
git commit -m "feat(ccui-ws): add WebSocket backend service for Claude Code UI"
```

---

## Task 3: Atualizar docker-compose.yml com HTTPS e CCUI

**Files:**
- Modify: `legal-workbench/docker-compose.yml`

**Step 1: Atualizar reverse-proxy com HTTPS**

Substituir secao `reverse-proxy`:

```yaml
  reverse-proxy:
    image: traefik:v3.6.5
    command:
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      # Entrypoints
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      # Redirect HTTP -> HTTPS
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      # Let's Encrypt
      - "--certificatesresolvers.letsencrypt.acme.email=pedro@lexvector.com.br"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      # File provider for external services
      - "--providers.file.directory=/etc/traefik/dynamic"
      - "--providers.file.watch=true"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./docker/traefik:/etc/traefik/dynamic:ro
      - ./docker/traefik/letsencrypt:/letsencrypt
    networks:
      - legal-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.middlewares.auth.basicauth.users=PGR:$$apr1$$srv7aVBj$$lh5oVstYMwaEi5vB6ppgC/,MCBS:$$apr1$$tFXQKb/8$$EfbMbctlMOT5RsYlUkDtI/,ABP:$$apr1$$kvqG8i1i$$RE9g6iKuWL/VoPnNOTQmU1"
```

**Step 2: Atualizar frontend-react labels para HTTPS**

```yaml
  frontend-react:
    build: ./frontend
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.react.rule=Host(`legalworkbench.duckdns.org`) && PathPrefix(`/`)"
      - "traefik.http.routers.react.entrypoints=websecure"
      - "traefik.http.routers.react.tls=true"
      - "traefik.http.routers.react.tls.certresolver=letsencrypt"
      - "traefik.http.routers.react.priority=1"
      - "traefik.http.routers.react.middlewares=auth"
      - "traefik.http.services.react.loadbalancer.server.port=3000"
    networks:
      - legal-network
    depends_on:
      - reverse-proxy
      - api-doc-assembler
```

**Step 3: Atualizar api-stj labels para HTTPS**

```yaml
  api-stj:
    # ... build config stays same ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.stj.rule=Host(`legalworkbench.duckdns.org`) && PathPrefix(`/api/stj`)"
      - "traefik.http.routers.stj.entrypoints=websecure"
      - "traefik.http.routers.stj.tls=true"
      - "traefik.http.routers.stj.tls.certresolver=letsencrypt"
      - "traefik.http.routers.stj.priority=10"
      - "traefik.http.middlewares.stj-strip.stripprefix.prefixes=/api/stj"
      - "traefik.http.routers.stj.middlewares=stj-strip"
      - "traefik.http.services.stj.loadbalancer.server.port=8000"
```

**Step 4: Atualizar api-text-extractor labels para HTTPS**

```yaml
  api-text-extractor:
    # ... build config stays same ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.text.rule=Host(`legalworkbench.duckdns.org`) && PathPrefix(`/api/text`)"
      - "traefik.http.routers.text.entrypoints=websecure"
      - "traefik.http.routers.text.tls=true"
      - "traefik.http.routers.text.tls.certresolver=letsencrypt"
      - "traefik.http.routers.text.priority=10"
      - "traefik.http.middlewares.text-strip.stripprefix.prefixes=/api/text"
      - "traefik.http.middlewares.text-buffering.buffering.maxRequestBodyBytes=104857600"
      - "traefik.http.routers.text.middlewares=text-strip,text-buffering"
      - "traefik.http.services.text.loadbalancer.server.port=8001"
```

**Step 5: Atualizar api-doc-assembler labels para HTTPS**

```yaml
  api-doc-assembler:
    # ... build config stays same ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.doc.rule=Host(`legalworkbench.duckdns.org`) && PathPrefix(`/api/doc`)"
      - "traefik.http.routers.doc.entrypoints=websecure"
      - "traefik.http.routers.doc.tls=true"
      - "traefik.http.routers.doc.tls.certresolver=letsencrypt"
      - "traefik.http.routers.doc.priority=10"
      - "traefik.http.middlewares.doc-strip.stripprefix.prefixes=/api/doc"
      - "traefik.http.routers.doc.middlewares=doc-strip"
      - "traefik.http.services.doc.loadbalancer.server.port=8002"
```

**Step 6: Atualizar api-trello labels para HTTPS**

```yaml
  api-trello:
    # ... build config stays same ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.trello.rule=Host(`legalworkbench.duckdns.org`) && PathPrefix(`/api/trello`)"
      - "traefik.http.routers.trello.entrypoints=websecure"
      - "traefik.http.routers.trello.tls=true"
      - "traefik.http.routers.trello.tls.certresolver=letsencrypt"
      - "traefik.http.routers.trello.priority=10"
      - "traefik.http.middlewares.trello-strip.stripprefix.prefixes=/api/trello"
      - "traefik.http.routers.trello.middlewares=trello-strip"
      - "traefik.http.services.trello.loadbalancer.server.port=8004"
```

**Step 7: Atualizar api-ledes-converter labels para HTTPS**

```yaml
  api-ledes-converter:
    # ... build config stays same ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.ledes.rule=Host(`legalworkbench.duckdns.org`) && PathPrefix(`/api/ledes`)"
      - "traefik.http.routers.ledes.entrypoints=websecure"
      - "traefik.http.routers.ledes.tls=true"
      - "traefik.http.routers.ledes.tls.certresolver=letsencrypt"
      - "traefik.http.routers.ledes.priority=10"
      - "traefik.http.middlewares.ledes-strip.stripprefix.prefixes=/api/ledes"
      - "traefik.http.routers.ledes.middlewares=ledes-strip"
      - "traefik.http.services.ledes.loadbalancer.server.port=8003"
```

**Step 8: Adicionar servico api-ccui-ws**

Adicionar antes da secao Redis:

```yaml
  # ============================================================
  # CCUI WebSocket - Claude Code UI Backend
  # ============================================================
  api-ccui-ws:
    build:
      context: .
      dockerfile: docker/services/ccui-ws/Dockerfile
    labels:
      - "traefik.enable=true"
      # Chat API endpoint
      - "traefik.http.routers.ccui-chat.rule=Host(`legalworkbench.duckdns.org`) && PathPrefix(`/api/chat`)"
      - "traefik.http.routers.ccui-chat.entrypoints=websecure"
      - "traefik.http.routers.ccui-chat.tls=true"
      - "traefik.http.routers.ccui-chat.tls.certresolver=letsencrypt"
      - "traefik.http.routers.ccui-chat.priority=15"
      # WebSocket endpoint
      - "traefik.http.routers.ccui-ws.rule=Host(`legalworkbench.duckdns.org`) && PathPrefix(`/ws`)"
      - "traefik.http.routers.ccui-ws.entrypoints=websecure"
      - "traefik.http.routers.ccui-ws.tls=true"
      - "traefik.http.routers.ccui-ws.tls.certresolver=letsencrypt"
      - "traefik.http.routers.ccui-ws.priority=20"
      - "traefik.http.services.ccui-ws.loadbalancer.server.port=8005"
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - APP_VERSION=${APP_VERSION:-1.0.0}
      - LOG_LEVEL=INFO
      - SENTRY_DSN=${SENTRY_DSN:-}
    networks:
      - legal-network
    depends_on:
      - reverse-proxy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

**Step 9: Validar YAML localmente**

```bash
cd /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench
docker compose config --quiet && echo "YAML valido"
```

Expected: `YAML valido`

**Step 10: Commit**

```bash
git add legal-workbench/docker-compose.yml
git commit -m "feat(lw): HTTPS Let's Encrypt + CCUI integration"
```

---

## Task 4: Abrir porta 443 no firewall Oracle

**Step 1: Verificar firewall atual**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "sudo firewall-cmd --list-ports"
```

**Step 2: Abrir porta 443**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "sudo firewall-cmd --permanent --add-port=443/tcp && sudo firewall-cmd --reload"
```

Expected: `success`

**Step 3: Verificar OCI Security List**

> **NOTA:** A Security List da VCN Oracle precisa ter porta 443 aberta.
> Se o teste final falhar, verificar no Oracle Console:
> Networking -> Virtual Cloud Networks -> VCN -> Security Lists -> Ingress Rules
> Adicionar regra: Source 0.0.0.0/0, Protocol TCP, Destination Port 443

**Step 4: Verificar portas abertas**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "sudo firewall-cmd --list-ports | grep 443"
```

Expected: `443/tcp` na lista

---

## Task 5: Deploy para VM

**Step 1: Sincronizar repo com VM**

```bash
rsync -avz --delete \
  --exclude='.venv' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='coverage' \
  --exclude='dist' \
  -e "ssh -i ~/.ssh/oci_lw" \
  /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench/ \
  opc@137.131.201.119:/home/opc/lex-vector/legal-workbench/
```

**Step 2: Criar diretorio letsencrypt com permissoes**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "mkdir -p /home/opc/lex-vector/legal-workbench/docker/traefik/letsencrypt && chmod 700 /home/opc/lex-vector/legal-workbench/docker/traefik/letsencrypt"
```

**Step 3: Parar containers antigos**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "cd /home/opc/lex-vector/legal-workbench && docker compose down"
```

**Step 4: Rebuild e iniciar todos os containers**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "cd /home/opc/lex-vector/legal-workbench && docker compose build --no-cache && docker compose up -d"
```

**Step 5: Verificar containers**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep legal-workbench"
```

Expected: Todos containers `Up` e `healthy`

---

## Task 6: Verificar certificado Let's Encrypt

**Step 1: Verificar logs do Traefik**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "docker logs legal-workbench-reverse-proxy-1 2>&1 | grep -i 'acme\|letsencrypt\|certificate' | tail -20"
```

Expected: Mensagens sobre obtencao de certificado bem-sucedida

**Step 2: Verificar arquivo acme.json**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "ls -la /home/opc/lex-vector/legal-workbench/docker/traefik/letsencrypt/"
```

Expected: Arquivo `acme.json` criado

**Step 3: Testar HTTPS via curl**

```bash
curl -I https://legalworkbench.duckdns.org/ --max-time 10
```

Expected: `HTTP/2 200` ou `HTTP/1.1 401` (401 = auth required, certificado OK)

**Step 4: Verificar certificado**

```bash
echo | openssl s_client -connect legalworkbench.duckdns.org:443 -servername legalworkbench.duckdns.org 2>/dev/null | openssl x509 -noout -issuer -dates
```

Expected: Issuer contendo "Let's Encrypt", dates validas

---

## Task 7: Testar servicos

**Step 1: Testar frontend (com auth)**

```bash
curl -I -u PGR:Chicago00@ https://legalworkbench.duckdns.org/
```

Expected: `HTTP/2 200`

**Step 2: Testar API STJ**

```bash
curl -s https://legalworkbench.duckdns.org/api/stj/health | jq .
```

Expected: `{"status": "healthy", ...}`

**Step 3: Testar CCUI WebSocket health**

```bash
curl -s https://legalworkbench.duckdns.org/api/chat/health 2>/dev/null || curl -s -u PGR:Chicago00@ https://legalworkbench.duckdns.org/api/chat/health
```

Expected: Resposta JSON com status

**Step 4: Testar redirect HTTP -> HTTPS**

```bash
curl -I http://legalworkbench.duckdns.org/ 2>&1 | head -5
```

Expected: `HTTP/1.1 301` ou `308` com `Location: https://...`

---

## Task 8: Remover container CCUI antigo (PM2)

**Step 1: Verificar PM2**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "pm2 list"
```

**Step 2: Parar e remover processo PM2 antigo**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "pm2 delete claude-ui 2>/dev/null || echo 'Processo nao existia'"
```

**Step 3: Salvar estado PM2**

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "pm2 save"
```

---

## Task 9: Commit final e push

**Step 1: Verificar status git**

```bash
cd /home/cmr-auto/claude-work/repos/lex-vector
git status
```

**Step 2: Push para remote**

```bash
git push origin work/session-20260120-012414
```

**Step 3: Criar PR (opcional)**

```bash
gh pr create --title "feat(lw): HTTPS Let's Encrypt + CCUI integration" --body "## Summary
- Configuracao HTTPS com Let's Encrypt para legalworkbench.duckdns.org
- Integracao do Claude Code UI WebSocket ao docker-compose.yml
- Estrutura Traefik para config dinamica
- Redirect automatico HTTP -> HTTPS

## Test Plan
- [ ] Site acessivel via HTTPS
- [ ] Certificado Let's Encrypt valido
- [ ] Todos os servicos respondem via HTTPS
- [ ] CCUI WebSocket funciona
- [ ] Redirect HTTP -> HTTPS funciona"
```

---

## Rollback

Se algo falhar:

```bash
# 1. Reverter para versao anterior
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "cd /home/opc/lex-vector/legal-workbench && git checkout HEAD~1 -- docker-compose.yml && docker compose down && docker compose up -d"

# 2. OU reverter localmente e re-deploy
git revert HEAD
# ... rsync novamente
```

---

## URLs Finais

| Servico | URL |
|---------|-----|
| Legal Workbench | https://legalworkbench.duckdns.org/ |
| API STJ | https://legalworkbench.duckdns.org/api/stj/health |
| API Doc | https://legalworkbench.duckdns.org/api/doc/health |
| API Text | https://legalworkbench.duckdns.org/api/text/health |
| CCUI Chat | https://legalworkbench.duckdns.org/api/chat/health |
| CCUI WebSocket | wss://legalworkbench.duckdns.org/ws |

---

## Mecanismo de Sincronia Repo-VM

Para evitar drift futuro, seguir SEMPRE este fluxo:

1. **Modificar no REPO** (nunca na VM)
2. **Commit e push** para branch
3. **rsync** para VM
4. **docker compose build && up -d** na VM

Script sugerido (`deploy.sh`):

```bash
#!/bin/bash
rsync -avz --delete \
  --exclude='.venv' --exclude='node_modules' --exclude='__pycache__' \
  --exclude='.git' --exclude='coverage' --exclude='dist' \
  -e "ssh -i ~/.ssh/oci_lw" \
  /home/cmr-auto/claude-work/repos/lex-vector/legal-workbench/ \
  opc@137.131.201.119:/home/opc/lex-vector/legal-workbench/

ssh -i ~/.ssh/oci_lw opc@137.131.201.119 "cd /home/opc/lex-vector/legal-workbench && docker compose build && docker compose up -d"
```
