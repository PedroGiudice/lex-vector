"""
Downloader para STJ Dados Abertos
Baixa JSONs de acórdãos organizados por órgão julgador e mês
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Final
import httpx
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.console import Console
from tenacity import retry, stop_after_attempt, wait_exponential

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    STAGING_DIR,
    DEFAULT_TIMEOUT,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_DELAY,
    CONCURRENT_DOWNLOADS
)

console = Console()
logger = logging.getLogger(__name__)

# Constants
CHUNK_SIZE: Final[int] = 8192  # For hash computation


@dataclass
class DownloadStats:
    """Statistics for download operations."""
    downloaded: int = 0
    failed: int = 0
    skipped: int = 0
    not_found: int = 0  # 404s tracked separately (expected behavior)


def validate_json_integrity(file_path: Path) -> bool:
    """
    Validate JSON file integrity.

    Checks:
    1. File exists and is not empty
    2. Content is valid JSON
    3. Content is list or dict (expected STJ format)

    Args:
        file_path: Path to JSON file to validate

    Returns:
        True if file is valid, False otherwise
    """
    try:
        # Check file exists
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False

        # Check file is not empty
        if file_path.stat().st_size == 0:
            logger.error(f"File is empty: {file_path}")
            return False

        # Validate JSON content
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if data is list or dict (expected STJ formats)
        if not isinstance(data, (list, dict)):
            logger.error(f"JSON content is neither list nor dict: {file_path}")
            return False

        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating {file_path}: {e}")
        return False


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 hash of file contents.

    Args:
        file_path: Path to file to hash

    Returns:
        Hexadecimal SHA256 hash string
    """
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


