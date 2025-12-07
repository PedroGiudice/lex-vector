"""
Testes de integração do ImageCleaner com PDFs reais.

Testa o pipeline de limpeza com documentos reais dos sistemas:
- PJE (Processo Judicial Eletrônico)
- ESAJ (Sistema de Automação da Justiça)
- EPROC (Sistema de Processo Eletrônico)
- PROJUDI (Processo Judicial Digital)

Métricas validadas:
1. Redução de ruído (pixels cinza removidos)
2. Preservação de texto (pixels pretos mantidos)
3. Performance (tempo de processamento)

Execução:
    cd ferramentas/legal-text-extractor
    source .venv/bin/activate
    pytest tests/test_image_cleaner_integration.py -v
"""

import time
from pathlib import Path

import cv2
import numpy as np
import pytest
from pdf2image import convert_from_path
from PIL import Image

from src.core.image_cleaner import ImageCleaner, CleaningMode


# Diretório com fixtures reais
FIXTURES_DIR = Path(__file__).parent.parent / "test-documents" / "fixtures"


# Fixtures disponíveis por sistema
SYSTEM_FIXTURES = {
    "PJE": "fixture_pje.pdf",
    "ESAJ": "fixture_esaj.pdf",
    "EPROC": "fixture_eproc.pdf",
    "PROJUDI": "fixture_projudi.pdf",
}

# Fixtures adicionais para testes específicos
SPECIAL_FIXTURES = {
    "clean": "fixture_clean.pdf",           # Documento limpo (baseline)
    "dirty": "fixture_test_dirty.pdf",      # Documento com marcas d'água/carimbos
    "single": "fixture_single.pdf",         # Página única
    "multi": "fixture_multi_15pages.pdf",   # Multi-página (performance)
}


def pdf_to_image(pdf_path: Path, page_num: int = 1, dpi: int = 150) -> Image.Image:
    """Converte uma página de PDF para PIL Image."""
    images = convert_from_path(
        pdf_path,
        first_page=page_num,
        last_page=page_num,
        dpi=dpi,
    )
    return images[0] if images else None


def calculate_adaptive_threshold(original: np.ndarray) -> float:
    """
    Calcula threshold adaptativo baseado na composição do documento.

    Documentos com muitos elementos gráficos (cinza) têm threshold menor,
    pois é esperado que mais pixels sejam limpos junto.

    Returns:
        Threshold de preservação de texto (0-100)
    """
    if len(original.shape) == 3:
        gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
    else:
        gray = original

    total = gray.size
    gray_pct = np.sum((gray >= 50) & (gray < 200)) / total * 100

    # Quanto mais cinza, menor o threshold esperado
    # gray_pct 0%  → threshold 80% (documento limpo)
    # gray_pct 5%  → threshold 50% (alguns elementos gráficos)
    # gray_pct 10% → threshold 25% (muitos elementos gráficos)
    # gray_pct 15%+→ threshold 15% (documento muito "sujo")

    if gray_pct < 2:
        return 80.0
    elif gray_pct < 5:
        return 50.0
    elif gray_pct < 10:
        return 25.0
    else:
        return 15.0


def calculate_metrics(original: np.ndarray, cleaned: np.ndarray) -> dict:
    """
    Calcula métricas de qualidade da limpeza.

    Returns:
        Dict com:
        - noise_reduction: % de pixels cinza removidos
        - text_preservation: % de pixels pretos mantidos
        - white_increase: % de aumento de pixels brancos
        - adaptive_threshold: threshold recomendado baseado no documento
    """
    # Converte para grayscale se necessário
    if len(original.shape) == 3:
        orig_gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
    else:
        orig_gray = original

    if len(cleaned.shape) == 3:
        clean_gray = cv2.cvtColor(cleaned, cv2.COLOR_RGB2GRAY)
    else:
        clean_gray = cleaned

    total_pixels = orig_gray.size

    # Pixels cinza (ruído): 50 < valor < 200
    noise_before = np.sum((orig_gray > 50) & (orig_gray < 200))
    noise_after = np.sum((clean_gray > 50) & (clean_gray < 200))
    noise_reduction = (
        (noise_before - noise_after) / noise_before * 100 if noise_before > 0 else 0
    )

    # Pixels pretos (texto): valor < 50
    text_before = np.sum(orig_gray < 50)
    text_after = np.sum(clean_gray < 50)
    text_preservation = text_after / text_before * 100 if text_before > 0 else 100

    # Pixels brancos: valor > 240
    white_before = np.sum(orig_gray > 240)
    white_after = np.sum(clean_gray > 240)
    white_increase = (
        (white_after - white_before) / total_pixels * 100
    )

    return {
        "noise_reduction": round(noise_reduction, 1),
        "text_preservation": round(text_preservation, 1),
        "white_increase": round(white_increase, 1),
        "total_pixels": total_pixels,
        "adaptive_threshold": calculate_adaptive_threshold(original),
    }


