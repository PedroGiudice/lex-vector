"""
Processador para dados do STJ Dados Abertos.
Reaproveita código do sistema DJEN para evitar retrabalho.
"""
from __future__ import annotations

import json
import hashlib
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Final
from dataclasses import dataclass, field
from enum import Enum
import logging
from rich.console import Console

console = Console()
logger = logging.getLogger(__name__)


class ResultadoJulgamento(Enum):
    """
    Classificação do resultado do julgamento.

    Ordem importa: PARCIAL_PROVIMENTO é mais específico que PROVIMENTO,
    então deve ser checado primeiro.
    """
    PROVIMENTO = "provimento"
    PARCIAL_PROVIMENTO = "parcial_provimento"
    DESPROVIMENTO = "desprovimento"
    NAO_CONHECIDO = "nao_conhecido"
    INDETERMINADO = "indeterminado"


@dataclass
class LegalResultClassifier:
    """
    Classificador de resultado de julgamentos baseado em JurisMiner (R library).

    Implementa regex patterns para identificar o resultado do julgamento
    (provimento, parcial provimento, desprovimento, não conhecido) a partir
    do texto do dispositivo ou ementa.

    Examples:
        >>> classifier = LegalResultClassifier()
        >>> classifier.classificar("Recurso conhecido e provido.")
        <ResultadoJulgamento.PROVIMENTO: 'provimento'>

        >>> classifier.classificar("Recurso parcialmente provido.")
        <ResultadoJulgamento.PARCIAL_PROVIMENTO: 'parcial_provimento'>
    """

    # Patterns para PROVIMENTO (full grant)
    PROVIMENTO_PATTERNS: Final[List[str]] = field(default_factory=lambda: [
        r'd(ou|ar|ei)(-lhe)?\s+provimento',
        r'recurso\s+(especial\s+)?(conhecido\s+e\s+)?provido',
        r'provido\s+o\s+recurso',
        r'dar-lhe\s+provimento',
    ])

    # Patterns para PARCIAL_PROVIMENTO (partial grant) - CHECK FIRST (more specific)
    PARCIAL_PROVIMENTO_PATTERNS: Final[List[str]] = field(default_factory=lambda: [
        r'parcial(mente)?\s+provido',
        r'provido\s+(em\s+)?parte',
        r'd(ou|ar|ei)\s+parcial\s+provimento',
        r'parcial\s+provimento',
    ])

    # Patterns para DESPROVIMENTO (denial)
    DESPROVIMENTO_PATTERNS: Final[List[str]] = field(default_factory=lambda: [
        r'n[ãa]o\s+provido',
        r'negar\s+provimento',
        r'improvido',
        r'desprovido',
        r'negado\s+provimento',
    ])

    # Patterns para NAO_CONHECIDO (inadmissible)
    NAO_CONHECIDO_PATTERNS: Final[List[str]] = field(default_factory=lambda: [
        r'n[ãa]o\s+conhe[çc](o|er|ido|eu)',
        r'recurso\s+(especial\s+)?n[ãa]o\s+conhecido',
    ])

    def normalizar_texto(self, texto: str) -> str:
        """
        Normaliza texto para classificação.

        Remove headers padrão (SUPERIOR TRIBUNAL DE JUSTIÇA, nomes de turmas, etc)
        e padroniza espaços em branco.

        Args:
            texto: Texto original

        Returns:
            Texto normalizado (lowercase, sem headers, espaços padronizados)
        """
        if not texto:
            return ""

        # Convert to lowercase
        texto = texto.lower()

        # Remove common headers
        headers_to_remove = [
            r'superior\s+tribunal\s+de\s+justi[çc]a',
            r'(primeira|segunda|terceira|quarta|quinta|sexta)\s+turma',
            r'(primeira|segunda|terceira|quarta)\s+se[çc][ãa]o',
            r'corte\s+especial',
            r'relat[óo]r(a)?:',
            r'ministro(a)?:',
        ]

        for header_pattern in headers_to_remove:
            texto = re.sub(header_pattern, '', texto)

        # Standardize whitespace
        texto = re.sub(r'\s+', ' ', texto).strip()

        return texto

    def extrair_relatorio(self, texto: str) -> str:
        """
        Extrai seção RELATÓRIO do texto.

        Args:
            texto: Texto completo do acórdão

        Returns:
            Texto da seção RELATÓRIO ou string vazia
        """
        if not texto:
            return ""

        # Pattern: RELATÓRIO até VOTO ou próxima seção
        pattern = r'RELAT[ÓO]RIO\s*[:\-]?\s*(.*?)(?=VOTO|EMENTA|DECIS[ÃA]O|$)'
        match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1).strip()

        return ""

    def extrair_voto(self, texto: str) -> str:
        """
        Extrai seção VOTO do texto.

        Args:
            texto: Texto completo do acórdão

        Returns:
            Texto da seção VOTO ou string vazia
        """
        if not texto:
            return ""

        # Pattern: VOTO até DISPOSITIVO ou próxima seção
        pattern = r'VOTO\s*[:\-]?\s*(.*?)(?=DISPOSITIVO|DECIS[ÃA]O|EMENTA|$)'
        match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1).strip()

        return ""

    def extrair_dispositivo(self, texto: str) -> str:
        """
        Extrai seção DISPOSITIVO do texto.

        Args:
            texto: Texto completo do acórdão

        Returns:
            Texto da seção DISPOSITIVO ou string vazia
        """
        if not texto:
            return ""

        # Pattern: DISPOSITIVO, DECISÃO ou ACÓRDÃO até final ou próxima seção major
        pattern = r'(DISPOSITIVO|DECIS[ÃA]O|AC[ÓO]RD[ÃA]O)\s*[:\-]?\s*(.*?)(?=EMENTA|RELAT[ÓO]RIO|$)'
        match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(2).strip()

        return ""

    def classificar(self, texto: str) -> ResultadoJulgamento:
        """
        Classifica resultado do julgamento a partir do texto.

        ORDEM IMPORTA:
        1. PARCIAL_PROVIMENTO (mais específico)
        2. NAO_CONHECIDO
        3. DESPROVIMENTO
        4. PROVIMENTO
        5. INDETERMINADO (fallback)

        Args:
            texto: Texto do dispositivo ou ementa

        Returns:
            ResultadoJulgamento classificado

        Examples:
            >>> classifier = LegalResultClassifier()
            >>> classifier.classificar("Recurso conhecido e provido.")
            <ResultadoJulgamento.PROVIMENTO: 'provimento'>

            >>> classifier.classificar("Recurso parcialmente provido.")
            <ResultadoJulgamento.PARCIAL_PROVIMENTO: 'parcial_provimento'>

            >>> classifier.classificar("Recurso não conhecido.")
            <ResultadoJulgamento.NAO_CONHECIDO: 'nao_conhecido'>

            >>> classifier.classificar("Recurso improvido.")
            <ResultadoJulgamento.DESPROVIMENTO: 'desprovimento'>
        """
        if not texto:
            return ResultadoJulgamento.INDETERMINADO

        # Normalize text
        texto_normalizado = self.normalizar_texto(texto)

        # Check PARCIAL_PROVIMENTO first (more specific than PROVIMENTO)
        for pattern in self.PARCIAL_PROVIMENTO_PATTERNS:
            if re.search(pattern, texto_normalizado, re.IGNORECASE):
                return ResultadoJulgamento.PARCIAL_PROVIMENTO

        # Check NAO_CONHECIDO
        for pattern in self.NAO_CONHECIDO_PATTERNS:
            if re.search(pattern, texto_normalizado, re.IGNORECASE):
                return ResultadoJulgamento.NAO_CONHECIDO

        # Check DESPROVIMENTO
        for pattern in self.DESPROVIMENTO_PATTERNS:
            if re.search(pattern, texto_normalizado, re.IGNORECASE):
                return ResultadoJulgamento.DESPROVIMENTO

        # Check PROVIMENTO (less specific, check last)
        for pattern in self.PROVIMENTO_PATTERNS:
            if re.search(pattern, texto_normalizado, re.IGNORECASE):
                return ResultadoJulgamento.PROVIMENTO

        # Could not classify
        return ResultadoJulgamento.INDETERMINADO


