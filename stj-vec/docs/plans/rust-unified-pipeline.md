# Pipeline Unificado de Download + Ingestao STJ (Rust)

**Data:** 2026-03-16
**Status:** Plano -- nenhuma implementacao feita

---

## 1. Contexto e Motivacao

O pipeline atual divide-se em duas linguagens:

- **Python** (`legal-workbench/ferramentas/stj-dados-abertos/`): download de dados via CKAN API
- **Rust** (`stj-vec/crates/ingest/`): processamento de integras, chunking, insercao no SQLite

Unificar em Rust elimina a ponte entre linguagens, simplifica deploy (binario unico),
e permite execucao mensal com um unico comando.

### Fontes de dados (CKAN)

Portal: `https://dadosabertos.web.stj.jus.br`

| Dataset | ID CKAN | Resources | Formato |
|---------|---------|-----------|---------|
| Integras | `integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica` | ~1825 | Pares ZIP (TXTs) + JSON (metadados), nomeados `YYYYMM.zip` + `metadadosYYYYMM.json` |
| Espelhos (10 orgaos) | `espelhos-de-acordaos-{orgao}` | ~49 cada | 1 ZIP historico + JSONs mensais `YYYYMMDD.json` |

Orgaos (espelhos):
- corte-especial, primeira-secao, segunda-secao, terceira-secao
- primeira-turma, segunda-turma, terceira-turma, quarta-turma, quinta-turma, sexta-turma

---

## 2. Arquitetura Atual do Crate Ingest

```
stj-vec/crates/ingest/src/
  main.rs       -- CLI (Clap): Scan, Chunk, Embed, Full, Stats, Reset, ExportChunks, ImportEmbeddings
  pipeline.rs   -- Pipeline { storage, config, integras_dir, metadata_dir }
  scanner.rs    -- scan_integras_dir() -- varre subdiretorios de integras
  exporter.rs   -- export_chunks_for_modal()
  importer.rs   -- import_embeddings_from_modal()
  lib.rs        -- re-exports
```

Dependencias relevantes ja no workspace:
- `reqwest` (com feature `json`) -- HTTP client
- `zip` -- descompressao ZIP
- `tokio` (full) -- async runtime
- `indicatif` -- progress bars
- `chrono` -- datas

O `Pipeline` opera de forma sincrona (metodos `&self -> Result<()>`).
O `Storage` (core) usa rusqlite com `Mutex<Connection>`.

---

## 3. Schema dos Espelhos (verificado via CKAN API)

Cada JSON de espelho e um array de objetos. Campos do espelho (sample real da Primeira Turma):

```json
{
  "id": "000815399",
  "numeroProcesso": "1424080",
  "numeroRegistro": "201304043911",
  "siglaClasse": "EDcl no AgInt nos EDcl no REsp",
  "descricaoClasse": "EMBARGOS DE DECLARACAO NO AGRAVO INTERNO ...",
  "nomeOrgaoJulgador": "PRIMEIRA TURMA",
  "ministroRelator": "REGINA HELENA COSTA",
  "dataPublicacao": "DJE        DATA:25/05/2022",
  "ementa": "PROCESSUAL CIVIL. ADMINISTRATIVO...",
  "tipoDeDecisao": "ACORDAO",
  "dataDecisao": "20220523",
  "decisao": "Vistos e relatados estes autos...",
  "jurisprudenciaCitada": "...",
  "notas": null,
  "informacoesComplementares": null,
  "termosAuxiliares": null,
  "teseJuridica": null,
  "tema": null,
  "referenciasLegislativas": ["LEG:FED LEI:013105 ..."],
  "acordaosSimilares": []
}
```

### Mapeamento espelho -> documents

| Campo espelho | Campo documents | Notas |
|---------------|-----------------|-------|
| `numeroProcesso` | `processo` | Chave de cruzamento |
| `siglaClasse` | `classe` | Ex: "REsp", "AgInt no AREsp" |
| `nomeOrgaoJulgador` | `orgao_julgador` | Ex: "PRIMEIRA TURMA" |
| `dataDecisao` | `data_julgamento` | Formato `YYYYMMDD`, converter para `YYYY-MM-DD` |
| `ministroRelator` | `ministro` | Ja existe parcialmente via metadados integras |
| `ementa` | -- | Nao mapeado hoje, potencialmente util |
| `teseJuridica` | -- | Nao mapeado hoje, potencialmente util |

