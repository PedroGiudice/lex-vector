# Known Issues - API DJEN (CNJ)

**Propósito:** Documentar particularidades, armadilhas e erros conhecidos da API DJEN para evitar repetição de erros em desenvolvimento futuro.

**Última atualização:** 2025-11-22

---

## ⚠️ CRITICAL - Leia antes de modificar código de API

Este documento contém **lições aprendidas** de erros reais cometidos durante desenvolvimento. **Sempre consulte este arquivo** antes de escrever código que interage com a API DJEN.

---

## 1. Paginação Automática - NÃO use `offset`

### ❌ **ERRO COMUM:**
```python
# ❌ ERRADO - offset não existe!
publicacoes = downloader.baixar_api(
    tribunal='STJ',
    data='2025-11-20',
    limit=100,
    offset=200  # TypeError: unexpected keyword argument 'offset'
)
```

### ✅ **CORRETO:**
```python
# ✅ CORRETO - paginação automática com max_pages
publicacoes = downloader.baixar_api(
    tribunal='STJ',
    data='2025-11-20',
    limit=100,
    max_pages=1  # Limita a 1 página (opcional)
)
```

### 📝 **Explicação:**
- O método `baixar_api()` já faz paginação automática internamente
- Itera `page=1, 2, 3...` na URL até não haver mais resultados
- **NÃO aceita** parâmetro `offset` (estilo SQL)
- Use `max_pages` para limitar quantas páginas baixar

### 🔍 **Assinatura correta:**
```python
def baixar_api(
    self,
    tribunal: str,
    data: str,
    limit: int = 100,
    max_pages: Optional[int] = None
) -> List[PublicacaoRaw]
```

**Fonte:** `src/downloader.py:209-215`

---

## 2. Rate Limiting - Janela Deslizante (21 req/janela)

### ⚠️ **LIMITE REAL DA API:**
- **21 requisições** por janela de ~5 segundos
- HTTP 429 após exceder
- Header `Retry-After: 2` indica tempo de espera

### ❌ **ERRO COMUM:**
```python
# ❌ ERRADO - Delay fixo não respeita janela
time.sleep(2)  # Simplista, não funciona em alta taxa
```

### ✅ **CORRETO:**
```python
# ✅ CORRETO - Rate limiting adaptativo (implementado)
downloader = DJENDownloader(
    data_root=DATA_ROOT,
    requests_per_minute=144,  # Taxa sustentável
    adaptive_rate_limit=True  # Janela deslizante automática
)
```

### 📝 **Explicação:**
- API usa **janela deslizante**, não contador fixo
- 21 requests em 5s → HTTP 429
- Sistema atual usa buffer conservador (12 req/5s) para confiabilidade
- Retry automático com `Retry-After` header

**Fonte:** `diagnostico_performance.py:196-207`, `src/downloader.py:_check_rate_limit()`

---

## 3. Database - Problema N+1 com Commits

### ❌ **ERRO COMUM:**
```python
# ❌ ERRADO - Commit em cada INSERT (535x mais lento!)
for pub in publicacoes:
    inserir_publicacao(conn, pub)
    conn.commit()  # N+1 commits = MUITO LENTO
```

### ✅ **CORRETO:**
```python
# ✅ CORRETO - Batch commits (implementado)
BATCH_SIZE = 100
for i, pub in enumerate(publicacoes, start=1):
    inserir_publicacao(conn, pub)

    if i % BATCH_SIZE == 0:
        conn.commit()  # Commit a cada 100

conn.commit()  # Commit final
```

### 📝 **Explicação:**
- SQLite é single-writer, cada commit faz fsync no disco
- Commit individual: 117 writes/sec
- Batch commits (100): 62,894 writes/sec (**535x speedup**)

**Fonte:** `diagnostico_performance.py:64-79`, `scheduler.py:processar_publicacoes()`

---

## 4. Deduplicação - Hash SHA256 (não ID da API)

### ⚠️ **IMPORTANTE:**
API pode retornar mesma publicação com IDs diferentes em requests subsequentes.

### ❌ **ERRO COMUM:**
```python
# ❌ ERRADO - ID da API não garante unicidade
pub_id = item['id']  # Pode mudar entre requests
```

### ✅ **CORRETO:**
```python
# ✅ CORRETO - Hash do conteúdo (implementado)
import hashlib
hash_conteudo = hashlib.sha256(texto_html.encode()).hexdigest()
```

### 📝 **Explicação:**
- Hash do `texto_html` garante unicidade real
- Detecta republicações (mesmo conteúdo, ID diferente)
- Índice UNIQUE no DB: `CREATE UNIQUE INDEX idx_hash ON publicacoes(hash_conteudo)`

**Fonte:** `src/downloader.py:_gerar_hash()`, `scheduler.py:inicializar_banco()`

---

## 5. Timeout e Retry - Exponential Backoff

