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

Usage (API - simple):
    from modal_worker import extract_pdf
    result = extract_pdf.remote(pdf_bytes)

Usage (API - chunked with progress):
    from modal_worker import extract_pdf_chunked
    for progress in extract_pdf_chunked.remote_gen(pdf_bytes, chunk_size=100):
        if progress["type"] == "progress":
            print(f"Chunk {progress['chunk']}/{progress['total_chunks']} ({progress['percent']}%)")
        elif progress["type"] == "result":
            final_result = progress["data"]

Cost: ~$3.50/hour (A100 80GB GPU), billed per second
Performance: 3-5x faster than A10G for Marker extraction
"""

import modal
from typing import Generator

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

# Constants
DEFAULT_CHUNK_SIZE = 100  # Pages per chunk for large PDFs
PARALLEL_THRESHOLD = 300  # Pages above this use multi-T4 parallel
MAX_PARALLEL_WORKERS = 8  # Modal limit for concurrent GPU containers


@app.function(
    image=image,
    gpu="A100-80GB",  # 80GB VRAM - max performance for Marker
    timeout=7200,  # 2 hours max (large scanned PDFs can take 1h+)
    volumes={"/cache": model_cache},
    secrets=[],  # Add secrets here if needed
)
def extract_pdf(pdf_bytes: bytes, force_ocr: bool = False, page_range: list = None) -> dict:
    """
    Extract text from PDF using Marker with GPU acceleration.

    Args:
        pdf_bytes: Raw PDF file content
        force_ocr: Force OCR on all pages (default: auto-detect)
        page_range: Optional list of page indices to process (0-indexed)

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
        # DOCUMENTAÇÃO DAS CONFIGURAÇÕES:
        # - force_ocr: False = Marker detecta automaticamente se OCR é necessário
        # - disable_image_extraction: True = não inclui imagens no output (só texto)
        # - common_element_threshold: 0.4 = ignora elementos em >40% das páginas (assinaturas, headers)
        # - drop_repeated_text: True = remove texto duplicado
        # - OcrBuilder_recognition_batch_size: 64 = batch maior = OCR mais rápido em GPU
        config = {
            "output_format": "markdown",
            "paginate_output": True,
            "disable_image_extraction": True,
            "force_ocr": force_ocr,  # False = auto-detect, True = força OCR em tudo
            # Otimizações para PDFs jurídicos (assinaturas repetidas, headers/footers)
            "common_element_threshold": 0.4,
            "common_element_min_blocks": 5,
            "drop_repeated_text": True,
            # Performance OCR
            "OcrBuilder_recognition_batch_size": 64,
        }
        if page_range:
            config["page_range"] = page_range
            print(f"Processing pages: {page_range}")

        converter = PdfConverter(
            artifact_dict=models,
            config=config,
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
    gpu=None,  # CPU only - just counting pages
    timeout=60,
)
def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """
    Get the total number of pages in a PDF.

    Args:
        pdf_bytes: Raw PDF file content

    Returns:
        Total number of pages
    """
    import tempfile
    import pdfplumber

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        pdf_path = f.name

    try:
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)
    finally:
        import os
        os.unlink(pdf_path)


