# STJ Dados Abertos: Integras + Correcao CLI - Plano de Implementacao

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrar o dataset completo de integras do STJ (decisoes terminativas + acordaos) ao sistema existente, corrigir os comandos mortos da CLI, e garantir download incremental diario.

**Architecture:** Nova tabela `integras` separada da tabela `acordaos` existente. Novo downloader especializado para ZIPs+JSONs. Novo processor para HTML->texto. Correlacao via numero_processo extraido. CLI unificada com comandos funcionais para ambos os datasets.

**Tech Stack:** Python 3.12, DuckDB, httpx, typer, rich, zipfile, html (stdlib), tenacity

---

## Contexto Critico

### O que existe hoje
- Tabela `acordaos` com 29.160 espelhos (resumos com ~548 chars de texto_integral)
- 10 datasets CKAN de espelhos por orgao julgador
- CLI com 3 comandos de download MORTOS (usam funcoes deprecadas que retornam lista vazia)
- CKANClient funcional mas limitado a espelhos

### O que vamos adicionar
- Dataset de integras: `integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica`
  - 1.756 resources: 873 ZIPs (~8.1 GB) + 878 JSONs metadados (~1.1 GB) + 4 CSVs
  - Periodo: fev/2022 ate hoje (atualizado diariamente)
  - ZIPs contem: arquivos `{SeqDocumento}.txt` com texto completo em HTML (~15 KB media)
  - JSONs contem: lista de metadados (SeqDocumento, processo, ministro, dataPublicacao, etc.)
  - Tipos: DECISAO (~80%) + ACORDAO (~20%)
  - Correlacao ZIP<->JSON: SeqDocumento == nome do .txt (100% match comprovado)
  - Volume total: ~9.2 GB (TUDO que existe disponivel, desde fev/2022)

### Dados verificados empiricamente
- Volume OCI montado em `/mnt/juridico-data` com 185 GB livres
- Consolidados mensais: 202202, 202203, 202204, 202207 (cobrem meses SEM diarios)
- Diarios: 20220502 ate 20260122 (sem sobreposicao com consolidados)
- Campos JSON variam entre consolidados e diarios:
  - Consolidados: `seqDocumento` (minusculo), datas em epoch ms, campo `ministro`
  - Diarios recentes: `SeqDocumento` (maiusculo), datas em ISO, campo `NM_MINISTRO`
- Amostra verificada: metadados20260122.json (236 registros) vs textos20260122.zip (233 arquivos) = 100% match
- Texto medio: ~15 KB por decisao (HTML com `<br>` como separador de linha)

---

## Task 1: Estender config.py com dataset de integras

**Files:**
- Modify: `legal-workbench/ferramentas/stj-dados-abertos/config.py`
- Test: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_config.py`

**Step 1: Write failing test**

```python
# tests/test_config.py - adicionar

def test_integras_dataset_id_exists():
    from config import INTEGRAS_DATASET_ID
    assert INTEGRAS_DATASET_ID == "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"

def test_integras_dirs_exist():
    from config import INTEGRAS_DIR, INTEGRAS_STAGING_DIR, INTEGRAS_TEXTOS_DIR
    assert INTEGRAS_DIR is not None
    assert INTEGRAS_STAGING_DIR is not None
    assert INTEGRAS_TEXTOS_DIR is not None

def test_get_integras_dataset_id():
    from config import get_integras_dataset_id
    assert get_integras_dataset_id() == "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"
```

**Step 2: Run test to verify it fails**

```bash
cd legal-workbench/ferramentas/stj-dados-abertos
source .venv/bin/activate
pytest tests/test_config.py -v -k "integras"
```
Expected: FAIL (ImportError)

**Step 3: Implement in config.py**

Adicionar apos `CKAN_DATASETS` (linha ~79):

```python
# Dataset de Integras (decisoes terminativas + acordaos com texto completo)
INTEGRAS_DATASET_ID: Final[str] = "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"

def get_integras_dataset_id() -> str:
    """Get CKAN dataset ID for integras."""
    return INTEGRAS_DATASET_ID