---

## 4. Novos Modulos e Arquivos

### 4.1 Novo modulo: `download.rs` (no crate ingest)

Responsavel por baixar resources do CKAN (integras e espelhos).

```rust
// stj-vec/crates/ingest/src/download.rs

/// Tipos CKAN deserializados
struct CkanPackageResponse { success: bool, result: CkanPackage }
struct CkanPackage { resources: Vec<CkanResource> }
struct CkanResource { id: String, name: String, url: String, format: String, size: Option<u64> }

/// Estado de download local (tracking de quais resources ja foram baixados)
struct DownloadManifest { downloaded: HashMap<String, DownloadedResource> }
struct DownloadedResource { resource_id: String, name: String, downloaded_at: String, size: u64 }

/// Funcoes principais
async fn list_resources(client: &Client, dataset_id: &str) -> Result<Vec<CkanResource>>
async fn download_resource(client: &Client, resource: &CkanResource, dest_dir: &Path) -> Result<PathBuf>
async fn download_integras(client: &Client, config: &DownloadConfig) -> Result<DownloadSummary>
async fn download_espelhos(client: &Client, config: &DownloadConfig) -> Result<DownloadSummary>
fn load_manifest(path: &Path) -> Result<DownloadManifest>
fn save_manifest(manifest: &DownloadManifest, path: &Path) -> Result<()>
```

**Logica incremental:** um `manifest.json` em cada diretorio de dados rastreia
quais resources (por `id` CKAN) ja foram baixados. Antes de baixar, consulta o
manifest e pula os que ja existem.

### 4.2 Novo modulo: `enrich.rs` (no crate ingest)

Responsavel por cruzar espelhos com documents no SQLite.

```rust
// stj-vec/crates/ingest/src/enrich.rs

/// Espelho deserializado do JSON CKAN
struct EspelhoAcordao {
    id: String,
    numero_processo: String,
    sigla_classe: Option<String>,
    nome_orgao_julgador: Option<String>,
    ministro_relator: Option<String>,
    data_decisao: Option<String>,  // YYYYMMDD
    ementa: Option<String>,
    // ... demais campos opcionais
}

/// Resultado do enriquecimento
struct EnrichSummary { matched: u64, updated: u64, unmatched: u64 }

fn enrich_from_espelhos(storage: &Storage, espelhos_dir: &Path) -> Result<EnrichSummary>
fn load_espelhos(path: &Path) -> Result<Vec<EspelhoAcordao>>
fn normalize_processo(raw: &str) -> String  // Remove pontos, barras, espacos
```

**Logica de cruzamento:**
1. Carregar todos os JSONs de espelhos de um diretorio
2. Para cada espelho, normalizar `numeroProcesso`
3. Buscar no SQLite: `SELECT id, classe, orgao_julgador, data_julgamento FROM documents WHERE processo = ?`
4. Se encontrou e campos estao vazios/NULL, fazer UPDATE seletivo
5. Reportar estatisticas de match/update/unmatched

**Normalizacao de processo:** o campo `processo` em `documents` pode ter formatos
variados (com/sem pontuacao). O `numeroProcesso` do espelho e apenas digitos.
Precisamos normalizar ambos para comparacao (strip de tudo que nao e digito).

### 4.3 Novo modulo: `unzip.rs` (no crate ingest)

Extrai ZIPs de integras baixados para o diretorio de integras.

```rust
// stj-vec/crates/ingest/src/unzip.rs

fn extract_integras_zip(zip_path: &Path, dest_dir: &Path) -> Result<usize>
```

O pipeline atual espera integras em subdiretorios como `stj-vec/data/integras/202202/`.
Cada ZIP contem TXTs nomeados por `seqDocumento`. Este modulo extrai para o formato
que o scanner ja espera.

### 4.4 Modificacoes em modulos existentes

#### `main.rs` -- novos subcomandos

```rust
enum Commands {
    // ... existentes ...

    /// Baixa integras do CKAN
    Download {
        #[arg(long, value_enum)]
        source: DownloadSource,
        #[arg(long)]
        limit: Option<usize>,
    },
    /// Enriquece documents com dados dos espelhos
    Enrich,
    /// Pipeline completo mensal: download + ingest + enrich
    Update,
}

enum DownloadSource { Integras, Espelhos, All }
```

#### `config.rs` (core) -- novas configs

