# Modal Embedding Service Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Modal Class que gera embeddings BGE-M3 (1024 dims) para ~7M chunks juridicos do STJ, com modelo pre-carregado em Volume para cold start minimo.

**Architecture:** Modal Class com T4 GPU, modelo BGE-M3 FP16 no Volume, chunks exportados como JSONL por source, embeddings salvos como .npz + index .json. `modal.map()` distribui sources entre containers. VM exporta chunks e importa embeddings via CLI do stj-vec-ingest.

**Tech Stack:** Modal (Class, Volume, Image), sentence-transformers, torch FP16, numpy, stj-vec-ingest (Rust CLI)

---

## Data Flow

```
VM (stj-vec-ingest)           Modal Volume              Modal Class (T4)
─────────────────            ────────────              ─────────────────
export-chunks ──────────────> /chunks/{source}.jsonl
                                                       @enter: load BGE-M3 FP16
                              /chunks/*.jsonl ────────> encode batches
                              /embeddings/{source}.npz  <── numpy (N,1024)
                              /embeddings/{source}.json <── [chunk_ids...]
import-embeddings <──────────< /embeddings/*
     └──> SQLite vec_chunks
```

## Referencia: APIs existentes

**Storage** (stj-vec-core):
- `Storage::open(path, dim)` -- dim=1024 cria vec_chunks
- `storage.insert_embedding(chunk_id, &[f32; 1024])` -- insere 1 embedding
- `storage.insert_embeddings_batch(&[(String, Vec<f32>)])` -- insere batch
- `storage.list_ingest_by_status("chunked")` -- sources prontos para embedding

**Pipeline** (stj-vec-ingest):
- `pipeline.embed_pending()` -- placeholder atual, precisa ser substituido
- `pipeline.storage` -- acesso ao Storage

**Config** (config.toml):
```toml
[embedding]
model = "BAAI/bge-m3"
dim = 1024
provider = "modal"

[embedding.modal]
endpoint = ""  # nao usado -- embed e offline via Volume
batch_size = 256
```

---

### Task 1: Criar Volume e baixar modelo BGE-M3

**Owner: backend-developer**

**Files:**
- Create: `stj-vec/modal/download_model.py`

**Step 1: Criar script de download do modelo para Volume**

```python
"""Download BGE-M3 para Modal Volume (executar 1x)."""
import modal

app = modal.App("stj-vec-model-download")

volume = modal.Volume.from_name("stj-vec-models", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("sentence-transformers>=3.0.0", "torch>=2.0.0")
)

@app.function(
    image=image,
    volumes={"/models": volume},
    timeout=900,
)
def download_model():
    from sentence_transformers import SentenceTransformer
    import os

    model_path = "/models/bge-m3"
    if os.path.exists(model_path) and os.listdir(model_path):
        print(f"Modelo ja existe em {model_path}")
        return

    print("Baixando BAAI/bge-m3...")
    model = SentenceTransformer("BAAI/bge-m3")
    model.save(model_path)
    volume.commit()
    print(f"Modelo salvo em {model_path}")
```

**Step 2: Executar download**

Run: `cd /home/opc/lex-vector/stj-vec && modal run modal/download_model.py::download_model`
Expected: modelo baixado no Volume `stj-vec-models` em `/models/bge-m3`

**Step 3: Verificar Volume**

Run: `modal volume ls stj-vec-models /models/bge-m3/ | head -10`
Expected: arquivos do modelo (config.json, model.safetensors, etc)

**Step 4: Commit**

```bash
git add stj-vec/modal/download_model.py
git commit -m "feat(stj-vec): add Modal script to download BGE-M3 to Volume"
```

---

### Task 2: Criar Modal Class para embedding

**Owner: backend-developer**

**Files:**
- Create: `stj-vec/modal/embed.py`

**Step 1: Implementar Class com @enter para carregar modelo**

