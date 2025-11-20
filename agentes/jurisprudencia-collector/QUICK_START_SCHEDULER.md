# Quick Start - Scheduler

Guia rápido para começar a usar o scheduler de download automático.

## Execução Rápida

### Opção 1: Executar job imediatamente (foreground)

```bash
cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector
source .venv/bin/activate
python scheduler.py --now
```

Isso vai:
1. Executar download de TODOS os 10 tribunais AGORA
2. Agendar próxima execução para 8:00 AM de amanhã
3. Ficar rodando em foreground (Ctrl+C para parar)

### Opção 2: Executar em background (recomendado)

```bash
cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector
./run_scheduler.sh --now
```

Isso vai:
1. Executar download de TODOS os 10 tribunais AGORA
2. Continuar rodando em background
3. Salvar logs em `logs/scheduler_background.log`

### Opção 3: Apenas agendar (sem executar agora)

```bash
cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector
./run_scheduler.sh
```

Isso vai:
1. Aguardar até 8:00 AM de amanhã
2. Executar download automaticamente
3. Continuar executando diariamente às 8:00 AM

## Comandos Úteis

```bash
# Ver status
./run_scheduler.sh --status

# Parar scheduler
./run_scheduler.sh --stop

# Acompanhar logs em tempo real
tail -f logs/scheduler_background.log

# Ver últimas 50 linhas do log
tail -50 logs/scheduler.log
```

## Verificar Resultados

```bash
# Conectar ao banco
sqlite3 jurisprudencia.db

# Ver última execução
SELECT * FROM downloads_historico ORDER BY data_execucao DESC LIMIT 10;

# Ver total de publicações por tribunal
SELECT
    tribunal,
    SUM(total_novas) as total_publicacoes,
    COUNT(*) as execucoes
FROM downloads_historico
GROUP BY tribunal
ORDER BY total_publicacoes DESC;

# Sair
.quit
```

## O que Esperar

### Primeira Execução (--now)

```
2025-11-20 19:30:00 [INFO] INICIANDO JOB DE DOWNLOAD DIÁRIO
2025-11-20 19:30:00 [INFO] Data: 2025-11-20
2025-11-20 19:30:00 [INFO] Tribunais: 10 (STJ, STF, TST, TJSP, TJRJ, TJMG, TJRS, TRF3, TRF4, TRF2)

2025-11-20 19:30:15 [INFO] [STJ] Processando tribunal
2025-11-20 19:30:17 [INFO] [STJ] Total de publicações: 1523 (16 páginas)
2025-11-20 19:31:45 [INFO] [STJ] ✓ Concluído em 90.2s - 1487 novas publicações

... (continua para outros tribunais) ...

2025-11-20 20:00:00 [INFO] RELATÓRIO FINAL DO JOB DE DOWNLOAD
2025-11-20 20:00:00 [INFO] Tempo total: 1800.5s (30.0 minutos)
2025-11-20 20:00:00 [INFO] Tribunais processados: 10
2025-11-20 20:00:00 [INFO]   ✓ Sucesso: 10
2025-11-20 20:00:00 [INFO]   ✗ Falha: 0
2025-11-20 20:00:00 [INFO] Publicações novas: 18724
2025-11-20 20:00:00 [INFO] Publicações duplicadas: 156
```

### Tempo Estimado

- **STJ:** ~90 segundos (1.500 publicações)
- **TJSP:** ~300 segundos (5.000 publicações)
- **Outros:** ~30-120 segundos (500-2.000 publicações cada)
- **Total:** ~30 minutos para todos os 10 tribunais

### Espaço em Disco

- **Por dia:** ~200 MB
- **Por mês:** ~6 GB
- **Por ano:** ~73 GB

## Solução Rápida de Problemas

### "Scheduler não inicia"

```bash
# Limpar PID obsoleto
rm -f scheduler.pid

# Tentar novamente
./run_scheduler.sh --now
```

### "Erro de importação (module not found)"

```bash
# Verificar que está usando venv correto
source .venv/bin/activate
which python
# Deve mostrar: /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector/.venv/bin/python
```

### "Rate limit (429)"

O scheduler já implementa retry automático. Se persistir, aguardar alguns minutos e tentar novamente.

### "Database is locked"

```bash
# Parar scheduler
./run_scheduler.sh --stop

# Aguardar 10 segundos
sleep 10

# Iniciar novamente
./run_scheduler.sh --now
```

## Próximos Passos

Após primeira execução bem-sucedida:

1. **Configurar systemd** (para execução permanente)
   - Ver `SCHEDULER_README.md` seção "Integração com Systemd"

2. **Configurar monitoramento** (para receber alertas de falhas)
   - Integrar com Grafana, Prometheus ou similar
   - Configurar emails de alerta

3. **Otimizar tribunais** (ajustar lista conforme necessidade)
   - Editar `TRIBUNAIS_PRIORITARIOS` em `scheduler.py`

---

**Dúvidas?** Ver documentação completa em `SCHEDULER_README.md`
