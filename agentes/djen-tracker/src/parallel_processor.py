"""
Parallel Processor - Processamento Paralelo de PDFs em Batch

Processa múltiplos PDFs em paralelo usando multiprocessing para
acelerar o filtro em larga escala (65 tribunais × 50-200 páginas).

Author: Claude Code (Development Agent)
Version: 1.0.0
"""

import logging
import multiprocessing as mp
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm


logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Resultado de processamento de um PDF."""
    pdf_path: Path
    success: bool
    matches_count: int
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0


class ParallelProcessor:
    """
    Processador paralelo de PDFs para filtro OAB.

    Usa ProcessPoolExecutor para processar múltiplos PDFs simultaneamente,
    otimizando para cenários de alta carga (milhares de páginas).

    Attributes:
        max_workers: Número máximo de processos paralelos
        show_progress: Exibir barra de progresso (tqdm)
        chunk_size: Tamanho do chunk para processamento
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        show_progress: bool = True,
        chunk_size: int = 1
    ):
        """
        Inicializa ParallelProcessor.

        Args:
            max_workers: Número de workers (default: CPU count)
            show_progress: Exibir progresso com tqdm
            chunk_size: Tamanho do chunk para map
        """
        if max_workers is None:
            # Usar 80% dos cores disponíveis
            max_workers = max(1, int(mp.cpu_count() * 0.8))

        self.max_workers = max_workers
        self.show_progress = show_progress
        self.chunk_size = chunk_size

        logger.info(
            f"ParallelProcessor inicializado com {max_workers} workers"
        )

    def process_batch(
        self,
        pdf_paths: List[Path],
        target_oabs: List[Tuple[str, str]],
        filter_func: Callable,
        min_score: float = 0.5,
        use_cache: bool = True
    ) -> Tuple[List, List[ProcessingResult]]:
        """
        Processa batch de PDFs em paralelo.

        Args:
            pdf_paths: Lista de paths para PDFs
            target_oabs: Lista de (numero, uf) desejadas
            filter_func: Função de filtro (ex: oab_filter.filter_single_pdf)
            min_score: Score mínimo
            use_cache: Usar cache

        Returns:
            (all_matches, processing_results)
        """
        import time

        logger.info(
            f"Processando {len(pdf_paths)} PDFs em paralelo "
            f"({self.max_workers} workers)..."
        )

        all_matches = []
        processing_results = []

        start_time = time.time()

        # Criar tarefas
        tasks = [
            (pdf_path, target_oabs, min_score, use_cache)
            for pdf_path in pdf_paths
        ]

        # Processar em paralelo
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submeter tarefas
            future_to_pdf = {
                executor.submit(
                    self._process_single_wrapper,
                    pdf_path,
                    target_oabs,
                    filter_func,
                    min_score,
                    use_cache
                ): pdf_path
                for pdf_path in pdf_paths
            }

            # Coletar resultados com progresso
            iterator = as_completed(future_to_pdf)

            if self.show_progress:
                iterator = tqdm(
                    iterator,
                    total=len(pdf_paths),
                    desc="Processando PDFs",
                    unit="pdf"
                )

            for future in iterator:
                pdf_path = future_to_pdf[future]

                try:
                    matches, proc_result = future.result()
                    all_matches.extend(matches)
                    processing_results.append(proc_result)

                except Exception as e:
                    logger.error(f"Erro ao processar {pdf_path.name}: {e}")
                    processing_results.append(
                        ProcessingResult(
                            pdf_path=pdf_path,
                            success=False,
                            matches_count=0,
                            error_message=str(e)
                        )
                    )

        elapsed_time = time.time() - start_time

        # Estatísticas
        successful = sum(1 for r in processing_results if r.success)
        total_matches = len(all_matches)

        logger.info(
            f"Processamento concluído em {elapsed_time:.1f}s:\n"
            f"  - PDFs processados: {successful}/{len(pdf_paths)}\n"
            f"  - Matches encontrados: {total_matches}\n"
            f"  - Throughput: {len(pdf_paths)/elapsed_time:.1f} PDFs/s"
        )

        return all_matches, processing_results

    @staticmethod
    def _process_single_wrapper(
        pdf_path: Path,
        target_oabs: List[Tuple[str, str]],
        filter_func: Callable,
        min_score: float,
        use_cache: bool
    ) -> Tuple[List, ProcessingResult]:
        """
        Wrapper para processar PDF único (chamado em processo separado).

        Args:
            pdf_path: Path do PDF
            target_oabs: OABs alvo
            filter_func: Função de filtro
            min_score: Score mínimo
            use_cache: Usar cache

        Returns:
            (matches, ProcessingResult)
        """
        import time

        start_time = time.time()

        try:
            # Chamar função de filtro
            matches = filter_func(
                pdf_path=pdf_path,
                target_oabs=target_oabs,
                min_score=min_score,
                use_cache=use_cache
            )

            elapsed_time = time.time() - start_time

            result = ProcessingResult(
                pdf_path=pdf_path,
                success=True,
                matches_count=len(matches),
                processing_time_seconds=elapsed_time
            )

            return matches, result

        except Exception as e:
            elapsed_time = time.time() - start_time

            logger.error(f"Erro ao processar {pdf_path.name}: {e}")

            result = ProcessingResult(
                pdf_path=pdf_path,
                success=False,
                matches_count=0,
                error_message=str(e),
                processing_time_seconds=elapsed_time
            )

            return [], result

    def process_batch_chunked(
        self,
        pdf_paths: List[Path],
        target_oabs: List[Tuple[str, str]],
        filter_func: Callable,
        min_score: float = 0.5,
        use_cache: bool = True,
        chunk_size: int = 10
    ) -> Tuple[List, List[ProcessingResult]]:
        """
        Processa batch de PDFs em chunks (útil para datasets muito grandes).

        Args:
            pdf_paths: Lista de paths para PDFs
            target_oabs: Lista de (numero, uf) desejadas
            filter_func: Função de filtro
            min_score: Score mínimo
            use_cache: Usar cache
            chunk_size: Tamanho dos chunks

        Returns:
            (all_matches, processing_results)
        """
        logger.info(
            f"Processando {len(pdf_paths)} PDFs em chunks de {chunk_size}..."
        )

        all_matches = []
        all_results = []

        # Dividir em chunks
        chunks = [
            pdf_paths[i:i + chunk_size]
            for i in range(0, len(pdf_paths), chunk_size)
        ]

        logger.info(f"Total de chunks: {len(chunks)}")

        # Processar cada chunk
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processando chunk {i}/{len(chunks)}...")

            matches, results = self.process_batch(
                pdf_paths=chunk,
                target_oabs=target_oabs,
                filter_func=filter_func,
                min_score=min_score,
                use_cache=use_cache
            )

            all_matches.extend(matches)
            all_results.extend(results)

        logger.info(
            f"Todos os chunks processados: "
            f"{len(all_matches)} matches em {len(all_results)} PDFs"
        )

        return all_matches, all_results

    def get_processing_stats(
        self,
        results: List[ProcessingResult]
    ) -> dict:
        """
        Calcula estatísticas de processamento.

        Args:
            results: Lista de ProcessingResult

        Returns:
            Dict com estatísticas
        """
        if not results:
            return {}

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        total_time = sum(r.processing_time_seconds for r in results)
        avg_time = total_time / len(results) if results else 0

        total_matches = sum(r.matches_count for r in successful)

        return {
            'total_pdfs': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(results) if results else 0,
            'total_matches': total_matches,
            'avg_matches_per_pdf': (
                total_matches / len(successful) if successful else 0
            ),
            'total_processing_time_seconds': total_time,
            'avg_time_per_pdf_seconds': avg_time,
            'throughput_pdfs_per_second': (
                len(results) / total_time if total_time > 0 else 0
            )
        }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Uso: python parallel_processor.py <dir_com_pdfs>")
        sys.exit(1)

    pdf_dir = Path(sys.argv[1])

    if not pdf_dir.exists():
        print(f"Diretório não encontrado: {pdf_dir}")
        sys.exit(1)

    # Listar PDFs
    pdf_paths = list(pdf_dir.glob("*.pdf"))

    if not pdf_paths:
        print(f"Nenhum PDF encontrado em {pdf_dir}")
        sys.exit(1)

    print(f"\nEncontrados {len(pdf_paths)} PDFs")

    # Simular função de filtro (mock)
    def mock_filter_func(pdf_path, target_oabs, min_score, use_cache):
        """Mock filter function para teste."""
        import time
        import random

        # Simular processamento
        time.sleep(random.uniform(0.1, 0.5))

        # Simular matches aleatórios
        num_matches = random.randint(0, 3)

        matches = [
            {
                'pdf': str(pdf_path),
                'oab': f"{random.randint(100000, 999999)}/SP",
                'score': random.uniform(0.5, 1.0)
            }
            for _ in range(num_matches)
        ]

        return matches

    # OABs de interesse (mock)
    target_oabs = [
        ('123456', 'SP'),
        ('789012', 'RJ'),
    ]

    # Criar processor
    processor = ParallelProcessor(
        max_workers=4,
        show_progress=True
    )

    # Processar
    print("\nIniciando processamento paralelo...\n")

    matches, results = processor.process_batch(
        pdf_paths=pdf_paths[:10],  # Processar apenas 10 para teste
        target_oabs=target_oabs,
        filter_func=mock_filter_func,
        min_score=0.5
    )

    # Estatísticas
    print("\n" + "=" * 70)
    print("ESTATÍSTICAS DE PROCESSAMENTO")
    print("=" * 70)

    stats = processor.get_processing_stats(results)

    print(f"PDFs processados: {stats['successful']}/{stats['total_pdfs']}")
    print(f"Taxa de sucesso: {stats['success_rate']:.1%}")
    print(f"Matches encontrados: {stats['total_matches']}")
    print(f"Média de matches/PDF: {stats['avg_matches_per_pdf']:.1f}")
    print(f"Tempo total: {stats['total_processing_time_seconds']:.1f}s")
    print(f"Tempo médio/PDF: {stats['avg_time_per_pdf_seconds']:.2f}s")
    print(f"Throughput: {stats['throughput_pdfs_per_second']:.1f} PDFs/s")
