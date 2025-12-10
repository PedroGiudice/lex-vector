"""
Gemini Client - Wrapper para Gemini CLI.

Este módulo fornece interface Python para o Gemini CLI,
otimizado para processar arquivos grandes diretamente.

IMPORTANTE: Gemini lê arquivos diretamente para context offloading.
Não passar conteúdo via stdin para arquivos grandes - isso desperdiça tokens.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


@dataclass
class GeminiConfig:
    """Configuração do cliente Gemini."""

    model: Literal["gemini-2.5-flash", "gemini-2.5-pro"] = "gemini-2.5-flash"
    timeout_seconds: int = 300  # 5 min para arquivos grandes
    max_retries: int = 2


@dataclass
class GeminiResponse:
    """Resposta do Gemini."""

    text: str
    success: bool
    error: str | None = None
    model_used: str = ""


class GeminiClient:
    """
    Cliente para Gemini CLI.

    Usa subprocess para chamar `gemini` CLI diretamente.
    Otimizado para ler arquivos grandes sem carregar em memória Python.

    Example:
        >>> client = GeminiClient()
        >>> response = client.process_file(
        ...     file_path=Path("final.md"),
        ...     prompt="Classifique as seções deste documento jurídico..."
        ... )
        >>> if response.success:
        ...     print(response.text)
    """

    def __init__(self, config: GeminiConfig | None = None):
        """
        Inicializa cliente.

        Args:
            config: Configuração customizada
        """
        self.config = config or GeminiConfig()
        self._verify_cli_available()

    def _verify_cli_available(self) -> None:
        """Verifica se Gemini CLI está disponível."""
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise RuntimeError("Gemini CLI retornou erro")
            logger.debug(f"Gemini CLI disponível: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError(
                "Gemini CLI não encontrado. Instale com: pip install google-generativeai"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Gemini CLI timeout ao verificar versão")

    def process_file(
        self,
        file_path: Path,
        prompt: str,
        output_format: Literal["text", "json"] = "text",
    ) -> GeminiResponse:
        """
        Processa arquivo com Gemini.

        IMPORTANTE: O arquivo é lido e passado via stdin para o Gemini.
        Para arquivos muito grandes (>1MB), considere dividir em chunks.

        Args:
            file_path: Caminho do arquivo para processar
            prompt: Instrução para o Gemini
            output_format: Formato esperado do output

        Returns:
            GeminiResponse com resultado
        """
        if not file_path.exists():
            return GeminiResponse(
                text="",
                success=False,
                error=f"Arquivo não encontrado: {file_path}",
            )

        # Monta comando: gemini -m modelo "prompt"
        # Conteúdo do arquivo vai via stdin
        cmd = [
            "gemini",
            "-m", self.config.model,
            prompt,
        ]

        file_size = file_path.stat().st_size
        logger.info(f"Gemini: Processando {file_path.name} ({file_size:,} bytes)")

        for attempt in range(self.config.max_retries + 1):
            try:
                # Lê arquivo e passa via stdin
                with open(file_path, "r", encoding="utf-8") as f:
                    file_content = f.read()

                # Combina prompt + conteúdo
                full_input = f"{prompt}\n\n---\n\nDOCUMENTO:\n\n{file_content}"

                result = subprocess.run(
                    ["gemini", "-m", self.config.model],
                    input=full_input,
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout_seconds,
                )

                if result.returncode == 0:
                    text = result.stdout.strip()

                    # Valida JSON se esperado
                    if output_format == "json":
                        try:
                            json.loads(text)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Output não é JSON válido: {e}")
                            # Tenta extrair JSON do output
                            text = self._extract_json(text)

                    return GeminiResponse(
                        text=text,
                        success=True,
                        model_used=self.config.model,
                    )
                else:
                    error = result.stderr.strip() or "Erro desconhecido"
                    logger.warning(f"Gemini erro (tentativa {attempt + 1}): {error}")

            except subprocess.TimeoutExpired:
                logger.warning(f"Gemini timeout (tentativa {attempt + 1})")
            except Exception as e:
                logger.warning(f"Gemini exceção (tentativa {attempt + 1}): {e}")

        return GeminiResponse(
            text="",
            success=False,
            error=f"Falha após {self.config.max_retries + 1} tentativas",
        )

    def process_text(self, text: str, prompt: str) -> GeminiResponse:
        """
        Processa texto direto (para textos pequenos).

        Para textos grandes, prefira process_file().

        Args:
            text: Texto para processar
            prompt: Instrução

        Returns:
            GeminiResponse
        """
        full_input = f"{prompt}\n\n---\n\n{text}"

        try:
            result = subprocess.run(
                ["gemini", "-m", self.config.model],
                input=full_input,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
            )

            if result.returncode == 0:
                return GeminiResponse(
                    text=result.stdout.strip(),
                    success=True,
                    model_used=self.config.model,
                )
            else:
                return GeminiResponse(
                    text="",
                    success=False,
                    error=result.stderr.strip(),
                )
        except Exception as e:
            return GeminiResponse(
                text="",
                success=False,
                error=str(e),
            )

    @staticmethod
    def _extract_json(text: str) -> str:
        """
        Tenta extrair JSON de texto que pode ter markdown code blocks.

        Args:
            text: Texto potencialmente com ```json ... ```

        Returns:
            JSON extraído ou texto original
        """
        import re

        # Tenta extrair de code block
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            return match.group(1).strip()

        # Tenta encontrar { ... } ou [ ... ]
        for start, end in [('{', '}'), ('[', ']')]:
            first = text.find(start)
            last = text.rfind(end)
            if first != -1 and last > first:
                candidate = text[first:last + 1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    continue

        return text
