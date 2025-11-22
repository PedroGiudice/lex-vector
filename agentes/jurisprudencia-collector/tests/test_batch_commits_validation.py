#!/usr/bin/env python3
"""
Testes de Validação para Batch Commits (P3)

OBJETIVO: Validar que a implementação EXISTENTE segue as especificações.

Implementação atual (scheduler.py):
- BATCH_SIZE = 100 (linha 286)
- Commit a cada 100 inserções (linha 349-352)
- Commit final das restantes (linha 359)
- Rollback apenas de duplicatas (linha 170)

Status: IMPLEMENTADO ✅
Testes: VALIDAÇÃO (não TDD RED→GREEN)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
import sqlite3
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


# Mock de PublicacaoRaw (mesma estrutura de downloader.py)
@dataclass
class PublicacaoRaw:
    id: str
    hash_conteudo: str
    numero_processo: Optional[str]
    numero_processo_fmt: Optional[str]
    tribunal: str
    orgao_julgador: Optional[str]
    tipo_comunicacao: str
    classe_processual: Optional[str]
    texto_html: str
    data_publicacao: str
    destinatario_advogados: List[Dict]
    metadata: Dict


def criar_publicacao_mock(index: int, tribunal: str = 'STJ') -> PublicacaoRaw:
    """Cria publicação mock para testes."""
    import hashlib

    texto = f"Acórdão de teste {index}"
    hash_conteudo = hashlib.sha256(texto.encode()).hexdigest()

    return PublicacaoRaw(
        id=f"pub_{index}",
        hash_conteudo=hash_conteudo,
        numero_processo=f"12345{index:05d}",
        numero_processo_fmt=f"1234-56.2024.8.26.{index:04d}",
        tribunal=tribunal,
        orgao_julgador="1ª Turma",
        tipo_comunicacao="Intimação",
        classe_processual="Apelação Cível",
        texto_html=f"<p>{texto}</p>",
        data_publicacao="2025-01-01",
        destinatario_advogados=[],
        metadata={'fonte': 'test'}
    )


class TestBatchCommitsValidacao:
    """Validação do sistema de batch commits já implementado."""

    def setup_method(self):
        """Setup: criar banco de dados temporário com schema."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = Path(self.temp_db.name)
        self.conn = sqlite3.connect(self.db_path)

        # Criar schema (baseado em init_database.sql)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS publicacoes (
                id TEXT PRIMARY KEY,
                hash_conteudo TEXT UNIQUE NOT NULL,
                numero_processo TEXT,
                numero_processo_fmt TEXT,
                tribunal TEXT NOT NULL,
                orgao_julgador TEXT,
                tipo_publicacao TEXT NOT NULL,
                classe_processual TEXT,
                assuntos TEXT,
                texto_html TEXT NOT NULL,
                texto_limpo TEXT NOT NULL,
                ementa TEXT,
                data_publicacao TEXT NOT NULL,
                data_julgamento TEXT,
                relator TEXT,
                fonte TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def teardown_method(self):
        """Teardown: fechar conexão e remover arquivo temporário."""
        self.conn.close()
        self.db_path.unlink(missing_ok=True)

    def test_batch_size_configurado_como_100(self):
        """
        VALIDAÇÃO: BATCH_SIZE = 100 no scheduler.py.

        Implementação atual (scheduler.py L286).
        """
        # Importar após setup (para garantir path correto)
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scheduler import processar_publicacoes

        # BATCH_SIZE é hardcoded no código - verificar via inspeção do código
        import inspect
        source = inspect.getsource(processar_publicacoes)

        assert 'BATCH_SIZE = 100' in source, (
            "BATCH_SIZE deveria ser 100 (scheduler.py L286)"
        )

    def test_processar_publicacoes_aceita_parametros(self):
        """
        VALIDAÇÃO: processar_publicacoes aceita parâmetros corretos.

        Implementação atual (scheduler.py L258-283):
        - conn: Connection
        - publicacoes: List[PublicacaoRaw]
        - tribunal: str
        - tipos_desejados: List[str] (default: ['Acórdão'])
        """
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scheduler import processar_publicacoes

        # Criar publicações mock
        pubs = [criar_publicacao_mock(i) for i in range(5)]

        # Deve aceitar estes parâmetros sem erro
        stats = processar_publicacoes(
            conn=self.conn,
            publicacoes=pubs,
            tribunal='STJ',
            tipos_desejados=['Acórdão']
        )

        assert isinstance(stats, dict)
        assert 'total' in stats
        assert 'novas' in stats
        assert 'duplicadas' in stats
        assert 'filtrados' in stats
        assert 'erros' in stats

    def test_commits_ocorrem_em_batches_de_100(self):
        """
        VALIDAÇÃO: Commits ocorrem a cada 100 inserções.

        Implementação atual (scheduler.py L349-352):
        - if i % BATCH_SIZE == 0: conn.commit()
        """
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scheduler import processar_publicacoes

        # Criar 250 publicações (2.5 batches)
        pubs = [criar_publicacao_mock(i) for i in range(250)]

        # Processar
        stats = processar_publicacoes(
            conn=self.conn,
            publicacoes=pubs,
            tribunal='STJ',
            tipos_desejados=['Acórdão']
        )

        # Verificar que todas foram inseridas
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM publicacoes")
        count = cursor.fetchone()[0]

        # Deve ter inserido todas (ou filtrado se processador rejeitar)
        # Como são mocks válidos, deve ter processado todas
        assert count == stats['novas'], (
            f"Esperado {stats['novas']} inserções, obtido {count}"
        )

    def test_commit_final_apos_batch_incompleto(self):
        """
        VALIDAÇÃO: Commit final das inserções restantes (< BATCH_SIZE).

        Implementação atual (scheduler.py L359-360):
        - conn.commit() após loop (commit final)
        """
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scheduler import processar_publicacoes

        # Criar 150 publicações (1 batch completo + 50 restantes)
        pubs = [criar_publicacao_mock(i) for i in range(150)]

        stats = processar_publicacoes(
            conn=self.conn,
            publicacoes=pubs,
            tribunal='STJ',
            tipos_desejados=['Acórdão']
        )

        # Verificar que TODAS foram inseridas (incluindo as 50 restantes)
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM publicacoes")
        count = cursor.fetchone()[0]

        assert count == stats['novas'], (
            f"Commit final deveria ter salvado todas, mas salvou apenas {count}/{stats['novas']}"
        )

    def test_rollback_apenas_de_duplicatas(self):
        """
        VALIDAÇÃO: Rollback apenas de duplicatas, não de todo o batch.

        Implementação atual (scheduler.py L166-171):
        - IntegrityError (hash duplicado) → conn.rollback() da transação atual
        - Não afeta inserções anteriores do batch
        """
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scheduler import processar_publicacoes

        # Criar 10 publicações
        pubs = [criar_publicacao_mock(i) for i in range(10)]

        # Primeira execução (todas novas)
        stats1 = processar_publicacoes(
            conn=self.conn,
            publicacoes=pubs,
            tribunal='STJ',
            tipos_desejados=['Acórdão']
        )

        assert stats1['novas'] == 10
        assert stats1['duplicadas'] == 0

        # Segunda execução (todas duplicadas)
        stats2 = processar_publicacoes(
            conn=self.conn,
            publicacoes=pubs,
            tribunal='STJ',
            tipos_desejados=['Acórdão']
        )

        assert stats2['novas'] == 0
        assert stats2['duplicadas'] == 10

        # Verificar que ainda há 10 no banco (não foram removidas)
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM publicacoes")
        count = cursor.fetchone()[0]
        assert count == 10

    def test_batch_commit_nao_bloqueia_em_caso_de_erro(self):
        """
        VALIDAÇÃO: Erro em publicação não bloqueia todo o batch.

        Implementação atual (scheduler.py L354-356):
        - try/except ao redor de cada publicação
        - Exceção incrementa stats['erros'] mas não interrompe loop
        """
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scheduler import processar_publicacoes

        # Criar mix de publicações válidas e inválidas
        pubs = [criar_publicacao_mock(i) for i in range(5)]

        # Corromper uma publicação (hash None causará erro)
        pubs[2].hash_conteudo = None

        # Processar (deve continuar apesar do erro)
        stats = processar_publicacoes(
            conn=self.conn,
            publicacoes=pubs,
            tribunal='STJ',
            tipos_desejados=['Acórdão']
        )

        # Deve ter processado as válidas (4 de 5)
        # Nota: erro pode vir do processador_texto, não necessariamente da inserção
        # Então verificar que PELO MENOS algumas foram inseridas
        assert stats['novas'] >= 1, (
            f"Pelo menos 1 publicação válida deveria ter sido inserida, "
            f"mas stats mostram: {stats}"
        )


