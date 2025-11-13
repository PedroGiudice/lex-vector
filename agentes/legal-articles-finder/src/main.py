#!/usr/bin/env python3
"""
Legal Articles Finder - Agente de Análise e Extração de Artigos Legais

Identifica citações legais em documentos e extrai artigos completos de um corpus local.

Uso:
    python main.py analyze <documento.txt> [--output analise.md] [--format json|markdown]
    python main.py search <LEI> <ARTIGO> [ex: CF 5]
    python main.py index <CODE> <NOME> <ARQUIVO> [ANO]
    python main.py stats
"""
import argparse
import sys
from pathlib import Path

from analyzer import DocumentAnalyzer
from corpus_indexer import CorpusIndexer
from citation_parser import CitationParser


def main():
    """CLI principal."""
    parser = argparse.ArgumentParser(
        description="Legal Articles Finder - Análise e Extração de Artigos Legais",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--corpus-db',
        type=Path,
        default=Path(__file__).parent.parent / "corpus" / "index.db",
        help="Caminho do banco de dados do corpus"
    )

    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')

    # Comando: analyze
    analyze_parser = subparsers.add_parser('analyze', help='Analisa documento jurídico')
    analyze_parser.add_argument('document', type=Path, help='Documento para analisar (TXT, MD ou JSON)')
    analyze_parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Arquivo de saída (default: stdout)'
    )
    analyze_parser.add_argument(
        '-f', '--format',
        choices=['json', 'markdown'],
        default='markdown',
        help='Formato de saída'
    )
    analyze_parser.add_argument(
        '--no-deduplicate',
        action='store_true',
        help='Não remover citações duplicadas'
    )

    # Comando: search
    search_parser = subparsers.add_parser('search', help='Busca artigo específico no corpus')
    search_parser.add_argument('law_code', help='Código da lei (ex: CF, CC, CPC)')
    search_parser.add_argument('article', help='Número do artigo (ex: 5, 121)')

    # Comando: index
    index_parser = subparsers.add_parser('index', help='Indexa nova lei no corpus')
    index_parser.add_argument('code', help='Código da lei (ex: CF, CC)')
    index_parser.add_argument('name', help='Nome completo da lei')
    index_parser.add_argument('file', type=Path, help='Arquivo TXT com texto da lei')
    index_parser.add_argument('year', type=int, nargs='?', help='Ano da lei (opcional)')

    # Comando: stats
    subparsers.add_parser('stats', help='Mostra estatísticas do corpus')

    # Comando: test
    test_parser = subparsers.add_parser('test', help='Testa parser de citações com texto')
    test_parser.add_argument('text', help='Texto para analisar')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Executar comando
    try:
        if args.command == 'analyze':
            cmd_analyze(args)
        elif args.command == 'search':
            cmd_search(args)
        elif args.command == 'index':
            cmd_index(args)
        elif args.command == 'stats':
            cmd_stats(args)
        elif args.command == 'test':
            cmd_test(args)
    except Exception as e:
        print(f"❌ Erro: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_analyze(args):
    """Comando: analyze"""
    print(f"⚖️  Analisando: {args.document}")
    print(f"📋 Formato: {args.format}\n")

    analyzer = DocumentAnalyzer(args.corpus_db)

    result = analyzer.analyze(
        args.document,
        deduplicate=not args.no_deduplicate,
        output_format=args.format
    )

    # Gerar output
    if args.format == 'markdown':
        output_text = result.to_markdown()
    else:
        output_text = result.to_json()

    # Escrever resultado
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"✅ Análise salva em: {args.output}")
    else:
        print(output_text)


def cmd_search(args):
    """Comando: search"""
    indexer = CorpusIndexer(args.corpus_db)

    print(f"🔍 Buscando: {args.law_code.upper()} art. {args.article}\n")

    article = indexer.find_article(args.law_code, args.article)

    if not article:
        print(f"❌ Artigo não encontrado no corpus")
        sys.exit(1)

    # Exibir artigo
    print(f"✅ Artigo encontrado:\n")
    print(f"**Art. {article.number}**\n")
    print(article.caput)
    print()

    if article.paragraphs:
        print("**Parágrafos:**\n")
        for i, para in enumerate(article.paragraphs, 1):
            print(f"§{i}º {para}\n")


def cmd_index(args):
    """Comando: index"""
    indexer = CorpusIndexer(args.corpus_db)

    print(f"📚 Indexando: {args.code} - {args.name}")
    print(f"📄 Arquivo: {args.file}")
    if args.year:
        print(f"📅 Ano: {args.year}")
    print()

    law_id = indexer.index_law(
        code=args.code,
        name=args.name,
        file_path=args.file,
        year=args.year
    )

    print(f"\n✅ Lei indexada com sucesso (ID: {law_id})")


def cmd_stats(args):
    """Comando: stats"""
    indexer = CorpusIndexer(args.corpus_db)

    stats = indexer.get_law_stats()

    print("📊 Estatísticas do Corpus\n")
    print(f"**Total de leis:** {stats['total_laws']}")
    print(f"**Total de artigos:** {stats['total_articles']}\n")

    if stats['laws']:
        print("📖 Leis Indexadas:\n")
        for law in stats['laws']:
            print(f"• **{law['code']}**: {law['name']}")
            print(f"  Artigos: {law['articles']}\n")
    else:
        print("⚠️  Nenhuma lei indexada ainda.")
        print("\nPara indexar uma lei:")
        print("  python main.py index <CODE> <NAME> <FILE> [YEAR]")


def cmd_test(args):
    """Comando: test"""
    parser = CitationParser()

    print(f"🔍 Analisando texto:\n")
    print(f'"{args.text}"\n')
    print("=" * 60)
    print()

    citations = parser.parse(args.text)

    if not citations:
        print("❌ Nenhuma citação encontrada")
        sys.exit(0)

    print(f"📋 {len(citations)} citação(ões) encontrada(s):\n")

    for i, citation in enumerate(citations, 1):
        print(f"{i}. {citation}")
        print(f"   Raw: '{citation.raw_text}'")

        if citation.law_code:
            law_name = parser.get_law_name(citation.law_code)
            print(f"   Lei: {law_name}")

        print(f"   Artigo: {citation.article}")

        if citation.paragraph:
            print(f"   Parágrafo: §{citation.paragraph}")
        if citation.inciso:
            print(f"   Inciso: {citation.inciso}")
        if citation.alinea:
            print(f"   Alínea: {citation.alinea}")

        print()


if __name__ == "__main__":
    main()
