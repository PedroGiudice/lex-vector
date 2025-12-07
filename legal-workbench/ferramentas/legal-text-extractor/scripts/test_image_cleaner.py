#!/usr/bin/env python3
"""
Testes unitários para ImageCleaner.

Gera imagens sintéticas e valida matematicamente que:
1. Marcas d'água cinza são removidas (pixels → 255)
2. Adaptive threshold funciona em imagens com gradiente
3. Carimbos coloridos são removidos
4. Speckles são removidos sem destruir pontuação

Execução:
    cd ferramentas/legal-text-extractor
    source .venv/bin/activate
    python scripts/test_image_cleaner.py
"""

import sys
from pathlib import Path

import numpy as np

# Adiciona o diretório raiz ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.image_cleaner import ImageCleaner, CleaningMode


def create_test_image_with_watermark() -> np.ndarray:
    """
    Cria imagem sintética: fundo branco, texto preto, marca d'água cinza.

    Layout:
    - Fundo: branco (255)
    - Retângulo superior: texto preto (0)
    - Traço diagonal: marca d'água cinza claro (210)
    """
    img = np.full((200, 300), 255, dtype=np.uint8)  # Fundo branco

    # "Texto" preto (retângulo)
    img[30:50, 50:250] = 0

    # "Marca d'água" cinza (traço diagonal)
    for i in range(100):
        y = 80 + i
        x = 50 + i * 2
        if y < 200 and x < 300:
            img[y, x : min(x + 10, 300)] = 210  # Cinza claro

    return img


def create_test_image_with_gradient() -> np.ndarray:
    """
    Cria imagem sintética: gradiente de fundo com texto.

    Simula scan com iluminação irregular.
    """
    # Gradiente de cinza (claro → escuro)
    gradient = np.linspace(200, 100, 300).astype(np.uint8)
    img = np.tile(gradient, (200, 1))

    # "Texto" preto sobre gradiente
    img[50:70, 50:250] = 0
    img[100:120, 50:250] = 0

    return img


def create_test_image_with_color_stamp() -> np.ndarray:
    """
    Cria imagem BGR sintética com carimbo azul.
    """
    img = np.full((200, 300, 3), 255, dtype=np.uint8)  # Fundo branco BGR

    # "Texto" preto
    img[30:50, 50:250] = [0, 0, 0]

    # "Carimbo" azul (BGR: azul = [255, 0, 0])
    img[80:120, 100:200] = [255, 100, 50]  # Azul com variação

    return img


def create_test_image_with_speckles() -> np.ndarray:
    """
    Cria imagem sintética com ruído pontual (speckles).
    """
    img = np.full((200, 300), 255, dtype=np.uint8)  # Fundo branco

    # "Texto" preto (retângulo grande)
    img[30:50, 50:250] = 0

    # Speckles aleatórios (pontos pretos isolados)
    np.random.seed(42)
    speckle_coords = np.random.randint(0, 200, size=(50, 2))
    for y, x in speckle_coords:
        if y < 200 and x < 300:
            img[y, x % 300] = 0  # Ponto preto isolado

    return img


def test_remove_gray_watermarks():
    """Testa remoção de marca d'água cinza."""
    print("=" * 60)
    print("TEST: remove_gray_watermarks")
    print("=" * 60)

    img = create_test_image_with_watermark()

    # Verifica que há pixels cinza antes da limpeza
    gray_pixels_before = np.sum((img > 100) & (img < 250))
    print(f"Pixels cinza antes: {gray_pixels_before}")
    assert gray_pixels_before > 0, "Imagem de teste deve ter pixels cinza"

    # Aplica limpeza
    cleaned = ImageCleaner.remove_gray_watermarks(img, threshold=200)

    # Verifica que pixels cinza claro (>200) foram convertidos para branco
    gray_pixels_after = np.sum((cleaned > 200) & (cleaned < 255))
    print(f"Pixels cinza (>200) após limpeza: {gray_pixels_after}")

    # Verifica que texto preto foi preservado
    black_pixels = np.sum(cleaned == 0)
    print(f"Pixels pretos preservados: {black_pixels}")
    assert black_pixels > 0, "Texto preto deve ser preservado"

    # Verifica que marca d'água (210) foi removida
    watermark_pixels = np.sum(cleaned == 210)
    print(f"Pixels de marca d'água (210): {watermark_pixels}")
    assert watermark_pixels == 0, "Marca d'água deve ser removida"

    print("✅ PASSED: Marca d'água cinza removida corretamente\n")


def test_clean_dirty_scan():
    """Testa adaptive threshold em scan com gradiente."""
    print("=" * 60)
    print("TEST: clean_dirty_scan")
    print("=" * 60)

    img = create_test_image_with_gradient()

    # Verifica que há variação de cinza antes
    unique_values_before = len(np.unique(img))
    print(f"Valores únicos antes: {unique_values_before}")
    assert unique_values_before > 10, "Imagem deve ter gradiente"

    # Aplica adaptive threshold
    cleaned = ImageCleaner.clean_dirty_scan(img, block_size=31, c=15)

    # Verifica que resultado é binarizado (apenas 0 e 255)
    unique_values_after = np.unique(cleaned)
    print(f"Valores únicos após: {unique_values_after}")
    assert len(unique_values_after) == 2, "Resultado deve ser binarizado"
    assert 0 in unique_values_after, "Deve ter pixels pretos"
    assert 255 in unique_values_after, "Deve ter pixels brancos"

    # Verifica que texto foi preservado (há pixels pretos)
    black_pixels = np.sum(cleaned == 0)
    print(f"Pixels pretos (texto): {black_pixels}")
    assert black_pixels > 0, "Texto deve ser preservado"

    print("✅ PASSED: Adaptive threshold funcionou corretamente\n")


