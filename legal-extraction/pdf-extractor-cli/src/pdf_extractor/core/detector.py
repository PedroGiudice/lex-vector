"""
Detector automático de sistemas judiciais brasileiros.

Portado de: judicial-system-detector.js (verbose-correct-doodle)

Detecta automaticamente qual sistema de processo judicial eletrônico brasileiro
gerou o PDF, baseado em padrões textuais específicos de cada sistema.

Sistemas suportados:
- PJE (Processo Judicial Eletrônico - CNJ)
- ESAJ (Sistema de Automação da Justiça - Softplan)
- EPROC (Sistema de Processo Eletrônico - TRF4)
- PROJUDI (Processo Judicial Digital)
- STF (Sistema e-STF - Supremo Tribunal Federal)
- STJ (Sistema e-STJ - Superior Tribunal de Justiça)
"""

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass
class SystemConfig:
    """Configuração de detecção para um sistema judicial"""

    name: str
    code: str
    priority: int  # 1 = alta (específico), 2 = média, 3 = baixa (genérico)
    signatures: list[Pattern]
    min_matches: int
    description: str


@dataclass
class DetectionResult:
    """Resultado de detecção de sistema"""

    system: str
    name: str
    confidence: int  # 0-100
    matches: int
    total_patterns: int
    description: str


@dataclass
class SystemDetection:
    """Resultado completo da detecção"""

    system: str
    name: str
    confidence: int
    details: dict


