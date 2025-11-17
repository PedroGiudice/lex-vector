"""
Testes para módulo tribunais.py - Lista de tribunais brasileiros.

Valida:
- Total de 65 tribunais
- Categorização correta (Superiores, Estaduais, Federais, Trabalho, Militares)
- Funções de consulta e filtro
- Validação de siglas
- Estatísticas
"""

import pytest
from src.tribunais import (
    TipoTribunal,
    TRIBUNAIS_SUPERIORES,
    TRIBUNAIS_ESTADUAIS,
    TRIBUNAIS_FEDERAIS,
    TRIBUNAIS_TRABALHO,
    TRIBUNAIS_MILITARES,
    get_all_tribunais,
    get_tribunais_by_type,
    get_tribunais_prioritarios,
    get_siglas,
    get_count,
    get_stats,
    validate_sigla
)


class TestTribunaisConstants:
    """Testes para constantes de tribunais."""

    def test_total_tribunais_superiores(self):
        """Valida que existem exatamente 5 tribunais superiores."""
        assert len(TRIBUNAIS_SUPERIORES) == 5

    def test_total_tribunais_estaduais(self):
        """Valida que existem exatamente 27 tribunais estaduais."""
        assert len(TRIBUNAIS_ESTADUAIS) == 27

    def test_total_tribunais_federais(self):
        """Valida que existem exatamente 6 tribunais federais (TRFs)."""
        assert len(TRIBUNAIS_FEDERAIS) == 6

    def test_total_tribunais_trabalho(self):
        """Valida que existem exatamente 24 tribunais do trabalho (TRTs)."""
        assert len(TRIBUNAIS_TRABALHO) == 24

    def test_total_tribunais_militares(self):
        """Valida que existem exatamente 3 tribunais militares."""
        assert len(TRIBUNAIS_MILITARES) == 3

    def test_tribunais_superiores_conhecidos(self):
        """Valida presença dos principais tribunais superiores."""
        assert 'STF' in TRIBUNAIS_SUPERIORES
        assert 'STJ' in TRIBUNAIS_SUPERIORES
        assert 'TST' in TRIBUNAIS_SUPERIORES
        assert 'TSE' in TRIBUNAIS_SUPERIORES
        assert 'STM' in TRIBUNAIS_SUPERIORES

    def test_tribunais_estaduais_conhecidos(self):
        """Valida presença de tribunais estaduais importantes."""
        assert 'TJSP' in TRIBUNAIS_ESTADUAIS
        assert 'TJRJ' in TRIBUNAIS_ESTADUAIS
        assert 'TJMG' in TRIBUNAIS_ESTADUAIS
        assert 'TJRS' in TRIBUNAIS_ESTADUAIS
        assert 'TJDF' in TRIBUNAIS_ESTADUAIS

    def test_todos_tribunais_tem_nome(self):
        """Valida que todos tribunais têm campo 'nome'."""
        todos = get_all_tribunais()
        for sigla, info in todos.items():
            assert 'nome' in info, f"{sigla} não tem campo 'nome'"
            assert isinstance(info['nome'], str)
            assert len(info['nome']) > 0

    def test_todos_tribunais_tem_tipo(self):
        """Valida que todos tribunais têm campo 'tipo'."""
        todos = get_all_tribunais()
        for sigla, info in todos.items():
            assert 'tipo' in info, f"{sigla} não tem campo 'tipo'"
            assert isinstance(info['tipo'], TipoTribunal)


class TestGetAllTribunais:
    """Testes para get_all_tribunais()."""

    def test_total_correto(self):
        """Valida total de 65 tribunais."""
        todos = get_all_tribunais()
        assert len(todos) == 65

    def test_nao_tem_duplicatas(self):
        """Valida que não há siglas duplicadas."""
        todos = get_all_tribunais()
        siglas = list(todos.keys())
        assert len(siglas) == len(set(siglas))

    def test_todas_categorias_incluidas(self):
        """Valida que todas categorias estão incluídas."""
        todos = get_all_tribunais()

        # Verificar que contém todos os superiores
        for sigla in TRIBUNAIS_SUPERIORES.keys():
            assert sigla in todos

        # Verificar que contém todos os estaduais
        for sigla in TRIBUNAIS_ESTADUAIS.keys():
            assert sigla in todos

        # E assim por diante...
        assert len(todos) == (
            len(TRIBUNAIS_SUPERIORES) +
            len(TRIBUNAIS_ESTADUAIS) +
            len(TRIBUNAIS_FEDERAIS) +
            len(TRIBUNAIS_TRABALHO) +
            len(TRIBUNAIS_MILITARES)
        )


