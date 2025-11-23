"""
DJENDownloader - Download de publicações DJEN para base de jurisprudência

Baseado em:
- docs/ARQUITETURA_JURISPRUDENCIA.md
- docs/API_TESTING_REPRODUCIBLE.md
- agentes/djen-tracker/src/rate_limiter.py
"""
import hashlib
import logging
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json

# Import rate limiter from djen-tracker
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'djen-tracker' / 'src'))
from rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class PublicacaoRaw:
    """Dados brutos de uma publicação (antes de processamento)."""
    id: str
    hash_conteudo: str
    numero_processo: Optional[str]
    numero_processo_fmt: Optional[str]
    tribunal: str
    orgao_julgador: Optional[str]
    tipo_comunicacao: str
    classe_processual: Optional[str]
    texto_html: str
    data_publicacao: str
    destinatario_advogados: List[Dict]
    metadata: Dict  # Metadados adicionais da API


class DJENDownloader:
    """
    Downloader de publicações DJEN para construção de base de jurisprudência.

    Features:
    - Download via API (método preferido - mais rápido)
    - Download de caderno completo (fallback - mais completo)
    - Rate limiting inteligente (30 req/min)
    - Retry automático (3 tentativas com backoff exponencial)
    - Deduplicação via hash SHA256
    - Logging detalhado

    Baseado nos comandos validados em API_TESTING_REPRODUCIBLE.md
    """

    API_BASE_URL = "https://comunicaapi.pje.jus.br/api/v1"

    def __init__(
        self,
        data_root: Path,
        requests_per_minute: int = 280,
        adaptive_rate_limit: bool = True,
        max_retries: int = 3
    ):
        """
        Inicializa DJENDownloader.

        Args:
            data_root: Diretório raiz para armazenamento
            requests_per_minute: Limite de requisições por minuto
            adaptive_rate_limit: Habilitar rate limiting adaptativo com janela deslizante
            max_retries: Número máximo de tentativas em caso de falha
        """
        self.data_root = Path(data_root)
        self.max_retries = max_retries
        self.adaptive_rate_limit = adaptive_rate_limit

        # Rate limiting adaptativo - janela deslizante
        # Buffer conservador: 12 req/5s (~57% do limite da API de 21 req/5s)
        self.request_window_size = 12
        self.request_window_duration = 5.0  # segundos
        self.request_count = 0
        self.window_start = time.time()

        # Criar diretórios
        self.downloads_dir = self.data_root / 'downloads'
        self.logs_dir = self.data_root / 'logs'
        self.cache_dir = self.data_root / 'cache'

        for directory in [self.downloads_dir, self.logs_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Rate limiter (mantido para compatibilidade, mas não usado com adaptive_rate_limit=True)
        self.rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            delay_seconds=0.21,  # Delay mínimo entre requests
            max_backoff_seconds=300,
            enable_backoff=True
        )

        # HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; JurisprudenciaCollector/1.0)',
            'Accept': 'application/json'
        })

        # Cache de hashes (para deduplicação em memória)
        self.hash_cache = set()
        self._load_hash_cache()

        logger.info(f"DJENDownloader inicializado: {self.data_root}")
        if adaptive_rate_limit:
            logger.info(
                f"Rate limiting adaptativo: {self.request_window_size} req/"
                f"{self.request_window_duration}s (janela deslizante)"
            )
        else:
            logger.info(f"Rate limiting: {requests_per_minute} req/min")

    def _load_hash_cache(self):
        """Carrega cache de hashes de publicações já baixadas."""
        cache_file = self.cache_dir / 'hashes.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.hash_cache = set(data.get('hashes', []))
                logger.info(f"Hash cache carregado: {len(self.hash_cache)} entradas")
            except Exception as e:
                logger.error(f"Erro ao carregar hash cache: {e}")
                self.hash_cache = set()

    def _save_hash_cache(self):
        """Salva cache de hashes."""
        cache_file = self.cache_dir / 'hashes.json'
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'hashes': list(self.hash_cache),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            logger.debug("Hash cache salvo")
        except Exception as e:
            logger.error(f"Erro ao salvar hash cache: {e}")

    def _gerar_hash(self, texto: str) -> str:
        """
        Gera hash SHA256 de texto para deduplicação.

        Args:
            texto: Texto a ser hasheado

        Returns:
            Hash SHA256 hexadecimal
        """
        return hashlib.sha256(texto.encode('utf-8')).hexdigest()

    def _check_rate_limit(self):
        """
        Rate limiting adaptativo baseado em janela deslizante.

        Controla requisições para evitar HTTP 429 da API:
        - Limite: 12 requisições por janela de 5 segundos
        - Buffer de segurança conservador: API permite ~21, usamos 12 (57% do limite)
        - Pausa automática quando janela atinge limite
        """
        if not self.adaptive_rate_limit:
            # Usar RateLimiter antigo se adaptive desabilitado
            self.rate_limiter.wait()
            return

        self.request_count += 1

        # Se atingir limite da janela (buffer de segurança)
        if self.request_count >= self.request_window_size:
            elapsed = time.time() - self.window_start

            # Se janela ainda não expirou, pausar
            if elapsed < self.request_window_duration:
                sleep_time = self.request_window_duration - elapsed
                logger.debug(
                    f"Rate limit: pausando {sleep_time:.1f}s (window reset) - "
                    f"{self.request_count} req em {elapsed:.1f}s"
                )
                time.sleep(sleep_time)

            # Resetar janela
            self.request_count = 0
            self.window_start = time.time()

    def _fazer_requisicao(
        self,
        url: str,
        method: str = 'GET',
        **kwargs
    ) -> requests.Response:
        """
        Faz requisição HTTP com rate limiting adaptativo e retry automático.

        Args:
            url: URL da requisição
            method: Método HTTP (GET, POST)
            **kwargs: Argumentos adicionais para requests

        Returns:
            Response object

        Raises:
            Exception: Se todas as tentativas falharem
        """
        for tentativa in range(1, self.max_retries + 1):
            try:
                # Rate limiting adaptativo ANTES do request
                self._check_rate_limit()

                # Fazer requisição
                if method == 'GET':
                    response = self.session.get(url, timeout=30, **kwargs)
                elif method == 'POST':
                    response = self.session.post(url, timeout=30, **kwargs)
                else:
                    raise ValueError(f"Método HTTP não suportado: {method}")

                # Registrar requisição (para backward compatibility)
                if not self.adaptive_rate_limit:
                    self.rate_limiter.record_request()

                # Tratar rate limiting (429) com retry
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2))
                    logger.warning(
                        f"HTTP 429 (Rate Limit) - "
                        f"Aguardando {retry_after}s antes de retry {tentativa}/{self.max_retries}"
                    )
                    time.sleep(retry_after)

                    # Resetar janela de rate limit após 429
                    if self.adaptive_rate_limit:
                        self.request_count = 0
                        self.window_start = time.time()
                    else:
                        self.rate_limiter.trigger_backoff(429)

                    if tentativa < self.max_retries:
                        continue
                    else:
                        raise Exception("Rate limit exceeded após todas as tentativas")

                # Verificar status
                response.raise_for_status()
                return response

            except requests.exceptions.Timeout:
                if tentativa < self.max_retries:
                    backoff = 2 ** tentativa  # Exponential: 1s, 2s, 4s
                    logger.warning(
                        f"Timeout - Retry {tentativa}/{self.max_retries} em {backoff}s"
                    )
                    time.sleep(backoff)
                    continue
                logger.error(f"Timeout após {self.max_retries} tentativas")
                raise

            except requests.exceptions.RequestException as e:
                logger.warning(f"Erro na requisição (tentativa {tentativa}/{self.max_retries}): {e}")

                if tentativa < self.max_retries:
                    # Backoff exponencial: 2^tentativa segundos
                    backoff = 2 ** tentativa
                    logger.info(f"Aguardando {backoff}s antes de tentar novamente...")
                    time.sleep(backoff)
                else:
                    raise Exception(f"Falha após {self.max_retries} tentativas: {e}")

    def baixar_api(
        self,
        tribunal: str,
        data: str,
        limit: int = 100,
        max_pages: Optional[int] = None
    ) -> List[PublicacaoRaw]:
        """
        Baixa publicações via API DJEN.

        Baseado no comando validado:
        curl -s "https://comunicaapi.pje.jus.br/api/v1/comunicacao?
        dataInicio={data}&dataFim={data}&siglaTribunal={tribunal}&limit=100"

        Args:
            tribunal: Sigla do tribunal (STJ, TJSP, TRF3, etc)
            data: Data no formato YYYY-MM-DD
            limit: Itens por página (max: 100)
            max_pages: Limite de páginas a baixar (None = todas)

        Returns:
            Lista de PublicacaoRaw com dados brutos da API
        """
        logger.info(f"[{tribunal}] Baixando publicações via API - {data}")

        publicacoes = []
        page = 0
        total_pages = None
        duplicatas = 0

        while True:
            page += 1

            # Limitar páginas se especificado
            if max_pages and page > max_pages:
                logger.info(f"[{tribunal}] Limite de {max_pages} páginas atingido")
                break

            # Construir URL
            url = (
                f"{self.API_BASE_URL}/comunicacao"
                f"?dataInicio={data}"
                f"&dataFim={data}"
                f"&siglaTribunal={tribunal}"
                f"&limit={limit}"
                f"&page={page}"
            )

            logger.debug(f"[{tribunal}] Página {page}/{total_pages or '?'}")

            try:
                # Fazer requisição
                response = self._fazer_requisicao(url)
                data_json = response.json()

                # Verificar status
                if data_json.get('status') != 'success':
                    logger.warning(f"[{tribunal}] API retornou status: {data_json.get('status')}")
                    break

                # Extrair metadados
                total_count = data_json.get('count', 0)
                items = data_json.get('items', [])

                if total_pages is None:
                    # Calcular total de páginas
                    total_pages = (total_count // limit) + (1 if total_count % limit else 0)
                    logger.info(f"[{tribunal}] Total de publicações: {total_count} ({total_pages} páginas)")

                # Processar items
                for item in items:
                    # Extrair texto HTML
                    texto_html = item.get('texto', '')

                    if not texto_html:
                        logger.debug(f"[{tribunal}] Item sem texto - pulando")
                        continue

                    # Gerar hash para deduplicação
                    hash_conteudo = self._gerar_hash(texto_html)

                    # Verificar duplicata
                    if hash_conteudo in self.hash_cache:
                        duplicatas += 1
                        logger.debug(f"[{tribunal}] Duplicata detectada: {hash_conteudo[:16]}...")
                        continue

                    # Adicionar ao cache
                    self.hash_cache.add(hash_conteudo)

                    # Criar PublicacaoRaw
                    publicacao = PublicacaoRaw(
                        id=item.get('id', ''),
                        hash_conteudo=hash_conteudo,
                        numero_processo=item.get('numero_processo'),
                        numero_processo_fmt=item.get('numeroprocessocommascara'),
                        tribunal=tribunal,
                        orgao_julgador=item.get('nomeOrgao'),
                        tipo_comunicacao=item.get('tipoComunicacao', 'Intimação'),
                        classe_processual=item.get('nomeClasse'),
                        texto_html=texto_html,
                        data_publicacao=data,
                        destinatario_advogados=item.get('destinatarioadvogados', []),
                        metadata={
                            'data_disponibilizacao': item.get('data_disponibilizacao'),
                            'meio_circulacao': item.get('meio_circulacao'),
                            'caderno_processo': item.get('caderno_processo')
                        }
                    )

                    publicacoes.append(publicacao)

                # Verificar se há próxima página
                if not items or len(items) < limit:
                    logger.debug(f"[{tribunal}] Última página atingida")
                    break

            except Exception as e:
                logger.error(f"[{tribunal}] Erro ao baixar página {page}: {e}")
                break

        # Salvar hash cache
        self._save_hash_cache()

        logger.info(
            f"[{tribunal}] Download completo: {len(publicacoes)} novas publicações, "
            f"{duplicatas} duplicatas"
        )

        return publicacoes

    def baixar_caderno(
        self,
        tribunal: str,
        data: str,
        meio: str = 'E'
    ) -> Tuple[Optional[Path], Dict]:
        """
        Baixa caderno completo (PDF) de publicações.

        Baseado no comando validado:
        curl -s "https://comunicaapi.pje.jus.br/api/v1/caderno/{tribunal}/{data}/{meio}"

        Args:
            tribunal: Sigla do tribunal
            data: Data no formato YYYY-MM-DD
            meio: Meio de publicação (E=Eletrônico, I=Impresso)

        Returns:
            Tupla (caminho_pdf, metadados)
        """
        logger.info(f"[{tribunal}] Baixando caderno PDF - {data} (meio: {meio})")

        # Construir URL da API de metadados
        metadata_url = f"{self.API_BASE_URL}/caderno/{tribunal}/{data}/{meio}"

        try:
            # Etapa 1: Obter metadados e URL do S3
            response = self._fazer_requisicao(metadata_url)
            metadata = response.json()

            # Verificar status
            if metadata.get('status') != 'Processado':
                logger.warning(
                    f"[{tribunal}] Caderno não processado: {metadata.get('status')}"
                )
                return None, metadata

            # Verificar se há publicações
            total_comunicacoes = metadata.get('comunicacoes', 0)
            if total_comunicacoes == 0:
                logger.info(f"[{tribunal}] Sem publicações nesta data")
                return None, metadata

            # Extrair URL do S3
            s3_url = metadata.get('url')
            if not s3_url:
                raise Exception("URL de download não encontrada nos metadados")

            logger.info(
                f"[{tribunal}] {total_comunicacoes} comunicações, "
                f"{metadata.get('paginas', 0)} páginas"
            )

            # Etapa 2: Download do ZIP do S3
            logger.debug(f"[{tribunal}] Baixando ZIP do S3...")
            zip_response = self._fazer_requisicao(s3_url)

            # Nome do arquivo
            filename = f"{tribunal}_{data}_{meio}.zip"
            output_path = self.downloads_dir / tribunal / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Salvar ZIP
            with open(output_path, 'wb') as f:
                f.write(zip_response.content)

            logger.info(
                f"[{tribunal}] Caderno baixado: {output_path} "
                f"({len(zip_response.content)/1024/1024:.1f}MB)"
            )

            return output_path, metadata

        except Exception as e:
            logger.error(f"[{tribunal}] Erro ao baixar caderno: {e}")
            return None, {}

    def salvar_publicacoes(
        self,
        publicacoes: List[PublicacaoRaw],
        tribunal: str,
        data: str
    ) -> Path:
        """
        Salva publicações em arquivo JSON.

        Args:
            publicacoes: Lista de PublicacaoRaw
            tribunal: Sigla do tribunal
            data: Data (YYYY-MM-DD)

        Returns:
            Path do arquivo salvo
        """
        if not publicacoes:
            logger.warning(f"[{tribunal}] Nenhuma publicação para salvar")
            return None

        # Nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{tribunal}_{data}_{timestamp}.json"
        output_path = self.downloads_dir / tribunal / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Converter para dict
        data_to_save = {
            'tribunal': tribunal,
            'data_publicacao': data,
            'timestamp_download': datetime.now().isoformat(),
            'total': len(publicacoes),
            'publicacoes': [asdict(pub) for pub in publicacoes]
        }

        # Salvar JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)

        logger.info(f"[{tribunal}] {len(publicacoes)} publicações salvas em {output_path}")
        return output_path

    def get_stats(self) -> Dict:
        """
        Retorna estatísticas do downloader.

        Returns:
            Dict com estatísticas
        """
        return {
            'hash_cache_size': len(self.hash_cache),
            'rate_limiter': self.rate_limiter.get_stats(),
            'data_root': str(self.data_root)
        }
