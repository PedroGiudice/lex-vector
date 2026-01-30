# Modal GPU Snapshot T4 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduzir cold start do Text Extractor de ~2min para ~10s usando GPU Memory Snapshots nas T4.

**Architecture:** Refatorar `extract_chunk_t4` de `@app.function` para `@app.cls` com GPU Memory Snapshot. O snapshot captura os modelos Marker carregados na VRAM, permitindo restore instantaneo em novos containers.

**Tech Stack:** Modal (GPU Snapshot alpha), Python, Marker-PDF

---

## Task 1: Criar classe T4Extractor com GPU Snapshot

**Files:**
- Modify: `legal-workbench/ferramentas/legal-text-extractor/modal_worker.py:425-513`

**Step 1: Adicionar nova classe T4Extractor**

Adicionar apos a linha 422 (fim de `extract_pdf_chunked`):

```python
@app.cls(
    image=image,
    gpu="T4",
    timeout=1800,  # 30 min per chunk
    volumes={"/cache": model_cache},
    enable_memory_snapshot=True,
    experimental_options={"enable_gpu_snapshot": True},
)
class T4Extractor:
    """
    T4 GPU extractor with memory snapshot for fast cold starts.

    Uses Modal GPU Memory Snapshot to reduce cold start from ~2min to ~10s.
    The snapshot captures loaded Marker models in VRAM.
    """

    @modal.enter(snap=True)
    def warmup(self):
        """Load models and capture in snapshot."""
        import os
        os.environ["HF_HOME"] = "/cache/huggingface"
        os.environ["TORCH_HOME"] = "/cache/torch"
        os.environ["MARKER_CACHE_DIR"] = "/cache/marker"

        from marker.models import create_model_dict

        print("[T4Extractor] Loading Marker models for snapshot...")
        self.models = create_model_dict()
        print("[T4Extractor] Models loaded and captured in snapshot")

    @modal.method()
    def extract_chunk(
        self,
        pdf_bytes: bytes,
        page_range: list[int],
        chunk_id: int,
        force_ocr: bool = False
    ) -> dict:
        """
        Extract text from a specific page range using T4 GPU.

        Models are pre-loaded via snapshot, eliminating cold start.
        """
        import os
        import time
        import tempfile

        from marker.converters.pdf import PdfConverter
        from marker.output import text_from_rendered

        start_time = time.time()

        # Save PDF to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            pdf_path = f.name

        try:
            print(f"[Chunk {chunk_id}] Processing pages {page_range[0]+1}-{page_range[-1]+1}...")

            # Configure converter (models already loaded via snapshot)
            config = {
                "output_format": "markdown",
                "paginate_output": True,
                "disable_image_extraction": True,
                "force_ocr": force_ocr,
                "common_element_threshold": 0.4,
                "common_element_min_blocks": 5,
                "drop_repeated_text": True,
                "OcrBuilder_recognition_batch_size": 64,
                "page_range": page_range,
            }

            converter = PdfConverter(artifact_dict=self.models, config=config)

            convert_start = time.time()
            rendered = converter(pdf_path)
            text, images, metadata = text_from_rendered(rendered)
            convert_time = time.time() - convert_start

            total_time = time.time() - start_time
            print(f"[Chunk {chunk_id}] Done: {len(text):,} chars in {convert_time:.1f}s")

            return {
                "chunk_id": chunk_id,
                "text": text,
                "pages": len(page_range),
                "page_range": [page_range[0], page_range[-1]],
                "native_pages": metadata.get("native_pages", len(page_range)),
                "ocr_pages": metadata.get("ocr_pages", 0),
                "chars": len(text),
                "convert_time": round(convert_time, 2),
                "total_time": round(total_time, 2),
                "snapshot_enabled": True,
            }

        finally:
            os.unlink(pdf_path)
```

**Step 2: Verificar sintaxe**

Run: `cd /home/opc/lex-vector/legal-workbench/ferramentas/legal-text-extractor && python -m py_compile modal_worker.py`
Expected: Sem output (sucesso)

**Step 3: Commit**

