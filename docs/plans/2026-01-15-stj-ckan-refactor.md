# STJ CKAN API Refactor - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the STJ backend to use the new CKAN API at `dadosabertos.web.stj.jus.br` since the old URL returns 404.

**Architecture:** Replace direct URL construction with CKAN API v3 calls. The CKAN API exposes datasets as "packages" containing multiple "resources" (monthly JSON files). We'll fetch the package metadata first, then download resources by their URLs.

**Tech Stack:** Python 3.10+, FastAPI, httpx, DuckDB, CKAN API v3

---

## Context

### Old API (404 - Broken)
```
https://www.stj.jus.br/sites/portalp/SiteAssets/documentos/noticias/abertos/{Orgao}/{Year}/{YYYYMM}.json
```

### New CKAN API (Working)
```
Base: https://dadosabertos.web.stj.jus.br
List packages: /api/3/action/package_list
Package details: /api/3/action/package_show?id={package_id}
```

### CKAN Datasets (11 total)
| Dataset ID | Orgao Key |
|------------|-----------|
| espelhos-de-acordaos-corte-especial | corte_especial |
| espelhos-de-acordaos-primeira-secao | primeira_secao |
| espelhos-de-acordaos-segunda-secao | segunda_secao |
| espelhos-de-acordaos-terceira-secao | terceira_secao |
| espelhos-de-acordaos-primeira-turma | primeira_turma |
| espelhos-de-acordaos-segunda-turma | segunda_turma |
| espelhos-de-acordaos-terceira-turma | terceira_turma |
| espelhos-de-acordaos-quarta-turma | quarta_turma |
| espelhos-de-acordaos-quinta-turma | quinta_turma |
| espelhos-de-acordaos-sexta-turma | sexta_turma |
| integras-de-acordaos | integras |

### CKAN Resource Structure
Each package contains resources with:
- `url`: Direct download URL for the JSON file
- `name`: Filename (e.g., "20241101.json" or "espelhos_acordaos_primeira_turma.zip")
- `format`: "JSON" or "ZIP"
- `created`: Creation timestamp

---

## Task 1: Update config.py with CKAN Constants

**Files:**
- Modify: `legal-workbench/ferramentas/stj-dados-abertos/config.py`
- Test: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_config.py` (new)

**Step 1: Write the failing test**

Create `tests/test_config.py`:

```python
"""Tests for config.py CKAN configuration."""
import pytest
from config import (
    CKAN_BASE_URL,
    CKAN_DATASETS,
    get_ckan_package_url,
    get_orgao_dataset_id,
)


def test_ckan_base_url_correct():
    """CKAN base URL should point to dadosabertos.web.stj.jus.br."""
    assert CKAN_BASE_URL == "https://dadosabertos.web.stj.jus.br"


def test_ckan_datasets_has_all_orgaos():
    """Should have mapping for all 10 orgaos + integras."""
    expected_orgaos = [
        "corte_especial",
        "primeira_secao", "segunda_secao", "terceira_secao",
        "primeira_turma", "segunda_turma", "terceira_turma",
        "quarta_turma", "quinta_turma", "sexta_turma",
    ]
    for orgao in expected_orgaos:
        assert orgao in CKAN_DATASETS


def test_get_ckan_package_url():
    """Should return correct CKAN API URL."""
    url = get_ckan_package_url("primeira_turma")
    assert url == "https://dadosabertos.web.stj.jus.br/api/3/action/package_show?id=espelhos-de-acordaos-primeira-turma"


def test_get_orgao_dataset_id():
    """Should map orgao key to dataset ID."""
    assert get_orgao_dataset_id("corte_especial") == "espelhos-de-acordaos-corte-especial"
    assert get_orgao_dataset_id("primeira_turma") == "espelhos-de-acordaos-primeira-turma"


def test_get_orgao_dataset_id_invalid():
    """Invalid orgao should raise KeyError."""
    with pytest.raises(KeyError):
        get_orgao_dataset_id("invalid_orgao")
