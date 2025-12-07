"""
ImageCleaner - Pre-processamento de imagens para OCR de documentos jurídicos.

Algoritmos vetorizados (Numpy/OpenCV) para limpeza de:
1. Documentos digitais (PJe): Marcas d'água cinza sobre texto preto
2. Documentos escaneados: Manchas, amarelamento, carimbos, speckles

Stack: opencv-python-headless, numpy, PIL
Constraint: Zero GUI (cv2.imshow proibido), execução em servidor/WSL

Author: Pedro Giudice
Date: 2025-11-25
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

import cv2
import numpy as np
from PIL import Image


class CleaningMode(str, Enum):
    """Modos de limpeza disponíveis."""

    AUTO = "auto"  # Detecta automaticamente baseado em histograma
    DIGITAL = "digital"  # Otimizado para PDFs digitais com marca d'água
    SCANNED = "scanned"  # Otimizado para scans com manchas/carimbos


@dataclass
class CleaningOptions:
    """
    Opções de configuração para o ImageCleaner.

    Permite customização granular dos algoritmos de limpeza.
    Use valores padrão para a maioria dos casos.

    Example:
        >>> options = CleaningOptions(
        ...     mode=CleaningMode.DIGITAL,
        ...     watermark_threshold=190,  # Mais agressivo
        ...     despeckle_kernel=5,       # Maior suavização
        ... )
        >>> cleaner = ImageCleaner.from_options(options)
    """

    # Modo de limpeza
    mode: CleaningMode = CleaningMode.AUTO

    # Threshold para remoção de marca d'água (0-255)
    # Pixels > threshold são convertidos para branco
    # Menor = mais agressivo (remove mais cinza)
    watermark_threshold: int = 200

    # Adaptive threshold settings
    # block_size: Tamanho da vizinhança (deve ser ímpar)
    # c: Constante subtraída da média
    adaptive_block_size: int = 31
    adaptive_c: int = 15

    # Kernel para despeckle (deve ser ímpar)
    # Maior = mais suavização (pode perder detalhes)
    despeckle_kernel: int = 3

    # Iterações de dilatação para máscaras de carimbo
    # Mais iterações = captura mais borda do carimbo
    stamp_dilate_iterations: int = 2

    # Ranges HSV customizados para carimbos
    # Se None, usa cores padrão (azul, vermelho, verde)
    custom_stamp_colors: list[tuple[np.ndarray, np.ndarray]] | None = None

    def __post_init__(self):
        """Valida parâmetros."""
        if not 0 <= self.watermark_threshold <= 255:
            raise ValueError("watermark_threshold deve ser 0-255")
        if self.adaptive_block_size % 2 == 0:
            self.adaptive_block_size += 1
        if self.despeckle_kernel % 2 == 0:
            self.despeckle_kernel += 1


# Presets comuns
PRESET_DIGITAL_AGGRESSIVE = CleaningOptions(
    mode=CleaningMode.DIGITAL,
    watermark_threshold=180,  # Remove mais cinza
    despeckle_kernel=3,
)

PRESET_SCANNED_CONSERVATIVE = CleaningOptions(
    mode=CleaningMode.SCANNED,
    watermark_threshold=210,  # Preserva mais detalhes
    adaptive_c=10,  # Menos agressivo
    despeckle_kernel=3,
)

PRESET_OCR_OPTIMIZED = CleaningOptions(
    mode=CleaningMode.AUTO,
    watermark_threshold=200,
    adaptive_block_size=21,  # Menor bloco para texto pequeno
    adaptive_c=12,
    despeckle_kernel=3,
)


# Ranges HSV padrão para carimbos comuns em documentos judiciais brasileiros
DEFAULT_STAMP_COLORS: list[tuple[np.ndarray, np.ndarray]] = [
    # Azul (carimbos azuis comuns)
    (np.array([100, 50, 50]), np.array([130, 255, 255])),
    # Vermelho (parte 1: H=0-10)
    (np.array([0, 50, 50]), np.array([10, 255, 255])),
    # Vermelho (parte 2: H=170-180)
    (np.array([170, 50, 50]), np.array([180, 255, 255])),
    # Verde (carimbos verdes menos comuns)
    (np.array([35, 50, 50]), np.array([85, 255, 255])),
]


class ImageCleaner:
    """
    Cleaner de imagens para pré-processamento de OCR.

    Métodos principais:
    - remove_gray_watermarks(): Remove marcas d'água cinza (documentos digitais)
    - clean_dirty_scan(): Limpa scans com iluminação irregular (adaptive threshold)
    - remove_color_stamps(): Remove carimbos coloridos (HSV segmentation)
    - remove_speckles(): Remove ruído pontual (morphological opening)
    - process_image(): Orquestrador inteligente (auto-detecção de modo)

    Example:
        >>> cleaner = ImageCleaner()
        >>> img = Image.open("scan.png")
        >>> cleaned = cleaner.process_image(img, mode="scanned")
        >>> cleaned.save("cleaned.png")
    """

    def __init__(
        self,
        watermark_threshold: int = 200,
        adaptive_block_size: int = 31,
        adaptive_c: int = 15,
        despeckle_kernel_size: int = 3,
        stamp_colors: list[tuple[np.ndarray, np.ndarray]] | None = None,
    ):
        """
        Inicializa o cleaner com parâmetros configuráveis.

        Args:
            watermark_threshold: Limiar para remoção de cinza (0-255). Default 200.
                Pixels > threshold são convertidos para branco.
            adaptive_block_size: Tamanho do bloco para adaptive threshold. Deve ser ímpar.
            adaptive_c: Constante subtraída da média no adaptive threshold.
            despeckle_kernel_size: Tamanho do kernel para morphological opening.
                3x3 é recomendado para preservar pontuação.
            stamp_colors: Lista de ranges HSV [(lower, upper), ...] para carimbos.
                Se None, usa DEFAULT_STAMP_COLORS.
        """
        self.watermark_threshold = watermark_threshold
        self.adaptive_block_size = adaptive_block_size
        self.adaptive_c = adaptive_c
        self.despeckle_kernel_size = despeckle_kernel_size
        self.stamp_colors = stamp_colors or DEFAULT_STAMP_COLORS

    @classmethod
    def from_options(cls, options: CleaningOptions) -> "ImageCleaner":
        """
        Cria ImageCleaner a partir de CleaningOptions.

        Args:
            options: Instância de CleaningOptions

        Returns:
            ImageCleaner configurado

        Example:
            >>> opts = CleaningOptions(watermark_threshold=180)
            >>> cleaner = ImageCleaner.from_options(opts)
        """
        return cls(
            watermark_threshold=options.watermark_threshold,
            adaptive_block_size=options.adaptive_block_size,
            adaptive_c=options.adaptive_c,
            despeckle_kernel_size=options.despeckle_kernel,
            stamp_colors=options.custom_stamp_colors,
        )

    @staticmethod
    def remove_gray_watermarks(
        image: np.ndarray, threshold: int = 200
    ) -> np.ndarray:
        """
        Remove marcas d'água cinza claro de documentos digitais.

        Algoritmo: Threshold global simples.
        - Texto jurídico legítimo é preto (#000000)
        - Marcas d'água digitais são cinza claro (geralmente > #C0C0C0 = 192)
        - Pixels com valor > threshold são convertidos para branco (255)

        Args:
            image: Imagem em grayscale (np.ndarray uint8, shape HxW)
            threshold: Limiar de cinza (0-255). Pixels > threshold → 255.

        Returns:
            Imagem limpa (grayscale np.ndarray)

        Example:
            >>> img = cv2.imread("digital.png", cv2.IMREAD_GRAYSCALE)
            >>> clean = ImageCleaner.remove_gray_watermarks(img, threshold=200)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Vetorização numpy: muito mais rápido que loops
        result = image.copy()
        result[result > threshold] = 255
        return result

    @staticmethod
    def clean_dirty_scan(
        image: np.ndarray, block_size: int = 31, c: int = 15
    ) -> np.ndarray:
        """
        Limpa scans com iluminação irregular usando adaptive threshold.

        Algoritmo: Gaussian Adaptive Threshold.
        - Scans antigos têm variação de brilho (papel amarelado, sombras)
        - Threshold global falha: apaga texto em áreas claras, deixa ruído em escuras
        - Adaptive calcula limiar local baseado em vizinhança

        Args:
            image: Imagem em grayscale (np.ndarray uint8, shape HxW)
            block_size: Tamanho da vizinhança para cálculo do threshold. Deve ser ímpar.
            c: Constante subtraída da média ponderada.

        Returns:
            Imagem binarizada (grayscale np.ndarray, apenas 0 e 255)

        Example:
            >>> img = cv2.imread("old_scan.png", cv2.IMREAD_GRAYSCALE)
            >>> clean = ImageCleaner.clean_dirty_scan(img, block_size=31, c=15)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Garante block_size ímpar
        if block_size % 2 == 0:
            block_size += 1

        # Adaptive threshold usando média Gaussiana
        result = cv2.adaptiveThreshold(
            image,
            maxValue=255,
            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            thresholdType=cv2.THRESH_BINARY,
            blockSize=block_size,
            C=c,
        )

        return result

    @staticmethod
    def remove_color_stamps(
        image: np.ndarray,
        color_ranges: Sequence[tuple[np.ndarray, np.ndarray]] | None = None,
    ) -> np.ndarray:
        """
        Remove carimbos coloridos via segmentação HSV.

        Algoritmo: Color-based segmentation.
        1. Converte BGR → HSV (mais robusto a iluminação)
        2. Cria máscara para cada cor alvo usando cv2.inRange
        3. Dilata máscara para capturar bordas borradas
        4. Pinta região da máscara de branco
        5. Retorna em grayscale

        Args:
            image: Imagem BGR (np.ndarray uint8, shape HxWx3)
            color_ranges: Lista de tuplas (lower_hsv, upper_hsv) para cada cor.
                Se None, usa ranges padrão para carimbos azuis/vermelhos/verdes.

        Returns:
            Imagem grayscale com carimbos removidos (np.ndarray uint8, shape HxW)

        Example:
            >>> img = cv2.imread("with_stamp.png")  # BGR
            >>> clean = ImageCleaner.remove_color_stamps(img)
        """
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError("Input deve ser BGR (3D array com 3 canais)")

        if color_ranges is None:
            color_ranges = DEFAULT_STAMP_COLORS

        # Converte BGR → HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Cria máscara combinada para todas as cores
        combined_mask = np.zeros(image.shape[:2], dtype=np.uint8)

        for lower, upper in color_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, mask)

        # Dilata para pegar bordas borradas dos carimbos
        kernel = np.ones((5, 5), np.uint8)
        dilated_mask = cv2.dilate(combined_mask, kernel, iterations=2)

        # Pinta regiões mascaradas de branco na imagem original
        result = image.copy()
        result[dilated_mask > 0] = [255, 255, 255]

        # Converte para grayscale
        result_gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)

        return result_gray

    @staticmethod
    def remove_speckles(
        image: np.ndarray, kernel_size: int = 3
    ) -> np.ndarray:
        """
        Remove ruído pontual (speckles) usando median filter.

        Algoritmo: Median Filter.
        - Substitui cada pixel pela mediana da vizinhança
        - Eficaz para ruído "salt-and-pepper" (pontos pretos/brancos isolados)
        - Preserva bordas melhor que blur gaussiano
        - Kernel 3x3 remove speckles sem destruir pontuação

        Args:
            image: Imagem grayscale ou binarizada (np.ndarray uint8)
            kernel_size: Tamanho do kernel (3 recomendado). Deve ser ímpar.

        Returns:
            Imagem despeckled (np.ndarray uint8)

        Example:
            >>> img = cv2.imread("noisy.png", cv2.IMREAD_GRAYSCALE)
            >>> clean = ImageCleaner.remove_speckles(img, kernel_size=3)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Garante kernel_size ímpar
        if kernel_size % 2 == 0:
            kernel_size += 1

        # Median filter - eficaz para salt-and-pepper noise
        result = cv2.medianBlur(image, kernel_size)

        return result

    @staticmethod
    def has_speckle_noise(image: np.ndarray, threshold: float = 0.02) -> bool:
        """
        Detecta se imagem tem ruído salt-and-pepper (speckles).

        Heurística: Em áreas majoritariamente brancas (>200),
        speckles aparecem como pixels escuros isolados.
        Calcula a proporção de pixels escuros em áreas brancas.

        Args:
            image: Grayscale image (np.ndarray uint8, shape HxW)
            threshold: Se proporção de ruído > threshold, retorna True.
                       Default 0.02 = 2% de ruído em áreas brancas.

        Returns:
            True se detectar speckles significativos

        Example:
            >>> img = cv2.imread("scan.png", cv2.IMREAD_GRAYSCALE)
            >>> if ImageCleaner.has_speckle_noise(img):
            ...     img = ImageCleaner.remove_speckles(img)
        """
        if len(image.shape) != 2:
            raise ValueError("Input deve ser grayscale (2D array)")

        # Cria máscara de áreas brancas
        white_mask = image > 200

        # Se não há área branca suficiente, não faz sentido analisar
        if white_mask.sum() < image.size * 0.3:
            return False

        # Dentro das áreas "brancas", conta pixels escuros (ruído)
        # Speckles são pixels < 150 em áreas que deveriam ser brancas
        noise_in_white = (image < 150) & white_mask
        noise_ratio = noise_in_white.sum() / white_mask.sum()

        return noise_ratio > threshold

    def detect_mode(self, image: np.ndarray) -> CleaningMode:
        """
        Detecta automaticamente o melhor modo de limpeza.

        Heurística baseada em análise de histograma:
        1. Documentos digitais têm distribuição bimodal limpa (preto + branco)
        2. Scans têm distribuição mais espalhada (cinzas, manchas)
        3. Presença de cores fortes indica carimbos

        Args:
            image: Imagem BGR ou grayscale

        Returns:
            CleaningMode.DIGITAL ou CleaningMode.SCANNED
        """
        # Converte para grayscale se necessário
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Calcula histograma
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()

        # Normaliza
        hist_norm = hist / hist.sum()

        # Métricas de distribuição
        # 1. Concentração nos extremos (0-50 e 200-255)
        dark_mass = hist_norm[:50].sum()
        light_mass = hist_norm[200:].sum()
        extreme_ratio = dark_mass + light_mass

        # 2. Spread no meio (50-200) = ruído/manchas
        mid_mass = hist_norm[50:200].sum()

        # Heurística:
        # - Digital: extremos > 80%, meio < 20%
        # - Scanned: meio > 20%
        if extreme_ratio > 0.8 and mid_mass < 0.2:
            return CleaningMode.DIGITAL
        else:
            return CleaningMode.SCANNED

    def process_image(
        self,
        image_pil: Image.Image,
        mode: str | CleaningMode = "auto",
    ) -> Image.Image:
        """
        Orquestrador principal - processa imagem com pipeline apropriado.

        Pipelines:
        - DIGITAL: remove_gray_watermarks → (opcional) remove_speckles
        - SCANNED: remove_color_stamps → clean_dirty_scan → remove_speckles
        - AUTO: detect_mode() → pipeline correspondente

        Args:
            image_pil: Imagem PIL (RGB ou grayscale)
            mode: "auto", "digital", ou "scanned"

        Returns:
            Imagem PIL processada (grayscale)

        Example:
            >>> cleaner = ImageCleaner()
            >>> img = Image.open("document.png")
            >>> clean = cleaner.process_image(img, mode="auto")
            >>> clean.save("clean.png")
        """
        # Converte PIL → Numpy (OpenCV usa BGR, PIL usa RGB)
        img_np = np.array(image_pil)

        # Se grayscale, converte para 3 canais para processamento uniforme
        if len(img_np.shape) == 2:
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
        else:
            # PIL RGB → OpenCV BGR
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # Determina modo
        if isinstance(mode, str):
            mode = CleaningMode(mode.lower())

        if mode == CleaningMode.AUTO:
            mode = self.detect_mode(img_bgr)

        # Converte para grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # Aplica pipeline baseado no modo
        if mode == CleaningMode.DIGITAL:
            # Pipeline digital: remove marca d'água cinza
            result = self.remove_gray_watermarks(gray, self.watermark_threshold)
            # Despeckle condicional - só aplica se detectar ruído real
            # (evita degradar texto preto em documentos digitais limpos)
            if self.has_speckle_noise(result):
                result = self.remove_speckles(result, self.despeckle_kernel_size)

        else:  # SCANNED
            # Pipeline scanned: remove carimbos → adaptive threshold → despeckle
            result = self.remove_color_stamps(img_bgr, self.stamp_colors)
            result = self.clean_dirty_scan(
                result, self.adaptive_block_size, self.adaptive_c
            )
            result = self.remove_speckles(result, self.despeckle_kernel_size)

        # Converte de volta para PIL
        result_pil = Image.fromarray(result, mode="L")  # L = grayscale

        return result_pil


# Singleton para uso conveniente
_cleaner: ImageCleaner | None = None


def get_image_cleaner(**kwargs) -> ImageCleaner:
    """
    Obtém instância singleton do ImageCleaner.

    Args:
        **kwargs: Argumentos passados para ImageCleaner() na primeira chamada.

    Returns:
        Instância de ImageCleaner
    """
    global _cleaner
    if _cleaner is None:
        _cleaner = ImageCleaner(**kwargs)
    return _cleaner