def extrair_ementa(texto: str) -> str:
    """
    Extrai ementa do texto integral.

    Args:
        texto: Texto completo do acórdão

    Returns:
        Texto da ementa ou string vazia
    """
    if not texto:
        return ""

    # Pattern: EMENTA até próxima seção
    pattern = r'EMENTA\s*[:\-]?\s*(.*?)(?=RELAT[ÓO]RIO|VOTO|DISPOSITIVO|AC[ÓO]RD[ÃA]O)'
    match = re.search(pattern, texto, re.IGNORECASE | re.DOTALL)

    if match:
        conteudo = match.group(1).strip()
        # Only return if there's actual content (not just punctuation)
        if conteudo and len(conteudo) > 1:
            return conteudo

    return ""


def extrair_relator(texto: str) -> str:
    """
    Extrai nome do relator do texto.

    Args:
        texto: Texto completo do acórdão

    Returns:
        Nome do relator ou string vazia
    """
    if not texto:
        return ""

    # Patterns comuns para relator
    patterns = [
        r'RELAT[ÓO]R(?:\(A\))?\s*[:\-]\s*(?:MINISTR[OA]\s+)?([A-ZÀÁÃÂÉÊÍÓÔÕÚÇ\s]+)',
        r'MINISTR[OA]\s+RELAT[ÓO]R(?:\(A\))?\s*[:\-]?\s*([A-ZÀÁÃÂÉÊÍÓÔÕÚÇ\s]+)',
        r'(?:O|A)\s+(?:SENHOR|SENHORA)\s+MINISTR[OA]\s+([A-ZÀÁÃÂÉÊÍÓÔÕÚÇ\s]+)\s*\(RELAT[ÓO]R',
    ]

    for pattern in patterns:
        match = re.search(pattern, texto, re.IGNORECASE)
        if match:
            # Clean up the name (limit to ~50 chars, remove extra spaces)
            nome = match.group(1).strip()
            nome = re.sub(r'\s+', ' ', nome)
            return nome[:100]  # Limit length

    return ""


