"""
Downloader especializado para dataset de integras do STJ.

Baixa pares de (ZIP textos + JSON metadados), extrai textos,
e persiste progresso para retomada de downloads interrompidos.
"""
from __future__ import annotations

import hashlib
import json
import logging
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx
from rich.console import Console
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TimeRemainingColumn, DownloadColumn, TransferSpeedColumn,
)
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
console = Console()

# Timeout maior para ZIPs grandes (consolidados podem ter ~250 MB)
INTEGRAS_TIMEOUT = 120  # seconds
CHUNK_SIZE = 65536  # 64 KB for streaming downloads


class DownloadProgress:
    """Persiste progresso de download em JSON para retomada."""

    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self._completed: set[str] = set()
        if progress_file.exists():
            self.load()

    def mark_completed(self, resource_name: str):
        """Marca resource como completado."""
        self._completed.add(resource_name)
        self.save()

    def is_completed(self, resource_name: str) -> bool:
        """Verifica se resource ja foi completado."""
        return resource_name in self._completed

    def save(self):
        """Persiste progresso em disco."""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump({
                'completed': sorted(self._completed),
            }, f, indent=2)

    def load(self):
        """Carrega progresso do disco."""
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                self._completed = set(data.get('completed', []))
        except (json.JSONDecodeError, FileNotFoundError):
            self._completed = set()

    @property
    def total_completed(self) -> int:
        return len(self._completed)


class IntegrasDownloader:
    """
    Downloader especializado para dataset de integras do STJ.

    Baixa pares (ZIP textos + JSON metadados), extrai textos,
    e persiste progresso para retomada.
    """

    def __init__(
        self,
        staging_dir: Path,
        textos_dir: Path,
        metadata_dir: Path,
        progress_file: Path,
    ):
        self.staging_dir = staging_dir
        self.textos_dir = textos_dir
        self.metadata_dir = metadata_dir
        self.progress = DownloadProgress(progress_file)
        self.client = httpx.Client(timeout=INTEGRAS_TIMEOUT, follow_redirects=True)

        # Stats
        self.downloaded_zips = 0
        self.downloaded_jsons = 0
        self.extracted_files = 0
        self.skipped = 0
        self.errors = 0

    def close(self):
        """Fecha cliente HTTP."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=60),
    )
    def download_resource(self, url: str, dest: Path, force: bool = False) -> Path:
        """
        Download de um resource (ZIP ou JSON) com retry e streaming.
        """
        if dest.exists() and not force:
            logger.debug(f"Ja existe, pulando: {dest.name}")
            self.skipped += 1
            return dest

        dest.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Baixando: {url} -> {dest.name}")

        with self.client.stream("GET", url) as response:
            response.raise_for_status()
            with open(dest, 'wb') as f:
                for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                    f.write(chunk)

        return dest

    def extract_zip(self, zip_path: Path, dest_dir: Path) -> list[Path]:
        """
        Extrai textos (.txt) de um ZIP para diretorio organizado.
        Ignora arquivos que nao sao .txt.
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        extracted = []

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.namelist():
                if member.endswith('.txt'):
                    # Extrair apenas o arquivo, sem subdiretorio do ZIP
                    filename = Path(member).name
                    target = dest_dir / filename
                    with zf.open(member) as src, open(target, 'wb') as dst:
                        dst.write(src.read())
                    extracted.append(target)

        self.extracted_files += len(extracted)
        return extracted

    def validate_zip_integrity(self, zip_path: Path) -> bool:
        """Verifica se ZIP nao esta corrompido."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                bad = zf.testzip()
                if bad is not None:
                    logger.error(f"ZIP corrompido em: {bad}")
                    return False
            return True
        except (zipfile.BadZipFile, Exception) as e:
            logger.error(f"ZIP invalido {zip_path}: {e}")
            return False

    def download_pair(
        self,
        zip_url: str,
        zip_name: str,
        meta_url: str,
        meta_name: str,
        date_key: str,
        force: bool = False,
    ) -> tuple[list[Path], list[dict]]:
        """
        Baixa par (ZIP + JSON), extrai textos, carrega metadados.
        Retorna (lista_txts, lista_metadados).
        """
        # Download ZIP
        zip_path = self.staging_dir / zip_name
        self.download_resource(zip_url, zip_path, force)
        self.downloaded_zips += 1

        # Validar ZIP
        if not self.validate_zip_integrity(zip_path):
            logger.error(f"ZIP corrompido, re-baixando: {zip_name}")
            zip_path.unlink(missing_ok=True)
            self.download_resource(zip_url, zip_path, force=True)
            if not self.validate_zip_integrity(zip_path):
                raise ValueError(f"ZIP corrompido apos re-download: {zip_name}")

        # Extrair textos
        dest_dir = self.textos_dir / date_key
        txts = self.extract_zip(zip_path, dest_dir)

        # Download JSON de metadados
        meta_path = self.metadata_dir / meta_name
        self.download_resource(meta_url, meta_path, force)
        self.downloaded_jsons += 1

        # Carregar metadados
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadados = json.load(f)
        if not isinstance(metadados, list):
            metadados = [metadados]

        return txts, metadados

    def download_all(
        self,
        pairs: list[dict],
        force: bool = False,
    ) -> dict:
        """
        Download retroativo completo com barra de progresso.
        Persiste progresso a cada par completado.

        pairs: lista de dicts com keys: zip_url, zip_name, meta_url, meta_name, date_key
        """
        total = len(pairs)
        completed = 0
        skipped = 0
        errors = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Baixando {total} pares (ZIP+JSON)...",
                total=total,
            )

            for pair in pairs:
                date_key = pair["date_key"]

                if self.progress.is_completed(date_key) and not force:
                    skipped += 1
                    progress.update(task, advance=1)
                    continue

                try:
                    self.download_pair(
                        zip_url=pair["zip_url"],
                        zip_name=pair["zip_name"],
                        meta_url=pair["meta_url"],
                        meta_name=pair["meta_name"],
                        date_key=date_key,
                        force=force,
                    )
                    self.progress.mark_completed(date_key)
                    completed += 1
                except Exception as e:
                    logger.error(f"Erro no par {date_key}: {e}")
                    errors += 1

                progress.update(task, advance=1)

        return {
            "total": total,
            "completed": completed,
            "skipped": skipped,
            "errors": errors,
        }
