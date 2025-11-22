#!/usr/bin/env python3
"""
Script para executar download retroativo de publicações.

Uso:
    # Download dos últimos 30 dias (padrão)
    python run_retroativo.py

    # Download de intervalo específico
    python run_retroativo.py --inicio 2025-10-01 --fim 2025-10-31

    # Download apenas do STJ
    python run_retroativo.py --tribunais STJ

    # Download de múltiplos tribunais
    python run_retroativo.py --tribunais STJ,STF,TST
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar src/ ao path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scheduler import baixar_retroativo

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def main():
    parser = argparse.ArgumentParser(
        description='Download retroativo de publicações jurídicas'
    )

    parser.add_argument(
        '--inicio',
        type=str,
        help='Data inicial (YYYY-MM-DD). Padrão: 30 dias atrás'
    )

    parser.add_argument(
        '--fim',
        type=str,
        help='Data final (YYYY-MM-DD). Padrão: ontem'
    )

    parser.add_argument(
        '--tribunais',
        type=str,
        help='Tribunais separados por vírgula (ex: STJ,STF). Padrão: todos prioritários'
    )

    parser.add_argument(
        '--tipos',
        type=str,
        default='Acórdão',
        help='Tipos de publicação separados por vírgula (ex: Acórdão,Sentença). Padrão: Acórdão'
    )

    parser.add_argument(
        '--dias',
        type=int,
        help='Número de dias retroativos (alternativa a --inicio/--fim)'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Confirmar automaticamente sem prompt'
    )

    args = parser.parse_args()

    # Determinar datas
    if args.dias:
        # Modo: últimos N dias
        data_fim = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        data_inicio = (datetime.now() - timedelta(days=args.dias)).strftime('%Y-%m-%d')
    elif args.inicio and args.fim:
        # Modo: intervalo específico
        data_inicio = args.inicio
        data_fim = args.fim
    else:
        # Modo padrão: últimos 30 dias
        data_fim = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        data_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    # Determinar tribunais
    tribunais = None
    if args.tribunais:
        tribunais = [t.strip() for t in args.tribunais.split(',')]

    # Determinar tipos
    tipos_desejados = [t.strip() for t in args.tipos.split(',')]

    # Executar download retroativo
    print(f"\n🚀 INICIANDO DOWNLOAD RETROATIVO")
    print(f"   Período: {data_inicio} até {data_fim}")
    if tribunais:
        print(f"   Tribunais: {', '.join(tribunais)}")
    else:
        print(f"   Tribunais: TODOS (10 prioritários)")
    print(f"   Tipos: {', '.join(tipos_desejados)}")
    print()

    if not args.yes:
        confirmacao = input("Confirma execução? [s/N]: ")
        if confirmacao.lower() != 's':
            print("❌ Cancelado pelo usuário")
            return 1
    else:
        print("✅ Confirmação automática (--yes)")
        print()

    stats = baixar_retroativo(
        data_inicio=data_inicio,
        data_fim=data_fim,
        tribunais=tribunais,
        tipos_desejados=tipos_desejados
    )

    # Relatório final
    print("\n✅ DOWNLOAD RETROATIVO CONCLUÍDO COM SUCESSO!")
    print(f"\n📊 Estatísticas:")
    print(f"   Dias processados: {stats['dias_processados']}/{stats['total_dias']}")
    print(f"   Publicações novas: {stats['total_novas']}")
    print(f"   Publicações duplicadas: {stats['total_duplicadas']}")
    print(f"   Publicações filtradas: {stats['total_filtrados']}")
    print(f"   Erros: {stats['total_erros']}")

    if stats['total_novas'] > 0:
        tempo_total = (stats['fim'] - stats['inicio']).total_seconds()
        print(f"   Tempo total: {tempo_total:.1f}s ({tempo_total/60:.1f} min)")
        print(f"   Taxa: {stats['total_novas']/(tempo_total/60):.1f} publicações/min")

    return 0


if __name__ == '__main__':
    sys.exit(main())
