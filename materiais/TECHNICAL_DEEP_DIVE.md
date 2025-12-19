# Technical Deep Dive - Claude-Code-Projetos
## Análise Técnica Detalhada para One-Pager

---

## 1. ARQUITETURA DE SISTEMA

### Visão High-Level

```
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE INTERFACE                     │
│  (Orchestrator - Decision Making, Tool Calls, Memory)       │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌───────────────┐ ┌──────────┐ ┌─────────────────┐
│ Legal         │ │ Agentes  │ │ Comandos CLI    │
│ Workbench     │ │ Claude   │ │ (Standalone)    │
│ (Web App)     │ │          │ │                 │
└───────┬───────┘ └────┬─────┘ └────────┬────────┘
        │              │                 │
        ▼              ▼                 ▼
┌─────────────────────────────────────────────────┐
│          SHARED LIBRARY (Common Logic)          │
│  ├── utils/ (path, logger, config)             │
│  ├── scrapers/ (stj, stf, base)                │
│  └── parsers/ (ledes, pdf)                     │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Selenium │ │ SQLite   │ │ FileSystem│
│ (Chrome) │ │ (Data)   │ │ (Storage) │
└──────────┘ └──────────┘ └──────────┘
```

---

## 2. DECISÕES ARQUITETURAIS

### A. Flask vs FastAPI
**Decisão:** Flask 3.x
**Razão:** SSR com Jinja2, ecosystem maduro, setup simples
**Trade-off:** ✅ Rápido, ❌ Menos performante para async (não crítico)

### B. Selenium vs Requests
**Decisão:** Selenium WebDriver (headless Chrome)
**Razão:** Sites tribunais usam JavaScript pesado
**Trade-off:** ✅ Funciona em qualquer site, ❌ Mais lento

### C. SQLite vs PostgreSQL
**Decisão:** SQLite
**Razão:** Single-user, zero setup, portável
**Trade-off:** ✅ Simples, ❌ Sem concorrência write (não relevante)

### D. Monólito vs Microserviços
**Decisão:** Monólito modular com shared library
**Razão:** Time pequeno, funcionalidades relacionadas
**Trade-off:** ✅ Dev rápido, ❌ Escalabilidade limitada (não crítico inicialmente)

---

## 3. COMPONENTES TÉCNICOS

### A. Selenium Scraper

```python
class BaseScraper:
    def __init__(self, headless=True):
        self.driver = self._setup_driver(headless)

    def retry_on_failure(self, func, max_retries=3):
        for i in range(max_retries):
            try:
                return func()
            except Exception as e:
                time.sleep(2 ** i)  # Exponential backoff
        raise Exception("Max retries exceeded")
```

**Características:**
- Headless mode (mais rápido)
- Retry automático com backoff
- Logging detalhado
- Resource management

### B. LEDES Parser

```python
class LEDESParser:
    LEDES_COLUMNS = ["INVOICE_DATE", "HOURS", "RATE", ...]

    def parse_docx(self, docx_path):
        # Parse tables from DOCX
        # Validate LEDES 1998B format
        # Return structured entries

    def export_to_ledes(self, entries, output_path):
        # Format and write .ledes file
```

**Características:**
- Strict validation (100% conformidade)
- Flexible input (variações de DOCX)
- Error reporting detalhado

### C. Path Utils

```python
def get_project_root():
    return Path(__file__).parent.parent.parent

def get_data_dir(project_name):
    data_dir = get_project_root() / project_name / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
```

**Vantagens:**
- Zero hardcoding
- Cross-platform (WSL, Linux, macOS)
- Auto-cria diretórios

---

## 4. SEGURANÇA

### Autenticação
- **Flask-Login**: Gestão de sessões
- **Werkzeug**: Hashing PBKDF2
- **CSRF Protection**: Flask-WTF tokens

