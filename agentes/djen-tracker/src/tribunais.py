"""
Tribunais Brasileiros - Lista oficial para busca no DJEN.

Este módulo mantém a lista COMPLETA de tribunais brasileiros que publicam no
Diário de Justiça Eletrônico Nacional (DJEN).

TOTAL: 65 tribunais
- 5 Tribunais Superiores
- 27 Tribunais de Justiça Estaduais
- 6 Tribunais Regionais Federais
- 24 Tribunais Regionais do Trabalho
- 3 Tribunais de Justiça Militar

Fonte: https://comunica.pje.jus.br
"""
from typing import Dict, List, Set
from enum import Enum


class TipoTribunal(Enum):
    """Tipos de tribunais."""
    SUPERIOR = "Superior"
    ESTADUAL = "Estadual"
    FEDERAL = "Federal"
    TRABALHO = "Trabalho"
    MILITAR = "Militar"


# Tribunais Superiores (5)
TRIBUNAIS_SUPERIORES = {
    'STF': {'nome': 'Supremo Tribunal Federal', 'tipo': TipoTribunal.SUPERIOR},
    'STJ': {'nome': 'Superior Tribunal de Justiça', 'tipo': TipoTribunal.SUPERIOR},
    'TST': {'nome': 'Tribunal Superior do Trabalho', 'tipo': TipoTribunal.SUPERIOR},
    'TSE': {'nome': 'Tribunal Superior Eleitoral', 'tipo': TipoTribunal.SUPERIOR},
    'STM': {'nome': 'Superior Tribunal Militar', 'tipo': TipoTribunal.SUPERIOR},
}

# Tribunais de Justiça Estaduais (27)
TRIBUNAIS_ESTADUAIS = {
    'TJAC': {'nome': 'Tribunal de Justiça do Acre', 'tipo': TipoTribunal.ESTADUAL},
    'TJAL': {'nome': 'Tribunal de Justiça de Alagoas', 'tipo': TipoTribunal.ESTADUAL},
    'TJAM': {'nome': 'Tribunal de Justiça do Amazonas', 'tipo': TipoTribunal.ESTADUAL},
    'TJAP': {'nome': 'Tribunal de Justiça do Amapá', 'tipo': TipoTribunal.ESTADUAL},
    'TJBA': {'nome': 'Tribunal de Justiça da Bahia', 'tipo': TipoTribunal.ESTADUAL},
    'TJCE': {'nome': 'Tribunal de Justiça do Ceará', 'tipo': TipoTribunal.ESTADUAL},
    'TJDF': {'nome': 'Tribunal de Justiça do Distrito Federal', 'tipo': TipoTribunal.ESTADUAL},
    'TJES': {'nome': 'Tribunal de Justiça do Espírito Santo', 'tipo': TipoTribunal.ESTADUAL},
    'TJGO': {'nome': 'Tribunal de Justiça de Goiás', 'tipo': TipoTribunal.ESTADUAL},
    'TJMA': {'nome': 'Tribunal de Justiça do Maranhão', 'tipo': TipoTribunal.ESTADUAL},
    'TJMG': {'nome': 'Tribunal de Justiça de Minas Gerais', 'tipo': TipoTribunal.ESTADUAL},
    'TJMS': {'nome': 'Tribunal de Justiça de Mato Grosso do Sul', 'tipo': TipoTribunal.ESTADUAL},
    'TJMT': {'nome': 'Tribunal de Justiça de Mato Grosso', 'tipo': TipoTribunal.ESTADUAL},
    'TJPA': {'nome': 'Tribunal de Justiça do Pará', 'tipo': TipoTribunal.ESTADUAL},
    'TJPB': {'nome': 'Tribunal de Justiça da Paraíba', 'tipo': TipoTribunal.ESTADUAL},
    'TJPE': {'nome': 'Tribunal de Justiça de Pernambuco', 'tipo': TipoTribunal.ESTADUAL},
    'TJPI': {'nome': 'Tribunal de Justiça do Piauí', 'tipo': TipoTribunal.ESTADUAL},
    'TJPR': {'nome': 'Tribunal de Justiça do Paraná', 'tipo': TipoTribunal.ESTADUAL},
    'TJRJ': {'nome': 'Tribunal de Justiça do Rio de Janeiro', 'tipo': TipoTribunal.ESTADUAL},
    'TJRN': {'nome': 'Tribunal de Justiça do Rio Grande do Norte', 'tipo': TipoTribunal.ESTADUAL},
    'TJRO': {'nome': 'Tribunal de Justiça de Rondônia', 'tipo': TipoTribunal.ESTADUAL},
    'TJRR': {'nome': 'Tribunal de Justiça de Roraima', 'tipo': TipoTribunal.ESTADUAL},
    'TJRS': {'nome': 'Tribunal de Justiça do Rio Grande do Sul', 'tipo': TipoTribunal.ESTADUAL},
    'TJSC': {'nome': 'Tribunal de Justiça de Santa Catarina', 'tipo': TipoTribunal.ESTADUAL},
    'TJSE': {'nome': 'Tribunal de Justiça de Sergipe', 'tipo': TipoTribunal.ESTADUAL},
    'TJSP': {'nome': 'Tribunal de Justiça de São Paulo', 'tipo': TipoTribunal.ESTADUAL},
    'TJTO': {'nome': 'Tribunal de Justiça do Tocantins', 'tipo': TipoTribunal.ESTADUAL},
}

