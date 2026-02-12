"""Testes para classificação automática de códigos UTBMS."""

import pytest

from api.task_codes import classify_activity_code, classify_task_code


class TestClassifyTaskCode:
    """Testes para classify_task_code."""

    # --- Task codes em português ---

    def test_recurso_especial(self) -> None:
        assert classify_task_code("Elaboração de recurso especial") == "L510"

    def test_contestacao_trabalhista(self) -> None:
        assert classify_task_code("Contestação trabalhista") == "L210"

    def test_peticao_juntada(self) -> None:
        assert classify_task_code("Petição de juntada de documentos") == "L250"

    def test_negociacao_acordo(self) -> None:
        assert classify_task_code("Negociação de acordo") == "L160"

    def test_agravo_instrumento(self) -> None:
        assert classify_task_code("Agravo de instrumento") == "L510"

    def test_embargos_declaracao(self) -> None:
        assert classify_task_code("Embargos de declaração") == "L510"

    def test_analise_caso_estrategia(self) -> None:
        assert classify_task_code("Análise do caso e estratégia") == "L100"

    def test_apelacao(self) -> None:
        assert classify_task_code("Apelação cível") == "L510"

    def test_mediacao(self) -> None:
        assert classify_task_code("Mediação judicial") == "L160"

    def test_investigacao(self) -> None:
        assert classify_task_code("Investigação de fatos relevantes") == "L120"

    def test_diligencia(self) -> None:
        assert classify_task_code("Diligência no fórum") == "L120"

    def test_testemunha(self) -> None:
        assert classify_task_code("Preparação de testemunha") == "L310"

    def test_audiencia(self) -> None:
        assert classify_task_code("Audiência de instrução") == "L310"

    def test_parecer(self) -> None:
        assert classify_task_code("Parecer jurídico sobre o mérito") == "L100"

    def test_defesa(self) -> None:
        assert classify_task_code("Defesa administrativa") == "L210"

    # --- Task codes em inglês ---

    def test_draft_special_appeal(self) -> None:
        assert classify_task_code("Draft and file a Special Appeal") == "L510"

    def test_prepare_defense_response(self) -> None:
        assert classify_task_code("Prepare defense response") == "L210"

    def test_settlement_conference(self) -> None:
        assert classify_task_code("Settlement conference preparation") == "L160"

    def test_file_motion(self) -> None:
        assert classify_task_code("File motion for summary judgment") == "L250"

    def test_case_assessment(self) -> None:
        assert classify_task_code("Case assessment and strategy") == "L100"

    def test_fact_finding(self) -> None:
        assert classify_task_code("Fact finding and evidence collection") == "L120"

    def test_witness_deposition(self) -> None:
        assert classify_task_code("Witness deposition preparation") == "L310"

    def test_discovery_process(self) -> None:
        assert classify_task_code("Discovery process management") == "L120"

    # --- Edge cases ---

    def test_string_vazia(self) -> None:
        assert classify_task_code("") == ""

    def test_sem_match(self) -> None:
        assert classify_task_code("Pagamento de custas processuais") == ""

    def test_peticao_sem_cedilha(self) -> None:
        """Patterns com [cç] devem aceitar 'peticao' sem cedilha."""
        assert classify_task_code("peticao inicial") == "L250"

    def test_contestacao_sem_acentos(self) -> None:
        """Patterns com [aã] e [cç] devem aceitar sem acentuação."""
        assert classify_task_code("contestacao trabalhista") == "L210"

    def test_negociacao_sem_acentos(self) -> None:
        assert classify_task_code("negociacao extrajudicial") == "L160"

    def test_case_insensitive(self) -> None:
        assert classify_task_code("RECURSO EXTRAORDINÁRIO") == "L510"
        assert classify_task_code("SETTLEMENT AGREEMENT") == "L160"

    def test_descricao_longa(self) -> None:
        desc = "Elaboração e revisão de recurso especial com análise detalhada"
        assert classify_task_code(desc) == "L510"

    def test_none_like_empty(self) -> None:
        """String vazia retorna vazio."""
        assert classify_task_code("") == ""


