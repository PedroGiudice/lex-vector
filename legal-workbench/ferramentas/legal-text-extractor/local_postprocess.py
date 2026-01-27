"""
Local Post-Processor - Clean extracted text using local LLM via Ollama.

Model-agnostic design - easy to swap models.

Usage:
    python local_postprocess.py input.md output.md
    python local_postprocess.py input.md --model qwen2.5:3b
    python local_postprocess.py input.md --model llama3.2:3b
    python local_postprocess.py input.md --script-only  # No LLM, just regex cleanup
"""

import os
import re
import sys
import time
import argparse
import requests
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_MODEL = "qwen2.5:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"
CHUNK_SIZE = 8000  # chars per chunk (smaller for local models)


# =============================================================================
# SCRIPT-BASED CLEANUP (fast, no LLM)
# =============================================================================

def script_cleanup(text: str) -> str:
    """
    Fast regex-based cleanup. Removes known artifacts.

    This handles 80% of the cleanup without needing an LLM.
    """
    # Remove image references: ![](path)
    text = re.sub(r'!\[\]\([^)]+\)\s*', '', text)

    # Remove page markers: {123}---
    text = re.sub(r'\{?\d+\}?-{2,}\s*', '', text)

    # Remove standalone page numbers: {123}
    text = re.sub(r'^\{\d+\}\s*$', '', text, flags=re.MULTILINE)

    # Replace <br> with newline
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    # Remove excessive blank lines (more than 2)
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    # Remove trailing whitespace on lines
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)

    # Remove repeated dashes (separators)
    text = re.sub(r'-{10,}', '', text)

    # Fix common OCR errors in Portuguese legal text
    ocr_fixes = [
        (r'\bé\s+que\b', 'é que'),      # broken "é que"
        (r'\bà\s+s\b', 'às'),            # broken "às"
        (r'\bR\s*\$\s*', 'R$ '),         # fix R$ spacing
        (r'BRL\s+', 'BRL '),             # fix BRL spacing
    ]
    for pattern, replacement in ocr_fixes:
        text = re.sub(pattern, replacement, text)

    return text.strip()


# =============================================================================
# LLM-BASED CLEANUP (slower, smarter)
# =============================================================================

def llm_cleanup(text: str, model: str) -> str:
    """
    Use local LLM via Ollama to clean text.
    """
    prompt = f"""Limpe este texto extraído de documento jurídico brasileiro.

REGRAS:
1. PRESERVAR todo conteúdo substantivo
2. CORRIGIR erros de OCR óbvios
3. FORMATAR corretamente (headers, listas, tabelas)
4. REMOVER artefatos (números de página soltos, lixo)
5. NÃO resumir ou omitir partes

TEXTO:
{text}

TEXTO LIMPO:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temp for consistent output
                    "num_predict": len(text) + 500,  # Allow slightly longer output
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", text)
    except Exception as e:
        print(f"  WARN: LLM failed: {e}")
        return text


def chunk_text(text: str, max_chars: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current = ""

    for para in text.split("\n\n"):
        if len(current) + len(para) + 2 <= max_chars:
            current += para + "\n\n"
        else:
            if current:
                chunks.append(current.strip())
            current = para + "\n\n"

    if current:
        chunks.append(current.strip())

    return chunks


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_document(
    input_path: str,
    output_path: str,
    model: str = DEFAULT_MODEL,
    script_only: bool = False
) -> dict:
    """Process document with optional LLM cleanup."""

    print(f"Reading: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    input_chars = len(text)
    print(f"Input: {input_chars:,} chars")

    # Step 1: Script cleanup (always runs, fast)
    print("Step 1: Script cleanup...")
    start = time.time()
    text = script_cleanup(text)
    script_time = time.time() - start
    after_script = len(text)
    print(f"  Script: {input_chars:,} -> {after_script:,} chars ({script_time:.2f}s)")

    # Step 2: LLM cleanup (optional)
    if not script_only:
        print(f"Step 2: LLM cleanup (model: {model})...")
        chunks = chunk_text(text)
        print(f"  Processing {len(chunks)} chunks...")

        start = time.time()
        cleaned_chunks = []

        for i, chunk in enumerate(chunks, 1):
            chunk_start = time.time()
            print(f"  Chunk {i}/{len(chunks)}...", end=" ", flush=True)

            cleaned = llm_cleanup(chunk, model)
            cleaned_chunks.append(cleaned)

            chunk_time = time.time() - chunk_start
            print(f"done ({chunk_time:.1f}s)")

        text = "\n\n".join(cleaned_chunks)
        llm_time = time.time() - start
        print(f"  LLM: {after_script:,} -> {len(text):,} chars ({llm_time:.1f}s)")
    else:
        llm_time = 0

    # Save output
    print(f"Writing: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    output_chars = len(text)
    total_time = script_time + llm_time

    return {
        "input_chars": input_chars,
        "output_chars": output_chars,
        "script_time": round(script_time, 2),
        "llm_time": round(llm_time, 1),
        "total_time": round(total_time, 1),
        "reduction_pct": round((1 - output_chars / input_chars) * 100, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Local text post-processor")
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("output", nargs="?", help="Output file (default: input_local.md)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--script-only", action="store_true", help="Only use script cleanup, no LLM")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: File not found: {args.input}")
        sys.exit(1)

    output_path = args.output or os.path.splitext(args.input)[0] + "_local.md"

    print("=" * 60)
    print("LOCAL POST-PROCESSOR")
    print("=" * 60)
    if args.script_only:
        print("Mode: Script-only (no LLM)")
    else:
        print(f"Mode: Script + LLM ({args.model})")
    print("=" * 60)

    stats = process_document(
        args.input,
        output_path,
        model=args.model,
        script_only=args.script_only
    )

    print("=" * 60)
    print("RESULTADO")
    print("=" * 60)
    print(f"Input:  {stats['input_chars']:,} chars")
    print(f"Output: {stats['output_chars']:,} chars")
    print(f"Reducao: {stats['reduction_pct']:.1f}%")
    print(f"Tempo script: {stats['script_time']}s")
    print(f"Tempo LLM: {stats['llm_time']}s")
    print(f"Tempo total: {stats['total_time']}s")
    print(f"\nArquivo: {output_path}")


if __name__ == "__main__":
    main()