# Diretorios de integras
INTEGRAS_DIR: Final[Path] = DATA_ROOT / "integras"
INTEGRAS_STAGING_DIR: Final[Path] = INTEGRAS_DIR / "staging"   # ZIPs e JSONs baixados
INTEGRAS_TEXTOS_DIR: Final[Path] = INTEGRAS_DIR / "textos"     # TXTs extraidos
INTEGRAS_METADATA_DIR: Final[Path] = INTEGRAS_DIR / "metadata"  # JSONs de metadados

# Controle de progresso
INTEGRAS_PROGRESS_FILE: Final[Path] = INTEGRAS_DIR / ".download_progress.json"

# Criar diretorios
for dir_path in [INTEGRAS_STAGING_DIR, INTEGRAS_TEXTOS_DIR, INTEGRAS_METADATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_config.py -v -k "integras"
```

**Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat(stj): add integras dataset config and directories"
```

---

## Task 2: Estender CKANClient para dataset de integras

**Files:**
- Modify: `legal-workbench/ferramentas/stj-dados-abertos/src/ckan_client.py`
- Test: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_ckan_client.py`

**Step 1: Write failing test**

```python
# tests/test_ckan_client.py - adicionar

def test_ckan_resource_extract_date_from_zip():
    """Testa extracao de data de nomes de ZIP (YYYYMMDD.zip e YYYYMM.zip)."""
    r1 = CKANResource(id="1", name="20260122.zip", url="", format="ZIP", created="")
    assert r1.extract_date() == "2026-01-22"

    r2 = CKANResource(id="2", name="202203.zip", url="", format="ZIP", created="")
    assert r2.extract_date_monthly() == "2022-03"

def test_get_integras_resources_paired():
    """Testa pareamento de ZIPs com JSONs de metadados."""
    ...
```

**Step 2: Run test - expected FAIL**

**Step 3: Implement**

Adicionar regex patterns para reconhecer ZIPs e metadados:
```python
ZIP_DATE_DAILY: Final[re.Pattern] = re.compile(r"^(\d{4})(\d{2})(\d{2})\.zip$")
ZIP_DATE_MONTHLY: Final[re.Pattern] = re.compile(r"^(\d{4})(\d{2})\.zip$")
METADADOS_DAILY: Final[re.Pattern] = re.compile(r"^metadados(\d{4})(\d{2})(\d{2})(?:\.json)?$")
METADADOS_MONTHLY: Final[re.Pattern] = re.compile(r"^metadados(\d{4})(\d{2})(?:\.json)?$")
```

Estender `CKANResource.extract_date()` para reconhecer todos os formatos.
Adicionar `extract_date_monthly()` para consolidados.

Adicionar ao `CKANClient`:
```python
def get_integras_package(self) -> CKANPackage:
    """Fetch package de integras (dataset unico, nao por orgao)."""
    url = f"{self._api_url('package_show')}?id={INTEGRAS_DATASET_ID}"
    ...

def get_integras_resource_pairs(self) -> list[tuple[CKANResource, CKANResource]]:
    """
    Retorna pares (zip_textos, json_metadados) ordenados por data.
    Cada par corresponde a um dia ou mes de publicacoes.
    Pareamento por data extraida do nome do resource.
    """
    ...

def get_integras_resources_by_date_range(
    self, start_date: str, end_date: str
) -> list[tuple[CKANResource, CKANResource]]:
    """Filtra pares por intervalo de datas."""
    ...
```

**Step 4: Run tests**

**Step 5: Commit**

```bash
git add src/ckan_client.py tests/test_ckan_client.py
git commit -m "feat(stj): extend CKANClient for integras dataset"
```

---

## Task 3: Criar IntegrasDownloader

**Files:**
- Create: `legal-workbench/ferramentas/stj-dados-abertos/src/integras_downloader.py`
- Test: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_integras_downloader.py`

**Step 1: Write failing tests**

```python
class TestDownloadProgress:
    def test_mark_completed(self, tmp_path): ...
    def test_is_completed(self, tmp_path): ...
    def test_persist_and_load(self, tmp_path): ...

class TestIntegrasDownloader:
    def test_download_zip(self, tmp_path): ...
    def test_download_metadados(self, tmp_path): ...
    def test_extract_zip(self, tmp_path): ...
    def test_download_pair(self, tmp_path): ...
    def test_progress_tracking(self, tmp_path): ...
    def test_resume_interrupted(self, tmp_path): ...
    def test_validate_zip_integrity(self, tmp_path): ...
```

**Step 2: Run - FAIL**

**Step 3: Implement**

```python
"""
Downloader especializado para dataset de integras do STJ.
Baixa pares de (ZIP textos + JSON metadados), extrai textos,
e persiste progresso para retomada de downloads interrompidos.
"""

class DownloadProgress:
    """Persiste progresso de download em JSON para retomada."""
    def __init__(self, progress_file: Path): ...
    def mark_completed(self, resource_name: str): ...
    def is_completed(self, resource_name: str) -> bool: ...
    def save(self): ...
    def load(self): ...

class IntegrasDownloader:
    def __init__(self, staging_dir, textos_dir, metadata_dir, progress_file): ...

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=5, max=60))
    def download_resource(self, url: str, dest: Path, force: bool = False) -> Path:
        """Download com stream=True para arquivos grandes e retry."""
        ...

    def extract_zip(self, zip_path: Path, dest_dir: Path) -> list[Path]:
        """Extrai textos de ZIP para subdiretorio por data."""
        ...

    def download_pair(self, zip_res, meta_res, force=False) -> tuple[list[Path], list[dict]]:
        """Baixa par (ZIP + JSON), extrai textos, carrega metadados."""
        ...

    def download_all(self, pairs, force=False) -> dict:
        """Download retroativo completo com progresso persistido."""
        ...

    def validate_zip_integrity(self, zip_path: Path) -> bool:
        """Verifica integridade do ZIP."""
        ...
```

**Detalhes criticos:**
- `stream=True` no httpx para ZIPs grandes (consolidados ~250 MB)
- Timeout: 120s para downloads grandes (vs 30s padrao)
- Progresso salvo a cada par completado (retomada granular)
- Extracao em subdiretorio por data: `textos/20260122/343876683.txt`
- SHA256 de cada ZIP baixado

**Step 4: Run tests**

**Step 5: Commit**

```bash
git add src/integras_downloader.py tests/test_integras_downloader.py
git commit -m "feat(stj): add IntegrasDownloader with progress tracking"
```

---

## Task 4: Criar IntegrasProcessor (HTML -> texto + normalizacao)

**Files:**
- Create: `legal-workbench/ferramentas/stj-dados-abertos/src/integras_processor.py`
- Test: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_integras_processor.py`

**Step 1: Write failing tests**

```python
class TestNormalizarMetadados:
    def test_normalizar_consolidado_mensal(self):
        """Consolidados: epoch ms, campo 'ministro', 'seqDocumento' minusculo."""
        raw = {
            "seqDocumento": 146211705,
            "dataPublicacao": 1646276400000,
            "tipoDocumento": "ACORDAO",
            "numeroRegistro": "202103353563",
            "processo": "AREsp 1996346    ",
            "dataRecebimento": 1634526000000,
            "dataDistribuicao": 1634785200000,
            "ministro": "LUIS FELIPE SALOMAO",
            "recurso": "AGRAVO INTERNO",
            "teor": "Concedendo",
            "descricaoMonocratica": None,
            "assuntos": "11806;11806"
        }
        result = normalizar_metadados(raw)
        assert result["seq_documento"] == 146211705
        assert result["data_publicacao"] == "2022-03-03"
        assert result["ministro"] == "LUIS FELIPE SALOMAO"
        assert result["numero_processo"] == "1996346"
        assert result["classe_processual"] == "AREsp"

    def test_normalizar_diario_recente(self):
        """Diarios: ISO dates, campo 'NM_MINISTRO', 'SeqDocumento' maiusculo."""
        raw = {
            "SeqDocumento": 353186704,
            "dataPublicacao": "2026-01-22",
            "tipoDocumento": "DECISAO",
            "numeroRegistro": "202400836220",
            "processo": "AREsp 2591846",
            "NM_MINISTRO": "PAULO SERGIO DOMINGUES",
            "teor": "Nao Conhecendo",
            "assuntos": "9992, 10433"
        }
        result = normalizar_metadados(raw)
        assert result["seq_documento"] == 353186704
        assert result["data_publicacao"] == "2026-01-22"
        assert result["ministro"] == "PAULO SERGIO DOMINGUES"
        assert result["numero_processo"] == "2591846"

class TestHtmlParaTexto:
    def test_converter_html_basico(self):
        html = "DECISAO<br>Trata-se de habeas corpus..."
        texto = html_para_texto(html)
        assert "<br>" not in texto
        assert "DECISAO" in texto

    def test_preservar_paragrafos(self):
        html = "Paragrafo 1<br><br>Paragrafo 2"
        texto = html_para_texto(html)
        assert "\n" in texto

class TestExtrairNumeroProcesso:
    def test_aresp(self):
        assert extrair_numero_processo("AREsp 2591846") == "2591846"
        assert extrair_classe_processual("AREsp 2591846") == "AREsp"

    def test_com_espacos(self):
        assert extrair_numero_processo("AREsp 1996346    ") == "1996346"

    def test_hc(self):
        assert extrair_numero_processo("HC 789012") == "789012"
```

**Step 2: Run - FAIL**

**Step 3: Implement**

```python
"""
Processador de integras do STJ.
Normaliza metadados (variacoes consolidados vs diarios),
converte HTML->texto, prepara registros para DuckDB.
"""

def normalizar_metadados(raw: dict) -> dict:
    """Normaliza campos variantes entre consolidados e diarios."""
    # SeqDocumento/seqDocumento -> seq_documento
    # ministro/NM_MINISTRO -> ministro
    # epoch ms -> ISO date (quando numerico)
    # processo -> numero_processo + classe_processual
    # assuntos (separador ; ou ,) -> string normalizada
    ...

def html_para_texto(html: str) -> str:
    """HTML -> texto limpo. Usa html.parser stdlib."""
    ...

def extrair_numero_processo(processo: str) -> str:
    """'AREsp 2591846' -> '2591846'"""
    ...

def extrair_classe_processual(processo: str) -> str:
    """'AREsp 2591846' -> 'AREsp'"""
    ...

def preparar_registro_integra(metadados: dict, texto_html: str) -> dict:
    """Combina metadados + texto em registro pronto para DuckDB."""
    ...

class IntegrasProcessor:
    """Processa lotes de integras."""
    def processar_batch(self, metadados: list[dict], textos_dir: Path) -> list[dict]:
        """Para cada metadado, encontra .txt, converte, prepara registro."""
        ...
```

**Step 4: Run tests**

**Step 5: Commit**

```bash
git add src/integras_processor.py tests/test_integras_processor.py
git commit -m "feat(stj): add IntegrasProcessor with HTML-to-text and field normalization"
```

---

## Task 5: Estender database.py com tabela `integras`

**Files:**
- Modify: `legal-workbench/ferramentas/stj-dados-abertos/src/database.py`
- Test: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_database.py`

**Step 1: Write failing tests**

```python
class TestIntegrasSchema:
    def test_criar_tabela_integras(self):
        """Tabela integras existe com colunas corretas."""
        ...

class TestIntegrasInsert:
    def test_inserir_integra(self): ...
    def test_deduplicar_por_seq_documento(self): ...

class TestIntegrasSearch:
    def test_buscar_texto_completo_fts(self): ...

class TestCorrelacao:
    def test_buscar_por_processo_unificado(self): ...
```

**Step 2: Run - FAIL**

**Step 3: Implement**

Adicionar ao `criar_schema()`:

```sql
CREATE TABLE IF NOT EXISTS integras (
    seq_documento BIGINT PRIMARY KEY,
    numero_processo VARCHAR NOT NULL,
    classe_processual VARCHAR,
    numero_registro VARCHAR,
    hash_conteudo VARCHAR UNIQUE NOT NULL,
    tipo_documento VARCHAR NOT NULL,  -- 'DECISAO' ou 'ACORDAO'
    ministro VARCHAR,
    teor VARCHAR,
    descricao_monocratica TEXT,
    recurso VARCHAR,
    texto_completo TEXT NOT NULL,
    data_publicacao DATE,
    data_recebimento DATE,
    data_distribuicao DATE,
    data_insercao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assuntos TEXT
);

CREATE INDEX IF NOT EXISTS idx_integras_processo ON integras(numero_processo);
CREATE INDEX IF NOT EXISTS idx_integras_tipo ON integras(tipo_documento);
CREATE INDEX IF NOT EXISTS idx_integras_ministro ON integras(ministro);
CREATE INDEX IF NOT EXISTS idx_integras_data_pub ON integras(data_publicacao DESC);
CREATE INDEX IF NOT EXISTS idx_integras_hash ON integras(hash_conteudo);

PRAGMA create_fts_index(
    'integras', 'seq_documento', 'texto_completo',
    stemmer = 'portuguese',
    stopwords = 'stopwords_juridico',
    strip_accents = 1,
    lower = 1,
    overwrite = 1
);
```

Novos metodos em STJDatabase:
```python
def inserir_integras_batch(self, registros) -> tuple[int, int, int]: ...
def buscar_texto_completo(self, termo, tipo=None, dias=365, limit=20): ...
def buscar_por_processo(self, numero_processo) -> dict: ...
def estatisticas_integras(self) -> dict: ...
```

**Step 4: Run tests**

**Step 5: Commit**

```bash
git add src/database.py tests/test_database.py
git commit -m "feat(stj): add integras table with FTS and correlation queries"
```

---

## Task 6: Corrigir comandos mortos da CLI (espelhos)

**Files:**
- Modify: `legal-workbench/ferramentas/stj-dados-abertos/cli.py`
- Modify: `legal-workbench/ferramentas/stj-dados-abertos/config.py`

**Step 1: Identificar problema**

`stj-download-periodo`, `stj-download-orgao`, `stj-download-mvp` usam `get_date_range_urls()` e `get_mvp_urls()` que retornam listas vazias. O `download_from_ckan()` existe no downloader mas nao esta exposto na CLI.

**Step 2: Reescrever comandos**

Substituir internals para usar `STJDownloader.download_from_ckan()`:

```python
@app.command()
def stj_download_orgao(
    orgao: str = typer.Argument(..., help="Orgao julgador"),
    meses: int = typer.Option(3, help="Ultimos N meses"),
    force: bool = typer.Option(False, "--force", "-f"),
):
    """Baixa espelhos de acordaos via CKAN API."""
    downloader = STJDownloader()
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=meses * 30)).strftime("%Y-%m-%d")
    files = downloader.download_from_ckan(orgao, start, end, force)
    ...
```

**Step 3: Remover funcoes deprecadas de config.py**

Deletar: `get_date_range_urls()`, `get_mvp_urls()`, `STJ_BASE_URL_LEGACY`, `STJ_BASE_URL`

**Step 4: Run tests**

**Step 5: Commit**

```bash
git add cli.py config.py
git commit -m "fix(stj): rewire CLI download commands to use CKAN API"
```

---

## Task 7: Adicionar comandos CLI para integras

**Files:**
- Modify: `legal-workbench/ferramentas/stj-dados-abertos/cli.py`

**Step 1: Implement novos comandos**

```python
@app.command()
def stj_download_integras(
    inicio: str = typer.Option(None, help="YYYY-MM-DD, default: baixa tudo"),
    fim: str = typer.Option(None, help="YYYY-MM-DD, default: hoje"),
    force: bool = typer.Option(False, "--force", "-f"),
):
    """Baixa integras completas do STJ. Retoma de onde parou se interrompido."""
    ...

@app.command()
def stj_processar_integras(
    data: str = typer.Option(None, help="YYYYMMDD especifico"),
):
    """Processa integras: extrai ZIPs, normaliza, insere no banco."""
    ...

@app.command()
def stj_buscar_integra(
    termo: str = typer.Argument(...),
    tipo: str = typer.Option(None, help="DECISAO ou ACORDAO"),
    dias: int = typer.Option(365),
    limit: int = typer.Option(20),
):
    """FTS no texto completo das integras."""
    ...

@app.command()
def stj_buscar_processo(
    numero: str = typer.Argument(...),
):
    """Busca unificada: espelho + integra(s) correlacionados."""
    ...

@app.command()
def stj_estatisticas_integras():
    """Estatisticas do dataset de integras."""
    ...
```

**Step 2: Commit**

```bash
git add cli.py
git commit -m "feat(stj): add CLI commands for integras"
```

---

## Task 8: Testes de integracao

**Files:**
- Create: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_integras_pipeline.py`

**Step 1: Write tests**

```python
class TestIntegrasPipeline:
    def test_full_pipeline(self, tmp_path): ...
    def test_correlacao_espelhos_integras(self, tmp_path): ...
    def test_progress_resume(self, tmp_path): ...
    def test_deduplicacao(self, tmp_path): ...
```

**Step 2: Run all tests**

```bash
pytest tests/ -v
```

**Step 3: Commit**

```bash
git add tests/
git commit -m "test(stj): add integration tests for integras pipeline"
```

---

## Task 9: Download retroativo completo (EXECUCAO)

```bash
export DATA_PATH=/mnt/juridico-data/stj
export DB_PATH=/mnt/juridico-data/stj/database/stj.duckdb
cd /home/opc/lex-vector/legal-workbench/ferramentas/stj-dados-abertos
source .venv/bin/activate

# Download completo (~9.2 GB, todos os resources desde fev/2022)
python cli.py stj-download-integras

# Processar tudo (extrair ZIPs, normalizar, inserir no banco)
python cli.py stj-processar-integras

# Verificar
python cli.py stj-estatisticas-integras
python cli.py stj-buscar-processo "2591846"
python cli.py stj-buscar-integra "habeas corpus" --limit 5
```

---

## Task 10: Documentacao e limpeza

**Files:**
- Modify: `README.md`, `CLAUDE.md`
- Delete: funcoes deprecadas restantes

Documentar novos comandos, schema da tabela integras, correlacao, estatisticas.

---

## Verificacao End-to-End

```bash
cd legal-workbench/ferramentas/stj-dados-abertos
source .venv/bin/activate
export DATA_PATH=/mnt/juridico-data/stj
export DB_PATH=/mnt/juridico-data/stj/database/stj.duckdb

# 1. Testes unitarios
pytest tests/ -v

# 2. Espelhos preservados
python cli.py stj-estatisticas
# Esperado: 29.160 acordaos

# 3. Integras completas
python cli.py stj-estatisticas-integras
# Esperado: centenas de milhares de registros

# 4. Correlacao
python cli.py stj-buscar-processo "2591846"

# 5. FTS integras
python cli.py stj-buscar-integra "responsabilidade civil" --limit 5

# 6. Download espelhos (CLI corrigida)
python cli.py stj-download-orgao corte_especial --meses 1

# 7. Info unificada
python cli.py stj-info
```

---

## Riscos e Mitigacoes

| Risco | Mitigacao |
|-------|-----------|
| Download interrompido | Progresso persistido; retry com backoff; retomada automatica |
| ZIP corrompido | Validacao pre-extracao; re-download automatico |
| Campos variantes | Normalizacao robusta para ambos os formatos (consolidado/diario) |
| Volume grande (9+ GB) | Download streaming; DuckDB comprime automaticamente |
| Correlacao imprecisa | Regex p/ extrair numero; indices para join eficiente |
| Espaco em disco | 185 GB livres, precisa ~20 GB (dados + indices) |

## Dependencias Novas

Nenhuma. Tudo stdlib + dependencias existentes (httpx, duckdb, typer, rich, tenacity).
