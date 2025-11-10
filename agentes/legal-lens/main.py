"""
Legal Lens - Menu Principal
Sistema RAG para análise de documentos jurídicos e extração de jurisprudência

Execução: python main.py ou via run_agent.ps1
"""
import json
import logging
from pathlib import Path
from typing import Dict, List
from src.pdf_processor import PDFProcessor
from src.rag_engine import RAGEngine
from src.jurisprudence_extractor import JurisprudenceExtractor
from src.utils import configurar_logging, formatar_tamanho, truncate_text
from datetime import datetime

logger = None


def carregar_config() -> Dict:
    """Carrega configuração de config.json"""
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def menu_principal():
    """Menu principal interativo"""
    print("\n" + "="*70)
    print("LEGAL LENS - Análise RAG de Documentos Jurídicos".center(70))
    print("="*70)
    print("\n📚 INDEXAÇÃO")
    print("  1. Indexar PDFs no vector database")
    print("  2. Indexar PDFs de diretório específico")
    print("  3. Listar documentos indexados")
    print("\n🔍 BUSCA E ANÁLISE")
    print("  4. Busca semântica livre")
    print("  5. Extrair jurisprudência por tema")
    print("  6. Extrair jurisprudência (todos os temas)")
    print("\n📊 RELATÓRIOS")
    print("  7. Estatísticas do vector database")
    print("  8. Relatório de extração de jurisprudência")
    print("\n🛠️  MANUTENÇÃO")
    print("  9. Limpar cache e reindexar")
    print("  10. Resetar vector database")
    print("\n0. Sair")
    print("-"*70)

    return input("\nEscolha uma opção: ").strip()


def menu_indexar_pdfs(config: Dict, pdf_processor: PDFProcessor, rag_engine: RAGEngine):
    """Menu para indexação de PDFs"""
    print("\n" + "-"*70)
    print("INDEXAÇÃO DE DOCUMENTOS".center(70))
    print("-"*70)

    # Buscar PDFs do oab-watcher
    input_dir = Path(config['paths']['input_cadernos'])

    if not input_dir.exists():
        print(f"\n✗ Diretório não encontrado: {input_dir}")
        print("  Certifique-se de que o oab-watcher já baixou alguns cadernos.")
        return

    # Listar PDFs
    pdf_files = list(input_dir.rglob('*.pdf'))

    if not pdf_files:
        print(f"\n✗ Nenhum PDF encontrado em: {input_dir}")
        return

    print(f"\n✓ Encontrados {len(pdf_files)} PDFs")
    print(f"\nTamanho total: {formatar_tamanho(sum(f.stat().st_size for f in pdf_files))}")

    # Confirmar
    resposta = input(f"\nIndexar todos os {len(pdf_files)} PDFs? (s/N): ").strip().lower()

    if resposta != 's':
        print("Operação cancelada.")
        return

    # Processar PDFs
    print("\n" + "="*70)
    print("Processando PDFs...".center(70))
    print("="*70)

    try:
        from tqdm import tqdm

        all_chunks = []

        for pdf_file in tqdm(pdf_files, desc="Processando"):
            try:
                chunks = pdf_processor.process_pdf(pdf_file, method='pdfplumber')
                all_chunks.extend(chunks)
            except Exception as e:
                logger.error(f"Erro ao processar {pdf_file.name}: {e}")

        # Adicionar ao RAG
        print("\nGerando embeddings e indexando...")
        added = rag_engine.add_documents(all_chunks)

        print("\n" + "="*70)
        print("INDEXAÇÃO CONCLUÍDA".center(70))
        print("="*70)
        print(f"\n✓ PDFs processados: {len(pdf_files)}")
        print(f"  Chunks gerados: {len(all_chunks)}")
        print(f"  Chunks indexados: {added}")
        print(f"  Total no DB: {rag_engine.collection.count()}")

    except Exception as e:
        print(f"\n✗ Erro na indexação: {e}")
        logger.error(f"Erro na indexação: {e}", exc_info=True)


