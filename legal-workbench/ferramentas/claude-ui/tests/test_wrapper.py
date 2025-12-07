"""Testes para ClaudeCodeWrapper."""
import pytest
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import Mock, patch, MagicMock
from backend.wrapper import ClaudeCodeWrapper
from backend.models import CLIState
from backend.exceptions import CLINotFoundError, CLIConnectionError


class TestClaudeCodeWrapperInit:
    """Testes de inicialização do wrapper."""

    def test_initial_state_is_disconnected(self):
        """Estado inicial deve ser DISCONNECTED."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        assert wrapper.get_state() == CLIState.DISCONNECTED

    def test_project_path_is_resolved(self):
        """Project path deve ser resolvido para caminho absoluto."""
        wrapper = ClaudeCodeWrapper(project_path=".")
        assert wrapper.project_path.is_absolute()

    def test_default_skip_permissions_is_true(self):
        """skip_permissions deve ser True por padrão."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        assert wrapper.skip_permissions is True

    def test_default_auto_reconnect_is_true(self):
        """auto_reconnect deve ser True por padrão."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        assert wrapper.auto_reconnect is True


class TestClaudeCodeWrapperCLICheck:
    """Testes de verificação do CLI."""

    def test_check_cli_not_installed(self):
        """Deve retornar False se claude não está no PATH."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        with patch('shutil.which', return_value=None):
            assert wrapper._check_cli_installed() is False

    def test_check_cli_installed(self):
        """Deve retornar True se claude está no PATH."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        with patch('shutil.which', return_value="/usr/bin/claude"):
            assert wrapper._check_cli_installed() is True

    def test_start_raises_cli_not_found(self):
        """Deve levantar CLINotFoundError se claude não está no PATH."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        with patch('shutil.which', return_value=None):
            with pytest.raises(CLINotFoundError):
                wrapper.start()


class TestClaudeCodeWrapperBuildCommand:
    """Testes de construção do comando."""

    def test_build_command_with_skip_permissions(self):
        """Deve incluir --dangerously-skip-permissions quando habilitado."""
        wrapper = ClaudeCodeWrapper(
            project_path="/tmp",
            skip_permissions=True
        )
        cmd = wrapper._build_command()
        assert "claude" in cmd
        assert "--dangerously-skip-permissions" in cmd

    def test_build_command_without_skip_permissions(self):
        """Não deve incluir flag quando desabilitado."""
        wrapper = ClaudeCodeWrapper(
            project_path="/tmp",
            skip_permissions=False
        )
        cmd = wrapper._build_command()
        assert "claude" in cmd
        assert "--dangerously-skip-permissions" not in cmd


class TestClaudeCodeWrapperStateDetection:
    """Testes de detecção de estado."""

    def test_detect_thinking_state(self):
        """Deve detectar estado THINKING."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")

        # Test various thinking patterns
        assert wrapper._detect_state_from_output("Thinking...") == CLIState.THINKING
        assert wrapper._detect_state_from_output("⠋ Processing") == CLIState.THINKING
        assert wrapper._detect_state_from_output("⠹ Working") == CLIState.THINKING

    def test_detect_executing_state(self):
        """Deve detectar estado EXECUTING."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")

        # Test tool execution patterns
        assert wrapper._detect_state_from_output("Running bash") == CLIState.EXECUTING
        assert wrapper._detect_state_from_output("⚡ Executing command") == CLIState.EXECUTING
        assert wrapper._detect_state_from_output("Read(/path/to/file)") == CLIState.EXECUTING

    def test_detect_idle_state(self):
        """Deve detectar estado IDLE."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")

        # Test idle/prompt patterns
        assert wrapper._detect_state_from_output("> ") == CLIState.IDLE
        assert wrapper._detect_state_from_output("❯") == CLIState.IDLE

    def test_no_state_change_for_regular_text(self):
        """Não deve mudar estado para texto regular."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")

        assert wrapper._detect_state_from_output("Hello world") is None
        assert wrapper._detect_state_from_output("Some output text") is None


class TestClaudeCodeWrapperCallbacks:
    """Testes de callbacks."""

    def test_on_output_callback_stored(self):
        """Callback on_output deve ser armazenado."""
        callback = Mock()
        wrapper = ClaudeCodeWrapper(
            project_path="/tmp",
            on_output=callback
        )
        assert wrapper.on_output is callback

    def test_on_state_change_callback_stored(self):
        """Callback on_state_change deve ser armazenado."""
        callback = Mock()
        wrapper = ClaudeCodeWrapper(
            project_path="/tmp",
            on_state_change=callback
        )
        assert wrapper.on_state_change is callback


class TestClaudeCodeWrapperIsAlive:
    """Testes do método is_alive."""

    def test_is_alive_false_when_no_process(self):
        """is_alive deve ser False quando não há processo."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        assert wrapper.is_alive() is False

    def test_is_alive_false_after_stop(self):
        """is_alive deve ser False após stop()."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        wrapper.stop()  # Should handle gracefully even without process
        assert wrapper.is_alive() is False


class TestClaudeCodeWrapperSendCommand:
    """Testes de send_command."""

    def test_send_command_adds_slash(self):
        """send_command deve adicionar / se não presente."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")

        # Mock the send method to capture what's sent
        wrapper.send = Mock()

        # Test without slash
        wrapper.send_command("status")
        wrapper.send.assert_called_with("/status")

    def test_send_command_keeps_slash(self):
        """send_command deve manter / se já presente."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")

        wrapper.send = Mock()

        # Test with slash
        wrapper.send_command("/status")
        wrapper.send.assert_called_with("/status")


class TestClaudeCodeWrapperContextManager:
    """Testes do context manager."""

    def test_context_manager_calls_start_and_stop(self):
        """Context manager deve chamar start() e stop()."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        wrapper.start = Mock(return_value=True)
        wrapper.stop = Mock()

        with wrapper:
            wrapper.start.assert_called_once()

        wrapper.stop.assert_called_once()


# Additional edge case tests
class TestClaudeCodeWrapperEdgeCases:
    """Testes de casos extremos."""

    def test_stop_without_start_is_safe(self):
        """stop() sem start() não deve falhar."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        # Should not raise
        wrapper.stop()
        assert wrapper.get_state() == CLIState.DISCONNECTED

    def test_get_output_empty_when_disconnected(self):
        """get_output deve retornar lista vazia quando desconectado."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        output = wrapper.get_output(timeout=0.1)
        assert output == []

    def test_get_statusline_none_initially(self):
        """get_statusline deve retornar None inicialmente."""
        wrapper = ClaudeCodeWrapper(project_path="/tmp")
        assert wrapper.get_statusline() is None