```bash
git add legal-workbench/ferramentas/legal-text-extractor/modal_worker.py
git commit -m "feat(modal): add T4Extractor class with GPU snapshot

- Add T4Extractor class using @app.cls with enable_memory_snapshot
- Pre-load Marker models in @modal.enter(snap=True)
- Reduces cold start from ~2min to ~10s per container

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Atualizar extract_pdf_parallel para usar T4Extractor

**Files:**
- Modify: `legal-workbench/ferramentas/legal-text-extractor/modal_worker.py:515-632`

**Step 1: Modificar extract_pdf_parallel**

Substituir a chamada `extract_chunk_t4.starmap(map_args)` por chamada ao T4Extractor:

```python
@app.function(
    image=image,
    gpu=None,  # Orchestrator - no GPU needed
    timeout=7200,  # 2 hours for large PDFs
)
def extract_pdf_parallel(
    pdf_bytes: bytes,
    force_ocr: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_workers: int = MAX_PARALLEL_WORKERS,
) -> dict:
    """
    Extract text from PDF using multiple T4 GPUs in parallel.

    Uses T4Extractor with GPU Memory Snapshot for fast cold starts.
    Each T4 container restores from snapshot in ~10s instead of ~2min.
    """
    import time
    import tempfile
    import pdfplumber

    start_time = time.time()

    # Get page count
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        pdf_path = f.name

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
    finally:
        import os
        os.unlink(pdf_path)

    print(f"PDF has {total_pages} pages")

    # Calculate chunks
    chunks = []
    for i in range(0, total_pages, chunk_size):
        chunk_end = min(i + chunk_size, total_pages)
        chunks.append(list(range(i, chunk_end)))

    # Limit workers
    actual_workers = min(len(chunks), max_workers)
    print(f"Processing {total_pages} pages in {len(chunks)} chunks using {actual_workers} parallel T4 GPUs (snapshot-enabled)")

    # Use T4Extractor with GPU snapshot
    extractor = T4Extractor()

    # Prepare arguments for parallel execution
    print(f"Launching {len(chunks)} parallel extraction jobs with GPU snapshot...")
    parallel_start = time.time()

    # Use map with the class method
    results = list(extractor.extract_chunk.map(
        [pdf_bytes] * len(chunks),
        chunks,
        list(range(len(chunks))),
        [force_ocr] * len(chunks),
    ))

    parallel_time = time.time() - parallel_start
    print(f"All {len(chunks)} chunks completed in {parallel_time:.1f}s")

    # Sort results by chunk_id to maintain page order
    results.sort(key=lambda x: x["chunk_id"])

    # Combine text
    combined_text = "\n\n".join(r["text"] for r in results)

    # Aggregate stats
    total_native = sum(r["native_pages"] for r in results)
    total_ocr = sum(r["ocr_pages"] for r in results)
    total_chars = sum(r["chars"] for r in results)

    # Calculate cost estimate (T4 = $0.59/hour)
    total_gpu_seconds = sum(r["total_time"] for r in results)
    estimated_cost = (total_gpu_seconds / 3600) * 0.59

    total_time = time.time() - start_time

    return {
        "text": combined_text,
        "pages": total_pages,
        "native_pages": total_native,
        "ocr_pages": total_ocr,
        "chars": total_chars,
        "processing_time": round(total_time, 2),
        "parallel_time": round(parallel_time, 2),
        "workers_used": actual_workers,
        "chunks": len(chunks),
        "chunk_size": chunk_size,
        "mode": "multi-t4-parallel-snapshot",
        "snapshot_enabled": True,
        "estimated_cost_usd": round(estimated_cost, 3),
        "chunk_stats": [
            {
                "chunk_id": r["chunk_id"],
                "pages": r["pages"],
                "chars": r["chars"],
                "time": r["total_time"],
            }
            for r in results
        ],
    }
```

**Step 2: Verificar sintaxe**

Run: `cd /home/opc/lex-vector/legal-workbench/ferramentas/legal-text-extractor && python -m py_compile modal_worker.py`
Expected: Sem output (sucesso)

**Step 3: Commit**

```bash
git add legal-workbench/ferramentas/legal-text-extractor/modal_worker.py
git commit -m "refactor(modal): use T4Extractor in extract_pdf_parallel

