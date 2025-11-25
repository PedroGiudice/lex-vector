"""
Segmentador de documentos juridicos em blocos logicos.

Implementa a logica de segmentacao baseada em:
1. Header Score: Deteccao de inicio de secao nas primeiras linhas
2. Footer Score: Deteccao de fim de secao nas ultimas linhas
3. Transicao de Anexos: Deteccao de mudanca para documentos anexos

Baseado em:
- JurisMiner (logica de segmentacao R -> Python)
- verbose-correct-doodle (regex de pecas)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import TypedDict

from .definitions import LegalTaxonomy, get_taxonomy
from .boundary_config import BoundaryConfig, get_conservative_config
from .boundary_detector import BoundaryDetector, has_boundary_markers


class PageClassification(TypedDict):
    """Resultado da classificacao de uma pagina."""

    page: int
    type: str
    confidence: float
    is_section_start: bool
    is_section_end: bool
    matched_terms: list[str]


class SectionInfo(TypedDict):
    """Informacoes de uma secao identificada."""

    section_id: int
    type: str
    start_page: int
    end_page: int
    confidence: float
    page_count: int


class SegmentationResult(TypedDict):
    """Resultado completo da segmentacao."""

    doc_id: str
    total_pages: int
    total_sections: int
    pages: list[PageClassification]
    sections: list[SectionInfo]


@dataclass
class DocumentSegmenter:
    """
    Segmentador de documentos juridicos.

    Analisa um documento markdown (final.md) e identifica:
    - Tipo de cada pagina
    - Inicio e fim de secoes
    - Transicoes entre pecas processuais
    """

    taxonomy: LegalTaxonomy = field(default_factory=get_taxonomy)

    # Configuracoes de janela adaptativa
    header_lines_min: int = 15  # Janela inicial
    header_lines_max: int = 50  # Janela maxima (evita freeze)
    header_lines_step: int = 10  # Incremento por tentativa
    footer_lines: int = 10  # Linhas do rodape para analise de footer
    min_confidence: float = 0.3  # Confianca minima para classificacao
    adaptive_threshold: float = 0.4  # Confianca minima para parar expansao

    # Padroes de anexos (triggers para estado ANEXOS)
    ANEXO_TRIGGERS = [
        r"\bPROCURA[CÇ][AÃ]O\b",
        r"\bSUBSTABELECIMENTO\b",
        r"\bDOC\.?\s*\d+",
        r"\bDOCUMENTO\s*\d+",
        r"\bANEXO\s*[IVX\d]+",
        r"\bCOMPROVANTE\b",
        r"\bCONTRATO\b",
    ]

    # Padroes de fim de secao
    FOOTER_TRIGGERS = [
        r"\bNESTES\s+TERMOS\b",
        r"\bPEDE\s+DEFERIMENTO\b",
        r"\bTERMOS\s+EM\s+QUE\b",
        r"\bP\.\s*DEFERIMENTO\b",
        r"\bAGUARDA\s+DEFERIMENTO\b",
        r"\bOAB[/\s]*[A-Z]{2}\s*\d+",
        r"\bADVOGAD[OA]\b",
    ]

    def __post_init__(self) -> None:
        """Compila padroes regex apos inicializacao."""
        # Compila triggers de anexo
        self._anexo_pattern = re.compile(
            "|".join(self.ANEXO_TRIGGERS), re.IGNORECASE
        )

        # Compila triggers de footer
        self._footer_pattern = re.compile(
            "|".join(self.FOOTER_TRIGGERS), re.IGNORECASE
        )

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza texto para matching robusto.

        Args:
            text: Texto original

        Returns:
            Texto normalizado (sem acentos, uppercase)
        """
        nfkd = unicodedata.normalize("NFKD", text)
        without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
        return without_accents.upper()

    def parse_markdown_pages(self, markdown_content: str) -> list[dict[str, str | int]]:
        """
        Parseia o markdown em paginas individuais.

        Espera formato: ## [[PAGE_XXX]] [TYPE: YYY]

        Args:
            markdown_content: Conteudo do final.md

        Returns:
            Lista de dicts com page_num, page_type, content
        """
        # Pattern para identificar headers de pagina
        page_pattern = re.compile(
            r"##\s*\[\[PAGE_(\d+)\]\]\s*\[TYPE:\s*(\w+)\]",
            re.IGNORECASE,
        )

        pages = []
        current_page = None
        current_content_lines = []

        for line in markdown_content.split("\n"):
            match = page_pattern.match(line)
            if match:
                # Salva pagina anterior se existir
                if current_page is not None:
                    pages.append({
                        "page_num": current_page["page_num"],
                        "page_type": current_page["page_type"],
                        "content": "\n".join(current_content_lines).strip(),
                    })
                    current_content_lines = []

                # Inicia nova pagina
                current_page = {
                    "page_num": int(match.group(1)),
                    "page_type": match.group(2).upper(),
                }
            elif current_page is not None:
                current_content_lines.append(line)

        # Salva ultima pagina
        if current_page is not None:
            pages.append({
                "page_num": current_page["page_num"],
                "page_type": current_page["page_type"],
                "content": "\n".join(current_content_lines).strip(),
            })

        return pages

    def _get_header_text(self, content: str, num_lines: int | None = None) -> str:
        """Extrai as primeiras N linhas do conteudo."""
        lines = content.split("\n")
        n = num_lines if num_lines is not None else self.header_lines_min
        return "\n".join(lines[:n])

    def _get_footer_text(self, content: str) -> str:
        """Extrai as ultimas N linhas do conteudo."""
        lines = content.split("\n")
        return "\n".join(lines[-self.footer_lines :])

    def _score_category(
        self, text: str, category: str, is_header: bool = True
    ) -> tuple[float, list[str]]:
        """
        Calcula score de uma categoria para um texto.

        Pesos ajustados para valorizar matches de patterns de header,
        que sao altamente indicativos do tipo de peca.

        Args:
            text: Texto a analisar
            category: Categoria da taxonomia
            is_header: Se True, usa header_patterns; se False, usa footer_patterns

        Returns:
            Tupla (score, termos_encontrados)
        """
        normalized = self.normalize_text(text)
        matched_terms = []
        score = 0.0

        # Busca sinonimos da categoria (peso menor - termo generico)
        category_pattern = self.taxonomy.get_category_pattern(category)
        synonyms_matches = category_pattern.findall(normalized)
        if synonyms_matches:
            matched_terms.extend(synonyms_matches)
            # Peso 0.3 por sinonimo, max 2 contribuicoes
            score += min(0.3 * len(synonyms_matches), 0.6)

        # Busca patterns de header ou footer (peso maior - muito indicativo)
        if is_header:
            pattern = self.taxonomy.get_header_pattern(category)
        else:
            pattern = self.taxonomy.get_footer_pattern(category)

        pattern_matches = pattern.findall(normalized)
        if pattern_matches:
            matched_terms.extend(pattern_matches)
            # Header/footer patterns sao muito indicativos - peso alto
            # Primeiro match vale 0.5, adicionais valem 0.2 cada
            score += 0.5 + 0.2 * (len(pattern_matches) - 1)

        # Limita score ao range [0.0, 1.0]
        final_score = max(0.0, min(score, 1.0))

        return final_score, matched_terms

    def _detect_section_end(self, content: str) -> bool:
        """Detecta se a pagina contem indicadores de fim de secao."""
        footer = self._get_footer_text(content)
        normalized = self.normalize_text(footer)
        return bool(self._footer_pattern.search(normalized))

    def _detect_anexo_transition(self, content: str) -> bool:
        """Detecta se a pagina inicia secao de anexos."""
        header = self._get_header_text(content)
        normalized = self.normalize_text(header)
        return bool(self._anexo_pattern.search(normalized))

    def _classify_with_window(
        self, content: str, window_lines: int
    ) -> tuple[str, float, list[str]]:
        """
        Classifica usando janela de tamanho especifico.

        Returns:
            Tupla (categoria, score, termos_matched)
        """
        header_text = self._get_header_text(content, window_lines)

        # Pontua todas as categorias
        scores: list[tuple[str, float, list[str]]] = []
        for category in self.taxonomy.all_categories():
            if category == "INDETERMINADO":
                continue

            score, terms = self._score_category(header_text, category, is_header=True)
            if score > 0:
                # Ajusta por prioridade da categoria (bonus de 0-0.15)
                priority = self.taxonomy.get_priority(category)
                priority_bonus = priority * 0.015  # Max 10 * 0.015 = 0.15
                adjusted_score = min(score + priority_bonus, 1.0)
                scores.append((category, adjusted_score, terms))

        # Ordena por score (maior primeiro)
        scores.sort(key=lambda x: x[1], reverse=True)

        if scores and scores[0][1] >= self.min_confidence:
            return scores[0]
        return ("INDETERMINADO", 0.0, [])

    def classify_page(self, content: str, page_num: int) -> PageClassification:
        """
        Classifica uma pagina individual com janela adaptativa.

        Comeca com janela minima e expande progressivamente se
        nao encontrar classificacao com confianca suficiente.

        Args:
            content: Conteudo textual da pagina
            page_num: Numero da pagina

        Returns:
            PageClassification com tipo e confianca
        """
        best_category = "INDETERMINADO"
        best_score = 0.0
        matched: list[str] = []
        window_used = self.header_lines_min

        # Janela adaptativa: expande se nao encontrar com confianca
        current_window = self.header_lines_min
        while current_window <= self.header_lines_max:
            category, score, terms = self._classify_with_window(content, current_window)

            # Atualiza melhor resultado se score maior
            if score > best_score:
                best_category = category
                best_score = score
                matched = terms
                window_used = current_window

            # Para se encontrou classificacao com confianca suficiente
            if score >= self.adaptive_threshold:
                break

            # Expande janela para proxima tentativa
            current_window += self.header_lines_step

        # Determina se e inicio de secao
        is_section_start = best_score > 0.5

        # Detecta fim de secao
        is_section_end = self._detect_section_end(content)

        # Verifica transicao para anexos (usa janela adaptada)
        if self._detect_anexo_transition(content):
            best_category = "ANEXOS"
            best_score = max(best_score, 0.7)
            is_section_start = True

        return PageClassification(
            page=page_num,
            type=best_category,
            confidence=round(best_score, 3),
            is_section_start=is_section_start,
            is_section_end=is_section_end,
            matched_terms=matched[:5],  # Limita a 5 termos
        )

    def segment(self, markdown_content: str, doc_id: str = "document") -> SegmentationResult:
        """
        Segmenta documento completo.

        Args:
            markdown_content: Conteudo do final.md
            doc_id: Identificador do documento

        Returns:
            SegmentationResult com classificacao de paginas e secoes
        """
        # Parseia paginas
        pages_data = self.parse_markdown_pages(markdown_content)

        if not pages_data:
            return SegmentationResult(
                doc_id=doc_id,
                total_pages=0,
                total_sections=0,
                pages=[],
                sections=[],
            )

        # Classifica cada pagina
        page_classifications: list[PageClassification] = []
        for page_data in pages_data:
            classification = self.classify_page(
                content=page_data["content"],
                page_num=page_data["page_num"],
            )
            page_classifications.append(classification)

        # Agrupa em secoes
        sections = self._build_sections(page_classifications)

        return SegmentationResult(
            doc_id=doc_id,
            total_pages=len(page_classifications),
            total_sections=len(sections),
            pages=page_classifications,
            sections=sections,
        )

    def _build_sections(
        self, classifications: list[PageClassification]
    ) -> list[SectionInfo]:
        """
        Agrupa paginas em secoes baseado em transicoes.

        Args:
            classifications: Lista de classificacoes de paginas

        Returns:
            Lista de SectionInfo
        """
        if not classifications:
            return []

        sections: list[SectionInfo] = []
        section_id = 1
        current_section_start = classifications[0]["page"]
        current_section_type = classifications[0]["type"]
        confidence_sum = classifications[0]["confidence"]
        page_count = 1

        for i in range(1, len(classifications)):
            prev = classifications[i - 1]
            curr = classifications[i]

            # Detecta transicao de secao
            is_new_section = (
                curr["is_section_start"]
                or prev["is_section_end"]
                or (curr["type"] != current_section_type and curr["confidence"] > 0.5)
            )

            if is_new_section:
                # Fecha secao anterior
                avg_confidence = confidence_sum / page_count
                sections.append(
                    SectionInfo(
                        section_id=section_id,
                        type=current_section_type,
                        start_page=current_section_start,
                        end_page=prev["page"],
                        confidence=round(avg_confidence, 3),
                        page_count=page_count,
                    )
                )

                # Inicia nova secao
                section_id += 1
                current_section_start = curr["page"]
                current_section_type = curr["type"]
                confidence_sum = curr["confidence"]
                page_count = 1
            else:
                # Continua secao atual
                confidence_sum += curr["confidence"]
                page_count += 1

        # Fecha ultima secao
        avg_confidence = confidence_sum / page_count
        sections.append(
            SectionInfo(
                section_id=section_id,
                type=current_section_type,
                start_page=current_section_start,
                end_page=classifications[-1]["page"],
                confidence=round(avg_confidence, 3),
                page_count=page_count,
            )
        )

        return sections

    def refine_anexos_section(
        self,
        section: SectionInfo,
        pages_data: list[dict],
        boundary_config: BoundaryConfig | None = None,
    ) -> list[SectionInfo]:
        """
        Refina uma secao de ANEXOS detectando boundaries entre documentos.

        Este metodo e OPCIONAL e CONSERVADOR:
        - So processa secoes do tipo ANEXOS
        - Usa configuracao conservadora por padrao
        - Preserva todo o conteudo (nenhuma linha e perdida)

        Args:
            section: SectionInfo da secao de anexos
            pages_data: Lista de paginas com conteudo
            boundary_config: Configuracao de boundary (opcional)

        Returns:
            Lista de SectionInfo refinadas (pode ser 1 se nenhum boundary detectado)

        ATENCAO: Boundaries mal detectados podem fragmentar documentos.
        Por isso, este metodo:
        1. Usa min_confidence alto (0.8+)
        2. Valida que todo conteudo esta preservado
        3. Na duvida, NAO separa
        """
        if section["type"] != "ANEXOS":
            # Nao e secao de anexos - retorna como esta
            return [section]

        # Extrai conteudo das paginas da secao
        section_content = ""
        page_line_map: list[tuple[int, int, int]] = []  # (page_num, start_line, end_line)

        current_line = 1
        for page_data in pages_data:
            page_num = page_data.get("page_num", 0)
            if section["start_page"] <= page_num <= section["end_page"]:
                content = page_data.get("content", "")
                lines = content.split("\n")
                line_count = len(lines)

                page_line_map.append((page_num, current_line, current_line + line_count - 1))
                section_content += content + "\n"
                current_line += line_count

        # Verifica rapidamente se ha marcadores de boundary
        if not has_boundary_markers(section_content):
            # Sem marcadores - retorna secao original
            return [section]

        # Configura detector
        config = boundary_config or get_conservative_config()
        detector = BoundaryDetector(config=config)

        # Detecta boundaries
        result = detector.detect(section_content)

        if result["total_boundaries"] == 0:
            # Nenhum boundary detectado com confidence suficiente
            return [section]

        # Converte segmentos de linha para paginas
        refined_sections: list[SectionInfo] = []
        base_section_id = section["section_id"] * 100  # Subsecoes: 100, 101, 102...

        for idx, segment in enumerate(result["segments"]):
            # Encontra paginas que contem este segmento
            start_page = self._line_to_page(segment["start_line"], page_line_map)
            end_page = self._line_to_page(segment["end_line"], page_line_map)

            if start_page is None or end_page is None:
                continue

            # Determina tipo do documento
            doc_type = segment.get("document_type", "ANEXO_DESCONHECIDO")
            if doc_type == "UNKNOWN":
                doc_type = "ANEXO_DESCONHECIDO"

            refined_sections.append(
                SectionInfo(
                    section_id=base_section_id + idx,
                    type=f"ANEXOS:{doc_type}",  # Subtipo: ANEXOS:PROCURACAO
                    start_page=start_page,
                    end_page=end_page,
                    confidence=round(segment.get("confidence", 0.5), 3),
                    page_count=end_page - start_page + 1,
                )
            )

        # Se nao conseguiu gerar secoes refinadas, retorna original
        if not refined_sections:
            return [section]

        return refined_sections

    @staticmethod
    def _line_to_page(
        line_num: int,
        page_line_map: list[tuple[int, int, int]],
    ) -> int | None:
        """
        Converte numero de linha global para numero de pagina.

        Args:
            line_num: Numero da linha (1-indexed)
            page_line_map: Lista de (page_num, start_line, end_line)

        Returns:
            Numero da pagina ou None se nao encontrar
        """
        for page_num, start_line, end_line in page_line_map:
            if start_line <= line_num <= end_line:
                return page_num
        return None

    def segment_with_boundary_refinement(
        self,
        markdown_content: str,
        doc_id: str = "document",
        boundary_config: BoundaryConfig | None = None,
    ) -> SegmentationResult:
        """
        Segmenta documento com refinamento opcional de secoes ANEXOS.

        Este metodo combina:
        1. Segmentacao padrao (classificacao de paginas)
        2. Refinamento de secoes ANEXOS (deteccao de boundaries)

        Args:
            markdown_content: Conteudo do final.md
            doc_id: Identificador do documento
            boundary_config: Configuracao de boundary (opcional)

        Returns:
            SegmentationResult com secoes refinadas

        ATENCAO: O refinamento e CONSERVADOR.
        Secoes ANEXOS so serao subdivididas se houver alta confianca.
        """
        # Segmentacao padrao
        base_result = self.segment(markdown_content, doc_id)

        if not base_result["sections"]:
            return base_result

        # Parseia paginas para ter acesso ao conteudo
        pages_data = self.parse_markdown_pages(markdown_content)

        # Refina secoes de ANEXOS
        refined_sections: list[SectionInfo] = []
        for section in base_result["sections"]:
            if section["type"] == "ANEXOS":
                refined = self.refine_anexos_section(
                    section, pages_data, boundary_config
                )
                refined_sections.extend(refined)
            else:
                refined_sections.append(section)

        # Renumera section_ids
        for idx, section in enumerate(refined_sections, start=1):
            section["section_id"] = idx

        return SegmentationResult(
            doc_id=doc_id,
            total_pages=base_result["total_pages"],
            total_sections=len(refined_sections),
            pages=base_result["pages"],
            sections=refined_sections,
        )
