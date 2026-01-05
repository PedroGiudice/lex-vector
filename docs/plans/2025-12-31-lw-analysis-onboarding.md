# Legal Workbench - Análise Completa para Onboarding

> **Para Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans para implementar melhorias task-by-task.

**Goal:** Documentar estado atual do projeto para onboarding de novos membros + plano de deployment Oracle Cloud

**Arquitetura:** Microserviços containerizados (Docker Compose) com frontend React SPA e 6 APIs FastAPI, orquestrados por Traefik reverse proxy

**Tech Stack:** React 18 + TypeScript 5 | FastAPI + Python 3.11 | DuckDB + Redis | Docker + Traefik

---

## 1. VISÃO GERAL DO PROJETO

### O que é o Legal Workbench?

Dashboard jurídico all-in-one para escritórios de advocacia. Uma **Single-Page Application (SPA)** React que integra múltiplos módulos:

| Módulo | Função | API Backend |
|--------|--------|-------------|
| **Hub Home** | Dashboard central | - |
| **Trello Command Center** | Gestão de tarefas/cards | api-trello:8004 |
| **Doc Assembler** | Geração de documentos via templates | api-doc-assembler:8002 |
| **STJ Search** | Busca jurisprudência STJ | api-stj:8000 |
| **Text Extractor** | Extração de texto de PDFs | api-text-extractor:8001 |
| **LEDES Converter** | Conversão para formato de faturamento | api-ledes-converter:8003 |
| **Claude Code UI** | Chat com IA (V1 e V2) | api-ccui-ws:8005 |

---

## 2. ARQUITETURA ATUAL

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRAEFIK (porta 80)                       │
│                     Reverse Proxy + Router                      │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Frontend     │     │   API Gateway   │     │   WebSocket     │
│  React SPA    │     │   (PathPrefix)  │     │   CCui WS       │
│  :3000        │     │                 │     │   :8005         │
└───────────────┘     │  /api/stj →8000 │     └─────────────────┘
                      │  /api/text→8001 │
                      │  /api/doc →8002 │
                      │  /api/ledes→8003│
                      │  /api/trello→8004
                      └─────────────────┘
                              │
                      ┌───────┴───────┐
                      │    REDIS      │
                      │    :6379      │
                      │  (Celery MQ)  │
                      └───────────────┘
                              │
                      ┌───────┴───────┐
                      │    DuckDB     │
                      │   (STJ data)  │
                      └───────────────┘
```

### Princípios Arquiteturais (North Star)

1. **Separação de Camadas**: Código (Git) | Ambiente (.venv) | Dados (~/)
2. **Uma Única Arquitetura**: Nunca manter 2 concomitantes
3. **Docker-first**: Todos serviços containerizados
4. **Traefik Router**: Roteamento automático por labels

---

## 3. STATUS ATUAL

### Frontend (React/TypeScript)

| Aspecto | Status | Detalhes |
|---------|--------|----------|
| **Framework** | ✅ Moderno | React 18.2 + Vite 5 + TypeScript 5.2 |
| **State Management** | ✅ Adequado | Zustand 4.4 (1 store por módulo) |
| **Routing** | ✅ OK | React Router 7.11 com lazy loading |
| **Styling** | ✅ OK | TailwindCSS 3.3 |
| **Testes** | ⚠️ Parcial | 8 arquivos de teste (cobertura ~15%) |
| **E2E Tests** | ❌ Ausente | Nenhum Playwright/Cypress |
| **Build** | ✅ OK | Vite produz bundle otimizado |

**Arquivos grandes que precisam refactoring:**
- `LedesConverterModule.tsx` (30KB) - candidato a split

### Backend (FastAPI Services)

| Serviço | Status | Healthcheck | Testes |
|---------|--------|-------------|--------|
| api-stj | ✅ Running | ✅ | ❓ |
| api-text-extractor | ✅ Running | ✅ | ❓ |
| api-doc-assembler | ✅ Running | ✅ | ❓ |
| api-ledes-converter | ✅ Running | ✅ | ❓ |
| api-trello | ✅ Running | ✅ | ❓ |
| api-ccui-ws | ✅ Running | ✅ | ❓ |

**Pontos positivos:**
- Todos healthchecks implementados
- Multi-stage builds (imagens otimizadas)
- Non-root users (segurança)
- Restart policies configuradas

### Infraestrutura

| Componente | Status |
|------------|--------|
| docker-compose.yml | ✅ Completo (9 serviços) |
| Traefik | ✅ Configurado (auto-discovery) |
| Redis | ✅ Running (Celery broker) |
| Volumes | ✅ Persistência configurada |
| Network | ✅ Bridge isolada |

---

## 4. DÉBITOS TÉCNICOS IDENTIFICADOS

### Críticos (Bloqueia Produção)

| # | Débito | Impacto | Esforço |
|---|--------|---------|---------|
| 1 | **Sem testes E2E** | Regressões não detectadas | Médio |
| 2 | **Cobertura de testes ~15%** | Bugs em produção | Alto |
| 3 | **Sem CI/CD pipeline** | Deploy manual, erros humanos | Médio |
| 4 | **Secrets hardcoded** | Risco de segurança | Baixo |

### Importantes (Afeta Manutenção)

| # | Débito | Impacto | Esforço |
|---|--------|---------|---------|
| 5 | CCui V1 e V2 coexistem | Confusão, código duplicado | Baixo |
| 6 | LedesConverter muito grande | Difícil manutenção | Médio |
| 7 | Logs não centralizados | Debug difícil em prod | Médio |
| 8 | Sem rate limiting global | Vulnerável a DDoS | Baixo |

### Nice-to-Have

| # | Débito | Impacto | Esforço |
|---|--------|---------|---------|
| 9 | Sem documentação de API (OpenAPI exportado) | Onboarding lento | Baixo |
| 10 | Sem monitoring (Prometheus/Grafana) | Sem visibilidade | Alto |

---

## 5. PLANO DE MELHORIAS

### Fase 1: Estabilização (1-2 semanas)

```markdown
### Task 1.1: Adicionar testes E2E básicos

