"""Testes para StatusLineParser."""
import pytest
import json
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.statusline import StatusLineParser
from backend.models import StatusLineData


class TestStatusLineParserBasic:
    """Testes básicos do parser."""

    @pytest.fixture
    def parser(self):
        return StatusLineParser()

    def test_parser_initialization(self, parser):
        """Parser deve inicializar sem erros."""
        assert parser is not None
        assert parser.get_last_data() is None


class TestStatusLineParserJSON:
    """Testes de parsing JSON."""

    @pytest.fixture
    def parser(self):
        return StatusLineParser()

    def test_parse_valid_json(self, parser):
        """Deve parsear JSON válido de statusline."""
        json_str = json.dumps({
            "model": {"name": "claude-sonnet-4", "display_name": "Claude Sonnet 4"},
            "workspace": {"current_dir": "/home/user/project"},
            "git": {"branch": "main", "dirty": False, "ahead": 0, "behind": 0},
            "context": {"percent": 45.2, "tokens": 12000, "limit": 128000}
        })

        data = parser.parse_json(json_str)

        assert data is not None
        assert data.model == "claude-sonnet-4"
        assert data.model_display == "Claude Sonnet 4"
        assert data.git_branch == "main"
        assert data.context_percent == 45.2

    def test_parse_full_json(self, parser):
        """Deve parsear JSON completo com session info."""
        json_str = json.dumps({
            "model": {"name": "claude-opus-4", "display_name": "Claude Opus 4"},
            "workspace": {"current_dir": "/home/user/project"},
            "git": {"branch": "feature", "dirty": True, "ahead": 2, "behind": 1},
            "context": {"percent": 75.5, "tokens": 50000, "limit": 200000},
            "session": {"cost": 0.15, "messages": 25, "duration": "01:30:00"}
        })

        data = parser.parse_json(json_str)

        assert data is not None
        assert data.git_dirty is True
        assert data.git_ahead == 2
        assert data.git_behind == 1
        assert data.session_cost == 0.15
        assert data.session_messages == 25
        assert data.session_duration == "01:30:00"

    def test_parse_invalid_json_returns_none(self, parser):
        """Deve retornar None para JSON inválido."""
        result = parser.parse_json("not valid json")
        assert result is None

    def test_parse_empty_json(self, parser):
        """Deve lidar com JSON vazio."""
        result = parser.parse_json("{}")
        assert result is not None  # Returns StatusLineData with defaults

    def test_raw_json_stored(self, parser):
        """Deve armazenar JSON original em raw_json."""
        json_str = json.dumps({"model": {"name": "test"}})
        data = parser.parse_json(json_str)

        assert data is not None
        assert data.raw_json is not None
        assert "model" in data.raw_json


class TestStatusLineParserDetection:
    """Testes de detecção de statusline."""

    @pytest.fixture
    def parser(self):
        return StatusLineParser()

    def test_is_statusline_json_positive(self, parser):
        """Deve detectar JSON de statusline."""
        line = json.dumps({"model": {"name": "test"}, "workspace": {}})
        assert parser.is_statusline_json(line) is True

    def test_is_statusline_json_with_git(self, parser):
        """Deve detectar JSON com info de git."""
        line = json.dumps({"git": {"branch": "main"}})
        assert parser.is_statusline_json(line) is True

    def test_is_statusline_json_negative(self, parser):
        """Não deve confundir com outro JSON."""
        line = json.dumps({"error": "something went wrong"})
        assert parser.is_statusline_json(line) is False

    def test_is_statusline_json_not_json(self, parser):
        """Deve retornar False para não-JSON."""
        assert parser.is_statusline_json("plain text") is False
        assert parser.is_statusline_json("") is False

    def test_is_statusline_json_partial_match(self, parser):
        """Deve detectar com match parcial de keys."""
        line = json.dumps({"context": {"percent": 50}})
        assert parser.is_statusline_json(line) is True


