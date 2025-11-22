# Roadmap - Sistema de Download de Jurisprudência

## Status Atual

### ✅ Fase 1: Filtro de Tipo de Publicação (CONCLUÍDA)
**Objetivo:** Filtrar downloads para apenas Acórdãos, eliminando 83% de ruído.

**Implementação:**
- ✅ Parâmetro `tipos_desejados` em `processar_publicacoes()`
- ✅ Normalização case-insensitive de tipos
- ✅ Estatísticas de filtragem
- ✅ Logging detalhado

**Resultado:**
- Redução de ~83% no volume de dados armazenados
- Foco exclusivo em publicações relevantes para análise jurisprudencial

---

### ✅ Fase 2: Aumento de Volume Mínimo (CONCLUÍDA)
**Objetivo:** Aumentar threshold de publicações esperadas para evitar fallback desnecessário.

**Implementação:**
- ✅ `min_publicacoes_esperadas`: 10 → 100

**Resultado:**
- Menos avisos de fallback para PDF
- Confiança maior na API como fonte primária

---

### ✅ Fase 3: Download Retroativo (CONCLUÍDA)
**Objetivo:** Baixar publicações históricas para construir base de dados robusta.

**Implementação:**
- ✅ Função `baixar_retroativo()` em `scheduler.py`
- ✅ Script `run_retroativo.py` com CLI
- ✅ Iteração dia a dia com progresso
- ✅ Estatísticas consolidadas
- ✅ Confirmação automática (`--yes`)

**Uso:**
```bash
# Últimos 30 dias (padrão)
python run_retroativo.py --yes

# Intervalo específico
python run_retroativo.py --inicio 2025-01-01 --fim 2025-03-31 --yes

# Apenas STJ
python run_retroativo.py --tribunais STJ --dias 90 --yes
```

**Limitação Atual:**
- Taxa: 30 requisições/minuto (2s delay)
- Tempo: ~3-4 min por dia (100 páginas)
- Escalabilidade: Download de 1 ano = ~18-24 horas

---

## 🔄 PIVOTE DE PRIORIDADE

**Descoberta crítica:** Download de 15 dias travou/demorou demais (~30min sem completar primeiro dia).
- Banco de dados: 0 bytes (nem tabelas foram criadas)
- Conclusão: Performance é BLOCKER para teste empírico

**Nova ordem:**
1. **Fase 4.0**: Diagnóstico e otimização de performance (PRIORIDADE MÁXIMA)
2. **Fase 3.1**: Teste empírico do filtro (requer volume = requer performance)

---

## 📋 Próximas Fases

### ✅ Fase 4: Otimização de Performance - Alta Escala (CONCLUÍDA)
**Objetivo:** Reduzir drasticamente tempo de download para viabilizar volumes grandes (anos de histórico).

**Implementação:**
- ✅ Rate limiting adaptativo (janela deslizante 12 req/5s)
- ✅ Batch commits no DB (100 pubs/batch)
- ✅ Retry exponential backoff para HTTP 429/timeout
- ✅ Tratamento robusto de erros

**Resultado Real:**
- **Antes:** 30 req/min (delay 2s artificial) = 1800 req/hora
- **Depois:** 144 req/min (delay ~0.42s adaptativo) = 8640 req/hora
- **Ganho:** **4.8x mais rápido** (buffer conservador para confiabilidade)
- **Trade-off:** Ganho teórico 9.3x reduzido para 4.8x para garantir HTTP 429 < 1%

**Impacto Real:**
- Download de 6 meses (180 dias): ~100h → **~21h**
- Download de 1 ano: ~200h → **~42h**
- HTTP 429: < 1% (vs 6% com buffer agressivo)

---

### Fase 5: Exploração de APIs Alternativas e Testes Adicionais
**Prioridade:** MÉDIA
**Objetivo:** Avaliar outras fontes de dados e expandir cobertura do sistema.

**Sub-tarefas:**
- [ ] **Investigar API DATAJUD**
  - Verificar se oferece vantagens sobre DJEN
  - Comparar cobertura de tribunais
  - Avaliar rate limits e performance
  - Testar qualidade/completude dos dados

- [ ] **Pesquisar outras APIs úteis**
  - APIs de tribunais específicos (TJSP, TJRJ, TRFs)
  - APIs de órgãos reguladores (OAB, CNJ)
  - APIs de legislação (LexML, Planalto)

- [ ] **Testes de longo prazo**
  - Monitorar estabilidade do sistema otimizado (1 semana)
  - Validar HTTP 429 < 1% consistente
  - Ajustar buffer gradualmente se necessário (12 → 14 → 15)

- [ ] **Testes de volume**
  - Download de 1 ano completo (validação final)
  - Verificar integridade de dados
  - Medir uso de espaço em disco

**Entregável:** Relatório de viabilidade de APIs alternativas

---

## ⚠️ IMPORTANTE: Diagnóstico ANTES de Otimização