def test_remove_color_stamps():
    """Testa remoção de carimbo colorido."""
    print("=" * 60)
    print("TEST: remove_color_stamps")
    print("=" * 60)

    img = create_test_image_with_color_stamp()

    # Verifica que há pixels azuis antes
    blue_channel = img[:, :, 0]
    blue_pixels_before = np.sum(blue_channel > 200)
    print(f"Pixels azuis antes: {blue_pixels_before}")

    # Aplica remoção de carimbo
    cleaned = ImageCleaner.remove_color_stamps(img)

    # Verifica que resultado é grayscale
    assert len(cleaned.shape) == 2, "Resultado deve ser grayscale"

    # Verifica que região do carimbo foi branqueada
    # O carimbo estava em img[80:120, 100:200]
    stamp_region = cleaned[80:120, 100:200]
    mean_stamp_region = np.mean(stamp_region)
    print(f"Média da região do carimbo: {mean_stamp_region:.1f}")
    assert mean_stamp_region > 200, "Região do carimbo deve ser clara (branqueada)"

    print("✅ PASSED: Carimbo colorido removido corretamente\n")


def test_remove_speckles():
    """Testa remoção de ruído pontual."""
    print("=" * 60)
    print("TEST: remove_speckles")
    print("=" * 60)

    img = create_test_image_with_speckles()

    # Conta pixels pretos antes
    black_before = np.sum(img == 0)
    print(f"Pixels pretos antes (texto + speckles): {black_before}")

    # Aplica despeckle
    cleaned = ImageCleaner.remove_speckles(img, kernel_size=3)

    # Conta pixels pretos depois
    black_after = np.sum(cleaned == 0)
    print(f"Pixels pretos após (apenas texto): {black_after}")

    # Speckles isolados devem ter sido removidos
    # mas texto (retângulo 20x200) deve permanecer
    expected_text_pixels = 20 * 200  # 4000 pixels
    print(f"Pixels de texto esperados: ~{expected_text_pixels}")

    # Verifica redução (speckles removidos)
    assert black_after < black_before, "Speckles devem ser removidos"

    # Verifica que texto foi preservado (margem de 50%)
    assert black_after > expected_text_pixels * 0.5, "Texto deve ser preservado"

    print("✅ PASSED: Speckles removidos, texto preservado\n")


def test_detect_mode():
    """Testa detecção automática de modo."""
    print("=" * 60)
    print("TEST: detect_mode")
    print("=" * 60)

    cleaner = ImageCleaner()

    # Imagem digital (bimodal: preto e branco)
    digital_img = np.full((200, 300, 3), 255, dtype=np.uint8)
    digital_img[50:100, 50:250] = [0, 0, 0]  # Texto preto
    mode_digital = cleaner.detect_mode(digital_img)
    print(f"Imagem digital detectada como: {mode_digital}")
    assert mode_digital == CleaningMode.DIGITAL, "Imagem bimodal deve ser DIGITAL"

    # Imagem scanned (gradiente/ruído)
    scanned_img = create_test_image_with_gradient()
    scanned_img_bgr = np.stack([scanned_img] * 3, axis=-1)
    mode_scanned = cleaner.detect_mode(scanned_img_bgr)
    print(f"Imagem com gradiente detectada como: {mode_scanned}")
    assert mode_scanned == CleaningMode.SCANNED, "Imagem com gradiente deve ser SCANNED"

    print("✅ PASSED: Detecção de modo funciona corretamente\n")


def test_process_image_integration():
    """Testa pipeline completo com PIL Image."""
    print("=" * 60)
    print("TEST: process_image (integration)")
    print("=" * 60)

    from PIL import Image

    cleaner = ImageCleaner()

    # Cria imagem PIL com marca d'água
    img_np = create_test_image_with_watermark()
    img_pil = Image.fromarray(img_np, mode="L")

    # Processa no modo digital
    result = cleaner.process_image(img_pil, mode="digital")

    # Verifica que retorna PIL Image
    assert isinstance(result, Image.Image), "Deve retornar PIL Image"

    # Verifica modo grayscale
    assert result.mode == "L", "Deve ser grayscale"

    # Converte para numpy e verifica limpeza
    result_np = np.array(result)
    watermark_pixels = np.sum(result_np == 210)
    print(f"Pixels de marca d'água após processamento: {watermark_pixels}")
    assert watermark_pixels == 0, "Marca d'água deve ser removida no pipeline"

    print("✅ PASSED: Pipeline de processamento funciona\n")


def run_all_tests():
    """Executa todos os testes."""
    print("\n" + "=" * 60)
    print("IMAGE CLEANER - TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        test_remove_gray_watermarks,
        test_clean_dirty_scan,
        test_remove_color_stamps,
        test_remove_speckles,
        test_detect_mode,
        test_process_image_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test.__name__}")
            print(f"   Exception: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
