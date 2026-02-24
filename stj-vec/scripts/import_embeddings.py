"""Importa embeddings (.npz + .json) para SQLite vec_chunks.

Uso: python3 scripts/import_embeddings.py --input /tmp/stj-vec-embeddings/embeddings --db db/stj-vec.db

Substitui o importer Rust que falha com 'Invalid checksum' em alguns .npz
(diferenca de strictness entre crate zip do Rust e zipfile do Python).
"""
import argparse
import json
import os
import sqlite3
import struct
import sys
import time
from pathlib import Path

import numpy as np


def ensure_vec_table(conn: sqlite3.Connection, dim: int):
    """Cria tabela vec_chunks se nao existir."""
    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
            chunk_id TEXT PRIMARY KEY,
            embedding float[{dim}] distance_metric=cosine
        )
    """)


def source_already_imported(conn: sqlite3.Connection, json_path: Path) -> bool:
    """Checa se o primeiro chunk_id de um source ja existe no DB."""
    chunk_ids = json.loads(json_path.read_text())
    if not chunk_ids:
        return True
    cursor = conn.execute(
        "SELECT 1 FROM vec_chunks WHERE chunk_id = ? LIMIT 1",
        (chunk_ids[0],),
    )
    return cursor.fetchone() is not None


def import_source(conn: sqlite3.Connection, npz_path: Path, json_path: Path) -> int:
    """Importa 1 source. Retorna quantidade de embeddings inseridos."""
    chunk_ids = json.loads(json_path.read_text())

    data = np.load(str(npz_path))
    embeddings = data["embeddings"]  # shape (N, dim)

    if len(chunk_ids) != len(embeddings):
        print(f"  SKIP: mismatch {len(chunk_ids)} ids vs {len(embeddings)} embeddings")
        return 0

    cursor = conn.cursor()
    for chunk_id, emb in zip(chunk_ids, embeddings):
        emb_bytes = emb.astype(np.float32).tobytes()
        cursor.execute(
            "INSERT INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, emb_bytes),
        )

    conn.commit()
    return len(chunk_ids)


def get_already_imported(conn: sqlite3.Connection) -> set:
    """Retorna set de source prefixes ja importados (baseado em chunk_ids existentes)."""
    try:
        cursor = conn.execute("SELECT DISTINCT substr(chunk_id, 1, 8) FROM vec_chunks LIMIT 1")
        cursor.fetchone()  # just test if table exists
    except Exception:
        return set()

    # Contar por source prefix e pegar os que tem embeddings
    cursor = conn.execute("""
        SELECT DISTINCT substr(chunk_id, 1, instr(chunk_id, '_') - 1)
        FROM vec_chunks
        WHERE chunk_id LIKE '%_%'
        LIMIT 100000
    """)
    return {row[0] for row in cursor}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Dir com .npz e .json")
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--dim", type=int, default=1024, help="Embedding dimension")
    parser.add_argument("--skip-existing", action="store_true", help="Pular sources ja importados")
    args = parser.parse_args()

    input_dir = Path(args.input)
    npz_files = sorted(input_dir.glob("*.npz"))
    print(f"{len(npz_files)} sources encontrados em {input_dir}")

    conn = sqlite3.connect(args.db)
    conn.enable_load_extension(True)
    import sqlite_vec
    sqlite_vec.load(conn)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")

    ensure_vec_table(conn, args.dim)

    total_sources = 0
    total_embeddings = 0
    t0 = time.time()

    for i, npz_path in enumerate(npz_files):
        source_name = npz_path.stem
        json_path = input_dir / f"{source_name}.json"

        if not json_path.exists():
            print(f"  SKIP {source_name}: no .json")
            continue

        if source_already_imported(conn, json_path):
            print(f"  SKIP {source_name}: already imported")
            total_sources += 1
            continue

        try:
            count = import_source(conn, npz_path, json_path)
            total_sources += 1
            total_embeddings += count
            elapsed = time.time() - t0
            rate = total_embeddings / elapsed if elapsed > 0 else 0
            remaining = len(npz_files) - i - 1
            eta_min = (remaining * elapsed / (i + 1)) / 60 if i > 0 else 0
            print(
                f"  [{i+1}/{len(npz_files)}] {source_name}: {count} embeddings "
                f"(total: {total_embeddings:,}, {rate:.0f}/s, ETA: {eta_min:.0f}min)"
            )
        except Exception as e:
            print(f"  ERROR {source_name}: {e}")
            continue

    elapsed = time.time() - t0
    print(f"\nDone: {total_sources} sources, {total_embeddings:,} embeddings em {elapsed/60:.1f}min")
    conn.close()


if __name__ == "__main__":
    main()
