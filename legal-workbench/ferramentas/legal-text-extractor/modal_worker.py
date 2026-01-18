"""
Modal Worker - GPU-accelerated PDF extraction using Marker.

This module provides serverless GPU processing for PDF extraction.
Deploy to Modal and call via API or CLI.

Setup:
    pip install modal
    modal token new
    modal deploy modal_worker.py

Usage (CLI):
    modal run modal_worker.py --pdf-path /path/to/document.pdf

Usage (API):
    from modal_worker import extract_pdf
    result = extract_pdf.remote(pdf_bytes)

Cost: ~$3.50/hour (A100 80GB GPU), billed per second
Performance: 3-5x faster than A10G for Marker extraction
"""

import modal

# Define the Modal app
app = modal.App("lw-marker-extractor")

# Define container image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "tesseract-ocr",
        "tesseract-ocr-por",
        "poppler-utils",
        "libgl1",
        "libglib2.0-0",
    )
    .pip_install(
        "marker-pdf>=1.0.0",
        "torch>=2.0.0",
        "pdfplumber>=0.10.0",
    )
)

# Volume for caching Hugging Face models (persist between runs)
model_cache = modal.Volume.from_name("marker-model-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu="A100-80GB",  # 80GB VRAM - max performance for Marker
    timeout=1800,  # 30 minutes max
    volumes={"/cache": model_cache},
    secrets=[],  # Add secrets here if needed
)
def extract_pdf(pdf_bytes: bytes, force_ocr: bool = False) -> dict:
    """
    Extract text from PDF using Marker with GPU acceleration.

    Args:
        pdf_bytes: Raw PDF file content
        force_ocr: Force OCR on all pages (default: auto-detect)

    Returns:
        dict with keys:
            - text: Extracted text content
            - pages: Number of pages processed
            - native_pages: Pages with native text
            - ocr_pages: Pages that required OCR
            - processing_time: Time in seconds
    """
    import os
    import time
    import tempfile

    # Set cache directories
    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["TORCH_HOME"] = "/cache/torch"
    os.environ["MARKER_CACHE_DIR"] = "/cache/marker"

    # Import after setting env vars
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    start_time = time.time()

    # Save PDF to temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        pdf_path = f.name

    try:
        # Load models (cached after first run)
        print("Loading Marker models...")
        models = create_model_dict()
        print(f"Models loaded in {time.time() - start_time:.1f}s")

        # Configure converter
        converter = PdfConverter(
            artifact_dict=models,
            config={
                "output_format": "markdown",
                "paginate_output": True,
                "disable_image_extraction": True,
                "force_ocr": force_ocr,
            }
        )

        # Process PDF
        print(f"Processing PDF...")
        convert_start = time.time()
        rendered = converter(pdf_path)
        text, images, metadata = text_from_rendered(rendered)
        convert_time = time.time() - convert_start

        total_time = time.time() - start_time

        # Extract page counts from metadata
        pages = metadata.get("pages", 0)
        native_pages = metadata.get("native_pages", pages)
        ocr_pages = metadata.get("ocr_pages", 0)

        print(f"Extraction complete: {len(text):,} chars, {pages} pages in {convert_time:.1f}s")

        return {
            "text": text,
            "pages": pages,
            "native_pages": native_pages,
            "ocr_pages": ocr_pages,
            "chars": len(text),
            "processing_time": round(total_time, 2),
            "convert_time": round(convert_time, 2),
        }

    finally:
        # Cleanup temp file
        os.unlink(pdf_path)


@app.function(
    image=image,
    gpu="A100-80GB",  # 80GB VRAM - full performance
    timeout=600,  # 10 minutes for initial model download (~1.5GB)
    volumes={"/cache": model_cache},
)
def warmup_models():
    """
    Pre-load models to cache. Run once after deploy to speed up first extraction.

    Usage:
        modal run modal_worker.py::warmup_models
    """
    import os
    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["TORCH_HOME"] = "/cache/torch"
    os.environ["MARKER_CACHE_DIR"] = "/cache/marker"

    from marker.models import create_model_dict

    print("Warming up Marker models...")
    models = create_model_dict()
    print("Models cached successfully!")
    return {"status": "ok", "models_loaded": len(models)}


@app.function(image=image, gpu="A100-80GB", timeout=30)
def health_check():
    """
    Verify GPU is available and working.

    Usage:
        modal run modal_worker.py::health_check
    """
    import torch

    cuda_available = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_available else None
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9 if cuda_available else 0

    return {
        "cuda_available": cuda_available,
        "device_name": device_name,
        "vram_gb": round(vram_gb, 1),
    }


@app.local_entrypoint()
def main(pdf_path: str = None, warmup: bool = False, health: bool = False):
    """
    CLI entrypoint for testing.

    Examples:
        modal run modal_worker.py --health
        modal run modal_worker.py --warmup
        modal run modal_worker.py --pdf-path /path/to/doc.pdf
    """
    if health:
        result = health_check.remote()
        print(f"Health check: {result}")
        return

    if warmup:
        result = warmup_models.remote()
        print(f"Warmup complete: {result}")
        return

    if pdf_path:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        print(f"Sending {len(pdf_bytes):,} bytes to Modal...")
        result = extract_pdf.remote(pdf_bytes)

        print("\n" + "=" * 60)
        print(f"RESULT")
        print("=" * 60)
        print(f"Pages: {result['pages']} ({result['native_pages']} native, {result['ocr_pages']} OCR)")
        print(f"Chars: {result['chars']:,}")
        print(f"Time: {result['processing_time']}s (convert: {result['convert_time']}s)")
        print("\nText preview:")
        print(result['text'][:500] + "..." if len(result['text']) > 500 else result['text'])
    else:
        print("Usage:")
        print("  modal run modal_worker.py --health")
        print("  modal run modal_worker.py --warmup")
        print("  modal run modal_worker.py --pdf-path /path/to/document.pdf")
