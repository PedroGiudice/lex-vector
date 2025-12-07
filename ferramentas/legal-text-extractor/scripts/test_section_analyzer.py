#!/usr/bin/env python3
"""
Script de teste para SectionAnalyzer - Milestone 1.5

Testa a implementação completa do analisador de seções com documento exemplo.
"""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analyzers.section_analyzer import SectionAnalyzer, Section

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Documento de teste (baseado no example 1 do prompt)
SAMPLE_DOCUMENT = """
EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 1ª VARA CÍVEL

JOSÉ DA SILVA, brasileiro, casado, comerciante, inscrito no CPF sob nº 123.456.789-00, residente e domiciliado na Rua das Flores, 100, São Paulo/SP, por seu advogado que esta subscreve (procuração anexa), vem, respeitosamente, à presença de Vossa Excelência, propor

AÇÃO DE COBRANÇA

em face de EMPRESA XYZ LTDA, pessoa jurídica de direito privado, inscrita no CNPJ sob nº 12.345.678/0001-90, com sede na Avenida Paulista, 500, São Paulo/SP, pelos fatos e fundamentos jurídicos a seguir expostos:

I - DOS FATOS

Em janeiro de 2024, o Autor prestou serviços de consultoria empresarial à Ré, conforme contrato anexo (doc. 1), pelo valor total de R$ 50.000,00 (cinquenta mil reais).

Os serviços foram prestados integralmente no período de janeiro a março de 2024, conforme atestado pela própria Ré em email datado de 31/03/2024 (doc. 2).

Contudo, apesar de notificada extrajudicialmente em 15/04/2024 (doc. 3), a Ré permanece inadimplente até a presente data.

II - DO DIREITO

O inadimplemento contratual está configurado nos termos do art. 389 do Código Civil, que estabelece o dever de reparar as perdas e danos decorrentes da inexecução da obrigação.

Ademais, o art. 395 do mesmo diploma legal prevê a mora do devedor que não efetua o pagamento no tempo devido.

III - DO PEDIDO

Diante do exposto, requer:

a) A citação da Ré para, querendo, contestar a presente ação, sob pena de revelia;

b) A procedência do pedido para condenar a Ré ao pagamento de R$ 50.000,00 (cinquenta mil reais), corrigidos monetariamente desde o vencimento e acrescidos de juros de mora de 1% ao mês;

c) A condenação da Ré ao pagamento das custas processuais e honorários advocatícios, que se estima em 20% do valor da condenação.

Atribui à causa o valor de R$ 50.000,00.

Nestes termos, pede deferimento.

São Paulo, 15 de janeiro de 2025.

___________________________
Dr. João Advogado
OAB/SP 123.456

---

PROCURAÇÃO

OUTORGANTE: JOSÉ DA SILVA, brasileiro, casado, comerciante, inscrito no CPF sob nº 123.456.789-00, residente e domiciliado na Rua das Flores, 100, São Paulo/SP.

OUTORGADO: Dr. João Advogado, inscrito na OAB/SP sob nº 123.456, com escritório na Rua dos Advogados, 200, São Paulo/SP.

PODERES: O outorgante confere ao outorgado poderes para representá-lo em juízo ou fora dele, com todas as cláusulas "ad judicia", podendo propor ações, contestar, reconvir, desistir, transigir, fazer acordos, receber e dar quitação, requerer medidas de urgência, substabelecer com ou sem reservas de poderes, enfim, praticar todos os atos necessários ao bom e fiel desempenho do mandato.

São Paulo, 10 de janeiro de 2025.

___________________________
José da Silva
Outorgante
""".strip()


def test_section_analyzer():
    """Testa SectionAnalyzer com documento exemplo"""

    logger.info("=" * 70)
    logger.info("TESTE: SectionAnalyzer - Milestone 1.5")
    logger.info("=" * 70)

    try:
        # 1. Inicializar analisador
        logger.info("\n[1/4] Inicializando SectionAnalyzer...")
        analyzer = SectionAnalyzer()
        logger.info("✓ SectionAnalyzer inicializado com sucesso")

        # 2. Analisar documento
        logger.info("\n[2/4] Analisando documento de teste...")
        logger.info(f"Tamanho do documento: {len(SAMPLE_DOCUMENT)} chars")

        sections = analyzer.analyze(SAMPLE_DOCUMENT)

        logger.info(f"✓ Análise concluída: {len(sections)} seções identificadas")

        # 3. Exibir resultados
        logger.info("\n[3/4] Resultados da análise:")
        logger.info("-" * 70)

        for i, section in enumerate(sections, 1):
            logger.info(f"\nSeção {i}:")
            logger.info(f"  Tipo: {section.type}")
            logger.info(f"  Posição: {section.start_pos} - {section.end_pos}")
            logger.info(f"  Tamanho: {len(section.content)} chars")
            logger.info(f"  Confiança: {section.confidence:.2f}")
            logger.info(f"  Preview: {section.content[:100]}...")

        # 4. Validações básicas
        logger.info("\n[4/4] Validações:")

        # Deve ter identificado ao menos 2 seções (petição + procuração)
        assert len(sections) >= 2, f"Esperado >= 2 seções, obtido {len(sections)}"
        logger.info("✓ Número de seções validado (>= 2)")

        # Seções devem estar ordenadas
        for i in range(len(sections) - 1):
            assert sections[i].start_pos < sections[i + 1].start_pos, \
                "Seções não estão ordenadas por posição"
        logger.info("✓ Seções ordenadas corretamente")

        # Confidence deve estar entre 0 e 1
        for section in sections:
            assert 0.0 <= section.confidence <= 1.0, \
                f"Confidence fora do range: {section.confidence}"
        logger.info("✓ Confidence scores válidos")

        # Tipos devem ser válidos
        valid_types = {
            "petição_inicial", "contestação", "réplica", "sentença", "acórdão",
            "despacho", "decisão_interlocutória", "parecer_mp", "laudo_pericial",
            "ata_audiência", "procuração", "substabelecimento", "contrato",
            "documento_fiscal", "correspondência", "outro"
        }

        for section in sections:
            assert section.type in valid_types, \
                f"Tipo inválido: {section.type}"
        logger.info("✓ Tipos de seção válidos")

        logger.info("\n" + "=" * 70)
        logger.info("TESTE CONCLUÍDO COM SUCESSO! ✓")
        logger.info("=" * 70)

        return True

    except Exception as e:
        logger.error("\n" + "=" * 70)
        logger.error(f"TESTE FALHOU: {e}")
        logger.error("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_section_analyzer()
    sys.exit(0 if success else 1)
