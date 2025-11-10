"""
RAG Engine - Sistema de Retrieval-Augmented Generation
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from .pdf_processor import DocumentChunk

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Motor RAG para busca semântica e recuperação de documentos jurídicos
    """

    def __init__(self, config: Dict):
        self.config = config
        self.embedding_model_name = config['rag']['embedding_model']
        self.collection_name = config['rag']['collection_name']
        self.top_k = config['rag']['top_k_results']
        self.similarity_threshold = config['rag']['similarity_threshold']

        # Paths
        data_root = Path(config['paths']['data_root'])
        self.vector_db_path = data_root / config['paths']['vector_db']
        self.vector_db_path.mkdir(parents=True, exist_ok=True)

        # Inicializar embedding model
        logger.info(f"Carregando modelo de embeddings: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)

        # Inicializar ChromaDB
        logger.info(f"Inicializando ChromaDB em: {self.vector_db_path}")
        self.client = chromadb.PersistentClient(
            path=str(self.vector_db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Criar ou carregar collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Collection '{self.collection_name}' carregada: {self.collection.count()} documentos")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Collection '{self.collection_name}' criada")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding para um texto

        Args:
            text: Texto para gerar embedding

        Returns:
            Vetor de embedding
        """
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def add_documents(self, chunks: List[DocumentChunk]) -> int:
        """
        Adiciona documentos ao vector store

        Args:
            chunks: Lista de chunks para indexar

        Returns:
            Número de documentos adicionados
        """
        if not chunks:
            logger.warning("Nenhum chunk para adicionar")
            return 0

        logger.info(f"Gerando embeddings para {len(chunks)} chunks...")

        # Preparar dados
        ids = []
        texts = []
        embeddings = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            # ID único: source_file + page + chunk_number
            chunk_id = f"{chunk.source_file}_p{chunk.page_number}_c{chunk.metadata.get('chunk_number', i)}"
            ids.append(chunk_id)
            texts.append(chunk.text)

            # Gerar embedding
            embedding = self.generate_embedding(chunk.text)
            embeddings.append(embedding)

            # Preparar metadata (ChromaDB aceita apenas tipos básicos)
            metadata = {
                'source_file': chunk.source_file,
                'page_number': chunk.page_number,
                'chunk_number': chunk.metadata.get('chunk_number', i),
                'chunk_size': chunk.metadata.get('chunk_size', len(chunk.text)),
                'tribunal': chunk.metadata.get('tribunal', ''),
                'data': chunk.metadata.get('data', '')
            }
            metadatas.append(metadata)

        # Adicionar ao ChromaDB
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            logger.info(f"✓ {len(chunks)} chunks adicionados ao vector store")
            return len(chunks)

        except Exception as e:
            logger.error(f"Erro ao adicionar documentos: {e}")
            return 0

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Busca semântica por documentos relevantes

        Args:
            query: Texto da consulta
            top_k: Número de resultados (default: configuração)
            filter_metadata: Filtros de metadata (ex: {'tribunal': 'TJSP'})

        Returns:
            Lista de documentos relevantes com scores
        """
        top_k = top_k or self.top_k

        logger.info(f"Buscando: '{query[:100]}...'")

        # Gerar embedding da query
        query_embedding = self.generate_embedding(query)

        # Buscar no ChromaDB
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata  # Filtros de metadata
            )

            # Formatar resultados
            formatted_results = []

            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i]
                    similarity = 1 - distance  # Converter distância em similaridade

                    # Filtrar por threshold
                    if similarity < self.similarity_threshold:
                        continue

                    formatted_results.append({
                        'id': doc_id,
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity': round(similarity, 4),
                        'distance': round(distance, 4)
                    })

            logger.info(f"✓ Encontrados {len(formatted_results)} resultados relevantes")
            return formatted_results

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            return []

    def search_by_theme(self, theme: str, top_k: Optional[int] = None) -> List[Dict]:
        """
        Busca documentos por tema jurídico

        Args:
            theme: Tema jurídico (ex: 'responsabilidade civil')
            top_k: Número de resultados

        Returns:
            Lista de documentos relevantes
        """
        # Expandir query com termos jurídicos
        query = f"jurisprudência sobre {theme}, decisões judiciais relacionadas a {theme}"

        return self.search(query, top_k)

    def get_collection_stats(self) -> Dict:
        """
        Retorna estatísticas da collection

        Returns:
            Dict com estatísticas
        """
        count = self.collection.count()

        # Obter sample de metadatas
        sample = self.collection.peek(limit=100)

        tribunais = set()
        datas = set()

        if sample['metadatas']:
            for metadata in sample['metadatas']:
                if metadata.get('tribunal'):
                    tribunais.add(metadata['tribunal'])
                if metadata.get('data'):
                    datas.add(metadata['data'])

        return {
            'total_documents': count,
            'tribunais_unicos': len(tribunais),
            'tribunais': sorted(list(tribunais)),
            'datas_unicas': len(datas),
            'periodo': f"{min(datas) if datas else 'N/A'} a {max(datas) if datas else 'N/A'}",
            'collection_name': self.collection_name,
            'embedding_model': self.embedding_model_name
        }

    def delete_documents(self, filter_metadata: Optional[Dict] = None) -> int:
        """
        Deleta documentos baseado em metadata

        Args:
            filter_metadata: Filtros (ex: {'source_file': 'arquivo.pdf'})

        Returns:
            Número de documentos deletados
        """
        try:
            count_before = self.collection.count()

            if filter_metadata:
                self.collection.delete(where=filter_metadata)
            else:
                logger.warning("Nenhum filtro especificado - nada foi deletado")
                return 0

            count_after = self.collection.count()
            deleted = count_before - count_after

            logger.info(f"✓ {deleted} documentos deletados")
            return deleted

        except Exception as e:
            logger.error(f"Erro ao deletar documentos: {e}")
            return 0

    def reset_collection(self):
        """Reseta a collection (apaga tudo)"""
        logger.warning("Resetando collection...")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Collection resetada")

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[Dict] = None
    ) -> List[Tuple[str, float]]:
        """
        Busca com scores de similaridade

        Args:
            query: Query de busca
            k: Número de resultados
            filter_dict: Filtros de metadata

        Returns:
            Lista de tuplas (documento, score)
        """
        results = self.search(query, top_k=k, filter_metadata=filter_dict)

        return [(r['text'], r['similarity']) for r in results]
