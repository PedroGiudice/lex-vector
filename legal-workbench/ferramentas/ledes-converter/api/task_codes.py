"""Classificação automática de códigos UTBMS para line items LEDES 1998B.

Mapeia descrições de atividades jurídicas para task codes (Lxxx) e
activity codes (Axxx) usando padrões regex bilíngues (PT-BR e EN).
"""

import re

# Task codes UTBMS para Litigation
TASK_CODE_PATTERNS: list[tuple[str, str]] = [
    # L510 - Appeals (recursos)
    (r"(?i)(appeal|recurso|apela[cç][aã]o|agravo|embargos?\s+de\s+declara)", "L510"),
    # L210 - Pleadings (defesas, contestações)
    (r"(?i)(defesa|defense|contesta[cç][aã]o|pleading|answer|resposta)", "L210"),
    # L160 - Settlement/ADR (negociações, acordos)
    (r"(?i)(acordo|settlement|negocia[cç][aã]o|media[cç][aã]o|concilia)", "L160"),
    # L250 - Other Written Motions (petições diversas)
    (r"(?i)(peti[cç][aã]o|motion|requerimento|manifesta[cç][aã]o)", "L250"),
    # L120 - Fact Investigation/Development
    (r"(?i)(investiga|dilig[eê]ncia|fact\s+finding|discovery|inqu[eé]rito)", "L120"),
    # L310 - Witness Management
    (r"(?i)(testemunha|witness|depoi?mento|oitiva|audi[eê]ncia)", "L310"),
    # L100 - Case Assessment
    (r"(?i)(an[aá]lise\s+(do\s+)?caso|case\s+assess|parecer|estudo)", "L100"),
]

ACTIVITY_CODE_PATTERNS: list[tuple[str, str]] = [
    # A103 - Draft/Revise
    (r"(?i)(draft|revise|elabora|redigi|reda[cç][aã]o|minuta|prepar)", "A103"),
    # A106 - Communicate (with client/opposing counsel)
    (r"(?i)(communic|reuni[aã]o|meeting|conference|e-?mail|correspond[eê]ncia)", "A106"),
    # A101 - Plan and Prepare
    (r"(?i)(plan|organiz|estrateg|estrat[eé]g)", "A101"),
    # A102 - Research
    (r"(?i)(research|pesquis|jurisprud|doutrina|bibliog)", "A102"),
    # A104 - Review/Analyze
    (r"(?i)(review|an[aá]lis|exam[ei]|verific|estud)", "A104"),
    # A107 - Travel
    (r"(?i)(travel|viag|desloca|translad)", "A107"),
]


def classify_task_code(description: str) -> str:
    """Retorna o task code UTBMS mais específico ou '' se nenhum match."""
    if not description:
        return ""
    for pattern, code in TASK_CODE_PATTERNS:
        if re.search(pattern, description):
            return code
    return ""


def classify_activity_code(description: str) -> str:
    """Retorna o activity code UTBMS mais específico ou '' se nenhum match."""
    if not description:
        return ""
    for pattern, code in ACTIVITY_CODE_PATTERNS:
        if re.search(pattern, description):
            return code
    return ""
