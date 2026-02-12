#!/usr/bin/env python3
"""
Tests for the unified LTE CLI.

Tests cover:
- CLI help and version commands
- Process command with various options
- Stats command with filters
- Batch command with dry-run
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

# Import the CLI app
from cli.main import __version__, app

runner = CliRunner()


class TestCLIVersion:
    """Tests for version command and flag."""

    def test_version_flag(self):
        """Test --version flag shows version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_short_flag(self):
        """Test -V short flag shows version."""
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert __version__ in result.stdout

    def test_version_command(self):
        """Test version command shows detailed info."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Legal Text Extractor" in result.stdout
        assert __version__ in result.stdout
        assert "Engines disponiveis" in result.stdout


class TestCLIHelp:
    """Tests for help command."""

    def test_main_help(self):
        """Test main --help shows all commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "process" in result.stdout
        assert "stats" in result.stdout
        assert "batch" in result.stdout
        assert "version" in result.stdout

    def test_process_help(self):
        """Test process --help shows options."""
        result = runner.invoke(app, ["process", "--help"])
        assert result.exit_code == 0
        assert "--engine" in result.stdout
        assert "--output" in result.stdout
        assert "--format" in result.stdout
        assert "--force-ocr" in result.stdout

    def test_stats_help(self):
        """Test stats --help shows options."""
        result = runner.invoke(app, ["stats", "--help"])
        assert result.exit_code == 0
        assert "--db" in result.stdout
        assert "--engine" in result.stdout
        assert "--since" in result.stdout
        assert "--export" in result.stdout

    def test_batch_help(self):
        """Test batch --help shows options."""
        result = runner.invoke(app, ["batch", "--help"])
        assert result.exit_code == 0
        assert "--parallel" in result.stdout
        assert "--recursive" in result.stdout
        assert "--pattern" in result.stdout
        assert "--dry-run" in result.stdout


class TestProcessCommand:
    """Tests for process command."""

    def test_process_file_not_found(self):
        """Test process with non-existent file."""
        result = runner.invoke(app, ["process", "/nonexistent/file.pdf"])
        assert result.exit_code != 0

    def test_process_invalid_engine(self):
        """Test process with invalid engine."""
        # Create a temp file to avoid file not found error
        with runner.isolated_filesystem():
            Path("test.pdf").write_bytes(b"%PDF-1.4")
            result = runner.invoke(app, ["process", "test.pdf", "--engine", "invalid"])
            assert result.exit_code != 0
            assert "Engine invalida" in result.stdout

    def test_process_invalid_format(self):
        """Test process with invalid format."""
        with runner.isolated_filesystem():
            Path("test.pdf").write_bytes(b"%PDF-1.4")
            result = runner.invoke(app, ["process", "test.pdf", "--format", "xml"])
            assert result.exit_code != 0
            assert "Formato invalido" in result.stdout


class TestStatsCommand:
    """Tests for stats command."""

    def test_stats_db_not_found(self):
        """Test stats with non-existent database."""
        result = runner.invoke(app, ["stats", "--db", "/nonexistent/db.sqlite"])
        assert result.exit_code != 0
        assert "Database nao encontrado" in result.stdout

    def test_stats_invalid_engine(self):
        """Test stats with invalid engine filter."""
        with runner.isolated_filesystem():
            # Create a minimal SQLite database
            import sqlite3

            Path("test.db").touch()
            conn = sqlite3.connect("test.db")
            conn.execute("CREATE TABLE caso (id INTEGER PRIMARY KEY)")
            conn.execute("CREATE TABLE observed_patterns (id INTEGER PRIMARY KEY)")
            conn.execute("CREATE TABLE divergences (id INTEGER PRIMARY KEY)")
            conn.close()

            result = runner.invoke(app, ["stats", "--db", "test.db", "--engine", "invalid"])
            assert result.exit_code != 0
            assert "Engine invalida" in result.stdout

    def test_stats_invalid_date(self):
        """Test stats with invalid date format."""
        with runner.isolated_filesystem():
            import sqlite3

            Path("test.db").touch()
            conn = sqlite3.connect("test.db")
            conn.execute("CREATE TABLE caso (id INTEGER PRIMARY KEY)")
            conn.execute("CREATE TABLE observed_patterns (id INTEGER PRIMARY KEY)")
            conn.execute("CREATE TABLE divergences (id INTEGER PRIMARY KEY)")
            conn.close()

            result = runner.invoke(app, ["stats", "--db", "test.db", "--since", "invalid-date"])
            assert result.exit_code != 0