def menu_indexar_diretorio(config: Dict, pdf_processor: PDFProcessor, rag_engine: RAGEngine):
    """Menu para indexar PDFs de diretório específico"""
    print("\n" + "-"*70)
    print("INDEXAR DIRETÓRIO ESPECÍFICO".center(70))
    print("-"*70)

    caminho = input("\nCaminho do diretório: ").strip()

    if not caminho:
        print("✗ Caminho não fornecido!")
        return

    dir_path = Path(caminho)

    if not dir_path.exists():
        print(f"✗ Diretório não encontrado: {dir_path}")
        return

    # Buscar PDFs
    pdf_files = list(dir_path.rglob('*.pdf'))

    if not pdf_files:
        print(f"✗ Nenhum PDF encontrado em: {dir_path}")
        return

    print(f"\n✓ Encontrados {len(pdf_files)} PDFs")

    # Processar
    resposta = input(f"\nIndexar {len(pdf_files)} PDFs? (s/N): ").strip().lower()

    if resposta != 's':
        print("Operação cancelada.")
        return

    try:
        all_chunks = pdf_processor.batch_process_pdfs(pdf_files)
        added = rag_engine.add_documents(all_chunks)

        print(f"\n✓ {added} chunks indexados de {len(pdf_files)} PDFs")

    except Exception as e:
        print(f"\n✗ Erro: {e}")
        logger.error(f"Erro ao indexar diretório: {e}", exc_info=True)


def menu_busca_semantica(rag_engine: RAGEngine):
    """Menu para busca semântica livre"""
    print("\n" + "-"*70)
    print("BUSCA SEMÂNTICA".center(70))
    print("-"*70)

    query = input("\nDigite sua consulta: ").strip()

    if not query:
        print("✗ Consulta vazia!")
        return

    top_k = input("Número de resultados (padrão 5): ").strip()
    top_k = int(top_k) if top_k.isdigit() else 5

    # Filtros opcionais
    print("\nFiltros opcionais (Enter para ignorar):")
    tribunal = input("  Tribunal (ex: TJSP): ").strip().upper()

    filter_metadata = None
    if tribunal:
        filter_metadata = {'tribunal': tribunal}

    # Buscar
    print("\n" + "="*70)
    print("Buscando...".center(70))
    print("="*70)

    try:
        results = rag_engine.search(query, top_k=top_k, filter_metadata=filter_metadata)

        if not results:
            print("\n✗ Nenhum resultado encontrado.")
            return

        print(f"\n✓ Encontrados {len(results)} resultados")
        print("\n" + "-"*70)

        for i, result in enumerate(results, 1):
            print(f"\n[{i}] Similaridade: {result['similarity']:.3f}")
            print(f"    Fonte: {result['metadata']['source_file']} (página {result['metadata']['page_number']})")
            print(f"    Tribunal: {result['metadata'].get('tribunal', 'N/A')}")
            print(f"\n    {truncate_text(result['text'], 300)}")
            print("-"*70)

    except Exception as e:
        print(f"\n✗ Erro na busca: {e}")
        logger.error(f"Erro na busca: {e}", exc_info=True)