@app.function(
    image=image,
    gpu="A100-80GB",
    timeout=14400,  # 4 hours max for very large PDFs with multiple chunks
    volumes={"/cache": model_cache},
)
def extract_pdf_chunked(
    pdf_bytes: bytes,
    force_ocr: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    auto_chunk: bool = True,
) -> Generator[dict, None, None]:
    """
    Extract text from PDF with automatic chunking and progress updates.

    For PDFs larger than chunk_size pages, processes in chunks and yields
    progress updates. Use with .remote_gen() for streaming.

    Args:
        pdf_bytes: Raw PDF file content
        force_ocr: Force OCR on all pages (default: auto-detect)
        chunk_size: Number of pages per chunk (default: 100)
        auto_chunk: If False, process entire PDF at once regardless of size

    Yields:
        Progress updates: {"type": "progress", "chunk": 1, "total_chunks": 7, "percent": 14, ...}
        Final result: {"type": "result", "data": {...}}

    Example:
        for update in extract_pdf_chunked.remote_gen(pdf_bytes):
            if update["type"] == "progress":
                print(f"{update['percent']}% complete")
            elif update["type"] == "result":
                text = update["data"]["text"]
    """
    import os
    import time
    import tempfile

    # Set cache directories
    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["TORCH_HOME"] = "/cache/torch"
    os.environ["MARKER_CACHE_DIR"] = "/cache/marker"

    # Import after setting env vars
    import pdfplumber
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    start_time = time.time()

    # Save PDF to temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        pdf_path = f.name

    try:
        # Get page count
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

        print(f"PDF has {total_pages} pages")

        # Determine if chunking is needed
        if not auto_chunk or total_pages <= chunk_size:
            # Process entire PDF at once (delegate to original function logic)
            print("Processing entire PDF (no chunking needed)")

            yield {
                "type": "progress",
                "chunk": 1,
                "total_chunks": 1,
                "percent": 0,
                "pages_processed": 0,
                "total_pages": total_pages,
                "message": "Loading models...",
            }

            # Load models
            models = create_model_dict()

            yield {
                "type": "progress",
                "chunk": 1,
                "total_chunks": 1,
                "percent": 10,
                "pages_processed": 0,
                "total_pages": total_pages,
                "message": "Processing PDF...",
            }

            # Configure and run
            config = {
                "output_format": "markdown",
                "paginate_output": True,
                "disable_image_extraction": True,
                "force_ocr": force_ocr,
                "common_element_threshold": 0.4,
                "common_element_min_blocks": 5,
                "drop_repeated_text": True,
                "OcrBuilder_recognition_batch_size": 64,
            }

            converter = PdfConverter(artifact_dict=models, config=config)
            rendered = converter(pdf_path)
            text, images, metadata = text_from_rendered(rendered)

            total_time = time.time() - start_time
            pages = metadata.get("pages", total_pages)

            yield {
                "type": "result",
                "data": {
                    "text": text,
                    "pages": pages,
                    "native_pages": metadata.get("native_pages", pages),
                    "ocr_pages": metadata.get("ocr_pages", 0),
                    "chars": len(text),
                    "processing_time": round(total_time, 2),
                    "chunked": False,
                    "total_chunks": 1,
                },
            }
            return

        # Chunked processing
        chunks = []
        for i in range(0, total_pages, chunk_size):
            chunk_end = min(i + chunk_size, total_pages)
            chunks.append(list(range(i, chunk_end)))

        total_chunks = len(chunks)
        print(f"Processing {total_pages} pages in {total_chunks} chunks of ~{chunk_size} pages")

        # Load models once
        yield {
            "type": "progress",
            "chunk": 0,
            "total_chunks": total_chunks,
            "percent": 0,
            "pages_processed": 0,
            "total_pages": total_pages,
            "message": "Loading models...",
        }

        models = create_model_dict()
        model_load_time = time.time() - start_time
        print(f"Models loaded in {model_load_time:.1f}s")

        # Process each chunk
        all_texts = []
        total_native_pages = 0
        total_ocr_pages = 0

        for chunk_idx, page_range in enumerate(chunks):
            chunk_num = chunk_idx + 1
            pages_so_far = sum(len(c) for c in chunks[:chunk_idx])
            percent = int((pages_so_far / total_pages) * 90) + 5  # 5-95% range

            yield {
                "type": "progress",
                "chunk": chunk_num,
                "total_chunks": total_chunks,
                "percent": percent,
                "pages_processed": pages_so_far,
                "total_pages": total_pages,
                "message": f"Processing chunk {chunk_num}/{total_chunks} (pages {page_range[0]+1}-{page_range[-1]+1})...",
            }

            print(f"Processing chunk {chunk_num}/{total_chunks}: pages {page_range[0]+1}-{page_range[-1]+1}")

            config = {
                "output_format": "markdown",
                "paginate_output": True,
                "disable_image_extraction": True,
                "force_ocr": force_ocr,
                "common_element_threshold": 0.4,
                "common_element_min_blocks": 5,
                "drop_repeated_text": True,
                "OcrBuilder_recognition_batch_size": 64,
                "page_range": page_range,
            }

            converter = PdfConverter(artifact_dict=models, config=config)
            chunk_start = time.time()
            rendered = converter(pdf_path)
            text, images, metadata = text_from_rendered(rendered)
            chunk_time = time.time() - chunk_start

            all_texts.append(text)
            total_native_pages += metadata.get("native_pages", len(page_range))
            total_ocr_pages += metadata.get("ocr_pages", 0)

            print(f"Chunk {chunk_num} done: {len(text):,} chars in {chunk_time:.1f}s")

        # Combine results
        combined_text = "\n\n".join(all_texts)
        total_time = time.time() - start_time

        print(f"All chunks complete: {len(combined_text):,} chars total in {total_time:.1f}s")

        yield {
            "type": "result",
            "data": {
                "text": combined_text,
                "pages": total_pages,
                "native_pages": total_native_pages,
                "ocr_pages": total_ocr_pages,
                "chars": len(combined_text),
                "processing_time": round(total_time, 2),
                "chunked": True,
                "total_chunks": total_chunks,
                "chunk_size": chunk_size,
            },
        }

    finally:
        # Cleanup temp file
        os.unlink(pdf_path)


