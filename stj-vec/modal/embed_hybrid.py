"""Modal Class para gerar embeddings BGE-M3 via FlagEmbedding (dense + sparse).

Output por source:
  /embeddings/{source}.npz          -- dense embeddings (float32, 1024d)
  /embeddings/{source}.json         -- chunk IDs (lista de hex strings)
  /embeddings/{source}.sparse.json  -- sparse weights [{token: weight, ...}, ...]
"""

import json

import modal

app = modal.App("stj-vec-embed-hybrid")

volume_models = modal.Volume.from_name("stj-vec-models")
volume_data = modal.Volume.from_name("stj-vec-data", create_if_missing=True)

GPU_CONFIG = "H200"
BATCH_SIZE = 128  # BGE-M3 sparse e compute-bound: batch maior nao aumenta throughput
MIN_SPARSE_WEIGHT = 0.01  # descartar pesos abaixo disso pra controlar tamanho

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "FlagEmbedding>=1.2.11",
    "transformers>=4.40.0,<4.46.0",
    "torch>=2.1.0",
    "numpy>=1.24.0",
)


@app.cls(
    image=image,
    gpu=GPU_CONFIG,
    volumes={
        "/models": volume_models,
        "/data": volume_data,
    },
    timeout=3600,
    scaledown_window=120,
    max_containers=1,
)
class HybridEmbedder:
    @modal.enter()
    def load_model(self):
        from FlagEmbedding import BGEM3FlagModel

        print("Carregando BGE-M3 via FlagEmbedding (dense + sparse)...")
        self.model = BGEM3FlagModel(
            "/models/bge-m3",
            use_fp16=True,
            device="cuda",
        )
        print("Modelo carregado.")

    @modal.method()
    def embed_source(self, source_name: str, batch_size: int = BATCH_SIZE,
                     dense: bool = True, sparse: bool = True) -> dict:
        """Processa 1 source JSONL, gera dense (.npz + .json) e/ou sparse (.sparse.json)."""
        import os
        import time

        import numpy as np
        import torch

        input_path = f"/data/chunks/{source_name}.jsonl"

        chunk_ids = []
        texts = []
        with open(input_path, "r") as f:
            for line in f:
                obj = json.loads(line)
                chunk_ids.append(obj["id"])
                texts.append(obj["content"])

        if not texts:
            return {"source": source_name, "count": 0, "status": "empty"}

        torch.cuda.reset_peak_memory_stats()
        t0 = time.perf_counter()

        output = self.model.encode(
            texts,
            batch_size=batch_size,
            max_length=512,
            return_dense=dense,
            return_sparse=sparse,
            return_colbert_vecs=False,
        )

        os.makedirs("/data/embeddings", exist_ok=True)

        # Dense: salvar .npz + .json (IDs)
        if dense and "dense_vecs" in output:
            embeddings = np.array(output["dense_vecs"], dtype=np.float32)
            np.savez_compressed(
                f"/data/embeddings/{source_name}.npz", embeddings=embeddings
            )
            with open(f"/data/embeddings/{source_name}.json", "w") as f:
                json.dump(chunk_ids, f)

        # Sparse: salvar .sparse.json
        if sparse and "lexical_weights" in output:
            sparse_list = []
            for weights_dict in output["lexical_weights"]:
                filtered = {
                    str(k): float(v)
                    for k, v in weights_dict.items()
                    if float(v) >= MIN_SPARSE_WEIGHT
                }
                sparse_list.append(filtered)
            with open(f"/data/embeddings/{source_name}.sparse.json", "w") as f:
                json.dump(sparse_list, f)

        # NAO fazer commit aqui -- commit concorrente de multiplos containers
        # causa contention no volume e perda de dados (last-write-wins).
        # O commit e feito em batch no final via flush_volume().

        elapsed = time.perf_counter() - t0
        vram_peak_gb = torch.cuda.max_memory_allocated() / (1024**3)
        vram_total_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        emb_per_sec = len(chunk_ids) / elapsed if elapsed > 0 else 0

        print(
            f"[CALIBRATION] source={source_name} chunks={len(chunk_ids)} "
            f"batch={batch_size} max_length=512 dense={dense} sparse={sparse}"
        )
        print(
            f"[CALIBRATION] VRAM peak: {vram_peak_gb:.1f}GB / {vram_total_gb:.1f}GB "
            f"({vram_peak_gb / vram_total_gb * 100:.0f}%)"
        )
        print(
            f"[CALIBRATION] Time: {elapsed:.1f}s | Throughput: {emb_per_sec:.0f} emb/s"
        )

        return {
            "source": source_name,
            "count": len(chunk_ids),
            "dense": dense,
            "sparse": sparse,
            "status": "done",
            "vram_peak_gb": round(vram_peak_gb, 2),
            "vram_total_gb": round(vram_total_gb, 2),
            "vram_pct": round(vram_peak_gb / vram_total_gb * 100, 1),
            "elapsed_s": round(elapsed, 1),
            "emb_per_sec": round(emb_per_sec, 1),
        }

    @modal.method()
    def embed_single(self, text: str) -> dict:
        """Embed de texto unico (para queries em tempo real)."""
        import numpy as np

        output = self.model.encode(
            [text],
            max_length=512,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )
        return {
            "dense": output["dense_vecs"][0].astype(np.float32).tolist(),
            "sparse": {
                str(k): float(v)
                for k, v in output["lexical_weights"][0].items()
                if float(v) >= MIN_SPARSE_WEIGHT
            },
        }


