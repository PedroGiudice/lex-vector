# Plano: Polimento do Deploy Oracle Cloud

**Objetivo:** Securizar o deploy atual adicionando autenticacao e fechando endpoints expostos.

**VM:** 64.181.162.38 | **SSH:** `ssh -i ~/.ssh/oci_lw opc@64.181.162.38`

---

## Task 1: Fechar Dashboard Traefik

**Problema:** Dashboard exposto publicamente em :8080 mostra toda infraestrutura.

**Acao:** Remover exposicao da porta 8080 no docker-compose.yml

```yaml
# ANTES
ports:
  - "80:80"
  - "8080:8080"   # Remover esta linha

# DEPOIS
ports:
  - "80:80"
```

**Arquivo:** `legal-workbench/docker-compose.yml` (linha 13-14)

---

## Task 2: Adicionar Basic Auth no Frontend

**Usuarios:**
- PGR / Chicago00@
- MCBS / Chicago00@
- ABP / Chicago00@

**Acao:** Configurar middleware de autenticacao no Traefik

**Step 1:** Gerar hashes das senhas (htpasswd format)
```bash
# Na VM, gerar hash para cada usuario
echo $(htpasswd -nb PGR 'Chicago00@') | sed -e s/\\$/\\$\\$/g
echo $(htpasswd -nb MCBS 'Chicago00@') | sed -e s/\\$/\\$\\$/g
echo $(htpasswd -nb ABP 'Chicago00@') | sed -e s/\\$/\\$\\$/g
```

**Step 2:** Adicionar middleware no docker-compose.yml (servico reverse-proxy)
```yaml
reverse-proxy:
  image: traefik:v3.6.5
  command:
    - "--api.insecure=false"  # Desabilitar dashboard inseguro
    - "--providers.docker=true"
    - "--providers.docker.exposedbydefault=false"
    - "--entrypoints.web.address=:80"
  labels:
    - "traefik.http.middlewares.auth.basicauth.users=PGR:$$hash1,MCBS:$$hash2,ABP:$$hash3"
  ports:
    - "80:80"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
  networks:
    - legal-network
```

**Step 3:** Aplicar middleware no frontend-react
```yaml
frontend-react:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.react.rule=PathPrefix(`/`)"
    - "traefik.http.routers.react.entrypoints=web"
    - "traefik.http.routers.react.priority=1"
    - "traefik.http.routers.react.middlewares=auth"  # ADICIONAR
    - "traefik.http.services.react.loadbalancer.server.port=3000"
```

---

## Task 3: Preparar Sentry (Opcional)

**Estado:** Codigo pronto, so falta DSN no .env

**Acao futura:** Quando tiver o DSN do Sentry, adicionar ao .env:
```bash
# Adicionar ao .env na VM
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
VITE_SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

---

## Task 4: Redeploy

```bash
# 1. Atualizar docker-compose.yml na VM (git pull ou editar)
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "cd ~/lex-vector && git pull"

# 2. Rebuild e restart
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "cd ~/lex-vector/legal-workbench && sudo docker compose up -d --force-recreate reverse-proxy frontend-react"
```

---

## Verificacao

1. Acessar http://64.181.162.38/ - deve pedir usuario/senha
2. Testar login com PGR/Chicago00@
3. Acessar http://64.181.162.38:8080 - deve dar timeout/connection refused
4. Testar APIs: `curl http://64.181.162.38/api/stj/health` (APIs ficam sem auth para integracao)

---

## Arquivos Modificados

| Arquivo | Mudanca |
|---------|---------|
| `legal-workbench/docker-compose.yml` | Remover porta 8080, adicionar middleware auth |

---

## Resultado Esperado

- Dashboard Traefik fechado
- Frontend protegido com basic auth (3 usuarios)
- APIs continuam acessiveis (para futuras integracoes)
- Sentry preparado para ativacao futura
