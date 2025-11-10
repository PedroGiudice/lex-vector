"""
agentes/legal-rag/config/embeddings_models.py

Configuração de modelos de embeddings com fallbacks.
Otimizado para textos jurídicos brasileiros.
"""

from typing import Literal, Optional, TYPE_CHECKING
from dataclasses import dataclass
import logging

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Tipos de modelos suportados
EmbeddingModel = Literal[
    "bge-m3",           # Multilingual, 8192 tokens, 1024 dim
    "bge-large-pt",     # Português específico, 512 tokens, 1024 dim
    "bertimbau-large",  # Melhor pt-br (neuralmind), 512 tokens, 1024 dim
    "labse",            # Multilingual Google, 512 tokens, 768 dim
    "paraphrase-xlm",   # Sentence-BERT multilingual, 128 tokens, 768 dim
]


@dataclass
class EmbeddingConfig:
    """Configuração de modelo de embedding."""

    model_name: EmbeddingModel
    model_path: str
    max_seq_length: int
    embedding_dim: int
    normalize: bool
    device: str = "cuda"  # ou "cpu"

    # Performance tuning
    batch_size: int = 32
    show_progress: bool = True

    def __post_init__(self):
        """Validação pós-inicialização."""
        if self.device not in ["cuda", "cpu", "auto"]:
            raise ValueError(f"Device inválido: {self.device}. Use 'cuda', 'cpu' ou 'auto'")

        if self.max_seq_length <= 0:
            raise ValueError("max_seq_length deve ser > 0")

        if self.embedding_dim <= 0:
            raise ValueError("embedding_dim deve ser > 0")


# Modelos recomendados por caso de uso
EMBEDDING_CONFIGS = {
    # Produção: melhor trade-off precisão/performance
    "production": EmbeddingConfig(
        model_name="bge-m3",
        model_path="BAAI/bge-m3",
        max_seq_length=8192,
        embedding_dim=1024,
        normalize=True,
        batch_size=32
    ),

    # Português específico: máxima precisão para pt-br
    "portuguese": EmbeddingConfig(
        model_name="bertimbau-large",
        model_path="neuralmind/bert-large-portuguese-cased",
        max_seq_length=512,
        embedding_dim=1024,
        normalize=True,
        batch_size=16  # Modelo maior, batch menor
    ),

    # Rápido: para prototipagem e testes
    "fast": EmbeddingConfig(
        model_name="paraphrase-xlm",
        model_path="sentence-transformers/paraphrase-xlm-r-multilingual-v1",
        max_seq_length=128,
        embedding_dim=768,
        normalize=True,
        batch_size=64
    ),

    # BGE Large PT: balanço entre velocidade e qualidade
    "balanced": EmbeddingConfig(
        model_name="bge-large-pt",
        model_path="BAAI/bge-large-pt",
        max_seq_length=512,
        embedding_dim=1024,
        normalize=True,
        batch_size=32
    ),

    # LaBSE: multilingual da Google
    "multilingual": EmbeddingConfig(
        model_name="labse",
        model_path="sentence-transformers/LaBSE",
        max_seq_length=512,
        embedding_dim=768,
        normalize=True,
        batch_size=32
    )
}


