#!/usr/bin/env python3
"""Importa embeddings (dense .npz + sparse .json + IDs .json) para Qdrant.

Usa REST + multiprocessing para maximizar throughput.
UUIDs derivados do chunk_id garantem idempotencia (re-run seguro).
"""

import argparse
import glob
import json
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, SparseVector


EMBEDDINGS_DIR = Path("/home/opc/lex-vector/stj-vec/embeddings")
COLLECTION = "stj"
QDRANT_URL = "http://localhost:6333"


def chunk_id_to_uuid(chunk_id: str) -> str:
    return str(uuid.UUID(chunk_id))


def get_source_files(embeddings_dir: Path) -> list[str]:
    npz_files = {Path(f).stem for f in glob.glob(str(embeddings_dir / "*.npz"))}
    sparse_files = {
        Path(f).stem.replace(".sparse", "")
        for f in glob.glob(str(embeddings_dir / "*.sparse.json"))
    }
    id_files = {
        Path(f).stem
        for f in glob.glob(str(embeddings_dir / "*.json"))
        if ".sparse." not in f
    }
    return sorted(npz_files & sparse_files & id_files)


def import_source(source: str, embeddings_dir: str, batch_size: int,
                  dry_run: bool) -> tuple[str, int, float, str]:
    """Importa um source. Roda em processo separado."""
    edir = Path(embeddings_dir)
    t0 = time.time()

    try:
        with open(edir / f"{source}.json") as f:
            ids = json.load(f)
        with open(edir / f"{source}.sparse.json") as f:
            sparse_data = json.load(f)
        data = np.load(str(edir / f"{source}.npz"))
        dense_data = data[list(data.keys())[0]]

        total = len(ids)
        assert total == dense_data.shape[0] == len(sparse_data)

        if dry_run:
            return source, total, time.time() - t0, "dry-run"

        client = QdrantClient(url=QDRANT_URL, timeout=120)

        for i in range(0, total, batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_dense = dense_data[i:i + batch_size]
            batch_sparse = sparse_data[i:i + batch_size]

            points = []
            for chunk_id, dvec, sdict in zip(batch_ids, batch_dense, batch_sparse):
                points.append(PointStruct(
                    id=chunk_id_to_uuid(chunk_id),
                    vector={
                        "dense": dvec.tolist(),
                        "sparse": SparseVector(
                            indices=[int(k) for k in sdict],
                            values=list(sdict.values()),
                        ),
                    },
                    payload={"chunk_id": chunk_id, "source": source},
                ))
            client.upsert(collection_name=COLLECTION, points=points, wait=False)

        return source, total, time.time() - t0, "ok"

    except Exception as e:
        return source, 0, time.time() - t0, f"ERRO: {e}"


def main():
    parser = argparse.ArgumentParser(description="Importa embeddings para Qdrant (REST + parallel)")
    parser.add_argument("--sources", nargs="*")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--resume-from", type=str)
    args = parser.parse_args()

    client = QdrantClient(url=QDRANT_URL, timeout=120)
    info = client.get_collection(COLLECTION)
    print(f"Collection '{COLLECTION}': {info.points_count:,} pontos existentes", flush=True)

    sources = get_source_files(EMBEDDINGS_DIR)
    if args.sources:
        requested = set(args.sources)
        missing = requested - set(sources)
        if missing:
            print(f"AVISO: nao encontrados: {missing}", flush=True)
        sources = [s for s in sources if s in requested]

    if args.resume_from:
        try:
            idx = sources.index(args.resume_from)
            sources = sources[idx:]
        except ValueError:
            print(f"ERRO: '{args.resume_from}' nao encontrado", file=sys.stderr)
            sys.exit(1)

    total_sources = len(sources)
    print(f"Sources: {total_sources} | Workers: {args.workers} | Batch: {args.batch_size}",
          flush=True)

    total_pts = 0
    errors = []
    t0 = time.time()

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(import_source, src, str(EMBEDDINGS_DIR),
                        args.batch_size, args.dry_run): src
            for src in sources
        }

        done_count = 0
        for future in as_completed(futures):
            done_count += 1
            src, count, elapsed, status = future.result()
            total_pts += count
            rate = count / elapsed if elapsed > 0 else 0

            if status in ("ok", "dry-run"):
                print(f"  [{done_count}/{total_sources}] {src}: {count:,} pts "
                      f"({elapsed:.1f}s, {rate:.0f}/s) [{status}]", flush=True)
            else:
                errors.append((src, status))
                print(f"  [{done_count}/{total_sources}] {src}: {status}", flush=True)

    elapsed_total = time.time() - t0
    print(f"\nTotal: {total_pts:,} pontos em {elapsed_total:.0f}s "
          f"({total_pts / elapsed_total:.0f} pts/s global)", flush=True)

    if errors:
        print(f"\n{len(errors)} erros:", flush=True)
        for src, err in errors:
            print(f"  {src}: {err}", flush=True)

    if not args.dry_run:
        info = client.get_collection(COLLECTION)
        print(f"Collection final: {info.points_count:,} pontos", flush=True)


if __name__ == "__main__":
    main()