```python
"""Modal Class para gerar embeddings BGE-M3 em batch."""
import modal
import json
import io

app = modal.App("stj-vec-embed")

volume_models = modal.Volume.from_name("stj-vec-models")
volume_data = modal.Volume.from_name("stj-vec-data", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0.0",
        "torch>=2.0.0",
        "numpy>=1.24.0",
    )
)


@app.cls(
    image=image,
    gpu="T4",
    volumes={
        "/models": volume_models,
        "/data": volume_data,
    },
    timeout=3600,
    container_idle_timeout=120,
)
class Embedder:
    @modal.enter()
    def load_model(self):
        import torch
        from sentence_transformers import SentenceTransformer

        print("Carregando BGE-M3 em FP16...")
        self.model = SentenceTransformer(
            "/models/bge-m3",
            device="cuda",
            model_kwargs={"torch_dtype": torch.float16},
        )
        self.model.eval()
        self.dim = self.model.get_sentence_embedding_dimension()
        print(f"Modelo carregado: dim={self.dim}")

    @modal.method()
    def embed_source(self, source_name: str, batch_size: int = 128) -> dict:
        """Processa 1 source JSONL, gera .npz + .json no Volume."""
        import numpy as np

        input_path = f"/data/chunks/{source_name}.jsonl"
        out_npz = f"/data/embeddings/{source_name}.npz"
        out_json = f"/data/embeddings/{source_name}.json"

        # Ler chunks
        chunk_ids = []
        texts = []
        with open(input_path, "r") as f:
            for line in f:
                obj = json.loads(line)
                chunk_ids.append(obj["id"])
                texts.append(obj["content"])

        if not texts:
            return {"source": source_name, "count": 0, "status": "empty"}

        # Gerar embeddings em batches
        all_embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        # Garantir float32 para compatibilidade com sqlite-vec
        embeddings = np.array(all_embeddings, dtype=np.float32)

        # Salvar
        import os
        os.makedirs("/data/embeddings", exist_ok=True)

        np.savez_compressed(out_npz, embeddings=embeddings)
        with open(out_json, "w") as f:
            json.dump(chunk_ids, f)

        volume_data.commit()

        return {
            "source": source_name,
            "count": len(chunk_ids),
            "shape": list(embeddings.shape),
            "status": "done",
        }

    @modal.method()
    def embed_single(self, text: str) -> list:
        """Embed de texto unico (para queries em tempo real)."""
        import numpy as np

        embedding = self.model.encode(
            [text],
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embedding[0].astype(np.float32).tolist()


@app.function(
    volumes={"/data": volume_data},
    timeout=60,
)
def list_pending_sources() -> list[str]:
    """Lista sources com chunks no Volume que ainda nao tem embeddings."""
    import os

    chunks_dir = "/data/chunks"
    embeddings_dir = "/data/embeddings"

    if not os.path.exists(chunks_dir):
        return []

    chunk_sources = {
        f.replace(".jsonl", "")
        for f in os.listdir(chunks_dir)
        if f.endswith(".jsonl")
    }
    done_sources = {
        f.replace(".npz", "")
        for f in os.listdir(embeddings_dir)
        if f.endswith(".npz")
    } if os.path.exists(embeddings_dir) else set()

    pending = sorted(chunk_sources - done_sources)
    return pending


@app.local_entrypoint()
def main(
    source: str = "",
    all_pending: bool = False,
    batch_size: int = 128,
):
    """Entrypoint: processar 1 source ou todos pendentes."""
    embedder = Embedder()

    if source:
        result = embedder.embed_source.remote(source, batch_size)
        print(f"Done: {result}")
    elif all_pending:
        sources = list_pending_sources.remote()
        print(f"{len(sources)} sources pendentes")
        if not sources:
            return

        # modal.map() distribui entre containers T4
        results = []
        for result in embedder.embed_source.map(
            sources,
            kwargs={"batch_size": batch_size},
        ):
            print(f"  {result['source']}: {result['count']} chunks -> {result['status']}")
            results.append(result)

        total = sum(r["count"] for r in results)
        print(f"\nTotal: {total} embeddings gerados para {len(results)} sources")
    else:
        print("Uso: modal run embed.py --source 202203")
        print("  ou: modal run embed.py --all-pending")
```

**Step 2: Verificar que compila/importa sem erros**

Run: `cd /home/opc/lex-vector/stj-vec && python -c "import ast; ast.parse(open('modal/embed.py').read()); print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add stj-vec/modal/embed.py
git commit -m "feat(stj-vec): add Modal embedding Class with T4 GPU and batch processing"
```

