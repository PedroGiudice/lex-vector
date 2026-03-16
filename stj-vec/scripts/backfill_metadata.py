#!/usr/bin/env python3
"""
Backfill de metadados para documentos que ficaram sem dados
por causa de arquivos de metadados sem extensão .json.

Lê os 378 JSONs sem extensão em juridico-data/stj/integras/metadata/
e faz UPDATE nos campos processo, ministro, assuntos, teor no SQLite.

Uso:
    python3 scripts/backfill_metadata.py [--dry-run]
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

METADATA_DIR = Path("/home/opc/juridico-data/stj/integras/metadata")
DB_PATH = Path("/home/opc/lex-vector/stj-vec/db/stj-vec.db")

def find_files_without_extension() -> list[Path]:
    """Encontra arquivos metadados* sem extensão .json."""
    files = []
    for f in sorted(METADATA_DIR.iterdir()):
        if f.name.startswith("metadados20") and not f.name.endswith(".json"):
            files.append(f)
    return files


def load_metadata(path: Path) -> list[dict]:
    """Carrega JSON de metadados."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "Metadados" in data:
        return data["Metadados"]
    return [data]


def backfill(dry_run: bool = False):
    files = find_files_without_extension()
    print(f"Arquivos sem extensão: {len(files)}")

    if not files:
        print("Nenhum arquivo para processar.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    total_updated = 0
    total_items = 0
    total_not_found = 0

    skipped_files = []
    for i, path in enumerate(files):
        try:
            items = load_metadata(path)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            skipped_files.append((path.name, str(e)[:80]))
            print(f"  SKIP {path.name}: {str(e)[:80]}")
            continue
        source = path.name.replace("metadados", "")
        batch_updated = 0

        for item in items:
            total_items += 1
            doc_id = str(item.get("SeqDocumento", ""))
            if not doc_id:
                continue

            processo = item.get("processo", "") or ""
            ministro = item.get("NM_MINISTRO") or item.get("ministro", "") or ""
            assuntos = item.get("assuntos", "") or ""
            teor = item.get("teor", "") or ""

            if dry_run:
                batch_updated += 1
                continue

            cursor = conn.execute(
                """UPDATE documents
                   SET processo = ?, ministro = ?, assuntos = ?, teor = ?
                   WHERE id = ? AND (processo = '' OR processo IS NULL)""",
                (processo, ministro, assuntos, teor, int(doc_id)),
            )
            if cursor.rowcount > 0:
                batch_updated += 1
            else:
                total_not_found += 1

        if not dry_run and batch_updated > 0:
            conn.commit()

        total_updated += batch_updated
        if (i + 1) % 50 == 0 or i == len(files) - 1:
            print(
                f"  [{i+1}/{len(files)}] {source}: "
                f"{batch_updated}/{len(items)} atualizados "
                f"(acum: {total_updated}/{total_items})"
            )

    conn.close()

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"\n{prefix}Concluído:")
    print(f"  Arquivos processados: {len(files) - len(skipped_files)}")
    print(f"  Arquivos com erro: {len(skipped_files)}")
    print(f"  Itens no JSON: {total_items}")
    print(f"  Documentos atualizados: {total_updated}")
    print(f"  Não encontrados no SQLite: {total_not_found}")
    if skipped_files:
        print(f"\n  Arquivos com erro (JSON corrompido):")
        for name, err in skipped_files:
            print(f"    {name}: {err}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    if dry:
        print("=== DRY RUN (nenhuma alteração será feita) ===\n")
    backfill(dry_run=dry)
