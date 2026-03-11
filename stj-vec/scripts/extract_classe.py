#!/usr/bin/env python3
"""Extrair classe processual dos 1M docs sem metadados via regex no conteudo.

Estrategia: ler chunk_index=0 de cada doc sem processo/classe, detectar a classe
via padroes textuais no inicio do documento, e popular os campos processo e classe.

Como nao ha numero de processo no corpo do texto, popula apenas classe.
"""

import re
import sqlite3
import time

DB_PATH = "db/stj-vec.db"

# Padroes ordenados do mais especifico ao mais generico.
# Cada tupla: (regex compilado, classe STJ normalizada)
CLASSE_PATTERNS = [
    # Compostas (testar antes das simples)
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
    (re.compile(r"\bconflito\s+de\s+compet[eê]ncia\b", re.I), "CC"),
    (re.compile(r"\bmedida\s+cautelar\b", re.I), "MC"),
    (re.compile(r"\ba[cç][aã]o\s+rescis[oó]ria\b", re.I), "AR"),
    (re.compile(r"\breclama[cç][aã]o\b", re.I), "RCL"),
    (re.compile(r"\bpeti[cç][aã]o\b", re.I), "PET"),
    # Siglas diretas no texto (ex: "REsp", "HC", "AREsp")
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
    """Extrai classe processual do texto do primeiro chunk."""
    # Buscar apenas nos primeiros 500 chars (a classe aparece no inicio)
    snippet = text[:500]
    for pattern, classe in CLASSE_PATTERNS:
        if pattern.search(snippet):
            return classe
    return None


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-1000000")

    # Contar docs alvo
    total = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE processo IS NULL OR processo = ''"
    ).fetchone()[0]
    print(f"Docs sem metadados: {total:,}", flush=True)

    # Ler chunk_index=0 dos docs sem processo
    print("Lendo chunk_index=0 dos docs alvo...", flush=True)
    t0 = time.time()
    cur = conn.execute(
        """
        SELECT d.id, substr(c.content, 1, 500)
        FROM documents d
        JOIN chunks c ON c.doc_id = d.id AND c.chunk_index = 0
        WHERE d.processo IS NULL OR d.processo = ''
        """
    )

    updates = []
    stats = {}
    no_match = 0

    for doc_id, content in cur:
        classe = extract_classe(content)
        if classe:
            updates.append((classe, doc_id))
            stats[classe] = stats.get(classe, 0) + 1
        else:
            no_match += 1

    elapsed = time.time() - t0
    print(f"  Lidos em {elapsed:.0f}s", flush=True)
    print(f"  Matches: {len(updates):,} ({len(updates)*100/total:.1f}%)", flush=True)
    print(f"  Sem match: {no_match:,}", flush=True)

    # Distribuicao
    print("\nDistribuicao de classes detectadas:", flush=True)
    for classe, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {classe:12s} -> {count:>10,}", flush=True)

    # Aplicar updates
    if updates:
        print(f"\nAplicando {len(updates):,} updates...", flush=True)
        t1 = time.time()
        batch_size = 50000
        for i in range(0, len(updates), batch_size):
            batch = updates[i : i + batch_size]
            conn.executemany(
                "UPDATE documents SET classe = ? WHERE id = ?", batch
            )
            conn.commit()
            done = i + len(batch)
            print(f"  {done:,}/{len(updates):,}", flush=True)
        print(f"  ({time.time() - t1:.0f}s)", flush=True)

    # Verificacao final
    print("\n=== RESULTADO ===", flush=True)
    for row in conn.execute(
        """SELECT classe, COUNT(*) FROM documents
           WHERE classe IS NOT NULL AND classe != ''
           GROUP BY classe ORDER BY COUNT(*) DESC"""
    ):
        print(f"  {row[0]:12s} -> {row[1]:>10,}", flush=True)

    remaining = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE classe IS NULL OR classe = ''"
    ).fetchone()[0]
    print(f"\n  Sem classe: {remaining:,}", flush=True)

    conn.close()


if __name__ == "__main__":
    main()
