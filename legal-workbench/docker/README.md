# Legal Workbench - Docker Setup

Dashboard jurídico containerizado para extração de texto, montagem de documentos e consulta de jurisprudência.

---

## Quick Start

```bash
# 1. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas API keys (GEMINI_API_KEY, TRELLO_API_KEY, TRELLO_API_TOKEN)

# 2. Subir todos os serviços
docker-compose up -d

# 3. Verificar status
docker-compose ps
```

Acesse: **http://localhost:8501**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network (Bridge)                   │
│                      172.28.0.0/16                           │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  streamlit-hub (Frontend)                          │     │
│  │  Port: 8501 → Interface Web                        │     │
│  └──────┬─────────────────────────────────────────────┘     │
│         │                                                    │
│         ├──────────┬──────────┬──────────┬──────────┐       │
│         │          │          │          │          │       │
│  ┌──────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐ │
│  │  text-   │ │  doc-  │ │  stj-  │ │ trello │ │ redis  │ │
│  │extractor │ │assembler│ │  api   │ │  -mcp  │ │ (queue)│ │
│  │  8001    │ │  8002  │ │  8003  │ │  8004  │ │  6379  │ │
│  │  +5555   │ │        │ │        │ │        │ │        │ │
│  │ (flower) │ │        │ │        │ │        │ │        │ │
│  └──────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │
│       │            │         │                              │
│  ┌────▼────────────▼─────────▼──────────┐                  │
│  │       Volumes Persistentes            │                  │
│  │  - app-data (PDFs, outputs)           │                  │
│  │  - text-extractor-cache (modelos)     │                  │
│  │  - stj-duckdb-data (banco)            │                  │
│  │  - redis-data (jobs)                  │                  │
│  └───────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
         │                      │
    ┌────▼────┐            ┌────▼────┐
    │ Gemini  │            │ Trello  │
    │   API   │            │   API   │
    └─────────┘            └─────────┘
```

---

## Services

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| **streamlit-hub** | 8501 | Interface web principal (Streamlit) | `curl http://localhost:8501/healthz` |
| **text-extractor** | 8001<br/>5555 | Extração OCR (Marker + Gemini)<br/>Flower (monitor Celery) | `curl http://localhost:8001/health` |
| **doc-assembler** | 8002 | Montagem de documentos DOCX | `curl http://localhost:8002/health` |
| **stj-api** | 8003 | Consulta de jurisprudência STJ | `curl http://localhost:8003/health` |
| **trello-mcp** | 8004 | Integração com Trello via MCP | `curl http://localhost:8004/health` |
| **redis** | 6379 | Fila de jobs (Celery backend) | `docker exec lw-redis redis-cli ping` |

### Recursos Alocados

| Service | Memory Limit | CPU Limit | Memory Reserve | CPU Reserve |
|---------|--------------|-----------|----------------|-------------|
| text-extractor | 10GB | 4 cores | 6GB | 2 cores |
| stj-api | 2GB | 2 cores | - | - |
| doc-assembler | 1GB | 1 core | - | - |
| trello-mcp | 512MB | 1 core | - | - |
| streamlit-hub | - | - | - | - |
| redis | - | - | - | - |

**Total estimado:** ~14GB RAM (ideal para WSL2 com 16GB)

---

## Prerequisites

### Requisitos Mínimos

- **Docker:** 24.0+ com BuildKit habilitado
- **Docker Compose:** 2.20+
- **RAM:** 14GB disponível (16GB total recomendado)
- **Disco:** 20GB livres (modelos Marker + cache)
- **CPU:** 4 cores (i5 12ª geração ou superior)

### Instalação Docker (WSL2 Ubuntu)

Se o Docker não estiver instalado no WSL2:

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar Docker e Docker Compose
sudo apt install -y docker.io docker-compose-v2

# Adicionar usuário ao grupo docker (evita usar sudo)
sudo usermod -aG docker $USER

