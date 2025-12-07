"""
Padrões regex para limpeza de documentos jurídicos brasileiros.

Portado de: advanced-signature-cleaner.js (verbose-correct-doodle)

Remove assinaturas digitais, selos, códigos de validação e elementos de
certificação específicos de cada sistema de processo judicial eletrônico brasileiro.

Baseado em: Pesquisa "Sistemas de processo judicial eletrônico no Brasil:
desafios técnicos de extração" (2025)
"""

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass
class CleaningPattern:
    """Padrão de limpeza individual com regex compilado"""

    description: str
    regex: Pattern
    replacement: str = ""
    category: str = "generic"


class SystemPatterns:
    """
    Padrões de limpeza para todos os sistemas judiciais brasileiros.

    Sistemas suportados:
    - PJE (Processo Judicial Eletrônico)
    - ESAJ (Sistema de Automação da Justiça - TJSP)
    - EPROC (Sistema de Processo Eletrônico - TRFs)
    - PROJUDI (variações regionais)
    - STF (Supremo Tribunal Federal)
    - STJ (Superior Tribunal de Justiça)
    - GENERIC_JUDICIAL (padrões genéricos)
    - UNIVERSAL (aplicados a todos os sistemas)
    """

    # ==========================================================================
    # PJE - Processo Judicial Eletrônico
    # ==========================================================================

    PJE = [
        CleaningPattern(
            description="Código de verificação PJE (formato XXXX.9999.9XX9.X9XX)",
            regex=re.compile(
                r'c[óo]digo\s+de\s+verifica[çc][ãa]o:\s*[A-Z0-9]{4}\.[0-9]{4}\.[0-9A-Z]{4}\.[A-Z0-9]{4}',
                re.IGNORECASE,
            ),
            category="pje",
        ),
        CleaningPattern(
            description="Timestamp de geração PJE",
            regex=re.compile(
                r'este\s+documento\s+foi\s+gerado\s+pelo\s+usu[áa]rio\s+'
                r'\d{3}\.\d{3}\.\d{3}-\d{2}\s+em\s+\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',
                re.IGNORECASE,
            ),
            category="pje",
        ),
        CleaningPattern(
            description="URL de validação PJE",
            regex=re.compile(
                r'https?://[a-z0-9.-]*\.(trt|trf|tst|cnj)\d*\.jus\.br/[^\s]*validar[^\s]*',
                re.IGNORECASE,
            ),
            category="pje",
        ),
        CleaningPattern(
            description="Tarja de assinatura dupla PJE (Resolução CNJ 281/2019)",
            regex=re.compile(
                r'documento\s+assinado\s+por\s+[^\n]{5,100}\s+e\s+certificado\s+digitalmente\s+por\s+[^\n]{5,100}',
                re.IGNORECASE,
            ),
            category="pje",
        ),
        CleaningPattern(
            description="QR Code placeholder PJE",
            regex=re.compile(r'\[QR\s+CODE\]|\{QR\s+CODE\}', re.IGNORECASE),
            category="pje",
        ),
        CleaningPattern(
            description="Rodapé PJE genérico",
            regex=re.compile(
                r'^[_\-=]+\s*processo\s+judicial\s+eletr[ôo]nico\s*[_\-=]+$',
                re.IGNORECASE | re.MULTILINE,
            ),
            category="pje",
        ),
    ]

    # ==========================================================================
    # ESAJ - Sistema de Automação da Justiça (TJSP)
    # ==========================================================================

    ESAJ = [
        CleaningPattern(
            description="Selo lateral vertical ESAJ (texto rotacionado)",
            regex=re.compile(
                r'c[óo]digo\s+do\s+documento:\s*[A-Z0-9]{8,20}', re.IGNORECASE
            ),
            category="esaj",
        ),
        CleaningPattern(
            description="Conferência de documento digital ESAJ",
            regex=re.compile(
                r'confer[êe]ncia\s+de\s+documento\s+digital.*?portal\s+e-saj',
                re.IGNORECASE | re.DOTALL,
            ),
            category="esaj",
        ),
        CleaningPattern(
            description="QR Code ESAJ com URL",
            regex=re.compile(
                r'https?://[a-z0-9.-]*\.jus\.br/[^\s]*esaj[^\s]*/documento[^\s]*',
                re.IGNORECASE,
            ),
            category="esaj",
        ),
        CleaningPattern(
            description="Barra de assinatura digital ESAJ",
            regex=re.compile(
                r'assinado\s+digitalmente\s+por:\s*[^\n]{5,80}\s+data:\s*'
                r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',
                re.IGNORECASE,
            ),
            category="esaj",
        ),
        CleaningPattern(
            description="Brasão e logotipo TJSP",
            regex=re.compile(
                r'tribunal\s+de\s+justi[çc]a\s+do\s+estado\s+de\s+s[ãa]o\s+paulo\s*-\s*tjsp',
                re.IGNORECASE,
            ),
            category="esaj",
        ),
        CleaningPattern(
            description="Referência Resolução 552/11 (brasão TJSP)",
            regex=re.compile(
                r'resolu[çc][ãa]o\s+n?[º°]?\s*552/11', re.IGNORECASE
            ),
            category="esaj",
        ),
        CleaningPattern(
            description="Marca d'água ESAJ",
            regex=re.compile(
                r'\[marca\s+d.?[áa]gua:?\s*esaj\]', re.IGNORECASE
            ),
            category="esaj",
        ),
    ]

    # ==========================================================================
    # EPROC - Sistema de Processo Eletrônico (TRFs)
    # ==========================================================================

    EPROC = [
        CleaningPattern(
            description="Referência a arquivo .p7s (assinatura destacada)",
            regex=re.compile(
                r'assinatura\s+digital\s+dispon[ií]vel\s+em:\s*[^\n]*\.p7s',
                re.IGNORECASE,
            ),
            category="eproc",
        ),
        CleaningPattern(
            description="Verificador de Conformidade ITI",
            regex=re.compile(
                r'verificador\s+de\s+conformidade\s+(iti|icp-brasil)',
                re.IGNORECASE,
            ),
            category="eproc",
        ),
        CleaningPattern(
            description="Selo PAdES padrão EPROC",
            regex=re.compile(
                r'assinado\s+eletronicamente\s+por.*?certificado\s+digital\s+icp-brasil',
                re.IGNORECASE | re.DOTALL,
            ),
            category="eproc",
        ),
        CleaningPattern(
            description="URL EPROC",
            regex=re.compile(
                r'https?://[a-z0-9.-]*\.(trf|tj)[a-z0-9]*\.jus\.br/[^\s]*eproc[^\s]*',
                re.IGNORECASE,
            ),
            category="eproc",
        ),
        CleaningPattern(
            description="ByteRange e referências técnicas CAdES",
            regex=re.compile(
                r'byterange\s*\[\s*\d+\s+\d+\s+\d+\s+\d+\s*\]', re.IGNORECASE
            ),
            category="eproc",
        ),
    ]

    # ==========================================================================
    # PROJUDI - Variações regionais
    # ==========================================================================

    PROJUDI = [
        CleaningPattern(
            description="Selo PAdES padrão PROJUDI",
            regex=re.compile(
                r'digitalmente\s+assinado\s+por.*?data:\s*\d{2}/\d{2}/\d{4}',
                re.IGNORECASE | re.DOTALL,
            ),
            category="projudi",
        ),
        CleaningPattern(
            description="URL PROJUDI (variações regionais)",
            regex=re.compile(
                r'https?://[a-z0-9.-]*\.jus\.br/[^\s]*projudi[^\s]*',
                re.IGNORECASE,
            ),
            category="projudi",
        ),
        CleaningPattern(
            description="Assinador Livre TJRJ",
            regex=re.compile(
                r'assinador\s+livre\s+(tjrj|tribunal\s+de\s+justi[çc]a\s+do\s+rio\s+de\s+janeiro)',
                re.IGNORECASE,
            ),
            category="projudi",
        ),
        CleaningPattern(
            description="Versão PROJUDI",
            regex=re.compile(
                r'projudi\s+-\s+vers[ãa]o\s+\d+\.\d+(\.\d+)?', re.IGNORECASE
            ),
            category="projudi",
        ),
        CleaningPattern(
            description="Brasões variados (variações regionais)",
            regex=re.compile(r'\[bras[ãa]o:?\s*[^\]]{5,50}\]', re.IGNORECASE),
            category="projudi",
        ),
    ]

    # ==========================================================================
    # STF - Supremo Tribunal Federal
    # ==========================================================================

    STF = [
        CleaningPattern(
            description="Marca d'água com CPF do consulente STF",
            regex=re.compile(
                r'cpf\s+do\s+consulente:\s*\d{3}\.\d{3}\.\d{3}-\d{2}',
                re.IGNORECASE,
            ),
            category="stf",
        ),
        CleaningPattern(
            description="Alerta de marca d'água STF",
            regex=re.compile(
                r'a\s+inser[çc][ãa]o\s+da\s+marca\s+d.?[áa]gua\s+se\s+sobrescreve.*?'
                r'sistemas\s+internos\s+do\s+tribunal',
                re.IGNORECASE | re.DOTALL,
            ),
            category="stf",
        ),
        CleaningPattern(
            description="Assinatura PKCS7 STF",
            regex=re.compile(
                r'assinatura\s+digital\s+pkcs\s*[#]?\s*7', re.IGNORECASE
            ),
            category="stf",
        ),
        CleaningPattern(
            description="URL validação STF",
            regex=re.compile(
                r'https?://(www\.)?stf\.jus\.br/[^\s]*(validar|autenticar)[^\s]*',
                re.IGNORECASE,
            ),
            category="stf",
        ),
        CleaningPattern(
            description="Projeto Victor (ocerização automática)",
            regex=re.compile(
                r'documento\s+processado\s+pelo\s+projeto\s+victor',
                re.IGNORECASE,
            ),
            category="stf",
        ),
        CleaningPattern(
            description="Resolução STF 693/2020",
            regex=re.compile(
                r'resolu[çc][ãa]o\s+stf\s+n?[º°]?\s*693/2020', re.IGNORECASE
            ),
            category="stf",
        ),
        CleaningPattern(
            description="Cabeçalho STF padrão",
            regex=re.compile(
                r'supremo\s+tribunal\s+federal\s*-\s*stf.*?pet\s+v3',
                re.IGNORECASE | re.DOTALL,
            ),
            category="stf",
        ),
    ]

    # ==========================================================================
    # STJ - Superior Tribunal de Justiça
    # ==========================================================================

    STJ = [
        CleaningPattern(
            description="Código de verificação STJ",
            regex=re.compile(r'c[óo]digo:\s*[A-Z0-9]{16,32}', re.IGNORECASE),
            category="stj",
        ),
        CleaningPattern(
            description="URL autenticação STJ",
            regex=re.compile(
                r'autentique\s+em:\s*https?://(www\.)?stj\.jus\.br/validar[^\s]*',
                re.IGNORECASE,
            ),
            category="stj",
        ),
        CleaningPattern(
            description="Dados de certificado STJ",
            regex=re.compile(
                r'assinado\s+por:\s*[^\n]{5,80}\s+-\s+cpf:\s*\d{3}\.\d{3}\.\d{3}-\d{2}',
                re.IGNORECASE,
            ),
            category="stj",
        ),
        CleaningPattern(
            description="Timestamp STJ",
            regex=re.compile(
                r'data:\s*\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+(brt|brst|-03:?00|-02:?00)',
                re.IGNORECASE,
            ),
            category="stj",
        ),
        CleaningPattern(
            description="Disclaimer MP 2.200-2/2001",
            regex=re.compile(
                r'documento\s+assinado\s+digitalmente\s+conforme\s+mp\s+n?[º°]?\s*2\.?200-2/2001',
                re.IGNORECASE,
            ),
            category="stj",
        ),
        CleaningPattern(
            description="QR Code STJ",
            regex=re.compile(
                r'valide\s+este\s+documento\s+via\s+qr\s+code', re.IGNORECASE
            ),
            category="stj",
        ),
        CleaningPattern(
            description="Cabeçalho STJ padrão",
            regex=re.compile(
                r'superior\s+tribunal\s+de\s+justi[çc]a\s*-\s*stj.*?'
                r'central\s+do\s+processo\s+eletr[ôo]nico',
                re.IGNORECASE | re.DOTALL,
            ),
            category="stj",
        ),
        CleaningPattern(
            description="Marca d'água STJ",
            regex=re.compile(
                r'\[logo\s+institucional\s+stj\]', re.IGNORECASE
            ),
            category="stj",
        ),
    ]

    # ==========================================================================
    # GENERIC_JUDICIAL - Padrões genéricos para sistemas não identificados
    # ==========================================================================

    GENERIC_JUDICIAL = [
        CleaningPattern(
            description="Assinatura digital genérica",
            regex=re.compile(
                r'assinado\s+digitalmente\s+por:?\s*[^\n]{5,100}',
                re.IGNORECASE,
            ),
            category="generic",
        ),
        CleaningPattern(
            description="Certificado digital genérico",
            regex=re.compile(
                r'certificado\s+digital:?\s*[^\n]{5,100}', re.IGNORECASE
            ),
            category="generic",
        ),
        CleaningPattern(
            description="Data/hora de assinatura genérica",
            regex=re.compile(
                r'data\s+da\s+assinatura:?\s*\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}(:\d{2})?',
                re.IGNORECASE,
            ),
            category="generic",
        ),
        CleaningPattern(
            description="URL de validação genérica",
            regex=re.compile(
                r'valide?\s+este\s+documento\s+em:?\s*https?://[^\s]+',
                re.IGNORECASE,
            ),
            category="generic",
        ),
    ]

    # ==========================================================================
    # UNIVERSAL - Padrões aplicados a TODOS os sistemas
    # ==========================================================================

    UNIVERSAL = [
        CleaningPattern(
            description="Serial number de certificado (hexadecimal longo)",
            regex=re.compile(r'serial\s+number:?\s*[0-9A-F]{16,}', re.IGNORECASE),
            category="universal",
        ),
        CleaningPattern(
            description="Hash SHA-1",
            regex=re.compile(r'sha-?1:?\s*[0-9A-F]{40}', re.IGNORECASE),
            category="universal",
        ),
        CleaningPattern(
            description="Hash SHA-256",
            regex=re.compile(r'sha-?256:?\s*[0-9A-F]{64}', re.IGNORECASE),
            category="universal",
        ),
        CleaningPattern(
            description="Autoridade Certificadora ICP-Brasil",
            regex=re.compile(r'ac\s+[a-z]+\s+-\s+icp-brasil', re.IGNORECASE),
            category="universal",
        ),
        CleaningPattern(
            description="Emissor de certificado",
            regex=re.compile(
                r'emissor:?\s*cn\s*=\s*ac\s+[^\n]{10,80}', re.IGNORECASE
            ),
            category="universal",
        ),
        CleaningPattern(
            description="Subject do certificado",
            regex=re.compile(
                r'subject:?\s*cn\s*=\s*[^\n]{10,80}cpf\s*=\s*\d{11}',
                re.IGNORECASE,
            ),
            category="universal",
        ),
        CleaningPattern(
            description="Validade do certificado",
            regex=re.compile(
                r'v[áa]lido\s+de:?\s*\d{2}/\d{2}/\d{4}\s+at[ée]:?\s*\d{2}/\d{2}/\d{4}',
                re.IGNORECASE,
            ),
            category="universal",
        ),
        CleaningPattern(
            description="Padrão PAdES/CAdES/XAdES",
            regex=re.compile(
                r'\b(pades|cades|xades)\s+(signature|assinatura)',
                re.IGNORECASE,
            ),
            category="universal",
        ),
        CleaningPattern(
            description="Referência ETSI TS 102 778",
            regex=re.compile(r'etsi\s+ts\s+102\s+778', re.IGNORECASE),
            category="universal",
        ),
        CleaningPattern(
            description="ITI - Instituto Nacional de Tecnologia da Informação",
            regex=re.compile(
                r'iti\s+-\s+instituto\s+nacional\s+de\s+tecnologia\s+da\s+informa[çc][ãa]o',
                re.IGNORECASE,
            ),
            category="universal",
        ),
        CleaningPattern(
            description="URL validador ITI",
            regex=re.compile(
                r'https?://(www\.)?validar\.iti\.gov\.br[^\s]*',
                re.IGNORECASE,
            ),
            category="universal",
        ),
        CleaningPattern(
            description="Timestamp RFC 3161",
            regex=re.compile(r'timestamp\s+rfc\s+3161', re.IGNORECASE),
            category="universal",
        ),
        CleaningPattern(
            description="Assinatura qualificada ICP-Brasil",
            regex=re.compile(
                r'assinatura\s+qualificada\s+icp-brasil', re.IGNORECASE
            ),
            category="universal",
        ),
        CleaningPattern(
            description="Linhas separadoras estéticas",
            regex=re.compile(r'^[_\-=*]{10,}$', re.MULTILINE),
            category="universal",
        ),
        CleaningPattern(
            description='Páginas numeradas isoladas (ex: "Página 1 de 10")',
            regex=re.compile(
                r'^p[áa]gina\s+\d+\s+(de|/)\s+\d+\s*$',
                re.IGNORECASE | re.MULTILINE,
            ),
            category="universal",
        ),
    ]

    @classmethod
    def get_patterns(cls, system: str) -> list[CleaningPattern]:
        """
        Retorna padrões para um sistema específico + universais.

        Args:
            system: Código do sistema (PJE, ESAJ, STF, STJ, EPROC, PROJUDI, GENERIC_JUDICIAL)

        Returns:
            Lista de CleaningPattern combinando padrões específicos + universais

        Example:
            >>> patterns = SystemPatterns.get_patterns("PJE")
            >>> len(patterns)  # 6 PJE + 15 UNIVERSAL
            21
        """
        system_upper = system.upper()

        # Get system-specific patterns
        system_patterns = getattr(cls, system_upper, cls.GENERIC_JUDICIAL)

        # Combine with universal patterns
        return system_patterns + cls.UNIVERSAL

    @classmethod
    def get_all_systems(cls) -> list[str]:
        """Retorna lista de todos os sistemas suportados"""
        return ["PJE", "ESAJ", "EPROC", "PROJUDI", "STF", "STJ", "GENERIC_JUDICIAL"]

    @classmethod
    def count_patterns(cls, system: str) -> dict[str, int]:
        """
        Conta padrões por sistema.

        Returns:
            Dict com contagem: {"system": N, "universal": M, "total": N+M}
        """
        system_patterns = getattr(cls, system.upper(), cls.GENERIC_JUDICIAL)
        return {
            "system": len(system_patterns),
            "universal": len(cls.UNIVERSAL),
            "total": len(system_patterns) + len(cls.UNIVERSAL),
        }
