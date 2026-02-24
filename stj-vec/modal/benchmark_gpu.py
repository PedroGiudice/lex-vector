"""Benchmark real: mesma source em configs diferentes de GPU/batch.

Mede emb/s, VRAM real, e calcula emb/$ para cada config.
Usa 1 source pendente como amostra representativa.
"""
import modal
import json
import time

app = modal.App("stj-vec-benchmark")

volume_models = modal.Volume.from_name("stj-vec-models")
volume_data = modal.Volume.from_name("stj-vec-data")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0.0",
        "torch>=2.0.0",
        "numpy>=1.24.0",
    )
)

# Custo por GPU por hora (Modal pricing fev/2026)
GPU_COST_PER_HOUR = {
    "L4": 0.59,
    "A10G": 1.10,
    "A100-40GB": 2.10,
    "A100-80GB": 2.50,
}

CONFIGS = [
    {"gpu": "L4", "batch_sizes": [64, 128, 256]},
    {"gpu": "A10G", "batch_sizes": [64, 128, 256]},
    {"gpu": "A100-80GB", "batch_sizes": [512, 1024, 2048]},
]


@app.function(
    volumes={"/data": volume_data},
    timeout=60,
)
def pick_benchmark_source() -> str:
    """Escolhe 1 source pendente de tamanho medio (~10-20K chunks)."""
    import os

    chunks_dir = "/data/chunks"
    embeddings_dir = "/data/embeddings"

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
    if not pending:
        raise RuntimeError("Nenhum source pendente para benchmark")

    # Usar file size como proxy (evita contar linhas, que e lento no Volume)
    sizes = []
    for s in pending:
        path = f"{chunks_dir}/{s}.jsonl"
        sizes.append((s, os.path.getsize(path)))

    sizes.sort(key=lambda x: x[1])
    mid = len(sizes) // 2
    chosen = sizes[mid]
    print(f"Benchmark source: {chosen[0]} ({chosen[1] / 1e6:.1f}MB)")
    print(f"Total pendentes: {len(pending)}")
    return chosen[0]


@app.cls(
    image=image,
    gpu="L4",
    volumes={"/models": volume_models, "/data": volume_data},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=600,
    scaledown_window=60,
)
class BenchL4:
    @modal.enter()
    def load(self):
        import torch
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("/models/bge-m3", device="cuda",
                                          model_kwargs={"torch_dtype": torch.float16})
        self.model.eval()

    @modal.method()
    def run(self, source: str, batch_size: int) -> dict:
        return _bench(self.model, source, batch_size, "L4")


@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/models": volume_models, "/data": volume_data},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=600,
    scaledown_window=60,
)
class BenchA10G:
    @modal.enter()
    def load(self):
        import torch
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("/models/bge-m3", device="cuda",
                                          model_kwargs={"torch_dtype": torch.float16})
        self.model.eval()

    @modal.method()
    def run(self, source: str, batch_size: int) -> dict:
        return _bench(self.model, source, batch_size, "A10G")


@app.cls(
    image=image,
    gpu="A100-80GB",
    volumes={"/models": volume_models, "/data": volume_data},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=600,
    scaledown_window=60,
)
class BenchA100:
    @modal.enter()
    def load(self):
        import torch
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("/models/bge-m3", device="cuda",
                                          model_kwargs={"torch_dtype": torch.float16})
        self.model.eval()

    @modal.method()
    def run(self, source: str, batch_size: int) -> dict:
        return _bench(self.model, source, batch_size, "A100-80GB")


