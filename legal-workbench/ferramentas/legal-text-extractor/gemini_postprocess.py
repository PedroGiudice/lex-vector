"""
Gemini Post-Processor - Clean and structure extracted text.

Uses Gemini API to clean up Marker output:
- Remove OCR artifacts
- Fix formatting issues
- Structure sections properly
- Preserve legal document semantics

Usage:
    python gemini_postprocess.py input.md output.md
    python gemini_postprocess.py input.md  # outputs to input_cleaned.md

TODO: Implementar salvamento incremental (chunk por chunk) para:
      - Permitir cancelamento sem perda total
      - Visualizar progresso parcial
      - Retomar de onde parou em caso de erro
"""

import os
import sys
import time
from pathlib import Path

# Gemini API via google-generativeai
try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: google-generativeai not installed")
    print("Run: pip install google-generativeai")
    sys.exit(1)


def get_api_key() -> str:
    """Get Gemini API key from environment."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("ERROR: GEMINI_API_KEY not set")
        print("Run: export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)
    return key


def chunk_text(text: str, max_chars: int = 30000) -> list[str]:
    """
    Split text into chunks for API processing.

    Tries to split at paragraph boundaries to preserve context.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by double newlines (paragraphs)
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def clean_chunk(model, chunk: str, chunk_num: int, total_chunks: int) -> str:
    """
    Clean a single chunk of text using Gemini.
    """
    prompt = f"""Você é um especialista em processamento de documentos jurídicos brasileiros.

TAREFA: Limpar e estruturar o texto extraído por OCR de um documento jurídico.

REGRAS:
1. PRESERVAR todo o conteúdo substantivo - não remova informações
2. CORRIGIR erros de OCR óbvios (caracteres trocados, espaçamento)
3. FORMATAR corretamente:
   - Títulos de seções (## para principais, ### para sub)
   - Listas numeradas e com bullets
   - Citações legais (artigos, leis, jurisprudência)
   - Parágrafos bem separados
4. REMOVER:
   - Cabeçalhos/rodapés repetitivos de página
   - Números de página soltos
   - Artefatos de OCR (caracteres estranhos, linhas de separação desnecessárias)
5. NÃO adicionar conteúdo que não existe no original
6. NÃO resumir ou omitir partes

Este é o chunk {chunk_num} de {total_chunks}.

TEXTO PARA LIMPAR:
---
{chunk}
---

TEXTO LIMPO:"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"  WARN: Chunk {chunk_num} failed: {e}")
        return chunk  # Return original on failure


def process_document(input_path: str, output_path: str) -> dict:
    """
    Process entire document through Gemini.

    Returns stats dict.
    """
    # Setup API
    api_key = get_api_key()
    genai.configure(api_key=api_key)

    # Use gemini-2.5-flash for speed and cost efficiency
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Read input
    print(f"Reading: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    input_chars = len(text)
    print(f"Input: {input_chars:,} chars")

    # Chunk for processing
    chunks = chunk_text(text)
    print(f"Processing {len(chunks)} chunks...")

    start_time = time.time()
    cleaned_chunks = []

    for i, chunk in enumerate(chunks, 1):
        print(f"  Chunk {i}/{len(chunks)} ({len(chunk):,} chars)...", end=" ", flush=True)
        chunk_start = time.time()

        cleaned = clean_chunk(model, chunk, i, len(chunks))
        cleaned_chunks.append(cleaned)

        chunk_time = time.time() - chunk_start
        print(f"done ({chunk_time:.1f}s)")

        # Rate limiting - Gemini free tier has limits
        if i < len(chunks):
            time.sleep(1)  # Small delay between chunks

    # Combine chunks
    result = "\n\n".join(cleaned_chunks)
    output_chars = len(result)

    # Write output
    print(f"Writing: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    total_time = time.time() - start_time

    stats = {
        "input_chars": input_chars,
        "output_chars": output_chars,
        "chunks": len(chunks),
        "time_seconds": round(total_time, 1),
        "reduction_pct": round((1 - output_chars / input_chars) * 100, 1) if input_chars > 0 else 0,
    }

    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python gemini_postprocess.py input.md [output.md]")
        print("       python gemini_postprocess.py input.md  # outputs to input_cleaned.md")
        sys.exit(1)

    input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        # Default: input_cleaned.md
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_cleaned.md"

    print("=" * 60)
    print("GEMINI POST-PROCESSOR")
    print("=" * 60)

    stats = process_document(input_path, output_path)

    print("=" * 60)
    print("RESULTADO")
    print("=" * 60)
    print(f"Input:  {stats['input_chars']:,} chars")
    print(f"Output: {stats['output_chars']:,} chars")
    print(f"Chunks: {stats['chunks']}")
    print(f"Tempo:  {stats['time_seconds']}s")
    print(f"Mudanca: {stats['reduction_pct']:+.1f}%")
    print(f"\nArquivo salvo: {output_path}")


if __name__ == "__main__":
    main()
