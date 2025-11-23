# STJ Dados Abertos

Sistema de coleta, processamento e análise de acórdãos do Superior Tribunal de Justiça via API de Dados Abertos.

## Características

- **Download automatizado** de acórdãos por órgão julgador e período
- **Banco DuckDB otimizado** para 50GB+ de dados
- **Full-text search** em ementas e inteiro teor
- **CLI específica** com comandos descritivos
- **Reaproveitamento** de código do sistema DJEN

## Estrutura

```
stj-dados-abertos/
├── cli.py              # CLI principal com comandos específicos
├── config.py           # Configurações centralizadas
├── requirements.txt    # Dependências
└── src/
    ├── downloader.py   # Download de JSONs do STJ
    ├── processor.py    # Processamento com reuso de código DJEN
    └── database.py     # Banco DuckDB otimizado
```

## Setup

### 1. Ativar Virtual Environment

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/stj-dados-abertos
source .venv/bin/activate
```

### 2. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 3. Verificar HD Externo

O sistema armazena dados em `/mnt/e/` (HD externo):

```bash
ls /mnt/e/
```

Se não estiver montado:
```bash
# Verificar discos disponíveis
lsblk

# Montar (ajustar /dev/sdX conforme necessário)
sudo mount /dev/sdc1 /mnt/e
```

### 4. Inicializar Sistema

```bash
python cli.py stj-init
```

Isso criará:
- Diretórios de dados em `/mnt/e/stj-data/`
- Schema do banco DuckDB
- Índices para full-text search

## Uso

### Comandos de Download

#### Download por Período

```bash
# Baixar 6 meses da Terceira Turma
python cli.py stj-download-periodo 2024-01-01 2024-06-30 --orgao terceira_turma

# Forçar re-download (sobrescrever existentes)
python cli.py stj-download-periodo 2024-01-01 2024-06-30 --orgao corte_especial --force
```

#### Download por Órgão

```bash
# Baixar últimos 3 meses da Primeira Seção
python cli.py stj-download-orgao primeira_secao --meses 3

# Baixar últimos 12 meses da Corte Especial
python cli.py stj-download-orgao corte_especial --meses 12
```

#### Download MVP (Teste Rápido)

```bash
# Baixar últimos 30 dias da Corte Especial (para testes)
python cli.py stj-download-mvp
```

### Comandos de Processamento

#### Processar Staging

```bash
# Processar todos os JSONs do staging
python cli.py stj-processar-staging

# Processar apenas arquivos de um órgão específico
python cli.py stj-processar-staging --pattern "corte_especial_*.json"

# Atualizar registros duplicados (se houver mudanças)
python cli.py stj-processar-staging --atualizar
```

### Comandos de Busca

#### Buscar em Ementas

```bash
# Busca básica
python cli.py stj-buscar-ementa "responsabilidade civil"

# Busca com filtros
python cli.py stj-buscar-ementa "dano moral" --orgao terceira_turma --dias 90 --limit 50

# Busca em todo o banco (últimos 365 dias)
python cli.py stj-buscar-ementa "recurso especial" --dias 365
```

#### Buscar em Inteiro Teor

```bash
# ATENÇÃO: Pode ser lento! Use filtros temporais.
python cli.py stj-buscar-acordao "dano moral" --dias 30 --limit 10

# Busca filtrada por órgão
python cli.py stj-buscar-acordao "contrato de consumo" --orgao segunda_turma --dias 60
```

### Comandos de Estatísticas

#### Ver Estatísticas Gerais

```bash
python cli.py stj-estatisticas
```

Mostra:
- Total de acórdãos no banco
- Distribuição por órgão julgador
- Distribuição por tipo de decisão (Acórdão vs Monocrática)
- Período coberto
- Acórdãos dos últimos 30 dias
- Tamanho do banco em MB

### Comandos de Exportação

#### Exportar Resultados para CSV

```bash
# Exportar top 100 acórdãos mais recentes
python cli.py stj-exportar "SELECT * FROM acordaos ORDER BY data_publicacao DESC LIMIT 100" --output top100.csv