class TestClassifyActivityCode:
    """Testes para classify_activity_code."""

    # --- Activity codes em português ---

    def test_elaboracao_peticao(self) -> None:
        assert classify_activity_code("Elaboração de petição") == "A103"

    def test_reuniao_cliente(self) -> None:
        assert classify_activity_code("Reunião com cliente") == "A106"

    def test_pesquisa_jurisprudencial(self) -> None:
        assert classify_activity_code("Pesquisa jurisprudencial") == "A102"

    def test_analise_documentos(self) -> None:
        assert classify_activity_code("Análise de documentos") == "A104"

    def test_redacao_minuta(self) -> None:
        assert classify_activity_code("Redação de minuta contratual") == "A103"

    def test_correspondencia(self) -> None:
        assert classify_activity_code("Correspondência com a parte contrária") == "A106"

    def test_viagem_forum(self) -> None:
        assert classify_activity_code("Viagem ao fórum de São Paulo") == "A107"

    def test_deslocamento(self) -> None:
        assert classify_activity_code("Deslocamento até o tribunal") == "A107"

    def test_organizacao_estrategia(self) -> None:
        assert classify_activity_code("Organização de estratégia processual") == "A101"

    def test_doutrina(self) -> None:
        assert classify_activity_code("Consulta à doutrina especializada") == "A102"

    def test_exame_provas(self) -> None:
        assert classify_activity_code("Exame detalhado das provas") == "A104"

    # --- Activity codes em inglês ---

    def test_draft_appeal_brief(self) -> None:
        assert classify_activity_code("Draft appeal brief") == "A103"

    def test_email_opposing_counsel(self) -> None:
        assert classify_activity_code("Email exchange with opposing counsel") == "A106"

    def test_research_case_law(self) -> None:
        assert classify_activity_code("Research case law precedents") == "A102"

    def test_review_contract(self) -> None:
        assert classify_activity_code("Review contract terms") == "A104"

    def test_plan_litigation_strategy(self) -> None:
        assert classify_activity_code("Plan litigation strategy") == "A101"

    def test_travel_courthouse(self) -> None:
        assert classify_activity_code("Travel to courthouse") == "A107"

    def test_meeting_client(self) -> None:
        assert classify_activity_code("Meeting with client to discuss case") == "A106"

    # --- Edge cases ---

    def test_string_vazia(self) -> None:
        assert classify_activity_code("") == ""

    def test_sem_match(self) -> None:
        assert classify_activity_code("Pagamento de custas") == ""

    def test_case_insensitive(self) -> None:
        assert classify_activity_code("DRAFT MOTION") == "A103"
        assert classify_activity_code("RESEARCH PRECEDENTS") == "A102"

    def test_reuniao_sem_acento(self) -> None:
        """Pattern [aã] aceita 'reuniao' sem til."""
        assert classify_activity_code("reuniao com advogado") == "A106"

    def test_redacao_sem_cedilha(self) -> None:
        """Pattern [cç] aceita 'redacao' sem cedilha."""
        assert classify_activity_code("redacao de parecer") == "A103"

    def test_preparacao_como_draft(self) -> None:
        """'prepar' faz match em A103 (Draft/Revise)."""
        assert classify_activity_code("Preparação de documentos") == "A103"

    def test_email_com_hifen(self) -> None:
        """Pattern e-?mail aceita com e sem hífen."""
        assert classify_activity_code("Envio de e-mail ao cliente") == "A106"
        assert classify_activity_code("Envio de email ao cliente") == "A106"


class TestPriorityOrder:
    """Testes para verificar que a ordem de prioridade dos patterns está correta."""

    def test_task_appeal_before_motion(self) -> None:
        """'Appeal' (L510) deve ter prioridade sobre patterns genéricos."""
        assert classify_task_code("Appeal motion filed") == "L510"

    def test_activity_draft_before_plan(self) -> None:
        """'Draft' (A103) deve ter prioridade sobre 'Plan' (A101)."""
        assert classify_activity_code("Draft a plan") == "A103"