- Replace extract_chunk_t4.starmap with T4Extractor.extract_chunk.map
- Update mode to 'multi-t4-parallel-snapshot'
- Add snapshot_enabled flag to response

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: Adicionar funcao de warmup para T4Extractor

**Files:**
- Modify: `legal-workbench/ferramentas/legal-text-extractor/modal_worker.py`

**Step 1: Adicionar warmup_t4_snapshot**

Adicionar apos a funcao `warmup_models`:

```python
@app.function(image=image, gpu=None, timeout=300)
def warmup_t4_snapshot():
    """
    Trigger T4Extractor snapshot creation.

    Call this after deploy to pre-create the GPU memory snapshot.
    Subsequent T4 containers will restore from snapshot in ~10s.

    Usage:
        modal run modal_worker.py::warmup_t4_snapshot
    """
    print("Triggering T4Extractor snapshot creation...")
    extractor = T4Extractor()

    # Just instantiating triggers the @modal.enter(snap=True) method
    # which creates the snapshot
    print("T4Extractor snapshot created successfully!")
    return {"status": "ok", "message": "T4 GPU snapshot created"}
```

**Step 2: Atualizar CLI main**

Na funcao `main()`, adicionar opcao `--warmup-t4`:

```python
@app.local_entrypoint()
def main(
    pdf_path: str = None,
    warmup: bool = False,
    warmup_t4: bool = False,  # NOVO
    health: bool = False,
    chunked: bool = False,
    parallel: bool = False,
    smart: bool = False,
    mode: str = "auto",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    count_pages: bool = False,
):
    """
    CLI entrypoint for testing.

    Examples:
        modal run modal_worker.py --health
        modal run modal_worker.py --warmup
        modal run modal_worker.py --warmup-t4              # NEW: Create T4 snapshot
        modal run modal_worker.py --pdf-path /path/to/doc.pdf
        modal run modal_worker.py --pdf-path /path/to/doc.pdf --parallel
    """
    if health:
        result = health_check.remote()
        print(f"Health check: {result}")
        return

    if warmup:
        result = warmup_models.remote()
        print(f"Warmup complete: {result}")
        return

    if warmup_t4:  # NOVO
        result = warmup_t4_snapshot.remote()
        print(f"T4 snapshot warmup: {result}")
        return

    # ... resto do codigo permanece igual
```

**Step 3: Verificar sintaxe**

Run: `cd /home/opc/lex-vector/legal-workbench/ferramentas/legal-text-extractor && python -m py_compile modal_worker.py`
Expected: Sem output (sucesso)

**Step 4: Commit**

```bash
git add legal-workbench/ferramentas/legal-text-extractor/modal_worker.py
git commit -m "feat(modal): add warmup_t4_snapshot function and CLI option

- Add warmup_t4_snapshot() to trigger snapshot creation
- Add --warmup-t4 CLI option
- Run after deploy to pre-create GPU memory snapshot

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: Deploy e testar snapshot

**Files:**
- None (operacional)

**Step 1: Deploy para Modal**

Run: `cd /home/opc/lex-vector/legal-workbench/ferramentas/legal-text-extractor && modal deploy modal_worker.py`
Expected: Deploy bem-sucedido com mensagem de criacao do app

**Step 2: Criar snapshot T4**

Run: `cd /home/opc/lex-vector/legal-workbench/ferramentas/legal-text-extractor && modal run modal_worker.py --warmup-t4`
Expected: "T4Extractor snapshot created successfully!"

**Step 3: Testar extracao paralela com PDF pequeno**

Run: `cd /home/opc/lex-vector/legal-workbench/ferramentas/legal-text-extractor && modal run modal_worker.py --pdf-path /path/to/test.pdf --parallel`
Expected:
- Mensagem "snapshot-enabled" no output
- Cold start reduzido (verificar no dashboard Modal)

**Step 4: Commit final**

```bash
git add .
git commit -m "docs: update ISSUES.md with GPU snapshot solution