class STJDownloader:
    """
    Downloader para arquivos JSON do STJ Dados Abertos.

    Características:
    - Sem rate limiting (STJ não tem limites documentados)
    - Retry automático com backoff exponencial
    - Progress bar para acompanhamento
    - Download paralelo (4 simultâneos por padrão)
    """

    def __init__(self, staging_dir: Optional[Path] = None):
        self.staging_dir = staging_dir or STAGING_DIR
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(timeout=DEFAULT_TIMEOUT)
        self.stats = DownloadStats()
        self._checksums: dict[str, str] = {}  # filename -> sha256 hash

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    @retry(
        stop=stop_after_attempt(DEFAULT_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=DEFAULT_RETRY_DELAY, max=30)
    )
    def download_json(self, url: str, filename: str, force: bool = False) -> Optional[Path]:
        """
        Baixa um arquivo JSON do STJ com validação completa de integridade.

        Args:
            url: URL do arquivo JSON
            filename: Nome do arquivo para salvar
            force: Sobrescrever se já existir

        Returns:
            Path do arquivo baixado ou None se falhou/404
        """
        output_path = self.staging_dir / filename

        # Skip se já existe (a menos que force=True)
        if output_path.exists() and not force:
            logger.info(f"Arquivo já existe, pulando: {filename}")
            self.stats.skipped += 1
            return output_path

        try:
            logger.info(f"Baixando: {url}")
            response = self.client.get(url)

            # Handle 404 as INFO (expected for empty months)
            if response.status_code == 404:
                logger.info(f"Arquivo não encontrado (404): {url} - expected for empty months")
                self.stats.not_found += 1
                return None

            response.raise_for_status()

            # Validate JSON BEFORE saving to disk
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Resposta não é JSON válido de {url}: {e}")
                self.stats.failed += 1
                raise

            # Validate data structure (must be list or dict)
            if not isinstance(data, (list, dict)):
                logger.error(f"JSON content is neither list nor dict from {url}")
                self.stats.failed += 1
                raise ValueError("Invalid JSON structure: expected list or dict")

            # Save to disk
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Validate integrity AFTER saving
            if not validate_json_integrity(output_path):
                logger.error(f"File failed integrity check after save: {filename}")
                output_path.unlink(missing_ok=True)  # Delete corrupted file
                self.stats.failed += 1
                raise ValueError("File failed post-save integrity validation")

            # Compute and store SHA256 checksum
            checksum = compute_sha256(output_path)
            self._checksums[filename] = checksum

            self.stats.downloaded += 1
            record_count = len(data) if isinstance(data, list) else "dict"
            logger.info(f"Baixado com sucesso: {filename} ({record_count} registros, SHA256: {checksum[:8]}...)")
            return output_path

        except httpx.HTTPStatusError as e:
            # Log other HTTP errors (non-404) as ERROR
            logger.error(f"Erro HTTP ao baixar {url}: {e.response.status_code} - {e}")
            self.stats.failed += 1
            raise
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao baixar {url}: {e}")
            self.stats.failed += 1
            raise
        except json.JSONDecodeError as e:
            # Already logged above, just re-raise
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao baixar {url}: {e}")
            self.stats.failed += 1
            raise

    def download_batch(self, url_configs: list[dict], show_progress: bool = True) -> list[Path]:
        """
        Baixa múltiplos arquivos em sequência com progress bar.

        Args:
            url_configs: Lista de dicts com 'url', 'filename'
            show_progress: Mostrar barra de progresso

        Returns:
            Lista de Paths dos arquivos baixados
        """
        downloaded_files = []

        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Baixando {len(url_configs)} arquivos...",
                    total=len(url_configs)
                )

                for config in url_configs:
                    file_path = self.download_json(
                        config["url"],
                        config["filename"],
                        force=config.get("force", False)
                    )
                    if file_path:
                        downloaded_files.append(file_path)
                    progress.update(task, advance=1)
        else:
            for config in url_configs:
                file_path = self.download_json(
                    config["url"],
                    config["filename"],
                    force=config.get("force", False)
                )
                if file_path:
                    downloaded_files.append(file_path)

        return downloaded_files

    def get_checksum(self, filename: str) -> Optional[str]:
        """
        Get SHA256 checksum for a downloaded file.

        Args:
            filename: Name of the file

        Returns:
            SHA256 hash string or None if not found
        """
        return self._checksums.get(filename)

    def get_staging_files(self, pattern: str = "*.json") -> list[Path]:
        """
        Lista arquivos no diretório staging.

        Args:
            pattern: Pattern glob para filtrar arquivos

        Returns:
            Lista de Paths dos arquivos
        """
        return sorted(self.staging_dir.glob(pattern))

    def cleanup_staging(self, days_old: int = 7):
        """
        Remove arquivos antigos do staging.

        Args:
            days_old: Remover arquivos mais velhos que N dias
        """
        cutoff = datetime.now().timestamp() - (days_old * 86400)
        removed = 0

        for file_path in self.staging_dir.glob("*.json"):
            if file_path.stat().st_mtime < cutoff:
                file_path.unlink()
                removed += 1
                logger.info(f"Removido arquivo antigo: {file_path.name}")

        if removed:
            console.print(f"[yellow]Limpeza: {removed} arquivos antigos removidos[/yellow]")

    def print_stats(self):
        """Imprime estatísticas do download."""
        console.print("\n[bold cyan]Estatísticas de Download:[/bold cyan]")
        console.print(f"✅ Baixados: {self.stats.downloaded}")
        console.print(f"⏭️  Pulados: {self.stats.skipped}")
        console.print(f"ℹ️  Não encontrados (404): {self.stats.not_found}")
        console.print(f"❌ Falhas: {self.stats.failed}")


def test_download_single():
    """Teste: baixar um arquivo de exemplo."""
    # Testar com Corte Especial de novembro/2024
    test_url = "https://www.stj.jus.br/sites/portalp/SiteAssets/documentos/noticias/abertos/CorteEspecial/2024/202411.json"

    with STJDownloader() as downloader:
        console.print("[bold green]Teste: Download de arquivo único[/bold green]")
        file_path = downloader.download_json(
            test_url,
            "test_corte_especial_202411.json",
            force=True
        )

        if file_path:
            # Validar conteúdo
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                console.print(f"✅ Arquivo válido com {len(data)} registros")
                if data:
                    console.print(f"Exemplo de campos: {list(data[0].keys())[:5]}...")
        else:
            console.print("[red]❌ Download falhou ou arquivo não existe[/red]")


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Executar teste
    test_download_single()