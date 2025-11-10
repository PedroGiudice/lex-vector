"""
Jurisprudence Extractor - Extração de jurisprudência por tema
"""
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class JurisprudenceEntry:
    """Entrada de jurisprudência extraída"""
    numero_processo: Optional[str]
    tribunal: str
    vara: Optional[str]
    data_publicacao: str
    tipo_decisao: Optional[str]
    tema: str
    ementa: Optional[str]
    dispositivo: Optional[str]
    partes: List[str]
    texto_completo: str
    source_file: str
    page_number: int
    confidence: float


class JurisprudenceExtractor:
    """
    Extrai e classifica jurisprudência de documentos jurídicos
    """

    def __init__(self, config: Dict, rag_engine):
        self.config = config
        self.rag_engine = rag_engine
        self.temas_interesse = config['extraction']['temas_interesse']
        self.min_confidence = config['extraction']['min_confidence']

        # Patterns de regex para extração
        self.patterns = {
            'numero_processo': re.compile(
                r'(?:processo|proc\.|n[°º])\s*:?\s*(\d{7}-?\d{2}\.?\d{4}\.?\d{1}\.?\d{2}\.?\d{4})',
                re.IGNORECASE
            ),
            'vara': re.compile(
                r'(\d+[ªº°]?\s*vara\s+(?:cível|criminal|trabalhista|federal|estadual)?)',
                re.IGNORECASE
            ),
            'tipo_decisao': re.compile(
                r'\b(sentença|acórdão|despacho|decisão|agravo|recurso|apelação)\b',
                re.IGNORECASE
            ),
            'partes': re.compile(
                r'(?:autor|autora|requerente|apelante|recorrente|exequente)\s*:?\s*([A-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ][a-záàâãéèêíïóôõöúçñ\s]+)',
                re.IGNORECASE
            )
        }

    def extract_numero_processo(self, text: str) -> Optional[str]:
        """Extrai número do processo"""
        match = self.patterns['numero_processo'].search(text)
        return match.group(1) if match else None

    def extract_vara(self, text: str) -> Optional[str]:
        """Extrai vara/comarca"""
        match = self.patterns['vara'].search(text)
        return match.group(1) if match else None

    def extract_tipo_decisao(self, text: str) -> Optional[str]:
        """Extrai tipo de decisão"""
        matches = self.patterns['tipo_decisao'].findall(text)
        return matches[0] if matches else None

    def extract_partes(self, text: str) -> List[str]:
        """Extrai partes do processo"""
        matches = self.patterns['partes'].findall(text)
        return [m.strip() for m in matches[:10]]  # Limitar a 10 partes

    def extract_ementa(self, text: str) -> Optional[str]:
        """
        Tenta extrair ementa do texto

        Ementa geralmente aparece no início, entre tags ou após "EMENTA:"
        """
        # Procurar por "EMENTA:" seguido de texto
        match = re.search(r'EMENTA\s*:?\s*(.+?)(?:\n\n|\n[A-Z]{2,})', text, re.DOTALL | re.IGNORECASE)
        if match:
            ementa = match.group(1).strip()
            # Limitar tamanho
            return ementa[:1000] if len(ementa) > 1000 else ementa

        # Fallback: pegar primeiros 500 caracteres
        return text[:500].strip()

    def extract_dispositivo(self, text: str) -> Optional[str]:
        """
        Tenta extrair dispositivo (parte final da decisão)

        Procura por palavras-chave como "ISTO POSTO", "DISPOSITIVO", etc.
        """
        patterns = [
            r'(?:ISTO POSTO|ANTE O EXPOSTO|DISPOSITIVO)\s*:?\s*(.+)',
            r'(?:DECIDO|DETERMINO|JULGO)\s+(.+?)(?:\n\n|\.|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                dispositivo = match.group(1).strip()
                return dispositivo[:500] if len(dispositivo) > 500 else dispositivo

        return None

    def classify_theme(self, text: str) -> Tuple[str, float]:
        """
        Classifica o texto em um dos temas de interesse

        Args:
            text: Texto para classificar

        Returns:
            Tupla (tema, confidence)
        """
        # Para cada tema, calcular similaridade
        best_theme = "outros"
        best_score = 0.0

        for tema in self.temas_interesse:
            # Buscar similares no RAG
            results = self.rag_engine.search(
                query=f"jurisprudência sobre {tema}",
                top_k=1
            )

            if results:
                score = results[0]['similarity']
                if score > best_score:
                    best_score = score
                    best_theme = tema

        # Se nenhum tema teve boa similaridade, classificar como "outros"
        if best_score < self.min_confidence:
            best_theme = "outros"

        return best_theme, best_score

    def extract_from_text(
        self,
        text: str,
        metadata: Dict,
        theme: Optional[str] = None
    ) -> Optional[JurisprudenceEntry]:
        """
        Extrai entrada de jurisprudência de um texto

        Args:
            text: Texto do documento
            metadata: Metadata do documento
            theme: Tema (se None, será classificado automaticamente)

        Returns:
            JurisprudenceEntry ou None se não for jurisprudência relevante
        """
        # Classificar tema
        if theme is None:
            theme, confidence = self.classify_theme(text)
        else:
            confidence = 1.0

        # Verificar se é jurisprudência válida (deve ter processo ou decisão)
        numero_processo = self.extract_numero_processo(text)
        tipo_decisao = self.extract_tipo_decisao(text)

        if not numero_processo and not tipo_decisao:
            logger.debug("Texto não parece ser jurisprudência (sem processo ou decisão)")
            return None

        # Extrair campos
        entry = JurisprudenceEntry(
            numero_processo=numero_processo,
            tribunal=metadata.get('tribunal', ''),
            vara=self.extract_vara(text),
            data_publicacao=metadata.get('data', ''),
            tipo_decisao=tipo_decisao,
            tema=theme,
            ementa=self.extract_ementa(text),
            dispositivo=self.extract_dispositivo(text),
            partes=self.extract_partes(text),
            texto_completo=text[:2000],  # Limitar tamanho
            source_file=metadata.get('source_file', ''),
            page_number=metadata.get('page_number', 0),
            confidence=confidence
        )

        return entry

    def extract_from_search_results(
        self,
        search_results: List[Dict],
        theme: str
    ) -> List[JurisprudenceEntry]:
        """
        Extrai jurisprudência de resultados de busca RAG

        Args:
            search_results: Resultados da busca RAG
            theme: Tema da busca

        Returns:
            Lista de entradas de jurisprudência
        """
        entries = []

        for result in search_results:
            text = result['text']
            metadata = result['metadata']
            confidence = result['similarity']

            entry = self.extract_from_text(text, metadata, theme)

            if entry:
                # Atualizar confidence com a do RAG
                entry.confidence = min(entry.confidence, confidence)

                if entry.confidence >= self.min_confidence:
                    entries.append(entry)

        logger.info(f"✓ Extraídas {len(entries)} entradas de jurisprudência para tema '{theme}'")
        return entries

    def extract_by_theme(self, theme: str, top_k: int = 20) -> List[JurisprudenceEntry]:
        """
        Extrai jurisprudência por tema específico

        Args:
            theme: Tema de interesse
            top_k: Número máximo de resultados

        Returns:
            Lista de entradas de jurisprudência
        """
        logger.info(f"Extraindo jurisprudência sobre: {theme}")

        # Buscar no RAG
        search_results = self.rag_engine.search_by_theme(theme, top_k=top_k)

        # Extrair jurisprudência
        entries = self.extract_from_search_results(search_results, theme)

        return entries

    def extract_all_themes(self, top_k_per_theme: int = 10) -> Dict[str, List[JurisprudenceEntry]]:
        """
        Extrai jurisprudência para todos os temas configurados

        Args:
            top_k_per_theme: Número de resultados por tema

        Returns:
            Dict {tema: [entries]}
        """
        results = {}

        logger.info(f"Extraindo jurisprudência para {len(self.temas_interesse)} temas")

        for theme in self.temas_interesse:
            entries = self.extract_by_theme(theme, top_k=top_k_per_theme)
            if entries:
                results[theme] = entries

        total_entries = sum(len(entries) for entries in results.values())
        logger.info(f"✓ Total: {total_entries} entradas extraídas em {len(results)} temas")

        return results

    def save_to_json(self, entries: List[JurisprudenceEntry], output_path: Path):
        """Salva entradas em JSON"""
        data = [asdict(entry) for entry in entries]

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ {len(entries)} entradas salvas em {output_path}")

    def generate_report(
        self,
        theme_entries: Dict[str, List[JurisprudenceEntry]]
    ) -> Dict:
        """
        Gera relatório consolidado de extração

        Args:
            theme_entries: Dict {tema: [entries]}

        Returns:
            Dict com estatísticas
        """
        report = {
            'total_temas': len(theme_entries),
            'total_entradas': sum(len(entries) for entries in theme_entries.values()),
            'por_tema': {},
            'tribunais': defaultdict(int),
            'tipos_decisao': defaultdict(int),
            'periodo': {
                'inicio': None,
                'fim': None
            }
        }

        all_dates = []

        for theme, entries in theme_entries.items():
            report['por_tema'][theme] = {
                'total': len(entries),
                'com_processo': sum(1 for e in entries if e.numero_processo),
                'com_ementa': sum(1 for e in entries if e.ementa),
                'confidence_media': round(sum(e.confidence for e in entries) / len(entries), 3) if entries else 0
            }

            # Agregar tribunais e tipos
            for entry in entries:
                if entry.tribunal:
                    report['tribunais'][entry.tribunal] += 1
                if entry.tipo_decisao:
                    report['tipos_decisao'][entry.tipo_decisao.lower()] += 1
                if entry.data_publicacao:
                    all_dates.append(entry.data_publicacao)

        # Período
        if all_dates:
            report['periodo']['inicio'] = min(all_dates)
            report['periodo']['fim'] = max(all_dates)

        # Converter defaultdict para dict normal
        report['tribunais'] = dict(report['tribunais'])
        report['tipos_decisao'] = dict(report['tipos_decisao'])

        return report
