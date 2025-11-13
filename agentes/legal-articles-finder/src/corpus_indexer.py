"""
corpus_indexer.py - Indexador de corpus legal

Indexa leis brasileiras em SQLite para busca rápida de artigos.

Estrutura do banco:
- laws: id, code, name, year, file_path
- articles: id, law_id, number, content, full_text, has_paragraphs
"""
import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager


@dataclass
class Law:
    """Representa uma lei no corpus."""
    id: Optional[int] = None
    code: str = ""           # CF, CC, CPC, etc
    name: str = ""           # Nome completo
    year: Optional[int] = None
    file_path: str = ""


@dataclass
class Article:
    """Representa um artigo de lei."""
    id: Optional[int] = None
    law_id: int = 0
    number: str = ""         # "5", "121", "186"
    content: str = ""        # Texto completo do artigo
    caput: str = ""          # Caput (primeira parte)
    paragraphs: List[str] = None  # Lista de parágrafos
    incisos: Dict[str, str] = None  # {inciso: texto}
    alineas: Dict[str, str] = None  # {alinea: texto}

    def __post_init__(self):
        if self.paragraphs is None:
            self.paragraphs = []
        if self.incisos is None:
            self.incisos = {}
        if self.alineas is None:
            self.alineas = {}


class CorpusIndexer:
    """Indexador de corpus legal."""

    def __init__(self, db_path: Path):
        """
        Inicializa indexador.

        Args:
            db_path: Caminho do banco SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Cria schema do banco."""
        with self._get_connection() as conn:
            # Tabela de leis
            conn.execute("""
                CREATE TABLE IF NOT EXISTS laws (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    year INTEGER,
                    file_path TEXT NOT NULL,
                    indexed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela de artigos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    law_id INTEGER NOT NULL,
                    number TEXT NOT NULL,
                    content TEXT NOT NULL,
                    caput TEXT,
                    has_paragraphs INTEGER DEFAULT 0,
                    FOREIGN KEY (law_id) REFERENCES laws(id) ON DELETE CASCADE
                )
            """)

            # Índices para busca rápida
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_articles_number
                ON articles(law_id, number)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_laws_code
                ON laws(code)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager para conexão SQLite."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def index_law(
        self,
        code: str,
        name: str,
        file_path: Path,
        year: Optional[int] = None
    ) -> int:
        """
        Indexa uma lei completa.

        Args:
            code: Código da lei (CF, CC, CPC, etc)
            name: Nome completo
            file_path: Caminho do arquivo com o texto da lei
            year: Ano da lei

        Returns:
            ID da lei indexada
        """
        # Ler arquivo
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Parsear artigos
        articles = self._parse_articles(text)

        with self._get_connection() as conn:
            # Inserir lei (ou atualizar se já existe)
            cursor = conn.execute("""
                INSERT OR REPLACE INTO laws (code, name, year, file_path)
                VALUES (?, ?, ?, ?)
            """, (code.upper(), name, year, str(file_path)))

            law_id = cursor.lastrowid

            # Deletar artigos antigos (se houver)
            conn.execute("DELETE FROM articles WHERE law_id = ?", (law_id,))

            # Inserir artigos
            for article in articles:
                has_paragraphs = 1 if article.paragraphs else 0

                conn.execute("""
                    INSERT INTO articles (law_id, number, content, caput, has_paragraphs)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    law_id,
                    article.number,
                    article.content,
                    article.caput,
                    has_paragraphs
                ))

            conn.commit()

        print(f"✅ Lei indexada: {code} ({len(articles)} artigos)")
        return law_id

    def _parse_articles(self, text: str) -> List[Article]:
        """
        Parseia artigos de um texto de lei.

        Formato esperado:
        Art. 5º [Caput do artigo...]
        § 1º [Texto do parágrafo...]
        I - [Texto do inciso...]

        Args:
            text: Texto completo da lei

        Returns:
            Lista de artigos parseados
        """
        articles = []

        # Regex para identificar início de artigo
        # Formato: "Art. 5º", "Art. 121", "Artigo 5°"
        article_pattern = re.compile(
            r'(?:^|\n)\s*Art(?:igo)?\.?\s+(\d+[º°]?(?:-[A-Z])?)\s*[–\-]?\s*',
            re.IGNORECASE | re.MULTILINE
        )

        matches = list(article_pattern.finditer(text))

        for i, match in enumerate(matches):
            article_num = match.group(1).replace('º', '').replace('°', '').strip()
            start = match.end()

            # Fim do artigo = início do próximo ou fim do texto
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            article_text = text[start:end].strip()

            # Extrair caput (texto antes do primeiro parágrafo)
            caput_match = re.search(r'^(.*?)(?=\n\s*§|\n\s*\d+\s*-|\Z)', article_text, re.DOTALL)
            caput = caput_match.group(1).strip() if caput_match else article_text

            # Extrair parágrafos
            paragraph_pattern = re.compile(r'\n\s*§\s*(\d+[º°]?)\s*[–\-]?\s*(.*?)(?=\n\s*§|\n\s*\d+\s*-|\Z)', re.DOTALL)
            paragraphs = [p.strip() for _, p in paragraph_pattern.findall(article_text)]

            article = Article(
                number=article_num,
                content=article_text,
                caput=caput,
                paragraphs=paragraphs
            )

            articles.append(article)

        return articles

    def find_article(
        self,
        law_code: str,
        article_number: str
    ) -> Optional[Article]:
        """
        Busca um artigo específico.

        Args:
            law_code: Código da lei (CF, CC, etc)
            article_number: Número do artigo

        Returns:
            Artigo encontrado ou None
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT a.*, l.code, l.name
                FROM articles a
                JOIN laws l ON a.law_id = l.id
                WHERE l.code = ? AND a.number = ?
            """, (law_code.upper(), article_number))

            row = cursor.fetchone()

            if not row:
                return None

            article = Article(
                id=row['id'],
                law_id=row['law_id'],
                number=row['number'],
                content=row['content'],
                caput=row['caput'],
                paragraphs=[]  # TODO: parsear do content se necessário
            )

            return article

    def get_law_stats(self) -> Dict:
        """Retorna estatísticas do corpus indexado."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM laws) as total_laws,
                    (SELECT COUNT(*) FROM articles) as total_articles
            """)

            row = cursor.fetchone()

            # Leis indexadas
            cursor = conn.execute("""
                SELECT l.code, l.name, COUNT(a.id) as articles_count
                FROM laws l
                LEFT JOIN articles a ON l.id = a.law_id
                GROUP BY l.id
                ORDER BY l.code
            """)

            laws = [
                {'code': row['code'], 'name': row['name'], 'articles': row['articles_count']}
                for row in cursor.fetchall()
            ]

            return {
                'total_laws': row['total_laws'],
                'total_articles': row['total_articles'],
                'laws': laws
            }


# ============================================================================
# CLI DE TESTE
# ============================================================================

if __name__ == "__main__":
    import sys

    # Criar indexador
    db_path = Path(__file__).parent.parent / "corpus" / "index.db"
    indexer = CorpusIndexer(db_path)

    print("📚 Corpus Indexer - Sistema de Indexação de Leis\n")

    # Mostrar stats
    stats = indexer.get_law_stats()
    print(f"📊 Status:")
    print(f"   Leis indexadas: {stats['total_laws']}")
    print(f"   Artigos indexados: {stats['total_articles']}\n")

    if stats['laws']:
        print("📖 Leis no corpus:")
        for law in stats['laws']:
            print(f"   • {law['code']}: {law['name']} ({law['articles']} artigos)")
    else:
        print("⚠️  Nenhuma lei indexada ainda.")
        print("\nPara indexar uma lei:")
        print("   python corpus_indexer.py index <CODE> <NAME> <FILE> [YEAR]")
        print("\nExemplo:")
        print("   python corpus_indexer.py index CF 'Constituição Federal' cf-1988.txt 1988")

    # Se argumentos CLI forem passados, processar comando
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "index" and len(sys.argv) >= 5:
            code = sys.argv[2]
            name = sys.argv[3]
            file_path = Path(sys.argv[4])
            year = int(sys.argv[5]) if len(sys.argv) > 5 else None

            print(f"\n🔄 Indexando {code}...")
            try:
                indexer.index_law(code, name, file_path, year)
            except FileNotFoundError as e:
                print(f"❌ Erro: {e}")
                sys.exit(1)

        elif command == "search" and len(sys.argv) >= 4:
            law_code = sys.argv[2]
            article_num = sys.argv[3]

            print(f"\n🔍 Buscando {law_code} art. {article_num}...")
            article = indexer.find_article(law_code, article_num)

            if article:
                print(f"\n✅ Artigo encontrado:\n")
                print(f"Art. {article.number}")
                print(f"{article.caput}\n")
                if article.paragraphs:
                    for i, para in enumerate(article.paragraphs, 1):
                        print(f"§{i}º {para}\n")
            else:
                print(f"❌ Artigo não encontrado")
