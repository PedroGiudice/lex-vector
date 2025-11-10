"""
ContinuousDownloader - Download contínuo de cadernos DJEN com rate limiting
"""
import json
import logging
import time
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

# Importar componentes do oab-watcher (integração)
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "oab-watcher"))
try:
    from src import CacheManager, TextParser, BuscaInteligente
    OAB_WATCHER_AVAILABLE = True
except ImportError:
    OAB_WATCHER_AVAILABLE = False
    logging.warning("oab-watcher não disponível, funcionalidades de análise desabilitadas")

import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class DownloadStatus:
    """Status de um download."""
    tribunal: str
    data: str
    meio: str
    status: str  # 'sucesso', 'falha', 'duplicata', 'processando'
    arquivo: Optional[str] = None
    tamanho_bytes: int = 0
    tempo_download: float = 0
    erro: Optional[str] = None


class ContinuousDownloader:
    """
    Downloader contínuo de cadernos DJEN.

    Roda indefinidamente até ser interrompido (Ctrl+C), baixando:
    - STF (Supremo Tribunal Federal)
    - STJ (Superior Tribunal de Justiça)
    - TJSP 2ª Instância (Tribunal de Justiça de São Paulo)

    Features:
    - Rate limiting inteligente
    - Checkpoint para resumir downloads
    - Integração com oab-watcher para análise
    - Estatísticas em tempo real
    - Retry automático
    """

    def __init__(self, config: Dict):
        """
        Inicializa ContinuousDownloader.

        Args:
            config: Dict de configuração (config.json)
        """
        self.config = config

        # Paths
        self.data_root = Path(config['paths']['data_root'])
        self.cadernos_dir = self.data_root / config['paths']['cadernos']
        self.logs_dir = self.data_root / config['paths']['logs']
        self.checkpoint_file = self.data_root / config['paths']['checkpoint']

        # Criar diretórios
        self.cadernos_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiter
        self.rate_limiter = RateLimiter(
            requests_per_minute=config['rate_limiting']['requests_per_minute'],
            delay_seconds=config['rate_limiting']['delay_between_requests_seconds'],
            max_backoff_seconds=config['rate_limiting']['max_backoff_seconds'],
            enable_backoff=config['rate_limiting']['backoff_on_429']
        )

        # HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config['scraping']['user_agent'],
            'Accept': 'application/json'
        })

        # Checkpoint (resumir downloads)
        self.checkpoint = self._load_checkpoint()

        # Estatísticas
        self.stats = {
            'total_downloads': 0,
            'sucessos': 0,
            'falhas': 0,
            'duplicatas': 0,
            'bytes_baixados': 0,
            'tempo_total': 0,
            'inicio': datetime.now().isoformat()
        }

        # Integração oab-watcher
        self.oab_integration_enabled = (
            config.get('integracao_oab_watcher', {}).get('enabled', False)
            and OAB_WATCHER_AVAILABLE
        )

        if self.oab_integration_enabled:
            cache_dir = self.data_root / "cache"
            self.cache_manager = CacheManager(cache_dir)
            self.text_parser = TextParser()
            logger.info("Integração oab-watcher ATIVA")

        logger.info(f"ContinuousDownloader inicializado: {self.data_root}")

    def _load_checkpoint(self) -> Dict:
        """Carrega checkpoint de downloads anteriores."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                logger.info(f"Checkpoint carregado: {len(checkpoint)} entradas")
                return checkpoint
            except Exception as e:
                logger.error(f"Erro ao carregar checkpoint: {e}")
                return {}
        return {}

    def _save_checkpoint(self):
        """Salva checkpoint."""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.checkpoint, f, indent=2)
            logger.debug("Checkpoint salvo")
        except Exception as e:
            logger.error(f"Erro ao salvar checkpoint: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    def _fetch_cadernos_disponiveis(
        self,
        tribunal: str,
        data: str
    ) -> List[Dict]:
        """
        Busca cadernos disponíveis na API.

        Args:
            tribunal: Sigla (STF, STJ, TJSP)
            data: Data (YYYY-MM-DD)

        Returns:
            Lista de cadernos disponíveis
        """
        # Rate limiting
        self.rate_limiter.wait()

        url = "https://comunicaapi.pje.jus.br/api/v1/cadernos"
        params = {
            'siglaTribunal': tribunal,
            'data': data
        }

        try:
            response = self.session.get(url, params=params, timeout=30)

            # Tratar 429 (Too Many Requests)
            if response.status_code == 429:
                self.rate_limiter.trigger_backoff(429)
                raise Exception("Rate limit exceeded (429)")

            response.raise_for_status()
            self.rate_limiter.record_request()

            data = response.json()
            cadernos = data.get('items', [])

            logger.info(f"[{tribunal}] {len(cadernos)} cadernos disponíveis em {data}")

            return cadernos

        except requests.RequestException as e:
            logger.error(f"Erro ao buscar cadernos {tribunal}/{data}: {e}")
            raise

    def _download_caderno(
        self,
        caderno: Dict,
        tribunal: str
    ) -> DownloadStatus:
        """
        Baixa um caderno individual.

        Args:
            caderno: Dict com dados do caderno
            tribunal: Sigla do tribunal

        Returns:
            DownloadStatus
        """
        hash_caderno = caderno.get('hash', 'unknown')
        data = caderno.get('data', 'unknown')
        meio = caderno.get('meio', 'unknown')
        url = caderno.get('url', '')

        # Nome do arquivo
        filename = f"{tribunal}_{data}_{meio}_{hash_caderno}.pdf"
        output_path = self.cadernos_dir / tribunal / filename

        # Verificar se já baixou
        checkpoint_key = f"{tribunal}_{hash_caderno}"
        if checkpoint_key in self.checkpoint:
            logger.debug(f"[{tribunal}] Duplicata: {filename}")
            return DownloadStatus(
                tribunal=tribunal,
                data=data,
                meio=meio,
                status='duplicata',
                arquivo=str(output_path)
            )

        # Criar diretório
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Rate limiting
        self.rate_limiter.wait()

        # Download
        inicio = time.time()
        try:
            response = self.session.get(url, timeout=60, stream=True)

            if response.status_code == 429:
                self.rate_limiter.trigger_backoff(429)
                raise Exception("Rate limit exceeded (429)")

            response.raise_for_status()
            self.rate_limiter.record_request()

            # Salvar arquivo
            total_bytes = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    total_bytes += len(chunk)

            tempo = time.time() - inicio

            # Registrar no checkpoint
            self.checkpoint[checkpoint_key] = {
                'arquivo': str(output_path),
                'timestamp': datetime.now().isoformat(),
                'tamanho': total_bytes
            }
            self._save_checkpoint()

            logger.info(
                f"[{tribunal}] ✓ {filename} "
                f"({total_bytes/1024/1024:.1f}MB em {tempo:.1f}s)"
            )

            return DownloadStatus(
                tribunal=tribunal,
                data=data,
                meio=meio,
                status='sucesso',
                arquivo=str(output_path),
                tamanho_bytes=total_bytes,
                tempo_download=tempo
            )

        except Exception as e:
            logger.error(f"[{tribunal}] ✗ Erro ao baixar {filename}: {e}")
            return DownloadStatus(
                tribunal=tribunal,
                data=data,
                meio=meio,
                status='falha',
                erro=str(e)
            )

    def run_once(self, data: Optional[str] = None) -> Dict:
        """
        Executa um ciclo de download (hoje ou data específica).

        Args:
            data: Data (YYYY-MM-DD) ou None para hoje

        Returns:
            Dict com estatísticas do ciclo
        """
        if not data:
            data = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"\n{'='*70}")
        logger.info(f"CICLO DE DOWNLOAD - {data}")
        logger.info(f"{'='*70}")

        tribunais = self.config['tribunais']['prioritarios']
        resultados = []

        for tribunal in tribunais:
            try:
                # Buscar cadernos disponíveis
                cadernos = self._fetch_cadernos_disponiveis(tribunal, data)

                # Baixar cada caderno
                for caderno in cadernos:
                    status = self._download_caderno(caderno, tribunal)
                    resultados.append(status)

                    # Atualizar estatísticas
                    self.stats['total_downloads'] += 1
                    if status.status == 'sucesso':
                        self.stats['sucessos'] += 1
                        self.stats['bytes_baixados'] += status.tamanho_bytes
                        self.stats['tempo_total'] += status.tempo_download
                    elif status.status == 'falha':
                        self.stats['falhas'] += 1
                    elif status.status == 'duplicata':
                        self.stats['duplicatas'] += 1

            except Exception as e:
                logger.error(f"Erro ao processar {tribunal}: {e}")

        # Resumo do ciclo
        sucessos = sum(1 for r in resultados if r.status == 'sucesso')
        falhas = sum(1 for r in resultados if r.status == 'falha')
        duplicatas = sum(1 for r in resultados if r.status == 'duplicata')

        logger.info(f"\n{'='*70}")
        logger.info(f"RESUMO DO CICLO - {data}")
        logger.info(f"Sucessos: {sucessos} | Falhas: {falhas} | Duplicatas: {duplicatas}")
        logger.info(f"{'='*70}\n")

        return {
            'data': data,
            'total': len(resultados),
            'sucessos': sucessos,
            'falhas': falhas,
            'duplicatas': duplicatas
        }

    def run_continuous(self, intervalo_minutos: Optional[int] = None):
        """
        Executa download contínuo (loop infinito).

        Args:
            intervalo_minutos: Intervalo entre ciclos (ou usa config)
        """
        intervalo = intervalo_minutos or self.config['download']['intervalo_minutos']

        logger.info(f"\n{'#'*70}")
        logger.info(f"DOWNLOAD CONTÍNUO INICIADO")
        logger.info(f"Intervalo: {intervalo} minutos")
        logger.info(f"Tribunais: {', '.join(self.config['tribunais']['prioritarios'])}")
        logger.info(f"Ctrl+C para interromper")
        logger.info(f"{'#'*70}\n")

        ciclo = 0

        try:
            while True:
                ciclo += 1
                logger.info(f">>> CICLO #{ciclo}")

                # Executar ciclo
                self.run_once()

                # Mostrar estatísticas
                logger.info(f"\n{'='*70}")
                logger.info(f"ESTATÍSTICAS GLOBAIS")
                logger.info(f"Total downloads: {self.stats['total_downloads']}")
                logger.info(f"Sucessos: {self.stats['sucessos']}")
                logger.info(f"Falhas: {self.stats['falhas']}")
                logger.info(f"Duplicatas: {self.stats['duplicatas']}")
                logger.info(f"Bytes baixados: {self.stats['bytes_baixados']/1024/1024:.1f}MB")
                logger.info(f"Rate limiter: {self.rate_limiter.get_stats()}")
                logger.info(f"{'='*70}\n")

                # Aguardar próximo ciclo
                logger.info(f"Aguardando {intervalo} minutos até próximo ciclo...")
                time.sleep(intervalo * 60)

        except KeyboardInterrupt:
            logger.info(f"\n{'#'*70}")
            logger.info("INTERROMPIDO PELO USUÁRIO (Ctrl+C)")
            logger.info(f"Total de ciclos: {ciclo}")
            logger.info(f"Estatísticas salvas em checkpoint")
            logger.info(f"{'#'*70}\n")