---

### Task 3: Adicionar export-chunks ao stj-vec-ingest

**Owner: eu (orquestrador)**

**Files:**
- Create: `stj-vec/crates/ingest/src/exporter.rs`
- Modify: `stj-vec/crates/ingest/src/lib.rs`
- Modify: `stj-vec/crates/ingest/src/main.rs`

**Step 1: Implementar exporter.rs**

```rust
//! Exporta chunks do SQLite para JSONL (1 arquivo por source).
//! Destino: Modal Volume via `modal volume put`.

use anyhow::{Context, Result};
use std::io::Write;
use std::path::Path;

use stj_vec_core::storage::Storage;

/// Exporta chunks de sources com status "chunked" para JSONL.
/// Retorna (sources_exported, chunks_exported).
pub fn export_chunks_for_modal(
    storage: &Storage,
    output_dir: &Path,
    limit: Option<usize>,
) -> Result<(usize, usize)> {
    std::fs::create_dir_all(output_dir)
        .with_context(|| format!("falha ao criar {}", output_dir.display()))?;

    let sources = storage.list_ingest_by_status("chunked")?;
    let sources_to_process = match limit {
        Some(n) => &sources[..n.min(sources.len())],
        None => &sources,
    };

    let mut total_sources = 0;
    let mut total_chunks = 0;

    for source in sources_to_process {
        let out_path = output_dir.join(format!("{}.jsonl", source.source_file));

        // Buscar todos os chunks desse source via documents
        let chunks = get_chunks_by_source(storage, &source.source_file)?;

        if chunks.is_empty() {
            tracing::warn!(source = %source.source_file, "no chunks found, skipping");
            continue;
        }

        let mut file = std::fs::File::create(&out_path)
            .with_context(|| format!("falha ao criar {}", out_path.display()))?;

        for (chunk_id, content) in &chunks {
            let line = serde_json::json!({"id": chunk_id, "content": content});
            writeln!(file, "{}", line)?;
        }

        tracing::info!(
            source = %source.source_file,
            chunks = chunks.len(),
            path = %out_path.display(),
            "exported"
        );
        total_sources += 1;
        total_chunks += chunks.len();
    }

    Ok((total_sources, total_chunks))
}

/// Busca chunks de um source (via JOIN documents.source_file -> chunks.doc_id).
fn get_chunks_by_source(
    storage: &Storage,
    source: &str,
) -> Result<Vec<(String, String)>> {
    // Nota: Storage nao tem metodo direto para isso.
    // Usar query customizada seria melhor, mas por ora iteramos
    // documentos do source e buscamos chunks de cada.
    // TODO: adicionar Storage::get_chunks_by_source() para eficiencia.

    let docs = storage.list_documents_by_source(source)?;
    let mut all_chunks = Vec::new();

    for doc_id in &docs {
        let chunks = storage.get_chunks_by_doc(doc_id)?;
        for chunk in chunks {
            all_chunks.push((chunk.id, chunk.content));
        }
    }

    Ok(all_chunks)
}
```

**Step 2: Adicionar `list_documents_by_source` ao Storage (core crate)**

Modify: `stj-vec/crates/core/src/storage.rs`

Adicionar metodo ao `impl Storage`:

```rust
/// Lista IDs de documentos de um source.
pub fn list_documents_by_source(&self, source: &str) -> Result<Vec<String>> {
    let conn = self.lock()?;
    let mut stmt = conn.prepare(
        "SELECT id FROM documents WHERE source_file = ? ORDER BY id",
    )?;
    let ids = stmt
        .query_map(params![source], |row| row.get::<_, String>(0))?
        .filter_map(|r| r.ok())
        .collect();
    Ok(ids)
}
```

**Step 3: Adicionar modulo ao lib.rs e subcomando ao main.rs**

Em `stj-vec/crates/ingest/src/lib.rs`, adicionar:
```rust
pub mod exporter;
```