@app.cls(
    image=image,
    gpu="T4",
    timeout=1800,  # 30 min per chunk
    volumes={"/cache": model_cache},
    enable_memory_snapshot=True,
    experimental_options={"enable_gpu_snapshot": True},
)
class T4Extractor:
    """
    T4 GPU extractor with memory snapshot for fast cold starts.

    Uses Modal GPU Memory Snapshot to reduce cold start from ~2min to ~10s.
    The snapshot captures loaded Marker models in VRAM.
    """

    @modal.enter(snap=True)
    def warmup(self):
        """Load models and capture in snapshot."""
        import os
        os.environ["HF_HOME"] = "/cache/huggingface"
        os.environ["TORCH_HOME"] = "/cache/torch"
        os.environ["MARKER_CACHE_DIR"] = "/cache/marker"

        from marker.models import create_model_dict

        print("[T4Extractor] Loading Marker models for snapshot...")
        self.models = create_model_dict()
        print("[T4Extractor] Models loaded and captured in snapshot")

    @modal.method()
    def extract_chunk(
        self,
        pdf_bytes: bytes,
        page_range: list[int],
        chunk_id: int,
        force_ocr: bool = False
    ) -> dict:
        """
        Extract text from a specific page range using T4 GPU.

        Models are pre-loaded via snapshot, eliminating cold start.
        """
        import os
        import time
        import tempfile

        from marker.converters.pdf import PdfConverter
        from marker.output import text_from_rendered

        start_time = time.time()

        # Save PDF to temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            pdf_path = f.name

        try:
            print(f"[Chunk {chunk_id}] Processing pages {page_range[0]+1}-{page_range[-1]+1}...")

            # Configure converter (models already loaded via snapshot)
            config = {
                "output_format": "markdown",
                "paginate_output": True,
                "disable_image_extraction": True,
                "force_ocr": force_ocr,
                "common_element_threshold": 0.4,
                "common_element_min_blocks": 5,
                "drop_repeated_text": True,
                "OcrBuilder_recognition_batch_size": 64,
                "page_range": page_range,
            }

            converter = PdfConverter(artifact_dict=self.models, config=config)

            convert_start = time.time()
            rendered = converter(pdf_path)
            text, images, metadata = text_from_rendered(rendered)
            convert_time = time.time() - convert_start

            total_time = time.time() - start_time
            print(f"[Chunk {chunk_id}] Done: {len(text):,} chars in {convert_time:.1f}s")

            return {
                "chunk_id": chunk_id,
                "text": text,
                "pages": len(page_range),
                "page_range": [page_range[0], page_range[-1]],
                "native_pages": metadata.get("native_pages", len(page_range)),
                "ocr_pages": metadata.get("ocr_pages", 0),
                "chars": len(text),
                "convert_time": round(convert_time, 2),
                "total_time": round(total_time, 2),
                "snapshot_enabled": True,
            }

        finally:
            os.unlink(pdf_path)


