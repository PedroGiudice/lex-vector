# 🚀 Como Usar o Sistema Otimizado

**Sistema:** jurisprudencia-collector v2.0 (otimizado)
**Performance:** 4.8x mais rápido que versão anterior

---

## 📋 Pré-requisitos

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector
source .venv/bin/activate
```

---

## 🎯 Uso Básico

### 1. Download Retroativo (Intervalo de Datas)

```python
from scheduler import baixar_retroativo

# Download de 1 dia, 1 tribunal
stats = baixar_retroativo(
    data_inicio='2025-11-19',
    data_fim='2025-11-19',
    tribunais=['STJ']
)

# Download de 1 semana, múltiplos tribunais
stats = baixar_retroativo(
    data_inicio='2025-11-14',
    data_fim='2025-11-21',
    tribunais=['STJ', 'TJSP', 'TRF3']
)

# Download de 6 meses, todos os tribunais prioritários
stats = baixar_retroativo(
    data_inicio='2025-05-21',
    data_fim='2025-11-21'
    # tribunais=None usa TRIBUNAIS_PRIORITARIOS (10 tribunais)
)
```

### 2. Download Diário (Scheduler)

```bash
# Execução única (hoje)
python scheduler.py --now

# Execução agendada (8:00 AM diariamente)
python scheduler.py
```

### 3. Filtragem por Tipo de Publicação

```python
# Apenas acórdãos (padrão)
stats = baixar_retroativo(
    data_inicio='2025-11-19',
    data_fim='2025-11-19',
    tipos_desejados=['Acórdão']
)

# Múltiplos tipos
stats = baixar_retroativo(
    data_inicio='2025-11-19',
    data_fim='2025-11-19',
    tipos_desejados=['Acórdão', 'Sentença', 'Decisão']
)

# ⚠️ ATENÇÃO: Lista vazia filtra TUDO (nenhuma publicação processada)
```

---

## ⚙️ Configurações Avançadas

### Rate Limiting Adaptativo

**Padrão:** 12 req/5s (144 req/min)

Para ajustar (em `src/downloader.py`):

```python
# Mais agressivo (risco de HTTP 429)
self.request_window_size = 15  # 180 req/min

# Mais conservador (menor risco)
self.request_window_size = 10  # 120 req/min
```

### Batch Size (Commits)

**Padrão:** 100 publicações por batch

Para ajustar (em `scheduler.py`):

```python
def processar_publicacoes(...):
    BATCH_SIZE = 500  # Batch maior (mais RAM, mais ganho)
    # ou
    BATCH_SIZE = 50   # Batch menor (menos RAM, menos ganho)
```

### Desabilitar Rate Adaptativo

```python
downloader = DJENDownloader(
    data_root=DATA_ROOT,
    requests_per_minute=30,
    adaptive_rate_limit=False,  # Usa RateLimiter antigo
    max_retries=3
)
```

---

## 📊 Monitoramento

### Logs

```bash
# Logs em tempo real
tail -f logs/scheduler.log

# Filtrar HTTP 429
grep "HTTP 429" logs/scheduler.log

# Filtrar batch commits
grep "Batch commit" logs/scheduler.log
```

### Estatísticas de Download

```python
stats = baixar_retroativo(...)

print(f"Publicações novas: {stats['total_novas']}")
print(f"Duplicadas: {stats['total_duplicadas']}")
print(f"Filtradas: {stats['total_filtrados']}")
print(f"Erros: {stats['total_erros']}")
print(f"Tempo total: {stats['tempo_total']}s")
```

---

## 🛠️ Troubleshooting

### Problema: Muitos HTTP 429

**Sintoma:** Logs mostram múltiplos `HTTP 429 (Rate Limit)`

**Solução:**
```python
# Reduzir request_window_size em src/downloader.py
self.request_window_size = 10  # vs 12 padrão
```

### Problema: Download muito lento

**Sintoma:** Throughput < 100 req/min

**Causas possíveis:**
1. Buffer muito conservador
2. API lenta (latência alta)
3. HTTP 429 frequentes

**Diagnóstico:**
```bash
# Verificar latência média
grep "Total de publicações" logs/scheduler.log

# Verificar HTTP 429
grep -c "HTTP 429" logs/scheduler.log
```

**Solução:**
```python
# Se HTTP 429 = 0%, aumentar buffer
self.request_window_size = 14  # vs 12 padrão
```

### Problema: Banco de dados corrompido

**Sintoma:** Erros de SQLite ao inserir publicações

**Diagnóstico:**
```python
import sqlite3
conn = sqlite3.connect('jurisprudencia.db')
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check;')
print(cursor.fetchone()[0])  # Esperado: 'ok'
```

**Solução:** Restaurar backup mais recente

---

## 📈 Estimativas de Tempo

| Período | Tribunais | Publicações* | Tempo estimado** |
|---------|-----------|--------------|------------------|
| 1 dia | 1 tribunal | ~1,000 | ~7 min |
| 1 semana | 1 tribunal | ~7,000 | ~50 min |
| 1 mês | 1 tribunal | ~30,000 | ~3.5 horas |
| 6 meses | 1 tribunal | ~180,000 | ~21 horas |
| 6 meses | 10 tribunais | ~1,800,000 | ~210 horas (~9 dias) |

\* Estimativa média (varia por tribunal e data)
\*\* Com rate limit conservador (144 req/min)

---

## 🚨 Limites e Restrições

### Limites da API DJEN
- **Rate limit:** ~21 req/5s (sistema usa 12 para segurança)
- **Timeout:** 30s por requisição
- **Paginação:** 100 itens por página (max)

### Limites do Sistema
- **Batch size:** 100 publicações (padrão)
- **Max retries:** 3 tentativas
- **Backoff max:** 4s (exponencial: 1s → 2s → 4s)

---

## 📚 Referências

- **Arquitetura:** `docs/ARQUITETURA_JURISPRUDENCIA.md`
- **API Testing:** `docs/API_TESTING_REPRODUCIBLE.md`
- **Code Review:** `CODE_REVIEW_OPTIMIZATION.md`
- **Relatório Final:** `RELATORIO_FINAL_OTIMIZACAO.md`
- **Resumo Executivo:** `RESUMO_EXECUTIVO.md`

---

## 💡 Dicas de Performance

1. **Use filtro de tipos:** Filtre apenas tipos necessários (ex: apenas 'Acórdão')
2. **Monitore HTTP 429:** Se > 1%, reduza `request_window_size`
3. **Ajuste batch size:** Se RAM disponível, teste com batch 500
4. **Execute em horário de baixa carga:** Madrugada (menor competição por rate limit)
5. **Use múltiplas instâncias:** Execute download de tribunais diferentes em paralelo (com rate limit total)

---

**Última atualização:** 2025-11-21
**Versão:** 2.0 (otimizado)