class TestBatchCommand:
    """Tests for batch command."""

    def test_batch_dir_not_found(self):
        """Test batch with non-existent directory."""
        result = runner.invoke(app, ["batch", "/nonexistent/dir"])
        assert result.exit_code != 0

    def test_batch_empty_dir(self):
        """Test batch with empty directory."""
        with runner.isolated_filesystem():
            Path("empty_dir").mkdir()
            result = runner.invoke(app, ["batch", "empty_dir"])
            assert result.exit_code == 0
            assert "Nenhum arquivo encontrado" in result.stdout

    def test_batch_dry_run(self):
        """Test batch with --dry-run lists files without processing."""
        with runner.isolated_filesystem():
            Path("test_dir").mkdir()
            (Path("test_dir") / "doc1.pdf").write_bytes(b"%PDF-1.4")
            (Path("test_dir") / "doc2.pdf").write_bytes(b"%PDF-1.4")

            result = runner.invoke(app, ["batch", "test_dir", "--dry-run"])
            assert result.exit_code == 0
            assert "dry-run" in result.stdout
            assert "doc1.pdf" in result.stdout
            assert "doc2.pdf" in result.stdout
            assert "Execute sem --dry-run" in result.stdout

    def test_batch_invalid_engine(self):
        """Test batch with invalid engine."""
        with runner.isolated_filesystem():
            Path("test_dir").mkdir()
            (Path("test_dir") / "test.pdf").write_bytes(b"%PDF-1.4")
            result = runner.invoke(app, ["batch", "test_dir", "--engine", "invalid"])
            assert result.exit_code != 0
            assert "Engine invalida" in result.stdout

    def test_batch_invalid_format(self):
        """Test batch with invalid format."""
        with runner.isolated_filesystem():
            Path("test_dir").mkdir()
            (Path("test_dir") / "test.pdf").write_bytes(b"%PDF-1.4")
            result = runner.invoke(app, ["batch", "test_dir", "--format", "xml"])
            assert result.exit_code != 0
            assert "Formato invalido" in result.stdout

    def test_batch_recursive_option(self):
        """Test batch with --recursive finds nested files."""
        with runner.isolated_filesystem():
            Path("test_dir/subdir").mkdir(parents=True)
            (Path("test_dir") / "doc1.pdf").write_bytes(b"%PDF-1.4")
            (Path("test_dir/subdir") / "doc2.pdf").write_bytes(b"%PDF-1.4")

            # Without recursive
            result = runner.invoke(app, ["batch", "test_dir", "--dry-run"])
            assert "doc1.pdf" in result.stdout
            assert "doc2.pdf" not in result.stdout

            # With recursive
            result = runner.invoke(app, ["batch", "test_dir", "--recursive", "--dry-run"])
            assert "doc1.pdf" in result.stdout
            assert "doc2.pdf" in result.stdout

    def test_batch_pattern_filter(self):
        """Test batch with --pattern filters files."""
        with runner.isolated_filesystem():
            Path("test_dir").mkdir()
            (Path("test_dir") / "processo_123.pdf").write_bytes(b"%PDF-1.4")
            (Path("test_dir") / "contrato_456.pdf").write_bytes(b"%PDF-1.4")
            (Path("test_dir") / "processo_789.pdf").write_bytes(b"%PDF-1.4")

            result = runner.invoke(
                app, ["batch", "test_dir", "--pattern", "processo_*.pdf", "--dry-run"]
            )
            assert "processo_123.pdf" in result.stdout
            assert "processo_789.pdf" in result.stdout
            assert "contrato_456.pdf" not in result.stdout


class TestCLINoArgs:
    """Test CLI with no arguments."""

    def test_no_args_shows_help(self):
        """Test that running with no args shows help."""
        result = runner.invoke(app, [])
        # Typer with no_args_is_help returns exit code 0, but shows Usage
        # The app is configured with no_args_is_help=True
        assert "process" in result.stdout or "Usage" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
