"""Chunkifica arquivo markdown e exporta JSONL para Modal.

Replica o chunker Rust (max_tokens=512, overlap=64, min=30, token=chars/4).

Uso:
  python3 01_chunk_export.py /tmp/integra_teste.md /tmp/case-bench/chunks.jsonl
"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path


MAX_TOKENS = 512
OVERLAP_TOKENS = 64
MIN_CHUNK_TOKENS = 30


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def strip_html(text: str) -> str:
    text = re.sub(r'<[bB][rR]\s*/?>', '\n', text)
    text = re.sub(r'</?[pP]>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    return text


def chunk_text(text: str, doc_id: str) -> list[dict]:
    clean = strip_html(text)
    paragraphs = [line.strip() for line in clean.split('\n') if line.strip()]

    # Split long paragraphs by sentence
    split_paras = []
    for para in paragraphs:
        if estimate_tokens(para) > MAX_TOKENS:
            remaining = para
            while remaining:
                max_chars = MAX_TOKENS * 4
                if len(remaining) <= max_chars:
                    split_paras.append(remaining)
                    break
                search = remaining[:max_chars]
                split_at = search.rfind('. ')
                if split_at == -1:
                    split_at = max_chars
                else:
                    split_at += 2
                split_paras.append(remaining[:split_at])
                remaining = remaining[split_at:]
        else:
            split_paras.append(para)

    chunks = []
    current_text = ""
    chunk_index = 0

    for para in split_paras:
        para_tokens = estimate_tokens(para)
        current_tokens = estimate_tokens(current_text)

        if current_tokens > 0 and current_tokens + para_tokens > MAX_TOKENS:
            if estimate_tokens(current_text) >= MIN_CHUNK_TOKENS:
                chunk_id = hashlib.md5(f"{doc_id}-{chunk_index}".encode()).hexdigest()
                chunks.append({
                    "id": chunk_id,
                    "content": current_text.strip(),
                    "chunk_index": chunk_index,
                    "token_count": estimate_tokens(current_text),
                })
                chunk_index += 1

            # Overlap
            overlap_chars = OVERLAP_TOKENS * 4
            if len(current_text) > overlap_chars:
                current_text = current_text[-overlap_chars:]

        if current_text and not current_text.endswith('\n'):
            current_text += '\n'
        current_text += para

    # Last chunk
    if estimate_tokens(current_text) >= MIN_CHUNK_TOKENS:
        chunk_id = hashlib.md5(f"{doc_id}-{chunk_index}".encode()).hexdigest()
        chunks.append({
            "id": chunk_id,
            "content": current_text.strip(),
            "chunk_index": chunk_index,
            "token_count": estimate_tokens(current_text),
        })

    return chunks


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 01_chunk_export.py <input.md> <output.jsonl>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    text = input_path.read_text()
    doc_id = hashlib.md5(input_path.name.encode()).hexdigest()

    t0 = time.monotonic()
    chunks = chunk_text(text, doc_id)
    elapsed = time.monotonic() - t0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for chunk in chunks:
            f.write(json.dumps({"id": chunk["id"], "content": chunk["content"]}) + '\n')

    total_chars = sum(len(c["content"]) for c in chunks)
    avg_chars = total_chars // len(chunks) if chunks else 0

    print(f"Input:    {len(text):,} chars")
    print(f"Chunks:   {len(chunks)}")
    print(f"Avg size: {avg_chars:,} chars/chunk ({avg_chars // 4} tokens)")
    print(f"JSONL:    {output_path} ({output_path.stat().st_size:,} bytes)")
    print(f"Tempo:    {elapsed:.2f}s")


if __name__ == "__main__":
    main()