# Exportar acórdãos de um órgão específico
python cli.py stj-exportar "SELECT numero_processo, ementa, relator FROM acordaos WHERE orgao_julgador = 'Terceira Turma'" --output terceira_turma.csv

# Exportar ementas com termo específico
python cli.py stj-exportar "SELECT * FROM acordaos WHERE ementa LIKE '%responsabilidade civil%'" --output resp_civil.csv
```

### Comandos de Utilidade

#### Ver Informações do Sistema

```bash
python cli.py stj-info
```

Mostra:
- Paths configurados
- Status do HD externo
- Órgãos julgadores disponíveis
- Comandos principais

## Órgãos Julgadores Disponíveis

| Chave | Nome Completo | Prioridade |
|-------|---------------|------------|
| `corte_especial` | Corte Especial | 1 (mais importante) |
| `primeira_secao` | Primeira Seção | 2 |
| `segunda_secao` | Segunda Seção | 2 |
| `terceira_secao` | Terceira Seção | 3 |
| `primeira_turma` | Primeira Turma | 4 |
| `segunda_turma` | Segunda Turma | 4 |
| `terceira_turma` | Terceira Turma | 4 |
| `quarta_turma` | Quarta Turma | 4 |
| `quinta_turma` | Quinta Turma | 4 |
| `sexta_turma` | Sexta Turma | 4 |

## Terminologia Jurídica

**IMPORTANTE:** Usar grafia correta em código e documentação:

- ✅ **acórdão** (plural: acórdãos) - decisão colegiada do tribunal
- ✅ **decisão monocrática** - decisão individual do relator
- ✅ **ementa** - resumo oficial do acórdão
- ✅ **inteiro teor** - texto completo do acórdão
- ✅ **órgão julgador** (não "orgão") - turma/seção que julgou
- ✅ **relator** - ministro responsável pelo processo
- ✅ **jurisprudência** - conjunto de decisões

## Schema do Banco

```sql
CREATE TABLE acordaos (
    id VARCHAR PRIMARY KEY,
    numero_processo VARCHAR NOT NULL,
    hash_conteudo VARCHAR UNIQUE NOT NULL,

    -- Classificação
    tribunal VARCHAR DEFAULT 'STJ',
    orgao_julgador VARCHAR NOT NULL,
    tipo_decisao VARCHAR,
    classe_processual VARCHAR,

    -- Conteúdo
    ementa TEXT,
    texto_integral TEXT,  -- Comprimido automaticamente
    relator VARCHAR,

    -- Datas
    data_publicacao TIMESTAMP,
    data_julgamento TIMESTAMP,
    data_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    assuntos TEXT,  -- JSON array
    fonte VARCHAR DEFAULT 'STJ-Dados-Abertos',
    fonte_url VARCHAR,
    metadata TEXT
);
```

### Índices

- `idx_hash` - Deduplicação por hash do conteúdo
- `idx_processo` - Busca por número de processo
- `idx_orgao` - Filtro por órgão julgador
- `idx_data_publicacao` - Queries temporais
- `idx_recentes` - Índice parcial (últimos 90 dias, queries frequentes)
- `fts_ementa` - Full-text search em ementas
- `fts_texto_integral` - Full-text search em inteiro teor

## Performance

### Otimizações Implementadas

1. **WAL mode** - Melhor performance em HD externo
2. **Batch insert** - 1000 registros por transação (configurável)
3. **Deduplicação por hash** - Evita inserções duplicadas
4. **Compressão ZSTD** - Automática pelo DuckDB
5. **Índices parciais** - Últimos 90 dias (queries mais comuns)
6. **FTS otimizado** - Full-text search com BM25 ranking

### Limites Testados

- ✅ **Volume:** Otimizado para 50GB+ de dados
- ✅ **Threads:** 4 threads DuckDB
- ✅ **Memória:** Limite de 4GB (configurável em `config.py`)
- ✅ **Batch size:** 1000 registros/transação

### Dicas de Performance

#### Para Downloads

```bash
# Download paralelo não implementado - STJ não tem rate limits documentados
# Mas pode ser adicionado se necessário (config.CONCURRENT_DOWNLOADS = 4)
```

#### Para Buscas

```bash
# Busca em EMENTA é mais rápida (índice menor)
python cli.py stj-buscar-ementa "termo" --dias 90

