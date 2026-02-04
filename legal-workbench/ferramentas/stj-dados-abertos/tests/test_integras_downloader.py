"""Tests for IntegrasDownloader."""
import json
import zipfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.integras_downloader import IntegrasDownloader, DownloadProgress


class TestDownloadProgress:
    def test_create_empty(self, tmp_path):
        """Progresso vazio inicial."""
        progress_file = tmp_path / ".progress.json"
        progress = DownloadProgress(progress_file)
        assert not progress.is_completed("test.zip")

    def test_mark_completed(self, tmp_path):
        """Marcar resource como completado."""
        progress_file = tmp_path / ".progress.json"
        progress = DownloadProgress(progress_file)
        progress.mark_completed("20260122.zip")
        assert progress.is_completed("20260122.zip")
        assert not progress.is_completed("20260121.zip")

    def test_persist_and_load(self, tmp_path):
        """Progresso deve persistir em disco."""
        progress_file = tmp_path / ".progress.json"

        # Salvar
        progress1 = DownloadProgress(progress_file)
        progress1.mark_completed("20260122.zip")
        progress1.mark_completed("20260121.zip")
        progress1.save()

        # Carregar em nova instancia
        progress2 = DownloadProgress(progress_file)
        progress2.load()
        assert progress2.is_completed("20260122.zip")
        assert progress2.is_completed("20260121.zip")
        assert not progress2.is_completed("20260120.zip")


class TestIntegrasDownloader:
    @pytest.fixture
    def downloader(self, tmp_path):
        """Fixture com downloader configurado em diretorio temporario."""
        staging = tmp_path / "staging"
        textos = tmp_path / "textos"
        metadata = tmp_path / "metadata"
        progress_file = tmp_path / ".progress.json"
        staging.mkdir()
        textos.mkdir()
        metadata.mkdir()
        return IntegrasDownloader(staging, textos, metadata, progress_file)

    def test_validate_zip_integrity_valid(self, downloader, tmp_path):
        """ZIP valido deve passar validacao."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("12345.txt", "Conteudo de teste")
        assert downloader.validate_zip_integrity(zip_path) is True

    def test_validate_zip_integrity_invalid(self, downloader, tmp_path):
        """Arquivo corrompido deve falhar."""
        bad_path = tmp_path / "bad.zip"
        bad_path.write_bytes(b"not a zip file")
        assert downloader.validate_zip_integrity(bad_path) is False

    def test_extract_zip(self, downloader, tmp_path):
        """Testa extracao de textos do ZIP."""
        # Criar ZIP com arquivos de texto
        zip_path = tmp_path / "staging" / "20260122.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("111.txt", "<br>Texto do documento 111")
            zf.writestr("222.txt", "<p>Texto do documento 222</p>")
            zf.writestr("333.txt", "Texto simples 333")

        dest_dir = tmp_path / "textos" / "20260122"
        extracted = downloader.extract_zip(zip_path, dest_dir)

        assert len(extracted) == 3
        assert dest_dir.exists()
        assert (dest_dir / "111.txt").exists()
        assert (dest_dir / "222.txt").exists()
        assert (dest_dir / "333.txt").exists()

    def test_extract_zip_skip_non_txt(self, downloader, tmp_path):
        """Extracao deve ignorar arquivos que nao sao .txt."""
        zip_path = tmp_path / "staging" / "mixed.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("111.txt", "Documento 111")
            zf.writestr("README.md", "Leia-me")
            zf.writestr("data.csv", "col1,col2")

        dest_dir = tmp_path / "textos" / "mixed"
        extracted = downloader.extract_zip(zip_path, dest_dir)

        assert len(extracted) == 1
        assert (dest_dir / "111.txt").exists()
        assert not (dest_dir / "README.md").exists()

    def test_progress_tracking(self, downloader, tmp_path):
        """Testa que progresso e rastreado."""
        assert not downloader.progress.is_completed("20260122")
        downloader.progress.mark_completed("20260122")
        assert downloader.progress.is_completed("20260122")