```rust
struct DataConfig {
    pub integras_dir: String,
    pub metadata_dir: String,
    pub db_path: String,
    // NOVOS:
    pub espelhos_dir: String,      // default: "data/espelhos"
    pub download_dir: String,      // default: "data/downloads" (ZIPs brutos)
}

// Nova secao no TOML
struct CkanConfig {
    pub base_url: String,          // default: "https://dadosabertos.web.stj.jus.br"
    pub integras_dataset: String,  // default: "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"
    pub espelhos_datasets: Vec<String>,  // lista dos 10 dataset IDs
    pub download_timeout_secs: u64,      // default: 300
    pub max_concurrent_downloads: usize, // default: 2
}
```

#### `pipeline.rs` -- novos metodos

```rust
impl Pipeline {
    // NOVOS:
    pub async fn download(&self, source: DownloadSource, limit: Option<usize>) -> Result<()>
    pub fn enrich(&self) -> Result<EnrichSummary>
    pub async fn update(&self, limit: Option<usize>) -> Result<()>  // download + scan + chunk + enrich
}
```

**Nota sobre async:** o Pipeline atual e sincrono. Os metodos de download
precisam ser async (reqwest). Duas opcoes:

1. **Converter Pipeline para async** -- mais limpo, mas toca tudo
2. **Manter sincrono + `block_on` interno** -- pragmatico, menos invasivo

Recomendacao: opcao 1. O main ja roda sob `#[tokio::main]`. Converter os metodos
que precisam de async e manter os demais como `fn` normais chamados de dentro
de metodos async. Custo baixo pois o Pipeline nao e chamado de muitos lugares.

#### `storage.rs` (core) -- novos metodos

```rust
impl Storage {
    /// Busca documents por numero de processo (normalizado)
    pub fn find_documents_by_processo(&self, processo: &str) -> Result<Vec<Document>>

    /// Update seletivo de metadados (so atualiza campos NULL/vazios)
    pub fn enrich_document(
        &self,
        doc_id: &str,
        classe: Option<&str>,
        orgao_julgador: Option<&str>,
        data_julgamento: Option<&str>,
        ministro: Option<&str>,
    ) -> Result<bool>  // true se atualizou algo

    /// Indice para busca por processo (ja existe idx_docs_processo)
    // Nenhuma alteracao de schema necessaria
}
```

#### `lib.rs` -- novos exports

```rust
pub mod download;
pub mod enrich;
pub mod unzip;
```

---

## 5. Dependencias Rust

### Ja existentes no workspace (nenhuma adicao necessaria):
- `reqwest` (0.12, features: json) -- HTTP client
- `zip` (2) -- descompressao
- `tokio` (1, full) -- async runtime
- `serde` + `serde_json` -- serialization
- `indicatif` -- progress bars
- `chrono` -- datas
- `anyhow` -- error handling
- `tracing` -- logging

### Potencialmente necessarias:
- `tokio::fs` -- ja incluido em `tokio/full`, para escrita async de arquivos grandes
- Nenhuma dependencia nova necessaria. O workspace ja tem tudo.

---

## 6. Logica de Cruzamento Espelho <-> Documents

### Problema central: chave de join

O campo `processo` em `documents` vem do metadados de integras (`StjMetadata.processo`).
Formato tipico: `"REsp nº 1.424.080 - RS (2013/0404391-1)"` ou apenas digitos `"1424080"`.

O campo `numeroProcesso` do espelho e sempre digitos puros: `"1424080"`.

### Estrategia de normalizacao

```rust
fn normalize_processo(raw: &str) -> String {
    // Extrai apenas digitos, ignora pontos/barras/tracos/UF
    // "REsp nº 1.424.080 - RS (2013/0404391-1)" -> "1424080"
    // Mas cuidado: o numero do registro (2013/0404391-1) tambem tem digitos
    // Solucao: extrair apenas o primeiro grupo de digitos consecutivos com 5+ digitos
    // Ou usar regex mais sofisticado
    raw.chars().filter(|c| c.is_ascii_digit()).collect()
}
```

**Risco:** a normalizacao simples (so digitos) pode gerar colisoes se o campo `processo`
contiver o numero de registro junto. Mitigacao: validar com amostra antes de rodar em
massa. O campo `numeroRegistro` do espelho (`"201304043911"`) pode servir como chave
secundaria contra `numero_registro` do StjMetadata.

### Fluxo de enriquecimento