def menu_extrair_por_tema(config: Dict, extractor: JurisprudenceExtractor):
    """Menu para extração de jurisprudência por tema"""
    print("\n" + "-"*70)
    print("EXTRAÇÃO DE JURISPRUDÊNCIA POR TEMA".center(70))
    print("-"*70)

    # Listar temas disponíveis
    temas = config['extraction']['temas_interesse']

    print("\nTemas disponíveis:")
    for i, tema in enumerate(temas, 1):
        print(f"  {i}. {tema}")

    escolha = input("\nEscolha um tema (número) ou digite um tema personalizado: ").strip()

    if escolha.isdigit():
        idx = int(escolha) - 1
        if 0 <= idx < len(temas):
            tema = temas[idx]
        else:
            print("✗ Opção inválida!")
            return
    else:
        tema = escolha

    top_k = input("Número de resultados (padrão 20): ").strip()
    top_k = int(top_k) if top_k.isdigit() else 20

    # Extrair
    print(f"\n{'='*70}")
    print(f"Extraindo jurisprudência sobre: {tema}".center(70))
    print("="*70)

    try:
        entries = extractor.extract_by_theme(tema, top_k=top_k)

        if not entries:
            print("\n✗ Nenhuma jurisprudência encontrada para este tema.")
            return

        print(f"\n✓ Extraídas {len(entries)} entradas")
        print("\n" + "-"*70)

        # Mostrar primeiras 5
        for i, entry in enumerate(entries[:5], 1):
            print(f"\n[{i}] {entry.tipo_decisao or 'Decisão'} - {entry.tribunal}")
            if entry.numero_processo:
                print(f"    Processo: {entry.numero_processo}")
            print(f"    Data: {entry.data_publicacao}")
            print(f"    Confidence: {entry.confidence:.3f}")
            if entry.ementa:
                print(f"\n    Ementa: {truncate_text(entry.ementa, 200)}")
            print("-"*70)

        if len(entries) > 5:
            print(f"\n  ... e mais {len(entries) - 5} entradas")

        # Salvar
        salvar = input("\nSalvar resultados em JSON? (s/N): ").strip().lower()

        if salvar == 's':
            data_root = Path(config['paths']['data_root'])
            outputs_dir = data_root / config['paths']['outputs']
            outputs_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            tema_slug = tema.replace(' ', '_').lower()
            output_file = outputs_dir / f'jurisprudencia_{tema_slug}_{timestamp}.json'

            extractor.save_to_json(entries, output_file)
            print(f"✓ Salvo em: {output_file}")

    except Exception as e:
        print(f"\n✗ Erro na extração: {e}")
        logger.error(f"Erro na extração: {e}", exc_info=True)


