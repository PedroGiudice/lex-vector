#!/usr/bin/env python3
"""
Validador de Schema SQL para SQLite.
Testa sintaxe e verifica estrutura do banco.
"""

import sqlite3
import sys
from pathlib import Path

def validate_schema(schema_path: Path, db_path: Path = None):
    """Valida schema SQL criando banco temporário."""

    # Usar banco em memória se não especificado
    if db_path is None:
        db_path = ":memory:"

    print(f"📄 Lendo schema: {schema_path}")
    schema_sql = schema_path.read_text(encoding='utf-8')

    print(f"💾 Criando banco de dados: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Executar schema
        print("⚙️  Executando schema SQL...")
        cursor.executescript(schema_sql)

        # Verificar tabelas criadas
        cursor.execute("""
            SELECT name, type FROM sqlite_master
            WHERE type IN ('table', 'view', 'index', 'trigger')
            ORDER BY type, name
        """)

        objects = cursor.fetchall()

        # Agrupar por tipo
        tables = [name for name, type_ in objects if type_ == 'table']
        views = [name for name, type_ in objects if type_ == 'view']
        indexes = [name for name, type_ in objects if type_ == 'index']
        triggers = [name for name, type_ in objects if type_ == 'trigger']

        print("\n✅ SCHEMA VÁLIDO!\n")
        print("=" * 80)

        print(f"\n📊 TABELAS ({len(tables)}):")
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"  • {table:30} ({len(columns)} colunas)")

        print(f"\n👁️  VIEWS ({len(views)}):")
        for view in views:
            print(f"  • {view}")

        print(f"\n🔍 ÍNDICES ({len(indexes)}):")
        for index in indexes:
            if not index.startswith('sqlite_autoindex'):
                print(f"  • {index}")

        print(f"\n⚡ TRIGGERS ({len(triggers)}):")
        for trigger in triggers:
            print(f"  • {trigger}")

        # Verificar integridade
        print("\n🔧 Verificando integridade...")
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]

        if integrity == "ok":
            print("  ✅ Integridade: OK")
        else:
            print(f"  ⚠️  Integridade: {integrity}")
            return False

        # Verificar foreign keys
        cursor.execute("PRAGMA foreign_key_check")
        fk_issues = cursor.fetchall()

        if not fk_issues:
            print("  ✅ Foreign keys: OK")
        else:
            print(f"  ⚠️  Foreign key issues: {len(fk_issues)}")
            for issue in fk_issues:
                print(f"    - {issue}")
            return False

        # Testar inserção simples
        print("\n🧪 Testando inserção de dados...")
        test_id = "550e8400-e29b-41d4-a716-446655440000"
        test_hash = "a" * 64

        cursor.execute("""
            INSERT INTO publicacoes (
                id, hash_conteudo, tribunal, tipo_publicacao,
                texto_html, texto_limpo, data_publicacao, fonte
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_id,
            test_hash,
            'STJ',
            'Acórdão',
            '<p>Teste HTML</p>',
            'Teste texto limpo',
            '2025-11-20',
            'DJEN'
        ))

        # Verificar FTS5
        cursor.execute("SELECT * FROM publicacoes_fts WHERE rowid = 1")
        fts_result = cursor.fetchone()

        if fts_result:
            print("  ✅ FTS5 sincronizado via triggers")
        else:
            print("  ⚠️  FTS5 não sincronizou")
            return False

        # Verificar views
        cursor.execute("SELECT * FROM v_stats")
        stats = cursor.fetchone()
        if stats and stats[0] == 1:  # total_publicacoes
            print("  ✅ Views funcionando")
        else:
            print("  ⚠️  Views não retornam dados esperados")
            return False

        print("\n" + "=" * 80)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("=" * 80)

        return True

    except sqlite3.Error as e:
        print(f"\n❌ ERRO SQL: {e}")
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    schema_path = Path(__file__).parent / "schema.sql"

    if not schema_path.exists():
        print(f"❌ Schema não encontrado: {schema_path}")
        sys.exit(1)

    success = validate_schema(schema_path)
    sys.exit(0 if success else 1)
