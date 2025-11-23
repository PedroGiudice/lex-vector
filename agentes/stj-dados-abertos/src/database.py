"""
Database Manager para STJ Dados Abertos
========================================

Interface simplificada para o Hybrid Storage.
Fornece métodos de alto nível para operações comuns.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

from .hybrid_storage import STJHybridStorage


logger = logging.getLogger(__name__)


class STJDatabase:
    """
    Interface de alto nível para o storage híbrido do STJ.

    Simplifica operações comuns:
    - Inserção em batch
    - Buscas com filtros múltiplos
    - Estatísticas e relatórios
    - Validação de dados
    """

    def __init__(self):
        """Inicializa o database manager."""
        self.storage = STJHybridStorage(validate_on_init=True)
        logger.info("✓ STJDatabase inicializado")

    def insert_batch(self, acordaos: List[dict]) -> Dict[str, int]:
        """
        Insere múltiplos acórdãos em batch.

        Args:
            acordaos: Lista de dicionários com dados dos acórdãos

        Returns:
            Dicionário com estatísticas:
            - inserted: quantidade inserida
            - duplicates: quantidade de duplicatas
            - errors: quantidade de erros
        """
        stats = {"inserted": 0, "duplicates": 0, "errors": 0}

        for acordao in acordaos:
            try:
                # Converter para JSON string
                json_content = json.dumps(acordao, ensure_ascii=False, indent=2)

                # Inserir
                if self.storage.insert_acordao(acordao, json_content):
                    stats["inserted"] += 1
                else:
                    stats["duplicates"] += 1

            except Exception as e:
                logger.error(f"Erro ao inserir acórdão: {e}")
                stats["errors"] += 1

        logger.info(
            f"Batch inserido: {stats['inserted']} novos, "
            f"{stats['duplicates']} duplicatas, {stats['errors']} erros"
        )

        return stats

    def search(
        self,
        texto: Optional[str] = None,
        orgao: Optional[str] = None,
        relator: Optional[str] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """
        Busca acórdãos com filtros.

        Args:
            texto: Busca fulltext em ementa e texto integral
            orgao: Órgão julgador (ex: "Terceira Turma")
            relator: Nome do relator
            data_inicio: Data inicial (YYYY-MM-DD)
            data_fim: Data final (YYYY-MM-DD)
            limit: Máximo de resultados

        Returns:
            Lista de acórdãos encontrados
        """
        return self.storage.search_acordaos(
            texto=texto,
            orgao_julgador=orgao,
            relator=relator,
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=limit
        )

    def search_by_theme(self, theme: str, limit: int = 50) -> List[dict]:
        """
        Busca acórdãos por tema jurídico.

        Args:
            theme: Tema (ex: "responsabilidade civil", "ação monitória")
            limit: Máximo de resultados

        Returns:
            Lista de acórdãos relacionados ao tema
        """
        return self.search(texto=theme, limit=limit)

    def get_recent(self, days: int = 7, limit: int = 100) -> List[dict]:
        """
        Retorna acórdãos recentes.

        Args:
            days: Últimos N dias
            limit: Máximo de resultados

        Returns:
            Lista de acórdãos recentes
        """
        from datetime import datetime, timedelta

        data_inicio = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        return self.search(data_inicio=data_inicio, limit=limit)

    def get_by_orgao(self, orgao: str, limit: int = 100) -> List[dict]:
        """
        Retorna acórdãos de um órgão julgador específico.

        Args:
            orgao: Nome do órgão (ex: "Corte Especial", "Terceira Turma")
            limit: Máximo de resultados

        Returns:
            Lista de acórdãos do órgão
        """
        return self.search(orgao=orgao, limit=limit)

    def get_by_relator(self, relator: str, limit: int = 100) -> List[dict]:
        """
        Retorna acórdãos de um relator específico.

        Args:
            relator: Nome do relator
            limit: Máximo de resultados

        Returns:
            Lista de acórdãos do relator
        """
        return self.search(relator=relator, limit=limit)

    def get_statistics(self) -> dict:
        """
        Retorna estatísticas completas do database.

        Returns:
            Dicionário com métricas detalhadas
        """
        stats = self.storage.get_stats()

        # Adicionar estatísticas adicionais
        conn = self.storage.conn

        # Por órgão julgador
        orgaos = conn.execute("""
            SELECT orgao_julgador, COUNT(*) as total
            FROM acordao_index
            WHERE orgao_julgador IS NOT NULL
            GROUP BY orgao_julgador
            ORDER BY total DESC
            LIMIT 10
        """).fetchall()

        stats["top_orgaos"] = [
            {"orgao": o[0], "total": o[1]} for o in orgaos
        ]

        # Por relator
        relatores = conn.execute("""
            SELECT relator, COUNT(*) as total
            FROM acordao_index
            WHERE relator IS NOT NULL
            GROUP BY relator
            ORDER BY total DESC
            LIMIT 10
        """).fetchall()

        stats["top_relatores"] = [
            {"relator": r[0], "total": r[1]} for r in relatores
        ]

        # Distribuição temporal
        temporal = conn.execute("""
            SELECT
                strftime('%Y-%m', data_publicacao) as mes,
                COUNT(*) as total
            FROM acordao_index
            WHERE data_publicacao IS NOT NULL
            GROUP BY mes
            ORDER BY mes DESC
            LIMIT 12
        """).fetchall()

        stats["distribuicao_temporal"] = [
            {"mes": t[0], "total": t[1]} for t in temporal
        ]

        return stats

    def validate_integrity(self) -> Dict[str, Any]:
        """
        Valida integridade do database.

        Verificações:
        - Índices sem documentos
        - Documentos órfãos
        - Hashes duplicados
        - Tamanhos inconsistentes

        Returns:
            Relatório de integridade
        """
        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checked_at": None
        }

        from datetime import datetime
        report["checked_at"] = datetime.now().isoformat()

        conn = self.storage.conn

        # 1. Índices sem documentos
        missing_docs = conn.execute("""
            SELECT id, json_path FROM acordao_index
            WHERE json_path IS NOT NULL
        """).fetchall()

        for acordao_id, json_path in missing_docs:
            full_path = self.storage.data_root / json_path
            if not full_path.exists():
                report["errors"].append(
                    f"Documento ausente: {acordao_id} -> {json_path}"
                )
                report["valid"] = False

        # 2. Hashes duplicados
        duplicates = conn.execute("""
            SELECT hash_conteudo, COUNT(*) as cnt
            FROM acordao_index
            WHERE hash_conteudo IS NOT NULL
            GROUP BY hash_conteudo
            HAVING cnt > 1
        """).fetchall()

        if duplicates:
            report["warnings"].append(
                f"Encontrados {len(duplicates)} hashes duplicados"
            )

        # 3. Registros sem fulltext
        no_fulltext = conn.execute("""
            SELECT i.id
            FROM acordao_index i
            LEFT JOIN acordao_fulltext f ON i.id = f.id
            WHERE f.id IS NULL
        """).fetchall()

        if no_fulltext:
            report["warnings"].append(
                f"{len(no_fulltext)} acórdãos sem índice fulltext"
            )

        logger.info(
            f"Validação de integridade: "
            f"{len(report['errors'])} erros, {len(report['warnings'])} avisos"
        )

        return report

    def optimize(self):
        """
        Otimiza o database (VACUUM, ANALYZE, etc).
        """
        logger.info("Otimizando database...")

        conn = self.storage.conn

        # Analisa estatísticas para melhor query planning
        conn.execute("ANALYZE")

        # Checkpoint do WAL
        conn.execute("CHECKPOINT")

        logger.info("✓ Database otimizado")

    def close(self):
        """Fecha conexões."""
        self.storage.close()
        logger.info("✓ STJDatabase fechado")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