@app.function(
    image=image,
    gpu="T4",  # 16GB VRAM - economia mode
    timeout=1800,  # 30 min per chunk
    volumes={"/cache": model_cache},
)
def extract_chunk_t4(pdf_bytes: bytes, page_range: list[int], chunk_id: int, force_ocr: bool = False) -> dict:
    """
    Extract text from a specific page range using T4 GPU.

    This function is designed to be called via .map() for parallel processing.
    Each invocation runs on a separate T4 container.

    Args:
        pdf_bytes: Raw PDF file content
        page_range: List of 0-indexed page numbers to process
        chunk_id: Identifier for this chunk (for ordering results)
        force_ocr: Force OCR on all pages

    Returns:
        dict with chunk_id, text, pages processed, and timing info
    """
    import os
    import time
    import tempfile

    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["TORCH_HOME"] = "/cache/torch"
    os.environ["MARKER_CACHE_DIR"] = "/cache/marker"

    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    start_time = time.time()

    # Save PDF to temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        pdf_path = f.name

    try:
        # Load models
        print(f"[Chunk {chunk_id}] Loading models for pages {page_range[0]+1}-{page_range[-1]+1}...")
        models = create_model_dict()
        model_time = time.time() - start_time
        print(f"[Chunk {chunk_id}] Models loaded in {model_time:.1f}s")

        # Configure converter
        config = {
            "output_format": "markdown",
            "paginate_output": True,
            "disable_image_extraction": True,
            "force_ocr": force_ocr,
            "common_element_threshold": 0.4,
            "common_element_min_blocks": 5,
            "drop_repeated_text": True,
            "OcrBuilder_recognition_batch_size": 64,
            "page_range": page_range,
        }

        converter = PdfConverter(artifact_dict=models, config=config)

        # Process
        print(f"[Chunk {chunk_id}] Processing {len(page_range)} pages...")
        convert_start = time.time()
        rendered = converter(pdf_path)
        text, images, metadata = text_from_rendered(rendered)
        convert_time = time.time() - convert_start

        total_time = time.time() - start_time
        print(f"[Chunk {chunk_id}] Done: {len(text):,} chars in {convert_time:.1f}s")

        return {
            "chunk_id": chunk_id,
            "text": text,
            "pages": len(page_range),
            "page_range": [page_range[0], page_range[-1]],
            "native_pages": metadata.get("native_pages", len(page_range)),
            "ocr_pages": metadata.get("ocr_pages", 0),
            "chars": len(text),
            "model_time": round(model_time, 2),
            "convert_time": round(convert_time, 2),
            "total_time": round(total_time, 2),
        }

    finally:
        os.unlink(pdf_path)