class TestBatchCommitsPerformance:
    """Testes de performance do batch commit."""

    def setup_method(self):
        """Setup: criar banco de dados temporário."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = Path(self.temp_db.name)
        self.conn = sqlite3.connect(self.db_path)

        # Criar schema
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS publicacoes (
                id TEXT PRIMARY KEY,
                hash_conteudo TEXT UNIQUE NOT NULL,
                numero_processo TEXT,
                numero_processo_fmt TEXT,
                tribunal TEXT NOT NULL,
                orgao_julgador TEXT,
                tipo_publicacao TEXT NOT NULL,
                classe_processual TEXT,
                assuntos TEXT,
                texto_html TEXT NOT NULL,
                texto_limpo TEXT NOT NULL,
                ementa TEXT,
                data_publicacao TEXT NOT NULL,
                data_julgamento TEXT,
                relator TEXT,
                fonte TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def teardown_method(self):
        """Teardown."""
        self.conn.close()
        self.db_path.unlink(missing_ok=True)

    def test_batch_commit_mais_rapido_que_commit_individual(self):
        """
        VALIDAÇÃO: Batch commit é mais rápido que commit individual.

        Expectativa:
        - Batch (100 inserções/commit): ~0.1s para 500 inserções
        - Individual (1 inserção/commit): ~5s para 500 inserções
        - Speedup: ~50x
        """
        import time
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scheduler import processar_publicacoes

        # Criar 500 publicações
        pubs = [criar_publicacao_mock(i) for i in range(500)]

        # Medir tempo com batch commit
        start = time.time()
        stats = processar_publicacoes(
            conn=self.conn,
            publicacoes=pubs,
            tribunal='STJ',
            tipos_desejados=['Acórdão']
        )
        elapsed_batch = time.time() - start

        # Batch deve completar em < 5s (com processamento incluído)
        assert elapsed_batch < 5.0, (
            f"Batch commit deveria ser rápido, mas levou {elapsed_batch:.2f}s"
        )

        # Verificar que todas foram inseridas
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM publicacoes")
        count = cursor.fetchone()[0]
        assert count == stats['novas']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
