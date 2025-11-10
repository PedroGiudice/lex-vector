"""
DJEN Tracker - Main Entry Point
"""
import json
import logging
import sys
from pathlib import Path

from src import ContinuousDownloader


def configurar_logging(config: dict):
    """Configura logging."""
    log_level = logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))

    # File handler
    data_root = Path(config['paths']['data_root'])
    logs_dir = data_root / config['paths']['logs']
    logs_dir.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    log_file = logs_dir / f"djen_tracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def main():
    """Entry point."""
    # Carregar configuração
    config_path = Path(__file__).parent / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Configurar logging
    configurar_logging(config)
    logger = logging.getLogger(__name__)

    logger.info("="*70)
    logger.info("DJEN TRACKER v1.0 - Monitor Contínuo de Cadernos")
    logger.info("="*70)

    # Criar downloader
    downloader = ContinuousDownloader(config)

    # Menu
    print("\n" + "="*70)
    print("DJEN TRACKER - Opções de Execução")
    print("="*70)
    print("1. Download contínuo (loop infinito)")
    print("2. Download de hoje (execução única)")
    print("3. Download de data específica")
    print("0. Sair")
    print("-"*70)

    opcao = input("\nEscolha uma opção: ").strip()

    if opcao == '1':
        intervalo = input("Intervalo entre ciclos (minutos) [30]: ").strip()
        intervalo = int(intervalo) if intervalo else 30
        print(f"\nIniciando download contínuo (intervalo: {intervalo}min)")
        print("Pressione Ctrl+C para interromper\n")
        downloader.run_continuous(intervalo_minutos=intervalo)

    elif opcao == '2':
        print("\nExecutando download de hoje...")
        downloader.run_once()
        print("\nDownload concluído!")

    elif opcao == '3':
        data = input("Data (YYYY-MM-DD): ").strip()
        print(f"\nExecutando download de {data}...")
        downloader.run_once(data=data)
        print("\nDownload concluído!")

    elif opcao == '0':
        print("\nEncerrando...")
        sys.exit(0)

    else:
        print("\nOpção inválida!")
        sys.exit(1)


if __name__ == "__main__":
    main()