Em `main.rs`, adicionar variante ao enum `Commands`:
```rust
/// Export chunks to JSONL for Modal embedding
ExportChunks {
    /// Output directory for JSONL files
    #[arg(short, long, default_value = "/tmp/stj-vec-chunks")]
    output: PathBuf,
    /// Limit number of sources to export
    #[arg(short, long)]
    limit: Option<usize>,
},
```

E no match:
```rust
Commands::ExportChunks { output, limit } => {
    let (sources, chunks) = stj_vec_ingest::exporter::export_chunks_for_modal(
        &pipeline.storage, &output, limit,
    )?;
    println!("Exported {chunks} chunks from {sources} sources to {}", output.display());
    println!("Upload: modal volume put stj-vec-data {0}/ /chunks/ --force", output.display());
}
```

**Step 4: Adicionar serde_json como dep do ingest (se nao tiver)**

Verificar `crates/ingest/Cargo.toml` -- serde_json ja esta nas deps.

**Step 5: Verificar compilacao**

Run: `cd /home/opc/lex-vector/stj-vec && cargo check -p stj-vec-ingest`
Expected: PASS (nota: pipeline.storage precisa ser pub ou acessivel)

**Step 6: Commit**

```bash
git add stj-vec/crates/core/src/storage.rs stj-vec/crates/ingest/src/exporter.rs stj-vec/crates/ingest/src/lib.rs stj-vec/crates/ingest/src/main.rs
git commit -m "feat(stj-vec): add export-chunks command for Modal Volume upload"
```

---

### Task 4: Adicionar import-embeddings ao stj-vec-ingest

**Owner: eu (orquestrador)**

**Files:**
- Create: `stj-vec/crates/ingest/src/importer.rs`
- Modify: `stj-vec/crates/ingest/src/lib.rs`
- Modify: `stj-vec/crates/ingest/src/main.rs`

**Step 1: Implementar importer.rs**

