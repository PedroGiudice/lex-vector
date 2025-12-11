# Legal Workbench - Docker Setup

## Quick Start

```bash
# 1. Copiar environment variables
cp .env.example .env
# Editar .env com suas API keys

# 2. Build e start
docker-compose up -d

# 3. Verificar status
docker-compose ps
```

## Acessos

| Service | URL | Descrição |
|---------|-----|-----------|
| Hub | http://localhost:8501 | Interface Streamlit |
| Text Extractor | http://localhost:8001/docs | API Docs |
| Doc Assembler | http://localhost:8002/docs | API Docs |
| STJ API | http://localhost:8003/docs | API Docs |
| Trello MCP | http://localhost:8004/docs | API Docs |
| Celery Flower | http://localhost:5555 | Job Monitor |

## Requisitos WSL2

Arquivo `%UserProfile%\.wslconfig`:

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

Após editar: `wsl --shutdown`

## Comandos Úteis

```bash
# Logs de um serviço
docker-compose logs -f text-extractor

# Rebuild específico
docker-compose build --no-cache doc-assembler

# Restart serviço
docker-compose restart stj-api

# Parar tudo
docker-compose down

# Limpar volumes (CUIDADO: apaga dados!)
docker-compose down -v
```

## Troubleshooting

**OOM (Out of Memory):**
- Verificar: `docker stats`
- Aumentar swap no .wslconfig
- Reduzir MAX_CONCURRENT_JOBS=1

**Serviço não inicia:**
- `docker-compose logs <service>`
- Verificar .env está configurado
