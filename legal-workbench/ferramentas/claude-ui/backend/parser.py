"""
Parser para output do Claude Code CLI.

Responsabilidades:
- Detectar e extrair blocos de código (```language ... ```)
- Detectar thinking blocks
- Detectar tool calls e results
- Limpar ANSI escape sequences
- Converter para estrutura renderizável
"""
import re
from typing import List, Tuple, Optional
from datetime import datetime
from .models import ContentBlock, ContentType


class OutputParser:
    """
    Parse output do CLI em blocos estruturados.

    O Claude Code CLI emite output com:
    - Blocos de código com syntax highlighting
    - Seções de "thinking" (raciocínio do modelo)
    - Tool calls (bash, file operations, etc.)
    - Tool results
    - Texto normal

    Este parser identifica cada tipo e retorna lista de ContentBlock.
    """

    # ANSI escape sequence pattern
    ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    # Code block pattern: ```language\ncode\n```
    CODE_BLOCK = re.compile(r'```(\w*)\n?(.*?)```', re.DOTALL)

    # Thinking patterns
    THINKING_START = re.compile(r'<thinking>|Thinking\.\.\.|🤔', re.IGNORECASE)
    THINKING_END = re.compile(r'</thinking>|Done thinking', re.IGNORECASE)

    # Tool call patterns - matches various tool invocation formats
    TOOL_CALL_PATTERNS = [
        re.compile(r'⚡\s*(\w+)\s*(.*)'),  # ⚡ ToolName args
        re.compile(r'Running\s+(\w+):\s*(.*)'),  # Running Tool: args
        re.compile(r'(\w+)\((.*?)\)', re.DOTALL),  # Tool(args)
    ]

    # Tool result pattern
    TOOL_RESULT = re.compile(r'(?:Result|Output|✓):\s*(.*)', re.DOTALL | re.IGNORECASE)

    # Error patterns
    ERROR_PATTERNS = [
        re.compile(r'Error:\s*(.*)', re.IGNORECASE),
        re.compile(r'❌\s*(.*)'),
        re.compile(r'Failed:\s*(.*)', re.IGNORECASE),
    ]

    # System message patterns
    SYSTEM_PATTERNS = [
        re.compile(r'\[system\]\s*(.*)', re.IGNORECASE),
        re.compile(r'ℹ️\s*(.*)'),
    ]

    def __init__(self):
        """Initialize parser."""
        self._thinking_mode = False
        self._code_buffer = []
        self._current_language = ""

    def parse(self, raw_output: str) -> List[ContentBlock]:
        """
        Parse output raw em lista de blocos.

        Args:
            raw_output: Texto raw do CLI (pode conter ANSI codes)

        Returns:
            Lista ordenada de ContentBlock
        """
        # First strip ANSI codes
        clean_output = self.strip_ansi(raw_output)

        blocks = []

        # Extract code blocks first (they're the most structured)
        code_blocks_data = self.extract_code_blocks(clean_output)

        # Track positions that are part of code blocks
        code_positions = set()
        for lang, code, start, end in code_blocks_data:
            for i in range(start, end):
                code_positions.add(i)
            blocks.append(ContentBlock(
                type=ContentType.CODE,
                content=code.strip(),
                language=lang or "text",
                timestamp=datetime.now()
            ))

        # Extract thinking blocks
        thinking_data = self.detect_thinking(clean_output)
        for content, start, end in thinking_data:
            # Skip if overlaps with code
            if not any(i in code_positions for i in range(start, end)):
                blocks.append(ContentBlock(
                    type=ContentType.THINKING,
                    content=content.strip(),
                    timestamp=datetime.now()
                ))

        # Extract tool calls
        tool_calls = self.detect_tool_calls(clean_output)
        for tool_name, args, start, end in tool_calls:
            if not any(i in code_positions for i in range(start, end)):
                blocks.append(ContentBlock(
                    type=ContentType.TOOL_CALL,
                    content=args,
                    tool_name=tool_name,
                    timestamp=datetime.now()
                ))

        # Extract tool results
        tool_results = self.detect_tool_results(clean_output)
        for content, start, end in tool_results:
            if not any(i in code_positions for i in range(start, end)):
                blocks.append(ContentBlock(
                    type=ContentType.TOOL_RESULT,
                    content=content.strip(),
                    timestamp=datetime.now()
                ))

        # Extract errors
        errors = self.detect_errors(clean_output)
        for content, start, end in errors:
            if not any(i in code_positions for i in range(start, end)):
                blocks.append(ContentBlock(
                    type=ContentType.ERROR,
                    content=content.strip(),
                    timestamp=datetime.now()
                ))

        # Extract system messages
        system_msgs = self.detect_system_messages(clean_output)
        for content, start, end in system_msgs:
            if not any(i in code_positions for i in range(start, end)):
                blocks.append(ContentBlock(
                    type=ContentType.SYSTEM,
                    content=content.strip(),
                    timestamp=datetime.now()
                ))

        # Remaining text becomes TEXT blocks
        remaining = self._extract_remaining_text(clean_output, blocks)
        if remaining.strip():
            blocks.append(ContentBlock(
                type=ContentType.TEXT,
                content=remaining.strip(),
                timestamp=datetime.now()
            ))

        # Sort by timestamp (they should all be very close)
        return blocks

    def strip_ansi(self, text: str) -> str:
        """Remove ANSI escape sequences."""
        return self.ANSI_ESCAPE.sub('', text)

    def extract_code_blocks(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Extrai blocos de código.

        Returns:
            Lista de (language, code, start_pos, end_pos)
        """
        results = []
        for match in self.CODE_BLOCK.finditer(text):
            language = match.group(1) or ""
            code = match.group(2)
            results.append((language, code, match.start(), match.end()))
        return results

    def detect_thinking(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detecta seções de thinking/raciocínio.

        Returns:
            Lista de (content, start_pos, end_pos)
        """
        results = []

        # Look for <thinking>...</thinking> blocks
        thinking_pattern = re.compile(r'<thinking>(.*?)</thinking>', re.DOTALL | re.IGNORECASE)
        for match in thinking_pattern.finditer(text):
            results.append((match.group(1), match.start(), match.end()))

        # Also look for "Thinking..." sections (they usually end with newlines)
        lines = text.split('\n')
        in_thinking = False
        thinking_start = 0
        thinking_content = []
        current_pos = 0

        for line in lines:
            if self.THINKING_START.search(line) and not in_thinking:
                in_thinking = True
                thinking_start = current_pos
                thinking_content = [line]
            elif in_thinking:
                if self.THINKING_END.search(line) or (line.strip() == '' and thinking_content):
                    thinking_content.append(line)
                    results.append((
                        '\n'.join(thinking_content),
                        thinking_start,
                        current_pos + len(line)
                    ))
                    in_thinking = False
                    thinking_content = []
                else:
                    thinking_content.append(line)
            current_pos += len(line) + 1  # +1 for newline

        return results

    def detect_tool_calls(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Detecta tool calls.

        Returns:
            Lista de (tool_name, arguments, start_pos, end_pos)
        """
        results = []

        for pattern in self.TOOL_CALL_PATTERNS:
            for match in pattern.finditer(text):
                tool_name = match.group(1)
                args = match.group(2) if match.lastindex >= 2 else ""

                # Filter out common false positives
                if tool_name.lower() in ['print', 'str', 'int', 'len', 'range', 'list', 'dict']:
                    continue

                results.append((tool_name, args, match.start(), match.end()))

        return results

    def detect_tool_results(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detecta resultados de tool execution.

        Returns:
            Lista de (content, start_pos, end_pos)
        """
        results = []
        for match in self.TOOL_RESULT.finditer(text):
            results.append((match.group(1), match.start(), match.end()))
        return results

    def detect_errors(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detecta mensagens de erro.

        Returns:
            Lista de (content, start_pos, end_pos)
        """
        results = []
        for pattern in self.ERROR_PATTERNS:
            for match in pattern.finditer(text):
                results.append((match.group(1), match.start(), match.end()))
        return results

    def detect_system_messages(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Detecta mensagens de sistema.

        Returns:
            Lista de (content, start_pos, end_pos)
        """
        results = []
        for pattern in self.SYSTEM_PATTERNS:
            for match in pattern.finditer(text):
                results.append((match.group(1), match.start(), match.end()))
        return results

    def _extract_remaining_text(self, text: str, blocks: List[ContentBlock]) -> str:
        """
        Extract text that wasn't captured by other extractors.
        This is a simplified implementation.
        """
        # For now, return empty if we have blocks
        # A more sophisticated implementation would track positions
        if blocks:
            return ""
        return text

    def parse_line(self, line: str) -> Optional[ContentBlock]:
        """
        Parse uma única linha de output.

        Útil para streaming/real-time parsing.

        Args:
            line: Linha única de output

        Returns:
            ContentBlock ou None se linha não reconhecida
        """
        clean_line = self.strip_ansi(line)

        # Check for errors first (high priority)
        for pattern in self.ERROR_PATTERNS:
            match = pattern.match(clean_line)
            if match:
                return ContentBlock(
                    type=ContentType.ERROR,
                    content=match.group(1),
                    timestamp=datetime.now()
                )

        # Check for system messages
        for pattern in self.SYSTEM_PATTERNS:
            match = pattern.match(clean_line)
            if match:
                return ContentBlock(
                    type=ContentType.SYSTEM,
                    content=match.group(1),
                    timestamp=datetime.now()
                )

        # Check for tool calls
        for pattern in self.TOOL_CALL_PATTERNS:
            match = pattern.match(clean_line)
            if match:
                tool_name = match.group(1)
                if tool_name.lower() not in ['print', 'str', 'int', 'len']:
                    return ContentBlock(
                        type=ContentType.TOOL_CALL,
                        content=match.group(2) if match.lastindex >= 2 else "",
                        tool_name=tool_name,
                        timestamp=datetime.now()
                    )

        # Check for tool results
        match = self.TOOL_RESULT.match(clean_line)
        if match:
            return ContentBlock(
                type=ContentType.TOOL_RESULT,
                content=match.group(1),
                timestamp=datetime.now()
            )

        # Default to text
        if clean_line.strip():
            return ContentBlock(
                type=ContentType.TEXT,
                content=clean_line,
                timestamp=datetime.now()
            )

        return None