```rust
//! Importa embeddings (.npz + .json) gerados pelo Modal para SQLite.

use anyhow::{Context, Result};
use std::io::Read;
use std::path::Path;

use stj_vec_core::storage::Storage;

/// Importa embeddings de um diretorio com .npz + .json.
/// Retorna (sources_imported, embeddings_imported).
pub fn import_embeddings_from_modal(
    storage: &Storage,
    input_dir: &Path,
    limit: Option<usize>,
) -> Result<(usize, usize)> {
    let mut npz_files: Vec<_> = std::fs::read_dir(input_dir)?
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().is_some_and(|ext| ext == "npz"))
        .collect();

    npz_files.sort_by_key(|e| e.file_name());

    let files_to_process = match limit {
        Some(n) => &npz_files[..n.min(npz_files.len())],
        None => &npz_files,
    };

    let mut total_sources = 0;
    let mut total_embeddings = 0;

    for entry in files_to_process {
        let npz_path = entry.path();
        let source_name = npz_path
            .file_stem()
            .unwrap_or_default()
            .to_string_lossy()
            .into_owned();

        let json_path = input_dir.join(format!("{source_name}.json"));
        if !json_path.exists() {
            tracing::warn!(source = %source_name, "index JSON not found, skipping");
            continue;
        }

        // Ler chunk IDs
        let ids_content = std::fs::read_to_string(&json_path)?;
        let chunk_ids: Vec<String> = serde_json::from_str(&ids_content)?;

        // Ler embeddings do .npz
        let embeddings = read_npz_embeddings(&npz_path)?;

        if chunk_ids.len() != embeddings.len() {
            anyhow::bail!(
                "mismatch {source_name}: {} ids vs {} embeddings",
                chunk_ids.len(),
                embeddings.len()
            );
        }

        // Inserir em batch
        let pairs: Vec<(String, Vec<f32>)> = chunk_ids
            .into_iter()
            .zip(embeddings)
            .collect();

        storage.insert_embeddings_batch(&pairs)?;

        // Atualizar ingest_log para "done"
        if let Ok(Some(status)) = storage.get_ingest_status(&source_name) {
            storage.set_ingest_status(
                &source_name,
                "done",
                status.doc_count,
                status.chunk_count,
            )?;
        }

        tracing::info!(
            source = %source_name,
            embeddings = pairs.len(),
            "imported"
        );
        total_sources += 1;
        total_embeddings += pairs.len();
    }

    Ok((total_sources, total_embeddings))
}

/// Le array de embeddings de um arquivo .npz (numpy compressed).
/// Espera key "embeddings" com shape (N, dim) e dtype float32.
fn read_npz_embeddings(path: &Path) -> Result<Vec<Vec<f32>>> {
    let file = std::fs::File::open(path)
        .with_context(|| format!("falha ao abrir {}", path.display()))?;

    let mut archive = zip::ZipArchive::new(file)
        .with_context(|| format!("falha ao ler npz {}", path.display()))?;

    // .npz e um zip com arrays .npy dentro. A key "embeddings" gera "embeddings.npy".
    let mut npy_file = archive
        .by_name("embeddings.npy")
        .with_context(|| "key 'embeddings' nao encontrada no npz")?;

    let mut data = Vec::new();
    npy_file.read_to_end(&mut data)?;

    parse_npy_f32_2d(&data)
}

/// Parser minimo de .npy format (numpy array serializado).
/// Suporta apenas dtype float32, C-contiguous, 2D.
fn parse_npy_f32_2d(data: &[u8]) -> Result<Vec<Vec<f32>>> {
    // .npy format: 6 magic bytes, 2 version bytes, 2 header_len bytes, header, data
    if data.len() < 10 || &data[..6] != b"\x93NUMPY" {
        anyhow::bail!("nao e formato .npy valido");
    }

    let header_len = u16::from_le_bytes([data[8], data[9]]) as usize;
    let header_str = std::str::from_utf8(&data[10..10 + header_len])?;

    // Parse shape from header: {'descr': '<f4', 'fortran_order': False, 'shape': (N, D), }
    let shape = parse_npy_shape(header_str)?;
    if shape.len() != 2 {
        anyhow::bail!("esperado array 2D, got {}D", shape.len());
    }

    let (rows, cols) = (shape[0], shape[1]);
    let data_start = 10 + header_len;
    let expected_bytes = rows * cols * 4; // float32 = 4 bytes

    if data.len() < data_start + expected_bytes {
        anyhow::bail!(
            "dados insuficientes: {} bytes, esperado {}",
            data.len() - data_start,
            expected_bytes
        );
    }

    let float_data = &data[data_start..data_start + expected_bytes];
    let mut result = Vec::with_capacity(rows);

    for i in 0..rows {
        let start = i * cols * 4;
        let end = start + cols * 4;
        let row: Vec<f32> = float_data[start..end]
            .chunks_exact(4)
            .map(|bytes| f32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]))
            .collect();
        result.push(row);
    }

    Ok(result)
}

/// Extrai shape do header .npy.
fn parse_npy_shape(header: &str) -> Result<Vec<usize>> {
    // Procura 'shape': (N, D)
    let shape_start = header
        .find("'shape':")
        .or_else(|| header.find("\"shape\":"))
        .ok_or_else(|| anyhow::anyhow!("shape nao encontrado no header"))?;

    let after = &header[shape_start..];
    let paren_start = after
        .find('(')
        .ok_or_else(|| anyhow::anyhow!("( nao encontrado"))?;
    let paren_end = after
        .find(')')
        .ok_or_else(|| anyhow::anyhow!(") nao encontrado"))?;

    let shape_str = &after[paren_start + 1..paren_end];
    let dims: Vec<usize> = shape_str
        .split(',')
        .filter_map(|s| s.trim().parse().ok())
        .collect();

    Ok(dims)
}
```

**Step 2: Registrar modulo e subcomando**

Em `lib.rs` adicionar: `pub mod importer;`

Em `main.rs` adicionar variante:
```rust
/// Import embeddings from Modal Volume (.npz + .json)
ImportEmbeddings {
    /// Directory with .npz and .json files
    #[arg(short, long, default_value = "/tmp/stj-vec-embeddings")]
    input: PathBuf,
    /// Limit number of sources to import
    #[arg(short, long)]
    limit: Option<usize>,
},
```

E no match:
```rust
Commands::ImportEmbeddings { input, limit } => {
    let (sources, embeddings) = stj_vec_ingest::importer::import_embeddings_from_modal(
        &pipeline.storage, &input, limit,
    )?;
    println!("Imported {embeddings} embeddings from {sources} sources");
}
```

