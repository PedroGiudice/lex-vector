# Quick Start - STJ Dados Abertos

Guia rápido para começar a usar o sistema em 5 minutos.

## 1. Setup Inicial (1 minuto)

```bash
# Ir para o diretório
cd ~/claude-work/repos/Claude-Code-Projetos/ferramentas/stj-dados-abertos

# Ativar venv
source .venv/bin/activate

# Verificar HD externo
ls /mnt/e/

# Inicializar sistema
python cli.py stj-init
```

**Saída esperada:**
```
✅ HD externo acessível: /mnt/e
✅ Schema do banco criado

Diretórios criados:
  • Staging: /mnt/e/stj-data/staging
  • Database: /mnt/e/stj-data/database
  • Logs: /mnt/e/stj-data/logs
```

## 2. Primeiro Download (2 minutos)

### Opção A: Download MVP (mais rápido)

```bash
# Baixar últimos 30 dias da Corte Especial (teste rápido)
python cli.py stj-download-mvp
```

### Opção B: Download Específico

```bash
# Baixar últimos 3 meses da Terceira Turma
python cli.py stj-download-orgao terceira_turma --meses 3
```

**Saída esperada:**
```
📥 Baixando 3 arquivos...
████████████████████████████████████████ 100%

Estatísticas de Download:
✅ Baixados: 2
⏭️  Pulados: 0
❌ Falhas: 1

✅ Download concluído: 2 arquivos
📁 Diretório: /mnt/e/stj-data/staging
```

## 3. Processar e Inserir no Banco (1 minuto)

```bash
python cli.py stj-processar-staging
```

**Saída esperada:**
```
⚙️  Processando arquivos do staging...

📊 Arquivos encontrados: 2
  • terceira_turma_202409.json
  • terceira_turma_202410.json

Inserindo 245 registros...
████████████████████████████████████████ 100%

✅ Processamento concluído:
  • Inseridos: 245
  • Duplicados: 0
  • Erros: 0

📊 Total no banco: 245 acórdãos
```

## 4. Primeira Busca (1 minuto)

```bash
# Buscar "responsabilidade civil" nas ementas
python cli.py stj-buscar-ementa "responsabilidade civil" --limit 5
```

**Saída esperada:**
```
🔍 Buscando 'responsabilidade civil' nas ementas...
📅 Período: últimos 365 dias

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Processo          ┃ Órgão          ┃ Relator                 ┃ Data Pub.  ┃ Ementa (preview)     ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ REsp 1234567/SP   │ Terceira Turma │ Min. Paulo Sanseverino  │ 2024-10-15 │ RESPONSABILIDADE ... │
│ REsp 1234568/RJ   │ Terceira Turma │ Min. Ricardo Villas...  │ 2024-10-10 │ CIVIL. DANO MORAL... │
│ REsp 1234569/MG   │ Terceira Turma │ Min. Nancy Andrighi     │ 2024-10-05 │ CONSUMIDOR. RESP...  │
└───────────────────┴────────────────┴─────────────────────────┴────────────┴──────────────────────┘

✅ 3 resultado(s) encontrado(s)
```

## 5. Ver Estatísticas

```bash
python cli.py stj-estatisticas
```

**Saída esperada:**
```
📊 Estatísticas do Banco STJ

Total de acórdãos: 245
Tamanho do banco: 12.45 MB

Período coberto:
  • Mais antigo: 2024-08-01 00:00:00
  • Mais recente: 2024-11-20 00:00:00

Últimos 30 dias: 78 acórdãos

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Órgão                       ┃ Quantidade ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Terceira Turma              │        245 │
└─────────────────────────────┴────────────┘
```

## Comandos Mais Usados

### Download

```bash
# Download rápido (MVP)
python cli.py stj-download-mvp

# Download por órgão
python cli.py stj-download-orgao corte_especial --meses 6

# Download por período
python cli.py stj-download-periodo 2024-01-01 2024-06-30 --orgao terceira_turma
```

