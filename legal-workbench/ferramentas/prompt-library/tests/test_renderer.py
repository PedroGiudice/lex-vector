"""Testes para renderer.py - interpolação de variáveis."""

import pytest
from core.renderer import (
    render,
    preview,
    get_missing_variables,
    RenderError,
    MissingVariableError
)
from core.models import PromptTemplate, PromptVariable


@pytest.fixture
def simple_template():
    """Template simples com uma variável obrigatória."""
    return PromptTemplate(
        id="simple",
        titulo="Simple",
        categoria="test",
        descricao="Template simples",
        variaveis=[
            PromptVariable(nome="nome", label="Nome", obrigatorio=True)
        ],
        template="Olá, {nome}!"
    )


@pytest.fixture
def complex_template():
    """Template com múltiplas variáveis, algumas opcionais."""
    return PromptTemplate(
        id="complex",
        titulo="Complex",
        categoria="test",
        descricao="Template complexo",
        variaveis=[
            PromptVariable(nome="nome", label="Nome", obrigatorio=True),
            PromptVariable(nome="cargo", label="Cargo", obrigatorio=True),
            PromptVariable(
                nome="saudacao",
                label="Saudação",
                obrigatorio=False,
                default="Prezado(a)"
            ),
            PromptVariable(
                nome="assinatura",
                label="Assinatura",
                obrigatorio=False
            ),
        ],
        template="{saudacao} {nome},\n\nSeu cargo é: {cargo}\n\n{assinatura}"
    )


@pytest.fixture
def no_vars_template():
    """Template sem variáveis."""
    return PromptTemplate(
        id="static",
        titulo="Static",
        categoria="test",
        descricao="Template estático",
        variaveis=[],
        template="Este é um texto fixo sem variáveis."
    )


class TestGetMissingVariables:
    """Testes para get_missing_variables()."""

    def test_all_provided(self, simple_template):
        """Sem faltantes quando tudo fornecido."""
        missing = get_missing_variables(simple_template, {"nome": "João"})
        assert missing == []

    def test_missing_required(self, simple_template):
        """Detecta variável obrigatória faltando."""
        missing = get_missing_variables(simple_template, {})
        assert missing == ["nome"]

    def test_empty_string_counts_as_missing(self, simple_template):
        """String vazia conta como faltante."""
        missing = get_missing_variables(simple_template, {"nome": ""})
        assert missing == ["nome"]

        missing = get_missing_variables(simple_template, {"nome": "   "})
        assert missing == ["nome"]

    def test_optional_not_required(self, complex_template):
        """Variáveis opcionais não são reportadas como faltantes."""
        missing = get_missing_variables(
            complex_template,
            {"nome": "João", "cargo": "Dev"}
        )
        assert missing == []

    def test_default_satisfies_required(self, complex_template):
        """Default satisfaz requisito (não é faltante)."""
        # saudacao tem default, não deve aparecer em missing
        missing = get_missing_variables(
            complex_template,
            {"nome": "João", "cargo": "Dev"}
        )
        assert "saudacao" not in missing


class TestRender:
    """Testes para render()."""

    def test_simple_render(self, simple_template):
        """Renderiza template simples."""
        result = render(simple_template, {"nome": "Maria"})
        assert result == "Olá, Maria!"

    def test_complex_render_all_vars(self, complex_template):
        """Renderiza com todas as variáveis."""
        result = render(complex_template, {
            "nome": "Ana",
            "cargo": "Advogada",
            "saudacao": "Cara",
            "assinatura": "Atenciosamente"
        })
        assert "Cara Ana" in result
        assert "Advogada" in result
        assert "Atenciosamente" in result

    def test_render_uses_defaults(self, complex_template):
        """Usa valores default quando não fornecidos."""
        result = render(complex_template, {
            "nome": "Pedro",
            "cargo": "Gerente"
        })
        assert "Prezado(a) Pedro" in result  # default de saudacao

    def test_render_no_vars(self, no_vars_template):
        """Template sem variáveis renderiza normalmente."""
        result = render(no_vars_template, {})
        assert result == "Este é um texto fixo sem variáveis."

    def test_render_missing_required_raises(self, simple_template):
        """Levanta erro se variável obrigatória falta."""
        with pytest.raises(MissingVariableError) as exc_info:
            render(simple_template, {})

        assert "nome" in exc_info.value.missing_vars

    def test_render_missing_multiple(self, complex_template):
        """Reporta múltiplas variáveis faltantes."""
        with pytest.raises(MissingVariableError) as exc_info:
            render(complex_template, {})

        assert set(exc_info.value.missing_vars) == {"nome", "cargo"}

    def test_extra_vars_ignored(self, simple_template):
        """Variáveis extras são ignoradas."""
        result = render(simple_template, {
            "nome": "João",
            "extra": "ignorada",
            "outra": "também ignorada"
        })
        assert result == "Olá, João!"


class TestPreview:
    """Testes para preview()."""

    def test_preview_no_vars(self, simple_template):
        """Preview sem variáveis mostra marcadores."""
        result = preview(simple_template)
        assert result == "Olá, [nome]!"

    def test_preview_partial_vars(self, complex_template):
        """Preview com algumas variáveis preenchidas."""
        result = preview(complex_template, {"nome": "Ana"})

        assert "Ana" in result  # fornecida
        assert "[cargo]" in result  # não fornecida
        assert "Prezado(a)" in result  # default aplicado

    def test_preview_all_vars(self, simple_template):
        """Preview com todas as variáveis = render."""
        result = preview(simple_template, {"nome": "João"})
        assert result == "Olá, João!"

    def test_preview_uses_defaults(self, complex_template):
        """Preview usa defaults para variáveis com default."""
        result = preview(complex_template, {"nome": "Maria", "cargo": "Dev"})

        assert "Prezado(a)" in result  # default
        assert "[assinatura]" in result  # sem default, sem valor


class TestRenderError:
    """Testes para classes de erro."""

    def test_missing_variable_error_message(self):
        """MissingVariableError tem mensagem informativa."""
        error = MissingVariableError(["var1", "var2"])

        assert "var1" in str(error)
        assert "var2" in str(error)
        assert error.missing_vars == ["var1", "var2"]

    def test_render_error_is_exception(self):
        """RenderError é Exception."""
        assert issubclass(RenderError, Exception)
        assert issubclass(MissingVariableError, RenderError)
