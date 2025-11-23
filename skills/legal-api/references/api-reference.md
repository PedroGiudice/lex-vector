# DJEN API Reference

**Base URL:** `https://comunicaapi.pje.jus.br`
**Documentation:** https://comunicaapi.pje.jus.br/swagger
**Last Updated:** 2025-11-23

---

## Authentication

Currently, the API does not require authentication for public endpoints.

---

## Endpoints

### GET /api/v1/comunicacao

Search for legal publications with filters.

**URL:**
```
GET https://comunicaapi.pje.jus.br/api/v1/comunicacao
```

**Query Parameters:**

| Parameter | Type | Required | Description | Notes |
|-----------|------|----------|-------------|-------|
| `siglaTribunal` | string | No | Tribunal code (STJ, TJSP, etc) | |
| `dataInicio` | string | No | Start date (YYYY-MM-DD) | |
| `dataFim` | string | No | End date (YYYY-MM-DD) | |
| `numeroProcesso` | string | No | Case number | |
| `numeroOab` | string | No | OAB number | ⚠️ **DOES NOT WORK** - see Known Issues |
| `ufOab` | string | No | OAB state (SP, RJ, etc) | ⚠️ **DOES NOT WORK** - see Known Issues |
| `page` | integer | No | Page number (1-indexed) | Default: 1 |
| `limit` | integer | No | Results per page | Default: 100, Max: 100 |

**Example Request:**
```bash
curl -X GET "https://comunicaapi.pje.jus.br/api/v1/comunicacao?siglaTribunal=STJ&dataInicio=2025-11-01&dataFim=2025-11-30&page=1&limit=100"
```

**Example Response:**
```json
{
  "totalItems": 15432,
  "currentPage": 1,
  "totalPages": 155,
  "items": [
    {
      "id": "abc123",
      "siglaTribunal": "STJ",
      "numeroprocessocommascara": "0001234-56.2025.3.00.0000",
      "numero_processo": "00012345620253000000",
      "tipoComunicacao": "Acórdão",
      "nomeClasse": "HABEAS CORPUS",
      "nomeOrgao": "PRIMEIRA TURMA",
      "data_disponibilizacao": "2025-11-20",
      "texto": "<html><body><p>EMENTA: ...</p></body></html>",
      "advogados": [
        {
          "nome": "João Silva",
          "numeroOab": "129021",
          "ufOab": "SP"
        }
      ]
    }
  ]
}
```

---

### GET /api/v1/caderno/{tribunal}/{data}/{meio}/download

Download complete daily caderno (PDF).

**URL:**
```
GET https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/{meio}/download
```

**Path Parameters:**

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `tribunal` | string | Yes | Tribunal code | STF, STJ, TJSP |
| `data` | string | Yes | Publication date (YYYY-MM-DD) | 2025-11-20 |
| `meio` | string | Yes | Publication medium | E (Electronic) |

**Example Request:**
```bash
curl -o STJ_2025-11-20.pdf \
  "https://comunicaapi.pje.jus.br/api/v1/caderno/STJ/2025-11-20/E/download"
```

**Response:**
- Content-Type: `application/pdf`
- Binary PDF file

---

## Tribunal Codes

### Superior Courts (5)
- `STF` - Supremo Tribunal Federal
- `STJ` - Superior Tribunal de Justiça
- `TST` - Tribunal Superior do Trabalho
- `TSE` - Tribunal Superior Eleitoral
- `STM` - Superior Tribunal Militar

### State Courts (27)
- `TJSP` - São Paulo
- `TJRJ` - Rio de Janeiro
- `TJMG` - Minas Gerais
- `TJRS` - Rio Grande do Sul
- `TJPR` - Paraná
- `TJSC` - Santa Catarina
- `TJDF` - Distrito Federal
- `TJBA` - Bahia
- `TJCE` - Ceará
- `TJPE` - Pernambuco
- `TJES` - Espírito Santo
- `TJGO` - Goiás
- `TJPA` - Pará
- `TJPB` - Paraíba
- `TJPI` - Piauí
- `TJRN` - Rio Grande do Norte
- `TJSE` - Sergipe
- `TJTO` - Tocantins
- `TJAC` - Acre
- `TJAL` - Alagoas
- `TJAM` - Amazonas
- `TJAP` - Amapá
- `TJMA` - Maranhão
- `TJMS` - Mato Grosso do Sul
- `TJMT` - Mato Grosso
- `TJRO` - Rondônia
- `TJRR` - Roraima

### Federal Courts (6)
- `TRF1` - 1ª Região
- `TRF2` - 2ª Região
- `TRF3` - 3ª Região
- `TRF4` - 4ª Região
- `TRF5` - 5ª Região
- `TRF6` - 6ª Região

### Labor Courts (24)
- `TRT1` through `TRT24` - Regional Labor Courts

### Military Courts (3)
- `TJMSP` - São Paulo
- `TJMRS` - Rio Grande do Sul
- `TJMMG` - Minas Gerais

