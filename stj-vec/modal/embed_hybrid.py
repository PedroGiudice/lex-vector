"""Modal Class para gerar embeddings BGE-M3 dense + sparse via FlagEmbedding.

H200 ($4.54/h) com FlagEmbedding: dense (1024d) + sparse (lexical weights)
numa unica passada. Elimina necessidade de re-embedding pro sparse.

Output por source:
  /embeddings/{source}.npz       -- dense embeddings (N x 1024, float32)
  /embeddings/{source}.json      -- chunk_ids alinhados
  /embeddings/{source}.sparse.json -- sparse weights [{token: weight, ...}, ...]
"""
import modal
import json

app = modal.App("stj-vec-embed-hybrid")

volume_models = modal.Volume.from_name("stj-vec-models")
volume_data = modal.Volume.from_name("stj-vec-data", create_if_missing=True)

GPU_CONFIG = "H200"
BATCH_SIZE = 1024  # FlagEmbedding e mais pesado que TEI, comecar conservador
MIN_SPARSE_WEIGHT = 0.01  # descartar pesos abaixo disso pra controlar tamanho

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "FlagEmbedding>=1.2.11",
        "torch>=2.1.0",
        "numpy>=1.24.0",
    )
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
    def embed_source(self, source_name: str, batch_size: int = BATCH_SIZE) -> dict:
        """Processa 1 source JSONL, gera .npz + .json + .sparse.json no Volume."""
        import numpy as np
        import os
        import time
        import torch

        input_path = f"/data/chunks/{source_name}.jsonl"
        out_npz = f"/data/embeddings/{source_name}.npz"
        out_json = f"/data/embeddings/{source_name}.json"
        out_sparse = f"/data/embeddings/{source_name}.sparse.json"

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

        # FlagEmbedding: dense + sparse numa chamada
        output = self.model.encode(
            texts,
            batch_size=batch_size,
            max_length=512,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,  # skip ColBERT, nao precisamos
        )

        # Dense embeddings
        dense = np.array(output["dense_vecs"], dtype=np.float32)

        # Sparse weights: converter token_ids (int) pra string e filtrar pesos baixos
        sparse_list = []
        for weights_dict in output["lexical_weights"]:
            filtered = {
                str(k): float(v)
                for k, v in weights_dict.items()
                if float(v) >= MIN_SPARSE_WEIGHT
            }
            sparse_list.append(filtered)

        os.makedirs("/data/embeddings", exist_ok=True)

        np.savez_compressed(out_npz, embeddings=dense)
        with open(out_json, "w") as f:
            json.dump(chunk_ids, f)
        with open(out_sparse, "w") as f:
            json.dump(sparse_list, f)

        volume_data.commit()

        elapsed = time.perf_counter() - t0
        vram_peak_gb = torch.cuda.max_memory_allocated() / (1024**3)
        vram_total_gb = torch.cuda.get_device_properties(0).total_mem / (1024**3)
        emb_per_sec = len(chunk_ids) / elapsed if elapsed > 0 else 0

        print(f"[CALIBRATION] source={source_name} chunks={len(chunk_ids)} "
              f"batch={batch_size} max_length=512")
        print(f"[CALIBRATION] VRAM peak: {vram_peak_gb:.1f}GB / {vram_total_gb:.1f}GB "
              f"({vram_peak_gb/vram_total_gb*100:.0f}%)")
        print(f"[CALIBRATION] Time: {elapsed:.1f}s | Throughput: {emb_per_sec:.0f} emb/s")

        return {
            "source": source_name,
            "count": len(chunk_ids),
            "dense_shape": list(dense.shape),
            "sparse_avg_tokens": round(
                sum(len(s) for s in sparse_list) / len(sparse_list), 1
            ),
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
def list_pending_sources() -> list[str]:
    """Lista sources que nao tem .sparse.json (precisam de re-embedding hybrid)."""
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
    # Pendente = nao tem .sparse.json (mesmo que tenha .npz do dense-only)
    done_sources = {
        f.replace(".sparse.json", "")
        for f in os.listdir(embeddings_dir)
        if f.endswith(".sparse.json")
    } if os.path.exists(embeddings_dir) else set()

    return sorted(chunk_sources - done_sources)


@app.local_entrypoint()
def main(
    source: str = "",
    all_pending: bool = False,
    batch_size: int = BATCH_SIZE,
):
    """Entrypoint: processar 1 source ou todos pendentes (hybrid dense+sparse)."""
    embedder = HybridEmbedder()

    if source:
        result = embedder.embed_source.remote(source, batch_size)
        print(f"Done: {result}")
    elif all_pending:
        sources = list_pending_sources.remote()
        print(f"{len(sources)} sources pendentes (hybrid)")
        if not sources:
            return

        results = []
        for result in embedder.embed_source.map(
            sources,
            kwargs={"batch_size": batch_size},
        ):
            print(
                f"  {result['source']}: {result['count']} chunks, "
                f"sparse avg {result.get('sparse_avg_tokens', '?')} tokens -> "
                f"{result['status']}"
            )
            results.append(result)

        total = sum(r["count"] for r in results)
        print(f"\nTotal: {total} embeddings (dense+sparse) para {len(results)} sources")
    else:
        print("Uso: modal run embed_hybrid.py --source 202203")
        print("  ou: modal run embed_hybrid.py --all-pending")