# Tribunais Regionais Federais (6)
TRIBUNAIS_FEDERAIS = {
    'TRF1': {'nome': 'Tribunal Regional Federal da 1ª Região', 'tipo': TipoTribunal.FEDERAL},
    'TRF2': {'nome': 'Tribunal Regional Federal da 2ª Região', 'tipo': TipoTribunal.FEDERAL},
    'TRF3': {'nome': 'Tribunal Regional Federal da 3ª Região', 'tipo': TipoTribunal.FEDERAL},
    'TRF4': {'nome': 'Tribunal Regional Federal da 4ª Região', 'tipo': TipoTribunal.FEDERAL},
    'TRF5': {'nome': 'Tribunal Regional Federal da 5ª Região', 'tipo': TipoTribunal.FEDERAL},
    'TRF6': {'nome': 'Tribunal Regional Federal da 6ª Região', 'tipo': TipoTribunal.FEDERAL},
}

# Tribunais Regionais do Trabalho (24)
TRIBUNAIS_TRABALHO = {
    'TRT1': {'nome': 'Tribunal Regional do Trabalho da 1ª Região (RJ)', 'tipo': TipoTribunal.TRABALHO},
    'TRT2': {'nome': 'Tribunal Regional do Trabalho da 2ª Região (SP)', 'tipo': TipoTribunal.TRABALHO},
    'TRT3': {'nome': 'Tribunal Regional do Trabalho da 3ª Região (MG)', 'tipo': TipoTribunal.TRABALHO},
    'TRT4': {'nome': 'Tribunal Regional do Trabalho da 4ª Região (RS)', 'tipo': TipoTribunal.TRABALHO},
    'TRT5': {'nome': 'Tribunal Regional do Trabalho da 5ª Região (BA)', 'tipo': TipoTribunal.TRABALHO},
    'TRT6': {'nome': 'Tribunal Regional do Trabalho da 6ª Região (PE)', 'tipo': TipoTribunal.TRABALHO},
    'TRT7': {'nome': 'Tribunal Regional do Trabalho da 7ª Região (CE)', 'tipo': TipoTribunal.TRABALHO},
    'TRT8': {'nome': 'Tribunal Regional do Trabalho da 8ª Região (PA/AP)', 'tipo': TipoTribunal.TRABALHO},
    'TRT9': {'nome': 'Tribunal Regional do Trabalho da 9ª Região (PR)', 'tipo': TipoTribunal.TRABALHO},
    'TRT10': {'nome': 'Tribunal Regional do Trabalho da 10ª Região (DF/TO)', 'tipo': TipoTribunal.TRABALHO},
    'TRT11': {'nome': 'Tribunal Regional do Trabalho da 11ª Região (AM/RR)', 'tipo': TipoTribunal.TRABALHO},
    'TRT12': {'nome': 'Tribunal Regional do Trabalho da 12ª Região (SC)', 'tipo': TipoTribunal.TRABALHO},
    'TRT13': {'nome': 'Tribunal Regional do Trabalho da 13ª Região (PB)', 'tipo': TipoTribunal.TRABALHO},
    'TRT14': {'nome': 'Tribunal Regional do Trabalho da 14ª Região (RO/AC)', 'tipo': TipoTribunal.TRABALHO},
    'TRT15': {'nome': 'Tribunal Regional do Trabalho da 15ª Região (SP - Campinas)', 'tipo': TipoTribunal.TRABALHO},
    'TRT16': {'nome': 'Tribunal Regional do Trabalho da 16ª Região (MA)', 'tipo': TipoTribunal.TRABALHO},
    'TRT17': {'nome': 'Tribunal Regional do Trabalho da 17ª Região (ES)', 'tipo': TipoTribunal.TRABALHO},
    'TRT18': {'nome': 'Tribunal Regional do Trabalho da 18ª Região (GO)', 'tipo': TipoTribunal.TRABALHO},
    'TRT19': {'nome': 'Tribunal Regional do Trabalho da 19ª Região (AL)', 'tipo': TipoTribunal.TRABALHO},
    'TRT20': {'nome': 'Tribunal Regional do Trabalho da 20ª Região (SE)', 'tipo': TipoTribunal.TRABALHO},
    'TRT21': {'nome': 'Tribunal Regional do Trabalho da 21ª Região (RN)', 'tipo': TipoTribunal.TRABALHO},
    'TRT22': {'nome': 'Tribunal Regional do Trabalho da 22ª Região (PI)', 'tipo': TipoTribunal.TRABALHO},
    'TRT23': {'nome': 'Tribunal Regional do Trabalho da 23ª Região (MT)', 'tipo': TipoTribunal.TRABALHO},
    'TRT24': {'nome': 'Tribunal Regional do Trabalho da 24ª Região (MS)', 'tipo': TipoTribunal.TRABALHO},
}

