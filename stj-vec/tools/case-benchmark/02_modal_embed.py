"""Modal: embeda JSONL via FlagEmbedding BGE-M3 (dense + sparse).

Usa A10G ($1.10/h) com FlagEmbedding. Gera ambos dense (.npz) e sparse (.sparse.json)
numa unica chamada. Volume: case-knowledge-data.

Fluxo:
  1. Upload JSONL:   modal volume put case-knowledge-data /tmp/case-bench/chunks.jsonl chunks/
  2. Rodar:          modal run 02_modal_embed.py --source chunks
  3. Download:       modal volume get case-knowledge-data embeddings/ /tmp/case-bench/embeddings/

Output por source:
  embeddings/{source}.npz         -- dense embeddings (N, 1024) float32
  embeddings/{source}.json        -- chunk_ids ordenados
  embeddings/{source}.sparse.json -- lexical weights [{token_id: weight, ...}, ...]
"""
import modal
import json
import time

app = modal.App("case-knowledge-embed")

volume_models = modal.Volume.from_name("stj-vec-models")
volume_data = modal.Volume.from_name("case-knowledge-data", create_if_missing=True)

GPU_CONFIG = "L4"
BATCH_SIZE = 128
MIN_SPARSE_WEIGHT = 0.01

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "FlagEmbedding>=1.2.11",
        "transformers>=4.40.0,<4.46.0",
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
        import numpy as np
        import os
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

        output = self.model.encode(
            texts,
            batch_size=batch_size,
            max_length=512,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
        )

        elapsed = time.perf_counter() - t0
        vram_peak_gb = torch.cuda.max_memory_allocated() / (1024**3)
        vram_total_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)

        # Dense
        embeddings = np.array(output["dense_vecs"], dtype=np.float32)

        # Sparse
        sparse_list = []
        for weights_dict in output["lexical_weights"]:
            filtered = {
                str(k): float(v)
                for k, v in weights_dict.items()
                if float(v) >= MIN_SPARSE_WEIGHT
            }
            sparse_list.append(filtered)

        os.makedirs("/data/embeddings", exist_ok=True)
        np.savez_compressed(out_npz, embeddings=embeddings)
        with open(out_json, "w") as f:
            json.dump(chunk_ids, f)
        with open(out_sparse, "w") as f:
            json.dump(sparse_list, f)

        volume_data.commit()

        emb_per_sec = len(chunk_ids) / elapsed if elapsed > 0 else 0

        print(f"[INFO] source={source_name} chunks={len(chunk_ids)} "
              f"batch={batch_size} max_length=512")
        print(f"[INFO] VRAM peak: {vram_peak_gb:.1f}GB / {vram_total_gb:.1f}GB "
              f"({vram_peak_gb/vram_total_gb*100:.0f}%)")
        print(f"[INFO] Time: {elapsed:.1f}s | Throughput: {emb_per_sec:.0f} emb/s")

        return {
            "source": source_name,
            "count": len(chunk_ids),
            "dense_shape": list(embeddings.shape),
            "sparse_avg_tokens": round(
                sum(len(s) for s in sparse_list) / len(sparse_list), 1
            ),
            "embed_time_secs": round(elapsed, 2),
            "vram_peak_gb": round(vram_peak_gb, 2),
            "vram_pct": round(vram_peak_gb / vram_total_gb * 100, 1),
            "emb_per_sec": round(emb_per_sec, 1),
            "status": "done",
        }


@app.local_entrypoint()
def main(source: str = "", batch_size: int = BATCH_SIZE):
    if not source:
        print("Uso: modal run 02_modal_embed.py --source chunks")
        return

    t0 = time.time()
    embedder = HybridEmbedder()
    result = embedder.embed_source.remote(source, batch_size)
    total = time.time() - t0

    print(f"\n--- Resultado ---")
    print(f"Source:        {result['source']}")
    print(f"Chunks:        {result['count']}")
    print(f"Dense shape:   {result['dense_shape']}")
    print(f"Sparse avg:    {result['sparse_avg_tokens']} tokens/chunk")
    print(f"Embed time:    {result['embed_time_secs']}s (GPU)")
    print(f"VRAM:          {result['vram_peak_gb']}GB ({result['vram_pct']}%)")
    print(f"Throughput:    {result['emb_per_sec']} emb/s")
    print(f"Total time:    {total:.1f}s (incl. cold start)")
    print(f"Status:        {result['status']}")

    gpu_per_hour = 0.80  # L4
    cost = (total / 3600) * gpu_per_hour
    print(f"Custo est.:    ${cost:.4f} (T4 @ ${gpu_per_hour}/h)")