```
Para cada arquivo JSON em espelhos_dir/:
  Para cada espelho no JSON:
    processo_norm = normalize_processo(espelho.numeroProcesso)
    docs = storage.find_documents_by_processo(processo_norm)
    Para cada doc em docs:
      houve_update = storage.enrich_document(
        doc.id,
        classe = espelho.siglaClasse  SE doc.classe IS NULL,
        orgao_julgador = espelho.nomeOrgaoJulgador  SE doc.orgao_julgador IS NULL,
        data_julgamento = format_date(espelho.dataDecisao)  SE doc.data_julgamento IS NULL,
        ministro = espelho.ministroRelator  SE doc.ministro IS NULL,
      )
```

### SQL de enriquecimento

```sql
UPDATE documents SET
  classe = COALESCE(classe, ?1),
  orgao_julgador = COALESCE(orgao_julgador, ?2),
  data_julgamento = COALESCE(data_julgamento, ?3),
  ministro = COALESCE(ministro, ?4)
WHERE id = ?5
  AND (classe IS NULL OR orgao_julgador IS NULL OR data_julgamento IS NULL OR ministro IS NULL)
```

Isso garante idempotencia: re-rodar o enrich nao sobrescreve dados ja preenchidos.

---

## 7. Fluxo do Comando `update`

```
stj-ingest update
  |
  +-> download --source integras
  |     +-> CKAN API: list resources do dataset de integras
  |     +-> Para cada resource nao no manifest:
  |     |     +-> Download ZIP + JSON metadados
  |     |     +-> Extrair ZIP para integras_dir/{YYYYMM}/
  |     |     +-> Mover JSON metadados para metadata_dir/
  |     |     +-> Registrar no manifest
  |     +-> Report: N novos resources baixados
  |
  +-> download --source espelhos
  |     +-> Para cada um dos 10 datasets de espelhos:
  |     |     +-> CKAN API: list resources
  |     |     +-> Para cada JSON nao no manifest:
  |     |           +-> Download para espelhos_dir/{orgao}/
  |     |           +-> Registrar no manifest
  |     +-> Report: N novos JSONs baixados
  |
  +-> scan + chunk (pipeline existente)
  |     +-> Detecta novos subdiretorios em integras_dir
  |     +-> Chunka e insere no SQLite
  |
  +-> enrich
        +-> Le todos os JSONs de espelhos
        +-> Cruza com documents
        +-> Report: N matched, N updated, N unmatched
```

---

## 8. Estrutura de Diretorios de Dados

```
stj-vec/data/                          # NOVO diretorio raiz de dados
  downloads/                           # ZIPs brutos (temporarios ou archivados)
    integras/
      202202.zip
      metadados202202.json
      ...
    manifest.json                      # tracking de downloads
  integras/                            # Extraidos (o que o scanner ja espera)
    202202/
      000001.txt
      000002.txt
      ...
  espelhos/                            # JSONs de espelhos por orgao
    corte-especial/
      20220508.json  (extraido do ZIP historico)
      20220531.json
      ...
    primeira-turma/
      20220531.json
      ...
    manifest.json                      # tracking de downloads
  metadata/                            # Metadados de integras (ja existente)
    metadados202202.json
    ...
```

---

## 9. Estimativa de Complexidade

| # | Tarefa | Arquivos | Complexidade | Horas est. |
|---|--------|----------|--------------|------------|
| 1 | `download.rs` -- tipos CKAN + list resources | download.rs | Baixa | 1h |
| 2 | `download.rs` -- download individual + manifest | download.rs | Media | 2h |
| 3 | `download.rs` -- download_integras (ZIP + JSON pareados) | download.rs | Media | 2h |
| 4 | `download.rs` -- download_espelhos (10 datasets) | download.rs | Media | 2h |
| 5 | `unzip.rs` -- extracao de ZIPs de integras | unzip.rs | Baixa | 1h |
| 6 | `enrich.rs` -- struct EspelhoAcordao + deserialize | enrich.rs | Baixa | 1h |
| 7 | `enrich.rs` -- logica de cruzamento + normalize_processo | enrich.rs | Media-Alta | 3h |
| 8 | `storage.rs` -- find_documents_by_processo + enrich_document | storage.rs | Baixa | 1h |
| 9 | `config.rs` -- CkanConfig + DataConfig expandido | config.rs | Baixa | 0.5h |
| 10 | `main.rs` -- novos subcomandos (Download, Enrich, Update) | main.rs | Baixa | 1h |
| 11 | `pipeline.rs` -- async conversion + novos metodos | pipeline.rs | Media | 2h |
| 12 | Testes unitarios (download mock, enrich, normalize) | tests | Media | 2h |
| 13 | Teste de integracao com CKAN real (1 resource) | tests | Baixa | 1h |
| **Total** | | | | **~19.5h** |

