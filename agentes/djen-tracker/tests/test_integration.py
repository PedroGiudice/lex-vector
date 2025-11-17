"""
Testes de integração end-to-end para djen-tracker.

Testa o fluxo completo:
1. Extração de texto de PDF
2. Cache do texto extraído
3. Detecção de OABs no texto
4. Deduplicação e scoring
5. Exportação de resultados

Marcados como @pytest.mark.integration
"""

import pytest
from pathlib import Path

from src.pdf_text_extractor import PDFTextExtractor
from src.cache_manager import CacheManager
from src.oab_matcher import OABMatcher


@pytest.mark.integration
class TestIntegrationWorkflow:
    """Testes de integração do workflow completo."""

    def test_workflow_completo_sem_cache(
        self,
        sample_pdf_with_oab,
        cache_dir,
        temp_dir
    ):
        """
        Testa workflow completo: PDF -> Extração -> Match OAB
        (sem usar cache)
        """
        # 1. Extrair texto do PDF
        extractor = PDFTextExtractor()
        extraction_result = extractor.extract(sample_pdf_with_oab)

        assert extraction_result.success is True
        assert len(extraction_result.text) > 0

        # 2. Buscar OABs no texto
        matcher = OABMatcher()
        matches = matcher.find_all(extraction_result.text, min_score=0.0)

        # Deve encontrar pelo menos algumas OABs
        assert len(matches) > 0

        # 3. Verificar que matches são válidos
        for match in matches:
            assert len(match.numero) >= 4
            assert match.uf in matcher.UFS_VALIDAS
            assert 0.0 <= match.score_contexto <= 1.0

    def test_workflow_com_cache(
        self,
        sample_pdf_with_oab,
        cache_dir
    ):
        """
        Testa workflow com cache:
        1ª execução: extrai e cacheia
        2ª execução: recupera do cache
        """
        # Setup
        extractor = PDFTextExtractor()
        cache_manager = CacheManager(cache_dir)
        matcher = OABMatcher()

        # 1ª EXECUÇÃO - SEM CACHE
        # Verificar cache miss
        cached = cache_manager.get(sample_pdf_with_oab)
        assert cached is None

        # Extrair texto
        result1 = extractor.extract(sample_pdf_with_oab)
        assert result1.success is True

        # Salvar no cache
        cache_manager.save(
            pdf_path=sample_pdf_with_oab,
            text=result1.text,
            extraction_strategy=result1.strategy.value,
            page_count=result1.page_count
        )

        # Buscar OABs
        matches1 = matcher.find_all(result1.text, min_score=0.0)

        # 2ª EXECUÇÃO - COM CACHE
        # Recuperar do cache
        cached = cache_manager.get(sample_pdf_with_oab)
        assert cached is not None
        assert cached.text == result1.text

        # Buscar OABs (deve ser idêntico)
        matches2 = matcher.find_all(cached.text, min_score=0.0)

        # Resultados devem ser iguais
        assert len(matches1) == len(matches2)

        # Verificar estatísticas de cache
        stats = cache_manager.get_stats()
        assert stats.hits >= 1
        assert stats.total_entries >= 1

    def test_workflow_filtro_oab_especifico(
        self,
        sample_text_with_oabs,
        cache_dir
    ):
        """
        Testa workflow de filtro por OABs específicas.
        """
        matcher = OABMatcher()

        # Definir OABs alvo
        target_oabs = [
            ('123456', 'SP'),
            ('789012', 'SP'),
        ]

        # Filtrar apenas OABs específicas
        matches = matcher.filter_by_oabs(
            sample_text_with_oabs,
            target_oabs,
            min_score=0.0
        )

        # Deve encontrar exatamente as OABs solicitadas
        assert len(matches) == 2

        oabs_encontradas = {(m.numero, m.uf) for m in matches}
        assert ('123456', 'SP') in oabs_encontradas
        assert ('789012', 'SP') in oabs_encontradas

        # Não deve ter outras OABs
        assert len(oabs_encontradas) == 2

    def test_workflow_performance(
        self,
        sample_text_with_oabs,
        cache_dir
    ):
        """
        Testa performance do workflow completo.
        """
        import time

        matcher = OABMatcher()
        cache_manager = CacheManager(cache_dir)

        # Medir tempo de processamento
        start = time.time()

        # Processar texto (sem PDF para ser mais rápido)
        matches = matcher.find_all(sample_text_with_oabs, min_score=0.3)

        duration = time.time() - start

        # Deve processar em menos de 1 segundo
        assert duration < 1.0

        # Deve encontrar OABs
        assert len(matches) > 0