@app.function(
    volumes={"/data": volume_data},
    timeout=120,
)
def flush_volume() -> str:
    """Commit do volume apos todos os containers terminarem de escrever."""
    volume_data.commit()
    return "committed"


@app.function(
    volumes={"/data": volume_data},
    timeout=120,
)
def list_pending_sources() -> list[str]:
    """Lista sources que nao tem dense+sparse completo."""
    import os

    chunks_dir = "/data/chunks"
    embeddings_dir = "/data/embeddings"

    if not os.path.exists(chunks_dir):
        return []

    chunk_sources = {
        f.replace(".jsonl", "") for f in os.listdir(chunks_dir) if f.endswith(".jsonl")
    }

    if not os.path.exists(embeddings_dir):
        return sorted(chunk_sources)

    emb_files = set(os.listdir(embeddings_dir))
    pending = []
    for src in chunk_sources:
        has_dense = f"{src}.npz" in emb_files and f"{src}.json" in emb_files
        has_sparse = f"{src}.sparse.json" in emb_files
        if not (has_dense and has_sparse):
            pending.append(src)

    return sorted(pending)


@app.local_entrypoint()
def main(
    source: str = "",
    all_pending: bool = False,
    batch_size: int = BATCH_SIZE,
):
    """Entrypoint: processar 1 source ou todos pendentes (dense + sparse)."""
    embedder = HybridEmbedder()

    if source:
        result = embedder.embed_source.remote(source, batch_size)
        flush_volume.remote()
        print(f"Done: {result}")
    elif all_pending:
        sources = list_pending_sources.remote()
        print(f"{len(sources)} sources pendentes (dense + sparse)")
        if not sources:
            return

        handles = []
        for s in sources:
            handle = embedder.embed_source.spawn(s, batch_size)
            handles.append(handle)
        print(f"Despachadas {len(handles)} chamadas via .spawn()")

        results = []
        total_handles = len(handles)
        for i, handle in enumerate(handles, 1):
            result = handle.get()
            print(
                f"  [{i}/{total_handles}] {result['source']}: {result['count']} chunks "
                f"-> {result['status']}"
            )
            results.append(result)

        flush_volume.remote()
        print("Volume committed.")

        total = sum(r["count"] for r in results)
        print(f"\nTotal: {total} embeddings para {len(results)} sources")
    else:
        print("Uso: modal run embed_hybrid.py --source 202203")
        print("  ou: modal run embed_hybrid.py --all-pending")
