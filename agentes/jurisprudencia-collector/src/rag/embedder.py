"""
Módulo de Geração de Embeddings para Busca Semântica

Este módulo implementa geração de embeddings usando modelos transformer
otimizados para texto em português (brasileiro). Suporta processamento
em batch para performance e cache local de modelos.

Modelos suportados:
- neuralmind/bert-base-portuguese-cased (768 dim) - Padrão
- sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dim) - Leve

Uso:
    from src.rag.embedder import Embedder

    embedder = Embedder(modelo='neuralmind/bert-base-portuguese-cased')
    embedding = embedder.encode("Texto de uma publicação jurídica")
    embeddings = embedder.encode_batch(["texto1", "texto2", "texto3"])
"""

from typing import List, Union, Optional, Dict
import numpy as np
from pathlib import Path
import logging
import time

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
except ImportError:
    raise ImportError(
        "transformers e torch não instalados. Execute: "
        "pip install transformers torch sentence-transformers"
    )

# Configuração de logging
logger = logging.getLogger(__name__)


class Embedder:
    """
    Gerador de embeddings para busca semântica usando modelos transformer.

    Attributes:
        modelo_nome: Nome do modelo HuggingFace (ex: 'neuralmind/bert-base-portuguese-cased')
        dimensao: Dimensão do vetor de embedding (768 ou 384)
        device: Device PyTorch ('cpu' ou 'cuda')
        max_length: Comprimento máximo de tokens (padrão: 512)
    """

    # Modelos suportados e suas especificações
    MODELOS_SUPORTADOS = {
        "neuralmind/bert-base-portuguese-cased": {
            "dimensao": 768,
            "tamanho_mb": 420,
            "descricao": "BERT português - Alta qualidade, mais pesado"
        },
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {
            "dimensao": 384,
            "tamanho_mb": 420,
            "descricao": "Multilíngue - Leve e rápido"
        },
        "sentence-transformers/distiluse-base-multilingual-cased-v2": {
            "dimensao": 512,
            "tamanho_mb": 480,
            "descricao": "DistilUSE - Balanço qualidade/velocidade"
        }
    }

    def __init__(
        self,
        modelo: str = "neuralmind/bert-base-portuguese-cased",
        cache_dir: Optional[Path] = None,
        device: Optional[str] = None,
        max_length: int = 512
    ):
        """
        Inicializa o embedder com modelo especificado.

        Args:
            modelo: Nome do modelo HuggingFace (deve estar em MODELOS_SUPORTADOS)
            cache_dir: Diretório para cache de modelos (padrão: ~/.cache/huggingface)
            device: Device PyTorch ('cpu', 'cuda', 'mps'). Se None, detecta automaticamente
            max_length: Comprimento máximo de tokens (trunca textos maiores)

        Raises:
            ValueError: Modelo não suportado
            RuntimeError: Erro ao carregar modelo
        """
        if modelo not in self.MODELOS_SUPORTADOS:
            raise ValueError(
                f"Modelo '{modelo}' não suportado. Opções: {list(self.MODELOS_SUPORTADOS.keys())}"
            )

        self.modelo_nome = modelo
        self.dimensao = self.MODELOS_SUPORTADOS[modelo]["dimensao"]
        self.max_length = max_length

        # Detectar device disponível
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = "mps"  # Apple Silicon
            else:
                self.device = "cpu"
        else:
            self.device = device

        # Configurar cache
        self.cache_dir = cache_dir or Path.home() / ".cache" / "huggingface"

        logger.info(
            f"Inicializando Embedder: {modelo} (dim={self.dimensao}, device={self.device})"
        )

        # Carregar modelo e tokenizer
        try:
            start_time = time.time()

            self.tokenizer = AutoTokenizer.from_pretrained(
                modelo,
                cache_dir=str(self.cache_dir)
            )

            self.model = AutoModel.from_pretrained(
                modelo,
                cache_dir=str(self.cache_dir)
            )
            self.model.to(self.device)
            self.model.eval()  # Modo inferência

            load_time = time.time() - start_time
            logger.info(f"Modelo carregado em {load_time:.2f}s")

        except Exception as e:
            logger.error(f"Erro ao carregar modelo {modelo}: {e}")
            raise RuntimeError(f"Falha ao carregar modelo: {e}")

    def encode(
        self,
        texto: str,
        normalizar: bool = True,
        mostrar_tempo: bool = False
    ) -> np.ndarray:
        """
        Gera embedding para um único texto.

        Args:
            texto: Texto para gerar embedding
            normalizar: Se True, normaliza vetor (norma L2 = 1)
            mostrar_tempo: Se True, loga tempo de processamento

        Returns:
            Array numpy com embedding (shape: [dimensao])

        Raises:
            ValueError: Texto vazio
        """
        if not texto or not texto.strip():
            raise ValueError("Texto vazio não pode ser processado")

        start_time = time.time() if mostrar_tempo else None

        # Tokenizar
        inputs = self.tokenizer(
            texto,
            return_tensors="pt",
            max_length=self.max_length,
            truncation=True,
            padding=True
        )

        # Mover para device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Gerar embedding
        with torch.no_grad():
            outputs = self.model(**inputs)

        # Usar [CLS] token (primeira posição) como representação da sentença
        # Alternativa: mean pooling de todos os tokens
        embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()[0]

        # Normalizar se solicitado
        if normalizar:
            embedding = embedding / np.linalg.norm(embedding)

        if mostrar_tempo:
            elapsed = time.time() - start_time
            logger.debug(f"Embedding gerado em {elapsed*1000:.1f}ms")

        return embedding

    def encode_batch(
        self,
        textos: List[str],
        batch_size: int = 32,
        normalizar: bool = True,
        mostrar_progresso: bool = False
    ) -> np.ndarray:
        """
        Gera embeddings para múltiplos textos (batch processing).

        Args:
            textos: Lista de textos
            batch_size: Tamanho do batch para processamento
            normalizar: Se True, normaliza vetores
            mostrar_progresso: Se True, exibe progresso

        Returns:
            Array numpy com embeddings (shape: [num_textos, dimensao])

        Raises:
            ValueError: Lista vazia ou contém textos vazios
        """
        if not textos:
            raise ValueError("Lista de textos vazia")

        # Filtrar textos vazios
        textos_limpos = [t.strip() for t in textos if t and t.strip()]
        if len(textos_limpos) != len(textos):
            logger.warning(
                f"{len(textos) - len(textos_limpos)} textos vazios ignorados"
            )

        if not textos_limpos:
            raise ValueError("Todos os textos são vazios")

        embeddings = []
        total_batches = (len(textos_limpos) + batch_size - 1) // batch_size

        start_time = time.time()

        for i in range(0, len(textos_limpos), batch_size):
            batch = textos_limpos[i:i + batch_size]
            batch_num = i // batch_size + 1

            if mostrar_progresso:
                logger.info(f"Processando batch {batch_num}/{total_batches}...")

            # Tokenizar batch
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                max_length=self.max_length,
                truncation=True,
                padding=True
            )

            # Mover para device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Gerar embeddings
            with torch.no_grad():
                outputs = self.model(**inputs)

            # Extrair [CLS] token embeddings
            batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

            # Normalizar se solicitado
            if normalizar:
                norms = np.linalg.norm(batch_embeddings, axis=1, keepdims=True)
                batch_embeddings = batch_embeddings / norms

            embeddings.append(batch_embeddings)

        # Concatenar todos os batches
        embeddings = np.vstack(embeddings)

        elapsed = time.time() - start_time
        logger.info(
            f"Processados {len(textos_limpos)} textos em {elapsed:.2f}s "
            f"({len(textos_limpos)/elapsed:.1f} textos/s)"
        )

        return embeddings

    def encode_com_metadata(
        self,
        texto: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Gera embedding com metadados adicionais (útil para debugging).

        Args:
            texto: Texto para processar
            metadata: Metadados opcionais (ex: publicacao_id, tipo)

        Returns:
            Dict com:
                - embedding: array numpy
                - dimensao: int
                - modelo: str
                - metadata: dict (se fornecido)
                - tamanho_texto: int (caracteres)
                - num_tokens: int (aproximado)
        """
        embedding = self.encode(texto, normalizar=True, mostrar_tempo=False)

        # Aproximar número de tokens (heurística: 4 chars = 1 token em português)
        num_tokens_approx = len(texto) // 4

        resultado = {
            "embedding": embedding,
            "dimensao": self.dimensao,
            "modelo": self.modelo_nome,
            "tamanho_texto": len(texto),
            "num_tokens_aprox": num_tokens_approx,
        }

        if metadata:
            resultado["metadata"] = metadata

        return resultado

    def serializar_embedding(self, embedding: np.ndarray) -> bytes:
        """
        Serializa embedding para armazenamento no SQLite (BLOB).

        Args:
            embedding: Array numpy (Float32)

        Returns:
            Bytes (BLOB) para inserir em SQLite
        """
        # Garantir dtype Float32
        embedding_f32 = embedding.astype(np.float32)
        return embedding_f32.tobytes()

    @staticmethod
    def desserializar_embedding(blob: bytes, dimensao: int) -> np.ndarray:
        """
        Desserializa embedding do SQLite (BLOB → numpy array).

        Args:
            blob: Bytes do BLOB
            dimensao: Dimensão do embedding (768 ou 384)

        Returns:
            Array numpy (Float32)

        Raises:
            ValueError: Tamanho incorreto do BLOB
        """
        expected_size = dimensao * 4  # 4 bytes por float32
        if len(blob) != expected_size:
            raise ValueError(
                f"BLOB com tamanho incorreto. "
                f"Esperado: {expected_size} bytes, recebido: {len(blob)} bytes"
            )

        return np.frombuffer(blob, dtype=np.float32)

    def info_modelo(self) -> Dict:
        """
        Retorna informações sobre o modelo carregado.

        Returns:
            Dict com especificações do modelo
        """
        return {
            "modelo": self.modelo_nome,
            "dimensao": self.dimensao,
            "device": self.device,
            "max_length": self.max_length,
            "cache_dir": str(self.cache_dir),
            **self.MODELOS_SUPORTADOS[self.modelo_nome]
        }


# Exemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Inicializar embedder
    embedder = Embedder(modelo="neuralmind/bert-base-portuguese-cased")

    # Testar texto único
    texto_exemplo = """
    APELAÇÃO CÍVEL. DIREITO CIVIL. RESPONSABILIDADE CIVIL.
    ACIDENTE DE TRÂNSITO. DANOS MATERIAIS. PROVA PERICIAL.
    Recurso conhecido e provido.
    """

    print("\n=== TESTE 1: Texto Único ===")
    embedding = embedder.encode(texto_exemplo, mostrar_tempo=True)
    print(f"Shape: {embedding.shape}")
    print(f"Primeiros 5 valores: {embedding[:5]}")
    print(f"Norma L2: {np.linalg.norm(embedding):.4f}")

    # Testar batch
    textos_batch = [
        "Apelação cível conhecida e provida.",
        "Recurso especial não conhecido.",
        "Habeas corpus deferido.",
    ]

    print("\n=== TESTE 2: Batch Processing ===")
    embeddings_batch = embedder.encode_batch(
        textos_batch,
        batch_size=2,
        mostrar_progresso=True
    )
    print(f"Shape: {embeddings_batch.shape}")

    # Testar serialização
    print("\n=== TESTE 3: Serialização ===")
    blob = embedder.serializar_embedding(embedding)
    print(f"Tamanho BLOB: {len(blob)} bytes")

    embedding_restaurado = Embedder.desserializar_embedding(blob, embedder.dimensao)
    print(f"Embeddings iguais: {np.allclose(embedding, embedding_restaurado)}")

    # Info do modelo
    print("\n=== TESTE 4: Informações do Modelo ===")
    info = embedder.info_modelo()
    for k, v in info.items():
        print(f"  {k}: {v}")