### Processamento

```bash
# Processar tudo
python cli.py stj-processar-staging

# Processar apenas um órgão
python cli.py stj-processar-staging --pattern "terceira_turma_*.json"

# Atualizar registros duplicados
python cli.py stj-processar-staging --atualizar
```

### Busca

```bash
# Busca rápida em ementa
python cli.py stj-buscar-ementa "dano moral"

# Busca com filtros
python cli.py stj-buscar-ementa "contrato" --orgao segunda_turma --dias 90

# Busca em inteiro teor (mais lento)
python cli.py stj-buscar-acordao "boa-fé objetiva" --dias 30
```

### Exportação

```bash
# Exportar top 100
python cli.py stj-exportar "SELECT * FROM acordaos LIMIT 100" --output top100.csv

# Exportar filtrado
python cli.py stj-exportar "SELECT * FROM acordaos WHERE orgao_julgador = 'Terceira Turma'" --output terceira.csv
```

## Workflow Completo

### Cenário: Analisar acórdãos sobre responsabilidade civil dos últimos 6 meses

```bash
# 1. Download (6 meses da Terceira Turma)
python cli.py stj-download-orgao terceira_turma --meses 6

# 2. Processar
python cli.py stj-processar-staging --pattern "terceira_turma_*.json"

# 3. Buscar
python cli.py stj-buscar-ementa "responsabilidade civil" --dias 180 --limit 50

# 4. Exportar resultados
python cli.py stj-exportar "
    SELECT
        numero_processo,
        relator,
        data_publicacao,
        ementa
    FROM acordaos
    WHERE ementa LIKE '%responsabilidade civil%'
        AND data_publicacao >= CURRENT_DATE - INTERVAL '6 months'
    ORDER BY data_publicacao DESC
" --output resp_civil_6m.csv

# 5. Ver estatísticas
python cli.py stj-estatisticas
```

## Troubleshooting Rápido

### HD não acessível

```bash
# Verificar
ls /mnt/e/

# Se não existir, montar
sudo mount /dev/sdc1 /mnt/e
```

### Nenhum arquivo baixado

```bash
# Verificar diretório staging
ls -la /mnt/e/stj-data/staging/

# Forçar re-download
python cli.py stj-download-mvp --force
```

### Busca sem resultados

```bash
# Verificar se há dados no banco
python cli.py stj-estatisticas

# Se vazio, processar staging
python cli.py stj-processar-staging
```

## Próximos Passos

1. **Expandir coleta:** Baixar mais órgãos julgadores
   ```bash
   for orgao in corte_especial primeira_turma segunda_turma; do
       python cli.py stj-download-orgao $orgao --meses 12
   done
   ```

2. **Automatizar:** Criar script de atualização diária
   ```bash
   # download_diario.sh
   #!/bin/bash
   cd ~/claude-work/repos/Claude-Code-Projetos/ferramentas/stj-dados-abertos
   source .venv/bin/activate
   python cli.py stj-download-mvp
   python cli.py stj-processar-staging
   ```

3. **Análise avançada:** Usar SQL direto
   ```sql
   -- Top 10 relatores mais ativos
   SELECT relator, COUNT(*) as total
   FROM acordaos
   GROUP BY relator
   ORDER BY total DESC
   LIMIT 10;
   ```

## Ajuda

```bash
# Ver todos os comandos
python cli.py --help

# Ajuda de comando específico
python cli.py stj-buscar-ementa --help

# Ver informações do sistema
python cli.py stj-info
```

## Limites e Performance

- ✅ **Download:** Sem rate limits (STJ não documenta)
- ✅ **Processamento:** ~1000 registros/segundo
- ✅ **Busca ementa:** <1 segundo (índice FTS)
- ⚠️ **Busca inteiro teor:** Pode ser lento (use `--dias 30`)
- ✅ **Exportação:** ~100k registros/segundo

---

**Dúvidas?** Consulte [README.md](README.md) para documentação completa.