def menu_extrair_todos_temas(config: Dict, extractor: JurisprudenceExtractor):
    """Menu para extração de todos os temas"""
    print("\n" + "-"*70)
    print("EXTRAÇÃO DE TODOS OS TEMAS".center(70))
    print("-"*70)

    top_k = input("Resultados por tema (padrão 10): ").strip()
    top_k = int(top_k) if top_k.isdigit() else 10

    print("\n" + "="*70)
    print("Extraindo jurisprudência para todos os temas...".center(70))
    print("="*70)

    try:
        theme_entries = extractor.extract_all_themes(top_k_per_theme=top_k)

        if not theme_entries:
            print("\n✗ Nenhuma jurisprudência encontrada.")
            return

        # Gerar relatório
        report = extractor.generate_report(theme_entries)

        print("\n" + "="*70)
        print("RELATÓRIO DE EXTRAÇÃO".center(70))
        print("="*70)
        print(f"\nTotal de temas: {report['total_temas']}")
        print(f"Total de entradas: {report['total_entradas']}")
        print(f"\nPeríodo: {report['periodo']['inicio']} a {report['periodo']['fim']}")

        print("\n--- Por Tema ---")
        for tema, stats in report['por_tema'].items():
            print(f"\n  {tema}:")
            print(f"    Total: {stats['total']}")
            print(f"    Com processo: {stats['com_processo']}")
            print(f"    Confidence média: {stats['confidence_media']:.3f}")

        print("\n--- Tribunais ---")
        for tribunal, count in sorted(report['tribunais'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {tribunal}: {count}")

        # Salvar
        salvar = input("\nSalvar resultados completos em JSON? (s/N): ").strip().lower()

        if salvar == 's':
            data_root = Path(config['paths']['data_root'])
            outputs_dir = data_root / config['paths']['outputs']
            outputs_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Salvar por tema
            for tema, entries in theme_entries.items():
                tema_slug = tema.replace(' ', '_').lower()
                output_file = outputs_dir / f'jurisprudencia_{tema_slug}_{timestamp}.json'
                extractor.save_to_json(entries, output_file)

            # Salvar relatório
            report_file = outputs_dir / f'relatorio_completo_{timestamp}.json'
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n✓ Arquivos salvos em: {outputs_dir}")

    except Exception as e:
        print(f"\n✗ Erro na extração: {e}")
        logger.error(f"Erro na extração: {e}", exc_info=True)


def menu_estatisticas(rag_engine: RAGEngine):
    """Menu para estatísticas do vector database"""
    print("\n" + "-"*70)
    print("ESTATÍSTICAS DO VECTOR DATABASE".center(70))
    print("-"*70)

    try:
        stats = rag_engine.get_collection_stats()

        print(f"\n✓ Collection: {stats['collection_name']}")
        print(f"  Modelo de embeddings: {stats['embedding_model']}")
        print(f"\n  Total de documentos: {stats['total_documents']}")
        print(f"  Tribunais únicos: {stats['tribunais_unicos']}")
        print(f"  Tribunais: {', '.join(stats['tribunais']) if stats['tribunais'] else 'N/A'}")
        print(f"\n  Datas únicas: {stats['datas_unicas']}")
        print(f"  Período: {stats['periodo']}")

    except Exception as e:
        print(f"\n✗ Erro ao obter estatísticas: {e}")
        logger.error(f"Erro ao obter estatísticas: {e}", exc_info=True)


def menu_resetar_db(rag_engine: RAGEngine):
    """Menu para resetar vector database"""
    print("\n" + "-"*70)
    print("RESETAR VECTOR DATABASE".center(70))
    print("-"*70)

    print("\n⚠️  ATENÇÃO: Esta operação apagará TODOS os documentos indexados!")
    confirmacao = input("\nDigite 'RESETAR' para confirmar: ").strip()

    if confirmacao != 'RESETAR':
        print("Operação cancelada.")
        return

    try:
        rag_engine.reset_collection()
        print("\n✓ Vector database resetado com sucesso.")

    except Exception as e:
        print(f"\n✗ Erro ao resetar: {e}")
        logger.error(f"Erro ao resetar DB: {e}", exc_info=True)


if __name__ == "__main__":
    # Configurar logging
    config = carregar_config()
    logger = configurar_logging(config)

    logger.info("="*70)
    logger.info("Legal Lens iniciado")
    logger.info("="*70)

    # Inicializar componentes
    print("\n⏳ Inicializando Legal Lens...")

    try:
        pdf_processor = PDFProcessor(config)
        rag_engine = RAGEngine(config)
        extractor = JurisprudenceExtractor(config, rag_engine)

        print("✓ Componentes inicializados com sucesso\n")

    except Exception as e:
        print(f"\n✗ Erro ao inicializar: {e}")
        logger.error(f"Erro na inicialização: {e}", exc_info=True)
        exit(1)

    # Loop do menu
    while True:
        try:
            opcao = menu_principal()

            if opcao == '1':
                menu_indexar_pdfs(config, pdf_processor, rag_engine)
            elif opcao == '2':
                menu_indexar_diretorio(config, pdf_processor, rag_engine)
            elif opcao == '3':
                menu_estatisticas(rag_engine)
            elif opcao == '4':
                menu_busca_semantica(rag_engine)
            elif opcao == '5':
                menu_extrair_por_tema(config, extractor)
            elif opcao == '6':
                menu_extrair_todos_temas(config, extractor)
            elif opcao == '7':
                menu_estatisticas(rag_engine)
            elif opcao == '8':
                # Placeholder para relatório de extração
                print("\n⚠️  Funcionalidade em desenvolvimento")
            elif opcao == '9':
                # Placeholder para limpar cache
                print("\n⚠️  Funcionalidade em desenvolvimento")
            elif opcao == '10':
                menu_resetar_db(rag_engine)
            elif opcao == '0':
                print("\nEncerrando Legal Lens...")
                logger.info("Legal Lens encerrado pelo usuário")
                break
            else:
                print("\n✗ Opção inválida! Escolha entre 0-10.")

        except KeyboardInterrupt:
            print("\n\nInterrompido pelo usuário (Ctrl+C)")
            logger.info("Legal Lens interrompido por Ctrl+C")
            break
        except Exception as e:
            logger.error(f"Erro não tratado no menu: {e}", exc_info=True)
            print(f"\n✗ Erro não tratado: {e}")
            print("Verifique os logs para mais detalhes.")
