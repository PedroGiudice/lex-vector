#!/usr/bin/env python3
"""Enriquece payload dos pontos no Qdrant com metadados do SQLite.

Adiciona: doc_id, chunk_index, secao, classe, tipo.
Cria payload indexes para filtragem eficiente.

Usa REST batch API (/collections/{collection}/points/batch) para performance.
"""

import argparse
import sqlite3
import time
import uuid

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

DB_PATH = "db/stj-vec.db"
COLLECTION = "stj"
QDRANT_URL = "http://localhost:6333"
BATCH_SIZE = 500
WORKERS = 4


def chunk_id_to_uuid(chunk_id: str) -> str:
    """Converte chunk_id hex para UUID string (mesmo formato usado na importacao)."""
    return str(uuid.UUID(chunk_id))


def load_chunk_metadata(db_path: str) -> list[dict]:
    """Carrega metadados de todos os chunks via JOIN com documents."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    cur = conn.execute(
        """
        SELECT c.id, c.doc_id, c.chunk_index, c.secao,
               d.classe, d.tipo, d.orgao_julgador, d.data_julgamento
        FROM chunks c
        JOIN documents d ON c.doc_id = d.id
    """
    )

    rows = []
    for chunk_id, doc_id, chunk_index, secao, classe, tipo, orgao, data_julg in cur:
        payload = {
            "doc_id": doc_id,
            "chunk_index": chunk_index or 0,
        }
        if secao:
            payload["secao"] = secao
        if classe:
            payload["classe"] = classe
        if tipo:
            payload["tipo"] = tipo
        if orgao:
            payload["orgao_julgador"] = orgao
        if data_julg:
            payload["data_julgamento"] = data_julg

        rows.append(
            {
                "point_id": chunk_id_to_uuid(chunk_id),
                "payload": payload,
            }
        )

    conn.close()
    return rows


def update_batch_rest(
    batch: list[dict], qdrant_url: str, collection: str
) -> tuple[int, str]:
    """Atualiza payload via REST batch API (mais eficiente que chamadas individuais)."""
    try:
        operations = []
        for item in batch:
            operations.append(
                {
                    "set_payload": {
                        "payload": item["payload"],
                        "points": [item["point_id"]],
                    }
                }
            )

        resp = requests.post(
            f"{qdrant_url}/collections/{collection}/points/batch",
            json={"operations": operations},
            timeout=120,
        )
        resp.raise_for_status()
        return len(batch), "ok"
    except Exception as e:
        return 0, f"ERRO: {e}"


def create_payload_indexes(qdrant_url: str, collection: str):
    """Cria payload indexes para filtragem eficiente."""
    client = QdrantClient(url=qdrant_url, timeout=120)

    indexes = {
        "doc_id": PayloadSchemaType.KEYWORD,
        "chunk_index": PayloadSchemaType.INTEGER,
        "secao": PayloadSchemaType.KEYWORD,
        "classe": PayloadSchemaType.KEYWORD,
        "tipo": PayloadSchemaType.KEYWORD,
        "orgao_julgador": PayloadSchemaType.KEYWORD,
        "data_julgamento": PayloadSchemaType.KEYWORD,
    }

    for field, schema in indexes.items():
        print(f"  Criando index: {field} ({schema})", flush=True)
        try:
            client.create_payload_index(
                collection_name=collection,
                field_name=field,
                field_schema=schema,
            )
        except Exception as e:
            # Index pode ja existir
            print(f"    (aviso: {e})", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Enriquecer payload do Qdrant com metadados SQLite"
    )
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--workers", type=int, default=WORKERS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--indexes-only", action="store_true", help="Apenas criar payload indexes"
    )
    args = parser.parse_args()

    if args.indexes_only:
        print("Criando payload indexes...", flush=True)
        create_payload_indexes(QDRANT_URL, COLLECTION)
        print("Done.", flush=True)
        return

    # Carregar metadados
    print("Carregando metadados do SQLite...", flush=True)
    t0 = time.time()
    rows = load_chunk_metadata(DB_PATH)
    print(f"  {len(rows):,} chunks em {time.time() - t0:.0f}s", flush=True)

    if args.dry_run:
        print(f"Dry run: {len(rows):,} pontos para atualizar", flush=True)
        for r in rows[:3]:
            print(f"  {r['point_id']}: {r['payload']}", flush=True)
        return

    # Processar sequencialmente em batches (REST batch API ja agrupa operacoes)
    print(
        f"Atualizando {len(rows):,} pontos (batch {args.batch_size})...", flush=True
    )
    t1 = time.time()
    total_done = 0
    errors = []

    for i in range(0, len(rows), args.batch_size):
        batch = rows[i : i + args.batch_size]
        count, status = update_batch_rest(batch, QDRANT_URL, COLLECTION)
        total_done += count
        if status != "ok":
            errors.append(status)
            print(f"  ERRO no batch {i}: {status}", flush=True)

        if total_done % 50000 < args.batch_size:
            elapsed = time.time() - t1
            rate = total_done / elapsed if elapsed > 0 else 0
            eta_min = (len(rows) - total_done) / rate / 60 if rate > 0 else 0
            print(
                f"  {total_done:,}/{len(rows):,} ({rate:.0f} pts/s, ETA {eta_min:.0f}m)",
                flush=True,
            )

    elapsed = time.time() - t1
    print(
        f"\nTotal: {total_done:,} pontos em {elapsed:.0f}s ({total_done / elapsed:.0f} pts/s)",
        flush=True,
    )
    if errors:
        print(f"Erros: {len(errors)}", flush=True)

    # Criar indexes
    print("\nCriando payload indexes...", flush=True)
    create_payload_indexes(QDRANT_URL, COLLECTION)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
