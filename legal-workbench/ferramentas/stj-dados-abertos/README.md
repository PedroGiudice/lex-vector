# STJ Dados Abertos

Sistema de coleta, processamento e analise de decisoes do Superior Tribunal de Justica via API de Dados Abertos CKAN.

## Datasets

### 1. Espelhos de Acordaos
- 10 datasets CKAN, um por orgao julgador
- JSONs diarios com resumos (~548 chars de texto)
- Campos: ementa, relator, orgao, data publicacao, etc.

### 2. Integras de Decisoes (novo)
- 1 dataset CKAN unico com ~1.760 resources
- ZIPs com textos completos em HTML (~15 KB media)
- JSONs de metadados com campos de classificacao
- Periodo: fev/2022 ate hoje (atualizado diariamente)
- Tipos: DECISAO (~80%) + ACORDAO (~20%)
- Correlacao via numero_processo com espelhos

## Estrutura

```
stj-dados-abertos/
├── cli.py                        # CLI principal (typer)
├── config.py                     # Configuracoes centralizadas
├── requirements.txt
└── src/
    ├── ckan_client.py            # CKAN API client (espelhos + integras)
    ├── downloader.py             # Download de espelhos (JSONs)
    ├── integras_downloader.py    # Download de integras (ZIPs + JSONs)
    ├── integras_processor.py     # HTML->texto + normalizacao
    ├── processor.py              # Processamento de espelhos
    └── database.py               # DuckDB (acordaos + integras)
```

## Setup

```bash
cd legal-workbench/ferramentas/stj-dados-abertos
source .venv/bin/activate
pip install -r requirements.txt

# Configurar armazenamento (producao)
export DATA_PATH=/mnt/juridico-data/stj
export DB_PATH=/mnt/juridico-data/stj/database/stj.duckdb

# Inicializar
python cli.py stj-init
```

## Comandos CLI

### Espelhos

```bash
# Download por periodo
python cli.py stj-download-periodo 2024-01-01 2024-12-31 --orgao terceira_turma

# Download por orgao (ultimos N meses)
python cli.py stj-download-orgao corte_especial --meses 6

# Download rapido (ultimo mes, todos os orgaos)
python cli.py stj-download-mvp

# Processar e inserir no banco
python cli.py stj-processar-staging

# Buscar
python cli.py stj-buscar-ementa "responsabilidade civil" --dias 90
python cli.py stj-buscar-acordao "dano moral" --dias 30
```

### Integras

```bash
# Download retroativo (desde fev/2022, com retomada automatica)
python cli.py stj-download-integras

# Download de periodo especifico
python cli.py stj-download-integras --inicio 2026-01-01 --fim 2026-01-31

# Processar e inserir no banco
python cli.py stj-processar-integras

# Processar data especifica
python cli.py stj-processar-integras --data 20260122

# Busca full-text
python cli.py stj-buscar-integra "habeas corpus" --tipo DECISAO --dias 365

# Busca unificada por processo (espelhos + integras)
python cli.py stj-buscar-processo 2591846

# Estatisticas
python cli.py stj-estatisticas-integras
```

### Utilidades

```bash
python cli.py stj-info           # Informacoes do sistema
python cli.py stj-estatisticas   # Estatisticas de espelhos
python cli.py stj-exportar "SELECT * FROM acordaos LIMIT 100" --output export.csv
```

## Schema

### Tabela `acordaos` (espelhos)

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | VARCHAR PK | UUID |
| numero_processo | VARCHAR | Numero do processo |
| hash_conteudo | VARCHAR UNIQUE | SHA256 para dedup |
| orgao_julgador | VARCHAR | Turma/secao |
| ementa | TEXT | Resumo oficial |
| texto_integral | TEXT | Inteiro teor |
| relator | VARCHAR | Ministro relator |
| resultado_julgamento | VARCHAR | Provimento/desprovimento |
| data_publicacao | TIMESTAMP | Data de publicacao |

### Tabela `integras`

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| seq_documento | BIGINT PK | ID STJ (chave natural) |
| numero_processo | VARCHAR | Numero do processo |
| classe_processual | VARCHAR | AREsp, REsp, HC, etc. |
| hash_conteudo | VARCHAR UNIQUE | SHA256 para dedup |
| tipo_documento | VARCHAR | DECISAO ou ACORDAO |
| ministro | VARCHAR | Ministro relator |
| teor | VARCHAR | Desfecho (Concedendo, etc.) |
| texto_completo | TEXT | Texto limpo (HTML convertido) |
| data_publicacao | DATE | Data de publicacao |

### Normalizacao de campos

Consolidados mensais e diarios usam formatos diferentes:

| Campo | Consolidados | Diarios |
|-------|-------------|---------|
| SeqDocumento | `seqDocumento` (minusculo) | `SeqDocumento` (maiusculo) |
| Ministro | `ministro` | `NM_MINISTRO` |
| Datas | epoch ms (1646276400000) | ISO string (2026-01-22) |
| Assuntos | separador `;` | separador `,` |

O `integras_processor.py` normaliza automaticamente ambos os formatos.

## Correlacao

A busca unificada (`stj-buscar-processo`) cruza espelhos e integras via `numero_processo`:

```
Processo 2591846:
  Espelhos: 1 (resumo, ementa, orgao julgador)
  Integras: 1 (texto completo, ministro, teor)
```

## Testes

```bash
source .venv/bin/activate
pytest tests/ -v         # 207 testes
```

## Stack

Python 3.12, DuckDB, httpx, typer, rich, tenacity

## Armazenamento

Volume de Bloco OCI montado em `/mnt/juridico-data` (200 GB).