# Tribunais de Justiça Militar (3)
TRIBUNAIS_MILITARES = {
    'TJMSP': {'nome': 'Tribunal de Justiça Militar de São Paulo', 'tipo': TipoTribunal.MILITAR},
    'TJMRS': {'nome': 'Tribunal de Justiça Militar do Rio Grande do Sul', 'tipo': TipoTribunal.MILITAR},
    'TJMMG': {'nome': 'Tribunal de Justiça Militar de Minas Gerais', 'tipo': TipoTribunal.MILITAR},
}


def get_all_tribunais() -> Dict[str, Dict]:
    """
    Retorna TODOS os tribunais brasileiros.

    Returns:
        Dict com sigla -> {nome, tipo}
    """
    todos = {}
    todos.update(TRIBUNAIS_SUPERIORES)
    todos.update(TRIBUNAIS_ESTADUAIS)
    todos.update(TRIBUNAIS_FEDERAIS)
    todos.update(TRIBUNAIS_TRABALHO)
    todos.update(TRIBUNAIS_MILITARES)
    return todos


def get_tribunais_by_type(tipo: TipoTribunal) -> Dict[str, Dict]:
    """
    Retorna tribunais de um tipo específico.

    Args:
        tipo: TipoTribunal enum

    Returns:
        Dict com sigla -> {nome, tipo}
    """
    todos = get_all_tribunais()
    return {
        sigla: info
        for sigla, info in todos.items()
        if info['tipo'] == tipo
    }


def get_tribunais_prioritarios() -> List[str]:
    """
    Retorna lista de tribunais prioritários (sugestão padrão).

    Baseado em volume de publicações e relevância:
    - Todos os Superiores (STF, STJ, TST, TSE, STM)
    - TRFs (federais)
    - TJs maiores (SP, RJ, MG, RS, PR, SC, DF, BA, CE, PE)
    - TRTs maiores (1-SP, 2-SP, 3-MG, 4-RS, 9-PR, 15-SP)

    Returns:
        Lista de siglas
    """
    prioritarios = []

    # Todos os superiores
    prioritarios.extend(TRIBUNAIS_SUPERIORES.keys())

    # Todos os federais
    prioritarios.extend(TRIBUNAIS_FEDERAIS.keys())

    # Estaduais maiores
    estaduais_prioritarios = [
        'TJSP', 'TJRJ', 'TJMG', 'TJRS', 'TJPR', 'TJSC',
        'TJDF', 'TJBA', 'TJCE', 'TJPE'
    ]
    prioritarios.extend(estaduais_prioritarios)

    # TRTs maiores
    trts_prioritarios = ['TRT1', 'TRT2', 'TRT3', 'TRT4', 'TRT9', 'TRT15']
    prioritarios.extend(trts_prioritarios)

    return prioritarios


def get_siglas() -> List[str]:
    """
    Retorna lista de todas as siglas.

    Returns:
        Lista ordenada de siglas
    """
    return sorted(get_all_tribunais().keys())


def get_count() -> int:
    """
    Retorna total de tribunais.

    Returns:
        Número de tribunais
    """
    return len(get_all_tribunais())


def get_stats() -> Dict:
    """
    Retorna estatísticas sobre os tribunais.

    Returns:
        Dict com contagens por tipo
    """
    todos = get_all_tribunais()
    stats = {
        'total': len(todos),
        'superiores': len(TRIBUNAIS_SUPERIORES),
        'estaduais': len(TRIBUNAIS_ESTADUAIS),
        'federais': len(TRIBUNAIS_FEDERAIS),
        'trabalho': len(TRIBUNAIS_TRABALHO),
        'militares': len(TRIBUNAIS_MILITARES),
    }
    return stats


def validate_sigla(sigla: str) -> bool:
    """
    Valida se uma sigla é válida.

    Args:
        sigla: Sigla do tribunal

    Returns:
        True se válida
    """
    return sigla.upper() in get_all_tribunais()


# Aliases para compatibilidade com config.json
TODOS_OS_TRIBUNAIS = get_siglas()
TRIBUNAIS_PRIORITARIOS_DEFAULT = get_tribunais_prioritarios()


if __name__ == '__main__':
    """Mostra estatísticas ao executar o módulo."""
    stats = get_stats()
    print("=" * 70)
    print("TRIBUNAIS BRASILEIROS - DJEN")
    print("=" * 70)
    print(f"Total: {stats['total']}")
    print(f"  - Superiores: {stats['superiores']}")
    print(f"  - Estaduais: {stats['estaduais']}")
    print(f"  - Federais: {stats['federais']}")
    print(f"  - Trabalho: {stats['trabalho']}")
    print(f"  - Militares: {stats['militares']}")
    print("=" * 70)
    print("\nPrioritários (sugestão):")
    for sigla in get_tribunais_prioritarios():
        info = get_all_tribunais()[sigla]
        print(f"  - {sigla}: {info['nome']}")
