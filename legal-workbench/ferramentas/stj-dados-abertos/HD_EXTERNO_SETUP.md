# 🗂️ Configuração do HD Externo - Base de Dados Jurídica

## 📋 O que você precisa fazer

### Opção 1: Rodar o script automático (RECOMENDADO)

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/ferramentas/stj-dados-abertos
./setup_hd_externo.sh
```

O script vai:
1. ✅ Detectar automaticamente seu HD externo (/mnt/e/, /mnt/d/, etc)
2. ✅ Criar toda a estrutura de diretórios
3. ✅ Configurar permissões
4. ✅ Testar performance
5. ✅ Criar arquivo de configuração
6. ✅ Criar link simbólico ~/juridico-data

### Opção 2: Configuração manual

Se preferir fazer manualmente ou o script falhar:

```bash
# 1. Verificar onde está o HD
ls /mnt/

# 2. Criar estrutura (substitua /mnt/e pelo seu)
mkdir -p /mnt/e/juridico-data/{stj,tjsp,stf,shared}/{archive,staging,database,processed}

# 3. Criar link simbólico
ln -s /mnt/e/juridico-data ~/juridico-data

# 4. Testar acesso
touch ~/juridico-data/test.txt && rm ~/juridico-data/test.txt
echo "✅ HD configurado com sucesso!"
```

## 🏗️ Estrutura Criada

```
/mnt/e/juridico-data/                 # Base de todos os dados jurídicos
├── stj/                               # STJ Dados Abertos
│   ├── archive/                       # ZIPs históricos organizados por ano
│   │   ├── 2022/
│   │   ├── 2023/
│   │   ├── 2024/
│   │   └── 2025/
│   ├── staging/                       # JSONs temporários para processamento
│   ├── processed/                     # Arquivos já processados
│   └── database/
│       └── stj.duckdb                 # Base principal STJ (~50GB quando completa)
│
├── tjsp/                              # TJSP (estrutura pronta para futuro)
│   ├── archive/
│   ├── staging/
│   ├── processed/
│   └── database/
│       └── tjsp.duckdb
│
├── stf/                               # STF (estrutura pronta para futuro)
│   ├── archive/
│   ├── staging/
│   ├── processed/
│   └── database/
│       └── stf.duckdb
│
├── shared/                            # Recursos compartilhados entre projetos
│   ├── embeddings/                   # Vetores para RAG/semantic search
│   ├── models/                        # Modelos ML baixados
│   ├── cache/                         # Cache geral
│   └── temp/                          # Arquivos temporários
│
├── databases/                         # Bases consolidadas (futuro)
├── exports/                           # Exportações CSV/JSON
├── logs/                              # Logs centralizados
├── backups/                           # Backups automáticos
└── config.json                        # Configuração central
```

## 🚀 Por que essa estrutura?

### 1. **Performance no WSL2**
- Acesso direto via `/mnt/e/` é **10x mais rápido** que filesystem Windows nativo
- DuckDB com WAL mode funciona perfeitamente em mount
- Staging local minimiza I/O durante processamento

### 2. **Escalabilidade**
- Estrutura pronta para 3 tribunais (STJ, TJSP, STF)
- Fácil adicionar novos (TRFs, TRTs, etc)
- Shared resources evita duplicação

### 3. **Organização**
- Separação clara: archive (permanente) vs staging (temporário)
- Processed tracking evita reprocessamento
- Backups automáticos protegem dados

### 4. **Reusabilidade**
Outros projetos podem usar a mesma base:

```python
# Qualquer projeto Python pode acessar
import duckdb

# Conectar na base STJ
conn = duckdb.connect('/mnt/e/juridico-data/stj/database/stj.duckdb', read_only=True)

# Query simples
df = conn.execute("""
    SELECT numero_processo, ementa, data_publicacao
    FROM acordaos
    WHERE orgao_julgador = 'Corte Especial'
    ORDER BY data_publicacao DESC
    LIMIT 10
""").df()

# Ou usar o link simbólico
conn = duckdb.connect('~/juridico-data/stj/database/stj.duckdb')
```

## 📊 Estimativas de Espaço

| Tribunal | Período | Tamanho Estimado | Crescimento/Mês |
|----------|---------|------------------|-----------------|
| STJ | 2022-2025 | ~50GB | 1-2GB |
| TJSP | 2020-2025 | ~200GB | 5-10GB |
| STF | 2022-2025 | ~30GB | 0.5-1GB |
| **Total** | | **~300GB** | **~10GB/mês** |

## 🔧 Manutenção

### Limpeza automática (staging)
```bash
# Remover arquivos staging > 7 dias
find ~/juridico-data/stj/staging -type f -mtime +7 -delete
```

### Backup do database
```bash
# Backup mensal
cp ~/juridico-data/stj/database/stj.duckdb \
   ~/juridico-data/backups/stj_$(date +%Y%m%d).duckdb
```

### Verificar integridade
```bash
# No Python/DuckDB
import duckdb
conn = duckdb.connect('~/juridico-data/stj/database/stj.duckdb')
conn.execute("PRAGMA integrity_check").fetchall()
```

## ✅ Validação

Após rodar o script, verifique:

```bash
# 1. Estrutura criada
ls -la ~/juridico-data/

# 2. Permissões OK
touch ~/juridico-data/test.txt && rm ~/juridico-data/test.txt

# 3. Espaço disponível
df -h /mnt/e/

# 4. Config criada
cat ~/juridico-data/config.json
```

## 🎯 Próximos Passos

1. **Rodar o script de setup do HD**:
   ```bash
   ./setup_hd_externo.sh
   ```

2. **Atualizar o config.py do STJ** (já vai estar feito após rodar o script):
   ```python
   # O .env criado já tem os paths corretos
   source .env
   ```

3. **Testar com download pequeno**:
   ```bash
   python cli.py stj-download-periodo --inicio 2024-11-01 --fim 2024-11-10 --orgao corte_especial
   ```

4. **Para outros projetos**, usar os paths:
   - TJSP: `/mnt/e/juridico-data/tjsp/`
   - STF: `/mnt/e/juridico-data/stf/`
   - Embeddings compartilhados: `/mnt/e/juridico-data/shared/embeddings/`

## 💡 Dicas

- **Performance**: Sempre processe em staging primeiro, depois mova para archive
- **Deduplicação**: Use hash SHA256 para evitar duplicatas entre fontes
- **Queries**: Crie views materializadas para queries frequentes
- **Exports**: Use Parquet para exportações grandes (melhor que CSV)

---

**Essa estrutura está preparada para crescer com seus projetos jurídicos!** 🚀