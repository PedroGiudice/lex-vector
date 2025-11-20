"""
Módulo de Chunking para Textos Longos

Divide textos jurídicos longos em chunks (pedaços) menores para processamento
de embeddings. Implementa estratégia de sobreposição (overlap) para preservar
contexto entre chunks adjacentes.

Estratégia:
- Tamanho padrão: 500 tokens (~2000 caracteres em português)
- Sobreposição: 50 tokens (10% overlap)
- Divisão inteligente: Prefere quebrar em parágrafos/sentenças

Uso:
    from src.rag.chunker import Chunker

    chunker = Chunker(tamanho_chunk=500, overlap=50)
    chunks = chunker.dividir_texto("Texto longo...")
    chunks_com_metadata = chunker.dividir_com_metadata("Texto...", publicacao_id="abc123")
"""

from typing import List, Dict, Optional
import re
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """
    Representa um chunk de texto com metadados.

    Attributes:
        texto: Conteúdo do chunk
        chunk_index: Posição do chunk (0, 1, 2, ...)
        tamanho_chars: Tamanho em caracteres
        tamanho_tokens_aprox: Tamanho aproximado em tokens
        inicio: Posição inicial no texto original (caracteres)
        fim: Posição final no texto original (caracteres)
    """
    texto: str
    chunk_index: int
    tamanho_chars: int
    tamanho_tokens_aprox: int
    inicio: int
    fim: int


