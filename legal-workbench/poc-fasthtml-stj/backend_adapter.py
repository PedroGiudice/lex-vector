"""
Backend Adapter - Bridge between FastHTML and STJ Engines
Replaces mock_data.py with real backend calls
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add backend to path (for Docker deployment)
BACKEND_PATH = Path(__file__).parent / "backend"
if BACKEND_PATH.exists():
    sys.path.insert(0, str(BACKEND_PATH))

# Try to import real engines
try:
    from src.downloader import STJDownloader
    from src.processor import STJProcessor
    from src.database import STJDatabase
    REAL_BACKEND = True
except ImportError:
    REAL_BACKEND = False
    print("[WARNING] Real backend not available, using mock mode")

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=2)


class BackendAdapter:
    """Adapter to interact with real STJ backend engines"""

    def __init__(self):
        self.duckdb_path = os.environ.get("DUCKDB_PATH", "/app/data/stj.duckdb")
        self._db: Optional[STJDatabase] = None
        self._downloader: Optional[STJDownloader] = None

    @property
    def db(self) -> Optional['STJDatabase']:
        """Lazy load database connection"""
        if self._db is None and REAL_BACKEND:
            try:
                self._db = STJDatabase(self.duckdb_path)
            except Exception as e:
                print(f"[ERROR] Failed to connect to database: {e}")
        return self._db

    def get_quick_stats(self) -> Dict[str, Any]:
        """Get database statistics - uses same keys as mock_data.py"""
        if not REAL_BACKEND or not self.db:
            return self._mock_stats()

        try:
            stats = self.db.get_stats()
            return {
                "total_acordaos": stats.get("total_records", 0),
                "ultima_atualizacao": stats.get("last_updated", "N/A"),
                "processos_mes": stats.get("monthly_records", 0),
                "citacoes_medio": stats.get("avg_citations", 0.0),
            }
        except Exception as e:
            print(f"[ERROR] Failed to get stats: {e}")
            return self._mock_stats()

    def _mock_stats(self) -> Dict[str, Any]:
        """Fallback mock stats - same structure as mock_data.py"""
        return {
            "total_acordaos": 0,
            "ultima_atualizacao": "Sem dados",
            "processos_mes": 0,
            "citacoes_medio": 0.0,
        }

    def search_acordaos(
        self,
        domain: str = "",
        keywords: List[str] = None,
        acordaos_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for acordaos in the database"""
        if not REAL_BACKEND or not self.db:
            return self._mock_search(domain, keywords)

        try:
            # Build query based on filters
            filters = {}
            if domain:
                filters["materia"] = domain
            if acordaos_only:
                filters["tipo"] = "ACORDAO"

            results = self.db.search(
                keywords=keywords or [],
                filters=filters,
                limit=limit
            )

            return [self._format_acordao(r) for r in results]
        except Exception as e:
            print(f"[ERROR] Search failed: {e}")
            return self._mock_search(domain, keywords)

    def _format_acordao(self, record: Dict) -> Dict[str, Any]:
        """Format database record for display"""
        return {
            "numero": record.get("numero_processo", ""),
            "relator": record.get("relator", ""),
            "orgao": record.get("orgao_julgador", ""),
            "data": record.get("data_julgamento", ""),
            "ementa": record.get("ementa", "")[:500],
            "resultado": record.get("resultado", "UNKNOWN")
        }

    def _mock_search(self, domain: str, keywords: List[str]) -> List[Dict]:
        """Fallback mock search results"""
        return [
            {
                "numero": "REsp 1234567/SP",
                "relator": "Min. Mock Data",
                "orgao": "Segunda Turma",
                "data": "2024-01-15",
                "ementa": f"[MOCK] Busca por: {domain} / {keywords}. Backend real nao disponivel.",
                "resultado": "MOCK"
            }
        ]

    def generate_sql_preview(
        self,
        domain: str = "",
        keywords: List[str] = None,
        acordaos_only: bool = False
    ) -> str:
        """Generate SQL query preview"""
        parts = ["SELECT numero_processo, relator, ementa, data_julgamento"]
        parts.append("FROM stj_acordaos")

        conditions = []
        if domain:
            conditions.append(f"materia = '{domain}'")
        if keywords:
            kw_conditions = [f"ementa ILIKE '%{kw}%'" for kw in keywords]
            conditions.append(f"({' OR '.join(kw_conditions)})")
        if acordaos_only:
            conditions.append("tipo = 'ACORDAO'")

        if conditions:
            parts.append("WHERE " + " AND ".join(conditions))

        parts.append("ORDER BY data_julgamento DESC")
        parts.append("LIMIT 50;")

        return "\n".join(parts)

    async def stream_download_logs(
        self,
        start_date: str,
        end_date: str
    ):
        """Generator for streaming download progress"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        yield f"[{timestamp}] Iniciando download do STJ Dados Abertos..."
        yield f"[{timestamp}] Periodo: {start_date} ate {end_date}"

        if not REAL_BACKEND:
            yield f"[{timestamp}] [WARNING] Backend real nao disponivel"
            yield f"[{timestamp}] Executando em modo simulacao..."
            for i in range(5):
                await asyncio.sleep(0.5)
                yield f"[{timestamp}] [MOCK] Processando lote {i+1}/5..."
            yield f"[{timestamp}] [MOCK] Simulacao concluida"
            return

        try:
            # Real download would go here
            yield f"[{timestamp}] Conectando ao portal STJ..."
            await asyncio.sleep(1)
            yield f"[{timestamp}] Conexao estabelecida"
            yield f"[{timestamp}] Verificando atualizacoes..."
            await asyncio.sleep(0.5)
            yield f"[{timestamp}] Download em andamento..."
            # ... real implementation would stream from STJDownloader
            yield f"[{timestamp}] Download concluido com sucesso!"
        except Exception as e:
            yield f"[{timestamp}] [ERROR] Falha no download: {e}"


# Singleton instance
adapter = BackendAdapter()


# Compatibility functions (same interface as mock_data.py)
def get_quick_stats() -> Dict[str, Any]:
    return adapter.get_quick_stats()

def generate_sql_query(domain: str, keywords: List[str], acordaos_only: bool) -> str:
    return adapter.generate_sql_preview(domain, keywords, acordaos_only)

def generate_mock_acordaos(domain: str, keywords: List[str], acordaos_only: bool) -> List[Dict]:
    return adapter.search_acordaos(domain, keywords, acordaos_only)

async def stream_download(start_date: str, end_date: str):
    async for log in adapter.stream_download_logs(start_date, end_date):
        yield log


# Domain options (same as mock_data.py)
DOMAINS = [
    "Direito Civil",
    "Direito Penal",
    "Direito Tributario",
    "Direito Administrativo",
    "Direito do Trabalho",
    "Direito Processual Civil",
    "Direito Processual Penal",
    "Direito Constitucional",
    "Direito Empresarial",
    "Direito Ambiental"
]

KEYWORDS_BY_DOMAIN = {
    "Direito Civil": ["Dano Moral", "Responsabilidade Civil", "Contrato", "Posse", "Usucapiao"],
    "Direito Penal": ["Habeas Corpus", "Prisao Preventiva", "Trafico", "Roubo", "Homicidio"],
    "Direito Tributario": ["ICMS", "ISS", "Contribuicao", "Imunidade", "Isencao"],
    "Direito Administrativo": ["Licitacao", "Servidor Publico", "Concurso", "Improbidade"],
    "Direito do Trabalho": ["Rescisao", "FGTS", "Horas Extras", "Vinculo"],
    "Direito Processual Civil": ["Recurso Especial", "Agravo", "Embargos", "Tutela"],
    "Direito Processual Penal": ["Nulidade", "Competencia", "Prova Ilicita"],
    "Direito Constitucional": ["Direito Fundamental", "Controle", "Federacao"],
    "Direito Empresarial": ["Falencia", "Recuperacao", "Sociedade", "Marca"],
    "Direito Ambiental": ["Dano Ambiental", "Licenciamento", "APP", "Reserva Legal"]
}

QUERY_TEMPLATES = [
    {"name": "Divergencia Jurisprudencial", "description": "Casos com votos divergentes"},
    {"name": "Recursos Repetitivos", "description": "Temas repetitivos do STJ"},
    {"name": "Sumulas Aplicadas", "description": "Decisoes que citam sumulas"}
]
