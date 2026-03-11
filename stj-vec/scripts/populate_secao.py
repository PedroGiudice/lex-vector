#!/usr/bin/env python3
"""Popular coluna secao nos chunks via deteccao de marcadores + propagacao por documento.

Estrategia otimizada: em vez de ler 13.5M chunks com content (dezenas de GB),
usa SQL para encontrar APENAS os chunks com marcadores (via LIKE), e depois
propaga por ranges de chunk_index usando batch UPDATEs.

Fases:
  1. Buscar chunks com marcadores via SQL LIKE (sem ler content em Python)
  2. Construir ranges de propagacao (secao, doc_id, start_idx, end_idx)
  3. Executar range UPDATEs em batch
"""

import sqlite3
import time
import sys

DB_PATH = "db/stj-vec.db"

# Marcadores de secao buscados via SQL LIKE.
# Cada secao tem variantes com \r e \n (PDFs extraidos pelo Marker).
MARKERS = {
    "acordao": [
        "content LIKE 'ACÓRDÃO' || X'0D' || '%'",
        "content LIKE 'ACÓRDÃO' || X'0A' || '%'",
        "content LIKE 'ACORDAO' || X'0D' || '%'",
        "content LIKE 'ACORDAO' || X'0A' || '%'",
        "content LIKE '%' || X'0A' || 'ACÓRDÃO' || X'0D' || '%'",
        "content LIKE '%' || X'0A' || 'ACÓRDÃO' || X'0A' || '%'",
        "content LIKE '%' || X'0D' || 'ACÓRDÃO' || X'0D' || '%'",
        "content LIKE '%' || X'0D' || 'ACÓRDÃO' || X'0A' || '%'",
    ],
    "decisao": [
        "content LIKE 'DECISÃO' || X'0D' || '%'",
        "content LIKE 'DECISÃO' || X'0A' || '%'",
        "content LIKE 'DECISAO' || X'0D' || '%'",
        "content LIKE 'DECISAO' || X'0A' || '%'",
        "content LIKE '%' || X'0A' || 'DECISÃO' || X'0D' || '%'",
        "content LIKE '%' || X'0A' || 'DECISÃO' || X'0A' || '%'",
        "content LIKE '%' || X'0D' || 'DECISÃO' || X'0D' || '%'",
        "content LIKE '%' || X'0D' || 'DECISÃO' || X'0A' || '%'",
    ],
    "ementa": [
        "content LIKE 'EMENTA' || X'0D' || '%'",
        "content LIKE 'EMENTA' || X'0A' || '%'",
        "content LIKE '%' || X'0A' || 'EMENTA' || X'0D' || '%'",
        "content LIKE '%' || X'0A' || 'EMENTA' || X'0A' || '%'",
        "content LIKE '%' || X'0D' || 'EMENTA' || X'0D' || '%'",
        "content LIKE '%' || X'0D' || 'EMENTA' || X'0A' || '%'",
    ],
    "voto": [
        "content LIKE 'VOTO' || X'0D' || '%'",
        "content LIKE 'VOTO' || X'0A' || '%'",
        "content LIKE '%' || X'0A' || 'VOTO' || X'0D' || '%'",
        "content LIKE '%' || X'0A' || 'VOTO' || X'0A' || '%'",
        "content LIKE '%' || X'0D' || 'VOTO' || X'0D' || '%'",
        "content LIKE '%' || X'0D' || 'VOTO' || X'0A' || '%'",
    ],
    "relatorio": [
        "content LIKE 'RELATÓRIO' || X'0D' || '%'",
        "content LIKE 'RELATÓRIO' || X'0A' || '%'",
        "content LIKE 'RELATORIO' || X'0D' || '%'",
        "content LIKE 'RELATORIO' || X'0A' || '%'",
        "content LIKE '%' || X'0A' || 'RELATÓRIO' || X'0D' || '%'",
        "content LIKE '%' || X'0A' || 'RELATÓRIO' || X'0A' || '%'",
        "content LIKE '%' || X'0D' || 'RELATÓRIO' || X'0D' || '%'",
        "content LIKE '%' || X'0D' || 'RELATÓRIO' || X'0A' || '%'",
    ],
}


