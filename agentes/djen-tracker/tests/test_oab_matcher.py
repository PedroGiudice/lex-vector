"""
Testes para módulo oab_matcher.py - Detecção robusta de números OAB.

CRÍTICO: Este módulo é o coração do sistema de filtro.
Testa 13+ padrões regex, scoring contextual, normalização e deduplicação.

Valida:
- Todos os 13+ padrões regex
- Scoring baseado em contexto
- Normalização de números e UFs
- Validação de OABs
- Deduplicação
- Edge cases e falsos positivos
"""

import pytest
from src.oab_matcher import OABMatcher, OABMatch


class TestOABMatcherPatterns:
    """Testes para padrões regex de detecção."""

    def test_padrao_oab_slash_uf_numero(self):
        """Padrão: OAB/SP 123.456"""
        matcher = OABMatcher()
        text = "Advogado: Dr. João Silva - OAB/SP 123.456"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    def test_padrao_oab_slash_uf_numero_sem_ponto(self):
        """Padrão: OAB/SP 123456 (sem pontuação)"""
        matcher = OABMatcher()
        text = "Advogado com OAB/SP 123456 válida"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    def test_padrao_numero_slash_uf(self):
        """Padrão: 123.456/SP"""
        matcher = OABMatcher()
        text = "Inscrito sob número 123.456/SP no quadro"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    def test_padrao_numero_hifen_uf(self):
        """Padrão: 123456-SP"""
        matcher = OABMatcher()
        text = "Patrono: Maria Santos (123456-SP)"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    def test_padrao_parenteses_oab(self):
        """Padrão: (OAB 123456/SP)"""
        matcher = OABMatcher()
        text = "Advogado: João Silva (OAB 123456/SP)"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    def test_padrao_advogado_oab(self):
        """Padrão: Advogado(a): OAB/SP 123456"""
        matcher = OABMatcher()
        text = "Advogada: OAB/SP 123456"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    def test_padrao_dr_nome_oab(self):
        """Padrão: Dr. Nome - OAB/SP nº 123.456"""
        matcher = OABMatcher()
        text = "Dr. Carlos Ferreira - OAB/SP nº 123.456"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    def test_padrao_inscricao_oab(self):
        """Padrão: Inscrição OAB/SP sob o nº 123.456"""
        matcher = OABMatcher()
        text = "Inscrição OAB/SP sob o nº 123.456"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    def test_padrao_procurador(self):
        """Padrão: Procurador: OAB 123456 - SP"""
        matcher = OABMatcher()
        text = "Procurador: OAB 123456 - SP"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    def test_padrao_defensor(self):
        """Padrão: Defensor: 123456/SP"""
        matcher = OABMatcher()
        text = "Defensor Público: 123456/SP"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(m.numero == '123456' and m.uf == 'SP' for m in matches)

    @pytest.mark.parametrize("text,expected_numero,expected_uf", [
        ("OAB/SP 123.456", "123456", "SP"),
        ("OAB/RJ 789012", "789012", "RJ"),
        ("123456/MG", "123456", "MG"),
        ("456789-BA", "456789", "BA"),
        ("(OAB 111222/CE)", "111222", "CE"),
        ("OAB-GO: 333444", "333444", "GO"),
        ("Registro OAB nº 555666 (PR)", "555666", "PR"),
    ])
    def test_multiplos_formatos(self, text, expected_numero, expected_uf):
        """Testa múltiplos formatos de OAB."""
        matcher = OABMatcher()
        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) >= 1
        assert any(
            m.numero == expected_numero and m.uf == expected_uf
            for m in matches
        ), f"Não encontrou {expected_numero}/{expected_uf} em '{text}'"