# Reiniciar WSL (executar no PowerShell do Windows)
wsl --shutdown

# Após reabrir o terminal WSL, verificar instalação
docker --version        # Deve mostrar 24.0+
docker compose version  # Deve mostrar 2.20+
```

> **Nota:** Após `usermod`, é necessário reiniciar o WSL para o grupo ter efeito.

### Configuração WSL2 (Windows)

Criar/editar arquivo `%UserProfile%\.wslconfig`:

```ini
[wsl2]
memory=14GB
processors=3
swap=8GB

[experimental]
autoMemoryReclaim=gradual
networkingMode=mirrored
sparseVhd=true
```

Após editar, reiniciar o WSL:

```bash
wsl --shutdown
```

**Justificativa:**
- `memory=14GB`: Reserva 2GB para o Windows dos 16GB totais
- `processors=3`: Suficiente para builds e runtime simultâneos
- `swap=8GB`: Cobre picos de memória do Marker durante OCR

### Troubleshooting: Correções Aplicadas (2025-12-11)

Durante a primeira execução, as seguintes correções foram necessárias:

#### 1. Atributo `version` obsoleto no docker-compose.yml
```yaml
# Antes (warning):
version: "3.8"

# Depois (corrigido):
# version removed (obsolete in Compose V2)
```

#### 2. Contexto de build inconsistente
Os Dockerfiles usam paths diferentes. O `docker-compose.yml` foi ajustado para:
- Serviços com código autocontido: `context: ./services/<service>/`
- Serviço `stj-api` (precisa de `ferramentas/`): `context: ..`

#### 3. Conflito de dependências no text-extractor
```txt
# requirements.txt - Correções:
redis>=4.5.2,<5.0.0  # celery[redis] 5.3.4 requer redis<5.0.0
pydantic>=2.7.1,<3.0.0  # marker-pdf requer pydantic>=2.7.1
```

#### 4. Limites de CPU para máquinas com poucos cores
Se você tem apenas 2 CPUs disponíveis, o `text-extractor` falhará. Ajuste no `docker-compose.yml`:
```yaml
# Para máquinas com 2 CPUs:
deploy:
  resources:
    limits:
      memory: 8G
      cpus: '2'
    reservations:
      memory: 4G
      cpus: '1'
```

---

## Environment Variables

### Variáveis Obrigatórias

Copie `.env.example` para `.env` e configure:

| Variável | Descrição | Como Obter | Exemplo |
|----------|-----------|------------|---------|
| `GEMINI_API_KEY` | Google Gemini API para classificação de texto | [Google AI Studio](https://aistudio.google.com/app/apikey) | `AIza...` |
| `TRELLO_API_KEY` | Trello API Key para integração | [Trello Power-Ups](https://trello.com/power-ups/admin) | `a1b2c3...` |
| `TRELLO_API_TOKEN` | Token de autenticação Trello | Mesmo link acima | `ATTA...` |

### Variáveis Opcionais

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `MAX_CONCURRENT_JOBS` | `2` | Jobs simultâneos no text-extractor (reduzir se OOM) |
| `JOB_TIMEOUT_SECONDS` | `600` | Timeout para processamento de PDFs |
| `CACHE_TTL_HOURS` | `24` | TTL do cache do STJ API |
| `SYNC_INTERVAL_HOURS` | `6` | Intervalo de sincronização STJ |
| `RATE_LIMIT_PER_MINUTE` | `100` | Rate limit da API Trello |
| `LOG_LEVEL` | `INFO` | Nível de log (DEBUG, INFO, WARNING, ERROR) |

---

## Usage

### Development

Subir com logs em tempo real:

```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/docker
docker-compose up
```

Rodar em background:

```bash
docker-compose up -d
```

Acompanhar logs de um serviço:

```bash
docker-compose logs -f text-extractor
```

Hot-reload (desenvolvimento):

```bash
# O docker-compose.yml já monta ../legal-workbench:ro no hub
# Alterações no código Python são refletidas após restart
docker-compose restart streamlit-hub
```

### Production

Build sem cache:

```bash
docker-compose build --no-cache
```

Deploy completo:

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
docker-compose ps
```