class JudicialSystemDetector:
    """
    Detecta automaticamente qual sistema judicial gerou o PDF.

    Usa análise de padrões textuais com sistema de scoring baseado em:
    - Quantidade de matches
    - Prioridade do sistema (especificidade)
    - Ratio de matches vs total de padrões

    Example:
        >>> detector = JudicialSystemDetector()
        >>> result = detector.detect_system(pdf_text)
        >>> print(f"Sistema: {result.system}, Confiança: {result.confidence}%")
    """

    def __init__(self):
        """Inicializa detector com padrões de todos os sistemas"""

        self.patterns = {
            "STF": SystemConfig(
                name="STF (Supremo Tribunal Federal)",
                code="STF",
                priority=1,  # Alta prioridade (padrões muito específicos)
                signatures=[
                    re.compile(r'supremo\s+tribunal\s+federal', re.I),
                    re.compile(r'e-stf', re.I),
                    re.compile(r'portal\.stf\.jus\.br', re.I),
                    re.compile(r'peticionamento\s+eletr[oô]nico\s+stf', re.I),
                    re.compile(r'resolu[cç][aã]o\s+stf\s+693', re.I),
                    re.compile(r'pkcs\s*[#]?\s*7', re.I),  # Assinatura PKCS7 específica do STF
                    re.compile(r'projeto\s+victor', re.I),
                ],
                min_matches=2,
                description="PDF gerado pelo sistema e-STF com assinatura PKCS7 e marca d'água com CPF",
            ),
            "STJ": SystemConfig(
                name="STJ (Superior Tribunal de Justiça)",
                code="STJ",
                priority=1,
                signatures=[
                    re.compile(r'superior\s+tribunal\s+de\s+justi[cç]a', re.I),
                    re.compile(r'e-stj', re.I),
                    re.compile(r'www\.stj\.jus\.br', re.I),
                    re.compile(r'central\s+do\s+processo\s+eletr[oô]nico', re.I),
                    re.compile(r'resolu[cç][aã]o\s+stj/gp\s+10', re.I),
                    re.compile(r'autentique\s+em:\s*https?://www\.stj\.jus\.br/validar', re.I),
                ],
                min_matches=2,
                description="PDF gerado pelo sistema e-STJ com múltiplos elementos de validação",
            ),
            "PJE": SystemConfig(
                name="PJE (Processo Judicial Eletrônico)",
                code="PJE",
                priority=2,
                signatures=[
                    re.compile(r'processo\s+judicial\s+eletr[oô]nico', re.I),
                    re.compile(r'\bpje\b', re.I),
                    re.compile(r'resolu[cç][aã]o\s+cnj\s+281', re.I),
                    re.compile(
                        r'documento\s+assinado\s+por.*e\s+certificado\s+digitalmente\s+por',
                        re.I,
                    ),
                    re.compile(
                        r'c[oó]digo\s+de\s+verifica[cç][aã]o:\s*[A-Z0-9]{4}\.[0-9]{4}\.[0-9]X{2}[0-9]\.[X0-9]{4}',
                        re.I,
                    ),
                    re.compile(
                        r'este\s+documento\s+foi\s+gerado\s+pelo\s+usu[aá]rio\s+\d{3}\.\d{3}\.\d{3}-\d{2}',
                        re.I,
                    ),
                    re.compile(r'trt\d+\.jus\.br/pje', re.I),
                    re.compile(r'trf\d+\.jus\.br/pje', re.I),
                ],
                min_matches=2,
                description="PDF gerado pelo PJE com códigos alfanuméricos e timestamps repetitivos",
            ),
            "ESAJ": SystemConfig(
                name="ESAJ (Sistema de Automação da Justiça)",
                code="ESAJ",
                priority=2,
                signatures=[
                    re.compile(r'e-saj', re.I),
                    re.compile(r'\besaj\b', re.I),
                    re.compile(r'softplan', re.I),
                    re.compile(r'portal\s+e-saj', re.I),
                    re.compile(r'confer[eê]ncia\s+de\s+documento\s+digital', re.I),
                    re.compile(r'tjsp\.jus\.br.*esaj', re.I),
                    re.compile(r'tjce\.jus\.br.*esaj', re.I),
                    re.compile(r'tjam\.jus\.br.*esaj', re.I),
                    re.compile(r'tjms\.jus\.br.*esaj', re.I),
                    re.compile(r'resolu[cç][aã]o\s+.*552/11', re.I),  # Resolução do brasão TJSP
                ],
                min_matches=2,
                description="PDF gerado pelo ESAJ com selo lateral vertical e QR codes",
            ),
            "EPROC": SystemConfig(
                name="EPROC (Sistema de Processo Eletrônico)",
                code="EPROC",
                priority=2,
                signatures=[
                    re.compile(r'\beproc\b', re.I),
                    re.compile(r'sistema\s+de\s+processo\s+eletr[oô]nico', re.I),
                    re.compile(r'trf4\.jus\.br.*eproc', re.I),
                    re.compile(r'trf2\.jus\.br.*eproc', re.I),
                    re.compile(r'trf6\.jus\.br.*eproc', re.I),
                    re.compile(r'tjrs\.jus\.br.*eproc', re.I),
                    re.compile(r'tjsc\.jus\.br.*eproc', re.I),
                    re.compile(r'\.p7s', re.I),  # Referência a arquivo de assinatura destacada
                    re.compile(r'cades', re.I),  # Padrão CAdES específico
                    re.compile(r'assinatura\s+destacada', re.I),
                ],
                min_matches=2,
                description="PDF gerado pelo EPROC com assinatura destacada (arquivo .p7s separado)",
            ),
            "PROJUDI": SystemConfig(
                name="PROJUDI (Processo Judicial Digital)",
                code="PROJUDI",
                priority=3,  # Menor prioridade (padrões menos específicos)
                signatures=[
                    re.compile(r'projudi', re.I),
                    re.compile(r'processo\s+judicial\s+digital', re.I),
                    re.compile(r'tjba\.jus\.br.*projudi', re.I),
                    re.compile(r'tjce\.jus\.br.*projudi', re.I),
                    re.compile(r'tjpr\.jus\.br.*projudi', re.I),
                    re.compile(r'tjmg\.jus\.br.*projudi', re.I),
                    re.compile(r'vers[aã]o\s+1\.\d+', re.I),  # Versões variadas
                    re.compile(r'assinador\s+livre', re.I),
                    re.compile(
                        r'universidade\s+federal\s+de\s+campina\s+grande', re.I
                    ),  # Origem do PROJUDI
                ],
                min_matches=2,
                description="PDF gerado pelo PROJUDI com variações regionais significativas",
            ),
        }

        # Padrões gerais de assinatura ICP-Brasil (não identificam sistema específico)
        self.icp_brasil_patterns = [
            re.compile(r'icp-brasil', re.I),
            re.compile(r'certificado\s+digital', re.I),
            re.compile(r'assinado\s+digitalmente', re.I),
            re.compile(r'pades|cades|xades', re.I),
            re.compile(r'ac\s+[a-z]+', re.I),  # Autoridade Certificadora
            re.compile(
                r'iti\s+-\s+instituto\s+nacional\s+de\s+tecnologia\s+da\s+informa[cç][aã]o',
                re.I,
            ),
        ]

    def detect_system(self, text: str, metadata: dict | None = None) -> SystemDetection:
        """
        Detecta qual sistema judicial gerou o PDF.

        Args:
            text: Texto extraído do PDF
            metadata: Metadados do PDF (opcional, não usado atualmente)

        Returns:
            SystemDetection com system code, name, confidence e details

        Example:
            >>> detector = JudicialSystemDetector()
            >>> result = detector.detect_system("Documento PJE assinado...")
            >>> result.system
            'PJE'
            >>> result.confidence
            85
        """
        if not text or len(text) < 100:
            return SystemDetection(
                system="UNKNOWN",
                name="Sistema Desconhecido",
                confidence=0,
                details={"reason": "Texto muito curto para análise (mínimo 100 caracteres)"},
            )

        results: list[DetectionResult] = []

        # Testa cada sistema
        for system_code, config in self.patterns.items():
            matches = self._count_matches(text, config.signatures)
            match_ratio = matches / len(config.signatures)

            # Calcula confiança baseada em matches e prioridade
            confidence = 0
            if matches >= config.min_matches:
                # Base: 40-100% dependendo do ratio de matches
                confidence = 40 + (match_ratio * 60)

                # Bônus por prioridade (sistemas mais específicos têm bônus)
                if config.priority == 1:
                    confidence = min(100, confidence + 10)

                # Bônus por matches acima do mínimo
                if matches > config.min_matches:
                    confidence = min(100, confidence + ((matches - config.min_matches) * 5))

            results.append(
                DetectionResult(
                    system=system_code,
                    name=config.name,
                    confidence=round(confidence),
                    matches=matches,
                    total_patterns=len(config.signatures),
                    description=config.description,
                )
            )

        # Ordena por confiança
        results.sort(key=lambda r: r.confidence, reverse=True)

        top_result = results[0]

        # Se nenhum sistema específico foi detectado com confiança razoável
        if top_result.confidence < 40:
            # Verifica se tem padrões ICP-Brasil gerais
            icp_matches = self._count_matches(text, self.icp_brasil_patterns)
            if icp_matches >= 2:
                return SystemDetection(
                    system="GENERIC_JUDICIAL",
                    name="Sistema Judicial Genérico (ICP-Brasil)",
                    confidence=50,
                    details={
                        "reason": "Detectado certificação ICP-Brasil mas sistema específico não identificado",
                        "icp_matches": icp_matches,
                        "all_results": [
                            {
                                "system": r.system,
                                "confidence": r.confidence,
                                "matches": r.matches,
                            }
                            for r in results[:3]
                        ],
                    },
                )

            return SystemDetection(
                system="UNKNOWN",
                name="Sistema Desconhecido",
                confidence=0,
                details={
                    "reason": "Nenhum padrão de sistema judicial brasileiro detectado",
                    "all_results": [
                        {"system": r.system, "confidence": r.confidence, "matches": r.matches}
                        for r in results[:3]
                    ],
                },
            )

        return SystemDetection(
            system=top_result.system,
            name=top_result.name,
            confidence=top_result.confidence,
            details={
                "matches": top_result.matches,
                "total_patterns": top_result.total_patterns,
                "description": top_result.description,
                "all_results": [
                    {"system": r.system, "confidence": r.confidence, "matches": r.matches}
                    for r in results[:3]  # Top 3 para debugging
                ],
            },
        )

    def _count_matches(self, text: str, patterns: list[Pattern]) -> int:
        """
        Conta quantos padrões regex fazem match no texto.

        Args:
            text: Texto a ser analisado
            patterns: Lista de padrões regex compilados

        Returns:
            Número de matches encontrados
        """
        count = 0
        for pattern in patterns:
            if pattern.search(text):
                count += 1
        return count

    def get_system_info(self, system_code: str) -> SystemConfig | None:
        """
        Retorna informações detalhadas sobre um sistema específico.

        Args:
            system_code: Código do sistema (PJE, ESAJ, STF, STJ, EPROC, PROJUDI)

        Returns:
            SystemConfig ou None se sistema não encontrado
        """
        return self.patterns.get(system_code)

    def list_supported_systems(self) -> list[dict]:
        """
        Lista todos os sistemas suportados.

        Returns:
            Lista de dicts com code, name e description

        Example:
            >>> detector = JudicialSystemDetector()
            >>> systems = detector.list_supported_systems()
            >>> len(systems)
            6
        """
        return [
            {"code": code, "name": config.name, "description": config.description}
            for code, config in self.patterns.items()
        ]
