#!/usr/bin/env python3
"""
Context Store Statistics Dashboard CLI

Visualiza estatisticas de uso do Context Store:
- Total de documentos processados
- Distribuicao por OCR engine
- Taxa de sucesso por engine
- Padroes mais frequentes
- Ultimos processamentos

Usage:
    python -m cli.context_stats --db data/context.db
    python -m cli.context_stats --db data/context.db --engine marker
    python -m cli.context_stats --db data/context.db --since 2024-01-01
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

# Initialize Typer app
app = typer.Typer(
    name="context-stats",
    help="Dashboard CLI para estatisticas do Context Store",
    add_completion=False,
)

console = Console()


class OutputFormat(str, Enum):
    """Formatos de output disponiveis"""

    TABLE = "table"
    JSON = "json"
    CSV = "csv"


@dataclass
class EngineStats:
    """Estatisticas por engine"""

    engine: str
    total_patterns: int
    avg_confidence: float
    total_occurrences: int
    deprecated_count: int
    active_count: int
    success_rate: float


@dataclass
class PatternStats:
    """Estatisticas de padroes"""

    pattern_type: str
    count: int
    avg_confidence: float
    top_engine: str


@dataclass
class RecentProcessing:
    """Processamento recente"""

    caso_cnj: str
    pattern_type: str
    engine: str
    confidence: float
    page: int
    created_at: str


class ContextStatsDB:
    """Acesso ao banco de dados do Context Store"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_summary(self) -> dict:
        """Retorna resumo geral do Context Store"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total de casos
            cursor.execute("SELECT COUNT(*) FROM caso")
            total_casos = cursor.fetchone()[0]

            # Total de padroes
            cursor.execute("SELECT COUNT(*) FROM observed_patterns")
            total_patterns = cursor.fetchone()[0]

            # Padroes ativos vs deprecados
            cursor.execute("SELECT deprecated, COUNT(*) FROM observed_patterns GROUP BY deprecated")
            rows = cursor.fetchall()
            active = sum(r[1] for r in rows if r[0] == 0 or r[0] is False)
            deprecated = sum(r[1] for r in rows if r[0] == 1 or r[0] is True)

            # Total de divergencias
            cursor.execute("SELECT COUNT(*) FROM divergences")
            total_divergences = cursor.fetchone()[0]

            # Total de ocorrencias
            cursor.execute("SELECT COALESCE(SUM(occurrence_count), 0) FROM observed_patterns")
            total_occurrences = cursor.fetchone()[0]

            # Confianca media global
            cursor.execute(
                "SELECT AVG(avg_confidence) FROM observed_patterns WHERE avg_confidence IS NOT NULL"
            )
            avg_confidence = cursor.fetchone()[0] or 0.0

            return {
                "total_casos": total_casos,
                "total_patterns": total_patterns,
                "active_patterns": active,
                "deprecated_patterns": deprecated,
                "total_divergences": total_divergences,
                "total_occurrences": total_occurrences,
                "avg_confidence": avg_confidence,
            }

    def get_engine_stats(
        self,
        engine_filter: str | None = None,
        since: datetime | None = None,
    ) -> list[EngineStats]:
        """Retorna estatisticas por engine"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    created_by_engine as engine,
                    COUNT(*) as total_patterns,
                    AVG(avg_confidence) as avg_confidence,
                    COALESCE(SUM(occurrence_count), 0) as total_occurrences,
                    SUM(CASE WHEN deprecated = 1 OR deprecated = 'true' THEN 1 ELSE 0 END) as deprecated_count,
                    SUM(CASE WHEN deprecated = 0 OR deprecated = 'false' OR deprecated IS NULL THEN 1 ELSE 0 END) as active_count
                FROM observed_patterns
                WHERE 1=1
            """
            params: list[Any] = []

            if engine_filter:
                query += " AND created_by_engine = ?"
                params.append(engine_filter)

            if since:
                query += " AND created_at >= ?"
                params.append(since.isoformat())

            query += " GROUP BY created_by_engine ORDER BY total_patterns DESC"

            cursor.execute(query, params)

            stats = []
            for row in cursor.fetchall():
                total = row["total_patterns"]
                deprecated = row["deprecated_count"]
                success_rate = ((total - deprecated) / total * 100) if total > 0 else 0.0

                stats.append(
                    EngineStats(
                        engine=row["engine"],
                        total_patterns=total,
                        avg_confidence=row["avg_confidence"] or 0.0,
                        total_occurrences=row["total_occurrences"],
                        deprecated_count=deprecated,
                        active_count=row["active_count"],
                        success_rate=success_rate,
                    )
                )

            return stats

    def get_pattern_distribution(
        self,
        since: datetime | None = None,
    ) -> list[PatternStats]:
        """Retorna distribuicao de tipos de padroes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    pattern_type,
                    COUNT(*) as count,
                    AVG(avg_confidence) as avg_confidence,
                    (
                        SELECT created_by_engine
                        FROM observed_patterns op2
                        WHERE op2.pattern_type = op.pattern_type
                        GROUP BY created_by_engine
                        ORDER BY COUNT(*) DESC
                        LIMIT 1
                    ) as top_engine
                FROM observed_patterns op
                WHERE 1=1
            """
            params: list[Any] = []

            if since:
                query += " AND created_at >= ?"
                params.append(since.isoformat())

            query += " GROUP BY pattern_type ORDER BY count DESC"

            cursor.execute(query, params)

            stats = []
            for row in cursor.fetchall():
                stats.append(
                    PatternStats(
                        pattern_type=row["pattern_type"],
                        count=row["count"],
                        avg_confidence=row["avg_confidence"] or 0.0,
                        top_engine=row["top_engine"] or "N/A",
                    )
                )

            return stats

    def get_recent_processings(
        self,
        limit: int = 10,
        engine_filter: str | None = None,
        since: datetime | None = None,
    ) -> list[RecentProcessing]:
        """Retorna ultimos processamentos"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT
                    c.numero_cnj,
                    op.pattern_type,
                    op.created_by_engine as engine,
                    op.avg_confidence as confidence,
                    op.last_seen_page as page,
                    op.created_at
                FROM observed_patterns op
                JOIN caso c ON op.caso_id = c.id
                WHERE 1=1
            """
            params: list[Any] = []

            if engine_filter:
                query += " AND op.created_by_engine = ?"
                params.append(engine_filter)

            if since:
                query += " AND op.created_at >= ?"
                params.append(since.isoformat())

            query += " ORDER BY op.created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            processings = []
            for row in cursor.fetchall():
                processings.append(
                    RecentProcessing(
                        caso_cnj=row["numero_cnj"],
                        pattern_type=row["pattern_type"],
                        engine=row["engine"],
                        confidence=row["confidence"] or 0.0,
                        page=row["page"],
                        created_at=row["created_at"],
                    )
                )

            return processings

    def get_divergence_stats(self) -> dict:
        """Retorna estatisticas de divergencias"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total por engine
            cursor.execute("""
                SELECT engine_used, COUNT(*) as count
                FROM divergences
                GROUP BY engine_used
                ORDER BY count DESC
            """)

            by_engine = {row["engine_used"]: row["count"] for row in cursor.fetchall()}

            # Media de divergencia
            cursor.execute("""
                SELECT AVG(ABS(expected_confidence - actual_confidence)) as avg_divergence
                FROM divergences
            """)
            avg_divergence = cursor.fetchone()["avg_divergence"] or 0.0

            return {
                "by_engine": by_engine,
                "avg_divergence": avg_divergence,
            }

    def get_casos_summary(self, limit: int = 10) -> list[dict]:
        """Retorna resumo dos casos mais recentes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    c.numero_cnj,
                    c.sistema,
                    c.created_at,
                    COUNT(op.id) as pattern_count,
                    AVG(op.avg_confidence) as avg_confidence
                FROM caso c
                LEFT JOIN observed_patterns op ON c.id = op.caso_id
                GROUP BY c.id
                ORDER BY c.created_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            return [dict(row) for row in cursor.fetchall()]


def render_summary_panel(summary: dict) -> Panel:
    """Renderiza painel de resumo"""
    text = Text()
    text.append("Casos: ", style="bold")
    text.append(f"{summary['total_casos']}\n")
    text.append("Padroes: ", style="bold")
    text.append(f"{summary['total_patterns']} ")
    text.append(f"({summary['active_patterns']} ativos, ", style="green")
    text.append(f"{summary['deprecated_patterns']} deprecados)\n", style="red")
    text.append("Ocorrencias: ", style="bold")
    text.append(f"{summary['total_occurrences']}\n")
    text.append("Divergencias: ", style="bold")
    text.append(f"{summary['total_divergences']}\n", style="yellow")
    text.append("Confianca Media: ", style="bold")
    confidence = summary["avg_confidence"]
    style = "green" if confidence >= 0.8 else "yellow" if confidence >= 0.6 else "red"
    text.append(f"{confidence:.1%}", style=style)

    return Panel(text, title="Resumo do Context Store", border_style="blue")


def render_engine_table(stats: list[EngineStats]) -> Table:
    """Renderiza tabela de estatisticas por engine"""
    table = Table(
        title="Estatisticas por Engine",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Engine", style="bold")
    table.add_column("Padroes", justify="right")
    table.add_column("Ativos", justify="right", style="green")
    table.add_column("Deprecados", justify="right", style="red")
    table.add_column("Ocorrencias", justify="right")
    table.add_column("Confianca", justify="right")
    table.add_column("Taxa Sucesso", justify="right")

    for s in stats:
        conf_style = (
            "green" if s.avg_confidence >= 0.8 else "yellow" if s.avg_confidence >= 0.6 else "red"
        )
        rate_style = (
            "green" if s.success_rate >= 80 else "yellow" if s.success_rate >= 60 else "red"
        )

        table.add_row(
            s.engine,
            str(s.total_patterns),
            str(s.active_count),
            str(s.deprecated_count),
            str(s.total_occurrences),
            f"[{conf_style}]{s.avg_confidence:.1%}[/{conf_style}]",
            f"[{rate_style}]{s.success_rate:.1f}%[/{rate_style}]",
        )

    return table


def render_pattern_table(stats: list[PatternStats]) -> Table:
    """Renderiza tabela de distribuicao de padroes"""
    table = Table(
        title="Distribuicao por Tipo de Padrao",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Tipo", style="bold")
    table.add_column("Quantidade", justify="right")
    table.add_column("Confianca Media", justify="right")
    table.add_column("Engine Principal", style="dim")

    for s in stats:
        conf_style = (
            "green" if s.avg_confidence >= 0.8 else "yellow" if s.avg_confidence >= 0.6 else "red"
        )

        table.add_row(
            s.pattern_type,
            str(s.count),
            f"[{conf_style}]{s.avg_confidence:.1%}[/{conf_style}]",
            s.top_engine,
        )

    return table


def render_recent_table(processings: list[RecentProcessing]) -> Table:
    """Renderiza tabela de processamentos recentes"""
    table = Table(
        title="Ultimos Processamentos",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("CNJ", style="dim", max_width=25)
    table.add_column("Tipo", style="bold")
    table.add_column("Engine")
    table.add_column("Pag", justify="right")
    table.add_column("Confianca", justify="right")
    table.add_column("Data", style="dim")

    for p in processings:
        conf_style = "green" if p.confidence >= 0.8 else "yellow" if p.confidence >= 0.6 else "red"

        # Truncate CNJ for display
        cnj_display = p.caso_cnj[:22] + "..." if len(p.caso_cnj) > 25 else p.caso_cnj

        # Format date
        try:
            dt = datetime.fromisoformat(p.created_at.replace("Z", "+00:00"))
            date_display = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            date_display = str(p.created_at)[:16] if p.created_at else "N/A"

        table.add_row(
            cnj_display,
            p.pattern_type,
            p.engine,
            str(p.page),
            f"[{conf_style}]{p.confidence:.1%}[/{conf_style}]",
            date_display,
        )

    return table


def render_casos_table(casos: list[dict]) -> Table:
    """Renderiza tabela de casos"""
    table = Table(
        title="Casos Recentes",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Numero CNJ", style="bold", max_width=30)
    table.add_column("Sistema")
    table.add_column("Padroes", justify="right")
    table.add_column("Confianca", justify="right")
    table.add_column("Criado", style="dim")

    for c in casos:
        conf = c.get("avg_confidence") or 0.0
        conf_style = "green" if conf >= 0.8 else "yellow" if conf >= 0.6 else "red"

        # Format date
        try:
            dt = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
            date_display = dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            date_display = str(c.get("created_at", "N/A"))[:10]

        table.add_row(
            c["numero_cnj"],
            c["sistema"],
            str(c.get("pattern_count", 0)),
            f"[{conf_style}]{conf:.1%}[/{conf_style}]" if conf > 0 else "-",
            date_display,
        )

    return table


def parse_date(date_str: str) -> datetime:
    """Parse date string in various formats"""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise typer.BadParameter(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


@app.command()
def dashboard(
    db: Path = typer.Option(
        Path("data/context.db"),
        "--db",
        "-d",
        help="Caminho para o banco de dados SQLite",
        exists=False,  # We handle the check ourselves for better error message
    ),
    engine: str | None = typer.Option(
        None,
        "--engine",
        "-e",
        help="Filtrar por engine (marker, pdfplumber, tesseract)",
    ),
    since: str | None = typer.Option(
        None,
        "--since",
        "-s",
        help="Filtrar desde data (YYYY-MM-DD)",
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Numero de itens a mostrar nas listas",
    ),
    section: str | None = typer.Option(
        None,
        "--section",
        help="Mostrar apenas uma secao: summary, engines, patterns, recent, casos",
    ),
):
    """
    Dashboard de estatisticas do Context Store.

    Mostra metricas de uso incluindo distribuicao por engine,
    tipos de padroes, e processamentos recentes.
    """
    # Validate database exists
    if not db.exists():
        console.print(f"[red]Erro:[/red] Database nao encontrado: {db}")
        console.print("\n[dim]Dica: Verifique o caminho ou execute processamentos primeiro.[/dim]")
        raise typer.Exit(1)

    # Parse date filter
    since_dt: datetime | None = None
    if since:
        try:
            since_dt = parse_date(since)
        except typer.BadParameter as e:
            console.print(f"[red]Erro:[/red] {e}")
            raise typer.Exit(1)

    # Validate engine filter
    valid_engines = ["marker", "pdfplumber", "tesseract"]
    if engine and engine.lower() not in valid_engines:
        console.print(f"[red]Erro:[/red] Engine invalida: {engine}")
        console.print(f"[dim]Engines validas: {', '.join(valid_engines)}[/dim]")
        raise typer.Exit(1)

    engine_filter = engine.lower() if engine else None

    try:
        store = ContextStatsDB(db)
    except FileNotFoundError as e:
        console.print(f"[red]Erro:[/red] {e}")
        raise typer.Exit(1)

    # Show filters if active
    if engine_filter or since_dt:
        filters = []
        if engine_filter:
            filters.append(f"engine={engine_filter}")
        if since_dt:
            filters.append(f"desde={since_dt.strftime('%Y-%m-%d')}")
        console.print(f"[dim]Filtros ativos: {', '.join(filters)}[/dim]\n")

    # Render sections based on --section flag
    sections_to_show = (
        [section] if section else ["summary", "engines", "patterns", "recent", "casos"]
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Carregando estatisticas...", total=None)

        if "summary" in sections_to_show and not engine_filter and not since_dt:
            summary = store.get_summary()
            console.print(render_summary_panel(summary))
            console.print()

        if "engines" in sections_to_show:
            engine_stats = store.get_engine_stats(engine_filter=engine_filter, since=since_dt)
            if engine_stats:
                console.print(render_engine_table(engine_stats))
                console.print()
            else:
                console.print("[dim]Nenhuma estatistica de engine encontrada.[/dim]\n")

        if "patterns" in sections_to_show:
            pattern_stats = store.get_pattern_distribution(since=since_dt)
            if pattern_stats:
                console.print(render_pattern_table(pattern_stats))
                console.print()
            else:
                console.print("[dim]Nenhum padrao encontrado.[/dim]\n")

        if "recent" in sections_to_show:
            recent = store.get_recent_processings(
                limit=limit,
                engine_filter=engine_filter,
                since=since_dt,
            )
            if recent:
                console.print(render_recent_table(recent))
                console.print()
            else:
                console.print("[dim]Nenhum processamento recente encontrado.[/dim]\n")

        if "casos" in sections_to_show:
            casos = store.get_casos_summary(limit=limit)
            if casos:
                console.print(render_casos_table(casos))
            else:
                console.print("[dim]Nenhum caso encontrado.[/dim]")


@app.command()
def engines(
    db: Path = typer.Option(
        Path("data/context.db"),
        "--db",
        "-d",
        help="Caminho para o banco de dados SQLite",
    ),
):
    """
    Mostra apenas estatisticas de engines.
    """
    if not db.exists():
        console.print(f"[red]Erro:[/red] Database nao encontrado: {db}")
        raise typer.Exit(1)

    store = ContextStatsDB(db)
    engine_stats = store.get_engine_stats()

    if engine_stats:
        console.print(render_engine_table(engine_stats))
    else:
        console.print("[dim]Nenhuma estatistica encontrada.[/dim]")


@app.command()
def divergences(
    db: Path = typer.Option(
        Path("data/context.db"),
        "--db",
        "-d",
        help="Caminho para o banco de dados SQLite",
    ),
):
    """
    Mostra estatisticas de divergencias.
    """
    if not db.exists():
        console.print(f"[red]Erro:[/red] Database nao encontrado: {db}")
        raise typer.Exit(1)

    store = ContextStatsDB(db)
    div_stats = store.get_divergence_stats()

    console.print(
        Panel(
            f"Divergencia Media: [yellow]{div_stats['avg_divergence']:.1%}[/yellow]",
            title="Divergencias",
            border_style="yellow",
        )
    )

    if div_stats["by_engine"]:
        table = Table(
            title="Divergencias por Engine",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold yellow",
        )
        table.add_column("Engine", style="bold")
        table.add_column("Divergencias", justify="right")

        for engine, count in sorted(
            div_stats["by_engine"].items(), key=lambda x: x[1], reverse=True
        ):
            table.add_row(engine, str(count))

        console.print(table)
    else:
        console.print("[dim]Nenhuma divergencia registrada.[/dim]")


@app.command()
def export(
    db: Path = typer.Option(
        Path("data/context.db"),
        "--db",
        "-d",
        help="Caminho para o banco de dados SQLite",
    ),
    output: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Arquivo de saida (default: stdout)",
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.JSON,
        "--format",
        "-f",
        help="Formato de saida",
    ),
):
    """
    Exporta estatisticas em formato JSON ou CSV.
    """
    import csv
    import json
    from io import StringIO

    if not db.exists():
        console.print(f"[red]Erro:[/red] Database nao encontrado: {db}")
        raise typer.Exit(1)

    store = ContextStatsDB(db)

    summary = store.get_summary()
    engine_stats = store.get_engine_stats()
    pattern_stats = store.get_pattern_distribution()

    if format == OutputFormat.JSON:
        data = {
            "summary": summary,
            "engines": [
                {
                    "engine": s.engine,
                    "total_patterns": s.total_patterns,
                    "avg_confidence": s.avg_confidence,
                    "total_occurrences": s.total_occurrences,
                    "deprecated_count": s.deprecated_count,
                    "active_count": s.active_count,
                    "success_rate": s.success_rate,
                }
                for s in engine_stats
            ],
            "patterns": [
                {
                    "pattern_type": s.pattern_type,
                    "count": s.count,
                    "avg_confidence": s.avg_confidence,
                    "top_engine": s.top_engine,
                }
                for s in pattern_stats
            ],
            "exported_at": datetime.now().isoformat(),
        }
        content = json.dumps(data, indent=2, ensure_ascii=False)

    elif format == OutputFormat.CSV:
        buffer = StringIO()
        writer = csv.writer(buffer)

        # Engine stats
        writer.writerow(["# Engine Statistics"])
        writer.writerow(
            [
                "engine",
                "total_patterns",
                "avg_confidence",
                "total_occurrences",
                "deprecated",
                "active",
                "success_rate",
            ]
        )
        for s in engine_stats:
            writer.writerow(
                [
                    s.engine,
                    s.total_patterns,
                    f"{s.avg_confidence:.4f}",
                    s.total_occurrences,
                    s.deprecated_count,
                    s.active_count,
                    f"{s.success_rate:.2f}",
                ]
            )

        writer.writerow([])
        writer.writerow(["# Pattern Distribution"])
        writer.writerow(["pattern_type", "count", "avg_confidence", "top_engine"])
        for s in pattern_stats:
            writer.writerow([s.pattern_type, s.count, f"{s.avg_confidence:.4f}", s.top_engine])

        content = buffer.getvalue()

    else:  # TABLE format
        console.print("[red]Use o comando 'dashboard' para visualizacao em tabela.[/red]")
        raise typer.Exit(1)

    if output:
        output.write_text(content)
        console.print(f"[green]Exportado para:[/green] {output}")
    else:
        print(content)


def main():
    """Entry point"""
    app()


if __name__ == "__main__":
    main()