Verificar health de todos os serviços:

```bash
docker-compose ps | grep "healthy"
```

### Individual Services

Rodar apenas um serviço (com dependências):

```bash
# Apenas text-extractor + redis
docker-compose up -d text-extractor

# Apenas STJ API
docker-compose up -d stj-api

# Rebuild específico
docker-compose build --no-cache doc-assembler
docker-compose up -d --no-deps doc-assembler
```

---

## Scripts

### Scripts Úteis (criar em `./scripts/`)

#### 1. `deploy.sh` - Deploy Completo

```bash
#!/bin/bash
# Full deployment script
set -e

echo "=== Legal Workbench Deploy ==="

# Check .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example and configure."
    exit 1
fi

# Build images
echo "Building images..."
docker-compose build --no-cache

# Stop existing containers
echo "Stopping containers..."
docker-compose down

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for health checks
echo "Waiting for services to become healthy..."
sleep 60

# Verify health
echo "Checking service health..."
docker-compose ps

echo "=== Deploy Complete ==="
echo "Access: http://localhost:8501"
```

#### 2. `health-check.sh` - Verificação de Saúde

```bash
#!/bin/bash
# Health check all services

SERVICES=("text-extractor:8001" "doc-assembler:8002" "stj-api:8003" "trello-mcp:8004" "streamlit-hub:8501")

echo "=== Health Check ==="

for service in "${SERVICES[@]}"; do
    name="${service%%:*}"
    port="${service##*:}"

    if [ "$name" == "streamlit-hub" ]; then
        endpoint="/healthz"
    else
        endpoint="/health"
    fi

    echo -n "Checking $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port$endpoint")

    if [ "$response" == "200" ]; then
        echo "✓ Healthy"
    else
        echo "✗ Failed (HTTP $response)"
    fi
done

# Check Redis
echo -n "Checking redis... "
if docker exec lw-redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Failed"
fi
```

#### 3. `backup.sh` - Backup de Volumes

```bash
#!/bin/bash
# Backup Docker volumes

BACKUP_DIR="${HOME}/backups/legal-workbench"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "=== Backup Volumes ==="

# Backup app-data
echo "Backing up app-data..."
docker run --rm -v app-data:/source -v "$BACKUP_DIR":/backup alpine \
    tar czf "/backup/app-data_${DATE}.tar.gz" -C /source .

# Backup stj-duckdb-data
echo "Backing up stj-duckdb-data..."
docker run --rm -v stj-duckdb-data:/source -v "$BACKUP_DIR":/backup alpine \
    tar czf "/backup/stj-duckdb_${DATE}.tar.gz" -C /source .

# Backup text-extractor-cache (opcional, pode regenerar)
echo "Backing up text-extractor-cache..."
docker run --rm -v text-extractor-cache:/source -v "$BACKUP_DIR":/backup alpine \
    tar czf "/backup/extractor-cache_${DATE}.tar.gz" -C /source .

echo "=== Backup Complete ==="
ls -lh "$BACKUP_DIR"
```

#### 4. `rollback.sh` - Rollback de Versão

```bash
#!/bin/bash
# Rollback to previous version

set -e

BACKUP_TAG="${1:-latest}"

echo "=== Rollback to $BACKUP_TAG ==="

# Tag current images as backup
echo "Tagging current images..."
docker-compose images -q | while read image_id; do
    docker tag "$image_id" "${image_id}:backup-$(date +%Y%m%d)"
done

# Pull previous version
echo "Pulling $BACKUP_TAG images..."
docker-compose pull

# Restart services
echo "Restarting services..."
docker-compose up -d

echo "=== Rollback Complete ==="
```