---

## 10. Ordem de Implementacao

### Fase 1: Fundacao (sem IO externo)

1. **Config** -- adicionar `CkanConfig` e campos novos em `DataConfig`
2. **Storage** -- `find_documents_by_processo()` e `enrich_document()`
3. **Enrich** -- `EspelhoAcordao`, `load_espelhos()`, `normalize_processo()`
4. **Testes enrich** -- com fixture JSONs locais

> Validacao: rodar `enrich` com JSONs de espelho baixados manualmente.
> Isso valida a logica de cruzamento antes de automatizar o download.

### Fase 2: Download

5. **Download types** -- structs CKAN, manifest
6. **Download core** -- `list_resources()`, `download_resource()`
7. **download_espelhos()** -- 10 datasets, tracking incremental
8. **download_integras()** -- ZIP + JSON pareados
9. **Unzip** -- extracao automatica

> Validacao: baixar 1 resource de espelho + 1 de integras via CLI.

### Fase 3: Integracao

10. **Pipeline async** -- converter metodos necessarios
11. **CLI** -- novos subcomandos Download, Enrich, Update
12. **Pipeline.update()** -- orquestrar download + scan + chunk + enrich
13. **Testes E2E** -- mock HTTP ou teste com CKAN real (1 resource)

> Validacao: rodar `stj-ingest update` end-to-end.

---

## 11. Riscos e Mitigacoes

| Risco | Impacto | Mitigacao |
|-------|---------|-----------|
| Normalizacao de processo gera falsos positivos/negativos | Match rate baixo no enrich | Testar com amostra de 1000 espelhos antes de rodar em massa |
| ZIPs de integras sao grandes (200+ MB) | Download lento, disco | Download incremental, limpar ZIPs apos extracao |
| CKAN API instavel ou rate-limited | Downloads falham | Retry com backoff, `--limit` para controlar volume |
| Campo `processo` em documents tem formato inconsistente | Join falha | Normalizar ambos os lados; fallback por `numeroRegistro` |
| Pipeline sincrono -> async quebra interface | Regressao | Converter gradualmente, manter testes passando |
| Espelhos tem ~500 resources (10 datasets x 49) | Volume de dados | Paralelismo controlado (max 2 downloads simultaneos) |

---

## 12. O Que NAO Esta no Escopo

- **Re-download de dados ja ingeridos** -- o pipeline e incremental, nao reconstroi do zero
- **Scheduler/cron** -- execucao mensal manual
- **Embeddings** -- pipeline de embeddings (Modal/ONNX) continua separado
- **Qdrant** -- importacao para Qdrant continua via `import_qdrant.py`
- **Ementa/teseJuridica** -- campos ricos dos espelhos que nao mapeiam para `documents` hoje.
  Decisao futura: criar campos novos ou tabela separada `espelhos`
- **Deprecar Python** -- apos validacao do pipeline Rust, o codigo Python pode ser archivado

---

## 13. Decisoes em Aberto (requer alinhamento)

1. **Armazenar espelhos integrais?** Os espelhos tem campos ricos (ementa, teseJuridica,
   jurisprudenciaCitada, referenciasLegislativas) que nao cabem em `documents`.
   Opcoes:
   - (a) Criar tabela `espelhos` com todos os campos (mais flexivel, mais schema)
   - (b) Apenas enriquecer `documents` com os 4 campos mapeados (mais simples)
   - Recomendacao: comecar com (b), evoluir para (a) se/quando precisar buscar por ementa

2. **Converter Pipeline inteiro para async ou manter hibrido?**
   - Recomendacao: converter. O custo e baixo e o resultado e mais idiomatico.

3. **Onde armazenar `data/`?** O DB ja esta em `stj-vec/db/` (52GB).
   Os espelhos sao pequenos (~50MB total). As integras brutas (ZIPs) sao ~40GB.
   - Opcao: manter ZIPs em `stj-vec/data/downloads/` e deletar apos extracao
   - Ou: manter em diretorio separado fora do repo (ex: `/home/opc/juridico-data/stj/`)