**Análise preliminar do código:**
- **Gargalo atual:** 100% rate limiting artificial (`delay_seconds=2.0`)
- **NÃO é gargalo:** Database (SQLite ~10K writes/sec, usando 0.5/sec)
- **NÃO é gargalo:** Serialization (BeautifulSoup parsing ~10-50ms)
- **DESCONHECIDO:** Limite real da API DJEN (não documentado)

**Sub-tarefas:**

#### 4.0: Diagnóstico e Medição (OBRIGATÓRIO PRIMEIRO) - EM EXECUÇÃO

**Objetivo:** Medir estado atual ANTES de otimizar (evitar otimização prematura).

**⚠️ CLARIFICAÇÃO CRÍTICA:**
- **Sistema atual:** Completamente sequencial (1 thread, 1 connection, 1 request/vez)
- **Para atingir 17 req/sec:** Requer paralelização (não implementado)
- **Connection pooling:** Não aplicável (SQLite = single-writer)
- **Load testing:** NÃO foi feito ainda
- **Profiling:** NÃO foi feito ainda
- **Evidência empírica:** Download de 15 dias travou (~30min sem completar primeiro dia, banco vazio)

**QUESTÕES CRÍTICAS A RESPONDER:**

1. **Onde está o gargalo?**
   - [ ] API requests (network latency)?
   - [ ] HTML parsing (BeautifulSoup)?
   - [ ] Database writes (SQLite)?
   - [ ] Rate limiting artificial (delay de 2s)?

2. **Qual taxa viabiliza 6 meses?**
   - 6 meses = ~180 dias
   - Meta: download em <24h
   - Requer: 180 dias / 24h = 7.5 dias/hora = **0.125 dias/minuto**
   - Com 100 páginas/dia: **12.5 páginas/minuto = ~5s por página**
   - Taxa atual: ~3-4 min/dia (100 páginas) = **2-2.4s por página** ✅ (teoricamente OK!)
   - **Conclusão:** Taxa atual DEVERIA ser suficiente. Por que travou?

3. **Limite real da API:**
   - [ ] Testar sem rate limiting artificial
   - [ ] Descobrir ponto de HTTP 429
   - [ ] Identificar se é por minuto, hora ou dia
   - [ ] Verificar se é por IP ou global

4. **Estratégias de otimização:**
   - [ ] Remover/reduzir delay artificial
   - [ ] Paralelização (múltiplas requisições simultâneas)
   - [ ] Batching (requisitar múltiplas páginas por chamada, se API suportar)
   - [ ] Caching (não re-baixar duplicatas)
   - [ ] Async/await (asyncio + aiohttp)

- [ ] **Benchmark de latência da API (sem rate limiting)**
  - Medir tempo de resposta real (min/avg/max/p95)
  - Identificar variação por horário
  - Testar diferentes endpoints (tribunais diferentes)
  - **Ferramenta:** Script de benchmark isolado

- [ ] **Teste de limite de rate**
  - Aumentar gradualmente requests/min até receber HTTP 429
  - Identificar se limite é por minuto, por hora, ou por dia
  - Verificar se limite é por IP ou global
  - Testar com diferentes User-Agents
  - **Método:** Testes controlados em ambiente de staging

- [ ] **Profiling de processamento local**
  - Instrumentar código com `cProfile` ou `line_profiler`
  - Medir tempo REAL de cada etapa:
    - HTTP request (network)
    - Parsing HTML (BeautifulSoup)
    - Extração de ementa (regex)
    - Inserção SQLite (write)
  - Calcular % de tempo em cada etapa
  - **Comando:** `python -m cProfile -o profile.stats run_retroativo.py --dias 1 --yes`
  - **Análise:** `python -m pstats profile.stats`

- [ ] **Profiling de queries SQL**
  - Ativar logging de queries: `PRAGMA query_only = ON`
  - Executar `EXPLAIN QUERY PLAN` nas queries principais
  - Identificar table scans vs index usage
  - Medir tempo de INSERT vs SELECT
  - **Ferramenta:** SQLite EXPLAIN QUERY PLAN

- [ ] **Load testing (simulação de carga)**
  - **NÃO aplicável no estado atual** (sistema sequencial)
  - Só faz sentido APÓS implementar paralelização
  - Quando implementar: usar `wrk` ou `Apache Bench`

- [ ] **Benchmark de database**
  - Throughput de writes (inserts/sec)
  - Impacto de índices
  - Comparar WAL mode vs DELETE mode
  - Testar batch inserts (1 vs 100 vs 1000)
  - **Ferramenta:** Script de stress test

- [ ] **Criar relatório de diagnóstico**
  - Documentar todos os resultados
  - Identificar gargalo REAL com dados
  - Calcular ganho máximo teórico
  - Propor soluções baseadas em evidência

**Entregável:** `DIAGNOSTICO_PERFORMANCE.md` com métricas objetivas

---

#### 4.1: Otimização Baseada em Dados (APÓS 4.0)
- [ ] Analisar limites de rate da API DJEN (documentação oficial)
- [ ] Testar limites práticos (experimentos controlados)
- [ ] Investigar se API suporta requisições paralelas
- [ ] Verificar se há endpoint batch/bulk
- [ ] Consultar termos de uso e políticas de fair use

