# DJEN Tracker v1.0

Monitor **contínuo** e automático de cadernos DJEN com download inteligente.

## ✨ Features State-of-the-Art

- 🔄 **Download Contínuo**: Loop infinito com intervalo configurável (default 30min)
- 🏛️ **Tribunais Prioritários**: STF, STJ, TJSP 2ª Instância
- 🚦 **Rate Limiting Inteligente**: 20 req/min + backoff exponencial em 429
- 💾 **Checkpoint System**: Resume downloads após interrupção (Ctrl+C)
- 🔗 **Integração oab-watcher**: Usa TextParser e BuscaInteligente (opcional)
- 📊 **Estatísticas em Tempo Real**: Downloads, erros, duplicatas, MB baixados

## Arquitetura

```
src/
├── rate_limiter.py           # Rate limiting + backoff exponencial
├── continuous_downloader.py  # Download contínuo com retry automático
└── __init__.py               # Exports limpos (v1.0.0)
```

**Tribunais Monitorados:**
- **STF** (Supremo Tribunal Federal)
- **STJ** (Superior Tribunal de Justiça)
- **TJSP 2ª Instância** (Tribunal de Justiça de São Paulo)

## Setup Rápido

```powershell
cd agentes\djen-tracker
.\run_agent.ps1  # Detecta uv/pip automaticamente
```

## Uso

### 1. Download Contínuo (Recomendado) 🔄

Roda **indefinidamente** até ser interrompido:

```bash
python main.py
# Escolha opção 1
# Intervalo: 30 minutos (ou personalizar)
# Ctrl+C para parar (salva checkpoint automaticamente)
```

**O que faz:**
- A cada 30min, baixa cadernos novos de STF, STJ, TJSP
- Pula duplicatas (checkpoint)
- Retry automático em falhas
- Backoff exponencial se receber 429
- Estatísticas contínuas no console

### 2. Download de Hoje (Única Vez)

```bash
python main.py
# Escolha opção 2
```

### 3. Download de Data Específica

```bash
python main.py
# Escolha opção 3
# Informar: 2025-11-07
```

## Configuração (config.json)

```json
{
  "tribunais": {
    "prioritarios": ["STF", "STJ", "TJSP"]
  },
  "download": {
    "intervalo_minutos": 30,
    "max_concurrent": 3,
    "retry_attempts": 3,
    "timeout_seconds": 60
  },
  "rate_limiting": {
    "requests_per_minute": 20,
    "delay_between_requests_seconds": 3,
    "backoff_on_429": true,
    "max_backoff_seconds": 300
  },
  "integracao_oab_watcher": {
    "enabled": true,
    "usar_cache": true,
    "usar_text_parser": true
  }
}
```

## Integração com oab-watcher

O djen-tracker **importa automaticamente** componentes do oab-watcher se disponível:

```python
sys.path.insert(0, "../oab-watcher")
from src import CacheManager, TextParser, BuscaInteligente
```

**Agentes separados mas integrados:**
- `oab-watcher/` - Busca inteligente por OAB
- `djen-tracker/` - Download contínuo de cadernos (este agente)

Se oab-watcher não estiver disponível, funciona normalmente sem análise.

## Estrutura de Dados (E:\)

**Separado do oab-watcher:**

```
E:\claude-code-data\agentes\djen-tracker\
├── cadernos/
│   ├── STF/              # PDFs do Supremo
│   │   └── STF_2025-11-08_1_abc123.pdf
│   ├── STJ/              # PDFs do Superior
│   │   └── STJ_2025-11-08_1_def456.pdf
│   └── TJSP/             # PDFs do TJSP 2ª Instância
│       └── TJSP_2025-11-08_2_ghi789.pdf
├── logs/
│   └── djen_tracker_20251108_120000.log
├── cache/                # Cache oab-watcher (se integrado)
│   └── cache.db
└── checkpoint.json       # Resumir downloads
```

## Exemplo de Execução

```
================================================================
DOWNLOAD CONTÍNUO INICIADO
Intervalo: 30 minutos
Tribunais: STF, STJ, TJSP
Ctrl+C para interromper
================================================================

>>> CICLO #1

======================================================================
CICLO DE DOWNLOAD - 2025-11-08
======================================================================

[STF] 2 cadernos disponíveis em 2025-11-08
[STF] ✓ STF_2025-11-08_1_abc123.pdf (12.3MB em 8.2s)
[STF] ✓ STF_2025-11-08_2_def456.pdf (15.7MB em 10.1s)

[STJ] 3 cadernos disponíveis em 2025-11-08
[STJ] ✓ STJ_2025-11-08_1_ghi789.pdf (8.9MB em 6.3s)
[STJ] Duplicata: STJ_2025-11-08_2_jkl012.pdf
[STJ] ✓ STJ_2025-11-08_3_mno345.pdf (11.2MB em 7.8s)

[TJSP] 5 cadernos disponíveis em 2025-11-08
[TJSP] ✓ TJSP_2025-11-08_1_pqr678.pdf (25.4MB em 14.5s)
...

======================================================================
RESUMO DO CICLO - 2025-11-08
Sucessos: 8 | Falhas: 0 | Duplicatas: 1
======================================================================

======================================================================
ESTATÍSTICAS GLOBAIS
Total downloads: 9
Sucessos: 8
Falhas: 0
Duplicatas: 1
Bytes baixados: 127.3MB
Rate limiter: {'requests_last_minute': 12, 'backoff_level': 0}
======================================================================

Aguardando 30 minutos até próximo ciclo...
```

## Checkpoint e Retomada

Se interromper (Ctrl+C) ou houver erro, o checkpoint salva progresso:

```json
{
  "STF_abc123": {
    "arquivo": "E:/claude-code-data/agentes/djen-tracker/cadernos/STF/STF_2025-11-08_1_abc123.pdf",
    "timestamp": "2025-11-08T12:30:45",
    "tamanho": 12893456
  }
}
```

Na próxima execução, **pula downloads já feitos** (duplicatas).

## Status

✅ **Implementado** - Pronto para produção!

**Componentes:**
- ✅ Rate Limiter com backoff exponencial
- ✅ Continuous Downloader com checkpoint
- ✅ Integração oab-watcher (opcional)
- ✅ Retry automático
- ✅ Estatísticas em tempo real
- ✅ Loop infinito configurável
