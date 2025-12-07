"""
Adaptive Cleaning Engine - Content-aware text cleaning for Brazilian judicial systems.

Uses fingerprint detection to identify the source system (PJE, ESAJ, EPROC, etc.)
and applies weighted cleaning rules accordingly.
"""

import re
from dataclasses import dataclass, field
from typing import Pattern

@dataclass
class SystemProfile:
    """Profile for a judicial system with fingerprints and cleaning rules."""
    name: str
    fingerprints: list[Pattern] = field(default_factory=list)
    cleaning_rules: list[Pattern] = field(default_factory=list)
    weight: float = 1.0  # Boost factor when this system is detected

@dataclass
class DetectionResult:
    """Result of system detection."""
    system: str
    confidence: float
    hits: int
    total_fingerprints: int

class CleanerEngine:
    """
    Adaptive text cleaner that detects judicial system and applies appropriate rules.

    Workflow:
    1. detect_system() - Scan text for fingerprints, return system + confidence
    2. clean() - Apply rules based on detected system with weighting
    """

    CONFIDENCE_THRESHOLD = 0.3  # Below this, only universal patterns

    def __init__(self):
        self.profiles: dict[str, SystemProfile] = {}
        self.universal_patterns: list[Pattern] = []
        self._setup_profiles()
        self._setup_universal()

    def _setup_profiles(self):
        """Initialize system profiles with fingerprints and cleaning rules."""
        # PJE Profile
        self.profiles["PJE"] = SystemProfile(
            name="PJE",
            fingerprints=[
                re.compile(r'processo\s+judicial\s+eletr[ôo]nico', re.I),
                re.compile(r'pje\.(trt|trf|tjsp|cnj)', re.I),
                re.compile(r'c[óo]digo\s+de\s+verifica[çc][ãa]o:\s*[A-Z0-9]{4}\.[0-9]{4}', re.I),
            ],
            cleaning_rules=[
                re.compile(r'c[óo]digo\s+de\s+verifica[çc][ãa]o:\s*[A-Z0-9]{4}\.[0-9]{4}\.[0-9A-Z]{4}\.[A-Z0-9]{4}', re.I),
                re.compile(r'este\s+documento\s+foi\s+gerado\s+pelo\s+usu[áa]rio.*?\d{2}:\d{2}:\d{2}', re.I | re.DOTALL),
                re.compile(r'documento\s+assinado\s+por\s+[^\n]{5,100}\s+e\s+certificado\s+digitalmente', re.I),
                re.compile(r'^[_\-=]+\s*processo\s+judicial\s+eletr[ôo]nico\s*[_\-=]+$', re.I | re.M),
            ],
            weight=1.5
        )

        # ESAJ Profile
        self.profiles["ESAJ"] = SystemProfile(
            name="ESAJ",
            fingerprints=[
                re.compile(r'e-?saj', re.I),
                re.compile(r'tjsp\.jus\.br', re.I),
                re.compile(r'tribunal\s+de\s+justi[çc]a.*?s[ãa]o\s+paulo', re.I),
            ],
            cleaning_rules=[
                re.compile(r'c[óo]digo\s+do\s+documento:\s*[A-Z0-9]{8,20}', re.I),
                re.compile(r'confer[êe]ncia\s+de\s+documento\s+digital.*?portal\s+e-saj', re.I | re.DOTALL),
                re.compile(r'assinado\s+digitalmente\s+por:\s*[^\n]{5,80}\s+data:\s*\d{2}/\d{2}/\d{4}', re.I),
                re.compile(r'resolu[çc][ãa]o\s+n?[º°]?\s*552/11', re.I),
            ],
            weight=1.5
        )

        # EPROC Profile
        self.profiles["EPROC"] = SystemProfile(
            name="EPROC",
            fingerprints=[
                re.compile(r'eproc', re.I),
                re.compile(r'trf\d\.jus\.br', re.I),
                re.compile(r'assinatura\s+digital\s+dispon[ií]vel\s+em:.*?\.p7s', re.I),
            ],
            cleaning_rules=[
                re.compile(r'assinatura\s+digital\s+dispon[ií]vel\s+em:\s*[^\n]*\.p7s', re.I),
                re.compile(r'verificador\s+de\s+conformidade\s+(iti|icp-brasil)', re.I),
                re.compile(r'assinado\s+eletronicamente\s+por.*?certificado\s+digital\s+icp-brasil', re.I | re.DOTALL),
                re.compile(r'byterange\s*\[\s*\d+\s+\d+\s+\d+\s+\d+\s*\]', re.I),
            ],
            weight=1.5
        )

        # PROJUDI Profile
        self.profiles["PROJUDI"] = SystemProfile(
            name="PROJUDI",
            fingerprints=[
                re.compile(r'projudi', re.I),
                re.compile(r'digitalmente\s+assinado\s+por', re.I),
            ],
            cleaning_rules=[
                re.compile(r'digitalmente\s+assinado\s+por.*?data:\s*\d{2}/\d{2}/\d{4}', re.I | re.DOTALL),
                re.compile(r'projudi\s+-\s+vers[ãa]o\s+\d+\.\d+', re.I),
                re.compile(r'assinador\s+livre\s+(tjrj|tribunal)', re.I),
            ],
            weight=1.5
        )

        # STF Profile
        self.profiles["STF"] = SystemProfile(
            name="STF",
            fingerprints=[
                re.compile(r'stf\.jus\.br', re.I),
                re.compile(r'supremo\s+tribunal\s+federal', re.I),
            ],
            cleaning_rules=[
                re.compile(r'cpf\s+do\s+consulente:\s*\d{3}\.\d{3}\.\d{3}-\d{2}', re.I),
                re.compile(r'documento\s+processado\s+pelo\s+projeto\s+victor', re.I),
                re.compile(r'resolu[çc][ãa]o\s+stf\s+n?[º°]?\s*693/2020', re.I),
            ],
            weight=1.5
        )

        # STJ Profile
        self.profiles["STJ"] = SystemProfile(
            name="STJ",
            fingerprints=[
                re.compile(r'stj\.jus\.br', re.I),
                re.compile(r'superior\s+tribunal\s+de\s+justi[çc]a', re.I),
            ],
            cleaning_rules=[
                re.compile(r'c[óo]digo:\s*[A-Z0-9]{16,32}', re.I),
                re.compile(r'autentique\s+em:\s*https?://(www\.)?stj\.jus\.br', re.I),
                re.compile(r'assinado\s+por:\s*[^\n]{5,80}\s+-\s+cpf:\s*\d{3}\.\d{3}\.\d{3}-\d{2}', re.I),
                re.compile(r'valide\s+este\s+documento\s+via\s+qr\s+code', re.I),
            ],
            weight=1.5
        )

    def _setup_universal(self):
        """Universal patterns applied regardless of detected system."""
        self.universal_patterns = [
            # Page numbers
            re.compile(r'p[áa]gina\s+\d+\s+de\s+\d+', re.I),
            re.compile(r'fls?\.\s*\d+', re.I),

            # Common certification text
            re.compile(r'documento\s+assinado\s+digitalmente\s+conforme\s+mp\s+n?[º°]?\s*2\.?200-2/2001', re.I),
            re.compile(r'icp-?brasil', re.I),

            # URLs (with and without protocol)
            re.compile(r'https?://[^\s]+\.jus\.br[^\s]*', re.I),
            re.compile(r'[a-z]+\.[a-z]+\.jus\.br\S*', re.I),  # pje.tjsp.jus.br...

            # Validation URLs and fragments (tarja lateral)
            re.compile(r'^/validar\s*$', re.I | re.M),  # isolated /validar line
            re.compile(r'validar\s+documento', re.I),

            # Validation codes (generic)
            re.compile(r'c[óo]digo\s+de\s+verifica[çc][ãa]o[:\s]+[A-Z0-9\.\-]+', re.I),
            re.compile(r'valide?\s+em[:\s]+', re.I),

            # Isolated CPF in tarja context
            re.compile(r'^CPF:\s*\d{3}\.\d{3}\.\d{3}-\d{2}\s*$', re.I | re.M),

            # Signature blocks
            re.compile(r'assinado\s+por[:\s]+[^\n]{5,80}', re.I),
            re.compile(r'certificado[:\s]+[A-Z0-9\-]+', re.I),
            re.compile(r'hash\s+(sha-?256|md5)[:\s]+[a-f0-9]+', re.I),

            # Timestamps (full and isolated)
            re.compile(r'data/hora[:\s]+\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}(:\d{2})?', re.I),
            re.compile(r'^Da\s*t[aL]/H[oO]r[aA][:\s,]*$', re.I | re.M),  # corrupted "Data/Hora" from OCR
            re.compile(r'^\d{2}/\d{2}/\d{4}\s*$', re.M),  # isolated date line
            re.compile(r'^\d{2}:\d{2}(:\d{2})?\s*$', re.M),  # isolated time line

            # Hex codes (tarja verification codes)
            re.compile(r'^[0-9a-f]{12,32}\s*$', re.I | re.M),  # isolated hex code
        ]

    def detect_system(self, text: str) -> DetectionResult:
        """
        Detect judicial system from text using fingerprint matching.

        Returns DetectionResult with system name, confidence score (0.0-1.0),
        number of hits, and total fingerprints checked.
        """
        scores: dict[str, int] = {}
        total_fingerprints = 0

        for name, profile in self.profiles.items():
            hits = 0
            for fp in profile.fingerprints:
                if fp.search(text):
                    hits += 1
            scores[name] = hits
            total_fingerprints += len(profile.fingerprints)

        # Find best match
        if not scores or max(scores.values()) == 0:
            return DetectionResult(
                system="UNKNOWN",
                confidence=0.0,
                hits=0,
                total_fingerprints=total_fingerprints
            )

        best_system = max(scores, key=scores.get)
        best_hits = scores[best_system]

        # Calculate confidence based on hits vs total fingerprints for that system
        profile = self.profiles[best_system]
        confidence = best_hits / len(profile.fingerprints) if profile.fingerprints else 0.0

        return DetectionResult(
            system=best_system,
            confidence=min(confidence, 1.0),
            hits=best_hits,
            total_fingerprints=len(profile.fingerprints)
        )

    def clean(self, text: str, force_system: str | None = None) -> str:
        """
        Clean text by removing judicial system artifacts.

        Args:
            text: Input text to clean
            force_system: If provided, skip detection and use this system

        Returns:
            Cleaned text with artifacts removed
        """
        if force_system and force_system in self.profiles:
            detection = DetectionResult(
                system=force_system,
                confidence=1.0,
                hits=0,
                total_fingerprints=0
            )
        else:
            detection = self.detect_system(text)

        cleaned = text

        # Apply system-specific rules if confidence is high enough
        if detection.confidence >= self.CONFIDENCE_THRESHOLD:
            profile = self.profiles.get(detection.system)
            if profile:
                for rule in profile.cleaning_rules:
                    cleaned = rule.sub('', cleaned)

        # Always apply universal patterns
        for pattern in self.universal_patterns:
            cleaned = pattern.sub('', cleaned)

        # Clean up multiple newlines and whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        cleaned = cleaned.strip()

        return cleaned


# Singleton instance for easy import
_engine: CleanerEngine | None = None

def get_cleaner() -> CleanerEngine:
    """Get or create singleton CleanerEngine instance."""
    global _engine
    if _engine is None:
        _engine = CleanerEngine()
    return _engine
