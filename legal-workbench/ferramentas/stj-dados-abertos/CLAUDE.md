# CLAUDE.md - STJ Dados Abertos

Pipeline de dados do STJ: espelhos de acordaos + integras de decisoes.

---

## Datasets

1. **Espelhos** - 10 datasets CKAN (1 por orgao), JSONs diarios com resumos
2. **Integras** - 1 dataset CKAN, ZIPs com textos HTML + JSONs de metadados

## Comandos

```bash
cd legal-workbench/ferramentas/stj-dados-abertos
source .venv/bin/activate
export DATA_PATH=/mnt/juridico-data/stj
export DB_PATH=/mnt/juridico-data/stj/database/stj.duckdb

# Testes
pytest tests/ -v

# Download de integras (retomavel)
python cli.py stj-download-integras

# Processar integras
python cli.py stj-processar-integras
```

## Normalizacao Integras

Campos variam entre consolidados mensais e diarios recentes:

| Consolidados | Diarios |
|-------------|---------|
| `seqDocumento` | `SeqDocumento` |
| `ministro` | `NM_MINISTRO` |
| epoch ms | ISO string |
| separador `;` | separador `,` |

## Dependencias

- httpx para requests
- DuckDB para armazenamento
- tenacity para retry

## NUNCA

- Fazer requests ao STJ sem cache check
- Ignorar rate limits da API do STJ
- Modificar tabela `acordaos` ao trabalhar em integras
- Assumir formato fixo de campos (sempre normalizar)

---

*Herdado de: ferramentas/CLAUDE.md*
