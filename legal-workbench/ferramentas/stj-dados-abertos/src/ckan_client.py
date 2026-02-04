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
    INTEGRAS_DATASET_ID,
    get_orgao_dataset_id,
    DEFAULT_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Regex patterns for filenames
DATE_PATTERN: Final[re.Pattern] = re.compile(r"^(\d{4})(\d{2})(\d{2})\.json$")
# Integras: ZIPs diarios (YYYYMMDD.zip) e mensais (YYYYMM.zip)
ZIP_DATE_DAILY: Final[re.Pattern] = re.compile(r"^(\d{4})(\d{2})(\d{2})\.zip$")
ZIP_DATE_MONTHLY: Final[re.Pattern] = re.compile(r"^(\d{4})(\d{2})\.zip$")
# Integras: JSONs de metadados diarios e mensais
METADADOS_DAILY: Final[re.Pattern] = re.compile(r"^metadados(\d{4})(\d{2})(\d{2})(?:\.json)?$")
METADADOS_MONTHLY: Final[re.Pattern] = re.compile(r"^metadados(\d{4})(\d{2})(?:\.json)?$")


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

    @property
    def is_csv(self) -> bool:
        """Check if resource is a CSV file."""
        return self.format == "CSV"

    def extract_date(self) -> Optional[str]:
        """
        Extract date from filename (daily patterns only).

        Supports:
        - YYYYMMDD.json -> YYYY-MM-DD (espelhos)
        - YYYYMMDD.zip -> YYYY-MM-DD (integras diarios)
        - metadadosYYYYMMDD.json -> YYYY-MM-DD (integras metadados diarios)

        Returns:
            ISO date string or None if filename doesn't match daily pattern.
        """
        # JSON espelhos: YYYYMMDD.json
        match = DATE_PATTERN.match(self.name)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"

        # ZIP diario: YYYYMMDD.zip
        match = ZIP_DATE_DAILY.match(self.name)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"

        # Metadados diario: metadadosYYYYMMDD.json
        match = METADADOS_DAILY.match(self.name)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"

        return None

    def extract_date_monthly(self) -> Optional[str]:
        """
        Extract monthly date from filename (monthly patterns only).

        Supports:
        - YYYYMM.zip -> YYYY-MM (integras consolidados mensais)
        - metadadosYYYYMM.json -> YYYY-MM (integras metadados mensais)

        Returns:
            YYYY-MM string or None if filename doesn't match monthly pattern.
        """
        # ZIP mensal: YYYYMM.zip
        match = ZIP_DATE_MONTHLY.match(self.name)
        if match:
            year, month = match.groups()
            return f"{year}-{month}"

        # Metadados mensal: metadadosYYYYMM.json
        match = METADADOS_MONTHLY.match(self.name)
        if match:
            year, month = match.groups()
            return f"{year}-{month}"

        return None

    def extract_date_key(self) -> Optional[str]:
        """
        Extract a date key for pairing resources.

        Returns the raw date digits from the filename (YYYYMMDD or YYYYMM).
        Used internally for matching ZIP<->JSON pairs.
        """
        # Daily ZIP/JSON
        match = ZIP_DATE_DAILY.match(self.name)
        if match:
            return "".join(match.groups())
        match = METADADOS_DAILY.match(self.name)
        if match:
            return "".join(match.groups())
        # Monthly ZIP/JSON
        match = ZIP_DATE_MONTHLY.match(self.name)
        if match:
            return "".join(match.groups())
        match = METADADOS_MONTHLY.match(self.name)
        if match:
            return "".join(match.groups())
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

    # ===================================================================
    # Integras
    # ===================================================================

    def get_integras_package(self) -> CKANPackage:
        """
        Fetch package de integras (dataset unico, nao por orgao).

        Returns:
            CKANPackage with metadata and resources list
        """
        url = f"{self._api_url('package_show')}?id={INTEGRAS_DATASET_ID}"

        logger.info(f"Fetching CKAN integras package: {INTEGRAS_DATASET_ID}")
        response = self.client.get(url)
        response.raise_for_status()

        data = response.json()
        if not data.get("success"):
            raise ValueError(f"CKAN API error: {data.get('error', 'Unknown')}")

        return CKANPackage.from_dict(data["result"])

    def get_integras_resource_pairs(self) -> List[tuple]:
        """
        Retorna pares (zip_textos, json_metadados) ordenados por data.

        Cada par corresponde a um dia ou mes de publicacoes.
        CSVs sao ignorados.
        Pareamento via date_key extraido do nome do arquivo.

        Returns:
            Lista de tuplas (CKANResource ZIP, CKANResource JSON)
        """
        package = self.get_integras_package()

        # Separar ZIPs e JSONs de metadados
        zips_by_key: dict[str, CKANResource] = {}
        metas_by_key: dict[str, CKANResource] = {}

        for resource in package.resources:
            if resource.is_csv:
                continue

            date_key = resource.extract_date_key()
            if not date_key:
                continue

            if resource.is_zip:
                zips_by_key[date_key] = resource
            elif resource.is_json and resource.name.startswith("metadados"):
                metas_by_key[date_key] = resource

        # Parear por date_key
        pairs = []
        for key in sorted(zips_by_key.keys()):
            if key in metas_by_key:
                pairs.append((zips_by_key[key], metas_by_key[key]))
            else:
                logger.warning(f"ZIP sem metadados correspondente: {zips_by_key[key].name}")

        logger.info(f"Encontrados {len(pairs)} pares de integras")
        return pairs

    def get_integras_resources_by_date_range(
        self, start_date: str, end_date: str
    ) -> List[tuple]:
        """
        Filtra pares de integras por intervalo de datas.

        Args:
            start_date: Data inicio (YYYY-MM-DD)
            end_date: Data fim (YYYY-MM-DD)

        Returns:
            Lista de tuplas (CKANResource ZIP, CKANResource JSON) filtrada
        """
        pairs = self.get_integras_resource_pairs()

        filtered = []
        for zip_res, meta_res in pairs:
            # Tentar data diaria primeiro, depois mensal
            resource_date = zip_res.extract_date()
            if resource_date:
                if start_date <= resource_date <= end_date:
                    filtered.append((zip_res, meta_res))
            else:
                # Mensal: comparar YYYY-MM com YYYY-MM do range
                monthly = zip_res.extract_date_monthly()
                if monthly:
                    start_monthly = start_date[:7]  # YYYY-MM
                    end_monthly = end_date[:7]
                    if start_monthly <= monthly <= end_monthly:
                        filtered.append((zip_res, meta_res))

        return filtered
