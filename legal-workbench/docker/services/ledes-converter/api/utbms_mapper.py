"""
UTBMS Code Mapper for LEDES 1998B

Maps line item descriptions to appropriate UTBMS task and activity codes
based on keyword matching.

UTBMS Task Codes (Litigation):
- L100: Case Assessment, Development and Administration
- L110: Fact Investigation/Development
- L120: Analysis/Strategy
- L130: Experts/Consultants
- L140: Document/File Management
- L150: Budgeting
- L160: Settlement/Non-Binding ADR
- L210: Pleadings
- L220: Interrogatories
- L230: Depositions
- L240: Document Production
- L250: Other Written Motions/Submissions
- L310: Trial Preparation
- L320: Trial/Hearing Attendance
- L330: Post-Trial Motions
- L510: Appeals

UTBMS Activity Codes:
- A101: Plan and prepare for
- A102: Research
- A103: Draft/Revise
- A104: Review/Analyze
- A105: Appear for/Attend
- A106: Communicate (with client, other counsel, etc.)
- A107: Travel
- A108: Other
"""

from typing import Dict, List

# Task code patterns: code -> list of keywords (case-insensitive)
TASK_CODE_PATTERNS: Dict[str, List[str]] = {
    "L510": [  # Appeals
        "appeal", "recurso", "stj", "stf", "agravo", "embargo",
        "recurso especial", "recurso extraordinário", "apelação",
        "recurso ordinário", "embargos de declaração"
    ],
    "L210": [  # Pleadings
        "defense", "defesa", "contestação", "resposta", "answer",
        "complaint", "pleading", "réplica", "tréplica"
    ],
    "L250": [  # Other Written Motions
        "motion", "petition", "petição", "requerimento", "moção",
        "motion to dismiss", "motion for summary", "tutela"
    ],
    "L160": [  # Settlement/ADR
        "settlement", "acordo", "negociação", "mediation", "mediação",
        "arbitration", "arbitragem", "conciliação", "adr"
    ],
    "L110": [  # Fact Investigation
        "research", "pesquisa", "jurisprudência", "jurisprudencia", "investigation",
        "investigação", "investigacao", "case law", "precedent", "diligência", "diligencia"
    ],
    "L120": [  # Analysis/Strategy
        "analysis", "análise", "strategy", "estratégia", "parecer",
        "opinion", "assessment", "avaliação"
    ],
    "L230": [  # Depositions
        "deposition", "interrogatório", "oitiva", "depoimento",
        "testemunha", "witness"
    ],
    "L320": [  # Trial/Hearing
        "trial", "julgamento", "hearing", "audiência",
        "sustentação oral", "oral argument"
    ],
    "L140": [  # Document Management
        "document", "documento", "file", "arquivo", "organize",
        "organizar", "index", "indexar"
    ],
}

# Activity code patterns: code -> list of keywords (case-insensitive)
ACTIVITY_CODE_PATTERNS: Dict[str, List[str]] = {
    "A103": [  # Draft/Revise
        "draft", "redigir", "prepare", "preparar", "write", "escrever",
        "elaborar", "revise", "revisar documento", "update", "atualizar"
    ],
    "A104": [  # Review/Analyze
        "review", "revisar", "analyze", "analisar", "examine", "examinar",
        "study", "estudar", "avaliar"
    ],
    "A106": [  # Communicate
        "meeting", "reunião", "reuniao", "conference", "conferência", "conferencia",
        "call", "ligação", "ligacao", "email", "correspond", "discuss", "discutir",
        "communicate", "comunicar"
    ],
    "A102": [  # Research
        "research", "pesquisa", "investigate", "investigar", "study",
        "jurisprudência", "case law", "precedent"
    ],
    "A105": [  # Appear/Attend
        "appear", "comparecer", "attend", "audiência", "audiencia", "hearing",
        "court", "tribunal", "fórum", "forum"
    ],
    "A101": [  # Plan and prepare
        "plan", "planejar", "prepare for", "preparar para",
        "strategy", "estratégia"
    ],
    "A107": [  # Travel
        "travel", "viagem", "deslocamento", "trip"
    ],
}


def infer_task_code(description: str, default: str = "L100") -> str:
    """
    Infer UTBMS task code from line item description.

    Args:
        description: The line item description text
        default: Default code if no pattern matches (default: L100)

    Returns:
        UTBMS task code (e.g., "L510", "L210")
    """
    if not description:
        return default

    desc_lower = description.lower()

    for code, patterns in TASK_CODE_PATTERNS.items():
        for pattern in patterns:
            if pattern in desc_lower:
                return code

    return default


def infer_activity_code(description: str, default: str = "A103") -> str:
    """
    Infer UTBMS activity code from line item description.

    Args:
        description: The line item description text
        default: Default code if no pattern matches (default: A103 - Draft/Revise)

    Returns:
        UTBMS activity code (e.g., "A103", "A106")
    """
    if not description:
        return default

    desc_lower = description.lower()

    for code, patterns in ACTIVITY_CODE_PATTERNS.items():
        for pattern in patterns:
            if pattern in desc_lower:
                return code

    return default
