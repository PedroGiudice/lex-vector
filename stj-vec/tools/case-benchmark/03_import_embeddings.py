"""Importa embeddings (dense + sparse) para knowledge.db.

Uso:
  python3 03_import_embeddings.py --input /tmp/case-bench/embeddings --db /path/to/knowledge.db

Arquivos esperados em --input:
  {source}.npz         - dense embeddings (numpy array)
  {source}.json        - chunk IDs
  {source}.sparse.json - sparse lexical weights [{token_id: weight}, ...]
"""
import argparse
import json
import sqlite3
import time
from pathlib import Path

import numpy as np
import sqlite_vec


def setup_tables(conn: sqlite3.Connection, dim: int) -> None:
    """Cria tabelas se nao existirem."""
    conn.execute(f"""CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
        chunk_id TEXT PRIMARY KEY,
        embedding float[{dim}]
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS sparse_index (
        token_id INTEGER NOT NULL,
        chunk_id TEXT NOT NULL,
        weight REAL NOT NULL,
        PRIMARY KEY (token_id, chunk_id)
    )""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_sparse_token
        ON sparse_index (token_id)""")


def import_dense(conn: sqlite3.Connection, chunk_ids: list, embeddings: np.ndarray) -> int:
    """Importa dense embeddings para vec_chunks."""
    count = 0
    for chunk_id, emb in zip(chunk_ids, embeddings):
        conn.execute(
            "INSERT OR REPLACE INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)",
            (chunk_id, emb.astype(np.float32).tobytes()),
        )
        count += 1
    return count


def import_sparse(conn: sqlite3.Connection, chunk_ids: list, sparse_data: list[dict]) -> int:
    """Importa sparse weights para sparse_index (tabela invertida)."""
    count = 0
    for chunk_id, weights in zip(chunk_ids, sparse_data):
        for token_id_str, weight in weights.items():
            conn.execute(
                "INSERT OR REPLACE INTO sparse_index (token_id, chunk_id, weight) VALUES (?, ?, ?)",
                (int(token_id_str), chunk_id, float(weight)),
            )
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="Importa dense + sparse embeddings para knowledge.db")
    parser.add_argument("--input", required=True, help="Dir com .npz, .json e .sparse.json")
    parser.add_argument("--db", required=True, help="knowledge.db path")
    parser.add_argument("--dim", type=int, default=1024)
    args = parser.parse_args()

    input_dir = Path(args.input)
    npz_files = sorted(input_dir.glob("*.npz"))
    print(f"{len(npz_files)} sources em {input_dir}")

    conn = sqlite3.connect(args.db)
    sqlite_vec.load(conn)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")

    setup_tables(conn, args.dim)

    total_dense = 0
    total_sparse = 0
    t0 = time.time()

    for npz_path in npz_files:
        source = npz_path.stem
        json_path = input_dir / f"{source}.json"
        sparse_path = input_dir / f"{source}.sparse.json"

        if not json_path.exists():
            print(f"  SKIP {source}: no .json")
            continue

        chunk_ids = json.loads(json_path.read_text())
        data = np.load(str(npz_path))
        embeddings = data["embeddings"]

        if len(chunk_ids) != len(embeddings):
            print(f"  SKIP {source}: mismatch {len(chunk_ids)} ids vs {len(embeddings)} embs")
            continue

        # Dense
        nd = import_dense(conn, chunk_ids, embeddings)
        total_dense += nd

        # Sparse
        ns = 0
        if sparse_path.exists():
            sparse_data = json.loads(sparse_path.read_text())
            if len(sparse_data) == len(chunk_ids):
                ns = import_sparse(conn, chunk_ids, sparse_data)
                total_sparse += ns
            else:
                print(f"  WARN {source}: sparse mismatch {len(sparse_data)} vs {len(chunk_ids)} chunks")
        else:
            print(f"  WARN {source}: no sparse file")

        conn.commit()
        print(f"  {source}: {nd} dense + {ns:,} sparse entries")

    elapsed = time.time() - t0
    print(f"\nTotal: {total_dense:,} dense embeddings + {total_sparse:,} sparse entries em {elapsed:.1f}s")
    conn.close()


if __name__ == "__main__":
    main()