**Total:** 65 tribunals

---

## Rate Limiting

### Limits
- **21 requests per 5-second sliding window**
- Exceeding triggers HTTP 429

### Response Headers
```
HTTP/1.1 429 Too Many Requests
Retry-After: 2
```

### Recommended Strategy
```python
# Conservative sustainable rate: 144 req/min (12 req/5s)
# Provides safety buffer below 21 req/5s limit

import time
from collections import deque

class RateLimiter:
    def __init__(self, requests_per_window=12, window_seconds=5):
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.request_times = deque()

    def wait_if_needed(self):
        now = time.time()

        # Remove old requests outside window
        while self.request_times and now - self.request_times[0] > self.window_seconds:
            self.request_times.popleft()

        # If at limit, wait
        if len(self.request_times) >= self.requests_per_window:
            sleep_time = self.window_seconds - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.request_times.popleft()

        # Record this request
        self.request_times.append(time.time())
```

---

## Known Limitations

### ⚠️ CRITICAL Issues

1. **OAB Filter Does NOT Work**
   - Parameters `numeroOab` and `ufOab` are ignored
   - API returns ALL publications regardless of filter
   - Workaround: Download all and filter locally
   - See `known-issues.md` for details

2. **Rate Limiting**
   - Strict 21 req/5s limit
   - Use adaptive rate limiter
   - Monitor HTTP 429 responses

3. **Historical Data Retention**
   - Publications older than 90 days may be unavailable
   - Download and store locally for long-term access

4. **PDF Availability**
   - Cadernos usually available after 8:00 AM
   - May be delayed on some tribunals

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | - |
| 400 | Bad Request | Check parameters format |
| 404 | Not Found | Caderno not available for that date/tribunal |
| 429 | Too Many Requests | Wait and retry (use `Retry-After` header) |
| 500 | Internal Server Error | Retry after delay |
| 503 | Service Unavailable | API temporarily down, retry later |

---

## Best Practices

### 1. Pagination
```python
def baixar_todas_paginas(tribunal, data):
    all_items = []
    page = 1

    while True:
        response = requests.get(
            f"{BASE_URL}/api/v1/comunicacao",
            params={
                'siglaTribunal': tribunal,
                'dataInicio': data,
                'dataFim': data,
                'page': page,
                'limit': 100
            }
        )

        data = response.json()
        all_items.extend(data['items'])

        if page >= data['totalPages']:
            break

        page += 1

    return all_items
```

### 2. Error Handling
```python
import requests
from requests.exceptions import Timeout, ConnectionError

def fazer_requisicao_robusta(url, params, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2))
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            return response

        except Timeout:
            backoff = 2 ** attempt
            time.sleep(backoff)
        except ConnectionError:
            time.sleep(5)

    raise Exception(f"Failed after {max_retries} retries")
```

### 3. Caching
```python
import hashlib
import os

def get_cached_or_fetch(tribunal, data, cache_dir='cache'):
    cache_key = hashlib.md5(f"{tribunal}_{data}".encode()).hexdigest()
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)

    # Fetch from API
    data = baixar_publicacoes(tribunal, data)

    # Save to cache
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(data, f)

    return data
```

---

## Testing

### Test Endpoints

```bash
# Test connectivity
curl "https://comunicaapi.pje.jus.br/api/v1/comunicacao?limit=1"

# Test specific tribunal
curl "https://comunicaapi.pje.jus.br/api/v1/comunicacao?siglaTribunal=STJ&limit=1"

# Test date range (use recent dates!)
curl "https://comunicaapi.pje.jus.br/api/v1/comunicacao?siglaTribunal=STJ&dataInicio=2025-11-20&dataFim=2025-11-20&limit=10"
```

### Integration Tests

```python
import pytest
import requests

BASE_URL = "https://comunicaapi.pje.jus.br"

def test_api_connectivity():
    response = requests.get(f"{BASE_URL}/api/v1/comunicacao", params={'limit': 1})
    assert response.status_code == 200

def test_pagination():
    response = requests.get(
        f"{BASE_URL}/api/v1/comunicacao",
        params={'siglaTribunal': 'STJ', 'limit': 10}
    )
    data = response.json()
    assert 'totalPages' in data
    assert 'items' in data
    assert len(data['items']) <= 10

def test_tribunal_filter():
    response = requests.get(
        f"{BASE_URL}/api/v1/comunicacao",
        params={'siglaTribunal': 'STJ', 'limit': 5}
    )
    data = response.json()
    for item in data['items']:
        assert item['siglaTribunal'] == 'STJ'
```

---

## Support

For questions about the DJEN API:
- **Email:** sistemasnacionais@cnj.jus.br
- **Phone:** (61) 2326-5353
- **Documentation:** https://comunica.pje.jus.br

---

## Related Documentation

- `known-issues.md` - Complete list of API quirks and workarounds
- `schema.md` - Database schema for storing API data
- `architecture.md` - System architecture overview