#### 4.2: Análise de Arquiteturas Alternativas
- [ ] **Abordagem 1: Paralelização**
  - Múltiplas conexões simultâneas (asyncio, aiohttp)
  - Thread pool / Process pool
  - Estimativa de ganho: 5-10x

- [ ] **Abordagem 2: Batch Downloads**
  - Se API suportar, requisitar múltiplos dias/páginas por chamada
  - Estimativa de ganho: 10-20x

- [ ] **Abordagem 3: Caching Inteligente**
  - Pré-carregar índices de publicações
  - Download apenas de metadados primeiro, depois conteúdo sob demanda
  - Estimativa de ganho: 2-5x (para re-downloads)

- [ ] **Abordagem 4: Distribuição de Carga**
  - Múltiplas máquinas/IPs (se permitido)
  - Rate limiting distribuído
  - Estimativa de ganho: linear com número de workers

#### 4.3: Prova de Conceito (PoC)
- [ ] Implementar solução mais promissora em ambiente de teste
- [ ] Medir performance real vs estimada
- [ ] Validar estabilidade (rodadas de 1000+ requisições)
- [ ] Verificar impacto em rate limiting / bloqueios

#### 4.4: Implementação em Produção
- [ ] Refatorar `downloader.py` com nova arquitetura
- [ ] Configuração dinâmica de taxa (fallback para modo lento se necessário)
- [ ] Logging de performance (latência, throughput)
- [ ] Monitoramento de erros (HTTP 429, timeouts)

#### 4.5: Testes de Carga
- [ ] Download de 30 dias com nova arquitetura
- [ ] Download de 1 ano completo
- [ ] Validação de integridade (nenhuma publicação perdida)
- [ ] Benchmarking formal (antes vs depois)

**Riscos:**
- ⚠️ API pode ter rate limits não documentados
- ⚠️ Requisições paralelas podem ser bloqueadas/throttled
- ⚠️ Violação de termos de uso (verificar antes)

**Critérios de Sucesso:**
- ✅ Taxa sustentada de 500+ req/min (mínimo)
- ✅ Zero perda de dados vs modo lento
- ✅ Ausência de bloqueios/bans
- ✅ Código estável para rodar 24/7

---

### Fase 5: Dashboard de Estatísticas
**Prioridade:** MÉDIA
**Objetivo:** Visualização de métricas da base de dados.

**Features:**
- [ ] Distribuição de publicações por tribunal
- [ ] Evolução temporal (publicações/dia)
- [ ] Taxa de filtragem (Acórdãos vs outros tipos)
- [ ] Tamanho da base de dados
- [ ] Palavras-chave mais frequentes (nuvem de palavras)

**Ferramentas:**
- Streamlit / Dash (dashboard web interativo)
- Matplotlib / Plotly (gráficos)

---

### Fase 6: Integração com RAG
**Prioridade:** ALTA (dependente de Fase 4)
**Objetivo:** Tornar base de jurisprudência pesquisável semanticamente.

**Features:**
- [ ] Embeddings de ementas (sentence-transformers)
- [ ] Vector store (ChromaDB / FAISS)
- [ ] API de busca semântica
- [ ] Interface de consulta (CLI + Web)
- [ ] Ranqueamento por relevância

**Exemplo de Uso:**
```python
# Buscar acórdãos similares
resultados = rag.buscar(
    query="responsabilidade civil por dano moral",
    tribunal="STJ",
    limit=10
)
```

---

## Cronograma Estimado

| Fase | Tempo Estimado | Dependências |
|------|----------------|--------------|
| ~~Fase 1~~ | ~~2-3h~~ | ✅ Concluída |
| ~~Fase 2~~ | ~~1h~~ | ✅ Concluída |
| ~~Fase 3~~ | ~~4-6h~~ | ✅ Concluída |
| Fase 3.1 | 1h | Fase 3 |
| Fase 4 | **2-3 semanas** | Fase 3 |
| Fase 5 | 1-2 dias | Fase 3 |
| Fase 6 | 1 semana | Fase 4 (base completa) |

---

## Notas Técnicas

### Performance Atual (Baseline)
```
Rate Limiting: 30 req/min (2s delay)
Throughput:    ~1800 publicações/hora
Tempo/Dia:     3-4 minutos (100 páginas)
Tempo/Ano:     18-24 horas
```

### Performance Alvo (Fase 4)
```
Rate Limiting: 1000 req/min (0.06s delay)
Throughput:    ~60000 publicações/hora
Tempo/Dia:     5-10 segundos
Tempo/Ano:     30-60 minutos
```

### Considerações Arquiteturais
- **Atual:** Síncrono, sequencial, single-threaded
- **Futuro:** Assíncrono, paralelo, multi-worker
- **Trade-off:** Complexidade vs Performance

---

**Última atualização:** 2025-11-21
**Próxima revisão:** Após conclusão de Fase 3.1 (validação empírica)