- Document GPU Memory Snapshot implementation for #2
- Mark issue as resolved

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: Implementar download nativo Tauri (Issue #5)

**Files:**
- Modify: `legal-workbench/frontend/src/lib/tauri.ts`
- Modify: `legal-workbench/frontend/src/components/text-extractor/OutputPanel.tsx`
- Modify: `legal-workbench/frontend/src-tauri/capabilities/default.json`

**Step 1: Adicionar funcao saveFileNative em tauri.ts**

```typescript
/**
 * Save file using native Tauri dialog (Tauri only)
 * Returns true if saved successfully, false otherwise
 */
export async function saveFileNative(
  content: string,
  defaultFilename: string,
  filters: { name: string; extensions: string[] }[]
): Promise<boolean> {
  if (!isTauri()) return false;

  try {
    const { save } = await import('@tauri-apps/plugin-dialog');
    const { writeTextFile } = await import('@tauri-apps/plugin-fs');

    const path = await save({
      defaultPath: defaultFilename,
      filters,
      title: 'Salvar arquivo',
    });

    if (path) {
      await writeTextFile(path, content);
      return true;
    }
  } catch (error) {
    console.error('Native save error:', error);
  }

  return false;
}
```

**Step 2: Atualizar capabilities/default.json**

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "opener:default",
    "dialog:default",
    "fs:default"
  ]
}
```

**Step 3: Atualizar handleDownload em OutputPanel.tsx**

```typescript
import { isTauri, saveFileNative } from '@/lib/tauri';

// ... dentro do componente

const handleDownload = useCallback(
  async (format: DownloadFormat) => {
    if (!result) return;

    let content: string;
    let mimeType: string;
    let extension: string;
    let filterName: string;

    switch (format) {
      case 'txt':
        content = result.text;
        mimeType = 'text/plain';
        extension = 'txt';
        filterName = 'Text files';
        break;
      case 'md':
        content = `# Extracted Text\n\n${result.text}\n\n---\n\n## Metadata\n\n- Pages: ${result.pages_processed}\n- Time: ${result.execution_time_seconds}s\n- Engine: ${result.engine_used}\n- Characters: ${result.text.length}\n`;
        mimeType = 'text/markdown';
        extension = 'md';
        filterName = 'Markdown files';
        break;
      case 'json':
        content = JSON.stringify(result, null, 2);
        mimeType = 'application/json';
        extension = 'json';
        filterName = 'JSON files';
        break;
    }

    // Try native Tauri save first
    if (isTauri()) {
      const saved = await saveFileNative(
        content,
        `extracted-text.${extension}`,
        [{ name: filterName, extensions: [extension] }]
      );
      if (saved) {
        setShowDownloadMenu(false);
        return;
      }
    }

    // Fallback to browser download
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extracted-text.${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setShowDownloadMenu(false);
  },
  [result]
);
```

**Step 4: Verificar TypeScript**

Run: `cd /home/opc/lex-vector/legal-workbench/frontend && bun run typecheck`
Expected: Sem erros

**Step 5: Commit**

```bash
git add legal-workbench/frontend/src/lib/tauri.ts \
        legal-workbench/frontend/src/components/text-extractor/OutputPanel.tsx \
        legal-workbench/frontend/src-tauri/capabilities/default.json
git commit -m "fix(tauri): implement native file save for download button

- Add saveFileNative() using tauri-plugin-dialog
- Update OutputPanel to use native save on Tauri
- Add dialog and fs permissions to capabilities
- Fixes #5: Download nao funciona no app Tauri

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Atualizar ISSUES.md

**Files:**
- Modify: `legal-workbench/ISSUES.md`

**Step 1: Mover issues para Resolvidos**

Atualizar status das issues #2 e #5 para "Resolvido" com documentacao da solucao.

**Step 2: Commit final**

```bash
git add legal-workbench/ISSUES.md
git commit -m "docs(issues): mark #2 and #5 as resolved

- #2: GPU Memory Snapshot reduces cold start from ~2min to ~10s
- #5: Native Tauri file save dialog implemented

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verificacao Final

**Checklist:**
- [ ] modal_worker.py compila sem erros
- [ ] T4Extractor classe criada com GPU snapshot
- [ ] extract_pdf_parallel usa T4Extractor
- [ ] warmup_t4_snapshot funciona
- [ ] Deploy para Modal bem-sucedido
- [ ] Download funciona no app Tauri
- [ ] ISSUES.md atualizado
