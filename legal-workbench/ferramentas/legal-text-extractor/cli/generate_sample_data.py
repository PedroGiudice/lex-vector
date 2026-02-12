#!/usr/bin/env python3
"""
Gera dados de exemplo para testar o CLI de estatisticas.

Usage:
    python cli/generate_sample_data.py --db data/sample_context.db
"""

import json
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import typer

app = typer.Typer()


def init_schema(conn: sqlite3.Connection):
    """Inicializa schema do banco"""
    schema = """
    CREATE TABLE IF NOT EXISTS caso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_cnj TEXT UNIQUE NOT NULL,
        sistema TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_caso_numero_cnj ON caso(numero_cnj);

    CREATE TABLE IF NOT EXISTS observed_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caso_id INTEGER NOT NULL,
        pattern_type TEXT NOT NULL,
        signature_hash TEXT NOT NULL,
        signature_vector TEXT NOT NULL,
        first_seen_page INTEGER NOT NULL,
        last_seen_page INTEGER NOT NULL,
        created_by_engine TEXT NOT NULL,
        engine_quality_score REAL NOT NULL,
        avg_confidence REAL,
        suggested_bbox TEXT,
        suggested_engine TEXT,
        occurrence_count INTEGER DEFAULT 1,
        divergence_count INTEGER DEFAULT 0,
        deprecated BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (caso_id) REFERENCES caso(id)
    );

    CREATE INDEX IF NOT EXISTS idx_patterns_caso ON observed_patterns(caso_id);
    CREATE INDEX IF NOT EXISTS idx_patterns_hash ON observed_patterns(signature_hash);
    CREATE INDEX IF NOT EXISTS idx_patterns_type ON observed_patterns(pattern_type);
    CREATE INDEX IF NOT EXISTS idx_patterns_deprecated ON observed_patterns(deprecated);
    CREATE INDEX IF NOT EXISTS idx_patterns_engine ON observed_patterns(created_by_engine);

    CREATE TABLE IF NOT EXISTS divergences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_id INTEGER NOT NULL,
        page_num INTEGER NOT NULL,
        expected_confidence REAL NOT NULL,
        actual_confidence REAL NOT NULL,
        engine_used TEXT NOT NULL,
        reason TEXT,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (pattern_id) REFERENCES observed_patterns(id)
    );

    CREATE INDEX IF NOT EXISTS idx_divergences_pattern ON divergences(pattern_id);
    """
    conn.executescript(schema)
    conn.commit()


def generate_cnj() -> str:
    """Gera numero CNJ aleatorio"""
    seq = random.randint(1, 9999999)
    digit = random.randint(10, 99)
    year = random.randint(2020, 2025)
    seg = random.choice([1, 4, 5, 8])
    trib = random.randint(1, 27)
    vara = random.randint(1, 100)
    return f"{seq:07d}-{digit}.{year}.{seg}.{trib:02d}.{vara:04d}"


def generate_signature() -> tuple:
    """Gera assinatura aleatoria"""
    features = [round(random.random(), 4) for _ in range(5)]
    hash_val = f"{random.randint(100000, 999999):x}"
    return features, hash_val


@app.command()
def generate(
    db: Path = typer.Option(
        Path("data/sample_context.db"),
        "--db",
        "-d",
        help="Caminho para o banco de dados",
    ),
    casos: int = typer.Option(
        15,
        "--casos",
        "-c",
        help="Numero de casos a gerar",
    ),
    patterns_per_caso: int = typer.Option(
        10,
        "--patterns",
        "-p",
        help="Padroes por caso (media)",
    ),
):
    """
    Gera dados de exemplo para o Context Store.
    """
    # Ensure parent directory exists
    db.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing database
    if db.exists():
        db.unlink()

    conn = sqlite3.connect(db)
    init_schema(conn)
    cursor = conn.cursor()

    engines = ["marker", "pdfplumber", "tesseract"]
    engine_quality = {"marker": 1.0, "pdfplumber": 0.9, "tesseract": 0.7}
    pattern_types = ["header", "footer", "table", "text_block", "image", "signature", "stamp"]
    sistemas = ["pje", "eproc", "tucujuris", "projudi", "saj"]

    print(f"Gerando {casos} casos com ~{patterns_per_caso} padroes cada...")

    caso_ids = []
    for i in range(casos):
        cnj = generate_cnj()
        sistema = random.choice(sistemas)
        created = datetime.now() - timedelta(days=random.randint(0, 180))

        cursor.execute(
            "INSERT INTO caso (numero_cnj, sistema, created_at) VALUES (?, ?, ?)",
            (cnj, sistema, created.isoformat()),
        )
        caso_ids.append(cursor.lastrowid)

    print(f"  {len(caso_ids)} casos criados")

    # Generate patterns
    pattern_ids = []
    total_patterns = 0
    for caso_id in caso_ids:
        n_patterns = random.randint(max(1, patterns_per_caso - 5), patterns_per_caso + 5)

        for _ in range(n_patterns):
            engine = random.choices(
                engines,
                weights=[0.5, 0.35, 0.15],  # Marker mais comum
                k=1,
            )[0]

            pattern_type = random.choice(pattern_types)
            features, sig_hash = generate_signature()

            # Confidence varies by engine
            base_conf = {
                "marker": 0.85,
                "pdfplumber": 0.75,
                "tesseract": 0.65,
            }[engine]
            confidence = min(1.0, max(0.3, base_conf + random.uniform(-0.15, 0.15)))

            page = random.randint(1, 50)
            occurrences = random.randint(1, 20)

            # Some patterns are deprecated
            deprecated = random.random() < 0.1

            created = datetime.now() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
            )

            cursor.execute(
                """
                INSERT INTO observed_patterns (
                    caso_id, pattern_type, signature_hash, signature_vector,
                    first_seen_page, last_seen_page, created_by_engine,
                    engine_quality_score, avg_confidence, occurrence_count,
                    deprecated, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    caso_id,
                    pattern_type,
                    sig_hash,
                    json.dumps(features),
                    page,
                    page + random.randint(0, 10),
                    engine,
                    engine_quality[engine],
                    confidence,
                    occurrences,
                    deprecated,
                    created.isoformat(),
                ),
            )
            pattern_ids.append(cursor.lastrowid)
            total_patterns += 1

    print(f"  {total_patterns} padroes criados")

    # Generate some divergences
    n_divergences = int(total_patterns * 0.15)
    divergence_patterns = random.sample(pattern_ids, min(n_divergences, len(pattern_ids)))

    for pattern_id in divergence_patterns:
        engine = random.choice(engines)
        expected = random.uniform(0.7, 0.95)
        actual = expected - random.uniform(0.2, 0.4)  # Always lower

        cursor.execute(
            """
            INSERT INTO divergences (
                pattern_id, page_num, expected_confidence,
                actual_confidence, engine_used
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (pattern_id, random.randint(1, 50), expected, max(0.1, actual), engine),
        )

    print(f"  {len(divergence_patterns)} divergencias criadas")

    conn.commit()
    conn.close()

    print(f"\nDatabase criado: {db}")
    print("\nPara visualizar:")
    print(f"  python -m cli.context_stats dashboard --db {db}")


if __name__ == "__main__":
    app()