def find_marker_chunks(conn):
    """Fase 1: Encontrar todos os chunks com marcadores via SQL (sem ler content em Python)."""
    doc_markers = {}  # {doc_id: [(chunk_index, secao), ...]}
    total = 0

    for secao, conditions in MARKERS.items():
        where = " OR ".join(conditions)
        sql = f"SELECT doc_id, chunk_index FROM chunks WHERE ({where})"
        cur = conn.execute(sql)
        count = 0
        for doc_id, chunk_index in cur:
            doc_markers.setdefault(doc_id, []).append((chunk_index, secao))
            count += 1
        total += count
        print(f"  {secao:12s} -> {count:>10,} chunks com marcador", flush=True)

    print(f"  Total: {total:,} marcadores em {len(doc_markers):,} docs", flush=True)
    return doc_markers


def get_max_chunk_indexes(conn, doc_ids):
    """Buscar max chunk_index por documento."""
    result = {}
    doc_list = list(doc_ids)
    for i in range(0, len(doc_list), 999):
        batch = doc_list[i : i + 999]
        placeholders = ",".join("?" * len(batch))
        sql = f"SELECT doc_id, MAX(chunk_index) FROM chunks WHERE doc_id IN ({placeholders}) GROUP BY doc_id"
        for doc_id, max_idx in conn.execute(sql, batch):
            result[doc_id] = max_idx
    return result


def build_range_updates(doc_markers, max_indexes):
    """Fase 2: Gerar (secao, doc_id, start_idx, end_idx) para propagacao."""
    updates = []
    for doc_id, markers in doc_markers.items():
        max_idx = max_indexes.get(doc_id, 0)
        if max_idx is None:
            continue

        # Deduplicar: mesmo chunk_index -> ultimo marcador vence
        seen = {}
        for idx, sec in markers:
            seen[idx] = sec
        sorted_markers = sorted(seen.items())

        for i, (start_idx, secao) in enumerate(sorted_markers):
            end_idx = (
                sorted_markers[i + 1][0] - 1
                if i + 1 < len(sorted_markers)
                else max_idx
            )
            if end_idx >= start_idx:
                updates.append((secao, doc_id, start_idx, end_idx))

    return updates


def apply_updates(conn, updates, batch_size=50000):
    """Fase 3: Executar range UPDATEs em batch."""
    for i in range(0, len(updates), batch_size):
        batch = updates[i : i + batch_size]
        conn.executemany(
            "UPDATE chunks SET secao = ? WHERE doc_id = ? AND chunk_index >= ? AND chunk_index <= ?",
            batch,
        )
        done = i + len(batch)
        if done % 200000 == 0 or done >= len(updates):
            print(f"  {done:,}/{len(updates):,} ranges aplicados", flush=True)
    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")

    # Reset
    print("Resetando secao...", flush=True)
    conn.execute("UPDATE chunks SET secao = NULL WHERE secao IS NOT NULL")
    conn.commit()

    # Fase 1
    print("\nFase 1: Buscando chunks com marcadores...", flush=True)
    t0 = time.time()
    doc_markers = find_marker_chunks(conn)
    print(f"  ({time.time() - t0:.0f}s)", flush=True)

    # Max chunk indexes
    print("\nObtendo max chunk_index...", flush=True)
    t1 = time.time()
    max_indexes = get_max_chunk_indexes(conn, doc_markers.keys())
    print(f"  {len(max_indexes):,} docs ({time.time() - t1:.0f}s)", flush=True)

    # Fase 2
    print("\nFase 2: Construindo range updates...", flush=True)
    updates = build_range_updates(doc_markers, max_indexes)
    print(f"  {len(updates):,} ranges", flush=True)

    # Fase 3
    print("\nFase 3: Aplicando updates...", flush=True)
    t2 = time.time()
    apply_updates(conn, updates)
    print(f"  ({time.time() - t2:.0f}s)", flush=True)

    # Verificacao
    print("\n=== RESULTADO ===", flush=True)
    for row in conn.execute(
        "SELECT secao, COUNT(*) FROM chunks GROUP BY secao ORDER BY COUNT(*) DESC"
    ):
        label = row[0] or "NULL"
        print(f"  {label:20s} -> {row[1]:>12,}", flush=True)

    conn.close()


if __name__ == "__main__":
    main()
