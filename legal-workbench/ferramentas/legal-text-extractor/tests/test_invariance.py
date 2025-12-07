"""
Testes de Invariancia Multi-Sistema.

Valida o principio arquitetural fundamental:
"A mesma peticao protocolada em PJe, ESAJ, EPROC deve produzir classificacao IDENTICA"

Referencia: docs/ARCHITECTURE_PRINCIPLES.md
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pytest


# =============================================================================
# UTILIDADES DE NORMALIZACAO
# =============================================================================


def normalize_whitespace(text: str) -> str:
    """Normaliza whitespace para comparacao semantica."""
    # Remove multiplos espacos/tabs
    text = re.sub(r"[ \t]+", " ", text)
    # Remove espacos no inicio/fim de linhas
    text = re.sub(r" *\n *", "\n", text)
    # Remove linhas vazias multiplas
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_unicode(text: str) -> str:
    """Normaliza Unicode para NFKD (decomposto)."""
    return unicodedata.normalize("NFKD", text)


def semantic_normalize(text: str) -> str:
    """Normalizacao completa para comparacao semantica."""
    text = normalize_unicode(text)
    text = normalize_whitespace(text)
    return text


# =============================================================================
# SIMULACAO DE LIMPEZA DE ARTEFATOS
# (Baseado em src/core/patterns.py e src/schemas/validation_artifacts.json)
# =============================================================================


class ArtifactCleaner:
    """Remove artefatos de validacao de sistemas processuais."""

    # Padroes UNIVERSAIS (aplicados a todos os sistemas)
    UNIVERSAL_PATTERNS = [
        # Paginas numeradas
        r"^[Pp][aá]gina\s+\d+\s+(de|/)\s+\d+\s*$",
        # Linhas separadoras
        r"^[_\-=*]{10,}\s*$",
        # Serial numbers
        r"^[Ss]erial\s+[Nn]umber:?\s*[0-9A-Fa-f]{16,}\s*$",
        # Hashes
        r"^[Ss][Hh][Aa]-?1:?\s*[0-9A-Fa-f]{40}\s*$",
        r"^[Ss][Hh][Aa]-?256:?\s*[0-9A-Fa-f]{64}\s*$",
        # AC ICP-Brasil
        r"^[Aa][Cc]\s+\w+\s+-\s+[Ii][Cc][Pp]-[Bb]rasil\s*$",
    ]

    # Padroes PJE
    PJE_PATTERNS = [
        r"^_{10,}\s*[Pp]rocesso\s+[Jj]udicial\s+[Ee]letr[oô]nico\s*_{10,}\s*$",
        r"^INIC1\s*-\s*[Pp]eticao\s+[Ii]nicial\s*$",
        r"^\[QR\s+CODE\]\s*$",
        r"^[Cc][oó]digo\s+de\s+verifica[cç][aã]o:\s*[A-Z0-9]{4}\.[0-9]{4}\.[0-9A-Z]{4}\.[A-Z0-9]{4}\s*$",
        r"^[Ee]ste\s+documento\s+foi\s+gerado\s+pelo\s+usu[aá]rio.*$",
        r"^[Dd]ocumento\s+assinado\s+por\s+.{5,100}\s+e\s+certificado\s+digitalmente.*$",
        r"^[Vv]alide\s+em:\s*https?://pje\.[^\s]+\s*$",
    ]

    # Padroes ESAJ
    ESAJ_PATTERNS = [
        r"^TRIBUNAL\s+DE\s+JUSTI[CÇ]A\s+DO\s+ESTADO\s+DE\s+S[AÃ]O\s+PAULO\s*-\s*TJSP\s*$",
        r"^[Cc][oó]digo\s+do\s+documento:\s*[A-Z0-9]{8,20}\s*$",
        r"^fls\.\s*\d+(/\d+)?\s*$",
        r"^[Aa]ssinado\s+digitalmente\s+por:\s*.{5,80}\s+[Dd]ata:\s*\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s*$",
        r"^[Cc]onfer[eê]ncia\s+de\s+documento\s+digital.*portal\s+e-[Ss][Aa][Jj]\s*$",
        r"^https?://esaj\.[^\s]+\s*$",
        r"^[Rr]esolu[cç][aã]o\s+n?[º°o]?\s*552/11.*$",
    ]

    # Padroes EPROC
    EPROC_PATTERNS = [
        r"^[Mm]ov\.\s*\d+.*$",
        r"^[Aa]ssinado\s+eletronicamente\s+por\s+.{5,100},?\s*certificado\s+digital\s+[Ii][Cc][Pp]-[Bb]rasil\s*$",
        r"^[Vv]erificador\s+de\s+[Cc]onformidade\s+[Ii][Tt][Ii]\s*$",
        r"^[Aa]ssinatura\s+digital\s+dispon[ií]vel\s+em:\s*[^\n]*\.p7s\s*$",
        r"^https?://eproc\.[^\s]+\s*$",
        r"^[Bb]yte[Rr]ange\s*\[\s*\d+\s+\d+\s+\d+\s+\d+\s*\]\s*$",
    ]

    @classmethod
    def get_patterns(cls, system: str) -> list[str]:
        """Retorna padroes para um sistema + universais."""
        system = system.upper()
        patterns = cls.UNIVERSAL_PATTERNS.copy()

        if system == "PJE":
            patterns.extend(cls.PJE_PATTERNS)
        elif system == "ESAJ":
            patterns.extend(cls.ESAJ_PATTERNS)
        elif system == "EPROC":
            patterns.extend(cls.EPROC_PATTERNS)

        return patterns

    @classmethod
    def clean(cls, text: str, system: str) -> str:
        """Remove artefatos de um sistema especifico."""
        patterns = cls.get_patterns(system)

        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

        # Normaliza whitespace resultante
        return semantic_normalize(text)


# =============================================================================
# FIXTURES
# =============================================================================


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "invariance"


def get_fixture_path(category: str, filename: str) -> Path:
    """Retorna caminho para um arquivo de fixture."""
    return FIXTURES_DIR / category / filename


def load_fixture(category: str, filename: str) -> str:
    """Carrega conteudo de uma fixture."""
    path = get_fixture_path(category, filename)
    if not path.exists():
        pytest.skip(f"Fixture nao encontrada: {path}")
    return path.read_text(encoding="utf-8")


# =============================================================================
# TESTES DE INVARIANCIA
# =============================================================================


class TestInvariancePeticaoInicial:
    """Testes de invariancia para Peticao Inicial."""

    CATEGORY = "peticao_inicial"
    SYSTEMS = ["pje", "esaj", "eproc"]

    def test_fixtures_exist(self):
        """Verifica se todas as fixtures existem."""
        assert get_fixture_path(self.CATEGORY, "texto_base.txt").exists()
        for system in self.SYSTEMS:
            path = get_fixture_path(self.CATEGORY, f"com_artefatos_{system}.txt")
            assert path.exists(), f"Fixture faltando: {path}"

    def test_texto_base_nao_vazio(self):
        """Texto base deve ter conteudo."""
        texto = load_fixture(self.CATEGORY, "texto_base.txt")
        assert len(texto) > 100, "Texto base muito curto"

    def test_artefatos_presentes_nos_arquivos(self):
        """Arquivos com artefatos devem ter marcadores de sistema."""
        markers = {
            "pje": ["INIC1", "Processo Judicial Eletronico", "verificacao"],
            "esaj": ["TJSP", "fls.", "e-SAJ"],
            "eproc": ["Mov.", "ITI", "ICP-Brasil"],
        }

        for system in self.SYSTEMS:
            texto = load_fixture(self.CATEGORY, f"com_artefatos_{system}.txt")
            for marker in markers[system]:
                assert marker.lower() in texto.lower(), (
                    f"Marcador '{marker}' nao encontrado em {system}"
                )

    def test_limpeza_remove_artefatos(self):
        """Limpeza deve remover artefatos especificos do sistema."""
        for system in self.SYSTEMS:
            texto_com_artefatos = load_fixture(
                self.CATEGORY, f"com_artefatos_{system}.txt"
            )
            texto_limpo = ArtifactCleaner.clean(texto_com_artefatos, system)

            # Nao deve conter artefatos apos limpeza
            assert "INIC1" not in texto_limpo
            assert "verificacao" not in texto_limpo.lower() or system != "pje"
            assert "fls." not in texto_limpo or system != "esaj"
            assert "Mov." not in texto_limpo or system != "eproc"

    def test_invariancia_semantica(self):
        """
        TESTE PRINCIPAL: Texto limpo deve ser semanticamente igual ao texto base.

        Este teste valida o principio arquitetural fundamental:
        "Mesma peticao em sistemas diferentes -> classificacao identica"
        """
        texto_base = load_fixture(self.CATEGORY, "texto_base.txt")
        texto_base_normalizado = semantic_normalize(texto_base)

        for system in self.SYSTEMS:
            texto_com_artefatos = load_fixture(
                self.CATEGORY, f"com_artefatos_{system}.txt"
            )
            texto_limpo = ArtifactCleaner.clean(texto_com_artefatos, system)

            # Compara semanticamente
            assert texto_limpo == texto_base_normalizado, (
                f"Texto limpo de {system} difere do texto base!\n"
                f"Tamanho base: {len(texto_base_normalizado)}\n"
                f"Tamanho limpo: {len(texto_limpo)}"
            )

    def test_invariancia_entre_sistemas(self):
        """Textos limpos de diferentes sistemas devem ser identicos entre si."""
        textos_limpos = {}

        for system in self.SYSTEMS:
            texto_com_artefatos = load_fixture(
                self.CATEGORY, f"com_artefatos_{system}.txt"
            )
            textos_limpos[system] = ArtifactCleaner.clean(texto_com_artefatos, system)

        # Compara todos os pares
        sistemas = list(textos_limpos.keys())
        for i, s1 in enumerate(sistemas):
            for s2 in sistemas[i + 1 :]:
                assert textos_limpos[s1] == textos_limpos[s2], (
                    f"Textos limpos de {s1} e {s2} diferem!"
                )

    def test_conteudo_semantico_preservado(self):
        """Conteudo semantico importante deve estar presente apos limpeza."""
        termos_essenciais = [
            "EXCELENTISSIMO SENHOR",
            "ACAO DE COBRANCA",
            "DOS FATOS",
            "DO DIREITO",
            "DO PEDIDO",
            "Nestes termos",
            "Pede deferimento",
            "OAB/SP",
        ]

        for system in self.SYSTEMS:
            texto_com_artefatos = load_fixture(
                self.CATEGORY, f"com_artefatos_{system}.txt"
            )
            texto_limpo = ArtifactCleaner.clean(texto_com_artefatos, system)

            for termo in termos_essenciais:
                assert termo.upper() in texto_limpo.upper(), (
                    f"Termo '{termo}' perdido apos limpeza em {system}"
                )


# =============================================================================
# TESTES DE NORMALIZACAO
# =============================================================================


class TestNormalizacao:
    """Testes para funcoes de normalizacao."""

    def test_normalize_whitespace_espacos_multiplos(self):
        """Remove espacos multiplos."""
        assert normalize_whitespace("a    b") == "a b"

    def test_normalize_whitespace_tabs(self):
        """Converte tabs para espacos."""
        assert normalize_whitespace("a\t\tb") == "a b"

    def test_normalize_whitespace_linhas_vazias(self):
        """Limita linhas vazias a 2."""
        assert normalize_whitespace("a\n\n\n\nb") == "a\n\nb"

    def test_semantic_normalize_completo(self):
        """Normalizacao semantica completa."""
        texto = "  a    b  \n\n\n\n  c  "
        resultado = semantic_normalize(texto)
        assert resultado == "a b\n\nc"


# =============================================================================
# RUNNER
# =============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
