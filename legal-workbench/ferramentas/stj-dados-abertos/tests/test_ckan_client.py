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


# ===========================================================================
# Testes para integras
# ===========================================================================

class TestCKANResourceIntegras:
    """Testes de extract_date para ZIPs e metadados de integras."""

    def test_extract_date_from_daily_zip(self):
        """ZIP diario: 20260122.zip -> 2026-01-22."""
        r = CKANResource(id="1", name="20260122.zip", url="", format="ZIP", created="")
        assert r.extract_date() == "2026-01-22"

    def test_extract_date_from_monthly_zip(self):
        """ZIP mensal: 202203.zip -> extract_date_monthly -> 2022-03."""
        r = CKANResource(id="2", name="202203.zip", url="", format="ZIP", created="")
        assert r.extract_date_monthly() == "2022-03"

    def test_extract_date_from_daily_metadados(self):
        """Metadados diario: metadados20260122.json -> 2026-01-22."""
        r = CKANResource(id="3", name="metadados20260122.json", url="", format="JSON", created="")
        assert r.extract_date() == "2026-01-22"

    def test_extract_date_from_monthly_metadados(self):
        """Metadados mensal: metadados202203.json -> extract_date_monthly -> 2022-03."""
        r = CKANResource(id="4", name="metadados202203.json", url="", format="JSON", created="")
        assert r.extract_date_monthly() == "2022-03"

    def test_extract_date_monthly_returns_none_for_daily(self):
        """ZIP diario nao tem date_monthly."""
        r = CKANResource(id="5", name="20260122.zip", url="", format="ZIP", created="")
        assert r.extract_date_monthly() is None

    def test_extract_date_returns_none_for_monthly(self):
        """ZIP mensal nao tem extract_date (8 digitos)."""
        r = CKANResource(id="6", name="202203.zip", url="", format="ZIP", created="")
        assert r.extract_date() is None

    def test_is_csv(self):
        """CSVs nao sao ZIP nem JSON mas devem ser detectados."""
        r = CKANResource(id="7", name="dados.csv", url="", format="CSV", created="")
        assert r.is_csv is True
        assert r.is_zip is False
        assert r.is_json is False


@pytest.fixture
def mock_integras_package_response():
    """Mock CKAN package_show response para integras."""
    return {
        "success": True,
        "result": {
            "id": "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica",
            "name": "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica",
            "title": "Integras de Decisoes Terminativas e Acordaos do Diario da Justica",
            "resources": [
                # Consolidado mensal
                {"id": "r1", "name": "202203.zip", "url": "https://stj/202203.zip", "format": "ZIP", "created": "2022-04-01"},
                {"id": "r2", "name": "metadados202203.json", "url": "https://stj/metadados202203.json", "format": "JSON", "created": "2022-04-01"},
                # Diario
                {"id": "r3", "name": "20260122.zip", "url": "https://stj/20260122.zip", "format": "ZIP", "created": "2026-01-23"},
                {"id": "r4", "name": "metadados20260122.json", "url": "https://stj/metadados20260122.json", "format": "JSON", "created": "2026-01-23"},
                # CSV (deve ser ignorado)
                {"id": "r5", "name": "resumo.csv", "url": "https://stj/resumo.csv", "format": "CSV", "created": "2026-01-01"},
            ]
        }
    }


class TestCKANClientIntegras:
    """Testes do CKANClient para dataset de integras."""

    @patch("ckan_client.httpx.Client.get")
    def test_get_integras_package(self, mock_get, mock_integras_package_response):
        """Busca package de integras."""
        mock_response = Mock()
        mock_response.json.return_value = mock_integras_package_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with CKANClient() as client:
            package = client.get_integras_package()

        assert package.name == "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica"
        assert len(package.resources) == 5

    @patch("ckan_client.httpx.Client.get")
    def test_get_integras_resource_pairs(self, mock_get, mock_integras_package_response):
        """Retorna pares (zip, json_metadados) ordenados por data."""
        mock_response = Mock()
        mock_response.json.return_value = mock_integras_package_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with CKANClient() as client:
            pairs = client.get_integras_resource_pairs()

        # 2 pares: consolidado mensal + diario
        assert len(pairs) == 2
        # Cada par tem (zip, json)
        for zip_res, meta_res in pairs:
            assert zip_res.is_zip
            assert meta_res.is_json

    @patch("ckan_client.httpx.Client.get")
    def test_get_integras_resources_by_date_range(self, mock_get, mock_integras_package_response):
        """Filtra pares por intervalo de datas."""
        mock_response = Mock()
        mock_response.json.return_value = mock_integras_package_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with CKANClient() as client:
            # Apenas 2026
            pairs = client.get_integras_resources_by_date_range("2026-01-01", "2026-12-31")

        assert len(pairs) == 1
        assert pairs[0][0].name == "20260122.zip"