#### 5. `logs.sh` - Visualizar Logs

```bash
#!/bin/bash
# View service logs with filtering

SERVICE="${1:-all}"
LINES="${2:-100}"

if [ "$SERVICE" == "all" ]; then
    docker-compose logs -f --tail="$LINES"
else
    docker-compose logs -f --tail="$LINES" "$SERVICE"
fi
```

**Uso:**

```bash
# Todos os logs
./scripts/logs.sh

# Apenas text-extractor, últimas 50 linhas
./scripts/logs.sh text-extractor 50
```

---

## Troubleshooting

### Problema: OOM (Out of Memory)

**Sintomas:**
- Container `text-extractor` reiniciando constantemente
- Erro `Killed` nos logs
- `docker stats` mostra uso de memória > 90%

**Solução:**

```bash
# 1. Verificar uso de memória
docker stats

# 2. Reduzir jobs concorrentes
# Editar .env:
MAX_CONCURRENT_JOBS=1

# 3. Aumentar swap no .wslconfig
swap=16GB

# 4. Restart WSL
wsl --shutdown

# 5. Restart containers
docker-compose restart text-extractor
```

### Problema: Serviço não inicia (unhealthy)

**Sintomas:**
- `docker-compose ps` mostra status `unhealthy`
- Health check falha continuamente

**Solução:**

```bash
# 1. Ver logs detalhados
docker-compose logs text-extractor

# 2. Verificar variáveis de ambiente
docker exec lw-text-extractor env | grep GEMINI

# 3. Testar health check manualmente
docker exec lw-text-extractor curl -f http://localhost:8001/health

# 4. Verificar arquivo .env
cat .env | grep -v "^#"

# 5. Rebuild completo
docker-compose down
docker-compose build --no-cache text-extractor
docker-compose up -d
```

### Problema: Marker models não carregam

**Sintomas:**
- `text-extractor` demora muito para iniciar (> 5 minutos)
- Erro `marker models not found` nos logs

**Solução:**

```bash
# 1. Verificar volume de cache
docker volume inspect text-extractor-cache

# 2. Limpar cache e recriar
docker-compose down
docker volume rm text-extractor-cache
docker-compose up -d text-extractor

# 3. Acompanhar download dos modelos (primeira vez ~8GB)
docker-compose logs -f text-extractor
```

### Problema: Redis connection refused

**Sintomas:**
- Celery não conecta ao Redis
- Erro `ConnectionRefusedError: [Errno 111] Connection refused`

**Solução:**

```bash
# 1. Verificar se Redis está rodando
docker-compose ps redis

# 2. Testar conexão
docker exec lw-redis redis-cli ping

# 3. Restart Redis
docker-compose restart redis

# 4. Verificar rede
docker network inspect legal-workbench-net
```

### Problema: Porta já em uso

**Sintomas:**
- Erro `bind: address already in use`

**Solução:**

```bash
# 1. Identificar processo usando a porta
sudo lsof -i :8501

# 2. Matar processo
sudo kill -9 <PID>

# Ou mudar porta no docker-compose.yml:
ports:
  - "8502:8501"  # Host:Container
```

### Problema: Permission denied em volumes

**Sintomas:**
- Erro `Permission denied` ao escrever em `/app/data`

**Solução:**

```bash
# 1. Verificar permissões do volume
docker volume inspect app-data

# 2. Ajustar permissões
docker run --rm -v app-data:/data alpine chown -R 1000:1000 /data

# 3. Restart serviço
docker-compose restart streamlit-hub
```

### Problema: Build falha no text-extractor

**Sintomas:**
- Timeout durante `apt-get install tesseract-ocr`
- Erro de compilação do Marker

**Solução:**

```bash
# 1. Build com logs detalhados
DOCKER_BUILDKIT=1 docker-compose build --progress=plain text-extractor

# 2. Build com mais memória
docker-compose build --memory=8g text-extractor

# 3. Limpar cache de build
docker builder prune -af
docker-compose build --no-cache text-extractor
```

