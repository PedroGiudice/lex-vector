"""
Tests for downloader.py

Tests integrity checks, 404 handling, and SHA256 computation.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import httpx

import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from downloader import (
    validate_json_integrity,
    compute_sha256,
    DownloadStats,
    STJDownloader,
)


@pytest.fixture
def temp_json_file(tmp_path: Path) -> Path:
    """Create a temporary JSON file for testing."""
    json_file = tmp_path / "test.json"
    data = {"key": "value", "items": [1, 2, 3]}
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return json_file


@pytest.fixture
def empty_file(tmp_path: Path) -> Path:
    """Create an empty file."""
    empty = tmp_path / "empty.json"
    empty.touch()
    return empty


@pytest.fixture
def invalid_json_file(tmp_path: Path) -> Path:
    """Create a file with invalid JSON."""
    invalid = tmp_path / "invalid.json"
    with open(invalid, "w") as f:
        f.write("{ invalid json }")
    return invalid


@pytest.fixture
def non_list_dict_json(tmp_path: Path) -> Path:
    """Create a JSON file with primitive type (not list/dict)."""
    primitive = tmp_path / "primitive.json"
    with open(primitive, "w") as f:
        json.dump(42, f)
    return primitive


class TestValidateJsonIntegrity:
    """Test suite for validate_json_integrity()."""

    def test_valid_dict(self, temp_json_file: Path):
        """Valid JSON dict should pass."""
        assert validate_json_integrity(temp_json_file) is True

    def test_valid_list(self, tmp_path: Path):
        """Valid JSON list should pass."""
        list_file = tmp_path / "list.json"
        with open(list_file, "w") as f:
            json.dump([1, 2, 3], f)
        assert validate_json_integrity(list_file) is True

    def test_nonexistent_file(self, tmp_path: Path):
        """Nonexistent file should fail."""
        fake_file = tmp_path / "nonexistent.json"
        assert validate_json_integrity(fake_file) is False

    def test_empty_file(self, empty_file: Path):
        """Empty file should fail."""
        assert validate_json_integrity(empty_file) is False

    def test_invalid_json(self, invalid_json_file: Path):
        """Invalid JSON should fail."""
        assert validate_json_integrity(invalid_json_file) is False

    def test_primitive_type(self, non_list_dict_json: Path):
        """Primitive JSON type (not list/dict) should fail."""
        assert validate_json_integrity(non_list_dict_json) is False


class TestComputeSha256:
    """Test suite for compute_sha256()."""

    def test_deterministic_hash(self, temp_json_file: Path):
        """Same file should produce same hash."""
        hash1 = compute_sha256(temp_json_file)
        hash2 = compute_sha256(temp_json_file)
        assert hash1 == hash2

    def test_hash_format(self, temp_json_file: Path):
        """Hash should be 64 character hex string."""
        hash_value = compute_sha256(temp_json_file)
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_different_files_different_hash(self, tmp_path: Path):
        """Different files should produce different hashes."""
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"

        with open(file1, "w") as f:
            json.dump({"data": "A"}, f)
        with open(file2, "w") as f:
            json.dump({"data": "B"}, f)

        hash1 = compute_sha256(file1)
        hash2 = compute_sha256(file2)
        assert hash1 != hash2

    def test_large_file_chunked_read(self, tmp_path: Path):
        """Large file should be read in chunks."""
        large_file = tmp_path / "large.json"
        # Create a file larger than chunk size (8192 bytes)
        large_data = {"items": ["x" * 1000 for _ in range(100)]}
        with open(large_file, "w") as f:
            json.dump(large_data, f)

        # Should complete without errors
        hash_value = compute_sha256(large_file)
        assert len(hash_value) == 64


class TestDownloadStats:
    """Test suite for DownloadStats dataclass."""

    def test_default_values(self):
        """Stats should initialize with zeros."""
        stats = DownloadStats()
        assert stats.downloaded == 0
        assert stats.failed == 0
        assert stats.skipped == 0
        assert stats.not_found == 0

    def test_increment_fields(self):
        """Fields should be incrementable."""
        stats = DownloadStats()
        stats.downloaded += 1
        stats.failed += 2
        stats.skipped += 3
        stats.not_found += 4

        assert stats.downloaded == 1
        assert stats.failed == 2
        assert stats.skipped == 3
        assert stats.not_found == 4


class TestSTJDownloader:
    """Test suite for STJDownloader class."""

    @pytest.fixture
    def downloader(self, tmp_path: Path) -> STJDownloader:
        """Create downloader with temporary staging dir."""
        return STJDownloader(staging_dir=tmp_path)

    def test_init_creates_staging_dir(self, tmp_path: Path):
        """Initialization should create staging directory."""
        staging = tmp_path / "staging"
        downloader = STJDownloader(staging_dir=staging)
        assert staging.exists()
        assert staging.is_dir()

    def test_context_manager(self, tmp_path: Path):
        """Should work as context manager."""
        with STJDownloader(staging_dir=tmp_path) as downloader:
            assert downloader.client is not None
        # Client should be closed after exit
        assert downloader.client.is_closed

    def test_get_checksum_not_found(self, downloader: STJDownloader):
        """Getting checksum for non-downloaded file should return None."""
        assert downloader.get_checksum("nonexistent.json") is None

    @patch("downloader.httpx.Client.get")
    def test_download_json_success(
        self,
        mock_get: Mock,
        downloader: STJDownloader,
    ):
        """Successful download should save file and compute checksum."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        mock_get.return_value = mock_response

        result = downloader.download_json(
            "https://example.com/test.json",
            "test.json",
        )

        assert result is not None
        assert result.exists()
        assert downloader.stats.downloaded == 1
        assert downloader.stats.failed == 0

        # Verify checksum was computed
        checksum = downloader.get_checksum("test.json")
        assert checksum is not None
        assert len(checksum) == 64

    @patch("downloader.httpx.Client.get")
    def test_download_json_404_logged_as_info(
        self,
        mock_get: Mock,
        downloader: STJDownloader,
        caplog: pytest.LogCaptureFixture,
    ):
        """404 responses should be logged as INFO, not ERROR."""
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with caplog.at_level(logging.INFO):
            result = downloader.download_json(
                "https://example.com/missing.json",
                "missing.json",
            )

        assert result is None
        assert downloader.stats.not_found == 1
        assert downloader.stats.failed == 0

        # Check log level
        log_records = [r for r in caplog.records if "404" in r.message]
        assert len(log_records) > 0
        assert all(r.levelno == logging.INFO for r in log_records)

    @patch("downloader.httpx.Client.get")
    def test_download_json_500_logged_as_error(
        self,
        mock_get: Mock,
        downloader: STJDownloader,
        caplog: pytest.LogCaptureFixture,
    ):
        """500 responses should be logged as ERROR."""
        # Mock 500 response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=Mock(),
            response=mock_response,
        )
        mock_get.return_value = mock_response

        with caplog.at_level(logging.ERROR):
            # Expect RetryError due to @retry decorator
            with pytest.raises((httpx.HTTPStatusError, Exception)):
                downloader.download_json(
                    "https://example.com/error.json",
                    "error.json",
                )

        # Failed counter should be incremented (once per retry attempt)
        assert downloader.stats.failed >= 1

        # Check ERROR log exists
        error_logs = [r for r in caplog.records if r.levelno == logging.ERROR]
        assert len(error_logs) > 0

    @patch("downloader.httpx.Client.get")
    def test_download_json_invalid_json_response(
        self,
        mock_get: Mock,
        downloader: STJDownloader,
    ):
        """Invalid JSON response should fail and log error."""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        mock_get.return_value = mock_response

        # Expect RetryError or JSONDecodeError
        with pytest.raises((json.JSONDecodeError, Exception)):
            downloader.download_json(
                "https://example.com/invalid.json",
                "invalid.json",
            )

        assert downloader.stats.failed >= 1

    @patch("downloader.httpx.Client.get")
    def test_download_json_invalid_structure(
        self,
        mock_get: Mock,
        downloader: STJDownloader,
    ):
        """JSON with invalid structure (not list/dict) should fail."""
        # Mock response with primitive type
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = "string_value"
        mock_get.return_value = mock_response

        # Expect RetryError or ValueError
        with pytest.raises((ValueError, Exception)):
            downloader.download_json(
                "https://example.com/primitive.json",
                "primitive.json",
            )

        assert downloader.stats.failed >= 1

    @patch("downloader.httpx.Client.get")
    def test_download_json_skip_existing(
        self,
        mock_get: Mock,
        downloader: STJDownloader,
    ):
        """Existing file should be skipped unless force=True."""
        # Create existing file
        existing = downloader.staging_dir / "existing.json"
        with open(existing, "w") as f:
            json.dump({"existing": True}, f)

        # Try to download without force
        result = downloader.download_json(
            "https://example.com/existing.json",
            "existing.json",
            force=False,
        )

        assert result == existing
        assert downloader.stats.skipped == 1
        # Should not make HTTP request
        mock_get.assert_not_called()

    @patch("downloader.httpx.Client.get")
    def test_download_json_force_overwrite(
        self,
        mock_get: Mock,
        downloader: STJDownloader,
    ):
        """Existing file should be overwritten with force=True."""
        # Create existing file
        existing = downloader.staging_dir / "existing.json"
        with open(existing, "w") as f:
            json.dump({"old": True}, f)

        # Mock new response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"new": True}
        mock_get.return_value = mock_response

        # Download with force=True
        result = downloader.download_json(
            "https://example.com/existing.json",
            "existing.json",
            force=True,
        )

        assert result == existing
        assert downloader.stats.downloaded == 1
        assert downloader.stats.skipped == 0

        # Verify content was updated
        with open(existing) as f:
            data = json.load(f)
        assert data == {"new": True}

    @patch("downloader.httpx.Client.get")
    @patch("downloader.validate_json_integrity")
    def test_download_json_fails_post_save_validation(
        self,
        mock_validate: Mock,
        mock_get: Mock,
        downloader: STJDownloader,
    ):
        """Failed post-save validation should delete file and fail."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1}]
        mock_get.return_value = mock_response

        # Mock validation failure
        mock_validate.return_value = False

        # Expect RetryError or ValueError
        with pytest.raises((ValueError, Exception)):
            downloader.download_json(
                "https://example.com/corrupt.json",
                "corrupt.json",
            )

        # File should not exist
        assert not (downloader.staging_dir / "corrupt.json").exists()
        assert downloader.stats.failed >= 1

    def test_get_staging_files(self, downloader: STJDownloader):
        """Should list files in staging directory."""
        # Create test files
        (downloader.staging_dir / "file1.json").touch()
        (downloader.staging_dir / "file2.json").touch()
        (downloader.staging_dir / "file.txt").touch()

        files = downloader.get_staging_files("*.json")
        assert len(files) == 2
        assert all(f.suffix == ".json" for f in files)


class TestSTJDownloaderCKAN:
    """Test STJDownloader with CKAN integration."""

    @pytest.fixture
    def mock_ckan_resources(self):
        """Mock CKAN resources."""
        from ckan_client import CKANResource
        return [
            CKANResource(
                id="1",
                name="20241201.json",
                url="https://dadosabertos.web.stj.jus.br/download/20241201.json",
                format="JSON",
                created="2024-12-05",
            ),
        ]

    @patch("downloader.CKANClient")
    @patch("downloader.httpx.Client.get")
    def test_download_from_ckan(
        self,
        mock_http_get,
        mock_ckan_class,
        mock_ckan_resources,
        tmp_path,
    ):
        """Should download files using CKAN resource URLs."""
        # Setup CKAN mock
        mock_ckan = MagicMock()
        mock_ckan.get_resources_by_date_range.return_value = mock_ckan_resources
        mock_ckan.__enter__ = Mock(return_value=mock_ckan)
        mock_ckan.__exit__ = Mock(return_value=None)
        mock_ckan_class.return_value = mock_ckan

        # Setup HTTP mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "test-acordao"}]
        mock_http_get.return_value = mock_response

        downloader = STJDownloader(staging_dir=tmp_path)
        files = downloader.download_from_ckan(
            orgao="primeira_turma",
            start_date="2024-12-01",
            end_date="2024-12-31"
        )

        assert len(files) == 1
        assert downloader.stats.downloaded == 1

    @patch("downloader.CKANClient")
    def test_download_from_ckan_no_resources(
        self,
        mock_ckan_class,
        tmp_path,
    ):
        """Should handle empty resource list gracefully."""
        mock_ckan = MagicMock()
        mock_ckan.get_resources_by_date_range.return_value = []
        mock_ckan.__enter__ = Mock(return_value=mock_ckan)
        mock_ckan.__exit__ = Mock(return_value=None)
        mock_ckan_class.return_value = mock_ckan

        downloader = STJDownloader(staging_dir=tmp_path)
        files = downloader.download_from_ckan(
            orgao="primeira_turma",
            start_date="2024-12-01",
            end_date="2024-12-31"
        )

        assert len(files) == 0
