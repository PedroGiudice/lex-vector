#!/usr/bin/env python3
"""
Gerador de PDFs sintéticos para testes da pipeline de extração.

Gera um PDF de teste com 3 páginas:
- Página 1: Texto normal (NATIVE) - fim de petição
- Página 2: Imagem de texto (RASTER_NEEDED) - contrato escaneado
- Página 3: Texto com tarja lateral (TARJA_DETECTED) - documento com assinatura digital

Uso:
    cd ferramentas/legal-text-extractor
    source .venv/bin/activate
    python scripts/generate_fixtures.py

Dependências:
    - reportlab>=4.0.0
    - Pillow>=10.0.0
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, lightgrey
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
import io


def create_page_1_text(c: canvas.Canvas):
    """
    Página 1: Texto normal extraível (NATIVE).

    Simula o fim de uma petição inicial com texto estruturado.
    """
    width, height = A4

    # Título
    c.setFont("Helvetica-Bold", 14)
    c.drawString(3*cm, height - 3*cm, "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 1ª VARA CÍVEL")

    # Texto da petição
    c.setFont("Helvetica", 11)
    y = height - 5*cm

    texto_peticao = [
        "JOSÉ DA SILVA, brasileiro, casado, advogado, inscrito na OAB/SP sob o nº 123.456,",
        "com escritório na Rua das Flores, nº 100, São Paulo/SP, vem, respeitosamente,",
        "à presença de Vossa Excelência, por seu advogado infra-assinado, propor a presente",
        "",
        "AÇÃO DE COBRANÇA",
        "",
        "em face de MARIA OLIVEIRA, brasileira, empresária, residente e domiciliada na",
        "Avenida Paulista, nº 500, São Paulo/SP, pelos fatos e fundamentos a seguir expostos:",
        "",
        "I - DOS FATOS",
        "",
        "O autor celebrou contrato de prestação de serviços com a ré em 15/01/2025,",
        "conforme documento em anexo, no valor total de R$ 50.000,00 (cinquenta mil reais).",
        "",
        "Os serviços foram devidamente prestados conforme acordado, porém a ré deixou de",
        "efetuar o pagamento na data aprazada (30/03/2025), permanecendo inadimplente até",
        "a presente data.",
        "",
        "II - DO DIREITO",
        "",
        "O Código Civil, em seu artigo 389, estabelece que não cumprida a obrigação,",
        "responde o devedor por perdas e danos, mais juros e atualização monetária.",
        "",
        "Diante do inadimplemento, é devida a cobrança do valor principal acrescido de",
        "juros moratórios de 1% ao mês e correção monetária pelo IPCA.",
        "",
        "III - DO PEDIDO",
        "",
        "Diante do exposto, requer:",
        "",
        "a) A citação da ré para contestar a presente ação, sob pena de revelia;",
        "b) A procedência do pedido para condenar a ré ao pagamento de R$ 50.000,00,",
        "   acrescido de juros e correção monetária;",
        "c) A condenação da ré ao pagamento das custas processuais e honorários advocatícios.",
        "",
        "Nestes termos,",
        "Pede deferimento.",
        "",
        "São Paulo, 24 de novembro de 2025.",
        "",
        "",
        "_________________________________",
        "Dr. José da Silva",
        "OAB/SP 123.456"
    ]

    for linha in texto_peticao:
        if linha.startswith("AÇÃO DE COBRANÇA"):
            c.setFont("Helvetica-Bold", 12)
            c.drawCentredString(width/2, y, linha)
            c.setFont("Helvetica", 11)
        elif linha.startswith("I -") or linha.startswith("II -") or linha.startswith("III -"):
            c.setFont("Helvetica-Bold", 11)
            c.drawString(3*cm, y, linha)
            c.setFont("Helvetica", 11)
        else:
            c.drawString(3*cm, y, linha)
        y -= 0.5*cm


def create_page_2_image(c: canvas.Canvas):
    """
    Página 2: Imagem de texto (RASTER_NEEDED).

    Simula uma página escaneada convertendo texto em imagem.
    Não será possível selecionar o texto (embedded image).
    """
    width, height = A4

    # Criar imagem com texto renderizado
    img_width = int(width * 2)  # 2x resolution para qualidade
    img_height = int(height * 2)

    img = Image.new('RGB', (img_width, img_height), color='white')
    draw = ImageDraw.Draw(img)

    # Tentar usar fonte do sistema, fallback para default
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()

    # Título
    y_pos = 150
    draw.text((200, y_pos), "CONTRATO DE PRESTAÇÃO DE SERVIÇOS", fill='black', font=font_title)

    # Texto do contrato (como imagem - não selecionável)
    y_pos = 300
    texto_contrato = [
        "Pelo presente instrumento particular de contrato de prestação de serviços,",
        "que entre si celebram, de um lado:",
        "",
        "CONTRATANTE: MARIA OLIVEIRA",
        "Brasileira, empresária, portadora do CPF nº 987.654.321-00",
        "Residente na Avenida Paulista, nº 500, São Paulo/SP",
        "",
        "CONTRATADO: JOSÉ DA SILVA",
        "Brasileiro, advogado, portador do CPF nº 123.456.789-00",
        "OAB/SP nº 123.456",
        "",
        "CLÁUSULA PRIMEIRA - DO OBJETO",
        "",
        "O contratado se obriga a prestar serviços de consultoria jurídica empresarial,",
        "incluindo análise de contratos, assessoria em questões trabalhistas e civis,",
        "pelo período de 6 (seis) meses.",
        "",
        "CLÁUSULA SEGUNDA - DO VALOR",
        "",
        "Pela prestação dos serviços, a contratante pagará o valor total de",
        "R$ 50.000,00 (cinquenta mil reais), em parcela única, até 30/03/2025.",
        "",
        "CLÁUSULA TERCEIRA - DAS OBRIGAÇÕES",
        "",
        "São obrigações do contratado:",
        "a) Prestar os serviços com qualidade e pontualidade;",
        "b) Manter sigilo sobre informações confidenciais;",
        "c) Fornecer relatórios mensais das atividades realizadas.",
        "",
        "CLÁUSULA QUARTA - DA RESCISÃO",
        "",
        "O presente contrato poderá ser rescindido por qualquer das partes mediante",
        "aviso prévio de 30 (trinta) dias.",
        "",
        "E por estarem justos e contratados, assinam o presente em 2 (duas) vias.",
        "",
        "São Paulo, 15 de janeiro de 2025.",
    ]

    line_height = 50
    for linha in texto_contrato:
        if "CLÁUSULA" in linha:
            draw.text((150, y_pos), linha, fill='black', font=font_title)
        else:
            draw.text((150, y_pos), linha, fill='black', font=font_text)
        y_pos += line_height

    # Salvar imagem em buffer e inserir no PDF
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    # Usar ImageReader para ler o buffer
    img_reader = ImageReader(img_buffer)

    # Inserir imagem no PDF (ocupando toda a página)
    c.drawImage(img_reader, 0, 0, width=width, height=height)


def create_page_3_with_tarja(c: canvas.Canvas):
    """
    Página 3: Texto com tarja lateral direita (TARJA_DETECTED).

    Simula documento com assinatura digital do PJe/e-SAJ.
    Tarja ocupa os últimos 20% da largura da página.
    """
    width, height = A4
    tarja_width = width * 0.20  # 20% da largura
    tarja_x = width - tarja_width  # Posição X do início da tarja

    # ÁREA PRINCIPAL (80% esquerda) - Texto do documento
    c.setFont("Helvetica-Bold", 14)
    c.drawString(3*cm, height - 3*cm, "CONTRATO SOCIAL")

    c.setFont("Helvetica", 11)
    y = height - 5*cm

    texto_documento = [
        "Pelo presente instrumento particular de contrato social, os sócios abaixo",
        "qualificados resolvem constituir uma sociedade limitada, mediante as seguintes",
        "cláusulas e condições:",
        "",
        "CLÁUSULA PRIMEIRA - DA DENOMINAÇÃO E SEDE",
        "",
        "A sociedade girará sob a denominação social SILVA & OLIVEIRA CONSULTORIA LTDA,",
        "com sede na Rua das Acácias, nº 200, São Paulo/SP, CEP 01234-567.",
        "",
        "CLÁUSULA SEGUNDA - DO OBJETO SOCIAL",
        "",
        "A sociedade tem por objeto social a prestação de serviços de consultoria",
        "empresarial, assessoria administrativa e gestão de negócios.",
        "",
        "CLÁUSULA TERCEIRA - DO CAPITAL SOCIAL",
        "",
        "O capital social é de R$ 100.000,00 (cem mil reais), dividido em 100 (cem)",
        "quotas de R$ 1.000,00 (mil reais) cada, assim distribuídas:",
        "",
        "- JOSÉ DA SILVA: 60 quotas, totalizando R$ 60.000,00",
        "- MARIA OLIVEIRA: 40 quotas, totalizando R$ 40.000,00",
        "",
        "CLÁUSULA QUARTA - DA ADMINISTRAÇÃO",
        "",
        "A administração da sociedade caberá aos sócios JOSÉ DA SILVA e MARIA OLIVEIRA,",
        "isoladamente, com poderes para praticar todos os atos necessários à gestão",
        "social, salvo as restrições constantes do contrato.",
        "",
        "CLÁUSULA QUINTA - DO EXERCÍCIO SOCIAL",
        "",
        "O exercício social coincidirá com o ano civil, encerrando-se em 31 de dezembro",
        "de cada ano, quando será levantado o balanço patrimonial e demonstrativo de",
        "resultados.",
    ]

    # Desenhar texto principal (limitado aos 80% da esquerda)
    max_x = tarja_x - 1*cm  # Margem de segurança
    for linha in texto_documento:
        if "CLÁUSULA" in linha:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(3*cm, y, linha)
            c.setFont("Helvetica", 11)
        else:
            c.drawString(3*cm, y, linha)
        y -= 0.5*cm

    # TARJA LATERAL (20% direita)
    # Fundo cinza claro
    c.setFillColor(HexColor('#F0F0F0'))
    c.rect(tarja_x, 0, tarja_width, height, fill=1, stroke=0)

    # Texto da tarja (rotacionado 90 graus, lendo de baixo para cima)
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 8)

    # Título da tarja (vertical)
    c.saveState()
    c.translate(tarja_x + tarja_width/2 + 0.3*cm, height/2)
    c.rotate(90)
    c.drawCentredString(0, 0, "DOCUMENTO ASSINADO DIGITALMENTE")
    c.restoreState()

    # Informações da assinatura (horizontal, texto pequeno)
    c.setFont("Helvetica", 6)
    y_tarja = height - 4*cm
    x_tarja = tarja_x + 0.2*cm

    info_tarja = [
        "Código de verificação:",
        "ABCD.1234.EFGH.5678",
        "",
        "Valide em:",
        "pje.tjsp.jus.br",
        "/validar",
        "",
        "Assinado por:",
        "JOSÉ DA SILVA",
        "CPF: 123.456.789-00",
        "",
        "Data/Hora:",
        "24/11/2025",
        "10:30:45",
        "",
        "Certificado:",
        "ICP-Brasil A3",
        "",
        "Hash SHA-256:",
        "3f4d5e6a7b8c9d0e",
        "1a2b3c4d5e6f7a8b",
    ]

    for linha in info_tarja:
        c.drawString(x_tarja, y_tarja, linha)
        y_tarja -= 0.35*cm


def generate_fixture_pdf(output_path: Path):
    """
    Gera o PDF de teste completo com 3 páginas.

    Args:
        output_path: Caminho onde o PDF será salvo
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=A4)

    # Página 1: Texto normal (NATIVE)
    create_page_1_text(c)
    c.showPage()

    # Página 2: Imagem de texto (RASTER_NEEDED)
    create_page_2_image(c)
    c.showPage()

    # Página 3: Texto com tarja lateral (TARJA_DETECTED)
    create_page_3_with_tarja(c)
    c.showPage()

    c.save()
    print(f"✅ PDF gerado com sucesso: {output_path}")
    print(f"   - Página 1: Texto normal (NATIVE)")
    print(f"   - Página 2: Imagem de texto (RASTER_NEEDED)")
    print(f"   - Página 3: Texto com tarja lateral (TARJA_DETECTED)")


if __name__ == "__main__":
    # Caminho do output
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output = project_root / "test-documents" / "fixture_test.pdf"

    generate_fixture_pdf(output)
