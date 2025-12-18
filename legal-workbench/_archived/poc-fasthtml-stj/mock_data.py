"""
Mock data for STJ PoC
Realistic Brazilian legal case data for testing
"""

from typing import List, Dict
from datetime import datetime, timedelta
import random

# Legal domains
LEGAL_DOMAINS = [
    "Direito Civil",
    "Direito Penal",
    "Direito Tributário",
    "Direito Administrativo",
    "Direito do Trabalho",
    "Direito Constitucional",
]

# Trigger words by domain
TRIGGER_WORDS = {
    "Direito Civil": [
        "Dano Moral",
        "Lucros Cessantes",
        "Responsabilidade Civil",
        "Contratos",
        "Propriedade",
        "Família",
        "Sucessões",
    ],
    "Direito Penal": [
        "Habeas Corpus",
        "Furto",
        "Roubo",
        "Estelionato",
        "Prescrição",
        "Dosimetria",
        "Progressão de Regime",
    ],
    "Direito Tributário": [
        "ICMS",
        "ISS",
        "IRPJ",
        "COFINS",
        "PIS",
        "Compensação Tributária",
        "Execução Fiscal",
    ],
    "Direito Administrativo": [
        "Licitação",
        "Servidor Público",
        "Concurso Público",
        "Improbidade Administrativa",
        "Desapropriação",
    ],
}

# Query templates
QUERY_TEMPLATES = [
    {
        "name": "Divergência entre Turmas",
        "description": "Buscar divergências jurisprudenciais entre diferentes turmas",
        "sql_template": "SELECT * FROM acordaos WHERE tipo_divergencia = 'TURMAS' AND ano >= 2020",
    },
    {
        "name": "Recursos Repetitivos",
        "description": "Recursos com repercussão geral ou repetitivos",
        "sql_template": "SELECT * FROM acordaos WHERE recurso_repetitivo = TRUE ORDER BY data_julgamento DESC",
    },
    {
        "name": "Súmulas Recentes",
        "description": "Súmulas publicadas nos últimos 2 anos",
        "sql_template": "SELECT * FROM sumulas WHERE data_publicacao >= DATE('now', '-2 years')",
    },
    {
        "name": "Temas de Alta Relevância",
        "description": "Casos com alta citação e relevância jurídica",
        "sql_template": "SELECT * FROM acordaos WHERE num_citacoes > 50 ORDER BY num_citacoes DESC",
    },
]

# Mock jurisprudence results
def generate_mock_acordaos(domain: str = "", keywords: List[str] = [], acordaos_only: bool = False) -> List[Dict]:
    """Generate mock acordão results"""

    outcomes = ["PROVIDO", "DESPROVIDO", "PARCIAL"]
    relatores = [
        "Min. Nancy Andrighi",
        "Min. Luis Felipe Salomão",
        "Min. Maria Isabel Gallotti",
        "Min. Paulo de Tarso Sanseverino",
        "Min. Marco Aurélio Bellizze",
        "Min. Ricardo Villas Bôas Cueva",
    ]

    turmas = ["3ª Turma", "4ª Turma", "2ª Seção"]

    results = []
    num_results = random.randint(8, 15)

    for i in range(num_results):
        # Generate date within last 3 years
        days_ago = random.randint(0, 1095)
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%d/%m/%Y")

        # Process number format: XXXXX-XX.YYYY.X.XX.XXXX
        processo = f"{random.randint(10000, 99999)}-{random.randint(10, 99)}.{random.randint(2018, 2024)}.{random.randint(1, 9)}.{random.randint(10, 99)}.{random.randint(1000, 9999)}"

        outcome = random.choice(outcomes)
        relator = random.choice(relatores)
        turma = random.choice(turmas)

        # Build ementa based on keywords
        keyword_text = " e ".join(keywords[:2]) if keywords else "matéria jurídica"
        ementa = f"RECURSO ESPECIAL. {domain.upper() if domain else 'DIREITO CIVIL'}. {keyword_text.upper()}. "

        if outcome == "PROVIDO":
            ementa += "Tese acolhida. Precedentes do STJ. Recurso provido."
        elif outcome == "DESPROVIDO":
            ementa += "Tese afastada. Jurisprudência consolidada em sentido contrário. Recurso desprovido."
        else:
            ementa += "Parcial procedência. Acolhimento em parte da pretensão recursal. Recurso parcialmente provido."

        results.append({
            "processo": processo,
            "data": date,
            "outcome": outcome,
            "relator": relator,
            "turma": turma,
            "ementa": ementa,
            "citacoes": random.randint(5, 120),
        })

    # Sort by date (most recent first)
    results.sort(key=lambda x: datetime.strptime(x["data"], "%d/%m/%Y"), reverse=True)

    return results


def generate_sql_query(domain: str = "", keywords: List[str] = [], acordaos_only: bool = False) -> str:
    """Generate realistic SQL query based on filters"""

    sql_parts = ["SELECT", "    a.numero_processo,", "    a.data_julgamento,",
                 "    a.resultado,", "    a.relator,", "    a.turma,",
                 "    a.ementa,", "    COUNT(c.id) as num_citacoes",
                 "FROM acordaos a", "LEFT JOIN citacoes c ON a.id = c.acordao_id"]

    where_clauses = []

    if domain:
        where_clauses.append(f"a.area_direito = '{domain}'")

    if keywords:
        keyword_conditions = []
        for kw in keywords:
            keyword_conditions.append(f"a.ementa LIKE '%{kw}%'")
        where_clauses.append(f"({' OR '.join(keyword_conditions)})")

    if acordaos_only:
        where_clauses.append("a.tipo_documento = 'ACORDAO'")

    if where_clauses:
        sql_parts.append("WHERE")
        sql_parts.append("    " + "\n    AND ".join(where_clauses))

    sql_parts.extend([
        "GROUP BY a.id",
        "ORDER BY a.data_julgamento DESC",
        "LIMIT 100;"
    ])

    return "\n".join(sql_parts)


def get_streaming_logs() -> List[str]:
    """Generate mock streaming logs for download process"""

    return [
        "[2024-12-13 10:23:45] Iniciando processo de download...",
        "[2024-12-13 10:23:45] Conectando ao portal STJ...",
        "[2024-12-13 10:23:46] Autenticação bem-sucedida",
        "[2024-12-13 10:23:46] Buscando processos do período 01/01/2024 - 31/12/2024",
        "[2024-12-13 10:23:47] Encontrados 247 processos",
        "[2024-12-13 10:23:48] Download batch 1/5: processos 1-50",
        "[2024-12-13 10:23:52] Download batch 2/5: processos 51-100",
        "[2024-12-13 10:23:55] Download batch 3/5: processos 101-150",
        "[2024-12-13 10:23:58] Download batch 4/5: processos 151-200",
        "[2024-12-13 10:24:01] Download batch 5/5: processos 201-247",
        "[2024-12-13 10:24:03] Processando PDFs baixados...",
        "[2024-12-13 10:24:05] Extraindo metadados de 247 documentos",
        "[2024-12-13 10:24:08] Indexando conteúdo no banco de dados",
        "[2024-12-13 10:24:10] Gerando relatório de importação",
        "[2024-12-13 10:24:11] CONCLUÍDO: 247 processos importados com sucesso",
        "[2024-12-13 10:24:11] Tempo total: 26 segundos",
    ]


def get_quick_stats() -> Dict:
    """Generate mock statistics for dashboard"""

    return {
        "total_acordaos": 15_847,
        "ultima_atualizacao": "13/12/2024 09:15",
        "processos_mes": 342,
        "citacoes_medio": 28.4,
    }
