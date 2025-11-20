# Scheduler de Download Automático - DJEN

Sistema de agendamento automático para download diário de publicações jurídicas dos principais tribunais brasileiros.

## Visão Geral

O scheduler implementa download automático diário de publicações do DJEN (Diário de Justiça Eletrônico Nacional) para os 10 tribunais prioritários:

- **Superiores:** STJ, STF, TST
- **Estaduais:** TJSP, TJRJ, TJMG, TJRS
- **Federais:** TRF2, TRF3, TRF4

## Funcionalidades

- Download automático diário às 8:00 AM
- Processamento completo de publicações (extração de ementas, relatores, etc)
- Inserção automática no banco SQLite com deduplicação
- Logging detalhado de estatísticas
- Graceful shutdown (SIGINT/SIGTERM)
- Relatório de execução salvo em `downloads_historico`
- Rate limiting inteligente (30 req/min)
- Retry automático em caso de falha

## Instalação

```bash
# 1. Ativar ambiente virtual
cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector
source .venv/bin/activate

# 2. Instalar dependências (se ainda não instaladas)
pip install -r requirements.txt

# 3. Verificar que schedule está instalado
pip list | grep schedule
# Deve mostrar: schedule==1.2.2
```

## Uso Básico

### Execução Interativa (foreground)

```bash
# Executar scheduler (aguarda até 8:00 AM)
python scheduler.py

# Executar job imediatamente + agendar para próximas execuções
python scheduler.py --now
```

### Execução em Background

```bash
# Iniciar scheduler em background
./run_scheduler.sh

# Iniciar e executar job imediatamente
./run_scheduler.sh --now

# Verificar status
./run_scheduler.sh --status

# Parar scheduler
./run_scheduler.sh --stop

# Acompanhar logs em tempo real
tail -f logs/scheduler_background.log
```

## Estrutura de Logs

Todos os logs são salvos em `logs/`:

- `scheduler.log` - Log principal (foreground)
- `scheduler_background.log` - Log quando executado via `run_scheduler.sh`
- `scheduler.pid` - PID do processo em background

Formato de log:
```
2025-11-20 08:00:15 [INFO] __main__: ================================================================================
2025-11-20 08:00:15 [INFO] __main__: INICIANDO JOB DE DOWNLOAD DIÁRIO
2025-11-20 08:00:15 [INFO] __main__: ================================================================================
2025-11-20 08:00:15 [INFO] __main__: Data: 2025-11-20
2025-11-20 08:00:15 [INFO] __main__: Tribunais: 10 (STJ, STF, TST, TJSP, TJRJ, TJMG, TJRS, TRF3, TRF4, TRF2)
2025-11-20 08:00:15 [INFO] __main__: [STJ] Processando tribunal
2025-11-20 08:00:17 [INFO] downloader: [STJ] Total de publicações: 1523 (16 páginas)
2025-11-20 08:01:45 [INFO] __main__: [STJ] ✓ Concluído em 90.2s - 1487 novas publicações
```

## Relatório de Execução

Após cada execução, estatísticas são salvas automaticamente na tabela `downloads_historico`:

```sql
SELECT
    tribunal,
    data_publicacao,
    total_publicacoes,
    total_novas,
    total_duplicadas,
    tempo_processamento,
    status
FROM downloads_historico
WHERE date(data_execucao) = date('now')
ORDER BY tribunal;
```

Exemplo de output:
```
STJ      | 2025-11-20 | Total: 1523  | Novas: 1487 | Duplicadas: 36   | Tempo: 90.2s | Status: sucesso
STF      | 2025-11-20 | Total:  234  | Novas:  230 | Duplicadas:  4   | Tempo: 12.5s | Status: sucesso
TST      | 2025-11-20 | Total:  567  | Novas:  560 | Duplicadas:  7   | Tempo: 34.1s | Status: sucesso
TJSP     | 2025-11-20 | Total: 5421  | Novas: 5380 | Duplicadas: 41   | Tempo: 287.3s | Status: sucesso
...
```

## Integração com Systemd (Produção)

Para executar como serviço permanente no sistema:

### 1. Criar arquivo de serviço

```bash
sudo nano /etc/systemd/system/jurisprudencia-scheduler.service
```

Conteúdo:
```ini
[Unit]
Description=Scheduler de Download DJEN - Jurisprudência
After=network.target

[Service]
Type=simple
User=cmr-auto
WorkingDirectory=/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector
ExecStart=/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector/.venv/bin/python /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector/scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Habilitar e iniciar serviço

```bash
# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviço (iniciar automaticamente no boot)
sudo systemctl enable jurisprudencia-scheduler.service

# Iniciar serviço
sudo systemctl start jurisprudencia-scheduler.service

# Verificar status
sudo systemctl status jurisprudencia-scheduler.service

# Ver logs em tempo real
sudo journalctl -u jurisprudencia-scheduler.service -f
```

### 3. Comandos úteis

```bash
# Parar serviço
sudo systemctl stop jurisprudencia-scheduler.service

# Reiniciar serviço
sudo systemctl restart jurisprudencia-scheduler.service

# Desabilitar serviço (não iniciar no boot)
sudo systemctl disable jurisprudencia-scheduler.service

# Ver logs completos
sudo journalctl -u jurisprudencia-scheduler.service