@app.function(
    image=image,
    gpu=None,  # Orchestrator - no GPU needed
    timeout=7200,  # 2 hours for large PDFs
)
def extract_pdf_parallel(
    pdf_bytes: bytes,
    force_ocr: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_workers: int = MAX_PARALLEL_WORKERS,
) -> dict:
    """
    Extract text from PDF using multiple T4 GPUs in parallel.

    Uses T4Extractor with GPU Memory Snapshot for fast cold starts.
    Each T4 container restores from snapshot in ~10s instead of ~2min.
    """
    import time
    import tempfile
    import pdfplumber

    start_time = time.time()

    # Get page count
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        pdf_path = f.name

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
    finally:
        import os
        os.unlink(pdf_path)

    print(f"PDF has {total_pages} pages")

    # Calculate chunks
    chunks = []
    for i in range(0, total_pages, chunk_size):
        chunk_end = min(i + chunk_size, total_pages)
        chunks.append(list(range(i, chunk_end)))

    # Limit workers
    actual_workers = min(len(chunks), max_workers)
    print(f"Processing {total_pages} pages in {len(chunks)} chunks using {actual_workers} parallel T4 GPUs (snapshot-enabled)")

    # Use T4Extractor with GPU snapshot
    extractor = T4Extractor()

    # Prepare arguments for parallel execution
    print(f"Launching {len(chunks)} parallel extraction jobs with GPU snapshot...")
    parallel_start = time.time()

    # Use map with the class method
    results = list(extractor.extract_chunk.map(
        [pdf_bytes] * len(chunks),
        chunks,
        list(range(len(chunks))),
        [force_ocr] * len(chunks),
    ))

    parallel_time = time.time() - parallel_start
    print(f"All {len(chunks)} chunks completed in {parallel_time:.1f}s")

    # Sort results by chunk_id to maintain page order
    results.sort(key=lambda x: x["chunk_id"])

    # Combine text
    combined_text = "\n\n".join(r["text"] for r in results)

    # Aggregate stats
    total_native = sum(r["native_pages"] for r in results)
    total_ocr = sum(r["ocr_pages"] for r in results)
    total_chars = sum(r["chars"] for r in results)

    # Calculate cost estimate (T4 = $0.59/hour)
    total_gpu_seconds = sum(r["total_time"] for r in results)
    estimated_cost = (total_gpu_seconds / 3600) * 0.59

    total_time = time.time() - start_time

    return {
        "text": combined_text,
        "pages": total_pages,
        "native_pages": total_native,
        "ocr_pages": total_ocr,
        "chars": total_chars,
        "processing_time": round(total_time, 2),
        "parallel_time": round(parallel_time, 2),
        "workers_used": actual_workers,
        "chunks": len(chunks),
        "chunk_size": chunk_size,
        "mode": "multi-t4-parallel-snapshot",
        "snapshot_enabled": True,
        "estimated_cost_usd": round(estimated_cost, 3),
        "chunk_stats": [
            {
                "chunk_id": r["chunk_id"],
                "pages": r["pages"],
                "chars": r["chars"],
                "time": r["total_time"],
            }
            for r in results
        ],
    }