class TestOABMatcherValidation:
    """Testes para validação de OABs."""

    def test_valida_oab_correta(self):
        """Valida OAB com formato correto."""
        matcher = OABMatcher()
        assert matcher.validate_oab('123456', 'SP') is True

    def test_rejeita_uf_invalida(self):
        """Rejeita UF inválida."""
        matcher = OABMatcher()
        assert matcher.validate_oab('123456', 'XX') is False
        assert matcher.validate_oab('123456', '99') is False

    def test_rejeita_numero_muito_curto(self):
        """Rejeita número com menos de 4 dígitos."""
        matcher = OABMatcher()
        assert matcher.validate_oab('123', 'SP') is False

    def test_rejeita_numero_muito_longo(self):
        """Rejeita número com mais de 6 dígitos."""
        matcher = OABMatcher()
        assert matcher.validate_oab('1234567', 'SP') is False

    def test_rejeita_numero_nao_numerico(self):
        """Rejeita número não numérico."""
        matcher = OABMatcher()
        assert matcher.validate_oab('ABC123', 'SP') is False

    def test_rejeita_numero_repetido(self):
        """Rejeita número com todos dígitos iguais (111111)."""
        matcher = OABMatcher()
        assert matcher.validate_oab('111111', 'SP') is False
        assert matcher.validate_oab('000000', 'SP') is False

    @pytest.mark.parametrize("uf", [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    ])
    def test_aceita_todas_ufs_brasileiras(self, uf):
        """Aceita todas UFs brasileiras válidas."""
        matcher = OABMatcher()
        assert matcher.validate_oab('123456', uf) is True


class TestOABMatcherNormalization:
    """Testes para normalização de OABs."""

    def test_normaliza_numero_com_pontos(self):
        """Remove pontos do número."""
        matcher = OABMatcher()
        numero, uf = matcher.normalize_oab('123.456', 'SP')
        assert numero == '123456'

    def test_normaliza_numero_com_tracos(self):
        """Remove traços do número."""
        matcher = OABMatcher()
        numero, uf = matcher.normalize_oab('123-456', 'SP')
        assert numero == '123456'

    def test_normaliza_uf_minuscula(self):
        """Converte UF para maiúsculas."""
        matcher = OABMatcher()
        numero, uf = matcher.normalize_oab('123456', 'sp')
        assert uf == 'SP'

    def test_normaliza_uf_com_espacos(self):
        """Remove espaços da UF."""
        matcher = OABMatcher()
        numero, uf = matcher.normalize_oab('123456', ' SP ')
        assert uf == 'SP'

    @pytest.mark.parametrize("input_num,expected", [
        ('123.456', '123456'),
        ('123-456', '123456'),
        ('123 456', '123456'),
        ('12.34.56', '123456'),
    ])
    def test_normaliza_variacoes_numero(self, input_num, expected):
        """Normaliza variações de formatação de número."""
        matcher = OABMatcher()
        numero, _ = matcher.normalize_oab(input_num, 'SP')
        assert numero == expected


class TestOABMatcherContextScoring:
    """Testes para scoring baseado em contexto."""

    def test_score_alto_com_palavras_positivas(self):
        """Score alto quando contexto tem palavras positivas."""
        matcher = OABMatcher()
        text = "Advogado Dr. João Silva com OAB/SP 123456 intimado"

        matches = matcher.find_all(text, min_score=0.0)

        assert len(matches) > 0
        # Deve ter score alto (> 0.5) pois tem "advogado", "dr", "intimado"
        assert matches[0].score_contexto > 0.5

    def test_score_baixo_com_palavras_negativas(self):
        """Score mais baixo quando contexto tem palavras negativas."""
        matcher = OABMatcher()
        text = "Processo CPF telefone 123456/SP CNPJ"

        matches = matcher.find_all(text, min_score=0.0)

        # Pode ou não detectar (depende de outras heurísticas)
        # Mas se detectar, score deve ser menor
        if matches:
            # Score deve ser relativamente baixo
            assert matches[0].score_contexto < 0.8

    def test_score_aumenta_com_nome_proprio(self):
        """Score aumenta quando há nome próprio no contexto."""
        matcher = OABMatcher()
        text1 = "OAB/SP 123456"  # Sem nome
        text2 = "Dr. João Silva OAB/SP 123456"  # Com nome

        matches1 = matcher.find_all(text1, min_score=0.0)
        matches2 = matcher.find_all(text2, min_score=0.0)

        if matches1 and matches2:
            # Score de text2 deve ser maior
            assert matches2[0].score_contexto > matches1[0].score_contexto


