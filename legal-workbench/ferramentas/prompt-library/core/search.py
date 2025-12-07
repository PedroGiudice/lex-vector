"""
Busca fuzzy em templates de prompt.

Responsabilidades:
- Busca por título, tags, descrição
- Filtro por categoria
- Ordenação por relevância
"""

from typing import List, Optional
from .models import PromptLibrary, PromptTemplate


def _normalize(text: str) -> str:
    """Normaliza texto para busca (lowercase, strip)."""
    return text.lower().strip()


def _calculate_score(query: str, prompt: PromptTemplate) -> int:
    """
    Calcula score de relevância para um prompt.

    Pontuação:
    - Match exato no título: 100
    - Título começa com query: 50
    - Query contida no título: 30
    - Match exato em tag: 25
    - Query contida em tag: 15
    - Query contida na descrição: 10
    - Match exato no ID: 80

    Returns:
        Score total (0 = sem match)
    """
    score = 0
    normalized_query = _normalize(query)

    if not normalized_query:
        return 0

    # Verificar match no ID
    normalized_id = _normalize(prompt.id)
    if normalized_query == normalized_id:
        score += 80

    # Verificar match no título
    normalized_titulo = _normalize(prompt.titulo)
    if normalized_query == normalized_titulo:
        score += 100
    elif normalized_titulo.startswith(normalized_query):
        score += 50
    elif normalized_query in normalized_titulo:
        score += 30

    # Verificar match em tags
    for tag in prompt.tags:
        normalized_tag = _normalize(tag)
        if normalized_query == normalized_tag:
            score += 25
        elif normalized_query in normalized_tag:
            score += 15

    # Verificar match na descrição
    normalized_descricao = _normalize(prompt.descricao)
    if normalized_query in normalized_descricao:
        score += 10

    return score


def search(
    library: PromptLibrary,
    query: str,
    categoria: Optional[str] = None,
    limit: int = 20
) -> List[PromptTemplate]:
    """
    Busca fuzzy na biblioteca.

    Busca em: titulo, tags, descricao
    Ordena por relevância (match no título > tags > descrição)

    Args:
        library: Biblioteca de prompts
        query: Termo de busca
        categoria: Filtro opcional por categoria
        limit: Máximo de resultados

    Returns:
        Lista de prompts ordenados por relevância
    """
    # Se a query está vazia, retornar todos os prompts (filtrados por categoria)
    normalized_query = _normalize(query)

    if not normalized_query:
        prompts = library.prompts
        if categoria:
            normalized_categoria = _normalize(categoria)
            prompts = [
                p for p in prompts
                if _normalize(p.categoria) == normalized_categoria
            ]
        return prompts[:limit]

    # Calcular score para cada prompt
    scored_prompts = []
    for prompt in library.prompts:
        # Filtrar por categoria se especificado
        if categoria:
            normalized_categoria = _normalize(categoria)
            if _normalize(prompt.categoria) != normalized_categoria:
                continue

        # Calcular score
        score = _calculate_score(query, prompt)

        # Manter apenas prompts com score > 0
        if score > 0:
            scored_prompts.append((score, prompt))

    # Ordenar por score decrescente
    scored_prompts.sort(key=lambda x: x[0], reverse=True)

    # Retornar até o limite de resultados
    return [prompt for _, prompt in scored_prompts[:limit]]


def filter_by_tags(
    library: PromptLibrary,
    tags: List[str],
    match_all: bool = False
) -> List[PromptTemplate]:
    """
    Filtra por tags.

    Args:
        library: Biblioteca de prompts
        tags: Lista de tags para filtrar
        match_all: Se True, exige todas as tags; se False, qualquer uma

    Returns:
        Lista de prompts que correspondem aos critérios
    """
    # Se a lista de tags está vazia, retornar todos os prompts
    if not tags:
        return library.prompts

    # Normalizar todas as tags de entrada
    normalized_input_tags = {_normalize(tag) for tag in tags}

    # Filtrar prompts
    matching_prompts = []
    for prompt in library.prompts:
        # Normalizar tags do prompt
        normalized_prompt_tags = {_normalize(tag) for tag in prompt.tags}

        if match_all:
            # Verificar se todas as tags de entrada estão nas tags do prompt
            if normalized_input_tags.issubset(normalized_prompt_tags):
                matching_prompts.append(prompt)
        else:
            # Verificar se pelo menos uma tag de entrada está nas tags do prompt
            if normalized_input_tags.intersection(normalized_prompt_tags):
                matching_prompts.append(prompt)

    return matching_prompts