**Files:**
- Create: `legal-workbench/frontend/e2e/smoke.spec.ts`
- Create: `legal-workbench/frontend/playwright.config.ts`
- Modify: `legal-workbench/frontend/package.json`

**Step 1: Instalar Playwright**
Run: `cd legal-workbench/frontend && bun add -D @playwright/test`

**Step 2: Configurar Playwright**
Criar playwright.config.ts com base URL http://localhost

**Step 3: Escrever smoke test**
Testar navegação entre módulos principais

**Step 4: Adicionar script no package.json**
"test:e2e": "playwright test"

**Step 5: Commit**
git commit -m "test: add Playwright E2E smoke tests"
```

```markdown
### Task 1.2: Remover CCui V1 (deprecated)

**Files:**
- Delete: `legal-workbench/frontend/src/pages/CCuiAssistantModule.tsx`
- Delete: `legal-workbench/frontend/src/components/ccui-assistant/`
- Modify: `legal-workbench/frontend/src/routes.tsx`

**Step 1: Remover rota /ccui-assistant**
**Step 2: Remover componentes órfãos**
**Step 3: Atualizar Hub Home (remover link)**
**Step 4: Commit**
```

### Fase 2: CI/CD + Secrets (1 semana)

```markdown
### Task 2.1: Criar GitHub Actions workflow

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/deploy.yml`

**CI Pipeline:**
1. Lint (ESLint + Prettier)
2. Type check (tsc --noEmit)
3. Unit tests (jest)
4. E2E tests (Playwright)
5. Docker build (sem push)

**Deploy Pipeline:**
1. Triggered on main merge
2. Build e push images para registry
3. SSH para servidor e docker-compose pull + up
```

```markdown
### Task 2.2: Externalizar secrets

**Files:**
- Create: `legal-workbench/.env.example`
- Modify: `legal-workbench/docker-compose.yml`

**Secrets a externalizar:**
- TRELLO_API_KEY
- TRELLO_API_TOKEN
- REDIS_PASSWORD (adicionar)
- API keys futuras
```

### Fase 3: Observabilidade (2 semanas)

```markdown
### Task 3.1: Adicionar logging estruturado

**Cada API:**
- Adicionar python-json-logger
- Formato: JSON com timestamp, level, service, request_id
- Output: stdout (Docker logs coleta)

### Task 3.2: Adicionar Prometheus metrics

**Por serviço:**
- prometheus-fastapi-instrumentator
- Métricas: requests_total, latency_histogram, errors
- Endpoint: /metrics

### Task 3.3: Configurar Grafana (opcional)

**Novo serviço no docker-compose:**
- grafana:3000
- Dashboards pré-configurados
```

---

## 6. PLANO DE DEPLOYMENT - ORACLE CLOUD