class Chunker:
    """
    Divisor de textos longos em chunks com sobreposição.

    Attributes:
        tamanho_chunk: Tamanho alvo do chunk em tokens (padrão: 500)
        overlap: Tamanho da sobreposição em tokens (padrão: 50)
        chars_por_token: Heurística para estimar tokens (padrão: 4.0)
    """

    def __init__(
        self,
        tamanho_chunk: int = 500,
        overlap: int = 50,
        chars_por_token: float = 4.0
    ):
        """
        Inicializa o chunker.

        Args:
            tamanho_chunk: Tamanho alvo do chunk em tokens (recomendado: 400-600)
            overlap: Sobreposição em tokens (recomendado: 10-20% do tamanho_chunk)
            chars_por_token: Caracteres por token (português: ~4.0, inglês: ~4.5)

        Raises:
            ValueError: Parâmetros inválidos
        """
        if tamanho_chunk <= 0:
            raise ValueError("tamanho_chunk deve ser positivo")
        if overlap < 0:
            raise ValueError("overlap não pode ser negativo")
        if overlap >= tamanho_chunk:
            raise ValueError("overlap deve ser menor que tamanho_chunk")
        if chars_por_token <= 0:
            raise ValueError("chars_por_token deve ser positivo")

        self.tamanho_chunk = tamanho_chunk
        self.overlap = overlap
        self.chars_por_token = chars_por_token

        # Converter tokens para caracteres
        self.tamanho_chunk_chars = int(tamanho_chunk * chars_por_token)
        self.overlap_chars = int(overlap * chars_por_token)

        logger.debug(
            f"Chunker inicializado: {tamanho_chunk} tokens ({self.tamanho_chunk_chars} chars), "
            f"overlap {overlap} tokens ({self.overlap_chars} chars)"
        )

    def dividir_texto(
        self,
        texto: str,
        estrategia: str = "paragrafo"
    ) -> List[Chunk]:
        """
        Divide texto em chunks com sobreposição.

        Args:
            texto: Texto para dividir
            estrategia: Estratégia de divisão ('paragrafo', 'sentenca', 'rigido')
                - 'paragrafo': Prefere quebrar em parágrafos (padrão)
                - 'sentenca': Prefere quebrar em sentenças
                - 'rigido': Quebra em posição exata (sem considerar estrutura)

        Returns:
            Lista de chunks com metadados

        Raises:
            ValueError: Texto vazio ou estratégia inválida
        """
        if not texto or not texto.strip():
            raise ValueError("Texto vazio não pode ser dividido")

        if estrategia not in ["paragrafo", "sentenca", "rigido"]:
            raise ValueError(f"Estratégia inválida: {estrategia}")

        texto = texto.strip()

        # Se texto cabe em um chunk, retornar sem dividir
        if len(texto) <= self.tamanho_chunk_chars:
            return [Chunk(
                texto=texto,
                chunk_index=0,
                tamanho_chars=len(texto),
                tamanho_tokens_aprox=self._estimar_tokens(texto),
                inicio=0,
                fim=len(texto)
            )]

        # Dividir conforme estratégia
        if estrategia == "paragrafo":
            return self._dividir_por_paragrafo(texto)
        elif estrategia == "sentenca":
            return self._dividir_por_sentenca(texto)
        else:  # rigido
            return self._dividir_rigido(texto)

    def dividir_com_metadata(
        self,
        texto: str,
        publicacao_id: str,
        estrategia: str = "paragrafo",
        metadata_adicional: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Divide texto e retorna chunks com metadados completos para DB.

        Args:
            texto: Texto para dividir
            publicacao_id: ID da publicação (UUID)
            estrategia: Estratégia de divisão
            metadata_adicional: Metadados extras (ex: tipo_publicacao, tribunal)

        Returns:
            Lista de dicts prontos para inserção no DB:
                {
                    'id': str (UUID v4),
                    'publicacao_id': str,
                    'chunk_index': int,
                    'texto': str,
                    'tamanho_tokens': int,
                    'metadata': dict (opcional)
                }
        """
        import uuid

        chunks = self.dividir_texto(texto, estrategia=estrategia)

        resultado = []
        for chunk in chunks:
            chunk_dict = {
                'id': str(uuid.uuid4()),
                'publicacao_id': publicacao_id,
                'chunk_index': chunk.chunk_index,
                'texto': chunk.texto,
                'tamanho_tokens': chunk.tamanho_tokens_aprox,
            }

            # Adicionar metadata se fornecido
            if metadata_adicional:
                chunk_dict['metadata'] = metadata_adicional

            resultado.append(chunk_dict)

        logger.info(
            f"Texto dividido em {len(resultado)} chunks "
            f"(publicacao_id={publicacao_id[:8]}...)"
        )

        return resultado

    def _dividir_por_paragrafo(self, texto: str) -> List[Chunk]:
        """
        Divide texto preferindo quebras em parágrafos.

        Estratégia:
        1. Dividir em parágrafos (\\n\\n)
        2. Agrupar parágrafos até atingir tamanho_chunk
        3. Adicionar overlap do chunk anterior
        """
        # Dividir em parágrafos
        paragrafos = re.split(r'\n{2,}', texto)
        chunks = []
        chunk_atual = []
        tamanho_atual = 0
        posicao = 0

        for paragrafo in paragrafos:
            paragrafo = paragrafo.strip()
            if not paragrafo:
                continue

            tamanho_paragrafo = len(paragrafo)

            # Se adicionar paragrafo exceder limite, criar chunk
            if tamanho_atual + tamanho_paragrafo > self.tamanho_chunk_chars and chunk_atual:
                # Criar chunk com parágrafos acumulados
                texto_chunk = "\n\n".join(chunk_atual)
                inicio = posicao - tamanho_atual
                fim = posicao

                chunks.append(Chunk(
                    texto=texto_chunk,
                    chunk_index=len(chunks),
                    tamanho_chars=len(texto_chunk),
                    tamanho_tokens_aprox=self._estimar_tokens(texto_chunk),
                    inicio=inicio,
                    fim=fim
                ))

                # Preparar próximo chunk com overlap
                # Pegar últimos N caracteres para overlap
                if self.overlap_chars > 0:
                    chunk_atual = [self._extrair_overlap(texto_chunk, self.overlap_chars)]
                    tamanho_atual = len(chunk_atual[0])
                else:
                    chunk_atual = []
                    tamanho_atual = 0

            # Adicionar parágrafo ao chunk atual
            chunk_atual.append(paragrafo)
            tamanho_atual += tamanho_paragrafo
            posicao += tamanho_paragrafo + 2  # +2 para \n\n

        # Adicionar último chunk se houver
        if chunk_atual:
            texto_chunk = "\n\n".join(chunk_atual)
            inicio = posicao - tamanho_atual
            fim = posicao

            chunks.append(Chunk(
                texto=texto_chunk,
                chunk_index=len(chunks),
                tamanho_chars=len(texto_chunk),
                tamanho_tokens_aprox=self._estimar_tokens(texto_chunk),
                inicio=inicio,
                fim=fim
            ))

        return chunks

    def _dividir_por_sentenca(self, texto: str) -> List[Chunk]:
        """
        Divide texto preferindo quebras em sentenças.

        Usa regex para detectar fim de sentença (. ! ?)
        """
        # Detectar sentenças (simplificado - pode ser melhorado)
        sentencas = re.split(r'(?<=[.!?])\s+', texto)

        chunks = []
        chunk_atual = []
        tamanho_atual = 0
        posicao = 0

        for sentenca in sentencas:
            sentenca = sentenca.strip()
            if not sentenca:
                continue

            tamanho_sentenca = len(sentenca)

            if tamanho_atual + tamanho_sentenca > self.tamanho_chunk_chars and chunk_atual:
                # Criar chunk
                texto_chunk = " ".join(chunk_atual)
                inicio = posicao - tamanho_atual
                fim = posicao

                chunks.append(Chunk(
                    texto=texto_chunk,
                    chunk_index=len(chunks),
                    tamanho_chars=len(texto_chunk),
                    tamanho_tokens_aprox=self._estimar_tokens(texto_chunk),
                    inicio=inicio,
                    fim=fim
                ))

                # Overlap
                if self.overlap_chars > 0:
                    chunk_atual = [self._extrair_overlap(texto_chunk, self.overlap_chars)]
                    tamanho_atual = len(chunk_atual[0])
                else:
                    chunk_atual = []
                    tamanho_atual = 0

            chunk_atual.append(sentenca)
            tamanho_atual += tamanho_sentenca + 1  # +1 para espaço
            posicao += tamanho_sentenca + 1

        # Último chunk
        if chunk_atual:
            texto_chunk = " ".join(chunk_atual)
            inicio = posicao - tamanho_atual
            fim = posicao

            chunks.append(Chunk(
                texto=texto_chunk,
                chunk_index=len(chunks),
                tamanho_chars=len(texto_chunk),
                tamanho_tokens_aprox=self._estimar_tokens(texto_chunk),
                inicio=inicio,
                fim=fim
            ))

        return chunks

    def _dividir_rigido(self, texto: str) -> List[Chunk]:
        """
        Divide texto em posições fixas (sem considerar estrutura).

        Útil para textos sem estrutura clara de parágrafos/sentenças.
        """
        chunks = []
        tamanho_texto = len(texto)
        inicio = 0

        while inicio < tamanho_texto:
            fim = min(inicio + self.tamanho_chunk_chars, tamanho_texto)
            texto_chunk = texto[inicio:fim]

            chunks.append(Chunk(
                texto=texto_chunk,
                chunk_index=len(chunks),
                tamanho_chars=len(texto_chunk),
                tamanho_tokens_aprox=self._estimar_tokens(texto_chunk),
                inicio=inicio,
                fim=fim
            ))

            # Avançar com overlap
            inicio += (self.tamanho_chunk_chars - self.overlap_chars)

        return chunks

    def _extrair_overlap(self, texto: str, tamanho: int) -> str:
        """
        Extrai últimos N caracteres de um texto para overlap.

        Tenta quebrar em palavra completa para melhor qualidade.
        """
        if len(texto) <= tamanho:
            return texto

        # Pegar últimos N caracteres
        overlap = texto[-tamanho:]

        # Tentar quebrar em espaço (palavra completa)
        espaco_idx = overlap.find(' ')
        if espaco_idx > 0:
            overlap = overlap[espaco_idx+1:]

        return overlap

    def _estimar_tokens(self, texto: str) -> int:
        """
        Estima número de tokens usando heurística chars_por_token.

        Args:
            texto: Texto para estimar

        Returns:
            Número aproximado de tokens
        """
        return int(len(texto) / self.chars_por_token)

    def estatisticas(self, chunks: List[Chunk]) -> Dict:
        """
        Calcula estatísticas sobre chunks gerados.

        Args:
            chunks: Lista de chunks

        Returns:
            Dict com estatísticas:
                - total_chunks: int
                - tamanho_medio_chars: float
                - tamanho_medio_tokens: float
                - tamanho_min/max: int
                - sobreposicao_media: float (%)
        """
        if not chunks:
            return {}

        tamanhos_chars = [c.tamanho_chars for c in chunks]
        tamanhos_tokens = [c.tamanho_tokens_aprox for c in chunks]

        # Calcular overlap médio
        overlaps = []
        for i in range(1, len(chunks)):
            chunk_anterior = chunks[i-1]
            chunk_atual = chunks[i]

            # Verificar sobreposição textual
            overlap_chars = 0
            for j in range(1, min(len(chunk_anterior.texto), len(chunk_atual.texto))):
                if chunk_anterior.texto[-j:] == chunk_atual.texto[:j]:
                    overlap_chars = j
                    break

            if chunk_anterior.tamanho_chars > 0:
                overlap_percent = (overlap_chars / chunk_anterior.tamanho_chars) * 100
                overlaps.append(overlap_percent)

        return {
            "total_chunks": len(chunks),
            "tamanho_medio_chars": sum(tamanhos_chars) / len(chunks),
            "tamanho_medio_tokens": sum(tamanhos_tokens) / len(chunks),
            "tamanho_min_chars": min(tamanhos_chars),
            "tamanho_max_chars": max(tamanhos_chars),
            "sobreposicao_media_percent": sum(overlaps) / len(overlaps) if overlaps else 0.0
        }


# Exemplo de uso
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Texto de exemplo (simulando acórdão)
    texto_exemplo = """
APELAÇÃO CÍVEL. DIREITO DO CONSUMIDOR. RESPONSABILIDADE CIVIL. DANOS MORAIS.

I - RELATÓRIO
Trata-se de apelação interposta por XYZ LTDA contra sentença que julgou procedente
pedido de indenização por danos morais no valor de R$ 10.000,00.

A parte autora alega ter sido vítima de cobranças indevidas e inscrição em órgãos
de proteção ao crédito, causando-lhe constrangimento e abalo psicológico.

II - FUNDAMENTAÇÃO
O Código de Defesa do Consumidor estabelece responsabilidade objetiva do fornecedor
por danos causados ao consumidor. No caso, restou demonstrado que a cobrança era
indevida, pois o débito já havia sido quitado anteriormente.

A jurisprudência pacífica do STJ reconhece que a inscrição indevida em cadastros
de inadimplentes gera dano moral in re ipsa, dispensando prova do abalo psicológico.

III - CONCLUSÃO
Ante o exposto, NEGO PROVIMENTO ao recurso, mantendo a sentença por seus próprios
fundamentos. Condenação em honorários recursais de 10% sobre o valor da condenação.
""" * 3  # Repetir para criar texto longo

    print("=" * 80)
    print("TESTE DE CHUNKING")
    print("=" * 80)

    # Inicializar chunker
    chunker = Chunker(tamanho_chunk=500, overlap=50)

    print(f"\nTexto original: {len(texto_exemplo)} caracteres")
    print(f"Tokens estimados: {chunker._estimar_tokens(texto_exemplo)}")

    # Testar diferentes estratégias
    for estrategia in ["paragrafo", "sentenca", "rigido"]:
        print(f"\n--- Estratégia: {estrategia} ---")
        chunks = chunker.dividir_texto(texto_exemplo, estrategia=estrategia)

        for i, chunk in enumerate(chunks):
            print(f"\nChunk {i}:")
            print(f"  Tamanho: {chunk.tamanho_chars} chars ({chunk.tamanho_tokens_aprox} tokens)")
            print(f"  Posição: [{chunk.inicio}:{chunk.fim}]")
            print(f"  Preview: {chunk.texto[:100]}...")

        # Estatísticas
        stats = chunker.estatisticas(chunks)
        print(f"\nEstatísticas:")
        for k, v in stats.items():
            if isinstance(v, float):
                print(f"  {k}: {v:.2f}")
            else:
                print(f"  {k}: {v}")

    # Testar com metadata
    print("\n" + "=" * 80)
    print("TESTE COM METADATA")
    print("=" * 80)

    chunks_db = chunker.dividir_com_metadata(
        texto=texto_exemplo,
        publicacao_id="abc123-def456-ghi789",
        estrategia="paragrafo",
        metadata_adicional={"tribunal": "TJSP", "tipo": "Acórdão"}
    )

    print(f"\nChunks gerados: {len(chunks_db)}")
    print(f"Exemplo de chunk DB:")
    print(f"  ID: {chunks_db[0]['id']}")
    print(f"  Publicação ID: {chunks_db[0]['publicacao_id']}")
    print(f"  Index: {chunks_db[0]['chunk_index']}")
    print(f"  Tokens: {chunks_db[0]['tamanho_tokens']}")
    print(f"  Metadata: {chunks_db[0].get('metadata', {})}")
