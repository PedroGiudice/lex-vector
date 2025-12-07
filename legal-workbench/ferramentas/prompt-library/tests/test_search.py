"""Testes para search.py - busca fuzzy e filtros."""

import pytest
from core.search import search, filter_by_tags, _normalize, _calculate_score
from core.models import PromptTemplate, PromptLibrary


@pytest.fixture
def sample_library():
    """Biblioteca com prompts variados para teste de busca."""
    return PromptLibrary(prompts=[
        PromptTemplate(
            id="contrato_analise",
            titulo="Análise de Contrato",
            categoria="juridico",
            descricao="Analisa cláusulas e riscos em contratos comerciais",
            tags=["contrato", "analise", "risco"],
            template="..."
        ),
        PromptTemplate(
            id="contrato_revisao",
            titulo="Revisão de Contrato",
            categoria="juridico",
            descricao="Revisa contratos para identificar problemas",
            tags=["contrato", "revisao"],
            template="..."
        ),
        PromptTemplate(
            id="hook_error",
            titulo="Debug de Hook Error",
            categoria="troubleshooting",
            descricao="Ajuda a resolver erros em hooks do Claude",
            tags=["hook", "erro", "debug", "claude"],
            template="..."
        ),
        PromptTemplate(
            id="git_merge",
            titulo="Resolver Conflito Git",
            categoria="troubleshooting",
            descricao="Guia para resolver conflitos de merge",
            tags=["git", "merge", "conflito"],
            template="..."
        ),
        PromptTemplate(
            id="formular_pedido",
            titulo="Como Formular Pedidos",
            categoria="meta",
            descricao="Meta-prompt sobre como fazer bons pedidos ao Claude",
            tags=["meta", "pedido", "prompt"],
            template="..."
        ),
    ])


class TestNormalize:
    """Testes para _normalize()."""

    def test_lowercase(self):
        assert _normalize("TESTE") == "teste"

    def test_strip(self):
        assert _normalize("  teste  ") == "teste"

    def test_combined(self):
        assert _normalize("  TESTE  ") == "teste"


class TestCalculateScore:
    """Testes para _calculate_score()."""

    def test_exact_title_match(self, sample_library):
        """Match exato no título = 100 pontos."""
        prompt = sample_library.prompts[0]  # "Análise de Contrato"
        score = _calculate_score("Análise de Contrato", prompt)
        assert score >= 100

    def test_title_starts_with(self, sample_library):
        """Título começa com query = 50 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("Análise", prompt)
        assert score >= 50

    def test_title_contains(self, sample_library):
        """Query contida no título = 30 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("Contrato", prompt)
        assert score >= 30

    def test_exact_tag_match(self, sample_library):
        """Match exato em tag = 25 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("risco", prompt)
        assert score >= 25

    def test_description_match(self, sample_library):
        """Query na descrição = 10 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("cláusulas", prompt)
        assert score >= 10

    def test_no_match(self, sample_library):
        """Sem match = 0 pontos."""
        prompt = sample_library.prompts[0]
        score = _calculate_score("xyz123", prompt)
        assert score == 0


class TestSearch:
    """Testes para search()."""

    def test_search_by_title(self, sample_library):
        """Busca por título retorna resultados ordenados."""
        results = search(sample_library, "Contrato")

        assert len(results) == 2
        # Ambos têm "Contrato" no título
        assert all("contrato" in r.id for r in results)

    def test_search_by_tag(self, sample_library):
        """Busca por tag encontra prompts."""
        results = search(sample_library, "debug")

        assert len(results) == 1
        assert results[0].id == "hook_error"

    def test_search_by_description(self, sample_library):
        """Busca por termo na descrição."""
        results = search(sample_library, "merge")

        assert len(results) == 1
        assert results[0].id == "git_merge"

    def test_search_with_categoria_filter(self, sample_library):
        """Filtro por categoria."""
        # Busca "contrato" mas apenas em troubleshooting (não deve encontrar)
        results = search(sample_library, "contrato", categoria="troubleshooting")
        assert len(results) == 0

        # Busca em juridico (deve encontrar)
        results = search(sample_library, "contrato", categoria="juridico")
        assert len(results) == 2

    def test_search_with_limit(self, sample_library):
        """Respeita limite de resultados."""
        results = search(sample_library, "contrato", limit=1)
        assert len(results) == 1

    def test_search_empty_query_returns_all(self, sample_library):
        """Query vazia retorna todos os prompts."""
        results = search(sample_library, "")
        assert len(results) == 5

        results = search(sample_library, "   ")
        assert len(results) == 5

    def test_search_empty_query_with_categoria(self, sample_library):
        """Query vazia com filtro de categoria."""
        results = search(sample_library, "", categoria="juridico")
        assert len(results) == 2

    def test_search_relevance_order(self, sample_library):
        """Resultados ordenados por relevância."""
        results = search(sample_library, "hook")

        # "hook_error" deve vir primeiro (match no ID e tag)
        assert results[0].id == "hook_error"


class TestFilterByTags:
    """Testes para filter_by_tags()."""

    def test_single_tag_any_match(self, sample_library):
        """Filtro por uma tag (match_all=False)."""
        results = filter_by_tags(sample_library, ["contrato"])

        assert len(results) == 2
        assert all("contrato" in p.tags for p in results)

    def test_multiple_tags_any_match(self, sample_library):
        """Múltiplas tags, qualquer uma (OR)."""
        results = filter_by_tags(sample_library, ["contrato", "git"])

        assert len(results) == 3  # 2 contratos + 1 git

    def test_multiple_tags_all_match(self, sample_library):
        """Múltiplas tags, todas (AND)."""
        results = filter_by_tags(sample_library, ["contrato", "analise"], match_all=True)

        assert len(results) == 1
        assert results[0].id == "contrato_analise"

    def test_no_matching_tags(self, sample_library):
        """Nenhum prompt tem a tag."""
        results = filter_by_tags(sample_library, ["inexistente"])
        assert len(results) == 0

    def test_empty_tags_returns_all(self, sample_library):
        """Lista de tags vazia retorna todos."""
        results = filter_by_tags(sample_library, [])
        assert len(results) == 5

    def test_case_insensitive(self, sample_library):
        """Busca por tag é case-insensitive."""
        results = filter_by_tags(sample_library, ["CONTRATO"])
        assert len(results) == 2