class TestOABMatcherDeduplication:
    """Testes para deduplicação de matches."""

    def test_deduplica_mesmo_oab_multiplas_vezes(self):
        """Deduplica quando mesma OAB aparece múltiplas vezes."""
        matcher = OABMatcher()
        text = """
        Advogado OAB/SP 123456 representa...
        O mesmo advogado (OAB 123456/SP) também...
        Conforme OAB/SP nº 123.456 já mencionado...
        """

        matches = matcher.find_all(text, min_score=0.0, deduplicate=True)

        # Deve retornar apenas 1 match (dedupli cado)
        oab_sp_123456 = [m for m in matches if m.numero == '123456' and m.uf == 'SP']
        assert len(oab_sp_123456) == 1

    def test_nao_deduplica_quando_desabilitado(self):
        """Não deduplica quando deduplicate=False."""
        matcher = OABMatcher()
        text = """
        OAB/SP 123456
        OAB/SP 123456
        OAB/SP 123456
        """

        matches = matcher.find_all(text, min_score=0.0, deduplicate=False)

        # Deve retornar 3 matches (não deduplicados)
        assert len(matches) >= 3

    def test_mantem_match_com_maior_score_apos_deduplicacao(self):
        """Mantém match com maior score após deduplicação."""
        matcher = OABMatcher()
        text = """
        Processo 123456/SP número protocolo
        Advogado Dr. João Silva OAB/SP 123456 intimado
        """

        matches = matcher.find_all(text, min_score=0.0, deduplicate=True)

        # Deve manter apenas 1, e deve ser o com melhor contexto
        oab_matches = [m for m in matches if m.numero == '123456' and m.uf == 'SP']
        if len(oab_matches) == 1:
            # Deve ter "advogado" ou "dr" no contexto (maior score)
            assert 'advogado' in oab_matches[0].texto_contexto.lower() or \
                   'dr' in oab_matches[0].texto_contexto.lower()


class TestOABMatcherFalsePositives:
    """Testes para evitar falsos positivos."""

    def test_nao_detecta_numero_processo(self):
        """Não detecta número de processo como OAB."""
        matcher = OABMatcher()
        text = "Processo nº 1234567-89.2025.8.26.0100"

        matches = matcher.find_all(text, min_score=0.4)

        # Não deve detectar número de processo
        assert len(matches) == 0

    def test_nao_detecta_cpf(self):
        """Não detecta CPF como OAB."""
        matcher = OABMatcher()
        text = "CPF: 123.456.789-01"

        matches = matcher.find_all(text, min_score=0.4)

        # Não deve detectar CPF
        assert len(matches) == 0

    def test_nao_detecta_telefone(self):
        """Não detecta telefone como OAB."""
        matcher = OABMatcher()
        text = "Telefone: (11) 98765-4321"

        matches = matcher.find_all(text, min_score=0.4)

        # Não deve detectar telefone
        assert len(matches) == 0

    def test_nao_detecta_cnpj(self):
        """Não detecta CNPJ como OAB."""
        matcher = OABMatcher()
        text = "CNPJ: 12.345.678/0001-90"

        matches = matcher.find_all(text, min_score=0.4)

        # Não deve detectar CNPJ
        assert len(matches) == 0

    def test_nao_detecta_numeros_soltos(self):
        """Não detecta números soltos sem contexto."""
        matcher = OABMatcher()
        text = "123456 789012 111222"

        matches = matcher.find_all(text, min_score=0.4)

        # Não deve detectar números sem contexto
        assert len(matches) == 0


class TestOABMatcherFilterByOabs:
    """Testes para filter_by_oabs (busca OABs específicas)."""

    def test_filtra_oabs_especificas(self, sample_text_with_oabs):
        """Filtra apenas OABs da lista fornecida."""
        matcher = OABMatcher()

        target_oabs = [
            ('123456', 'SP'),
            ('789012', 'SP'),
        ]

        matches = matcher.filter_by_oabs(
            sample_text_with_oabs,
            target_oabs,
            min_score=0.0
        )

        # Deve encontrar apenas as 2 OABs solicitadas
        assert len(matches) == 2

        numeros_encontrados = {(m.numero, m.uf) for m in matches}
        assert ('123456', 'SP') in numeros_encontrados
        assert ('789012', 'SP') in numeros_encontrados

    def test_nao_retorna_oabs_nao_solicitadas(self, sample_text_with_oabs):
        """Não retorna OABs que não foram solicitadas."""
        matcher = OABMatcher()

        target_oabs = [
            ('123456', 'SP'),  # Esta existe no texto
        ]

        matches = matcher.filter_by_oabs(
            sample_text_with_oabs,
            target_oabs,
            min_score=0.0
        )

        # Deve retornar apenas 1
        assert len(matches) == 1
        assert matches[0].numero == '123456'
        assert matches[0].uf == 'SP'

    def test_retorna_vazio_se_oab_nao_existe(self):
        """Retorna lista vazia se OAB não existe no texto."""
        matcher = OABMatcher()
        text = "Texto sem OABs relevantes"

        target_oabs = [
            ('999999', 'ZZ'),  # Não existe
        ]

        matches = matcher.filter_by_oabs(text, target_oabs, min_score=0.0)

        assert len(matches) == 0