```

**Step 2: Run test to verify it fails**

```bash
cd legal-workbench/ferramentas/stj-dados-abertos && python -m pytest tests/test_config.py -v
```

Expected: FAIL with "ImportError: cannot import name 'CKAN_BASE_URL'"

**Step 3: Write minimal implementation**

Update `config.py` - add after line 48 (replace STJ_BASE_URL):

```python
# CKAN API Configuration (New Data Source)
CKAN_BASE_URL: Final[str] = "https://dadosabertos.web.stj.jus.br"
CKAN_API_VERSION: Final[str] = "3"

# Map orgao keys to CKAN dataset IDs
CKAN_DATASETS: Final[dict[str, str]] = {
    "corte_especial": "espelhos-de-acordaos-corte-especial",
    "primeira_secao": "espelhos-de-acordaos-primeira-secao",
    "segunda_secao": "espelhos-de-acordaos-segunda-secao",
    "terceira_secao": "espelhos-de-acordaos-terceira-secao",
    "primeira_turma": "espelhos-de-acordaos-primeira-turma",
    "segunda_turma": "espelhos-de-acordaos-segunda-turma",
    "terceira_turma": "espelhos-de-acordaos-terceira-turma",
    "quarta_turma": "espelhos-de-acordaos-quarta-turma",
    "quinta_turma": "espelhos-de-acordaos-quinta-turma",
    "sexta_turma": "espelhos-de-acordaos-sexta-turma",
}

# Legacy URL (DEPRECATED - returns 404)
STJ_BASE_URL_LEGACY: Final[str] = "https://www.stj.jus.br/sites/portalp/SiteAssets/documentos/noticias/abertos/"


def get_orgao_dataset_id(orgao: str) -> str:
    """
    Get CKAN dataset ID for an orgao key.

    Args:
        orgao: Orgao key (e.g., "primeira_turma")

    Returns:
        CKAN dataset ID (e.g., "espelhos-de-acordaos-primeira-turma")

    Raises:
        KeyError: If orgao not found in CKAN_DATASETS
    """
    return CKAN_DATASETS[orgao]


def get_ckan_package_url(orgao: str) -> str:
    """
    Get CKAN API URL for package metadata.

    Args:
        orgao: Orgao key (e.g., "primeira_turma")

    Returns:
        Full CKAN API URL for package_show endpoint
    """
    dataset_id = get_orgao_dataset_id(orgao)
    return f"{CKAN_BASE_URL}/api/{CKAN_API_VERSION}/action/package_show?id={dataset_id}"
```

**Step 4: Run test to verify it passes**

```bash
cd legal-workbench/ferramentas/stj-dados-abertos && python -m pytest tests/test_config.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add legal-workbench/ferramentas/stj-dados-abertos/config.py legal-workbench/ferramentas/stj-dados-abertos/tests/test_config.py
git commit -m "$(cat <<'EOF'
feat(lw-stj): add CKAN API configuration

- Add CKAN_BASE_URL pointing to dadosabertos.web.stj.jus.br
- Add CKAN_DATASETS mapping orgao keys to dataset IDs
- Add get_ckan_package_url() helper function
- Deprecate STJ_BASE_URL (now returns 404)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Create CKANClient for API Interactions

**Files:**
- Create: `legal-workbench/ferramentas/stj-dados-abertos/src/ckan_client.py`
- Test: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_ckan_client.py` (new)

**Step 1: Write the failing test**

Create `tests/test_ckan_client.py`:

```python
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
```

**Step 2: Run test to verify it fails**

```bash
cd legal-workbench/ferramentas/stj-dados-abertos && python -m pytest tests/test_ckan_client.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'ckan_client'"

**Step 3: Write minimal implementation**

Create `src/ckan_client.py`:

```python
"""
CKAN API Client for STJ Dados Abertos.

Handles all interactions with the CKAN API at dadosabertos.web.stj.jus.br.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Final

import httpx

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    CKAN_BASE_URL,
    CKAN_API_VERSION,
    get_orgao_dataset_id,
    DEFAULT_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Regex to extract date from filename (YYYYMMDD.json)
DATE_PATTERN: Final[re.Pattern] = re.compile(r"^(\d{4})(\d{2})(\d{2})\.json$")


@dataclass
class CKANResource:
    """Represents a CKAN resource (file) within a package."""
    id: str
    name: str
    url: str
    format: str
    created: str

    @classmethod
    def from_dict(cls, data: dict) -> "CKANResource":
        """Create resource from CKAN API response dict."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            url=data.get("url", ""),
            format=data.get("format", "").upper(),
            created=data.get("created", ""),
        )

    @property
    def is_json(self) -> bool:
        """Check if resource is a JSON file."""
        return self.format == "JSON"

    @property
    def is_zip(self) -> bool:
        """Check if resource is a ZIP file."""
        return self.format == "ZIP"

    def extract_date(self) -> Optional[str]:
        """
        Extract date from filename (YYYYMMDD.json -> YYYY-MM-DD).

        Returns:
            ISO date string or None if filename doesn't match pattern.
        """
        match = DATE_PATTERN.match(self.name)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
        return None


@dataclass
class CKANPackage:
    """Represents a CKAN package (dataset) containing resources."""
    id: str
    name: str
    title: str
    resources: List[CKANResource]

    @classmethod
    def from_dict(cls, data: dict) -> "CKANPackage":
        """Create package from CKAN API response dict."""
        resources = [
            CKANResource.from_dict(r)
            for r in data.get("resources", [])
        ]
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            title=data.get("title", ""),
            resources=resources,
        )


class CKANClient:
    """
    Client for CKAN API at STJ Dados Abertos.

    Usage:
        with CKANClient() as client:
            package = client.get_package("primeira_turma")
            for resource in package.resources:
                print(resource.url)
    """

    def __init__(self, base_url: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url or CKAN_BASE_URL
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def _api_url(self, action: str) -> str:
        """Build CKAN API URL for an action."""
        return f"{self.base_url}/api/{CKAN_API_VERSION}/action/{action}"

    def get_package(self, orgao: str) -> CKANPackage:
        """
        Fetch package metadata for an orgao.

        Args:
            orgao: Orgao key (e.g., "primeira_turma")

        Returns:
            CKANPackage with metadata and resources list

        Raises:
            httpx.HTTPError: If API request fails
        """
        dataset_id = get_orgao_dataset_id(orgao)
        url = f"{self._api_url('package_show')}?id={dataset_id}"

        logger.info(f"Fetching CKAN package: {dataset_id}")
        response = self.client.get(url)
        response.raise_for_status()

        data = response.json()
        if not data.get("success"):
            raise ValueError(f"CKAN API error: {data.get('error', 'Unknown')}")

        return CKANPackage.from_dict(data["result"])

    def get_json_resources(self, orgao: str) -> List[CKANResource]:
        """
        Get only JSON resources for an orgao (excludes ZIP files).

        Args:
            orgao: Orgao key

        Returns:
            List of JSON resources sorted by date (newest first)
        """
        package = self.get_package(orgao)
        json_resources = [r for r in package.resources if r.is_json]

        # Sort by filename (date) descending
        json_resources.sort(key=lambda r: r.name, reverse=True)

        return json_resources

    def get_resources_by_date_range(
        self,
        orgao: str,
        start_date: str,
        end_date: str
    ) -> List[CKANResource]:
        """
        Get JSON resources within a date range.

        Args:
            orgao: Orgao key
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of resources within date range
        """
        resources = self.get_json_resources(orgao)

        # Filter by date range
        filtered = []
        for resource in resources:
            resource_date = resource.extract_date()
            if resource_date:
                if start_date <= resource_date <= end_date:
                    filtered.append(resource)

        return filtered

    def list_packages(self) -> List[str]:
        """
        List all available package IDs.

        Returns:
            List of package IDs
        """
        url = self._api_url("package_list")
        response = self.client.get(url)
        response.raise_for_status()

        data = response.json()
        return data.get("result", [])
```