def _bench(model, source: str, batch_size: int, gpu_name: str) -> dict:
    """Core benchmark: encode, mede tempo e VRAM."""
    import torch
    import numpy as np

    input_path = f"/data/chunks/{source}.jsonl"
    texts = []
    with open(input_path, "r") as f:
        for line in f:
            obj = json.loads(line)
            texts.append(obj["content"])

    n = len(texts)

    # Warmup (1 batch)
    warmup_n = min(batch_size, n)
    model.encode(texts[:warmup_n], batch_size=batch_size,
                 normalize_embeddings=True, convert_to_numpy=True)
    torch.cuda.synchronize()

    # VRAM apos warmup
    vram_alloc = torch.cuda.memory_allocated() / 1e9
    vram_reserved = torch.cuda.memory_reserved() / 1e9
    vram_total = torch.cuda.get_device_properties(0).total_memory / 1e9

    # Benchmark real
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    model.encode(texts, batch_size=batch_size, show_progress_bar=False,
                 normalize_embeddings=True, convert_to_numpy=True)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - t0

    emb_per_sec = n / elapsed
    cost_h = GPU_COST_PER_HOUR.get(gpu_name, 0)
    emb_per_dollar = (emb_per_sec * 3600) / cost_h if cost_h > 0 else 0
    vram_pct = (vram_reserved / vram_total) * 100

    result = {
        "gpu": gpu_name,
        "batch_size": batch_size,
        "chunks": n,
        "elapsed_s": round(elapsed, 1),
        "emb_per_sec": round(emb_per_sec, 1),
        "emb_per_dollar": round(emb_per_dollar),
        "vram_alloc_gb": round(vram_alloc, 1),
        "vram_reserved_gb": round(vram_reserved, 1),
        "vram_total_gb": round(vram_total, 1),
        "vram_usage_pct": round(vram_pct, 1),
    }
    print(f"  {gpu_name} batch={batch_size}: {emb_per_sec:.0f} emb/s, "
          f"VRAM {vram_pct:.0f}% ({vram_reserved:.1f}/{vram_total:.1f}GB), "
          f"{emb_per_dollar:.0f} emb/$")
    return result


@app.local_entrypoint()
def main():
    source = pick_benchmark_source.remote()
    print(f"\n{'='*60}")
    print(f"BENCHMARK: source={source}")
    print(f"{'='*60}\n")

    bench_classes = {
        "L4": BenchL4(),
        "A10G": BenchA10G(),
        "A100-80GB": BenchA100(),
    }

    all_results = []

    for cfg in CONFIGS:
        gpu = cfg["gpu"]
        bench = bench_classes[gpu]
        for bs in cfg["batch_sizes"]:
            print(f"[{gpu} batch={bs}] Running...")
            try:
                result = bench.run.remote(source, bs)
                all_results.append(result)
            except Exception as e:
                print(f"  FAILED: {e}")
                all_results.append({
                    "gpu": gpu, "batch_size": bs, "error": str(e)
                })

    # Tabela final
    print(f"\n{'='*60}")
    print("RESULTADOS")
    print(f"{'='*60}")
    print(f"{'GPU':<12} {'Batch':>6} {'emb/s':>8} {'VRAM%':>6} {'VRAM GB':>10} {'emb/$':>10}")
    print("-" * 60)
    for r in all_results:
        if "error" in r:
            print(f"{r['gpu']:<12} {r['batch_size']:>6}   FAILED: {r['error'][:30]}")
        else:
            print(f"{r['gpu']:<12} {r['batch_size']:>6} {r['emb_per_sec']:>8.0f} "
                  f"{r['vram_usage_pct']:>5.0f}% "
                  f"{r['vram_reserved_gb']:>4.1f}/{r['vram_total_gb']:.1f} "
                  f"{r['emb_per_dollar']:>10,}")

    # Melhor config
    valid = [r for r in all_results if "error" not in r]
    if valid:
        best = max(valid, key=lambda r: r["emb_per_dollar"])
        print(f"\nMELHOR emb/$: {best['gpu']} batch={best['batch_size']} "
              f"({best['emb_per_dollar']:,} emb/$, {best['emb_per_sec']:.0f} emb/s)")

        # Estimativa para 579 sources restantes (~9M chunks estimados)
        remaining_chunks = 9_000_000  # estimativa conservadora
        hours = remaining_chunks / best["emb_per_sec"] / 3600
        cost = hours * GPU_COST_PER_HOUR.get(best["gpu"], 0)
        print(f"Estimativa 579 sources (~{remaining_chunks/1e6:.0f}M chunks): "
              f"{hours:.1f}h x 1 container = ${cost:.2f}")
        print(f"Com 10 containers: ~{hours/10:.1f}h = ~${cost:.2f}")