# Busca em INTEIRO TEOR é mais lenta - use filtros temporais!
python cli.py stj-buscar-acordao "termo" --dias 30 --limit 10

# Para grandes períodos, use exportação SQL direta
python cli.py stj-exportar "SELECT ... WHERE ..." --output resultado.csv
```

## Troubleshooting

### HD Externo Não Acessível

**Erro:**
```
❌ HD externo não acessível: /mnt/e/
```

**Solução:**
```bash
# Verificar discos
lsblk

# Montar HD
sudo mount /dev/sdc1 /mnt/e

# Verificar montagem
df -h | grep /mnt/e
```

### Arquivo JSON Vazio ou Inválido

**Erro:**
```
Resposta não é JSON válido de URL
```

**Causa:** Alguns meses podem não ter dados publicados.

**Comportamento:** Sistema loga warning mas continua (não é erro fatal).

### Banco de Dados Corrompido

**Solução:**
```bash
# Criar backup
cp /mnt/e/stj-data/database/stj.duckdb /mnt/e/stj-data/database/stj.duckdb.backup

# Re-criar schema
python cli.py stj-init

# Re-processar staging
python cli.py stj-processar-staging
```

### Performance Lenta em Buscas

**Dicas:**

1. **Use filtros temporais:**
   ```bash
   # Rápido (últimos 30 dias)
   python cli.py stj-buscar-acordao "termo" --dias 30

   # Lento (todo o banco)
   python cli.py stj-buscar-acordao "termo" --dias 3650
   ```

2. **Busque em ementa, não inteiro teor:**
   ```bash
   # Rápido
   python cli.py stj-buscar-ementa "termo"

   # Lento
   python cli.py stj-buscar-acordao "termo"
   ```

3. **Use SQL direto para queries complexas:**
   ```bash
   python cli.py stj-exportar "SELECT ... WHERE ..." --output resultado.csv
   ```

## Roadmap

### MVP (Sprint Atual)
- [x] Downloader para JSONs do STJ
- [x] Processador com reuso de código DJEN
- [x] Database DuckDB otimizado
- [x] CLI com comandos específicos
- [ ] Testes unitários (database.py)
- [ ] Testes de integração (CLI end-to-end)

### Futuro
- [ ] Download paralelo (se necessário)
- [ ] Interface web (FastAPI + React)
- [ ] API REST para consultas
- [ ] Exportação para formatos adicionais (Parquet, Excel)
- [ ] Alertas automáticos (webhook/email)
- [ ] Dashboard de estatísticas

## Reaproveitamento de Código DJEN

Este sistema **reaproveita** funções do sistema jurisprudencia-collector (DJEN):

```python
from processador_texto import (
    extrair_ementa,
    extrair_relator
)
```

**Vantagens:**
- Zero retrabalho
- Mesma qualidade de extração
- Manutenção centralizada

**DIFERENÇA CRÍTICA:**
- **DJEN:** Input é HTML (precisa parsear)
- **STJ:** Input é JSON estruturado (campos já separados)

## Referências

- **API STJ Dados Abertos:** https://www.stj.jus.br/sites/portalp/Inicio/Transparencia-e-prestacao-de-contas/Dados-abertos
- **DuckDB Docs:** https://duckdb.org/docs/
- **Typer Docs:** https://typer.tiangolo.com/

---

**Desenvolvido para:** Coleta automatizada de jurisprudência do STJ
**Stack:** Python 3.12 + DuckDB + Typer + Rich
**Armazenamento:** HD externo (50GB+)
