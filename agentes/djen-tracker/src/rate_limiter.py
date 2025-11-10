"""
RateLimiter - Controle inteligente de taxa de requisições com backoff exponencial
"""
import time
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter inteligente com:
    - Controle de requisições por minuto
    - Delay fixo entre requisições
    - Backoff exponencial em caso de 429 (Too Many Requests)
    - Histórico de requisições para análise

    Exemplo:
        >>> limiter = RateLimiter(requests_per_minute=20, delay_seconds=3)
        >>> limiter.wait()  # Espera se necessário antes da requisição
        >>> # fazer requisição...
        >>> limiter.record_request()  # Registra requisição
        >>> if response.status_code == 429:
        ...     limiter.trigger_backoff()  # Ativa backoff exponencial
    """

    def __init__(
        self,
        requests_per_minute: int = 20,
        delay_seconds: float = 3.0,
        max_backoff_seconds: int = 300,
        enable_backoff: bool = True
    ):
        """
        Inicializa RateLimiter.

        Args:
            requests_per_minute: Máximo de requisições por minuto
            delay_seconds: Delay fixo entre requisições (segundos)
            max_backoff_seconds: Backoff máximo em segundos (default: 5min)
            enable_backoff: Se True, usa backoff exponencial em 429
        """
        self.requests_per_minute = requests_per_minute
        self.delay_seconds = delay_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.enable_backoff = enable_backoff

        # Histórico de requisições (timestamp)
        self.request_history = deque(maxlen=requests_per_minute)

        # Controle de backoff
        self.backoff_level = 0
        self.last_backoff_time = None
        self.last_request_time = None

        logger.info(
            f"RateLimiter inicializado: {requests_per_minute} req/min, "
            f"delay={delay_seconds}s, backoff={enable_backoff}"
        )

    def wait(self) -> float:
        """
        Espera necessária antes de fazer próxima requisição.

        Combina:
        1. Delay fixo desde última requisição
        2. Limite de requisições por minuto
        3. Backoff exponencial (se ativo)

        Returns:
            Tempo esperado em segundos
        """
        wait_time = 0.0
        now = datetime.now()

        # 1. Backoff exponencial (se ativo)
        if self.backoff_level > 0 and self.enable_backoff:
            backoff_wait = min(
                2 ** self.backoff_level,
                self.max_backoff_seconds
            )
            logger.warning(
                f"Backoff ativo (level {self.backoff_level}): "
                f"aguardando {backoff_wait}s"
            )
            time.sleep(backoff_wait)
            wait_time += backoff_wait

            # Reduzir backoff level gradualmente
            self.backoff_level = max(0, self.backoff_level - 1)

        # 2. Delay fixo desde última requisição
        if self.last_request_time:
            elapsed = (now - self.last_request_time).total_seconds()
            if elapsed < self.delay_seconds:
                delay_wait = self.delay_seconds - elapsed
                logger.debug(f"Delay fixo: aguardando {delay_wait:.2f}s")
                time.sleep(delay_wait)
                wait_time += delay_wait

        # 3. Limite de requisições por minuto
        if len(self.request_history) >= self.requests_per_minute:
            # Verificar tempo desde a requisição mais antiga
            oldest_request = self.request_history[0]
            time_since_oldest = (now - oldest_request).total_seconds()

            if time_since_oldest < 60:
                # Ainda dentro da janela de 1 minuto
                window_wait = 60 - time_since_oldest + 1  # +1 margem
                logger.warning(
                    f"Limite de {self.requests_per_minute} req/min atingido: "
                    f"aguardando {window_wait:.0f}s"
                )
                time.sleep(window_wait)
                wait_time += window_wait

        return wait_time

    def record_request(self):
        """Registra requisição no histórico."""
        now = datetime.now()
        self.request_history.append(now)
        self.last_request_time = now

        logger.debug(
            f"Requisição registrada "
            f"({len(self.request_history)}/{self.requests_per_minute} últimos 60s)"
        )

    def trigger_backoff(self, status_code: Optional[int] = 429):
        """
        Ativa backoff exponencial.

        Args:
            status_code: Código HTTP que causou backoff (default: 429)
        """
        if not self.enable_backoff:
            return

        self.backoff_level = min(self.backoff_level + 1, 8)  # Max 2^8 = 256s
        self.last_backoff_time = datetime.now()

        backoff_seconds = min(2 ** self.backoff_level, self.max_backoff_seconds)

        logger.warning(
            f"Backoff acionado (HTTP {status_code}): "
            f"level {self.backoff_level}, próximo wait ~{backoff_seconds}s"
        )

    def reset_backoff(self):
        """Reseta backoff para nível 0."""
        if self.backoff_level > 0:
            logger.info(f"Backoff resetado (era level {self.backoff_level})")
            self.backoff_level = 0

    def get_stats(self) -> dict:
        """
        Retorna estatísticas do rate limiter.

        Returns:
            Dict com estatísticas
        """
        if not self.request_history:
            return {
                'total_requests': 0,
                'requests_last_minute': 0,
                'average_interval': 0,
                'backoff_level': self.backoff_level,
                'last_request': None
            }

        # Calcular intervalo médio
        if len(self.request_history) > 1:
            intervals = [
                (self.request_history[i] - self.request_history[i-1]).total_seconds()
                for i in range(1, len(self.request_history))
            ]
            avg_interval = sum(intervals) / len(intervals)
        else:
            avg_interval = 0

        # Contar requisições no último minuto
        now = datetime.now()
        one_minute_ago = now - timedelta(seconds=60)
        recent_requests = sum(
            1 for ts in self.request_history
            if ts >= one_minute_ago
        )

        return {
            'total_requests': len(self.request_history),
            'requests_last_minute': recent_requests,
            'average_interval': round(avg_interval, 2),
            'backoff_level': self.backoff_level,
            'last_request': self.last_request_time.isoformat() if self.last_request_time else None
        }
