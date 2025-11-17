"""
Test suite para djen-tracker.

Esta suite contém testes unitários, de integração e end-to-end para
garantir qualidade e robustez do sistema.

Estrutura:
- test_tribunais.py: Testes para módulo de tribunais
- test_path_utils.py: Testes para utilitários de path
- test_oab_matcher.py: Testes para matcher de OAB (CRÍTICO)
- test_pdf_text_extractor.py: Testes para extração de PDF
- test_cache_manager.py: Testes para gerenciador de cache
- test_result_exporter.py: Testes para exportador de resultados
- test_integration.py: Testes end-to-end

Executar:
    pytest tests/                    # Todos testes
    pytest tests/ -v                 # Verbose
    pytest tests/ --cov=src          # Com cobertura
    pytest tests/ -m "not slow"      # Sem testes lentos
"""
