# STJ Dados Abertos API

FastAPI REST API para consulta de jurisprudência do Superior Tribunal de Justiça (STJ).

## Visão Geral

API RESTful que expõe funcionalidades de busca e consulta do banco de dados DuckDB contendo acórdãos do STJ. Inclui busca full-text, filtros por órgão julgador, estatísticas e sincronização automática com a base de dados abertos do STJ.

## Endpoints

### Health Check
```
GET /health
```
Verifica o status da API e conectividade com o banco de dados.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2024-12-11T10:00:00"
}
```

### Buscar Jurisprudência
```
GET /api/v1/search
```
Busca acórdãos por termo na ementa ou texto integral.

**Query Parameters:**
- `termo` (required): Termo para buscar (mínimo 3 caracteres)
- `orgao` (optional): Órgão julgador para filtrar
- `dias` (optional): Buscar nos últimos N dias (padrão: 365, max: 3650)
- `limit` (optional): Máximo de resultados (padrão: 100, max: 1000)
- `offset` (optional): Offset para paginação (padrão: 0)
- `campo` (optional): Campo para buscar - "ementa" ou "texto_integral" (padrão: "ementa")

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/search?termo=responsabilidade&orgao=Terceira%20Turma&dias=90&limit=10"
```

**Response:**
```json
{
  "total": 42,
  "limit": 10,
  "offset": 0,
  "resultados": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "numero_processo": "REsp 1234567/SP",
      "orgao_julgador": "Terceira Turma",
      "tipo_decisao": "Acórdão",
      "relator": "Ministro João Silva",
      "data_publicacao": "2024-12-01T00:00:00",
      "data_julgamento": "2024-11-28T00:00:00",
      "ementa": "RESPONSABILIDADE CIVIL. ...",
      "resultado_julgamento": "provimento"
    }
  ]
}
```

### Obter Detalhes de Caso
```
GET /api/v1/case/{case_id}
```
Retorna todos os detalhes de um acórdão específico, incluindo texto integral.

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/case/550e8400-e29b-41d4-a716-446655440000"
```

### Estatísticas
```
GET /api/v1/stats
```
Retorna estatísticas do banco de dados.

**Response:**
```json
{
  "total_acordaos": 150000,
  "por_orgao": {
    "Terceira Turma": 25000,
    "Quarta Turma": 24000,
    "Primeira Turma": 23000
  },
  "por_tipo": {
    "Acórdão": 120000,
    "Decisão Monocrática": 30000
  },
  "periodo": {
    "mais_antigo": "2022-05-01T00:00:00",
    "mais_recente": "2024-12-11T00:00:00"
  },
  "tamanho_db_mb": 5120.5,
  "ultimos_30_dias": 3500
}
```

### Sincronização
```
POST /api/v1/sync
```
Inicia sincronização com STJ Dados Abertos (executa em background).

**Request Body:**
```json
{
  "orgaos": ["corte_especial", "primeira_turma"],
  "dias": 30,
  "force": false
}
```

**Parâmetros:**
- `orgaos` (optional): Lista de órgãos para sincronizar (null = todos)
- `dias` (optional): Sincronizar últimos N dias (padrão: 30, max: 365)
- `force` (optional): Forçar redownload de arquivos existentes (padrão: false)

### Status de Sincronização
```
GET /api/v1/sync/status
```
Retorna o status da sincronização atual ou última executada.

## Instalação e Execução

### Com Docker Compose (Recomendado)

```bash
# Na raiz do legal-workbench
cd docker/services/stj-api
docker-compose up --build
```

A API estará disponível em: `http://localhost:8000`

Documentação interativa (Swagger): `http://localhost:8000/docs`

### Build Manual do Docker

```bash
# Na raiz do legal-workbench
docker build -f docker/services/stj-api/Dockerfile -t stj-api .

# Executar container
docker run -d \
  -p 8000:8000 \
  -v stj-data:/app/data \
  --name stj-api \
  stj-api
```

### Execução Local (Desenvolvimento)

```bash
# Instalar dependências
cd docker/services/stj-api
pip install -r requirements.txt

# Executar API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Nota:** Para execução local, certifique-se de que o backend do STJ está acessível e configurado corretamente.

## Configuração

### Variáveis de Ambiente

- `LOG_LEVEL`: Nível de logging (default: "INFO")
- `DUCKDB_MEMORY_LIMIT`: Limite de memória do DuckDB (default: "4GB")
- `DUCKDB_THREADS`: Número de threads do DuckDB (default: 4)

### Volumes Docker

- `/app/data`: Diretório de dados persistentes (banco DuckDB, logs, cache)

## Arquitetura

```
stj-api/
├── api/
│   ├── __init__.py           # Versão da API
│   ├── main.py               # FastAPI app e endpoints
│   ├── models.py             # Modelos Pydantic (request/response)
│   ├── dependencies.py       # Dependency injection (DB, cache)
│   └── scheduler.py          # Background scheduler (APScheduler)
├── Dockerfile                # Container definition
├── docker-compose.yml        # Docker Compose config
├── requirements.txt          # Python dependencies
└── README.md                 # Esta documentação
```

## Funcionalidades

- ✅ Busca full-text em ementas e texto integral (DuckDB FTS)
- ✅ Filtros por órgão julgador e período
- ✅ Paginação de resultados
- ✅ Cache in-memory com TTL (5 minutos)
- ✅ Sincronização automática diária (3 AM)
- ✅ Sincronização manual via endpoint
- ✅ Health check para monitoramento
- ✅ Documentação interativa (Swagger/ReDoc)
- ✅ Container Docker otimizado (multi-stage build)
- ✅ Stopwords jurídicas customizadas
- ✅ Stemming em português (DuckDB FTS)

## Performance

- **Cache**: Queries frequentes são cacheadas por 5 minutos
- **FTS Index**: Busca full-text otimizada com stemmer português
- **Paginação**: Resultados paginados para evitar sobrecarga
- **Background Jobs**: Sincronização roda em background sem bloquear API

## Desenvolvimento

### Estrutura de Código

A API reutiliza módulos do backend existente:
- `src/database.py`: Gerenciamento do banco DuckDB
- `src/processor.py`: Processamento e classificação de acórdãos
- `src/downloader.py`: Download de JSONs do STJ

### Adicionando Novos Endpoints

1. Adicionar modelo Pydantic em `api/models.py`
2. Implementar endpoint em `api/main.py`
3. Atualizar documentação neste README

### Testes

```bash
# Executar testes (TODO: implementar suite de testes)
pytest tests/
```

## Órgãos Julgadores Disponíveis

- `corte_especial`: Corte Especial
- `primeira_secao`: Primeira Seção
- `segunda_secao`: Segunda Seção
- `terceira_secao`: Terceira Seção
- `primeira_turma`: Primeira Turma
- `segunda_turma`: Segunda Turma
- `terceira_turma`: Terceira Turma
- `quarta_turma`: Quarta Turma
- `quinta_turma`: Quinta Turma
- `sexta_turma`: Sexta Turma

## Roadmap

- [ ] Implementar autenticação (API keys)
- [ ] Rate limiting
- [ ] Metrics e observabilidade (Prometheus)
- [ ] Testes automatizados (pytest)
- [ ] CI/CD pipeline
- [ ] Busca avançada (booleanos, proximidade)
- [ ] Export de resultados (CSV, PDF)

## Suporte

Para problemas ou dúvidas:
1. Verificar logs: `docker logs stj-api`
2. Verificar health check: `curl http://localhost:8000/health`
3. Documentação interativa: http://localhost:8000/docs

## Licença

Projeto interno Legal Workbench