**Step 4: Run test to verify it passes**

```bash
cd legal-workbench/ferramentas/stj-dados-abertos && python -m pytest tests/test_ckan_client.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add legal-workbench/ferramentas/stj-dados-abertos/src/ckan_client.py legal-workbench/ferramentas/stj-dados-abertos/tests/test_ckan_client.py
git commit -m "$(cat <<'EOF'
feat(lw-stj): add CKAN API client

- CKANResource dataclass for resource metadata
- CKANPackage dataclass for package metadata
- CKANClient with get_package, get_json_resources, get_resources_by_date_range
- Date extraction from YYYYMMDD.json filenames

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Refactor STJDownloader to Use CKANClient

**Files:**
- Modify: `legal-workbench/ferramentas/stj-dados-abertos/src/downloader.py`
- Update: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_downloader.py`

**Step 1: Write the failing test**

Add to `tests/test_downloader.py`:

```python
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
```

**Step 2: Run test to verify it fails**

```bash
cd legal-workbench/ferramentas/stj-dados-abertos && python -m pytest tests/test_downloader.py::TestSTJDownloaderCKAN -v
```

Expected: FAIL with "AttributeError: 'STJDownloader' object has no attribute 'download_from_ckan'"

**Step 3: Write minimal implementation**

Add to `src/downloader.py` after existing imports:

```python
from ckan_client import CKANClient, CKANResource
```

Add new method to `STJDownloader` class:

```python
    def download_from_ckan(
        self,
        orgao: str,
        start_date: str,
        end_date: str,
        force: bool = False,
        show_progress: bool = True
    ) -> list[Path]:
        """
        Download files from CKAN API for a date range.

        Args:
            orgao: Orgao key (e.g., "primeira_turma")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            force: Overwrite existing files
            show_progress: Show progress bar

        Returns:
            List of downloaded file paths
        """
        downloaded_files = []

        with CKANClient() as ckan:
            resources = ckan.get_resources_by_date_range(orgao, start_date, end_date)

            if not resources:
                logger.info(f"No resources found for {orgao} between {start_date} and {end_date}")
                return downloaded_files

            logger.info(f"Found {len(resources)} resources for {orgao}")

            # Build URL configs for batch download
            url_configs = []
            for resource in resources:
                filename = f"{orgao}_{resource.name}"
                url_configs.append({
                    "url": resource.url,
                    "filename": filename,
                    "force": force,
                })

            # Use existing batch download logic
            downloaded_files = self.download_batch(url_configs, show_progress)

        return downloaded_files

    def download_all_orgaos(
        self,
        start_date: str,
        end_date: str,
        orgaos: Optional[list[str]] = None,
        force: bool = False
    ) -> dict[str, list[Path]]:
        """
        Download from all orgaos (or specified subset).

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            orgaos: List of orgao keys (default: all)
            force: Overwrite existing files

        Returns:
            Dict mapping orgao to list of downloaded files
        """
        from config import CKAN_DATASETS

        target_orgaos = orgaos or list(CKAN_DATASETS.keys())
        results = {}

        for orgao in target_orgaos:
            logger.info(f"Downloading {orgao}...")
            files = self.download_from_ckan(orgao, start_date, end_date, force)
            results[orgao] = files

        return results
```

**Step 4: Run test to verify it passes**