### Input Validation
- **WTForms**: Validators (Length, Regexp)
- **File uploads**: Whitelist de extensões
- **SQL**: SQLAlchemy ORM (previne injection)

### Logging Seguro
- ❌ NUNCA logar senhas/tokens
- ✅ Apenas IDs, timestamps, status
- ✅ Rotação de logs

---

## 5. PERFORMANCE

### Bottlenecks Identificados

| Bottleneck | Causa | Mitigação |
|------------|-------|-----------|
| Selenium startup | 3-5s/Chrome | Reutilizar driver |
| PDF downloads | Bandwidth tribunal | Async threads |
| SQLite writes | Lock em concorrência | Batch inserts |

### Otimizações

1. **Caching de ChromeDriver** (driver pool)
2. **Batch Processing** (bulk_insert)
3. **Lazy Loading** (generators para logs)

---

## 6. TESTING STRATEGY

```
tests/
├── unit/           # Parsers, utils (alta cobertura)
├── integration/    # Scrapers (mock Selenium)
└── e2e/            # Fluxos críticos (login → export)
```

**Ferramentas:** pytest, pytest-cov, selenium-mock

---

## 7. DEPLOYMENT

### Dev (Atual)
- WSL2 Ubuntu 22.04
- ChromeDriver local
- Python 3.11 + venv

### Produção (Planejado)

**Opção 1: Oracle Cloud**
```bash
# bootstrap-oracle-cloud.sh
# nginx + gunicorn + systemd
```

**Opção 2: Docker Compose**
```yaml
services:
  web:
    build: .
    ports: ["5000:5000"]
  chrome:
    image: selenium/standalone-chrome
```

### CI/CD (Futuro)
```yaml
# GitHub Actions
- pytest --cov
- ruff check
- deploy to Oracle Cloud
```

---

## 8. OBSERVABILIDADE

### Logging

| Nível | Uso |
|-------|-----|
| DEBUG | Flow detalhado |
| INFO | Eventos normais |
| WARNING | Recuperáveis (retry OK) |
| ERROR | Requer atenção |
| CRITICAL | Sistema down |

**Destinos:** `~/.vibe-log/{app}.log`

### Metrics (Futuro)
- Processos/dia
- Taxa de sucesso scraping
- Tempo conversão LEDES
- Uptime

---

## 9. EXTENSIBILIDADE

### Adicionar Novo Tribunal

1. Criar `shared/scrapers/novo_tribunal.py`
2. Herdar de `BaseScraper`
3. Implementar `login()`, `search()`, `download()`
4. Criar route + template
5. **Tempo:** 2-3 dias

### Adicionar Novo Formato

1. Criar `shared/parsers/novo_formato.py`
2. Implementar `parse()` e `export()`
3. Adicionar validação
4. Criar route + testes
5. **Tempo:** 1-2 dias

---

## 10. LIÇÕES APRENDIDAS

| Erro | Correção |
|------|----------|
| Hardcoded paths | `path_utils` dinâmico |
| Secrets commitados | `.gitignore` + `.env.example` |
| Sem retry scraping | `retry_on_failure()` |
| Prints aleatórios | Logger centralizado |
| venv no Git | `.gitignore` absoluto |

---

## PONTOS FORTES

✅ Modularidade (shared library)
✅ Extensibilidade (fácil adicionar tribunais)
✅ Robustez (retry, logging)
✅ Simplicidade (monólito para time pequeno)
✅ Portabilidade (paths dinâmicos)

## DÉBITOS TÉCNICOS

❌ Testing: Cobertura inexistente
❌ Async: Scraping síncrono
❌ Caching: Sem cache de resultados
❌ Monitoring: Sem métricas real-time
❌ API: Sem REST para integrações

## PRÓXIMAS MELHORIAS

1. **Pytest + 80% coverage**
2. **Async scraping (aiohttp)**
3. **Redis cache**
4. **Prometheus metrics**
5. **REST API para B2B**
