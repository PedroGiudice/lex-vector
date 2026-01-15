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