@pytest.mark.integration
class TestIntegrationEdgeCases:
    """Testes de integração para edge cases."""

    def test_pdf_sem_oabs(self, sample_pdf_path):
        """
        Workflow com PDF que não contém OABs.
        """
        extractor = PDFTextExtractor()
        matcher = OABMatcher()

        # Extrair texto
        result = extractor.extract(sample_pdf_path)

        if result.success:
            # Buscar OABs
            matches = matcher.find_all(result.text, min_score=0.3)

            # Pode ou não ter OABs (depende do conteúdo do PDF de teste)
            # O importante é não crashar
            assert isinstance(matches, list)

    def test_texto_vazio(self):
        """
        Workflow com texto vazio.
        """
        matcher = OABMatcher()

        matches = matcher.find_all("", min_score=0.0)

        # Deve retornar lista vazia sem erros
        assert matches == []

    def test_multiplos_pdfs_sequencial(
        self,
        sample_pdf_with_oab,
        cache_dir,
        temp_dir
    ):
        """
        Processa múltiplos PDFs sequencialmente.
        """
        extractor = PDFTextExtractor()
        cache_manager = CacheManager(cache_dir)
        matcher = OABMatcher()

        # Processar mesmo PDF 3 vezes
        all_matches = []

        for i in range(3):
            # Verificar cache
            cached = cache_manager.get(sample_pdf_with_oab)

            if cached:
                text = cached.text
            else:
                result = extractor.extract(sample_pdf_with_oab)
                text = result.text
                cache_manager.save(
                    sample_pdf_with_oab,
                    text,
                    "pdfplumber",
                    10
                )

            # Buscar OABs
            matches = matcher.find_all(text, min_score=0.0)
            all_matches.append(matches)

        # Todos devem ter encontrado mesmo número de OABs
        assert len(all_matches[0]) == len(all_matches[1]) == len(all_matches[2])

        # Cache deve ter sido usado
        stats = cache_manager.get_stats()
        assert stats.hits >= 2  # 2ª e 3ª execução usaram cache


@pytest.mark.integration
class TestIntegrationRealScenario:
    """Testes simulando cenário real de uso."""

    def test_cenario_monitoramento_diario(
        self,
        sample_text_with_oabs,
        cache_dir
    ):
        """
        Simula cenário real:
        - Advogado monitora OABs específicas
        - Processa publicações diárias
        - Filtra apenas publicações relevantes
        """
        # Setup
        matcher = OABMatcher()

        # OABs do escritório
        oabs_escritorio = [
            ('123456', 'SP'),
            ('789012', 'SP'),
            ('345678', 'RJ'),
        ]

        # Processar "publicação diária"
        matches = matcher.filter_by_oabs(
            sample_text_with_oabs,
            oabs_escritorio,
            min_score=0.4  # Score mínimo para evitar falsos positivos
        )

        # Deve encontrar apenas OABs do escritório
        oabs_encontradas = {(m.numero, m.uf) for m in matches}

        for oab in oabs_encontradas:
            assert oab in oabs_escritorio

        # Cada match deve ter contexto útil
        for match in matches:
            assert len(match.texto_contexto) > 50
            assert match.score_contexto >= 0.4

    def test_cenario_relatorio_mensal(
        self,
        sample_text_with_oabs
    ):
        """
        Simula geração de relatório mensal:
        - Encontra todas OABs
        - Ordena por score
        - Agrupa por UF
        """
        matcher = OABMatcher()

        # Encontrar todas OABs
        all_matches = matcher.find_all(
            sample_text_with_oabs,
            min_score=0.3,
            deduplicate=True
        )

        # Agrupar por UF
        por_uf = {}
        for match in all_matches:
            if match.uf not in por_uf:
                por_uf[match.uf] = []
            por_uf[match.uf].append(match)

        # Verificar agrupamento
        assert len(por_uf) > 0

        for uf, matches in por_uf.items():
            assert uf in matcher.UFS_VALIDAS
            assert len(matches) > 0

            # Dentro de cada UF, deve estar ordenado por score
            scores = [m.score_contexto for m in matches]
            assert scores == sorted(scores, reverse=True)


@pytest.mark.integration
@pytest.mark.slow
class TestIntegrationStress:
    """Testes de stress/performance."""

    def test_processar_texto_grande(self):
        """
        Processa texto grande (simulando caderno completo).
        """
        matcher = OABMatcher()

        # Criar texto grande (10.000 linhas)
        linhas = []
        for i in range(10000):
            if i % 100 == 0:
                # A cada 100 linhas, inserir uma OAB
                linhas.append(f"Advogado OAB/SP {100000 + i} intimado")
            else:
                linhas.append(f"Linha {i} com texto genérico")

        texto_grande = "\n".join(linhas)

        import time
        start = time.time()

        # Processar
        matches = matcher.find_all(texto_grande, min_score=0.3)

        duration = time.time() - start

        # Deve processar em tempo razoável (< 10 segundos)
        assert duration < 10.0

        # Deve ter encontrado OABs (deduplicadas)
        assert len(matches) > 0

    def test_cache_multiplos_arquivos(self, cache_dir, temp_dir):
        """
        Testa cache com múltiplos arquivos.
        """
        cache_manager = CacheManager(cache_dir, compress=True)

        # Criar e cachear 10 "PDFs" simulados
        for i in range(10):
            fake_pdf = temp_dir / f"test_{i}.pdf"
            fake_pdf.write_bytes(b"%PDF-1.4\nContent %d\n%%EOF" % i)

            cache_manager.save(
                fake_pdf,
                f"Texto do arquivo {i}",
                "pdfplumber",
                1
            )

        # Verificar estatísticas
        stats = cache_manager.get_stats()
        assert stats.total_entries == 10

        # Recuperar todos (deve gerar 10 hits)
        for i in range(10):
            fake_pdf = temp_dir / f"test_{i}.pdf"
            entry = cache_manager.get(fake_pdf)
            assert entry is not None

        # Verificar hits
        stats = cache_manager.get_stats()
        assert stats.hits == 10
        assert stats.hit_rate == 1.0  # 100% hit rate
