"""Modal Class para gerar embeddings BGE-M3 via TEI (Text Embeddings Inference).

H200 ($4.54/h) com TEI hopper: batch=1024, 141GB HBM3e, 4.8TB/s bandwidth.
BGE-M3 568M params (~1GB FP16).
"""
import modal
import json

app = modal.App("stj-vec-embed")

volume_models = modal.Volume.from_name("stj-vec-models")
volume_data = modal.Volume.from_name("stj-vec-data", create_if_missing=True)

GPU_CONFIG = "H200"
PORT = 8000
BATCH_SIZE = 4096  # H200 tem 141GB, satura GPU

LAUNCH_FLAGS = [
    "--model-id", "/models/bge-m3",  # pre-carregado no Volume stj-vec-models
    "--port", str(PORT),
    "--max-batch-tokens", "2097152",  # 4096*512
    "--max-client-batch-size", "4096",
    "--dtype", "float16",
    "--payload-limit", "50000000",  # 50MB
]


def spawn_server():
    """Inicia TEI server e espera ficar pronto."""
    import subprocess
    import socket

    process = subprocess.Popen(["text-embeddings-router"] + LAUNCH_FLAGS)
    while True:
        try:
            socket.create_connection(("127.0.0.1", PORT), timeout=1).close()
            print("TEI server ready!")
            return process
        except (socket.timeout, ConnectionRefusedError):
            retcode = process.poll()
            if retcode is not None:
                raise RuntimeError(f"TEI server exited with code {retcode}")


# Imagem TEI com GPU arch 89 (Ada Lovelace = L4)
# Modelo ja esta no Volume stj-vec-models em /bge-m3/
tei_image = (
    modal.Image.from_registry(
        "ghcr.io/huggingface/text-embeddings-inference:hopper-1.7",
        add_python="3.11",
    )
    .dockerfile_commands("ENTRYPOINT []")
    .pip_install("httpx>=0.27.0", "numpy>=1.24.0")
)


@app.cls(
    image=tei_image,
    gpu=GPU_CONFIG,
    volumes={
        "/models": volume_models,
        "/data": volume_data,
    },
    timeout=3600,
    scaledown_window=120,
)
class Embedder:
    @modal.enter()
    def start_server(self):
        import httpx
        self.process = spawn_server()
        self.client = httpx.Client(
            base_url=f"http://127.0.0.1:{PORT}", timeout=120.0
        )

    @modal.exit()
    def stop_server(self):
        self.process.terminate()

    @modal.method()
    def embed_source(self, source_name: str, batch_size: int = 4096) -> dict:
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

        # Embeddar em batches via TEI HTTP
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = self.client.post("/embed", json={"inputs": batch})
            resp.raise_for_status()
            all_embeddings.extend(resp.json())

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
        resp = self.client.post("/embed", json={"inputs": [text]})
        resp.raise_for_status()
        return resp.json()[0]


@app.function(
    volumes={"/data": volume_data},
    timeout=120,
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
    batch_size: int = BATCH_SIZE,
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
