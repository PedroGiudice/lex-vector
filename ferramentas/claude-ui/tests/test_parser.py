"""Testes para OutputParser."""
import pytest
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.parser import OutputParser
from backend.models import ContentType, ContentBlock


class TestOutputParserANSI:
    """Testes de remoção de ANSI codes."""

    @pytest.fixture
    def parser(self):
        return OutputParser()

    def test_strip_ansi_codes(self, parser):
        """Deve remover escape sequences ANSI."""
        text = "\x1b[32mGreen text\x1b[0m"
        assert parser.strip_ansi(text) == "Green text"

    def test_strip_multiple_ansi_codes(self, parser):
        """Deve remover múltiplos ANSI codes."""
        text = "\x1b[1m\x1b[32mBold Green\x1b[0m Normal \x1b[31mRed\x1b[0m"
        result = parser.strip_ansi(text)
        assert result == "Bold Green Normal Red"

    def test_strip_ansi_preserves_content(self, parser):
        """Deve preservar conteúdo sem ANSI."""
        text = "Plain text without colors"
        assert parser.strip_ansi(text) == text

    def test_strip_ansi_cursor_codes(self, parser):
        """Deve remover cursor movement codes."""
        text = "\x1b[2J\x1b[HHello\x1b[K"
        result = parser.strip_ansi(text)
        assert "Hello" in result


class TestOutputParserCodeBlocks:
    """Testes de extração de blocos de código."""

    @pytest.fixture
    def parser(self):
        return OutputParser()

    def test_extract_python_code_block(self, parser):
        """Deve extrair bloco de código Python."""
        text = "Here is code:\n```python\nprint('hello')\n```\nEnd."
        blocks = parser.extract_code_blocks(text)

        assert len(blocks) == 1
        lang, code, start, end = blocks[0]
        assert lang == "python"
        assert "print('hello')" in code

    def test_extract_code_block_no_language(self, parser):
        """Deve extrair bloco sem linguagem especificada."""
        text = "```\nsome code\n```"
        blocks = parser.extract_code_blocks(text)

        assert len(blocks) == 1
        lang, code, start, end = blocks[0]
        assert lang == ""
        assert "some code" in code

    def test_extract_multiple_code_blocks(self, parser):
        """Deve extrair múltiplos blocos de código."""
        text = "```python\na=1\n```\nText\n```bash\nls -la\n```"
        blocks = parser.extract_code_blocks(text)

        assert len(blocks) == 2
        assert blocks[0][0] == "python"
        assert blocks[1][0] == "bash"

    def test_parse_returns_code_content_blocks(self, parser):
        """parse() deve retornar ContentBlock para código."""
        text = "```python\nprint('hello')\n```"
        blocks = parser.parse(text)

        code_blocks = [b for b in blocks if b.type == ContentType.CODE]
        assert len(code_blocks) >= 1
        assert code_blocks[0].language == "python"


class TestOutputParserThinking:
    """Testes de detecção de thinking."""

    @pytest.fixture
    def parser(self):
        return OutputParser()

    def test_detect_thinking_tags(self, parser):
        """Deve detectar <thinking> tags."""
        text = "<thinking>I need to analyze this</thinking>"
        results = parser.detect_thinking(text)

        assert len(results) >= 1
        assert "analyze" in results[0][0]

    def test_detect_thinking_pattern(self, parser):
        """Deve detectar padrão 'Thinking...'."""
        text = "Thinking...\nAnalyzing the problem\n"
        results = parser.detect_thinking(text)

        assert len(results) >= 1


class TestOutputParserToolCalls:
    """Testes de detecção de tool calls."""

    @pytest.fixture
    def parser(self):
        return OutputParser()

    def test_detect_tool_call_emoji(self, parser):
        """Deve detectar tool call com emoji."""
        text = "⚡ Read /path/to/file"
        results = parser.detect_tool_calls(text)

        assert len(results) >= 1
        tool_name = results[0][0]
        assert tool_name == "Read"

    def test_detect_running_pattern(self, parser):
        """Deve detectar padrão 'Running Tool:'."""
        text = "Running Bash: ls -la"
        results = parser.detect_tool_calls(text)

        assert len(results) >= 1

    def test_filter_common_functions(self, parser):
        """Não deve detectar funções comuns como tools."""
        text = "print(hello) str(value)"
        results = parser.detect_tool_calls(text)

        # Should not include print or str
        tool_names = [r[0].lower() for r in results]
        assert "print" not in tool_names
        assert "str" not in tool_names


class TestOutputParserErrors:
    """Testes de detecção de erros."""

    @pytest.fixture
    def parser(self):
        return OutputParser()

    def test_detect_error_pattern(self, parser):
        """Deve detectar padrão 'Error:'."""
        text = "Error: File not found"
        results = parser.detect_errors(text)

        assert len(results) >= 1
        assert "File not found" in results[0][0]

    def test_detect_error_emoji(self, parser):
        """Deve detectar erro com emoji."""
        text = "❌ Operation failed"
        results = parser.detect_errors(text)

        assert len(results) >= 1

    def test_detect_failed_pattern(self, parser):
        """Deve detectar padrão 'Failed:'."""
        text = "Failed: Connection refused"
        results = parser.detect_errors(text)

        assert len(results) >= 1


class TestOutputParserLineParsing:
    """Testes de parsing linha a linha."""

    @pytest.fixture
    def parser(self):
        return OutputParser()

    def test_parse_line_returns_error_block(self, parser):
        """parse_line deve retornar ERROR block para erros."""
        line = "Error: Something went wrong"
        block = parser.parse_line(line)

        assert block is not None
        assert block.type == ContentType.ERROR

    def test_parse_line_returns_text_block(self, parser):
        """parse_line deve retornar TEXT block para texto normal."""
        line = "Hello, this is a response"
        block = parser.parse_line(line)

        assert block is not None
        assert block.type == ContentType.TEXT

    def test_parse_line_empty_returns_none(self, parser):
        """parse_line deve retornar None para linha vazia."""
        block = parser.parse_line("")
        assert block is None

    def test_parse_line_whitespace_returns_none(self, parser):
        """parse_line deve retornar None para whitespace."""
        block = parser.parse_line("   ")
        assert block is None


class TestOutputParserSystemMessages:
    """Testes de detecção de mensagens de sistema."""

    @pytest.fixture
    def parser(self):
        return OutputParser()

    def test_detect_system_tag(self, parser):
        """Deve detectar [system] tag."""
        text = "[system] Session started"
        results = parser.detect_system_messages(text)

        assert len(results) >= 1

    def test_detect_info_emoji(self, parser):
        """Deve detectar mensagem com emoji info."""
        text = "ℹ️ Information message"
        results = parser.detect_system_messages(text)

        assert len(results) >= 1


class TestOutputParserIntegration:
    """Testes de integração do parser."""

    @pytest.fixture
    def parser(self):
        return OutputParser()

    def test_parse_mixed_content(self, parser):
        """Deve parsear conteúdo misto corretamente."""
        text = """Here is some code:
```python
def hello():
    print("Hello")
```
And here is the result.
Error: Something went wrong
"""
        blocks = parser.parse(text)

        # Should have at least code and error blocks
        types = [b.type for b in blocks]
        assert ContentType.CODE in types
        assert ContentType.ERROR in types

    def test_blocks_have_timestamps(self, parser):
        """Todos os blocks devem ter timestamps."""
        text = "```python\ncode\n```"
        blocks = parser.parse(text)

        for block in blocks:
            assert block.timestamp is not None
