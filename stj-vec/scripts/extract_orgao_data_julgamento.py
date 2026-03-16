#!/usr/bin/env python3
"""
Extrai orgao_julgador e data_julgamento do texto dos chunks no SQLite.

Campos que nao existem nos JSONs de metadados -- precisam ser extraidos
do texto dos acordaos (chunks iniciais: 0, 1 e 2).

Decisoes monocraticas nao tem orgao julgador nem data de julgamento
(nao foram a plenario), entao o script foca em documentos tipo ACORDAO.

Limites conhecidos:
- ~11% dos acordaos nao tem cabecalho "ACORDAO / acordam os Ministros da X"
  (comecam direto com EMENTA). Orgao nao pode ser extraido desses.
- Maioria dos acordaos nao inclui data de julgamento no texto.
  Os 412K que ja tem data vieram dos JSONs de metadados.

Uso:
    python3 scripts/extract_orgao_data_julgamento.py [--dry-run] [--verbose]
"""

import re
import sqlite3
import sys
import time
from pathlib import Path

DB_PATH = Path("/home/opc/lex-vector/stj-vec/db/stj-vec.db")

BATCH_SIZE = 10_000
COMMIT_EVERY = 1_000

# Valores validos de orgao_julgador (normalizados)
ORGAOS_VALIDOS = {
    "CORTE ESPECIAL",
    "PRIMEIRA SEÇÃO",
    "PRIMEIRA TURMA",
    "QUARTA TURMA",
    "QUINTA TURMA",
    "SEGUNDA SEÇÃO",
    "SEGUNDA TURMA",
    "SEXTA TURMA",
    "TERCEIRA SEÇÃO",
    "TERCEIRA TURMA",
}

# Mapeamento de variantes para valor canonico
ORGAO_ALIASES = {
    "PRIMEIRA SECAO": "PRIMEIRA SEÇÃO",
    "SEGUNDA SECAO": "SEGUNDA SEÇÃO",
    "TERCEIRA SECAO": "TERCEIRA SEÇÃO",
}

# ============================================================
# Regex para orgao_julgador
# ============================================================
# Padroes tipicos no texto dos acordaos:
#   "acordam os Ministros da PRIMEIRA TURMA do Superior Tribunal"
#   "acordam os Ministros da CORTE ESPECIAL"
#   "TERCEIRA TURMA do Superior Tribunal de Justiça"

_ORGAO_NAMES = "|".join(sorted(ORGAOS_VALIDOS, key=len, reverse=True))
# Tambem aceita variantes sem cedilha
_ORGAO_NAMES_ALL = _ORGAO_NAMES + "|" + "|".join(ORGAO_ALIASES.keys())

RE_ORGAO_ACORDAM = re.compile(
    r"acordam\s+os\s+(?:Srs\.\s+)?Ministros\s+da\s+("
    + _ORGAO_NAMES_ALL
    + r")",
    re.IGNORECASE,
)

RE_ORGAO_STANDALONE = re.compile(
    r"\b(" + _ORGAO_NAMES_ALL + r")\s+do\s+Superior\s+Tribunal",
    re.IGNORECASE,
)


def extract_orgao(text: str) -> str | None:
    """Extrai orgao julgador do texto do chunk."""
    # Prioridade 1: padrao "acordam os Ministros da X"
    m = RE_ORGAO_ACORDAM.search(text)
    if m:
        return _normalize_orgao(m.group(1))

    # Prioridade 2: "X do Superior Tribunal"
    m = RE_ORGAO_STANDALONE.search(text)
    if m:
        return _normalize_orgao(m.group(1))

    return None


def _normalize_orgao(raw: str) -> str | None:
    upper = raw.upper().strip()
    if upper in ORGAOS_VALIDOS:
        return upper
    if upper in ORGAO_ALIASES:
        return ORGAO_ALIASES[upper]
    return None


# ============================================================
# Regex para data_julgamento
# ============================================================
# Padroes:
#   "em sessão virtual de 25/02/2022 a 03/03/2022"  -> usa ultima data
#   "em sessão de 22/02/2022"
#   ", julgado em 15/03/2024,"  -> cuidado com citacoes
#
# Para evitar pegar citacoes de outros julgados, priorizamos:
#   1. "sessao virtual de DD/MM/YYYY a DD/MM/YYYY"
#   2. "sessao de DD/MM/YYYY"
# E so usamos "julgado em" se aparece ANTES da ementa (nas primeiras
# 500 chars, que e tipicamente o cabecalho do acordao).

_DATE_PATTERN = r"(\d{2}/\d{2}/\d{4})"

RE_SESSAO_VIRTUAL = re.compile(
    r"sess[aã]o\s+virtual\s+de\s+" + _DATE_PATTERN + r"\s+a\s+" + _DATE_PATTERN,
    re.IGNORECASE,
)

RE_SESSAO_DE = re.compile(
    r"(?:em\s+)?sess[aã]o\s+de\s+" + _DATE_PATTERN,
    re.IGNORECASE,
)

