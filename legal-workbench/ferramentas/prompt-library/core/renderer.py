"""
Renderização de templates de prompt com interpolação de variáveis.

Responsabilidades:
- Interpolar variáveis no template
- Validar variáveis obrigatórias
- Fornecer preview com placeholders
"""

from typing import Dict, List, Optional
from .models import PromptTemplate


class RenderError(Exception):
    """Erro ao renderizar template."""
    pass


class MissingVariableError(RenderError):
    """Variável obrigatória não fornecida."""

    def __init__(self, missing_vars: List[str]):
        self.missing_vars = missing_vars
        super().__init__(f"Variáveis obrigatórias faltando: {', '.join(missing_vars)}")


def get_missing_variables(
    template: PromptTemplate,
    variables: Dict[str, str]
) -> List[str]:
    """
    Retorna lista de variáveis obrigatórias faltando.

    Args:
        template: Template a verificar
        variables: Variáveis fornecidas

    Returns:
        Lista de nomes de variáveis obrigatórias não fornecidas
    """
    missing = []

    for variable in template.variaveis:
        if variable.obrigatorio:
            # Verifica se variável foi fornecida e tem valor não-vazio
            value = variables.get(variable.nome)
            has_value = value is not None and str(value).strip() != ""

            # Se não tem valor E não tem default, está faltando
            if not has_value and variable.default is None:
                missing.append(variable.nome)

    return missing


def _apply_defaults(
    template: PromptTemplate,
    variables: Dict[str, str]
) -> Dict[str, str]:
    """
    Aplica valores default para variáveis não fornecidas.

    Args:
        template: Template com definições de variáveis
        variables: Variáveis fornecidas pelo usuário

    Returns:
        Dicionário com valores (fornecidos + defaults)
    """
    result = variables.copy()

    for variable in template.variaveis:
        # Verifica se variável não foi fornecida ou está vazia
        value = result.get(variable.nome)
        is_empty = value is None or str(value).strip() == ""

        # Se está vazia E tem default, aplica o default
        if is_empty and variable.default is not None:
            result[variable.nome] = variable.default

    return result


def render(
    template: PromptTemplate,
    variables: Dict[str, str]
) -> str:
    """
    Renderiza template com variáveis.

    Args:
        template: Template a renderizar
        variables: Dicionário de variáveis {nome: valor}

    Returns:
        Texto do prompt com variáveis interpoladas

    Raises:
        MissingVariableError: Se variável obrigatória não fornecida
    """
    # 1. Aplica defaults
    vars_with_defaults = _apply_defaults(template, variables)

    # 2. Verifica variáveis obrigatórias faltando
    missing = get_missing_variables(template, vars_with_defaults)

    # 3. Se tem variáveis faltando, lança exceção
    if missing:
        raise MissingVariableError(missing)

    # 4. Interpola variáveis no template
    result = template.template

    for variable in template.variaveis:
        placeholder = "{" + variable.nome + "}"
        value = vars_with_defaults.get(variable.nome, "")
        result = result.replace(placeholder, str(value))

    return result


def preview(
    template: PromptTemplate,
    variables: Optional[Dict[str, str]] = None
) -> str:
    """
    Preview do template.

    Variáveis não fornecidas aparecem como [{nome}]

    Args:
        template: Template a visualizar
        variables: Variáveis opcionais para preencher

    Returns:
        Texto com variáveis interpoladas ou marcadores
    """
    # 1. Usa dicionário vazio se não fornecido
    vars_dict = variables or {}

    # 2. Aplica defaults
    vars_with_defaults = _apply_defaults(template, vars_dict)

    # 3. Interpola variáveis ou substitui por marcadores
    result = template.template

    for variable in template.variaveis:
        placeholder = "{" + variable.nome + "}"
        value = vars_with_defaults.get(variable.nome)

        # Se tem valor não-vazio, interpola
        if value is not None and str(value).strip():
            result = result.replace(placeholder, str(value))
        else:
            # Senão, mostra marcador
            result = result.replace(placeholder, f"[{variable.nome}]")

    return result
