"""
Marker GPU Benchmark - Custom Image para Modal Notebook
========================================================
Deploy: modal deploy marker_benchmark_image.py
Notebook: Sidebar -> Compute/Kernel -> Custom -> marker_benchmark_env

Imagem com Marker + modelos baked. A GPU e selecionada na sidebar do notebook.
"""

import modal

APP_NAME = "marker-gpu-benchmark"
CACHE_DIR = "/pretrained_models"
HF_CACHE_DIR = f"{CACHE_DIR}/huggingface"


def download_marker_models():
    """Baixa modelos do Marker durante build. Ficam permanentes na imagem."""
    import os

    os.environ["HF_HOME"] = HF_CACHE_DIR
    os.environ["TORCH_HOME"] = f"{CACHE_DIR}/torch"

    print("BUILD: Baixando modelos Marker...")
    from marker.models import create_model_dict

    models = create_model_dict()
    print(f"BUILD: {len(models)} modelos Marker baixados e baked.")


image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "tesseract-ocr",
        "tesseract-ocr-por",
        "poppler-utils",
        "libgl1",
        "libglib2.0-0",
        "git",
    )
    .run_commands(
        "pip install uv",
        "uv pip install --system --compile-bytecode "
        "marker-pdf torch pdfplumber "
        "pandas matplotlib tqdm ipywidgets",
    )
    .env(
        {
            "HF_HOME": HF_CACHE_DIR,
            "TORCH_HOME": f"{CACHE_DIR}/torch",
            "MARKER_CACHE_DIR": f"{CACHE_DIR}/marker",
            "TOKENIZERS_PARALLELISM": "false",
            "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
        }
    )
    .run_function(download_marker_models)
)

app = modal.App(APP_NAME)
benchmark_vol = modal.Volume.from_name("marker-benchmark-data", create_if_missing=True)


@app.function(
    image=image,
    gpu="any",
    timeout=14400,
    volumes={"/mnt/marker-benchmark-data": benchmark_vol},
)
def marker_benchmark_env():
    """
    Funcao ancora - registra a imagem no sistema Modal.
    Selecionar no Notebook: Compute/Kernel -> Custom -> marker_benchmark_env
    GPU: selecionar na sidebar (T4, L4, A10G, A100, H100)
    """
    pass
