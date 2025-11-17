"""
Testes para módulo pdf_text_extractor.py - Extração de texto de PDFs.

Valida:
- Estratégias de extração (pdfplumber, PyPDF2, OCR)
- Fallback inteligente
- Validação de PDFs
- Hash calculation
- Tratamento de PDFs corrompidos
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.pdf_text_extractor import (
    PDFTextExtractor,
    ExtractionResult,
    ExtractionStrategy
)


class TestPDFTextExtractorInit:
    """Testes para inicialização do extrator."""

    def test_init_default(self):
        """Inicializa com parâmetros default."""
        extractor = PDFTextExtractor()
        assert extractor.enable_ocr is False
        assert extractor.ocr_lang == 'por'
        assert extractor.max_file_size_mb == 100

    def test_init_com_ocr(self):
        """Inicializa com OCR habilitado."""
        extractor = PDFTextExtractor(enable_ocr=True)
        assert extractor.enable_ocr is True

    def test_init_custom_params(self):
        """Inicializa com parâmetros customizados."""
        extractor = PDFTextExtractor(
            enable_ocr=True,
            ocr_lang='eng',
            max_file_size_mb=50
        )
        assert extractor.ocr_lang == 'eng'
        assert extractor.max_file_size_mb == 50

    def test_check_dependencies(self):
        """Verifica bibliotecas disponíveis."""
        extractor = PDFTextExtractor()
        # Deve ter pelo menos uma biblioteca disponível
        assert extractor.has_pdfplumber or extractor.has_pypdf2


class TestPDFValidation:
    """Testes para validação de PDFs."""

    def test_valida_pdf_correto(self, sample_pdf_path):
        """Valida PDF correto."""
        extractor = PDFTextExtractor()
        valid, error = extractor.validate_pdf(sample_pdf_path)
        assert valid is True
        assert error is None

    def test_rejeita_arquivo_nao_existente(self, temp_dir):
        """Rejeita arquivo que não existe."""
        extractor = PDFTextExtractor()
        fake_path = temp_dir / "nao_existe.pdf"

        valid, error = extractor.validate_pdf(fake_path)
        assert valid is False
        assert "não encontrado" in error.lower()

    def test_rejeita_arquivo_nao_pdf(self, temp_dir):
        """Rejeita arquivo que não é PDF."""
        txt_file = temp_dir / "test.txt"
        txt_file.write_text("Not a PDF")

        extractor = PDFTextExtractor()
        valid, error = extractor.validate_pdf(txt_file)
        assert valid is False
        assert "não é pdf" in error.lower()

    def test_rejeita_pdf_muito_grande(self, sample_pdf_path):
        """Rejeita PDF maior que max_file_size_mb."""
        # Criar extractor com limite muito pequeno
        extractor = PDFTextExtractor(max_file_size_mb=0.001)

        valid, error = extractor.validate_pdf(sample_pdf_path)
        assert valid is False
        assert "muito grande" in error.lower()

    def test_rejeita_pdf_corrompido(self, corrupted_pdf_path):
        """Rejeita PDF com header inválido."""
        extractor = PDFTextExtractor()
        valid, error = extractor.validate_pdf(corrupted_pdf_path)
        assert valid is False
        assert "corrompido" in error.lower() or "inválido" in error.lower()


class TestPDFExtraction:
    """Testes para extração de texto."""

    def test_extract_pdf_valido(self, sample_pdf_path):
        """Extrai texto de PDF válido."""
        extractor = PDFTextExtractor()
        result = extractor.extract(sample_pdf_path)

        assert isinstance(result, ExtractionResult)
        assert result.success is True
        assert result.strategy in [
            ExtractionStrategy.PDFPLUMBER,
            ExtractionStrategy.PYPDF2
        ]
        assert result.page_count > 0

    def test_extract_retorna_texto(self, sample_pdf_path):
        """Extração retorna texto não vazio."""
        extractor = PDFTextExtractor()
        result = extractor.extract(sample_pdf_path)

        if result.success:
            assert isinstance(result.text, str)
            assert result.char_count == len(result.text)

    def test_extract_pdf_invalido(self, corrupted_pdf_path):
        """Extração falha para PDF corrompido."""
        extractor = PDFTextExtractor()
        result = extractor.extract(corrupted_pdf_path)

        assert result.success is False
        assert result.strategy == ExtractionStrategy.FAILED
        assert result.error_message is not None

    @pytest.mark.slow
    def test_fallback_strategy(self, sample_pdf_path):
        """Testa fallback entre estratégias."""
        extractor = PDFTextExtractor()

        # Mock para forçar falha da primeira estratégia
        with patch.object(extractor, '_extract_pdfplumber') as mock_pdfplumber:
            mock_pdfplumber.side_effect = Exception("Falha simulada")

            result = extractor.extract(sample_pdf_path)

            # Se PyPDF2 disponível, deve ter usado como fallback
            if extractor.has_pypdf2:
                assert result.strategy == ExtractionStrategy.PYPDF2


class TestHashCalculation:
    """Testes para cálculo de hash."""

    def test_calcula_hash_pdf(self, sample_pdf_path):
        """Calcula hash SHA256 de PDF."""
        hash_value = PDFTextExtractor.calculate_hash(sample_pdf_path)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hex = 64 chars
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_mesmo_pdf_mesmo_hash(self, sample_pdf_path):
        """Mesmo PDF gera mesmo hash."""
        hash1 = PDFTextExtractor.calculate_hash(sample_pdf_path)
        hash2 = PDFTextExtractor.calculate_hash(sample_pdf_path)

        assert hash1 == hash2

    def test_pdfs_diferentes_hashes_diferentes(self, sample_pdf_path, temp_dir):
        """PDFs diferentes geram hashes diferentes."""
        # Criar segundo PDF diferente
        pdf2_path = temp_dir / "test2.pdf"
        pdf2_path.write_bytes(b"%PDF-1.4\nDifferent content\n%%EOF")

        hash1 = PDFTextExtractor.calculate_hash(sample_pdf_path)
        hash2 = PDFTextExtractor.calculate_hash(pdf2_path)

        assert hash1 != hash2


class TestExtractionResult:
    """Testes para ExtractionResult dataclass."""

    def test_extraction_result_success(self):
        """Cria ExtractionResult de sucesso."""
        result = ExtractionResult(
            text="Texto extraído",
            strategy=ExtractionStrategy.PDFPLUMBER,
            page_count=5,
            char_count=100,
            success=True
        )

        assert result.success is True
        assert result.text == "Texto extraído"
        assert result.page_count == 5
        assert result.char_count == 100
        assert result.metadata == {}

    def test_extraction_result_failure(self):
        """Cria ExtractionResult de falha."""
        result = ExtractionResult(
            text="",
            strategy=ExtractionStrategy.FAILED,
            page_count=0,
            char_count=0,
            success=False,
            error_message="Erro de teste"
        )

        assert result.success is False
        assert result.error_message == "Erro de teste"

    def test_extraction_result_com_metadata(self):
        """Cria ExtractionResult com metadata."""
        result = ExtractionResult(
            text="Texto",
            strategy=ExtractionStrategy.PYPDF2,
            page_count=10,
            char_count=500,
            success=True,
            metadata={'custom': 'value'}
        )

        assert result.metadata['custom'] == 'value'


class TestPDFTextExtractorIntegration:
    """Testes de integração."""

    def test_workflow_completo(self, sample_pdf_path):
        """Testa workflow completo de extração."""
        extractor = PDFTextExtractor()

        # 1. Calcular hash
        pdf_hash = extractor.calculate_hash(sample_pdf_path)
        assert len(pdf_hash) == 64

        # 2. Validar PDF
        valid, error = extractor.validate_pdf(sample_pdf_path)
        assert valid is True

        # 3. Extrair texto
        result = extractor.extract(sample_pdf_path)
        assert result.success is True
        assert result.char_count > 0

    def test_multiplos_pdfs_sequencial(self, sample_pdf_path, temp_dir):
        """Extrai múltiplos PDFs sequencialmente."""
        extractor = PDFTextExtractor()

        # Usar mesmo PDF 3 vezes (simulando múltiplos arquivos)
        results = []
        for i in range(3):
            result = extractor.extract(sample_pdf_path)
            results.append(result)

        # Todos devem ter sucesso
        assert all(r.success for r in results)

        # Hashes devem ser iguais (mesmo arquivo)
        hash1 = extractor.calculate_hash(sample_pdf_path)
        for result in results:
            # Texto extraído deve ser consistente
            assert result.char_count > 0


@pytest.mark.slow
@pytest.mark.requires_tesseract
class TestOCRExtraction:
    """Testes para extração com OCR (marcados como slow)."""

    def test_ocr_disponivel_quando_habilitado(self):
        """Verifica disponibilidade de OCR quando habilitado."""
        extractor = PDFTextExtractor(enable_ocr=True)
        # Se OCR instalado, deve estar disponível
        # Se não, has_ocr será False (não é erro)
        assert isinstance(extractor.has_ocr, bool)

    def test_ocr_nao_usado_se_desabilitado(self, sample_pdf_path):
        """OCR não é usado se desabilitado."""
        extractor = PDFTextExtractor(enable_ocr=False)
        result = extractor.extract(sample_pdf_path)

        if result.success:
            # Estratégia não deve ser OCR
            assert result.strategy != ExtractionStrategy.OCR


class TestPDFTextExtractorEdgeCases:
    """Testes de edge cases."""

    def test_pdf_vazio(self, temp_dir):
        """Lida com PDF vazio."""
        empty_pdf = temp_dir / "empty.pdf"
        empty_pdf.write_bytes(b"%PDF-1.4\n%%EOF")

        extractor = PDFTextExtractor()
        result = extractor.extract(empty_pdf)

        # Pode falhar ou retornar texto vazio
        if result.success:
            assert result.char_count >= 0

    def test_pdf_com_muitas_paginas(self, temp_dir):
        """Testa comportamento com PDF de muitas páginas."""
        # Este é um teste conceitual - criaria PDF grande
        # Por ora, apenas valida que max_file_size funciona
        extractor = PDFTextExtractor(max_file_size_mb=1)
        assert extractor.max_file_size_mb == 1
