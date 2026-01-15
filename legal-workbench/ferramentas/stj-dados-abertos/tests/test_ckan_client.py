"""Tests for CKAN API client."""
import json
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from ckan_client import CKANClient, CKANResource, CKANPackage


@pytest.fixture
def mock_package_response():
    """Mock CKAN package_show response."""
    return {
        "success": True,
        "result": {
            "id": "espelhos-de-acordaos-primeira-turma",
            "name": "espelhos-de-acordaos-primeira-turma",
            "title": "Espelhos de Acordaos - Primeira Turma",
            "resources": [
                {
                    "id": "res-1",
                    "name": "20241101.json",
                    "url": "https://dadosabertos.web.stj.jus.br/dataset/xxx/resource/yyy/download/20241101.json",
                    "format": "JSON",
                    "created": "2024-11-05T10:00:00",
                },
                {
                    "id": "res-2",
                    "name": "20241201.json",
                    "url": "https://dadosabertos.web.stj.jus.br/dataset/xxx/resource/zzz/download/20241201.json",
                    "format": "JSON",
                    "created": "2024-12-05T10:00:00",
                },
                {
                    "id": "res-zip",
                    "name": "espelhos_acordaos.zip",
                    "url": "https://dadosabertos.web.stj.jus.br/dataset/xxx/resource/aaa/download/espelhos.zip",
                    "format": "ZIP",
                    "created": "2024-01-01T00:00:00",
                },
            ]
        }
    }


class TestCKANResource:
    """Test CKANResource dataclass."""

    def test_from_dict(self):
        """Should create resource from dict."""
        data = {
            "id": "123",
            "name": "20241101.json",
            "url": "https://example.com/file.json",
            "format": "JSON",
            "created": "2024-11-01T00:00:00",
        }
        resource = CKANResource.from_dict(data)
        assert resource.name == "20241101.json"
        assert resource.format == "JSON"

    def test_is_json(self):
        """Should detect JSON format."""
        json_res = CKANResource(id="1", name="test.json", url="", format="JSON", created="")
        zip_res = CKANResource(id="2", name="test.zip", url="", format="ZIP", created="")
        assert json_res.is_json is True
        assert zip_res.is_json is False

    def test_extract_date(self):
        """Should extract date from filename."""
        res = CKANResource(id="1", name="20241115.json", url="", format="JSON", created="")
        assert res.extract_date() == "2024-11-15"

    def test_extract_date_invalid(self):
        """Invalid filename should return None."""
        res = CKANResource(id="1", name="invalid.json", url="", format="JSON", created="")
        assert res.extract_date() is None


class TestCKANClient:
    """Test CKANClient."""

    @patch("ckan_client.httpx.Client.get")
    def test_get_package(self, mock_get, mock_package_response):
        """Should fetch and parse package metadata."""
        mock_response = Mock()
        mock_response.json.return_value = mock_package_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with CKANClient() as client:
            package = client.get_package("primeira_turma")

        assert package.id == "espelhos-de-acordaos-primeira-turma"
        assert len(package.resources) == 3

    @patch("ckan_client.httpx.Client.get")
    def test_get_json_resources(self, mock_get, mock_package_response):
        """Should filter only JSON resources."""
        mock_response = Mock()
        mock_response.json.return_value = mock_package_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with CKANClient() as client:
            resources = client.get_json_resources("primeira_turma")

        assert len(resources) == 2
        assert all(r.is_json for r in resources)

    @patch("ckan_client.httpx.Client.get")
    def test_get_resources_by_date_range(self, mock_get, mock_package_response):
        """Should filter resources by date range."""
        mock_response = Mock()
        mock_response.json.return_value = mock_package_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with CKANClient() as client:
            # Only December 2024
            resources = client.get_resources_by_date_range(
                "primeira_turma",
                start_date="2024-12-01",
                end_date="2024-12-31"
            )

        assert len(resources) == 1
        assert resources[0].name == "20241201.json"
