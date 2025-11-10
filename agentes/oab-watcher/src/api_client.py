"""
API Client - Cliente HTTP para comunicação com DJEN
"""
import requests
import logging
import json
from pathlib import Path
from typing import Dict, Optional, List, Callable
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

logger = logging.getLogger(__name__)


class DJENClient:
    """Cliente HTTP para API DJEN com retry e logging"""

    def __init__(self, config: Dict):
        self.base_url = config['api']['base_url']
        self.timeout = config['api']['timeout']
        self.max_retries = config['api']['max_retries']
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'OAB-Watcher/1.0'
        })

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        GET request com retry automático

        Args:
            endpoint: Caminho da API (ex: '/api/v1/comunicacao')
            params: Query parameters

        Returns:
            Dict com response JSON

        Raises:
            requests.RequestException em caso de falha
        """
        url = f"{self.base_url}{endpoint}"

        logger.info(f"GET {url}")
        logger.debug(f"Params: {params}")

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            logger.info(f"Response: {response.status_code} - {len(data.get('items', []))} items")

            return data

        except requests.RequestException as e:
            logger.error(f"Erro na requisição: {e}")
            raise

    def get_all_pages(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        page_size: int = 100,
        max_items: Optional[int] = None,
        show_progress: bool = True,
        callback: Optional[Callable[[List[Dict]], None]] = None
    ) -> List[Dict]:
        """
        Busca TODAS as páginas de uma consulta (suporte a paginação).

        Args:
            endpoint: Caminho da API
            params: Query parameters base
            page_size: Items por página (default: 100)
            max_items: Máximo de items a buscar (None = sem limite)
            show_progress: Mostrar progress bar (default: True)
            callback: Função chamada a cada página (para processar incremental)

        Returns:
            Lista completa de items de todas as páginas

        Exemplo:
            >>> client.get_all_pages(
            ...     '/api/v1/comunicacao',
            ...     {'data_inicio': '2025-11-07'},
            ...     max_items=1000
            ... )
        """
        params = params or {}
        all_items = []

        # Primeira requisição para descobrir total
        params_page = {**params, 'limit': page_size, 'offset': 0}
        first_response = self.get(endpoint, params_page)

        total_count = first_response.get('count', 0)
        items = first_response.get('items', [])
        all_items.extend(items)

        if callback:
            callback(items)

        logger.info(
            f"Paginação iniciada: {total_count} items totais, "
            f"page_size={page_size}"
        )

        # Calcular total de páginas
        if max_items and max_items < total_count:
            total_count = max_items

        total_pages = (total_count + page_size - 1) // page_size

        # Se só tem 1 página, retornar
        if total_pages <= 1:
            return all_items[:max_items] if max_items else all_items

        # Buscar páginas restantes
        with tqdm(
            total=total_count,
            initial=len(items),
            desc="Buscando páginas",
            disable=not show_progress,
            unit="items"
        ) as pbar:

            for page_num in range(2, total_pages + 1):
                # Verificar se já atingiu max_items
                if max_items and len(all_items) >= max_items:
                    break

                offset = (page_num - 1) * page_size
                params_page = {**params, 'limit': page_size, 'offset': offset}

                try:
                    response = self.get(endpoint, params_page)
                    items = response.get('items', [])

                    all_items.extend(items)
                    pbar.update(len(items))

                    if callback:
                        callback(items)

                    # Se não retornou items, parar
                    if not items:
                        logger.warning(f"Página {page_num} vazia, encerrando paginação")
                        break

                except Exception as e:
                    logger.error(f"Erro na página {page_num}: {e}")
                    # Continuar com próximas páginas
                    continue

        # Aplicar max_items se especificado
        final_items = all_items[:max_items] if max_items else all_items

        logger.info(
            f"Paginação concluída: {len(final_items)} items obtidos "
            f"de {total_count} totais"
        )

        return final_items

    def download_file(self, url: str, output_path: Path) -> bool:
        """
        Download de arquivo (PDF do caderno)

        Args:
            url: URL completa do arquivo
            output_path: Caminho onde salvar

        Returns:
            True se sucesso, False se falha
        """
        logger.info(f"Baixando: {url}")

        try:
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Salvo em: {output_path}")
            return True

        except requests.RequestException as e:
            logger.error(f"Erro no download: {e}")
            return False