class TestStatusLineParserExtract:
    """Testes de extração de output misto."""

    @pytest.fixture
    def parser(self):
        return StatusLineParser()

    def test_extract_from_mixed_output(self, parser):
        """Deve extrair statusline de output misto."""
        json_data = json.dumps({"model": {"name": "test"}, "workspace": {}})
        output = f"Some text\n{json_data}\nMore text"

        data = parser.extract_from_output(output)

        assert data is not None
        assert data.model == "test"

    def test_extract_json_on_own_line(self, parser):
        """Deve extrair JSON em sua própria linha."""
        json_data = json.dumps({"model": {"name": "claude-3"}, "context": {"percent": 30}})
        output = f"Output\n{json_data}\nEnd"

        data = parser.extract_from_output(output)
        assert data is not None

    def test_extract_returns_none_when_not_found(self, parser):
        """Deve retornar None quando não há statusline."""
        output = "Just regular text\nNo JSON here"
        data = parser.extract_from_output(output)
        assert data is None


class TestStatusLineParserState:
    """Testes de gestão de estado."""

    @pytest.fixture
    def parser(self):
        return StatusLineParser()

    def test_get_last_data_after_parse(self, parser):
        """get_last_data deve retornar último parse bem sucedido."""
        json_str = json.dumps({"model": {"name": "last"}})
        parser.parse_json(json_str)

        data = parser.get_last_data()
        assert data is not None
        assert data.model == "last"

    def test_clear_resets_state(self, parser):
        """clear() deve resetar estado."""
        json_str = json.dumps({"model": {"name": "test"}})
        parser.parse_json(json_str)

        parser.clear()
        assert parser.get_last_data() is None


class TestStatusLineParserPartial:
    """Testes de parsing parcial."""

    @pytest.fixture
    def parser(self):
        return StatusLineParser()

    def test_parse_partial_flat_structure(self, parser):
        """Deve parsear estrutura flat."""
        data = {
            "model": "claude-3",
            "current_dir": "/home/user",
            "git_branch": "main",
            "context_percent": 50.0
        }

        result = parser.parse_partial(data)

        assert result.model == "claude-3"
        assert result.current_dir == "/home/user"
        assert result.git_branch == "main"
        assert result.context_percent == 50.0

    def test_parse_partial_alternative_keys(self, parser):
        """Deve aceitar keys alternativas."""
        data = {
            "cwd": "/home/user",  # Alternative to current_dir
            "branch": "dev",      # Alternative to git_branch
            "percent": 25.0       # Alternative to context_percent
        }

        result = parser.parse_partial(data)

        assert result.current_dir == "/home/user"
        assert result.git_branch == "dev"
        assert result.context_percent == 25.0


class TestStatusLineParserFormat:
    """Testes de formatação."""

    @pytest.fixture
    def parser(self):
        return StatusLineParser()

    def test_format_summary_basic(self, parser):
        """format_summary deve gerar string legível."""
        data = StatusLineData(
            model_display="Claude Sonnet 4",
            git_branch="main",
            context_percent=45.5,
            context_tokens=5000,
            context_limit=100000
        )

        summary = parser.format_summary(data)

        assert "Claude Sonnet 4" in summary
        assert "main" in summary
        assert "45.5%" in summary

    def test_format_summary_with_git_dirty(self, parser):
        """format_summary deve mostrar dirty indicator."""
        data = StatusLineData(
            git_branch="feature",
            git_dirty=True,
            git_ahead=2,
            git_behind=1
        )

        summary = parser.format_summary(data)

        assert "feature" in summary
        assert "*" in summary  # dirty indicator
        assert "↑2" in summary  # ahead
        assert "↓1" in summary  # behind

    def test_format_summary_no_data(self, parser):
        """format_summary sem dados deve retornar mensagem padrão."""
        summary = parser.format_summary(None)
        assert "No statusline data available" in summary

    def test_format_summary_uses_last_data(self, parser):
        """format_summary deve usar último dado se não fornecido."""
        json_str = json.dumps({"model": {"display_name": "Test Model"}})
        parser.parse_json(json_str)

        summary = parser.format_summary()
        assert "Test Model" in summary