### ❌ **ERRO COMUM:**
```python
# ❌ ERRADO - Retry fixo sem backoff
for i in range(3):
    try:
        response = requests.get(url, timeout=5)
        break
    except Timeout:
        pass  # Retry imediato = pior
```

### ✅ **CORRETO:**
```python
# ✅ CORRETO - Exponential backoff (implementado)
for attempt in range(max_retries):
    try:
        response = requests.get(url, timeout=30)

        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 2))
            time.sleep(retry_after)
            continue

        return response

    except Timeout:
        backoff = 2 ** attempt  # 1s, 2s, 4s
        time.sleep(backoff)
```

### 📝 **Explicação:**
- Timeout curto (5s) causa falhas desnecessárias
- Retry imediato sobrecarrega API
- Exponential backoff: 1s → 2s → 4s
- HTTP 429: usar `Retry-After` header

**Fonte:** `src/downloader.py:_fazer_requisicao()`

---

## 6. Filtro de Tipo - Case-Insensitive e Sem Acentos

### ⚠️ **IMPORTANTE:**
API retorna `tipo_publicacao` com variações:
- `"Acórdão"`, `"ACÓRDÃO"`, `"  Acórdão\n"`
- Comparação direta falha!

### ❌ **ERRO COMUM:**
```python
# ❌ ERRADO - Case-sensitive e com acentos
if pub['tipo_publicacao'] == 'Acórdão':  # Falha com 'ACÓRDÃO'
```

### ✅ **CORRETO:**
```python
# ✅ CORRETO - Normalização (implementado)
import unicodedata

def normalizar_tipo_publicacao(tipo: str) -> str:
    if not tipo:
        return ""
    # Remove acentos
    sem_acentos = unicodedata.normalize('NFD', tipo)
    sem_acentos = ''.join(c for c in sem_acentos if unicodedata.category(c) != 'Mn')
    return sem_acentos.lower().strip()

# Comparação:
if normalizar_tipo_publicacao(pub['tipo_publicacao']) == 'acordao':
```

### 📝 **Explicação:**
- Normaliza: remove acentos, lowercase, trim
- `'Acórdão'` → `'acordao'`
- `'ACÓRDÃO  '` → `'acordao'`
- Comparação robusta

**Fonte:** `scheduler.py:normalizar_tipo_publicacao()`, `scheduler.py:processar_publicacoes()`

---

## 7. Payload Size - NÃO é Gargalo (<100KB)

### ✅ **VALIDADO:**
- Payload médio: ~50-100KB por request
- JSON serialization: **não é gargalo** (confirmado por profiling)
- Parsing HTML: ~10ms (5% do tempo total)

### 📝 **Conclusão:**
- **NÃO otimize** JSON parsing/serialization (ganho marginal)
- **Foco:** Rate limiting e batch commits (ganhos 10x e 500x)

**Fonte:** `diagnostico_performance.py:48-61`, `PROFILING-DETALHADO-V2.txt:98-100`

---

## 8. Connection Pooling - NÃO é Necessário

### ⚠️ **IMPORTANTE:**
SQLite é **single-writer**, connection pooling não ajuda.

### ❌ **ERRO COMUM:**
```python
# ❌ DESNECESSÁRIO - SQLite single-writer
from sqlalchemy import create_engine
engine = create_engine('sqlite:///db.sqlite', pool_size=10)
```

### ✅ **CORRETO:**
```python
# ✅ CORRETO - Conexão única (implementado)
import sqlite3
conn = sqlite3.connect('publicacoes.db')
# Uma conexão por processo é suficiente
```

### 📝 **Explicação:**
- SQLite permite apenas 1 escritor simultâneo
- Connection pool não melhora throughput
- Batch commits sim (535x speedup)

**Fonte:** Análise de diagnóstico, CLAUDE.md

---

## 9. Dados de Teste - Usar Datas Recentes

### ⚠️ **IMPORTANTE:**
Datas antigas (>30 dias) frequentemente retornam 0 publicações.

### ❌ **ERRO COMUM:**
```python
# ❌ ERRADO - Testa com datas antigas vazias
data_teste = '2024-01-01'  # Provavelmente vazio
```

### ✅ **CORRETO:**
```python
# ✅ CORRETO - Testa com dados recentes
from datetime import datetime, timedelta
data_teste = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
```

### 📝 **Explicação:**
- API retém dados recentes com mais consistência
- Testes com datas >30 dias podem retornar vazio (não erro)
- Para profiling: variar últimos 20 dias

**Fonte:** `profile_detalhado.py:70-71`, `PROFILING-DETALHADO-V2.txt:55-74`

---

## 10. Logging - Debug vs Info vs Warning

### ✅ **PADRÃO ATUAL:**