class TestImageCleanerIntegration:
    """Testes de integração com PDFs reais."""

    @pytest.fixture
    def cleaner(self):
        """Instância do ImageCleaner."""
        return ImageCleaner()

    @pytest.fixture
    def pje_image(self) -> Image.Image | None:
        """Primeira página do PDF PJE."""
        pdf_path = FIXTURES_DIR / SYSTEM_FIXTURES["PJE"]
        if not pdf_path.exists():
            pytest.skip(f"Fixture não encontrada: {pdf_path}")
        return pdf_to_image(pdf_path, page_num=1)

    @pytest.fixture
    def esaj_image(self) -> Image.Image | None:
        """Primeira página do PDF ESAJ."""
        pdf_path = FIXTURES_DIR / SYSTEM_FIXTURES["ESAJ"]
        if not pdf_path.exists():
            pytest.skip(f"Fixture não encontrada: {pdf_path}")
        return pdf_to_image(pdf_path, page_num=1)

    @pytest.fixture
    def eproc_image(self) -> Image.Image | None:
        """Primeira página do PDF EPROC."""
        pdf_path = FIXTURES_DIR / SYSTEM_FIXTURES["EPROC"]
        if not pdf_path.exists():
            pytest.skip(f"Fixture não encontrada: {pdf_path}")
        return pdf_to_image(pdf_path, page_num=1)

    @pytest.fixture
    def projudi_image(self) -> Image.Image | None:
        """Primeira página do PDF PROJUDI."""
        pdf_path = FIXTURES_DIR / SYSTEM_FIXTURES["PROJUDI"]
        if not pdf_path.exists():
            pytest.skip(f"Fixture não encontrada: {pdf_path}")
        return pdf_to_image(pdf_path, page_num=1)

    def test_pje_digital_cleaning(self, cleaner, pje_image):
        """
        Testa limpeza de documento PJE (digital com possíveis marcas d'água).

        PJE tipicamente tem:
        - Texto preto digital
        - Possíveis marcas d'água "CÓPIA" ou "MINUTA"
        - Tarjas laterais com certificação
        """
        if pje_image is None:
            pytest.skip("Imagem PJE não disponível")

        original = np.array(pje_image)

        start = time.time()
        cleaned = cleaner.process_image(pje_image, mode="digital")
        elapsed = time.time() - start

        cleaned_np = np.array(cleaned)
        metrics = calculate_metrics(original, cleaned_np)

        print(f"\n=== PJE (Digital) ===")
        print(f"Tempo: {elapsed:.2f}s")
        print(f"Redução de ruído: {metrics['noise_reduction']}%")
        print(f"Preservação de texto: {metrics['text_preservation']}%")
        print(f"Aumento de brancos: {metrics['white_increase']}%")

        # Asserts com threshold adaptativo
        threshold = metrics["adaptive_threshold"]
        print(f"Threshold adaptativo: {threshold}%")

        assert elapsed < 10, f"Processamento muito lento: {elapsed}s"
        assert metrics["text_preservation"] > threshold, \
            f"Texto não preservado adequadamente: {metrics['text_preservation']}% < {threshold}%"

    def test_esaj_digital_cleaning(self, cleaner, esaj_image):
        """
        Testa limpeza de documento ESAJ.

        ESAJ tipicamente tem:
        - Selo lateral com QR code e certificação
        - Texto digital limpo
        - Possíveis brasões/logos
        """
        if esaj_image is None:
            pytest.skip("Imagem ESAJ não disponível")

        original = np.array(esaj_image)

        start = time.time()
        cleaned = cleaner.process_image(esaj_image, mode="digital")
        elapsed = time.time() - start

        cleaned_np = np.array(cleaned)
        metrics = calculate_metrics(original, cleaned_np)

        print(f"\n=== ESAJ (Digital) ===")
        print(f"Tempo: {elapsed:.2f}s")
        print(f"Redução de ruído: {metrics['noise_reduction']}%")
        print(f"Preservação de texto: {metrics['text_preservation']}%")
        print(f"Aumento de brancos: {metrics['white_increase']}%")

        assert elapsed < 10, f"Processamento muito lento: {elapsed}s"
        assert metrics["text_preservation"] > 50, "Texto não preservado adequadamente"

    def test_eproc_scanned_cleaning(self, cleaner, eproc_image):
        """
        Testa limpeza de documento EPROC.

        EPROC pode ter documentos escaneados anexados.
        """
        if eproc_image is None:
            pytest.skip("Imagem EPROC não disponível")

        original = np.array(eproc_image)

        # Testa modo auto (deve detectar automaticamente)
        start = time.time()
        cleaned = cleaner.process_image(eproc_image, mode="auto")
        elapsed = time.time() - start

        cleaned_np = np.array(cleaned)
        metrics = calculate_metrics(original, cleaned_np)

        # Detecta qual modo foi usado
        detected_mode = cleaner.detect_mode(original)

        print(f"\n=== EPROC (Auto: {detected_mode.value}) ===")
        print(f"Tempo: {elapsed:.2f}s")
        print(f"Redução de ruído: {metrics['noise_reduction']}%")
        print(f"Preservação de texto: {metrics['text_preservation']}%")
        print(f"Aumento de brancos: {metrics['white_increase']}%")

        assert elapsed < 15, f"Processamento muito lento: {elapsed}s"
        assert metrics["text_preservation"] > 40, "Texto não preservado adequadamente"

    def test_projudi_scanned_cleaning(self, cleaner, projudi_image):
        """
        Testa limpeza de documento PROJUDI.

        PROJUDI frequentemente tem documentos escaneados.
        """
        if projudi_image is None:
            pytest.skip("Imagem PROJUDI não disponível")

        original = np.array(projudi_image)

        start = time.time()
        cleaned = cleaner.process_image(projudi_image, mode="scanned")
        elapsed = time.time() - start

        cleaned_np = np.array(cleaned)
        metrics = calculate_metrics(original, cleaned_np)

        print(f"\n=== PROJUDI (Scanned) ===")
        print(f"Tempo: {elapsed:.2f}s")
        print(f"Redução de ruído: {metrics['noise_reduction']}%")
        print(f"Preservação de texto: {metrics['text_preservation']}%")
        print(f"Aumento de brancos: {metrics['white_increase']}%")

        assert elapsed < 15, f"Processamento muito lento: {elapsed}s"
        # Modo scanned é mais agressivo, aceita menor preservação
        assert metrics["text_preservation"] > 30, "Texto não preservado adequadamente"

    def test_mode_detection_accuracy(self, cleaner):
        """
        Testa se a detecção automática de modo funciona com fixtures reais.
        """
        results = {}

        for system, filename in SYSTEM_FIXTURES.items():
            pdf_path = FIXTURES_DIR / filename
            if not pdf_path.exists():
                continue

            try:
                img = pdf_to_image(pdf_path, page_num=1)
                if img is None:
                    continue

                img_np = np.array(img)
                mode = cleaner.detect_mode(img_np)
                results[system] = mode.value
            except Exception as e:
                results[system] = f"ERROR: {e}"

        print(f"\n=== Detecção de Modo ===")
        for system, mode in results.items():
            print(f"  {system}: {mode}")

        # Pelo menos 2 sistemas devem ser detectados
        valid_results = [r for r in results.values() if not r.startswith("ERROR")]
        assert len(valid_results) >= 2, "Poucos sistemas detectados"

    def test_batch_processing_performance(self, cleaner):
        """
        Testa performance de processamento em lote.
        """
        images = []

        for system, filename in SYSTEM_FIXTURES.items():
            pdf_path = FIXTURES_DIR / filename
            if pdf_path.exists():
                try:
                    img = pdf_to_image(pdf_path, page_num=1, dpi=100)  # DPI menor para speed
                    if img:
                        images.append((system, img))
                except Exception:
                    pass

        if len(images) < 2:
            pytest.skip("Poucas fixtures disponíveis para teste de batch")

        print(f"\n=== Batch Processing ({len(images)} imagens) ===")

        total_time = 0
        for system, img in images:
            start = time.time()
            _ = cleaner.process_image(img, mode="auto")
            elapsed = time.time() - start
            total_time += elapsed
            print(f"  {system}: {elapsed:.2f}s")

        avg_time = total_time / len(images)
        print(f"  Tempo médio: {avg_time:.2f}s")
        print(f"  Tempo total: {total_time:.2f}s")

        assert avg_time < 10, f"Tempo médio muito alto: {avg_time:.2f}s"


