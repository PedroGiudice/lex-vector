#!/usr/bin/env python3
"""Popular coluna secao nos chunks via deteccao de marcadores + propagacao por documento.

Estrategia otimizada: em vez de ler 13.5M chunks com content (dezenas de GB),
usa SQL para encontrar APENAS os chunks com marcadores (via LIKE), e depois
propaga por ranges de chunk_index usando batch UPDATEs.

Fases:
  1. Buscar chunks com marcadores via SQL LIKE (ou carregar cache)
  2. Construir ranges de propagacao (secao, doc_id, start_idx, end_idx)
  3. Executar range UPDATEs em batch com commit intermediario

Uso:
  python3 scripts/populate_secao.py              # Executa tudo (usa cache se existir)
  python3 scripts/populate_secao.py --no-cache   # Forca re-scan da Fase 1
  python3 scripts/populate_secao.py --reset      # Reseta secao antes de popular
"""

import json
import sqlite3
import time
import sys
from pathlib import Path

DB_PATH = "db/stj-vec.db"
CACHE_PATH = "db/secao_markers_cache.json"

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


def save_cache(doc_markers):
    """Salvar marcadores em JSON para re-uso."""
    # Converter para formato serializavel: {doc_id: [[idx, secao], ...]}
    data = {doc_id: markers for doc_id, markers in doc_markers.items()}
    with open(CACHE_PATH, "w") as f:
        json.dump(data, f)
    size_mb = Path(CACHE_PATH).stat().st_size / 1024 / 1024
    print(f"  Cache salvo: {CACHE_PATH} ({size_mb:.1f} MB)", flush=True)


def load_cache():
    """Carregar marcadores do cache."""
    with open(CACHE_PATH) as f:
        data = json.load(f)
    # Converter listas de volta para tuplas
    doc_markers = {}
    total = 0
    for doc_id, markers in data.items():
        doc_markers[doc_id] = [(m[0], m[1]) for m in markers]
        total += len(markers)
    print(f"  Cache carregado: {total:,} marcadores em {len(doc_markers):,} docs", flush=True)
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

        # Deduplicar: mesmo chunk_index -> primeiro marcador vence
        # (o marcador no inicio do chunk define a secao; marcadores
        # que aparecem depois no content sao da secao seguinte)
        seen = {}
        for idx, sec in markers:
            if idx not in seen:
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
    """Fase 3: Executar range UPDATEs em batch com commit intermediario."""
    total = len(updates)
    t0 = time.time()
    for i in range(0, total, batch_size):
        batch = updates[i : i + batch_size]
        conn.executemany(
            "UPDATE chunks SET secao = ? WHERE doc_id = ? AND chunk_index >= ? AND chunk_index <= ?",
            batch,
        )
        conn.commit()
        done = i + len(batch)
        elapsed = time.time() - t0
        rate = done / elapsed if elapsed > 0 else 0
        eta = (total - done) / rate if rate > 0 else 0
        print(
            f"  {done:,}/{total:,} ranges ({done*100/total:.1f}%) "
            f"[{elapsed:.0f}s elapsed, ~{eta:.0f}s remaining]",
            flush=True,
        )


def main():
    use_cache = "--no-cache" not in sys.argv
    do_reset = "--reset" in sys.argv

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")

    # Reset (apenas se pedido)
    if do_reset:
        print("Resetando secao...", flush=True)
        t = time.time()
        conn.execute("UPDATE chunks SET secao = NULL WHERE secao IS NOT NULL")
        conn.commit()
        print(f"  ({time.time() - t:.0f}s)", flush=True)
    else:
        print("Skip reset (use --reset para forcar)", flush=True)

    # Fase 1: marcadores (com cache)
    cache_exists = Path(CACHE_PATH).exists()
    if use_cache and cache_exists:
        print(f"\nFase 1: Carregando cache ({CACHE_PATH})...", flush=True)
        t0 = time.time()
        doc_markers = load_cache()
        print(f"  ({time.time() - t0:.1f}s)", flush=True)
    else:
        print("\nFase 1: Buscando chunks com marcadores...", flush=True)
        t0 = time.time()
        doc_markers = find_marker_chunks(conn)
        print(f"  ({time.time() - t0:.0f}s)", flush=True)
        # Salvar cache
        print("  Salvando cache...", flush=True)
        save_cache(doc_markers)

    # Max chunk indexes
    print("\nObtendo max chunk_index...", flush=True)
    t1 = time.time()
    max_indexes = get_max_chunk_indexes(conn, doc_markers.keys())
    print(f"  {len(max_indexes):,} docs ({time.time() - t1:.0f}s)", flush=True)

    # Fase 2
    print("\nFase 2: Construindo range updates...", flush=True)
    t2 = time.time()
    updates = build_range_updates(doc_markers, max_indexes)
    print(f"  {len(updates):,} ranges ({time.time() - t2:.1f}s)", flush=True)

    # Fase 3
    print("\nFase 3: Aplicando updates...", flush=True)
    apply_updates(conn, updates)

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
