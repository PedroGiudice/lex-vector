"""Modal Class para gerar embeddings BGE-M3 em batch."""
import modal
import json

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
    gpu="L4",
    volumes={
        "/models": volume_models,
        "/data": volume_data,
    },
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=3600,
    scaledown_window=120,
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
        import os

        input_path = f"/data/chunks/{source_name}.jsonl"
        out_npz = f"/data/embeddings/{source_name}.npz"
        out_json = f"/data/embeddings/{source_name}.json"

        chunk_ids = []
        texts = []
        with open(input_path, "r") as f:
            for line in f:
                obj = json.loads(line)
                chunk_ids.append(obj["id"])
                texts.append(obj["content"])

        if not texts:
            return {"source": source_name, "count": 0, "status": "empty"}

        all_embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        embeddings = np.array(all_embeddings, dtype=np.float32)

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

    return sorted(chunk_sources - done_sources)


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