# Ver logs de hoje
sudo journalctl -u jurisprudencia-scheduler.service --since today
```

## Integração com Cron (Alternativa Simples)

Se preferir usar cron ao invés de systemd:

```bash
# Editar crontab
crontab -e

# Adicionar linha (executar às 8:00 AM todos os dias)
0 8 * * * cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector && .venv/bin/python scheduler.py --now >> logs/cron.log 2>&1

# Verificar jobs agendados
crontab -l
```

**NOTA:** Ao usar cron, o scheduler executa apenas uma vez (não fica em loop). Use `--now` para executar imediatamente.

## Personalização

### Alterar horário de execução

Editar `scheduler.py`:
```python
# Linha ~30
HORARIO_EXECUCAO = "08:00"  # Formato 24h (HH:MM)
```

### Alterar tribunais monitorados

Editar `scheduler.py`:
```python
# Linha ~33-44
TRIBUNAIS_PRIORITARIOS = [
    'STJ',   # Superior Tribunal de Justiça
    'STF',   # Supremo Tribunal Federal
    # ... adicionar/remover tribunais
]
```

Tribunais disponíveis:
- Superiores: STJ, STF, TST, STM, CSJT
- Estaduais: TJSP, TJRJ, TJMG, TJRS, TJPR, TJSC, TJPE, TJBA, TJCE, etc.
- Federais: TRF1, TRF2, TRF3, TRF4, TRF5, TRF6
- Eleitorais: TSE, TRE-SP, TRE-RJ, etc.
- Trabalhistas: TRT01, TRT02, TRT03, etc.

### Alterar rate limiting

Editar `scheduler.py` (linha ~282):
```python
downloader = DJENDownloader(
    data_root=DATA_ROOT,
    requests_per_minute=30,    # Ajustar conforme necessário
    delay_seconds=2.0,         # Delay fixo entre requests
    max_retries=3
)
```

## Monitoramento

### Verificar última execução

```sql
-- Ver última execução
SELECT
    MAX(data_execucao) as ultima_execucao,
    COUNT(*) as total_tribunais,
    SUM(total_novas) as total_publicacoes_novas
FROM downloads_historico;
```

### Estatísticas por tribunal (últimos 30 dias)

```sql
SELECT
    tribunal,
    COUNT(*) as execucoes,
    SUM(total_novas) as total_publicacoes,
    AVG(tempo_processamento) as tempo_medio_segundos,
    SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucessos,
    SUM(CASE WHEN status = 'falha' THEN 1 ELSE 0 END) as falhas
FROM downloads_historico
WHERE date(data_execucao) >= date('now', '-30 days')
GROUP BY tribunal
ORDER BY total_publicacoes DESC;
```

### Detectar problemas

```sql
-- Ver falhas recentes
SELECT
    tribunal,
    data_publicacao,
    erro,
    data_execucao
FROM downloads_historico
WHERE status = 'falha'
  AND date(data_execucao) >= date('now', '-7 days')
ORDER BY data_execucao DESC;
```

## Solução de Problemas

### Scheduler não inicia

```bash
# Verificar se porta/processo não está travado
ps aux | grep scheduler

# Limpar PID file obsoleto
rm -f scheduler.pid

# Verificar logs
tail -50 logs/scheduler.log
```

### Erro de importação (module not found)

```bash
# Recriar ambiente virtual
cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Rate limiting (HTTP 429)

O scheduler já implementa backoff exponencial automático. Se persistir:

1. Aumentar `delay_seconds` em `scheduler.py`
2. Reduzir `requests_per_minute`
3. Distribuir tribunais em múltiplas execuções

### Banco de dados travado (SQLite locked)

```bash
# Verificar processos acessando o banco
lsof jurisprudencia.db

# Se necessário, parar scheduler
./run_scheduler.sh --stop

# Verificar integridade do banco
sqlite3 jurisprudencia.db "PRAGMA integrity_check;"
```

## Arquitetura de Dados

Dados baixados são salvos em:

```
data/
├── downloads/          # JSONs baixados (backup)
│   ├── STJ/
│   ├── TJSP/
│   └── ...
├── logs/               # Logs do downloader
└── cache/              # Cache de hashes (deduplicação)
    └── hashes.json
```

Banco de dados:
```
jurisprudencia.db
├── publicacoes         # Textos completos
├── downloads_historico # Metadados de download
├── publicacoes_fts     # Índice FTS5 (busca textual)
└── ... (outras tabelas)
```

## Performance Estimada

**Por tribunal/dia:**
- STJ: ~1.500 publicações, ~90 segundos
- TJSP: ~5.000 publicações, ~300 segundos
- Outros: ~500-2.000 publicações, ~30-120 segundos

**Total (10 tribunais):**
- Tempo estimado: ~30 minutos
- Publicações: ~15.000-20.000/dia
- Espaço em disco: ~200 MB/dia

## Referências

- `docs/ARQUITETURA_JURISPRUDENCIA.md` - Arquitetura completa do sistema
- `src/downloader.py` - Implementação do downloader
- `src/processador_texto.py` - Processamento de publicações
- `schema.sql` - Esquema do banco de dados

---

**Última atualização:** 2025-11-20
**Autor:** Claude Code (Sonnet 4.5)
