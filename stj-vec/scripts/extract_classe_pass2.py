#!/usr/bin/env python3
"""Segundo passe: extrair classe dos docs restantes via ementa ou chunks 0-2.

Para docs que o pass1 nao conseguiu classificar (comecam com ACORDAO
generico), busca a classe na ementa ou nos primeiros chunks.
"""

import re
import sqlite3
import time

DB_PATH = "db/stj-vec.db"

CLASSE_PATTERNS = [
    (re.compile(r"\bagravos?\s+(?:regimentai?s?|interno)\b", re.I), "AGINT"),
    (re.compile(r"\bembargos\s+de\s+declara[cç][aã]o\b", re.I), "EDCL"),
    (re.compile(r"\bembargos\s+de\s+diverg[eê]ncia\b", re.I), "ERESP"),
    (re.compile(r"\bagravo\s+em\s+recurso\s+especial\b", re.I), "ARESP"),
    (re.compile(r"\brecurso\s+em\s+habeas\s+corpus\b", re.I), "RHC"),
    (re.compile(r"\brecurso\s+em\s+mandado\s+de\s+seguran[cç]a\b", re.I), "RMS"),
    (re.compile(r"\brecurso\s+especial\b", re.I), "RESP"),
    (re.compile(r"\brecurso\s+ordin[aá]rio\b", re.I), "RO"),
    (re.compile(r"\bmandado\s+de\s+seguran[cç]a\b", re.I), "MS"),
    (re.compile(r"\bhabeas\s+corpus\b", re.I), "HC"),
    (re.compile(r"\bconflito\s+(?:negativo\s+)?de\s+compet[eê]ncia\b", re.I), "CC"),
    (re.compile(r"\bmedida\s+cautelar\b", re.I), "MC"),
    (re.compile(r"\ba[cç][aã]o\s+rescis[oó]ria\b", re.I), "AR"),
    (re.compile(r"\breclama[cç][aã]o\b", re.I), "RCL"),
    (re.compile(r"\bpeti[cç][aã]o\b", re.I), "PET"),
    (re.compile(r"\bAREsp\b"), "ARESP"),
    (re.compile(r"\bREsp\b"), "RESP"),
    (re.compile(r"\bRHC\b"), "RHC"),
    (re.compile(r"\bRMS\b"), "RMS"),
    (re.compile(r"\bEAREsp\b"), "EARESP"),
    (re.compile(r"\bEREsp\b"), "ERESP"),
    (re.compile(r"\bAgInt\b"), "AGINT"),
    (re.compile(r"\bAgRg\b"), "AGRG"),
    (re.compile(r"\bEDcl\b"), "EDCL"),
    (re.compile(r"\bRcl\b"), "RCL"),
]


def extract_classe(text: str) -> str | None:
    for pattern, classe in CLASSE_PATTERNS:
        if pattern.search(text):
            return classe
    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-1000000")

    remaining = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE classe IS NULL OR classe = ''"
    ).fetchone()[0]
    print(f"Docs sem classe (antes): {remaining:,}", flush=True)

    # Buscar ementa + chunks 0-2 dos docs restantes
    print("Buscando conteudo dos docs restantes...", flush=True)
    t0 = time.time()

    # Primeiro: buscar na ementa (secao='ementa')
    cur = conn.execute(
        """
        SELECT d.id, GROUP_CONCAT(substr(c.content, 1, 500), ' ')
        FROM documents d
        JOIN chunks c ON c.doc_id = d.id
        WHERE (d.classe IS NULL OR d.classe = '')
        AND (c.secao = 'ementa' OR c.chunk_index <= 2)
        GROUP BY d.id
        """
    )

    updates = []
    stats = {}
    no_match = 0

    for doc_id, content in cur:
        if not content:
            no_match += 1
            continue
        classe = extract_classe(content)
        if classe:
            updates.append((classe, doc_id))
            stats[classe] = stats.get(classe, 0) + 1
        else:
            no_match += 1

    print(f"  ({time.time() - t0:.0f}s)", flush=True)
    print(f"  Matches: {len(updates):,}", flush=True)
    print(f"  Sem match: {no_match:,}", flush=True)

    print("\nDistribuicao:", flush=True)
    for classe, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {classe:12s} -> {count:>10,}", flush=True)

    if updates:
        print(f"\nAplicando {len(updates):,} updates...", flush=True)
        t1 = time.time()
        conn.executemany("UPDATE documents SET classe = ? WHERE id = ?", updates)
        conn.commit()
        print(f"  ({time.time() - t1:.0f}s)", flush=True)

    final = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE classe IS NULL OR classe = ''"
    ).fetchone()[0]
    print(f"\nDocs sem classe (depois): {final:,}", flush=True)
    print(f"Total classificados neste passe: {remaining - final:,}", flush=True)

    conn.close()


if __name__ == "__main__":
    main()
