"""Testes para models.py - validação de schemas Pydantic."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from core.models import PromptVariable, PromptTemplate, PromptLibrary


class TestPromptVariable:
    """Testes para PromptVariable."""

    def test_minimal_valid(self):
        """Variável com campos mínimos obrigatórios."""
        var = PromptVariable(nome="teste", label="Teste")
        assert var.nome == "teste"
        assert var.label == "Teste"
        assert var.tipo == "text"  # default
        assert var.obrigatorio is True  # default

    def test_all_fields(self):
        """Variável com todos os campos."""
        var = PromptVariable(
            nome="status",
            label="Status do Processo",
            tipo="select",
            obrigatorio=False,
            opcoes=["ativo", "arquivado", "suspenso"],
            placeholder="Selecione...",
            default="ativo"
        )
        assert var.tipo == "select"
        assert len(var.opcoes) == 3
        assert var.default == "ativo"

    def test_missing_required_field(self):
        """Deve falhar sem campo obrigatório."""
        with pytest.raises(ValidationError):
            PromptVariable(nome="teste")  # falta label

    def test_invalid_tipo(self):
        """Deve falhar com tipo inválido."""
        with pytest.raises(ValidationError):
            PromptVariable(nome="x", label="X", tipo="invalid")


class TestPromptTemplate:
    """Testes para PromptTemplate."""

    def test_minimal_valid(self):
        """Template com campos mínimos."""
        template = PromptTemplate(
            id="test_001",
            titulo="Teste",
            categoria="teste",
            descricao="Um teste",
            template="Olá {nome}"
        )
        assert template.id == "test_001"
        assert template.versao == "1.0"  # default
        assert template.tags == []  # default
        assert template.variaveis == []  # default

    def test_with_variables(self):
        """Template com variáveis definidas."""
        template = PromptTemplate(
            id="contract_review",
            titulo="Revisão de Contrato",
            categoria="juridico",
            descricao="Analisa cláusulas contratuais",
            variaveis=[
                PromptVariable(nome="contrato", label="Texto do Contrato", tipo="textarea"),
                PromptVariable(nome="foco", label="Foco da Análise", obrigatorio=False)
            ],
            template="Analise o contrato:\n{contrato}\n\nFoco: {foco}"
        )
        assert len(template.variaveis) == 2
        assert template.variaveis[0].tipo == "textarea"

    def test_with_metadata(self):
        """Template com metadados opcionais."""
        now = datetime.now()
        template = PromptTemplate(
            id="meta_001",
            titulo="Com Metadados",
            categoria="meta",
            descricao="Teste",
            template="...",
            autor="dev@test.com",
            versao="2.1",
            criado_em=now
        )
        assert template.autor == "dev@test.com"
        assert template.versao == "2.1"
        assert template.criado_em == now

    def test_missing_required(self):
        """Deve falhar sem campos obrigatórios."""
        with pytest.raises(ValidationError):
            PromptTemplate(id="x", titulo="X")  # falta categoria, descricao, template


class TestPromptLibrary:
    """Testes para PromptLibrary."""

    @pytest.fixture
    def sample_library(self):
        """Biblioteca de exemplo com 3 prompts."""
        return PromptLibrary(prompts=[
            PromptTemplate(
                id="juridico_001",
                titulo="Análise de Petição",
                categoria="juridico",
                descricao="Analisa petições",
                tags=["peticao", "analise"],
                template="..."
            ),
            PromptTemplate(
                id="juridico_002",
                titulo="Revisão de Contrato",
                categoria="juridico",
                descricao="Revisa contratos",
                tags=["contrato"],
                template="..."
            ),
            PromptTemplate(
                id="troubleshoot_001",
                titulo="Debug de Hook",
                categoria="troubleshooting",
                descricao="Ajuda com erros de hook",
                tags=["hook", "debug"],
                template="..."
            ),
        ])

    def test_empty_library(self):
        """Biblioteca vazia."""
        lib = PromptLibrary()
        assert lib.prompts == []
        assert lib.list_categorias() == []

    def test_get_by_id_found(self, sample_library):
        """Busca por ID existente."""
        result = sample_library.get_by_id("juridico_001")
        assert result is not None
        assert result.titulo == "Análise de Petição"

    def test_get_by_id_not_found(self, sample_library):
        """Busca por ID inexistente."""
        result = sample_library.get_by_id("nao_existe")
        assert result is None

    def test_get_by_categoria(self, sample_library):
        """Filtro por categoria."""
        juridicos = sample_library.get_by_categoria("juridico")
        assert len(juridicos) == 2

        troubleshoot = sample_library.get_by_categoria("troubleshooting")
        assert len(troubleshoot) == 1

    def test_list_categorias(self, sample_library):
        """Lista categorias únicas ordenadas."""
        categorias = sample_library.list_categorias()
        assert categorias == ["juridico", "troubleshooting"]
