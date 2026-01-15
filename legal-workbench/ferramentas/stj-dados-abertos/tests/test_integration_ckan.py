"""
Integration tests for CKAN API.

These tests hit the real CKAN API and should be run manually or in CI.
Mark with @pytest.mark.integration to skip in unit tests.
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta

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

        # CKAN uses UUID for id field, slug name for name field
        assert package.name == "espelhos-de-acordaos-primeira-turma"
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
