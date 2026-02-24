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
    secrets=[modal.Secret.from_name("huggingface-secret")],
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