class TestOABMatcherCompleteWorkflow:
    """Testes de workflow completo."""

    def test_workflow_completo(self, sample_text_with_oabs):
        """Testa workflow completo de detecção."""
        matcher = OABMatcher()

        # 1. Encontrar todas OABs
        all_matches = matcher.find_all(
            sample_text_with_oabs,
            min_score=0.3,
            deduplicate=True
        )

        # Deve encontrar várias OABs
        assert len(all_matches) > 0

        # 2. Verificar que cada match tem campos necessários
        for match in all_matches:
            assert isinstance(match, OABMatch)
            assert match.numero.isdigit()
            assert len(match.numero) >= 4
            assert match.uf in matcher.UFS_VALIDAS
            assert 0.0 <= match.score_contexto <= 1.0
            assert len(match.texto_contexto) > 0
            assert match.posicao_inicio < match.posicao_fim

        # 3. Ordenação por score (primeiro deve ter maior score)
        if len(all_matches) > 1:
            assert all_matches[0].score_contexto >= all_matches[1].score_contexto

    def test_texto_real_exemplo(self):
        """Testa com texto real de publicação judicial."""
        matcher = OABMatcher()

        texto_real = """
        TRIBUNAL DE JUSTIÇA DO ESTADO DE SÃO PAULO

        Processo nº 1234567-89.2025.8.26.0100
        Comarca de São Paulo

        DECISÃO

        Vistos.

        Intime-se o advogado Dr. João da Silva, inscrito na OAB/SP sob
        o nº 123.456, para manifestar-se no prazo de 15 dias.

        Advogado da parte autora: Dra. Maria Santos (OAB 789012/SP)
        Advogado da parte ré: Dr. Carlos Ferreira - OAB/RJ 345678

        São Paulo, 17 de novembro de 2025.
        """

        matches = matcher.find_all(texto_real, min_score=0.3)

        # Deve encontrar 3 OABs
        assert len(matches) == 3

        # Verificar OABs encontradas
        oabs_encontradas = {(m.numero, m.uf) for m in matches}
        assert ('123456', 'SP') in oabs_encontradas
        assert ('789012', 'SP') in oabs_encontradas
        assert ('345678', 'RJ') in oabs_encontradas

    def test_performance_texto_grande(self):
        """Testa performance com texto grande."""
        import time

        matcher = OABMatcher()

        # Criar texto grande (10.000 linhas)
        texto_grande = "\n".join([
            f"Linha {i} com OAB/SP {123456 + i} mencionada"
            for i in range(10000)
        ])

        start = time.time()
        matches = matcher.find_all(texto_grande, min_score=0.3)
        duration = time.time() - start

        # Deve processar em menos de 5 segundos
        assert duration < 5.0

        # Deve encontrar muitas OABs (deduplicadas)
        assert len(matches) > 0


class TestOABMatcherEdgeCases:
    """Testes de edge cases."""

    def test_texto_vazio(self):
        """Lida com texto vazio."""
        matcher = OABMatcher()
        matches = matcher.find_all("", min_score=0.0)
        assert len(matches) == 0

    def test_texto_muito_curto(self):
        """Lida com texto muito curto."""
        matcher = OABMatcher()
        matches = matcher.find_all("OAB", min_score=0.0)
        assert len(matches) == 0

    def test_oab_na_borda_do_texto(self):
        """Detecta OAB no início e fim do texto."""
        matcher = OABMatcher()

        # OAB no início
        text1 = "OAB/SP 123456 é o início"
        matches1 = matcher.find_all(text1, min_score=0.0)
        assert len(matches1) >= 1

        # OAB no fim
        text2 = "O fim é OAB/SP 123456"
        matches2 = matcher.find_all(text2, min_score=0.0)
        assert len(matches2) >= 1

    def test_multiplas_oabs_mesma_linha(self):
        """Detecta múltiplas OABs na mesma linha."""
        matcher = OABMatcher()
        text = "Advogados: OAB/SP 123456, OAB/RJ 789012, OAB/MG 345678"

        matches = matcher.find_all(text, min_score=0.0, deduplicate=False)

        # Deve encontrar todas 3
        assert len(matches) >= 3
