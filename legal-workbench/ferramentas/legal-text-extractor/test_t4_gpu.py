"""Test Marker on T4 GPU (16GB VRAM)"""
import modal

app = modal.App("test-t4-marker")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("tesseract-ocr", "tesseract-ocr-por", "poppler-utils", "libgl1", "libglib2.0-0")
    .pip_install("marker-pdf>=1.0.0", "torch>=2.0.0")
)

model_cache = modal.Volume.from_name("marker-model-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu="T4",  # 16GB VRAM
    timeout=600,
    volumes={"/cache": model_cache},
)
def test_marker_t4():
    """Test if Marker loads and runs on T4"""
    import os
    import torch
    import time

    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["TORCH_HOME"] = "/cache/torch"

    start = time.time()

    # Check GPU
    device = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9

    print(f"GPU: {device}")
    print(f"VRAM: {vram:.1f} GB")

    # Try loading Marker models
    print("Loading Marker models...")
    from marker.models import create_model_dict
    models = create_model_dict()

    load_time = time.time() - start
    print(f"Models loaded in {load_time:.1f}s")

    return {
        "gpu": device,
        "vram_gb": round(vram, 1),
        "models_loaded": len(models),
        "load_time_s": round(load_time, 1),
        "status": "OK"
    }


@app.local_entrypoint()
def main():
    result = test_marker_t4.remote()
    print(f"\nResult: {result}")