RE_JULGADO_EM = re.compile(
    r"julgado\s+em\s+" + _DATE_PATTERN,
    re.IGNORECASE,
)


def parse_date(date_str: str) -> str | None:
    """Converte DD/MM/YYYY para YYYY-MM-DD. Retorna None se invalido."""
    parts = date_str.split("/")
    if len(parts) != 3:
        return None
    day, month, year = parts
    if not (1 <= int(month) <= 12 and 1 <= int(day) <= 31 and 1900 <= int(year) <= 2030):
        return None
    return f"{year}-{month}-{day}"


def extract_data_julgamento(text: str) -> str | None:
    """Extrai data de julgamento do texto do chunk."""
    # Prioridade 1: sessao virtual (usar ultima data -- fim da sessao)
    m = RE_SESSAO_VIRTUAL.search(text)
    if m:
        return parse_date(m.group(2))

    # Prioridade 2: "sessao de DD/MM/YYYY"
    m = RE_SESSAO_DE.search(text)
    if m:
        return parse_date(m.group(1))

    # Prioridade 3: "julgado em" -- so se antes do EMENTA/RELATORIO
    # para evitar citacoes de outros julgados
    header = text[:600]
    m = RE_JULGADO_EM.search(header)
    if m:
        return parse_date(m.group(1))

    return None


# ============================================================
# Main
# ============================================================

def run(dry_run: bool = False, verbose: bool = False):
    if not DB_PATH.exists():
        print(f"ERRO: banco nao encontrado em {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-512000")  # 512MB cache

    # Estatisticas iniciais
    total_docs = conn.execute("SELECT count(*) FROM documents").fetchone()[0]
    total_acordaos = conn.execute(
        "SELECT count(*) FROM documents WHERE tipo = 'ACÓRDÃO'"
    ).fetchone()[0]

    print(f"Total documentos: {total_docs:,}")
    print(f"Total acordaos: {total_acordaos:,}")
    print()

    # Processar orgao_julgador
    print("=" * 60)
    print("FASE 1: Extraindo orgao_julgador")
    print("=" * 60)
    orgao_stats = process_orgao(conn, dry_run, verbose)

    print()
    print("=" * 60)
    print("FASE 2: Extraindo data_julgamento")
    print("=" * 60)
    data_stats = process_data_julgamento(conn, dry_run, verbose)

    conn.close()

    # Relatorio final
    print()
    print("=" * 60)
    print(f"{'[DRY-RUN] ' if dry_run else ''}RELATORIO FINAL")
    print("=" * 60)
    print()
    print("orgao_julgador:")
    print(f"  Processados: {orgao_stats['processed']:,}")
    print(f"  Extraidos:   {orgao_stats['extracted']:,}")
    print(f"  Falharam:    {orgao_stats['failed']:,}")
    if orgao_stats['processed'] > 0:
        pct = orgao_stats['extracted'] / orgao_stats['processed'] * 100
        print(f"  Taxa extracao: {pct:.1f}%")
    if orgao_stats['distribution']:
        print(f"  Distribuicao:")
        for orgao, count in sorted(orgao_stats['distribution'].items(), key=lambda x: -x[1]):
            print(f"    {orgao}: {count:,}")

    print()
    print("data_julgamento:")
    print(f"  Processados: {data_stats['processed']:,}")
    print(f"  Extraidos:   {data_stats['extracted']:,}")
    print(f"  Falharam:    {data_stats['failed']:,}")
    if data_stats['processed'] > 0:
        pct = data_stats['extracted'] / data_stats['processed'] * 100
        print(f"  Taxa extracao: {pct:.1f}%")
    if data_stats['by_pattern']:
        print(f"  Por padrao:")
        for pattern, count in sorted(data_stats['by_pattern'].items(), key=lambda x: -x[1]):
            print(f"    {pattern}: {count:,}")