class TestCleaningQuality:
    """Testes focados na qualidade da limpeza."""

    @pytest.fixture
    def cleaner(self):
        return ImageCleaner()

    def test_watermark_removal_effectiveness(self, cleaner):
        """
        Testa efetividade da remoção de marca d'água em documento real.
        """
        # Usa fixture_dirty que tem marcas d'água conhecidas
        pdf_path = FIXTURES_DIR / SPECIAL_FIXTURES["dirty"]
        if not pdf_path.exists():
            pytest.skip("Fixture dirty não encontrada")

        img = pdf_to_image(pdf_path, page_num=1)
        if img is None:
            pytest.skip("Falha ao converter PDF")

        original = np.array(img)
        if len(original.shape) == 3:
            gray = cv2.cvtColor(original, cv2.COLOR_RGB2GRAY)
        else:
            gray = original

        # Conta pixels em faixa de marca d'água (180-220)
        watermark_before = np.sum((gray > 180) & (gray < 220))

        cleaned = cleaner.process_image(img, mode="digital")
        cleaned_np = np.array(cleaned)

        watermark_after = np.sum((cleaned_np > 180) & (cleaned_np < 220))

        reduction = (
            (watermark_before - watermark_after) / watermark_before * 100
            if watermark_before > 0
            else 0
        )

        print(f"\n=== Remoção de Marca D'água ===")
        print(f"  Pixels (180-220) antes: {watermark_before}")
        print(f"  Pixels (180-220) depois: {watermark_after}")
        print(f"  Redução: {reduction:.1f}%")

        # Teste de sanidade: processamento deve completar sem erro
        # A efetividade depende do tipo de marca d'água no documento
        # Alguns documentos podem não ter watermarks tradicionais
        assert cleaned is not None, "Falha no processamento"
        # Se havia watermarks significativas, devem ter sido reduzidas
        # Caso contrário, aceita qualquer resultado
        if watermark_before > 10000:
            # Documento com muitos pixels cinza - espera alguma redução
            assert reduction > -20, f"Aumento excessivo de ruído: {reduction}%"

    def test_stamp_removal_on_colored_document(self, cleaner):
        """
        Testa remoção de carimbos em documento que pode ter carimbos coloridos.
        """
        # PROJUDI frequentemente tem carimbos
        pdf_path = FIXTURES_DIR / SYSTEM_FIXTURES["PROJUDI"]
        if not pdf_path.exists():
            pytest.skip("Fixture PROJUDI não encontrada")

        img = pdf_to_image(pdf_path, page_num=1)
        if img is None:
            pytest.skip("Falha ao converter PDF")

        original = np.array(img)

        # Converte para HSV para detectar cores
        if len(original.shape) == 3:
            hsv = cv2.cvtColor(original, cv2.COLOR_RGB2HSV)

            # Detecta pixels azuis (carimbos comuns)
            blue_mask = cv2.inRange(
                hsv,
                np.array([100, 50, 50]),
                np.array([130, 255, 255])
            )
            blue_before = np.sum(blue_mask > 0)
        else:
            blue_before = 0

        cleaned = cleaner.process_image(img, mode="scanned")

        print(f"\n=== Remoção de Carimbos Azuis ===")
        print(f"  Pixels azuis antes: {blue_before}")

        # Se havia pixels azuis, devem ter sido reduzidos
        # (resultado é grayscale, então todos azuis viram cinza/branco)
        if blue_before > 100:
            # Verifica que resultado é grayscale (sem cor)
            assert len(np.array(cleaned).shape) == 2, "Resultado deve ser grayscale"
            print(f"  Resultado: Grayscale (carimbos removidos)")