```bash
cd legal-workbench/ferramentas/stj-dados-abertos && python -m pytest tests/test_downloader.py::TestSTJDownloaderCKAN -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add legal-workbench/ferramentas/stj-dados-abertos/src/downloader.py legal-workbench/ferramentas/stj-dados-abertos/tests/test_downloader.py
git commit -m "$(cat <<'EOF'
feat(lw-stj): add CKAN download methods to STJDownloader

- download_from_ckan() fetches resources by date range
- download_all_orgaos() downloads from multiple orgaos
- Integrates CKANClient for resource discovery

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Update scheduler.py for CKAN Sync

**Files:**
- Modify: `legal-workbench/docker/services/stj-api/api/scheduler.py`

**Step 1: Read current scheduler**

```bash
cat legal-workbench/docker/services/stj-api/api/scheduler.py
```

**Step 2: Update run_sync_task to use CKAN**

Replace the download logic in `run_sync_task()`:

```python
def run_sync_task(orgaos: Optional[List[str]] = None, dias: int = 30, force: bool = False):
    """
    Background task to sync data from STJ CKAN API.

    Args:
        orgaos: List of orgao keys to sync (default: all)
        dias: Number of days to look back
        force: Force re-download of existing files
    """
    global _sync_status

    _sync_status = {
        "status": "running",
        "started_at": datetime.now(),
        "downloaded": 0,
        "processed": 0,
        "inserted": 0,
        "duplicates": 0,
        "errors": 0,
        "message": "Starting sync..."
    }

    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=dias)

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        logger.info(f"Sync task started: {start_str} to {end_str}")

        # Download from CKAN
        with STJDownloader() as downloader:
            results = downloader.download_all_orgaos(
                start_date=start_str,
                end_date=end_str,
                orgaos=orgaos,
                force=force
            )

            _sync_status["downloaded"] = sum(len(files) for files in results.values())
            _sync_status["message"] = f"Downloaded {_sync_status['downloaded']} files"

        # Process and insert
        processor = STJProcessor()
        all_files = []
        for files in results.values():
            all_files.extend(files)

        if all_files:
            registros = processor.processar_batch(all_files)
            _sync_status["processed"] = len(registros)

            # Insert to database
            with STJDatabase() as db:
                db.criar_schema()
                inserted, duplicates, errors = db.inserir_batch(registros)

                _sync_status["inserted"] = inserted
                _sync_status["duplicates"] = duplicates
                _sync_status["errors"] = errors

        _sync_status["status"] = "completed"
        _sync_status["completed_at"] = datetime.now()
        _sync_status["message"] = f"Sync completed: {_sync_status['inserted']} new records"

        logger.info(f"Sync completed: {_sync_status}")

    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        _sync_status["status"] = "failed"
        _sync_status["completed_at"] = datetime.now()
        _sync_status["message"] = f"Error: {str(e)}"
        _sync_status["errors"] += 1
```

**Step 3: Commit**

```bash
git add legal-workbench/docker/services/stj-api/api/scheduler.py
git commit -m "$(cat <<'EOF'
refactor(lw-stj): update scheduler to use CKAN API

- Replace legacy URL construction with CKAN download
- Use download_all_orgaos() for multi-orgao sync
- Maintain existing status tracking

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Update get_date_range_urls for Backward Compatibility

**Files:**
- Modify: `legal-workbench/ferramentas/stj-dados-abertos/config.py`

**Step 1: Deprecate and redirect get_date_range_urls**

```python
def get_date_range_urls(start_date: datetime, end_date: datetime, orgao: str) -> list[dict[str, str | int]]:
    """
    DEPRECATED: Use CKANClient.get_resources_by_date_range() instead.

    This function is kept for backward compatibility but logs a deprecation warning.
    """
    import warnings
    warnings.warn(
        "get_date_range_urls is deprecated. Use CKANClient.get_resources_by_date_range() instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Return empty list - callers should migrate to CKAN
    logger.warning("get_date_range_urls called - migrate to CKANClient")
    return []
```

**Step 2: Commit**

```bash
git add legal-workbench/ferramentas/stj-dados-abertos/config.py
git commit -m "$(cat <<'EOF'
refactor(lw-stj): deprecate get_date_range_urls

- Add deprecation warning
- Return empty list to prevent silent failures
- Callers should migrate to CKANClient

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Integration Test with Real CKAN API

**Files:**
- Create: `legal-workbench/ferramentas/stj-dados-abertos/tests/test_integration_ckan.py`

**Step 1: Write integration test**

```python
"""
Integration tests for CKAN API.

These tests hit the real CKAN API and should be run manually or in CI.
Mark with @pytest.mark.integration to skip in unit tests.
"""
import pytest
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from ckan_client import CKANClient