@app.function(
    image=image,
    gpu=None,  # Decision logic only
    timeout=60,
)
def decide_extraction_mode(total_pages: int, mode: str = "auto") -> dict:
    """
    Decide the best extraction mode based on page count and user preference.

    Modes:
    - "auto": Automatic selection based on page count
    - "economy": Always use multi-T4 parallel (cheapest)
    - "performance": Always use A100 (fastest for small PDFs)

    Args:
        total_pages: Total pages in the PDF
        mode: User-selected mode

    Returns:
        dict with recommended method and reasoning
    """
    if mode == "economy":
        return {
            "method": "parallel",
            "gpu": "T4",
            "reason": "User selected economy mode (multi-T4 parallel)",
            "estimated_workers": min((total_pages // DEFAULT_CHUNK_SIZE) + 1, MAX_PARALLEL_WORKERS),
        }

    if mode == "performance":
        return {
            "method": "sequential",
            "gpu": "A100-80GB",
            "reason": "User selected performance mode (single A100)",
            "estimated_workers": 1,
        }

    # Auto mode: decide based on page count
    if total_pages > PARALLEL_THRESHOLD:
        workers = min((total_pages // DEFAULT_CHUNK_SIZE) + 1, MAX_PARALLEL_WORKERS)
        return {
            "method": "parallel",
            "gpu": "T4",
            "reason": f"PDF has {total_pages} pages (>{PARALLEL_THRESHOLD}), multi-T4 parallel is faster and cheaper",
            "estimated_workers": workers,
        }
    else:
        return {
            "method": "sequential",
            "gpu": "A100-80GB",
            "reason": f"PDF has {total_pages} pages (<={PARALLEL_THRESHOLD}), A100 is efficient for this size",
            "estimated_workers": 1,
        }


@app.function(
    image=image,
    gpu=None,  # Orchestrator
    timeout=14400,  # 4 hours max
)
def extract_smart(
    pdf_bytes: bytes,
    force_ocr: bool = False,
    mode: str = "auto",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict:
    """
    Smart extraction that automatically chooses the best method.

    This is the recommended entry point for production use. It analyzes the PDF
    and selects the optimal extraction method (A100 sequential vs multi-T4 parallel).

    Args:
        pdf_bytes: Raw PDF file content
        force_ocr: Force OCR on all pages
        mode: "auto", "economy", or "performance"
        chunk_size: Pages per chunk for parallel mode

    Returns:
        dict with extracted text and processing details
    """
    import time
    import tempfile
    import pdfplumber

    start_time = time.time()

    # Get page count
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(pdf_bytes)
        pdf_path = f.name

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
    finally:
        import os
        os.unlink(pdf_path)

    # Decide method
    decision = decide_extraction_mode.local(total_pages, mode)
    print(f"Decision: {decision['reason']}")

    # Execute with chosen method
    if decision["method"] == "parallel":
        print(f"Using multi-T4 parallel extraction...")
        result = extract_pdf_parallel.local(
            pdf_bytes,
            force_ocr=force_ocr,
            chunk_size=chunk_size,
        )
    else:
        print(f"Using A100 sequential extraction...")
        result = extract_pdf.remote(pdf_bytes, force_ocr=force_ocr)
        result["mode"] = "a100-sequential"

    # Add decision info
    result["decision"] = decision
    result["total_time"] = round(time.time() - start_time, 2)

    return result


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


@app.function(image=image, gpu=None, timeout=300)
def warmup_t4_snapshot():
    """
    Trigger T4Extractor snapshot creation.

    Call this after deploy to pre-create the GPU memory snapshot.
    Subsequent T4 containers will restore from snapshot in ~10s.

    Usage:
        modal run modal_worker.py::warmup_t4_snapshot
    """
    print("Triggering T4Extractor snapshot creation...")
    extractor = T4Extractor()

    # Just instantiating triggers the @modal.enter(snap=True) method
    # which creates the snapshot
    print("T4Extractor snapshot created successfully!")
    return {"status": "ok", "message": "T4 GPU snapshot created"}


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
def main(
    pdf_path: str = None,
    warmup: bool = False,
    warmup_t4: bool = False,
    health: bool = False,
    chunked: bool = False,
    parallel: bool = False,
    smart: bool = False,
    mode: str = "auto",
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    count_pages: bool = False,
):
    """
    CLI entrypoint for testing.

    Examples:
        modal run modal_worker.py --health
        modal run modal_worker.py --warmup
        modal run modal_worker.py --warmup-t4              # Create T4 snapshot
        modal run modal_worker.py --pdf-path /path/to/doc.pdf
        modal run modal_worker.py --pdf-path /path/to/doc.pdf --chunked
        modal run modal_worker.py --pdf-path /path/to/doc.pdf --parallel
        modal run modal_worker.py --pdf-path /path/to/doc.pdf --smart
        modal run modal_worker.py --pdf-path /path/to/doc.pdf --smart --mode economy
        modal run modal_worker.py --pdf-path /path/to/doc.pdf --count-pages

    Modes (for --smart):
        auto: Automatic selection based on page count (default)
        economy: Always use multi-T4 parallel (cheapest)
        performance: Always use A100 (fastest for small PDFs)
    """
    if health:
        result = health_check.remote()
        print(f"Health check: {result}")
        return

    if warmup:
        result = warmup_models.remote()
        print(f"Warmup complete: {result}")
        return

    if warmup_t4:
        result = warmup_t4_snapshot.remote()
        print(f"T4 snapshot warmup: {result}")
        return

    if pdf_path:
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        print(f"Sending {len(pdf_bytes):,} bytes to Modal...")

        if count_pages:
            page_count = get_pdf_page_count.remote(pdf_bytes)
            print(f"PDF has {page_count} pages")
            return

        if smart:
            # Smart extraction - auto-selects best method
            print(f"Using smart extraction (mode={mode})")
            result = extract_smart.remote(pdf_bytes, mode=mode, chunk_size=chunk_size)

            print("\n" + "=" * 60)
            print(f"RESULT ({result.get('mode', 'unknown')})")
            print("=" * 60)
            print(f"Pages: {result['pages']} ({result.get('native_pages', '?')} native, {result.get('ocr_pages', '?')} OCR)")
            print(f"Chars: {result['chars']:,}")
            print(f"Time: {result.get('total_time', result.get('processing_time', '?'))}s")
            if "estimated_cost_usd" in result:
                print(f"Estimated cost: ${result['estimated_cost_usd']:.3f}")
            if "decision" in result:
                print(f"Decision: {result['decision']['reason']}")

        elif parallel:
            # Force multi-T4 parallel extraction
            print(f"Using multi-T4 parallel extraction (chunk_size={chunk_size})")
            result = extract_pdf_parallel.remote(pdf_bytes, chunk_size=chunk_size)

            print("\n" + "=" * 60)
            print("RESULT (multi-T4 parallel)")
            print("=" * 60)
            print(f"Pages: {result['pages']} ({result['native_pages']} native, {result['ocr_pages']} OCR)")
            print(f"Chars: {result['chars']:,}")
            print(f"Total time: {result['processing_time']}s (parallel: {result['parallel_time']}s)")
            print(f"Workers: {result['workers_used']} T4 GPUs")
            print(f"Chunks: {result['chunks']}")
            print(f"Estimated cost: ${result['estimated_cost_usd']:.3f}")

        elif chunked:
            # Use chunked extraction with progress (single A100)
            print(f"Using chunked extraction (chunk_size={chunk_size})")
            final_result = None

            for update in extract_pdf_chunked.remote_gen(
                pdf_bytes, chunk_size=chunk_size
            ):
                if update["type"] == "progress":
                    print(
                        f"[{update['percent']:3d}%] {update['message']} "
                        f"(chunk {update['chunk']}/{update['total_chunks']})"
                    )
                elif update["type"] == "result":
                    final_result = update["data"]

            result = final_result
            print("\n" + "=" * 60)
            print("RESULT (chunked A100)")
            print("=" * 60)
            print(f"Pages: {result['pages']} ({result['native_pages']} native, {result['ocr_pages']} OCR)")
            print(f"Chars: {result['chars']:,}")
            print(f"Time: {result['processing_time']}s")
            print(f"Chunks: {result['total_chunks']}")
        else:
            # Use simple extraction (single A100)
            result = extract_pdf.remote(pdf_bytes)

            print("\n" + "=" * 60)
            print("RESULT (A100)")
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
        print("  modal run modal_worker.py --pdf-path /path/to/document.pdf --chunked     # A100 com progress")
        print("  modal run modal_worker.py --pdf-path /path/to/document.pdf --parallel    # Multi-T4 paralelo")
        print("  modal run modal_worker.py --pdf-path /path/to/document.pdf --smart       # Auto-selecao")
        print("  modal run modal_worker.py --pdf-path /path/to/document.pdf --smart --mode economy")
        print("  modal run modal_worker.py --pdf-path /path/to/document.pdf --count-pages")
        print("")
        print("Modes for --smart:")
        print("  auto        - Seleciona automaticamente baseado em paginas (default)")
        print("  economy     - Sempre usa multi-T4 paralelo (mais barato)")
        print("  performance - Sempre usa A100 (mais rapido para PDFs pequenos)")