def get_embedding_model(
    config_name: str = "production",
    device: str = "auto",
    model_kwargs: Optional[dict] = None
) -> "SentenceTransformer":
    """
    Factory para modelos de embedding.

    Args:
        config_name: Nome da configuração (production/portuguese/fast/balanced/multilingual)
        device: "cuda", "cpu", ou "auto" (detecta automaticamente)
        model_kwargs: Kwargs adicionais para SentenceTransformer

    Returns:
        Modelo SentenceTransformer configurado

    Raises:
        ValueError: Se config_name inválido
        ImportError: Se sentence-transformers não instalado

    Example:
        >>> model = get_embedding_model("production", device="cuda")
        >>> embeddings = model.encode(["texto 1", "texto 2"])
        >>> embeddings.shape
        (2, 1024)
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers não instalado. "
            "Execute: pip install sentence-transformers"
        )

    # Validar config_name
    if config_name not in EMBEDDING_CONFIGS:
        available = ", ".join(EMBEDDING_CONFIGS.keys())
        raise ValueError(
            f"Configuração '{config_name}' inválida. "
            f"Disponíveis: {available}"
        )

    config = EMBEDDING_CONFIGS[config_name]

    # Auto-detectar device
    if device == "auto":
        device = _detect_device()

    config.device = device

    # Model kwargs padrão
    default_model_kwargs = {
        "device": device
    }

    if model_kwargs:
        default_model_kwargs.update(model_kwargs)

    logger.info(
        f"Carregando modelo de embeddings: {config.model_path} "
        f"(device={device}, dim={config.embedding_dim})"
    )

    try:
        model = SentenceTransformer(
            config.model_path,
            device=device,
            **default_model_kwargs
        )

        # Configurar max_seq_length
        model.max_seq_length = config.max_seq_length

        logger.info(
            f"Modelo carregado com sucesso. "
            f"Max sequence length: {model.max_seq_length}"
        )

        return model

    except Exception as e:
        logger.error(f"Erro ao carregar modelo {config.model_path}: {e}")
        raise


def _detect_device() -> str:
    """
    Detecta automaticamente device disponível.

    Returns:
        "cuda" se GPU disponível, "cpu" caso contrário
    """
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"GPU detectada: {gpu_name}")
        else:
            device = "cpu"
            logger.info("GPU não disponível, usando CPU")
        return device
    except ImportError:
        logger.warning("PyTorch não instalado, usando CPU")
        return "cpu"


def get_embedding_config(config_name: str) -> EmbeddingConfig:
    """
    Retorna configuração de embedding sem carregar modelo.

    Args:
        config_name: Nome da configuração

    Returns:
        EmbeddingConfig

    Raises:
        ValueError: Se config_name inválido
    """
    if config_name not in EMBEDDING_CONFIGS:
        available = ", ".join(EMBEDDING_CONFIGS.keys())
        raise ValueError(
            f"Configuração '{config_name}' inválida. "
            f"Disponíveis: {available}"
        )

    return EMBEDDING_CONFIGS[config_name]


def list_available_configs() -> list[str]:
    """
    Lista configurações disponíveis.

    Returns:
        Lista de nomes de configurações
    """
    return list(EMBEDDING_CONFIGS.keys())


def encode_batch(
    texts: list[str],
    model: "SentenceTransformer",
    batch_size: int = 32,
    show_progress: bool = True,
    normalize: bool = True
) -> "np.ndarray":
    """
    Codifica batch de textos com progress bar.

    Args:
        texts: Lista de textos
        model: Modelo SentenceTransformer
        batch_size: Tamanho do batch
        show_progress: Mostrar barra de progresso
        normalize: Normalizar embeddings

    Returns:
        Array numpy com embeddings (shape: [len(texts), embedding_dim])
    """
    import numpy as np

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        normalize_embeddings=normalize,
        convert_to_numpy=True
    )

    return embeddings


# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════

def compare_embeddings(
    text1: str,
    text2: str,
    model: "SentenceTransformer"
) -> float:
    """
    Compara similaridade entre dois textos.

    Args:
        text1: Primeiro texto
        text2: Segundo texto
        model: Modelo de embeddings

    Returns:
        Score de similaridade (cosine) entre 0 e 1
    """
    from sklearn.metrics.pairwise import cosine_similarity

    embeddings = model.encode([text1, text2])

    similarity = cosine_similarity(
        embeddings[0].reshape(1, -1),
        embeddings[1].reshape(1, -1)
    )[0][0]

    return float(similarity)


def benchmark_model(
    config_name: str,
    sample_texts: list[str],
    device: str = "auto"
) -> dict:
    """
    Faz benchmark de um modelo de embeddings.

    Args:
        config_name: Nome da configuração
        sample_texts: Textos de teste
        device: Device a usar

    Returns:
        Dict com métricas de performance:
        - encoding_time_ms: Tempo médio por texto
        - throughput_texts_per_sec: Throughput
        - memory_mb: Memória utilizada
    """
    import time
    import psutil
    import os

    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # MB

    # Carregar modelo
    model = get_embedding_model(config_name, device)
    config = get_embedding_config(config_name)

    mem_after_load = process.memory_info().rss / 1024 / 1024

    # Warm-up
    _ = model.encode(sample_texts[:2])

    # Benchmark
    start = time.time()
    embeddings = model.encode(
        sample_texts,
        batch_size=config.batch_size,
        show_progress_bar=False
    )
    end = time.time()

    elapsed = end - start
    throughput = len(sample_texts) / elapsed
    avg_time_ms = (elapsed / len(sample_texts)) * 1000

    mem_after_encode = process.memory_info().rss / 1024 / 1024

    return {
        "config_name": config_name,
        "model_path": config.model_path,
        "device": device,
        "num_texts": len(sample_texts),
        "embedding_dim": embeddings.shape[1],
        "encoding_time_ms": round(avg_time_ms, 2),
        "throughput_texts_per_sec": round(throughput, 2),
        "total_time_sec": round(elapsed, 2),
        "memory_model_mb": round(mem_after_load - mem_before, 2),
        "memory_total_mb": round(mem_after_encode - mem_before, 2)
    }


if __name__ == "__main__":
    # Teste básico
    print("Configurações disponíveis:")
    for name in list_available_configs():
        config = get_embedding_config(name)
        print(f"  - {name}: {config.model_path} ({config.embedding_dim}d)")

    # Testar carregamento
    print("\nTestando modelo 'fast'...")
    model = get_embedding_model("fast", device="cpu")

    # Testar encoding
    texts = [
        "O direito à liberdade de expressão é fundamental",
        "A prisão preventiva requer fundamentação adequada"
    ]

    embeddings = encode_batch(texts, model, show_progress=False)
    print(f"Embeddings gerados: {embeddings.shape}")

    # Testar similaridade
    sim = compare_embeddings(texts[0], texts[1], model)
    print(f"Similaridade: {sim:.3f}")
