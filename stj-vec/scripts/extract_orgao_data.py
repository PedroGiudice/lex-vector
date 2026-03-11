#!/usr/bin/env python3
"""Extrair orgao_julgador e data_julgamento dos chunks de acordaos.

Padroes nos acordaos STJ:
  - "Ministros da PRIMEIRA TURMA" -> orgao = "PRIMEIRA TURMA"
  - "sessao virtual de 04/02/2025 a 10/02/2025" -> data = "2025-02-04"
  - "Sessao de 13/08/2024" -> data = "2024-08-13"
"""

import re
import sqlite3
import time

DB_PATH = "db/stj-vec.db"

# Orgao julgador
RE_ORGAO = re.compile(
    r"Ministros\s+d[aoe]\s+"
    r"(PRIMEIRA TURMA|SEGUNDA TURMA|TERCEIRA TURMA|QUARTA TURMA|"
    r"QUINTA TURMA|SEXTA TURMA|CORTE ESPECIAL|"
    r"PRIMEIRA SE[CÇ][AÃ]O|SEGUNDA SE[CÇ][AÃ]O|TERCEIRA SE[CÇ][AÃ]O|"
    r"Turma)",
    re.I,
)

# Data de julgamento -- "sessao (virtual)? de DD/MM/AAAA"
RE_DATA = re.compile(
    r"[Ss]ess[aã]o\s+(?:[Vv]irtual\s+)?de\s+(\d{2}/\d{2}/\d{4})"
)


def parse_data(match_str: str) -> str | None:
    """Converte DD/MM/AAAA para AAAA-MM-DD."""
    try:
        d, m, y = match_str.split("/")
        return f"{y}-{m}-{d}"
    except Exception:
        return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-1000000")

    # Estado atual
    cur_orgao = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE orgao_julgador IS NOT NULL AND orgao_julgador != ''"
    ).fetchone()[0]
    cur_data = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE data_julgamento IS NOT NULL AND data_julgamento != ''"
    ).fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    print(f"Estado atual: orgao={cur_orgao:,}/{total:,}, data_julg={cur_data:,}/{total:,}", flush=True)

    # Ler chunks 0-3 de todos os docs (orgao/data podem estar em qualquer doc, nao so sem metadados)
    print("\nLendo chunks 0-3 de todos os docs...", flush=True)
    t0 = time.time()

    cur = conn.execute(
        """
        SELECT d.id, GROUP_CONCAT(substr(c.content, 1, 500), ' ')
        FROM documents d
        JOIN chunks c ON c.doc_id = d.id AND c.chunk_index <= 3
        WHERE (d.orgao_julgador IS NULL OR d.orgao_julgador = ''
               OR d.data_julgamento IS NULL OR d.data_julgamento = '')
        GROUP BY d.id
        """
    )

    orgao_updates = []
    data_updates = []
    orgao_stats = {}
    rows_read = 0

    for doc_id, content in cur:
        rows_read += 1
        if not content:
            continue

        m_orgao = RE_ORGAO.search(content)
        if m_orgao:
            orgao = m_orgao.group(1).upper()
            # Normalizar "TURMA" isolado
            if orgao == "TURMA":
                orgao = "TURMA (NAO ESPECIFICADA)"
            orgao_updates.append((orgao, doc_id))
            orgao_stats[orgao] = orgao_stats.get(orgao, 0) + 1

        m_data = RE_DATA.search(content)
        if m_data:
            data_iso = parse_data(m_data.group(1))
            if data_iso:
                data_updates.append((data_iso, doc_id))

    elapsed = time.time() - t0
    print(f"  {rows_read:,} docs lidos em {elapsed:.0f}s", flush=True)
    print(f"  orgao_julgador: {len(orgao_updates):,} matches", flush=True)
    print(f"  data_julgamento: {len(data_updates):,} matches", flush=True)

    print("\nDistribuicao orgao_julgador:", flush=True)
    for orgao, count in sorted(orgao_stats.items(), key=lambda x: -x[1]):
        print(f"  {orgao:30s} -> {count:>10,}", flush=True)

    # Aplicar orgao_julgador
    if orgao_updates:
        print(f"\nAplicando {len(orgao_updates):,} orgao_julgador...", flush=True)
        t1 = time.time()
        batch_size = 50000
        for i in range(0, len(orgao_updates), batch_size):
            batch = orgao_updates[i : i + batch_size]
            conn.executemany("UPDATE documents SET orgao_julgador = ? WHERE id = ?", batch)
            conn.commit()
            print(f"  {i + len(batch):,}/{len(orgao_updates):,}", flush=True)
        print(f"  ({time.time() - t1:.0f}s)", flush=True)

    # Aplicar data_julgamento
    if data_updates:
        print(f"\nAplicando {len(data_updates):,} data_julgamento...", flush=True)
        t2 = time.time()
        for i in range(0, len(data_updates), batch_size):
            batch = data_updates[i : i + batch_size]
            conn.executemany("UPDATE documents SET data_julgamento = ? WHERE id = ?", batch)
            conn.commit()
            print(f"  {i + len(batch):,}/{len(data_updates):,}", flush=True)
        print(f"  ({time.time() - t2:.0f}s)", flush=True)

    # Verificacao
    print("\n=== RESULTADO ===", flush=True)
    new_orgao = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE orgao_julgador IS NOT NULL AND orgao_julgador != ''"
    ).fetchone()[0]
    new_data = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE data_julgamento IS NOT NULL AND data_julgamento != ''"
    ).fetchone()[0]
    print(f"  orgao_julgador: {cur_orgao:,} -> {new_orgao:,} (+{new_orgao - cur_orgao:,})", flush=True)
    print(f"  data_julgamento: {cur_data:,} -> {new_data:,} (+{new_data - cur_data:,})", flush=True)

    conn.close()


if __name__ == "__main__":
    main()