### Comandos de Diagnóstico Rápido

```bash
# Status geral
docker-compose ps

# Uso de recursos
docker stats --no-stream

# Logs de erro
docker-compose logs --tail=50 | grep -i error

# Inspecionar container
docker inspect lw-text-extractor

# Acessar shell do container
docker exec -it lw-text-extractor /bin/bash

# Verificar conectividade entre containers
docker exec lw-hub ping text-extractor

# Listar volumes
docker volume ls | grep legal

# Espaço em disco
docker system df
```

---

## Performance Tuning

### Otimização de Memória

#### 1. Reduzir uso do text-extractor

```yaml
# docker-compose.yml
text-extractor:
  environment:
    - MAX_CONCURRENT_JOBS=1  # Reduzir de 2 para 1
    - MALLOC_TRIM_THRESHOLD_=65536  # Já configurado
  deploy:
    resources:
      limits:
        memory: 8G  # Reduzir de 10G
```

#### 2. Habilitar memory reclaim no WSL

```ini
# .wslconfig
[experimental]
autoMemoryReclaim=gradual  # Libera memória não usada
```

#### 3. Limpar cache periodicamente

```bash
# Limpar volumes não usados
docker volume prune -f

# Limpar cache de build
docker builder prune -af

# Limpar imagens antigas
docker image prune -a
```

### Otimização de CPU

#### 1. Ajustar CPU shares

```yaml
# docker-compose.yml
text-extractor:
  deploy:
    resources:
      limits:
        cpus: '3'  # Reduzir de 4
```

#### 2. Priorizar serviços críticos

```yaml
text-extractor:
  cpu_shares: 1024  # Alta prioridade

stj-api:
  cpu_shares: 512   # Média prioridade
```

### Otimização de Disco

#### 1. Usar overlay2 storage driver (padrão, verificar)

```bash
docker info | grep "Storage Driver"
```

#### 2. Limpar logs periodicamente

```yaml
# docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"  # Mantém apenas 3 arquivos de log
```

#### 3. Comprimir volumes de backup

```bash
# Usar compressão agressiva
tar czf backup.tar.gz --use-compress-program="gzip -9" /data
```

### Otimização de Rede

#### 1. Usar cache DNS

```yaml
# docker-compose.yml
networks:
  legal-workbench-net:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: lw-br0
      com.docker.network.driver.mtu: 1500
```

#### 2. Desabilitar IPv6 se não usado

```yaml
networks:
  legal-workbench-net:
    enable_ipv6: false
```

### Otimização de Build

#### 1. Usar BuildKit cache

```bash
# .env
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1
```

#### 2. Cache de dependências pip

```dockerfile
# Dockerfile (já implementado)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

#### 3. Multi-stage builds (já implementado)

Todos os Dockerfiles usam multi-stage builds para reduzir tamanho final.

### Monitoramento de Performance

```bash
# CPU e memória em tempo real
docker stats

# Top 5 containers por memória
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}" | sort -k2 -h | tail -5

# Disco usado por volumes
docker system df -v

# Rede: pacotes perdidos
docker exec lw-hub ping -c 10 text-extractor
```

### Benchmarks Esperados

| Operação | Tempo Esperado | Bottleneck |
|----------|----------------|------------|
| Extração PDF (50 páginas) | 30-60s | CPU (Marker OCR) |
| Classificação Gemini | 5-10s | Rede (API externa) |
| Query STJ (1000 resultados) | < 1s | I/O (DuckDB) |
| Montagem DOCX | < 2s | CPU (Jinja2) |
| Startup completo (cold) | 2-3 min | I/O (download modelos) |
| Startup (warm, cache) | 30-60s | CPU (health checks) |

---

## API Documentation

Todos os serviços backend expõem documentação interativa via FastAPI:

| Service | Swagger UI | ReDoc |
|---------|-----------|--------|
| text-extractor | http://localhost:8001/docs | http://localhost:8001/redoc |
| doc-assembler | http://localhost:8002/docs | http://localhost:8002/redoc |
| stj-api | http://localhost:8003/docs | http://localhost:8003/redoc |
| trello-mcp | http://localhost:8004/docs | http://localhost:8004/redoc |

### Exemplo: Extração de Texto

```bash
# Upload PDF e extrair texto
curl -X POST "http://localhost:8001/extract" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@documento.pdf" \
  -F "classify=true"