### Opção Recomendada: OCI Compute + Docker Compose

**Por que esta opção:**
- Menor complexidade (não precisa de Kubernetes)
- Compatível com estrutura atual
- Free Tier disponível (4 OCPUs, 24GB RAM)
- Custo zero para começar

### Arquitetura no Oracle Cloud

```
┌─────────────────────────────────────────────────────────────────┐
│                    OCI Virtual Cloud Network                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Public Subnet (10.0.0.0/24)                 │   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │         Compute Instance (Always Free)             │  │   │
│  │  │         VM.Standard.A1.Flex                        │  │   │
│  │  │         4 OCPU / 24GB RAM                          │  │   │
│  │  │                                                    │  │   │
│  │  │    ┌──────────────────────────────────────────┐   │  │   │
│  │  │    │           Docker Compose                 │   │  │   │
│  │  │    │   (mesma estrutura atual)                │   │  │   │
│  │  │    └──────────────────────────────────────────┘   │  │   │
│  │  │                                                    │  │   │
│  │  │    Block Volume (50GB) → /data                    │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Security List                                │   │
│  │              - Ingress: 80, 443, 22                       │   │
│  │              - Egress: All                                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Tasks para Deploy Oracle

```markdown
### Task 6.1: Criar conta Oracle Cloud

**Step 1:** Acessar cloud.oracle.com/free
**Step 2:** Criar conta (cartão de crédito necessário, mas não cobra)
**Step 3:** Ativar Always Free Tier

### Task 6.2: Provisionar infraestrutura via Terraform

**Files:**
- Create: `infra/oracle/main.tf`
- Create: `infra/oracle/variables.tf`
- Create: `infra/oracle/outputs.tf`

**Recursos:**
- VCN + Subnet
- Compute Instance (A1.Flex 4 OCPU)
- Block Volume (50GB para dados)
- Security List (80, 443, 22)

### Task 6.3: Configurar instância

**Step 1:** SSH para instância
**Step 2:** Instalar Docker + Docker Compose
```bash
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker opc
# Docker Compose v2
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Step 3:** Clonar repositório
**Step 4:** Configurar .env com secrets
**Step 5:** docker-compose up -d

### Task 6.4: Configurar domínio e HTTPS

**Step 1:** Apontar DNS para IP público da instância
**Step 2:** Modificar Traefik para Let's Encrypt
```yaml
# Adicionar ao docker-compose.yml
command:
  - "--certificatesresolvers.letsencrypt.acme.email=seu@email.com"
  - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
  - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
```

### Task 6.5: Configurar backup automático

**Step 1:** Criar script de backup
```bash
#!/bin/bash
# /home/opc/backup.sh
docker-compose exec -T redis redis-cli BGSAVE
docker cp $(docker-compose ps -q stj):/app/db/stj.duckdb /backup/
rclone copy /backup oracle-object-storage:legal-workbench-backups/
```

**Step 2:** Adicionar ao cron
```
0 3 * * * /home/opc/backup.sh
```
```

---

## 7. PRÓXIMOS PASSOS IMEDIATOS

1. **Hoje:** Revisar este plano com stakeholders
2. **Semana 1:** Implementar Task 1.1 e 1.2 (testes + cleanup CCui)
3. **Semana 2:** Implementar Task 2.1 (CI/CD)
4. **Semana 3:** Criar conta Oracle e provisionar infra (Tasks 6.1-6.3)
5. **Semana 4:** Deploy em produção + HTTPS (Tasks 6.4-6.5)

---

## 8. REFERÊNCIAS

### Documentação do Projeto
- `ARCHITECTURE.md` - North Star arquitetural
- `DISASTER_HISTORY.md` - Lições aprendidas
- `legal-workbench/docker/README.md` - Guia Docker completo

### Oracle Cloud
- [Deploy Microservices to Kubernetes](https://docs.oracle.com/en/solutions/deploy-microservices/index.html)
- [OCI Docker Compose Stack Sample](https://github.com/oracle-samples/orm-docker-compose-stack-sample)
- [Setting Up Docker on Oracle Cloud Free Tier](https://sunnydsouza.hashnode.dev/setting-up-docker-and-docker-compose-on-oracle-clouds-always-free-tier-instance)
- [Oracle Cloud Adoption Framework - Microservices](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/microservices.htm)

---

**Documento gerado em:** 2025-12-31
**Autor:** Technical Director (Claude)
**Status:** Aguardando aprovação