def processar_publicacao_stj(json_data: Dict) -> Dict:
    """
    Processa publicação JSON do STJ Dados Abertos.

    DIFERENÇA CRÍTICA vs DJEN:
    - Input é JSON estruturado (não HTML!)
    - Campos já vêm separados (ementa, relatório, voto)
    - Texto integral já está limpo
    - Classifica resultado do julgamento (provimento, desprovimento, etc)

    Args:
        json_data: Dict do JSON STJ com estrutura esperada:
            - processo: número do processo
            - dataPublicacao: data ISO
            - dataJulgamento: data ISO
            - orgaoJulgador: turma/seção
            - relator: nome do ministro
            - ementa: texto da ementa
            - inteiro_teor: texto completo do acórdão
            - assuntos: lista de assuntos

    Returns:
        Dict pronto para inserção no DuckDB, incluindo 'resultado_julgamento'
    """
    # Initialize classifier
    classifier = LegalResultClassifier()

    # Extrair campos principais
    numero_processo = json_data.get('processo', '')
    texto_integral = json_data.get('inteiro_teor', '')

    # Se não tem inteiro teor, tentar concatenar partes
    if not texto_integral:
        partes = []
        if json_data.get('ementa'):
            partes.append(f"EMENTA:\n{json_data['ementa']}")
        if json_data.get('relatorio'):
            partes.append(f"RELATÓRIO:\n{json_data['relatorio']}")
        if json_data.get('voto'):
            partes.append(f"VOTO:\n{json_data['voto']}")
        if json_data.get('decisao'):
            partes.append(f"DECISÃO:\n{json_data['decisao']}")

        texto_integral = "\n\n".join(partes)

    # Gerar hash para deduplicação
    hash_conteudo = hashlib.sha256(texto_integral.encode('utf-8')).hexdigest()

    # Extrair ementa
    # STJ às vezes tem campo 'ementa' direto, outras vezes está no texto
    ementa = json_data.get('ementa')
    if not ementa and texto_integral:
        ementa = extrair_ementa(texto_integral)

    # Extrair relator
    # STJ geralmente tem campo 'relator' ou 'ministro'
    relator = json_data.get('relator') or json_data.get('ministro')
    if not relator and texto_integral:
        relator = extrair_relator(texto_integral)

    # Converter datas
    data_publicacao = json_data.get('dataPublicacao')
    data_julgamento = json_data.get('dataJulgamento')

    # Se as datas vierem em timestamp (milliseconds)
    if isinstance(data_publicacao, (int, float)):
        data_publicacao = datetime.fromtimestamp(data_publicacao / 1000).isoformat()
    if isinstance(data_julgamento, (int, float)):
        data_julgamento = datetime.fromtimestamp(data_julgamento / 1000).isoformat()

    # Classificar tipo (STJ é sempre acórdão ou decisão monocrática)
    tipo_decisao = 'Acórdão'
    texto_inicio = texto_integral.lower()[:500]
    if 'monocr' in texto_inicio:  # Matches both monocrática and monocratica
        tipo_decisao = 'Decisão Monocrática'

    # Classificar resultado do julgamento
    # Prioridade: dispositivo > ementa > indeterminado
    resultado = ResultadoJulgamento.INDETERMINADO

    # Try extracting dispositivo first
    dispositivo = classifier.extrair_dispositivo(texto_integral)
    if dispositivo:
        resultado = classifier.classificar(dispositivo)

    # Fallback to ementa if dispositivo didn't give a result
    if resultado == ResultadoJulgamento.INDETERMINADO and ementa:
        resultado = classifier.classificar(ementa)

    # Montar registro processado
    return {
        'id': str(uuid.uuid4()),
        'numero_processo': numero_processo,
        'hash_conteudo': hash_conteudo,
        'tribunal': 'STJ',
        'orgao_julgador': json_data.get('orgaoJulgador', ''),
        'tipo_decisao': tipo_decisao,
        'classe_processual': json_data.get('classe', ''),
        'ementa': ementa,
        'texto_integral': texto_integral,
        'relator': relator,
        'data_publicacao': data_publicacao,
        'data_julgamento': data_julgamento,
        'resultado_julgamento': resultado.value,  # Store enum value
        'assuntos': json.dumps(json_data.get('assuntos', [])),
        'fonte': 'STJ-Dados-Abertos',
        'fonte_url': json_data.get('url', ''),
        'metadata': json.dumps({
            'original_id': json_data.get('id'),
            'versao': json_data.get('versao', '1.0'),
            'processado_em': datetime.now().isoformat()
        })
    }