**Step 3: Verificar compilacao**

Run: `cd /home/opc/lex-vector/stj-vec && cargo check -p stj-vec-ingest`
Expected: PASS

**Step 4: Commit**

```bash
git add stj-vec/crates/ingest/src/importer.rs stj-vec/crates/ingest/src/lib.rs stj-vec/crates/ingest/src/main.rs
git commit -m "feat(stj-vec): add import-embeddings command with .npz parser"
```

---

### Task 5: Teste end-to-end com 1 source

**Owner: eu (orquestrador) -- execucao manual com usuario**

**Step 1: Scan + chunk 1 source**

```bash
cd /home/opc/lex-vector/stj-vec
cargo run --release -p stj-vec-ingest -- --config config.toml scan
cargo run --release -p stj-vec-ingest -- --config config.toml chunk
# Parar apos 1 source se necessario (Ctrl+C apos primeiro source concluir)
```

**Step 2: Export chunks**

```bash
cargo run --release -p stj-vec-ingest -- --config config.toml export-chunks --limit 1 --output /tmp/stj-vec-chunks
ls -la /tmp/stj-vec-chunks/
wc -l /tmp/stj-vec-chunks/*.jsonl
```

Expected: 1 arquivo JSONL com milhares de linhas

**Step 3: Upload para Modal Volume**

```bash
modal volume put stj-vec-data /tmp/stj-vec-chunks/ /chunks/ --force
modal volume ls stj-vec-data /chunks/
```

**Step 4: Rodar embedding no Modal (1 source, T4)**

```bash
cd /home/opc/lex-vector/stj-vec
modal run modal/embed.py --source <NOME_SOURCE>
```

Expected: embedding gerado, resultado no Volume

**Step 5: Download embeddings**

```bash
modal volume get stj-vec-data /embeddings/ /tmp/stj-vec-embeddings/
ls -la /tmp/stj-vec-embeddings/
```

**Step 6: Import embeddings**

```bash
cargo run --release -p stj-vec-ingest -- --config config.toml import-embeddings --input /tmp/stj-vec-embeddings --limit 1
cargo run --release -p stj-vec-ingest -- --config config.toml stats
```

Expected: embedding_count > 0, ingest_done = 1

**Step 7: Testar busca via server**

```bash
# Em um terminal:
cargo run --release -p stj-vec-server -- --config config.toml &

# Em outro:
curl -X POST http://localhost:8421/search \
  -H 'Content-Type: application/json' \
  -d '{"query": "responsabilidade civil dano moral"}'
```

Expected: erro (server usa NoopEmbedder, busca vetorial nao funciona sem embedder real).
Nota: busca via server requer implementar ModalEmbedder ou OllamaEmbedder para queries online. Isso e task futura -- o objetivo aqui e validar que os embeddings foram gerados e importados corretamente.

Alternativa: verificar via SQLite diretamente:
```bash
sqlite3 db/stj-vec.db "SELECT COUNT(*) FROM vec_chunks;"
```

---

## Divisao de Trabalho (Agent Team)

| Task | Owner | Descricao |
|------|-------|-----------|
| 1. Download modelo | backend-developer | Script Modal + executar download |
| 2. Modal Class | backend-developer | embed.py completo |
| 3. export-chunks | eu (orquestrador) | Rust exporter + subcomando CLI |
| 4. import-embeddings | eu (orquestrador) | Rust importer + parser .npz |
| 5. Teste e2e | manual com usuario | Validar pipeline completo |

**Tasks 1-2 (backend-developer) e tasks 3-4 (eu) sao independentes e executam em paralelo.**

---

## Ordem de Execucao

| Task | Depende de | Estimativa |
|------|-----------|------------|
| 1. Download modelo | - | 10min |
| 2. Modal Class | 1 | 20min |
| 3. export-chunks | - | 15min |
| 4. import-embeddings | - | 20min |
| 5. Teste e2e | 2, 3, 4 | 30min (manual) |

**Total estimado: ~45min (paralelo) + 30min (teste manual)**