class TestGetTribunaisByType:
    """Testes para get_tribunais_by_type()."""

    def test_filtro_superiores(self):
        """Filtra apenas tribunais superiores."""
        superiores = get_tribunais_by_type(TipoTribunal.SUPERIOR)
        assert len(superiores) == 5
        assert 'STF' in superiores
        assert 'STJ' in superiores

    def test_filtro_estaduais(self):
        """Filtra apenas tribunais estaduais."""
        estaduais = get_tribunais_by_type(TipoTribunal.ESTADUAL)
        assert len(estaduais) == 27
        assert 'TJSP' in estaduais
        assert 'TJRJ' in estaduais

    def test_filtro_federais(self):
        """Filtra apenas tribunais federais."""
        federais = get_tribunais_by_type(TipoTribunal.FEDERAL)
        assert len(federais) == 6
        assert 'TRF1' in federais
        assert 'TRF6' in federais

    def test_filtro_trabalho(self):
        """Filtra apenas tribunais do trabalho."""
        trabalho = get_tribunais_by_type(TipoTribunal.TRABALHO)
        assert len(trabalho) == 24
        assert 'TRT1' in trabalho
        assert 'TRT24' in trabalho

    def test_filtro_militares(self):
        """Filtra apenas tribunais militares."""
        militares = get_tribunais_by_type(TipoTribunal.MILITAR)
        assert len(militares) == 3
        assert 'TJMSP' in militares
        assert 'TJMMG' in militares


class TestGetTribunaisPrioritarios:
    """Testes para get_tribunais_prioritarios()."""

    def test_retorna_lista(self):
        """Retorna uma lista."""
        prioritarios = get_tribunais_prioritarios()
        assert isinstance(prioritarios, list)

    def test_tem_todos_superiores(self):
        """Lista prioritária inclui todos os superiores."""
        prioritarios = get_tribunais_prioritarios()
        for sigla in TRIBUNAIS_SUPERIORES.keys():
            assert sigla in prioritarios

    def test_tem_todos_federais(self):
        """Lista prioritária inclui todos os federais."""
        prioritarios = get_tribunais_prioritarios()
        for sigla in TRIBUNAIS_FEDERAIS.keys():
            assert sigla in prioritarios

    def test_tem_tjsp(self):
        """Lista prioritária inclui TJSP (maior TJ do Brasil)."""
        prioritarios = get_tribunais_prioritarios()
        assert 'TJSP' in prioritarios

    def test_nao_vazio(self):
        """Lista prioritária não é vazia."""
        prioritarios = get_tribunais_prioritarios()
        assert len(prioritarios) > 0

    def test_nao_tem_duplicatas(self):
        """Lista prioritária não tem duplicatas."""
        prioritarios = get_tribunais_prioritarios()
        assert len(prioritarios) == len(set(prioritarios))


class TestGetSiglas:
    """Testes para get_siglas()."""

    def test_retorna_lista_ordenada(self):
        """Retorna lista ordenada de siglas."""
        siglas = get_siglas()
        assert isinstance(siglas, list)
        assert siglas == sorted(siglas)

    def test_total_correto(self):
        """Retorna 65 siglas."""
        siglas = get_siglas()
        assert len(siglas) == 65

    def test_contem_conhecidas(self):
        """Contém siglas conhecidas."""
        siglas = get_siglas()
        assert 'STF' in siglas
        assert 'TJSP' in siglas
        assert 'TRF1' in siglas
        assert 'TRT2' in siglas


class TestGetCount:
    """Testes para get_count()."""

    def test_retorna_65(self):
        """Retorna exatamente 65."""
        assert get_count() == 65


