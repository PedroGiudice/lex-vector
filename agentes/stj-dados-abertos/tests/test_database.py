"""
Testes unitários para database.py (DuckDB).
"""
import pytest
import tempfile
import uuid
from pathlib import Path
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.database import STJDatabase


@pytest.fixture
def temp_db():
    """Fixture: banco temporário para testes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.duckdb"
        yield db_path


@pytest.fixture
def sample_record():
    """Fixture: registro de teste válido."""
    return {
        'id': str(uuid.uuid4()),
        'numero_processo': 'REsp 1234567/SP',
        'hash_conteudo': 'test_hash_' + str(uuid.uuid4()),
        'tribunal': 'STJ',
        'orgao_julgador': 'Terceira Turma',
        'tipo_decisao': 'Acórdão',
        'classe_processual': 'REsp',
        'ementa': 'TESTE. EMENTA DE TESTE. RESPONSABILIDADE CIVIL.',
        'texto_integral': 'Texto completo do acórdão de teste com responsabilidade civil...',
        'relator': 'Ministro Paulo de Tarso Sanseverino',
        'data_publicacao': '2024-11-20T00:00:00',
        'data_julgamento': '2024-11-15T00:00:00',
        'assuntos': '["Direito Civil", "Responsabilidade Civil"]',
        'fonte': 'STJ-Dados-Abertos',
        'fonte_url': 'https://stj.jus.br/test',
        'metadata': '{}'
    }


class TestDatabaseConnection:
    """Testes de conexão e inicialização."""

    def test_create_database(self, temp_db):
        """Testa criação de banco."""
        with STJDatabase(temp_db) as db:
            assert db.conn is not None
            assert temp_db.exists()

    def test_create_schema(self, temp_db):
        """Testa criação de schema."""
        with STJDatabase(temp_db) as db:
            db.criar_schema()

            # Verificar tabela existe
            result = db.conn.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'acordaos'"
            ).fetchone()
            assert result[0] == 1

    def test_create_indexes(self, temp_db):
        """Testa criação de índices."""
        with STJDatabase(temp_db) as db:
            db.criar_schema()

            # Verificar índices existem
            indexes = db.conn.execute(
                "SELECT index_name FROM duckdb_indexes() WHERE table_name = 'acordaos'"
            ).fetchall()

            index_names = [idx[0] for idx in indexes]

            # Verificar índices principais
            assert 'idx_hash' in index_names
            assert 'idx_processo' in index_names
            assert 'idx_orgao' in index_names


class TestInsertOperations:
    """Testes de inserção."""

    def test_insert_single_record(self, temp_db, sample_record):
        """Testa inserção de registro único."""
        with STJDatabase(temp_db) as db:
            db.criar_schema()

            inseridos, duplicados, erros = db.inserir_batch([sample_record])

            assert inseridos == 1
            assert duplicados == 0
            assert erros == 0

            # Verificar registro foi inserido
            count = db.conn.execute("SELECT COUNT(*) FROM acordaos").fetchone()[0]
            assert count == 1

    def test_insert_duplicate_hash(self, temp_db, sample_record):
        """Testa deduplicação por hash."""
        with STJDatabase(temp_db) as db:
            db.criar_schema()

            # Inserir primeiro
            db.inserir_batch([sample_record])

            # Tentar inserir novamente (mesmo hash)
            inseridos, duplicados, erros = db.inserir_batch([sample_record])

            assert inseridos == 0
            assert duplicados == 1
            assert erros == 0

            # Banco deve ter apenas 1 registro
            count = db.conn.execute("SELECT COUNT(*) FROM acordaos").fetchone()[0]
            assert count == 1

    def test_insert_batch(self, temp_db):
        """Testa inserção em lote."""
        with STJDatabase(temp_db) as db:
            db.criar_schema()

            # Criar 100 registros únicos
            registros = []
            for i in range(100):
                registros.append({
                    'id': str(uuid.uuid4()),
                    'numero_processo': f'REsp {i}/SP',
                    'hash_conteudo': f'hash_{i}_{uuid.uuid4()}',
                    'tribunal': 'STJ',
                    'orgao_julgador': 'Terceira Turma',
                    'tipo_decisao': 'Acórdão',
                    'classe_processual': 'REsp',
                    'ementa': f'Ementa teste {i}',
                    'texto_integral': f'Texto teste {i}',
                    'relator': 'Ministro Teste',
                    'data_publicacao': '2024-11-20T00:00:00',
                    'data_julgamento': '2024-11-15T00:00:00',
                    'assuntos': '[]',
                    'fonte': 'STJ-Dados-Abertos',
                    'fonte_url': 'https://stj.jus.br/test',
                    'metadata': '{}'
                })

            inseridos, duplicados, erros = db.inserir_batch(registros)

            assert inseridos == 100
            assert duplicados == 0
            assert erros == 0

            # Verificar contagem
            count = db.conn.execute("SELECT COUNT(*) FROM acordaos").fetchone()[0]
            assert count == 100


class TestSearchOperations:
    """Testes de busca."""

    @pytest.fixture
    def db_with_data(self, temp_db):
        """Fixture: banco com dados de teste."""
        with STJDatabase(temp_db) as db:
            db.criar_schema()

            # Inserir registros de teste
            registros = [
                {
                    'id': str(uuid.uuid4()),
                    'numero_processo': 'REsp 1111111/SP',
                    'hash_conteudo': f'hash_1_{uuid.uuid4()}',
                    'tribunal': 'STJ',
                    'orgao_julgador': 'Terceira Turma',
                    'tipo_decisao': 'Acórdão',
                    'classe_processual': 'REsp',
                    'ementa': 'RESPONSABILIDADE CIVIL. DANO MORAL. QUANTUM INDENIZATÓRIO.',
                    'texto_integral': 'Trata-se de recurso especial sobre dano moral em relação de consumo...',
                    'relator': 'Ministro Paulo de Tarso Sanseverino',
                    'data_publicacao': '2024-11-20T00:00:00',
                    'data_julgamento': '2024-11-15T00:00:00',
                    'assuntos': '["Direito Civil", "Responsabilidade Civil", "Dano Moral"]',
                    'fonte': 'STJ-Dados-Abertos',
                    'fonte_url': 'https://stj.jus.br/test',
                    'metadata': '{}'
                },
                {
                    'id': str(uuid.uuid4()),
                    'numero_processo': 'REsp 2222222/RJ',
                    'hash_conteudo': f'hash_2_{uuid.uuid4()}',
                    'tribunal': 'STJ',
                    'orgao_julgador': 'Segunda Turma',
                    'tipo_decisao': 'Acórdão',
                    'classe_processual': 'REsp',
                    'ementa': 'DIREITO CONTRATUAL. RESCISÃO. BOA-FÉ OBJETIVA.',
                    'texto_integral': 'Recurso sobre rescisão contratual e aplicação da boa-fé objetiva...',
                    'relator': 'Ministro Teste',
                    'data_publicacao': '2024-11-19T00:00:00',
                    'data_julgamento': '2024-11-10T00:00:00',
                    'assuntos': '["Direito Civil", "Contratos"]',
                    'fonte': 'STJ-Dados-Abertos',
                    'fonte_url': 'https://stj.jus.br/test',
                    'metadata': '{}'
                }
            ]

            db.inserir_batch(registros)

        # Re-abrir para testes
        return STJDatabase(temp_db)

    def test_buscar_ementa(self, temp_db, db_with_data):
        """Testa busca em ementa."""
        with db_with_data as db:
            # Buscar termo que existe
            resultados = db.buscar_ementa("RESPONSABILIDADE", dias=365)
            assert len(resultados) > 0
            assert "RESPONSABILIDADE" in resultados[0]['ementa']

            # Buscar termo que não existe
            resultados = db.buscar_ementa("INEXISTENTE", dias=365)
            assert len(resultados) == 0

    def test_buscar_ementa_com_filtro_orgao(self, temp_db, db_with_data):
        """Testa busca em ementa com filtro de órgão."""
        with db_with_data as db:
            # Buscar apenas Terceira Turma
            resultados = db.buscar_ementa("CIVIL", orgao="Terceira Turma", dias=365)
            assert all(r['orgao_julgador'] == "Terceira Turma" for r in resultados)

            # Buscar apenas Segunda Turma
            resultados = db.buscar_ementa("CONTRATUAL", orgao="Segunda Turma", dias=365)
            assert all(r['orgao_julgador'] == "Segunda Turma" for r in resultados)

    def test_buscar_acordao(self, temp_db, db_with_data):
        """Testa busca em inteiro teor."""
        with db_with_data as db:
            # Buscar termo no inteiro teor
            resultados = db.buscar_acordao("relação de consumo", dias=365)
            assert len(resultados) > 0

            # Verificar que encontrou no texto integral
            resultados = db.buscar_acordao("rescisão contratual", dias=365)
            assert len(resultados) > 0


class TestStatistics:
    """Testes de estatísticas."""

    def test_obter_estatisticas(self, temp_db, sample_record):
        """Testa obtenção de estatísticas."""
        with STJDatabase(temp_db) as db:
            db.criar_schema()
            db.inserir_batch([sample_record])

            stats = db.obter_estatisticas()

            assert stats['total_acordaos'] == 1
            assert 'por_orgao' in stats
            assert 'por_tipo' in stats
            assert 'periodo' in stats
            assert stats['tamanho_db_mb'] > 0

    def test_estatisticas_por_orgao(self, temp_db):
        """Testa estatísticas por órgão."""
        with STJDatabase(temp_db) as db:
            db.criar_schema()

            # Inserir registros de diferentes órgãos
            registros = []
            for i in range(10):
                orgao = "Terceira Turma" if i < 5 else "Segunda Turma"
                registros.append({
                    'id': str(uuid.uuid4()),
                    'numero_processo': f'REsp {i}/SP',
                    'hash_conteudo': f'hash_{i}_{uuid.uuid4()}',
                    'tribunal': 'STJ',
                    'orgao_julgador': orgao,
                    'tipo_decisao': 'Acórdão',
                    'classe_processual': 'REsp',
                    'ementa': f'Ementa {i}',
                    'texto_integral': f'Texto {i}',
                    'relator': 'Ministro Teste',
                    'data_publicacao': '2024-11-20T00:00:00',
                    'data_julgamento': '2024-11-15T00:00:00',
                    'assuntos': '[]',
                    'fonte': 'STJ-Dados-Abertos',
                    'fonte_url': 'https://stj.jus.br/test',
                    'metadata': '{}'
                })

            db.inserir_batch(registros)

            stats = db.obter_estatisticas()

            assert stats['por_orgao']['Terceira Turma'] == 5
            assert stats['por_orgao']['Segunda Turma'] == 5


class TestExport:
    """Testes de exportação."""

    def test_exportar_csv(self, temp_db, sample_record):
        """Testa exportação para CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "export.csv"

            with STJDatabase(temp_db) as db:
                db.criar_schema()
                db.inserir_batch([sample_record])

                # Exportar
                db.exportar_csv("SELECT * FROM acordaos", csv_path)

            # Verificar arquivo foi criado
            assert csv_path.exists()
            assert csv_path.stat().st_size > 0

            # Verificar conteúdo (deve ter header + 1 linha)
            with open(csv_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) >= 2  # Header + 1 registro


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
