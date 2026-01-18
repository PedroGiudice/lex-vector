# HTTPS com Let's Encrypt no Traefik - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Habilitar HTTPS com certificado Let's Encrypt gratuito para legalworkbench.duckdns.org

**Architecture:** Traefik v3.6.5 como reverse proxy, Let's Encrypt via HTTP challenge (TLS-ALPN-01 ou HTTP-01), redirecionamento automatico HTTP -> HTTPS

**Tech Stack:** Traefik v3, Let's Encrypt, Docker Compose

---

## Task 1: Atualizar docker-compose.yml com HTTPS

**Files:**
- Modify: `~/lex-vector/legal-workbench/docker-compose.yml` (VM Oracle via SSH)

**Step 1: Adicionar entrypoint HTTPS e certificateResolvers**

Modificar a secao `command` do traefik:

```yaml
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
      # File provider
      - "--providers.file.directory=/etc/traefik/dynamic"
      - "--providers.file.watch=true"
```

**Step 2: Adicionar porta 443 e volume para certificados**

```yaml
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./docker/traefik:/etc/traefik/dynamic:ro
      - ./docker/traefik/letsencrypt:/letsencrypt
```

**Step 3: Verificar sintaxe**

```bash
ssh opc@64.181.162.38 "cd ~/lex-vector/legal-workbench && docker compose config --quiet && echo 'YAML valido'"
```
Expected: `YAML valido`

**Step 4: Commit na VM (opcional)**

---

## Task 2: Criar diretorio para certificados

**Files:**
- Create: `~/lex-vector/legal-workbench/docker/traefik/letsencrypt/` (diretorio)

**Step 1: Criar diretorio com permissoes corretas**

```bash
ssh opc@64.181.162.38 "mkdir -p ~/lex-vector/legal-workbench/docker/traefik/letsencrypt && chmod 700 ~/lex-vector/legal-workbench/docker/traefik/letsencrypt"
```
Expected: Sem output (sucesso)

---

## Task 3: Atualizar routers Docker para HTTPS

**Files:**
- Modify: `~/lex-vector/legal-workbench/docker-compose.yml` (labels dos servicos)

**Step 1: Atualizar frontend-react labels**

Adicionar `websecure` entrypoint e TLS:

```yaml
  frontend-react:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.react.rule=Host(`legalworkbench.duckdns.org`) && PathPrefix(`/`)"
      - "traefik.http.routers.react.entrypoints=websecure"
      - "traefik.http.routers.react.tls=true"
      - "traefik.http.routers.react.tls.certresolver=letsencrypt"
      - "traefik.http.routers.react.priority=1"
      - "traefik.http.routers.react.middlewares=auth"
      - "traefik.http.services.react.loadbalancer.server.port=3000"
```

**Step 2: Atualizar todos os outros routers (api-stj, api-doc-assembler, etc)**

Mesmo padrao: adicionar `Host()`, `websecure`, `tls`, `certresolver`

---

## Task 4: Atualizar dynamic.yml para ClaudeCodeUI

**Files:**
- Modify: `~/lex-vector/legal-workbench/docker/traefik/dynamic.yml`

**Step 1: Atualizar routers para HTTPS**

```yaml
http:
  routers:
    claudeui:
      rule: "Host(`legalworkbench.duckdns.org`) && PathPrefix(`/claude-ui`)"
      entryPoints:
        - websecure
      priority: 15
      service: claudeui
      middlewares:
        - claudeui-strip
      tls:
        certResolver: letsencrypt

    claudeui-ws:
      rule: "Host(`legalworkbench.duckdns.org`) && (PathPrefix(`/claude-ui/ws`) || PathPrefix(`/claude-ui/shell`))"
      entryPoints:
        - websecure
      priority: 25
      service: claudeui
      middlewares:
        - claudeui-strip
      tls:
        certResolver: letsencrypt

  middlewares:
    claudeui-strip:
      stripPrefix:
        prefixes:
          - "/claude-ui"

  services:
    claudeui:
      loadBalancer:
        servers:
          - url: "http://172.18.0.1:3002"
```

---

## Task 5: Abrir porta 443 no firewall Oracle

**Step 1: Verificar se iptables permite 443**

```bash
ssh opc@64.181.162.38 "sudo iptables -L INPUT -n | grep 443 || echo 'Porta 443 nao liberada'"
```

**Step 2: Liberar porta 443 se necessario**

```bash
ssh opc@64.181.162.38 "sudo firewall-cmd --permanent --add-port=443/tcp && sudo firewall-cmd --reload"
```

**Nota:** Security List da VCN Oracle ja deve ter 443 aberta (verificar no console Oracle se falhar)

---

## Task 6: Reiniciar Traefik e testar

**Step 1: Recriar container Traefik**

```bash
ssh opc@64.181.162.38 "cd ~/lex-vector/legal-workbench && docker compose up -d reverse-proxy"
```

**Step 2: Verificar logs (aguardar certificado)**

```bash
ssh opc@64.181.162.38 "docker logs legal-workbench-reverse-proxy-1 2>&1 | tail -30"
```
Expected: Mensagens sobre ACME/Let's Encrypt obtendo certificado

**Step 3: Testar HTTPS**

```bash
curl -I https://legalworkbench.duckdns.org/claude-ui/
```
Expected: `HTTP/2 200` ou `HTTP/1.1 200`

---

## Task 7: Verificacao final

**Step 1: Testar no browser**

- Abrir: `https://legalworkbench.duckdns.org/`
- Verificar: Cadeado verde no browser
- Verificar: Certificado emitido por Let's Encrypt

**Step 2: Testar ClaudeCodeUI**

- Abrir: `https://legalworkbench.duckdns.org/claude-ui/`
- Verificar: Interface carrega corretamente
- Verificar: WebSocket conecta (terminal funciona)

---

## Rollback

Se algo falhar:

```bash
# Reverter para HTTP apenas
ssh opc@64.181.162.38 "cd ~/lex-vector/legal-workbench && git checkout docker-compose.yml && docker compose up -d reverse-proxy"
```

---

## URLs Finais

| Servico | URL |
|---------|-----|
| Legal Workbench | https://legalworkbench.duckdns.org/ |
| ClaudeCodeUI | https://legalworkbench.duckdns.org/claude-ui/ |