def process_orgao(conn: sqlite3.Connection, dry_run: bool, verbose: bool) -> dict:
    stats = {
        "processed": 0,
        "extracted": 0,
        "failed": 0,
        "distribution": {},
    }

    offset = 0
    updates_pending = 0
    t0 = time.time()

    while True:
        # Buscar batch de acordaos sem orgao_julgador
        rows = conn.execute(
            """SELECT d.id FROM documents d
               WHERE d.tipo = 'ACÓRDÃO'
                 AND (d.orgao_julgador IS NULL OR d.orgao_julgador = '')
               LIMIT ? OFFSET ?""",
            (BATCH_SIZE, offset),
        ).fetchall()

        if not rows:
            break

        doc_ids = [r[0] for r in rows]
        stats["processed"] += len(doc_ids)

        # Buscar chunks 0 e 1 para esses docs
        placeholders = ",".join("?" * len(doc_ids))
        chunks = conn.execute(
            f"""SELECT doc_id, chunk_index, content FROM chunks
                WHERE doc_id IN ({placeholders})
                  AND chunk_index <= 2
                ORDER BY doc_id, chunk_index""",
            doc_ids,
        ).fetchall()

        # Agrupar chunks por doc_id
        doc_chunks: dict[str, str] = {}
        for doc_id, _idx, content in chunks:
            doc_id_str = str(doc_id)
            if doc_id_str in doc_chunks:
                doc_chunks[doc_id_str] += "\n" + content
            else:
                doc_chunks[doc_id_str] = content

        for doc_id in doc_ids:
            text = doc_chunks.get(str(doc_id), "")
            if not text:
                stats["failed"] += 1
                continue

            orgao = extract_orgao(text)
            if orgao:
                stats["extracted"] += 1
                stats["distribution"][orgao] = stats["distribution"].get(orgao, 0) + 1

                if not dry_run:
                    conn.execute(
                        "UPDATE documents SET orgao_julgador = ? WHERE id = ?",
                        (orgao, doc_id),
                    )
                    updates_pending += 1

                    if updates_pending >= COMMIT_EVERY:
                        conn.commit()
                        updates_pending = 0

                if verbose and stats["extracted"] <= 5:
                    print(f"  [orgao] doc={doc_id} -> {orgao}")
            else:
                stats["failed"] += 1
                if verbose and stats["failed"] <= 3:
                    snippet = text[:200].replace("\r", " ").replace("\n", " ")
                    print(f"  [orgao] FALHA doc={doc_id}: {snippet}")

        elapsed = time.time() - t0
        print(
            f"  Batch offset={offset:,}: "
            f"processados={stats['processed']:,} "
            f"extraidos={stats['extracted']:,} "
            f"falharam={stats['failed']:,} "
            f"({elapsed:.0f}s)"
        )

        offset += BATCH_SIZE

    # Commit final
    if not dry_run and updates_pending > 0:
        conn.commit()

    return stats


def process_data_julgamento(conn: sqlite3.Connection, dry_run: bool, verbose: bool) -> dict:
    stats = {
        "processed": 0,
        "extracted": 0,
        "failed": 0,
        "by_pattern": {},
    }

    offset = 0
    updates_pending = 0
    t0 = time.time()

    while True:
        # Buscar batch de acordaos sem data_julgamento
        rows = conn.execute(
            """SELECT d.id FROM documents d
               WHERE d.tipo = 'ACÓRDÃO'
                 AND (d.data_julgamento IS NULL OR d.data_julgamento = '')
               LIMIT ? OFFSET ?""",
            (BATCH_SIZE, offset),
        ).fetchall()

        if not rows:
            break

        doc_ids = [r[0] for r in rows]
        stats["processed"] += len(doc_ids)

        placeholders = ",".join("?" * len(doc_ids))
        chunks = conn.execute(
            f"""SELECT doc_id, chunk_index, content FROM chunks
                WHERE doc_id IN ({placeholders})
                  AND chunk_index <= 2
                ORDER BY doc_id, chunk_index""",
            doc_ids,
        ).fetchall()

        doc_chunks: dict[str, str] = {}
        for doc_id, _idx, content in chunks:
            doc_id_str = str(doc_id)
            if doc_id_str in doc_chunks:
                doc_chunks[doc_id_str] += "\n" + content
            else:
                doc_chunks[doc_id_str] = content

        for doc_id in doc_ids:
            text = doc_chunks.get(str(doc_id), "")
            if not text:
                stats["failed"] += 1
                continue

            data = extract_data_julgamento(text)
            if data:
                stats["extracted"] += 1
                # Identificar qual padrao casou (para estatisticas)
                pattern = _identify_date_pattern(text)
                stats["by_pattern"][pattern] = stats["by_pattern"].get(pattern, 0) + 1

                if not dry_run:
                    conn.execute(
                        "UPDATE documents SET data_julgamento = ? WHERE id = ?",
                        (data, doc_id),
                    )
                    updates_pending += 1

                    if updates_pending >= COMMIT_EVERY:
                        conn.commit()
                        updates_pending = 0

                if verbose and stats["extracted"] <= 5:
                    print(f"  [data] doc={doc_id} -> {data}")
            else:
                stats["failed"] += 1
                if verbose and stats["failed"] <= 3:
                    snippet = text[:200].replace("\r", " ").replace("\n", " ")
                    print(f"  [data] FALHA doc={doc_id}: {snippet}")

        elapsed = time.time() - t0
        print(
            f"  Batch offset={offset:,}: "
            f"processados={stats['processed']:,} "
            f"extraidos={stats['extracted']:,} "
            f"falharam={stats['failed']:,} "
            f"({elapsed:.0f}s)"
        )

        offset += BATCH_SIZE

    if not dry_run and updates_pending > 0:
        conn.commit()

    return stats


def _identify_date_pattern(text: str) -> str:
    if RE_SESSAO_VIRTUAL.search(text):
        return "sessao_virtual"
    if RE_SESSAO_DE.search(text):
        return "sessao_de"
    header = text[:600]
    if RE_JULGADO_EM.search(header):
        return "julgado_em"
    return "desconhecido"


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    verb = "--verbose" in sys.argv

    if dry:
        print("=== DRY RUN (nenhuma alteracao sera feita) ===")
    print()

    run(dry_run=dry, verbose=verb)