@pytest.mark.integration
class TestCKANIntegration:
    """Integration tests with real CKAN API."""

    def test_list_packages(self):
        """Should list available packages from real API."""
        with CKANClient() as client:
            packages = client.list_packages()

        assert len(packages) > 0
        assert "espelhos-de-acordaos-primeira-turma" in packages

    def test_get_package_primeira_turma(self):
        """Should fetch real package metadata."""
        with CKANClient() as client:
            package = client.get_package("primeira_turma")

        assert package.id == "espelhos-de-acordaos-primeira-turma"
        assert len(package.resources) > 0

    def test_get_json_resources(self):
        """Should get JSON resources only."""
        with CKANClient() as client:
            resources = client.get_json_resources("primeira_turma")

        assert len(resources) > 0
        assert all(r.is_json for r in resources)
        # Check filename format
        for r in resources:
            assert r.name.endswith(".json")

    def test_get_resources_by_date_range(self):
        """Should filter by date range."""
        with CKANClient() as client:
            # Get resources from last 60 days
            from datetime import datetime, timedelta
            end = datetime.now()
            start = end - timedelta(days=60)

            resources = client.get_resources_by_date_range(
                "primeira_turma",
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d")
            )

        # Should have at least 1 resource (assuming data exists)
        # Note: May be 0 if STJ hasn't published recently
        assert isinstance(resources, list)
```

**Step 2: Run integration test**

```bash
cd legal-workbench/ferramentas/stj-dados-abertos && python -m pytest tests/test_integration_ckan.py -v -m integration
```

**Step 3: Commit**

```bash
git add legal-workbench/ferramentas/stj-dados-abertos/tests/test_integration_ckan.py
git commit -m "$(cat <<'EOF'
test(lw-stj): add CKAN integration tests

- Test real CKAN API connectivity
- Mark with @pytest.mark.integration for CI
- Verify package listing and resource fetching

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Deploy and Validate on Oracle Cloud

**Files:**
- No code changes - deployment and validation

**Step 1: Sync changes to Oracle Cloud**

```bash
rsync -avz legal-workbench/ferramentas/stj-dados-abertos/ opc@64.181.162.38:/home/opc/lex-vector/legal-workbench/ferramentas/stj-dados-abertos/
```

**Step 2: Rebuild and restart container**

```bash
ssh opc@64.181.162.38 "cd /home/opc/lex-vector/legal-workbench && docker compose build api-stj && docker compose up -d api-stj"
```

**Step 3: Verify health**

```bash
ssh opc@64.181.162.38 "curl -s http://localhost/api/stj/health | jq"
```

**Step 4: Test sync with CKAN**

```bash
ssh opc@64.181.162.38 "curl -X POST http://localhost/api/stj/api/v1/sync -H 'Content-Type: application/json' -d '{\"orgaos\": [\"primeira_turma\"], \"dias\": 30}'"
```

**Step 5: Check sync status**

```bash
ssh opc@64.181.162.38 "curl -s http://localhost/api/stj/api/v1/sync/status | jq"
```

**Step 6: Verify data in database**

```bash
ssh opc@64.181.162.38 "curl -s 'http://localhost/api/stj/api/v1/stats' | jq"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Update config.py with CKAN constants | config.py, test_config.py |
| 2 | Create CKANClient | ckan_client.py, test_ckan_client.py |
| 3 | Refactor STJDownloader | downloader.py, test_downloader.py |
| 4 | Update scheduler for CKAN | scheduler.py |
| 5 | Deprecate get_date_range_urls | config.py |
| 6 | Integration tests | test_integration_ckan.py |
| 7 | Deploy and validate | N/A (deployment) |

**Total estimated commits:** 7
**Parallel execution possible:** Tasks 1-2 can run in parallel, Tasks 3-5 are sequential, Task 6 can run after Task 2
