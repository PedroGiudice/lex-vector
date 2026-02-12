"""
Context Store - Aprende padrões ao processar documentos

Princípios:
1. Similaridade, não identidade - Sugere, não determina
2. Engine-aware updates - Resultado de engine inferior não sobrescreve superior
3. Feedback loop - Aprende com acertos e erros
"""

import hashlib
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import (
    Caso,
    EngineQuality,
    EngineType,
    ObservationResult,
    PatternHint,
    PatternType,
    SignatureVector,
)

logger = logging.getLogger(__name__)

# Qualidade relativa de cada engine
ENGINE_QUALITY = {
    EngineType.MARKER: 1.0,
    EngineType.PDFPLUMBER: 0.9,
    EngineType.TESSERACT: 0.7,
}


class ContextStore:
    """
    Armazena e recupera padrões observados durante processamento.

    Features:
    - Busca por similaridade de vetores (cosine similarity)
    - Engine-aware: engines superiores têm prioridade
    - Auto-deprecação de padrões não confiáveis
    """

    SIMILARITY_THRESHOLD = 0.85  # Mínimo para considerar padrões similares
    DEPRECATION_THRESHOLD = 3  # Número de divergências antes de deprecar

    def __init__(self, db_path: Path):
        """
        Inicializa ContextStore.

        Args:
            db_path: Caminho para banco SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Inicializa schema do banco"""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema_sql = f.read()

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema_sql)
            conn.commit()

        logger.info(f"ContextStore initialized at {self.db_path}")

    def get_or_create_caso(self, numero_cnj: str, sistema: str) -> Caso:
        """
        Recupera ou cria um caso.

        Args:
            numero_cnj: Número CNJ do processo
            sistema: Sistema de origem ('pje', 'eproc', etc)

        Returns:
            Caso criado ou existente
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tenta recuperar existente
            cursor.execute(
                "SELECT id, numero_cnj, sistema, created_at, updated_at FROM caso WHERE numero_cnj = ?",
                (numero_cnj,),
            )
            row = cursor.fetchone()

            if row:
                return Caso(
                    id=row[0],
                    numero_cnj=row[1],
                    sistema=row[2],
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                )

            # Cria novo
            cursor.execute(
                "INSERT INTO caso (numero_cnj, sistema) VALUES (?, ?)", (numero_cnj, sistema)
            )
            conn.commit()

            caso_id = cursor.lastrowid
            logger.info(f"Created new caso: {numero_cnj} (id={caso_id})")

            return Caso(
                id=caso_id,
                numero_cnj=numero_cnj,
                sistema=sistema,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

    def _compute_signature_hash(self, vector: list[float]) -> str:
        """Computa hash MD5 de um vetor"""
        vector_str = json.dumps(vector, sort_keys=True)
        return hashlib.md5(vector_str.encode()).hexdigest()

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        Calcula similaridade cosine entre dois vetores.

        Args:
            vec1: Primeiro vetor
            vec2: Segundo vetor

        Returns:
            Similaridade entre 0.0 e 1.0
        """
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def find_similar_pattern(
        self,
        caso_id: int,
        signature_vector: list[float],
        pattern_type: PatternType | None = None,
    ) -> PatternHint | None:
        """
        Busca padrão similar no histórico do caso.

        Args:
            caso_id: ID do caso
            signature_vector: Vetor de assinatura
            pattern_type: Tipo de padrão (opcional, filtra busca)

        Returns:
            PatternHint se encontrado, None caso contrário
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Query base
            query = """
                SELECT
                    id, pattern_type, signature_vector, suggested_bbox,
                    suggested_engine, avg_confidence, created_by_engine,
                    occurrence_count
                FROM observed_patterns
                WHERE caso_id = ? AND deprecated = FALSE
            """
            params = [caso_id]

            # Filtra por tipo se especificado
            if pattern_type:
                query += " AND pattern_type = ?"
                params.append(pattern_type.value)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Calcula similaridade para cada padrão
            best_match = None
            best_similarity = 0.0

            for row in rows:
                stored_vector = json.loads(row[2])
                similarity = self._cosine_similarity(signature_vector, stored_vector)

                if similarity > best_similarity and similarity >= self.SIMILARITY_THRESHOLD:
                    best_similarity = similarity
                    best_match = row

            if not best_match:
                return None

            # Constrói PatternHint
            suggested_bbox = json.loads(best_match[3]) if best_match[3] else None
            suggested_engine = EngineType(best_match[4]) if best_match[4] else None
            avg_conf = best_match[5] or 0.8  # Default se None

            hint = PatternHint(
                pattern_id=best_match[0],
                similarity=best_similarity,
                suggested_bbox=suggested_bbox,
                suggested_engine=suggested_engine,
                confidence=avg_conf,
                created_by_engine=EngineType(best_match[6]),
                pattern_type=PatternType(best_match[1]),
                occurrence_count=best_match[7],
                avg_confidence=best_match[5],
            )

            logger.debug(
                f"Found similar pattern (similarity={best_similarity:.3f}, "
                f"type={hint.pattern_type.value}, engine={hint.created_by_engine.value})"
            )

            return hint

    def should_update_pattern(
        self,
        pattern_id: int,
        result: ObservationResult,
    ) -> bool:
        """
        Decide se deve atualizar padrão com novo resultado.

        Engine-aware: resultado de engine inferior NÃO sobrescreve engine superior.

        Args:
            pattern_id: ID do padrão
            result: Resultado da observação

        Returns:
            True se deve atualizar, False caso contrário
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT created_by_engine, engine_quality_score FROM observed_patterns WHERE id = ?",
                (pattern_id,),
            )
            row = cursor.fetchone()

            if not row:
                return False

            stored_engine = EngineType(row[0])
            stored_quality = row[1]
            result_quality = ENGINE_QUALITY[result.engine_used]

            # Só atualiza se nova engine é superior ou igual
            should_update = result_quality >= stored_quality

            if not should_update:
                logger.debug(
                    f"Skipping update: {result.engine_used.value} (q={result_quality:.2f}) "
                    f"< {stored_engine.value} (q={stored_quality:.2f})"
                )

            return should_update

    def learn_from_page(
        self,
        caso_id: int,
        signature: SignatureVector,
        result: ObservationResult,
        hint: PatternHint | None = None,
    ) -> int:
        """
        Aprende com resultado de processamento de uma página.

        Args:
            caso_id: ID do caso
            signature: Assinatura da página
            result: Resultado do processamento
            hint: Hint usado (se houver)

        Returns:
            ID do padrão (criado ou atualizado)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Verifica se padrão já existe
            cursor.execute(
                "SELECT id FROM observed_patterns WHERE caso_id = ? AND signature_hash = ?",
                (caso_id, signature.hash),
            )
            row = cursor.fetchone()

            if row:
                pattern_id = row[0]
                return self._update_pattern(pattern_id, result, hint, conn)
            else:
                return self._create_pattern(caso_id, signature, result, conn)

    def _create_pattern(
        self,
        caso_id: int,
        signature: SignatureVector,
        result: ObservationResult,
        conn: sqlite3.Connection,
    ) -> int:
        """Cria novo padrão"""
        cursor = conn.cursor()

        suggested_bbox = json.dumps(result.bbox) if result.bbox else None
        quality_score = ENGINE_QUALITY[result.engine_used]

        cursor.execute(
            """
            INSERT INTO observed_patterns (
                caso_id, pattern_type, signature_hash, signature_vector,
                first_seen_page, last_seen_page, created_by_engine,
                engine_quality_score, avg_confidence, suggested_bbox,
                suggested_engine
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                caso_id,
                result.pattern_type.value,
                signature.hash,
                json.dumps(signature.features),
                result.page_num,
                result.page_num,
                result.engine_used.value,
                quality_score,
                result.confidence,
                suggested_bbox,
                result.engine_used.value,
            ),
        )
        conn.commit()

        pattern_id = cursor.lastrowid
        logger.info(
            f"Created pattern {pattern_id}: type={result.pattern_type.value}, "
            f"page={result.page_num}, engine={result.engine_used.value}"
        )
        return pattern_id

    def _update_pattern(
        self,
        pattern_id: int,
        result: ObservationResult,
        hint: PatternHint | None,
        conn: sqlite3.Connection,
    ) -> int:
        """Atualiza padrão existente"""
        if not self.should_update_pattern(pattern_id, result):
            return pattern_id

        cursor = conn.cursor()

        # Se hint foi usado, verifica se houve divergência
        if hint and hint.avg_confidence:
            divergence_magnitude = abs(hint.avg_confidence - result.confidence)

            # Divergência significativa (>0.2) é registrada
            if divergence_magnitude > 0.2:
                self._record_divergence(pattern_id, result, hint.avg_confidence, conn)
                logger.warning(
                    f"Divergence detected in pattern {pattern_id}: "
                    f"expected={hint.avg_confidence:.3f}, actual={result.confidence:.3f}"
                )

        # Atualiza métricas do padrão
        cursor.execute(
            """
            UPDATE observed_patterns
            SET
                last_seen_page = ?,
                occurrence_count = occurrence_count + 1,
                avg_confidence = (avg_confidence * occurrence_count + ?) / (occurrence_count + 1),
                suggested_bbox = COALESCE(?, suggested_bbox),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                result.page_num,
                result.confidence,
                json.dumps(result.bbox) if result.bbox else None,
                pattern_id,
            ),
        )
        conn.commit()

        logger.debug(f"Updated pattern {pattern_id}")
        return pattern_id

    def _record_divergence(
        self,
        pattern_id: int,
        result: ObservationResult,
        expected_confidence: float,
        conn: sqlite3.Connection,
    ) -> None:
        """Registra divergência"""
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO divergences (
                pattern_id, page_num, expected_confidence,
                actual_confidence, engine_used
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                pattern_id,
                result.page_num,
                expected_confidence,
                result.confidence,
                result.engine_used.value,
            ),
        )
        conn.commit()

    def get_engine_stats(self) -> list[EngineQuality]:
        """
        Retorna estatísticas de qualidade por engine.

        Returns:
            Lista de EngineQuality
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM engine_stats")

            stats = []
            for row in cursor.fetchall():
                stats.append(
                    EngineQuality(
                        engine=EngineType(row[0]),
                        total_patterns=row[1],
                        avg_confidence=row[2] or 0.0,
                        total_occurrences=row[3],
                        deprecated_count=row[4],
                    )
                )

            return stats

    def get_pattern_count(self, caso_id: int, deprecated: bool = False) -> int:
        """Retorna contagem de padrões de um caso"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM observed_patterns WHERE caso_id = ? AND deprecated = ?",
                (caso_id, deprecated),
            )
            return cursor.fetchone()[0]

    def get_engine_hint_for_signature(
        self,
        signature_vector: list[float],
        pattern_type: PatternType | None = None,
        caso_id: int | None = None,
        min_occurrences: int = 2,
    ) -> PatternHint | None:
        """
        Busca hint de engine baseado em padrões similares GLOBAIS.

        Diferente de find_similar_pattern que busca apenas no caso específico,
        este método busca em TODOS os casos para sugerir o melhor engine
        baseado no histórico de sucesso.

        Estratégia:
        1. Se caso_id fornecido, primeiro tenta padrão do mesmo caso (preferência)
        2. Se não encontrar, busca padrões similares em todos os casos
        3. Retorna o engine com melhor avg_confidence para assinaturas similares

        Args:
            signature_vector: Vetor de assinatura da página
            pattern_type: Tipo de padrão (opcional, filtra busca)
            caso_id: ID do caso (opcional, prioriza padrões do mesmo caso)
            min_occurrences: Mínimo de ocorrências para considerar confiável

        Returns:
            PatternHint se encontrado, None caso contrário
        """
        # 1. Primeiro, tenta no mesmo caso (se fornecido)
        if caso_id is not None:
            hint = self.find_similar_pattern(
                caso_id=caso_id,
                signature_vector=signature_vector,
                pattern_type=pattern_type,
            )
            if hint and hint.should_use:
                logger.debug(f"Using case-specific hint: engine={hint.suggested_engine}")
                return hint

        # 2. Busca global em todos os casos
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Query padrões não-deprecados com ocorrências suficientes
            query = """
                SELECT
                    id, pattern_type, signature_vector, suggested_bbox,
                    suggested_engine, avg_confidence, created_by_engine,
                    occurrence_count, caso_id
                FROM observed_patterns
                WHERE deprecated = FALSE
                AND occurrence_count >= ?
            """
            params: list = [min_occurrences]

            # Filtra por tipo se especificado
            if pattern_type:
                query += " AND pattern_type = ?"
                params.append(pattern_type.value)

            # Ordena por confiança média (melhores primeiro)
            query += " ORDER BY avg_confidence DESC, occurrence_count DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                logger.debug("No global patterns found for engine hint")
                return None

            # Calcula similaridade e agrupa por engine
            engine_scores: dict[EngineType, list[tuple[float, float, int]]] = {}

            for row in rows:
                stored_vector = json.loads(row[2])
                similarity = self._cosine_similarity(signature_vector, stored_vector)

                if similarity >= self.SIMILARITY_THRESHOLD:
                    engine = EngineType(row[6])  # created_by_engine
                    avg_conf = row[5] or 0.8
                    occurrences = row[7]

                    if engine not in engine_scores:
                        engine_scores[engine] = []
                    engine_scores[engine].append((similarity, avg_conf, occurrences))

            if not engine_scores:
                logger.debug("No similar patterns found globally")
                return None

            # Calcula score ponderado por engine
            # Score = avg(similarity * confidence * log(occurrences))
            best_engine = None
            best_score = 0.0
            best_data = None

            for engine, scores in engine_scores.items():
                total_score = 0.0
                total_weight = 0.0
                for sim, conf, occ in scores:
                    weight = 1.0 + (occ / 10.0)  # Peso baseado em ocorrências
                    total_score += sim * conf * weight
                    total_weight += weight

                avg_score = total_score / total_weight if total_weight > 0 else 0
                if avg_score > best_score:
                    best_score = avg_score
                    best_engine = engine
                    # Pega dados do melhor match individual
                    best_match = max(scores, key=lambda x: x[0] * x[1])
                    best_data = best_match

            if best_engine is None or best_data is None:
                return None

            similarity, confidence, _ = best_data
            hint = PatternHint(
                pattern_id=0,  # Global hint, não tem pattern_id específico
                similarity=similarity,
                suggested_bbox=None,  # Global hint não sugere bbox
                suggested_engine=best_engine,
                confidence=confidence,
                created_by_engine=best_engine,
                pattern_type=pattern_type or PatternType.UNKNOWN,
                occurrence_count=sum(occ for _, _, occ in engine_scores[best_engine]),
                avg_confidence=confidence,
            )

            logger.info(
                f"Global engine hint: {best_engine.value} "
                f"(score={best_score:.3f}, similarity={similarity:.3f})"
            )

            return hint

    def get_best_engine_for_pattern_type(
        self,
        pattern_type: PatternType,
    ) -> EngineType | None:
        """
        Retorna o melhor engine para um tipo de padrão baseado em estatísticas globais.

        Usa a view engine_performance_by_type para determinar qual engine
        tem melhor desempenho histórico para o tipo de padrão especificado.

        Args:
            pattern_type: Tipo de padrão (HEADER, TABLE, TEXT_BLOCK, etc)

        Returns:
            EngineType com melhor performance, ou None se sem dados
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT engine, avg_confidence, total_occurrences
                FROM engine_performance_by_type
                WHERE pattern_type = ?
                ORDER BY avg_confidence DESC, total_occurrences DESC
                LIMIT 1
                """,
                (pattern_type.value,),
            )
            row = cursor.fetchone()

            if row:
                engine = EngineType(row[0])
                logger.debug(
                    f"Best engine for {pattern_type.value}: {engine.value} "
                    f"(avg_confidence={row[1]:.3f}, occurrences={row[2]})"
                )
                return engine

            return None
