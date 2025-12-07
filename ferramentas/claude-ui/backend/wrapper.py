"""
Core wrapper para o Claude Code CLI.

Responsabilidades:
- Spawn e gestão do processo subprocess
- Leitura não-bloqueante de stdout/stderr via threads
- Escrita para stdin
- Detecção de estado (idle/thinking/executing)
- Callbacks para output e mudanças de estado
"""
import subprocess
import threading
import queue
import shutil
import signal
import time
import logging
from pathlib import Path
from typing import Optional, Callable, List
from .models import CLIState, StatusLineData
from .exceptions import CLINotFoundError, CLIConnectionError

logger = logging.getLogger(__name__)


class ClaudeCodeWrapper:
    """
    Wrapper para comunicação com o Claude Code CLI.

    Usage:
        wrapper = ClaudeCodeWrapper(
            project_path="/path/to/project",
            on_output=lambda text: print(text),
            on_state_change=lambda state: print(f"State: {state}")
        )
        wrapper.start()
        wrapper.send("Hello Claude")
        # ...
        wrapper.stop()
    """

    # Patterns for state detection
    THINKING_PATTERNS = ['Thinking', '⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    TOOL_PATTERNS = ['Running', 'Executing', '⚡', 'bash', 'Read(', 'Write(', 'Edit(']
    IDLE_PATTERNS = ['>', '❯', '›']

    def __init__(
        self,
        project_path: str,
        on_output: Optional[Callable[[str], None]] = None,
        on_state_change: Optional[Callable[[CLIState], None]] = None,
        on_statusline: Optional[Callable[[StatusLineData], None]] = None,
        skip_permissions: bool = True,
        auto_reconnect: bool = True
    ):
        self.project_path = Path(project_path).resolve()
        self.on_output = on_output
        self.on_state_change = on_state_change
        self.on_statusline = on_statusline
        self.skip_permissions = skip_permissions
        self.auto_reconnect = auto_reconnect

        self._process: Optional[subprocess.Popen] = None
        self._state = CLIState.DISCONNECTED
        self._output_queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._statusline_data: Optional[StatusLineData] = None
        self._lock = threading.Lock()

    def start(self) -> bool:
        """
        Inicia o processo CLI.

        Returns:
            True se iniciou com sucesso

        Raises:
            CLINotFoundError: Se 'claude' não está no PATH
            CLIConnectionError: Se falhou ao iniciar processo
        """
        if not self._check_cli_installed():
            raise CLINotFoundError("Claude Code CLI not found in PATH. Install with: npm install -g @anthropic-ai/claude-code")

        self._set_state(CLIState.STARTING)
        self._stop_event.clear()

        try:
            cmd = self._build_command()
            logger.info(f"Starting CLI with command: {' '.join(cmd)}")

            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_path),
                text=True,
                bufsize=1  # Line buffered
            )

            # Start reader threads
            self._stdout_thread = threading.Thread(
                target=self._reader_thread,
                args=(self._process.stdout, "stdout"),
                daemon=True
            )
            self._stderr_thread = threading.Thread(
                target=self._reader_thread,
                args=(self._process.stderr, "stderr"),
                daemon=True
            )
            self._monitor_thread = threading.Thread(
                target=self._monitor_process,
                daemon=True
            )

            self._stdout_thread.start()
            self._stderr_thread.start()
            self._monitor_thread.start()

            self._set_state(CLIState.IDLE)
            logger.info("CLI started successfully")
            return True

        except Exception as e:
            self._set_state(CLIState.ERROR)
            raise CLIConnectionError(f"Failed to start CLI: {e}") from e

    def stop(self, timeout: float = 5.0) -> None:
        """
        Para o processo CLI gracefully.

        Args:
            timeout: Segundos para esperar antes de SIGKILL
        """
        logger.info("Stopping CLI...")
        self._stop_event.set()

        if self._process is None:
            self._set_state(CLIState.DISCONNECTED)
            return

        try:
            # Try graceful termination first
            self._process.terminate()
            try:
                self._process.wait(timeout=timeout)
                logger.info("CLI terminated gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                logger.warning("CLI not responding, sending SIGKILL")
                self._process.kill()
                self._process.wait(timeout=2.0)
        except Exception as e:
            logger.error(f"Error stopping CLI: {e}")
        finally:
            self._process = None
            self._set_state(CLIState.DISCONNECTED)

    def send(self, message: str) -> None:
        """
        Envia mensagem para o CLI via stdin.

        Args:
            message: Texto a enviar (newline adicionado automaticamente)

        Raises:
            CLIConnectionError: Se processo não está rodando
        """
        if not self.is_alive():
            raise CLIConnectionError("CLI process is not running")

        try:
            self._process.stdin.write(message + "\n")
            self._process.stdin.flush()
            logger.debug(f"Sent message: {message[:50]}...")
        except Exception as e:
            raise CLIConnectionError(f"Failed to send message: {e}") from e

    def send_command(self, command: str) -> None:
        """
        Envia comando slash para o CLI (e.g., /status, /compact).

        Args:
            command: Comando com ou sem / inicial
        """
        if not command.startswith("/"):
            command = "/" + command
        self.send(command)

    def get_output(self, timeout: float = 0.1) -> List[str]:
        """
        Obtém linhas de output pendentes (non-blocking).

        Args:
            timeout: Segundos para esperar por output

        Returns:
            Lista de linhas de output (pode ser vazia)
        """
        lines = []
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                line = self._output_queue.get(timeout=0.01)
                lines.append(line)
            except queue.Empty:
                if lines:  # Return what we have if we got something
                    break

        return lines

    def get_state(self) -> CLIState:
        """Retorna estado atual do CLI."""
        return self._state

    def is_alive(self) -> bool:
        """Verifica se processo está rodando."""
        return self._process is not None and self._process.poll() is None

    def get_statusline(self) -> Optional[StatusLineData]:
        """Retorna dados mais recentes da statusline (se disponível)."""
        return self._statusline_data

    # Private methods
    def _check_cli_installed(self) -> bool:
        """Verifica se 'claude' está no PATH."""
        return shutil.which("claude") is not None

    def _build_command(self) -> List[str]:
        """Constrói lista de argumentos para subprocess."""
        cmd = ["claude"]

        if self.skip_permissions:
            cmd.append("--dangerously-skip-permissions")

        return cmd

    def _reader_thread(self, stream, stream_name: str) -> None:
        """Thread que lê stream e enfileira output."""
        try:
            for line in stream:
                if self._stop_event.is_set():
                    break

                line = line.rstrip('\n\r')
                if not line:
                    continue

                # Enqueue for consumers
                self._output_queue.put(line)

                # Callback
                if self.on_output:
                    try:
                        self.on_output(line)
                    except Exception as e:
                        logger.error(f"Error in on_output callback: {e}")

                # Detect state changes
                new_state = self._detect_state_from_output(line)
                if new_state and new_state != self._state:
                    self._set_state(new_state)

                logger.debug(f"[{stream_name}] {line[:100]}")

        except Exception as e:
            if not self._stop_event.is_set():
                logger.error(f"Error reading {stream_name}: {e}")

    def _detect_state_from_output(self, line: str) -> Optional[CLIState]:
        """Detecta mudança de estado baseado no output."""
        # Check for thinking patterns
        for pattern in self.THINKING_PATTERNS:
            if pattern in line:
                return CLIState.THINKING

        # Check for tool execution patterns
        for pattern in self.TOOL_PATTERNS:
            if pattern in line:
                return CLIState.EXECUTING

        # Check for idle/prompt patterns (usually at start of line)
        stripped = line.strip()
        for pattern in self.IDLE_PATTERNS:
            if stripped.startswith(pattern) or stripped.endswith(pattern):
                return CLIState.IDLE

        return None

    def _monitor_process(self) -> None:
        """Monitor thread que detecta morte do processo."""
        while not self._stop_event.is_set():
            if self._process is not None:
                ret = self._process.poll()
                if ret is not None:
                    logger.warning(f"CLI process died with return code {ret}")
                    self._handle_process_death()
                    break
            time.sleep(0.5)

    def _handle_process_death(self) -> None:
        """Chamado quando processo morre inesperadamente."""
        self._process = None
        self._set_state(CLIState.DISCONNECTED)

        if self.auto_reconnect and not self._stop_event.is_set():
            logger.info("Attempting to reconnect...")
            time.sleep(1.0)
            try:
                self.start()
            except Exception as e:
                logger.error(f"Failed to reconnect: {e}")
                self._set_state(CLIState.ERROR)

    def _set_state(self, new_state: CLIState) -> None:
        """Atualiza estado e notifica callback."""
        with self._lock:
            if new_state != self._state:
                old_state = self._state
                self._state = new_state
                logger.debug(f"State changed: {old_state.value} -> {new_state.value}")

                if self.on_state_change:
                    try:
                        self.on_state_change(new_state)
                    except Exception as e:
                        logger.error(f"Error in on_state_change callback: {e}")

    def __enter__(self):
        """Context manager support."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.stop()
        return False