@dataclass
class ProcessingStats:
    """Estatísticas de processamento."""
    processados: int = 0
    com_ementa: int = 0
    com_relator: int = 0
    classificados: int = 0
    erros: int = 0


class STJProcessor:
    """
    Processador batch para múltiplos arquivos JSON do STJ.
    """

    def __init__(self):
        self.stats = ProcessingStats()

    def processar_arquivo_json(self, json_path: Path) -> List[Dict]:
        """
        Processa um arquivo JSON do STJ.

        Args:
            json_path: Caminho do arquivo JSON

        Returns:
            Lista de dicts processados
        """
        try:
            logger.info(f"Processando: {json_path.name}")

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # O JSON pode ser lista ou objeto único
            if not isinstance(data, list):
                data = [data]

            resultados = []
            for item in data:
                try:
                    processado = processar_publicacao_stj(item)
                    resultados.append(processado)

                    # Atualizar stats
                    self.stats.processados += 1
                    if processado.get('ementa'):
                        self.stats.com_ementa += 1
                    if processado.get('relator'):
                        self.stats.com_relator += 1
                    if processado.get('resultado_julgamento') != ResultadoJulgamento.INDETERMINADO.value:
                        self.stats.classificados += 1

                except Exception as e:
                    logger.error(f"Erro processando item: {e}")
                    self.stats.erros += 1
                    continue

            logger.info(f"Processados {len(resultados)} itens de {json_path.name}")
            return resultados

        except Exception as e:
            logger.error(f"Erro ao processar arquivo {json_path}: {e}")
            self.stats.erros += 1
            return []

    def processar_batch(self, json_files: List[Path]) -> List[Dict]:
        """
        Processa múltiplos arquivos JSON.

        Args:
            json_files: Lista de caminhos de arquivos

        Returns:
            Lista consolidada de todos os registros processados
        """
        todos_resultados = []

        for json_path in json_files:
            resultados = self.processar_arquivo_json(json_path)
            todos_resultados.extend(resultados)

        return todos_resultados

    def print_stats(self):
        """Imprime estatísticas do processamento."""
        console.print("\n[bold cyan]Estatísticas de Processamento:[/bold cyan]")
        console.print(f"📄 Total processados: {self.stats.processados}")
        console.print(f"📝 Com ementa: {self.stats.com_ementa} ({self.stats.com_ementa*100//max(self.stats.processados,1)}%)")
        console.print(f"👨‍⚖️ Com relator: {self.stats.com_relator} ({self.stats.com_relator*100//max(self.stats.processados,1)}%)")
        console.print(f"🏛️ Classificados: {self.stats.classificados} ({self.stats.classificados*100//max(self.stats.processados,1)}%)")
        console.print(f"❌ Erros: {self.stats.erros}")


def test_processor():
    """Teste do processador com dados mockados."""
    # Dados de teste simulando estrutura STJ
    test_data = {
        "processo": "REsp 1234567/SP",
        "dataPublicacao": "2024-11-20T00:00:00",
        "dataJulgamento": "2024-11-15T00:00:00",
        "orgaoJulgador": "Terceira Turma",
        "relator": "Ministro Paulo de Tarso Sanseverino",
        "ementa": "RECURSO ESPECIAL. DIREITO CIVIL. RESPONSABILIDADE CIVIL. DANO MORAL. QUANTUM INDENIZATÓRIO.",
        "inteiro_teor": """
        EMENTA: RECURSO ESPECIAL. DIREITO CIVIL. RESPONSABILIDADE CIVIL.
        RELATÓRIO: O SENHOR MINISTRO PAULO DE TARSO SANSEVERINO (Relator):
        Trata-se de recurso especial interposto...
        VOTO: Como relatado, trata-se de recurso especial...
        """,
        "classe": "REsp",
        "assuntos": ["Direito Civil", "Responsabilidade Civil", "Dano Moral"]
    }

    # Processar
    resultado = processar_publicacao_stj(test_data)

    # Validar
    console.print("[bold green]Teste de Processamento:[/bold green]")
    console.print(f"✅ ID gerado: {resultado['id'][:8]}...")
    console.print(f"✅ Hash: {resultado['hash_conteudo'][:16]}...")
    console.print(f"✅ Ementa extraída: {resultado['ementa'][:50]}...")
    console.print(f"✅ Relator: {resultado['relator']}")
    console.print(f"✅ Órgão: {resultado['orgao_julgador']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_processor()