class TestGetStats:
    """Testes para get_stats()."""

    def test_retorna_dict(self):
        """Retorna dicionário de estatísticas."""
        stats = get_stats()
        assert isinstance(stats, dict)

    def test_campos_corretos(self):
        """Contém campos esperados."""
        stats = get_stats()
        assert 'total' in stats
        assert 'superiores' in stats
        assert 'estaduais' in stats
        assert 'federais' in stats
        assert 'trabalho' in stats
        assert 'militares' in stats

    def test_valores_corretos(self):
        """Valores correspondem aos totais reais."""
        stats = get_stats()
        assert stats['total'] == 65
        assert stats['superiores'] == 5
        assert stats['estaduais'] == 27
        assert stats['federais'] == 6
        assert stats['trabalho'] == 24
        assert stats['militares'] == 3

    def test_soma_correta(self):
        """Soma das categorias = total."""
        stats = get_stats()
        soma = (
            stats['superiores'] +
            stats['estaduais'] +
            stats['federais'] +
            stats['trabalho'] +
            stats['militares']
        )
        assert soma == stats['total']


class TestValidateSigla:
    """Testes para validate_sigla()."""

    @pytest.mark.parametrize("sigla", [
        'STF', 'STJ', 'TJSP', 'TJRJ', 'TRF1', 'TRT2', 'TJMSP'
    ])
    def test_siglas_validas(self, sigla):
        """Valida siglas conhecidas."""
        assert validate_sigla(sigla) is True

    @pytest.mark.parametrize("sigla", [
        'INVALIDO', 'TJ99', 'XXX', '123', '', 'TRF7'
    ])
    def test_siglas_invalidas(self, sigla):
        """Rejeita siglas inválidas."""
        assert validate_sigla(sigla) is False

    def test_case_insensitive(self):
        """Valida case-insensitive (aceita minúsculas)."""
        assert validate_sigla('stf') is True
        assert validate_sigla('tjsp') is True
        assert validate_sigla('Tjrj') is True

    def test_sigla_com_espacos(self):
        """Rejeita siglas com espaços."""
        assert validate_sigla('STF ') is False
        assert validate_sigla(' STF') is False


class TestTribunaisIntegrity:
    """Testes de integridade dos dados de tribunais."""

    def test_nao_tem_tribunais_vazios(self):
        """Nenhum tribunal tem nome vazio."""
        todos = get_all_tribunais()
        for sigla, info in todos.items():
            assert info['nome'].strip() != '', f"{sigla} tem nome vazio"

    def test_siglas_maiusculas(self):
        """Todas siglas estão em maiúsculas."""
        todos = get_all_tribunais()
        for sigla in todos.keys():
            assert sigla == sigla.upper(), f"{sigla} não está em maiúsculas"

    def test_nomes_unicos(self):
        """Cada tribunal tem nome único (não repetido)."""
        todos = get_all_tribunais()
        nomes = [info['nome'] for info in todos.values()]
        assert len(nomes) == len(set(nomes))

    def test_tipos_validos(self):
        """Todos tribunais têm tipo válido."""
        todos = get_all_tribunais()
        tipos_validos = {
            TipoTribunal.SUPERIOR,
            TipoTribunal.ESTADUAL,
            TipoTribunal.FEDERAL,
            TipoTribunal.TRABALHO,
            TipoTribunal.MILITAR
        }
        for sigla, info in todos.items():
            assert info['tipo'] in tipos_validos, (
                f"{sigla} tem tipo inválido: {info['tipo']}"
            )

    def test_trts_numerados_corretamente(self):
        """TRTs estão numerados de 1 a 24 (sem pulos)."""
        trabalho = get_tribunais_by_type(TipoTribunal.TRABALHO)

        # Extrair números dos TRTs
        numeros = []
        for sigla in trabalho.keys():
            if sigla.startswith('TRT'):
                num = int(sigla[3:])
                numeros.append(num)

        numeros.sort()

        # Verificar que vai de 1 a 24
        assert numeros == list(range(1, 25))

    def test_trfs_numerados_corretamente(self):
        """TRFs estão numerados de 1 a 6."""
        federais = get_tribunais_by_type(TipoTribunal.FEDERAL)

        numeros = []
        for sigla in federais.keys():
            if sigla.startswith('TRF'):
                num = int(sigla[3:])
                numeros.append(num)

        numeros.sort()
        assert numeros == list(range(1, 7))

    def test_todos_tjs_tem_uf_valida(self):
        """Todos TJs têm UF válida (2 letras)."""
        estaduais = get_tribunais_by_type(TipoTribunal.ESTADUAL)

        for sigla in estaduais.keys():
            if sigla.startswith('TJ'):
                uf = sigla[2:]
                assert len(uf) == 2, f"{sigla} tem UF com tamanho != 2"
                assert uf.isalpha(), f"{sigla} tem UF não alfabética"
