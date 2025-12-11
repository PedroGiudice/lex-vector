# STJ API - Quick Start Guide

Guia rápido para subir a API STJ Dados Abertos.

## Método 1: Docker Compose (Mais Simples)

```bash
# 1. Navegar até o diretório da API
cd /home/user/Claude-Code-Projetos/legal-workbench/docker/services/stj-api

# 2. Subir o container
docker-compose up --build

# 3. Testar a API
./test_api.sh
```

A API estará disponível em: http://localhost:8000
Documentação Swagger: http://localhost:8000/docs

## Método 2: Build Manual do Docker

```bash
# 1. Na raiz do legal-workbench
cd /home/user/Claude-Code-Projetos/legal-workbench

# 2. Build da imagem
docker build -f docker/services/stj-api/Dockerfile -t stj-api .

# 3. Executar container
docker run -d \
  -p 8000:8000 \
  -v stj-api-data:/app/data \
  --name stj-api \
  stj-api

# 4. Ver logs
docker logs -f stj-api

# 5. Testar
cd docker/services/stj-api
./test_api.sh
```

## Método 3: Execução Local (Desenvolvimento)

```bash
# 1. Ativar venv do legal-workbench
cd /home/user/Claude-Code-Projetos/legal-workbench
source .venv/bin/activate

# 2. Instalar dependências da API
cd docker/services/stj-api
pip install -r requirements.txt

# 3. Executar API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Testes Rápidos

### Health Check
```bash
curl http://localhost:8000/health
```

### Estatísticas
```bash
curl http://localhost:8000/api/v1/stats
```

### Busca Simples
```bash
curl "http://localhost:8000/api/v1/search?termo=responsabilidade&limit=5"
```

## Documentação Interativa

Acesse: http://localhost:8000/docs

A documentação Swagger permite testar todos os endpoints diretamente pelo browser.

## Troubleshooting

### Container não inicia
```bash
# Ver logs detalhados
docker logs stj-api

# Verificar se a porta 8000 está livre
lsof -i :8000

# Parar container antigo
docker stop stj-api && docker rm stj-api
```

### Banco de dados vazio
A API precisa de dados no banco DuckDB. Para popular:

```bash
# Navegar até o backend
cd /home/user/Claude-Code-Projetos/legal-workbench/ferramentas/stj-dados-abertos

# Ativar venv
source .venv/bin/activate

# Executar CLI para download inicial
python cli.py download --orgao corte_especial --dias 30
python cli.py process
```

Ou use o endpoint de sincronização da API:
```bash
curl -X POST http://localhost:8000/api/v1/sync \
  -H "Content-Type: application/json" \
  -d '{"orgaos": ["corte_especial"], "dias": 30}'
```

## Estrutura de Arquivos

```
stj-api/
├── api/
│   ├── __init__.py         # Versão
│   ├── main.py             # FastAPI app
│   ├── models.py           # Modelos Pydantic
│   ├── dependencies.py     # DI (database, cache)
│   └── scheduler.py        # Background jobs
├── Dockerfile              # Container
├── docker-compose.yml      # Compose config
├── requirements.txt        # Dependências
├── README.md               # Documentação completa
├── QUICKSTART.md           # Este arquivo
└── test_api.sh             # Script de testes
```

## Próximos Passos

1. Popular banco de dados (ver seção Troubleshooting)
2. Testar endpoints com `./test_api.sh`
3. Explorar documentação Swagger em /docs
4. Configurar sincronização automática (já ativa por padrão, roda diariamente às 3 AM)

## Configuração Avançada

### Variáveis de Ambiente (docker-compose.yml)

```yaml
environment:
  - LOG_LEVEL=DEBUG           # DEBUG, INFO, WARNING, ERROR
  - DUCKDB_MEMORY_LIMIT=8GB   # Limite de RAM do DuckDB
  - DUCKDB_THREADS=8          # Threads para queries
```

### Volume de Dados

Os dados são persistidos em um volume Docker:
```bash
# Ver informações do volume
docker volume inspect stj-api-data

# Backup do volume
docker run --rm -v stj-api-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/stj-data-backup.tar.gz /data
```

## Suporte

- Logs: `docker logs stj-api`
- Health: `curl http://localhost:8000/health`
- Docs: http://localhost:8000/docs
- Backend: `/home/user/Claude-Code-Projetos/legal-workbench/ferramentas/stj-dados-abertos`