```python
# DEBUG - Detalhes técnicos (batch commits, rate limit)
logger.debug(f"Batch commit: {i}/100 processadas")

# INFO - Eventos importantes (início download, conclusão)
logger.info(f"[STJ] Baixando publicações via API - 2025-11-20")

# WARNING - Situações anormais não críticas (HTTP 429, timeout)
logger.warning(f"HTTP 429 - Aguardando 2s antes de retry")

# ERROR - Falhas críticas (timeout após retries)
logger.error(f"Timeout após 3 tentativas")
```

### 📝 **Orientação:**
- **DEBUG:** Usado para troubleshooting, desabilitado em produção
- **INFO:** Progresso normal, sempre visível
- **WARNING:** Algo inesperado mas recuperável
- **ERROR:** Falha crítica, requer atenção

**Fonte:** `scheduler.py`, `src/downloader.py`

---

## 11. Headers HTTP - Mínimos São Mais Rápidos ⚡

### ✅ **DESCOBERTA (2025-11-22):**
Headers mínimos resultam em **7% menos latência** (269ms vs 288ms default).

### ❌ **ERRO COMUM:**
```python
# ❌ DESNECESSÁRIO - Headers verbosos aumentam latência
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0...) Chrome/120...',
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8'
}
```

### ✅ **CORRETO:**
```python
# ✅ CORRETO - Headers mínimos (mais rápido)
headers = {
    'Accept': 'application/json'
}
# Resultado: 269ms avg (vs 288ms default)
```

### 📝 **Explicação:**
- Teste de 5 configurações (100 requisições)
- **Minimal** venceu: 269ms avg (min 236ms, max 299ms)
- Browser-like headers: 273-288ms avg
- Ganho: **7% speedup** apenas removendo headers desnecessários

**Fonte:** `tests/api/test_headers_impact.py`, `data/diagnostics/headers_impact.json`

---

## 12. Rate Limit Real - 198 req/min (não 144) 🚀

### ✅ **DESCOBERTA CRÍTICA (2025-11-22):**
Limite real da API = **20 req/window** → ~**198 req/min**

### ⚠️ **IMPORTANTE:**
Sistema atual usa **144 req/min**, mas pode subir para **180 req/min** com segurança.

### 📊 **Evidências:**
```
HTTP 429 recebido após 58 requisições em 17.6s
Taxa observada: 198 req/min
Header: X-RateLimit-Limit: 20 (req por janela)
Retry-After: 1s
```

### 💡 **Recomendação:**
```python
# Configuração ótima (margem de segurança 10%)
downloader = DJENDownloader(
    data_root=DATA_ROOT,
    requests_per_minute=180,  # Era 144 (pode subir!)
    adaptive_rate_limit=True,
    max_retries=3
)
```

### 📈 **Ganho Potencial:**
- Taxa atual: 144 req/min
- Taxa ótima: 180 req/min
- **Speedup: 1.25x** (25% mais rápido)

**Fonte:** `diagnostico_performance.py:290-330`, `DIAGNOSTICO_PERFORMANCE.md`

---

## 📚 REFERÊNCIAS RÁPIDAS

| Conceito | Arquivo | Linha |
|----------|---------|-------|
| Assinatura `baixar_api()` | `src/downloader.py` | 209-215 |
| Rate limiting adaptativo | `src/downloader.py` | `_check_rate_limit()` |
| Batch commits | `scheduler.py` | `processar_publicacoes()` |
| Normalização tipo | `scheduler.py` | `normalizar_tipo_publicacao()` |
| Hash deduplicação | `src/downloader.py` | `_gerar_hash()` |
| HTTP 429 handling | `src/downloader.py` | `_fazer_requisicao()` |

---

## 🔄 HISTÓRICO DE UPDATES

| Data | Issue | Descrição |
|------|-------|-----------|
| 2025-11-21 | #1 | Criação inicial - `offset` não existe |
| 2025-11-21 | #2 | Rate limiting janela deslizante |
| 2025-11-21 | #3 | Problema N+1 batch commits |
| 2025-11-21 | #4 | Normalização tipo case-insensitive |
| 2025-11-22 | #5 | Headers mínimos são 7% mais rápidos |
| 2025-11-22 | #6 | Rate limit real = 198 req/min (pode subir de 144→180) |

---

## ✅ CHECKLIST - Antes de Modificar Código de API

- [ ] Li este documento completo
- [ ] Verifiquei assinatura do método `baixar_api()`
- [ ] Não usei parâmetro `offset` (não existe!)
- [ ] Rate limiting adaptativo está habilitado
- [ ] Commits são em batch (não individual)
- [ ] Retry tem exponential backoff
- [ ] Filtros de tipo são normalizados
- [ ] Testes usam datas recentes (<30 dias)
- [ ] Logging usa níveis adequados

---

**Última revisão:** 2025-11-22
**Maintainer:** Development Team
**Contato:** Ver CLAUDE.md

---

**⚠️ IMPORTANTE:** Este documento deve ser atualizado sempre que novos issues/particularidades da API forem descobertos.