```

### Exemplo: Montagem de Documento

```bash
# Montar documento a partir de template
curl -X POST "http://localhost:8002/assemble" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "peticao_inicial.docx",
    "context": {
      "autor": "João Silva",
      "reu": "Empresa XYZ"
    }
  }'
```

---

## Maintenance

### Backup Automático (Cron)

```bash
# Adicionar ao crontab
crontab -e

# Backup diário às 3AM
0 3 * * * /home/user/Claude-Code-Projetos/legal-workbench/docker/scripts/backup.sh

# Limpeza semanal de volumes não usados
0 4 * * 0 docker volume prune -f
```

### Atualização de Imagens

```bash
# Atualizar imagem base
docker pull python:3.11-slim

# Rebuild todos os serviços
docker-compose build --no-cache

# Atualização sem downtime (rolling update)
for service in text-extractor doc-assembler stj-api trello-mcp; do
    docker-compose build --no-cache $service
    docker-compose up -d --no-deps $service
    sleep 30  # Aguardar health check
done
```

### Limpeza de Recursos

```bash
# Remover containers parados
docker container prune -f

# Remover imagens não usadas
docker image prune -a -f

# Remover volumes não usados (CUIDADO: apaga dados!)
docker volume prune -f

# Limpeza completa (CUIDADO!)
docker system prune -a --volumes -f
```

### Logs e Auditoria

```bash
# Exportar logs para análise
docker-compose logs --no-color > logs-$(date +%Y%m%d).txt

# Logs de um período específico
docker-compose logs --since="2024-01-01" --until="2024-01-31"

# Filtrar por nível de log
docker-compose logs | grep -i error

# Estatísticas de uso
docker stats --no-stream > stats-$(date +%Y%m%d).txt
```

---

## Security

### Secrets Management

Nunca commitar `.env` ao Git. Use Docker secrets em produção:

```yaml
# docker-compose.prod.yml
secrets:
  gemini_api_key:
    file: ./secrets/gemini_api_key.txt
  trello_api_key:
    file: ./secrets/trello_api_key.txt

services:
  text-extractor:
    secrets:
      - gemini_api_key
    environment:
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key
```

### Network Isolation

```yaml
# Expor apenas o frontend
ports:
  - "8501:8501"  # Apenas hub público

# Backend services sem exposição externa
# (acessados apenas via rede interna)
```

### Scan de Vulnerabilidades

```bash
# Scan de imagens
docker scan lw-text-extractor:latest

# Atualizar dependências
pip-audit -r requirements.txt
```

---

## References

- **Documentação Técnica:** `/home/user/Claude-Code-Projetos/docs/docker/DOCKER_ARCHITECTURE.md`
- **Diagramas de Fluxo:** `/home/user/Claude-Code-Projetos/docs/docker/WORKFLOW_DIAGRAM.md`
- **Regras de Desenvolvimento:** `/home/user/Claude-Code-Projetos/legal-workbench/CLAUDE.md`
- **Docker Compose Spec:** https://docs.docker.com/compose/compose-file/
- **Docker Best Practices:** https://docs.docker.com/develop/dev-best-practices/

---

**Última atualização:** 2025-12-11
**Versão:** 1.0.0
**Autor:** Pedro Giudice (PGR)

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
