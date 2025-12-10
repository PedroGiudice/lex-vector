"""
Prompt de Classificação Semântica de Peças Processuais.

Este é o componente MAIS CRÍTICO do sistema Bibliotecário.
O prompt instrui o Gemini a:
1. Identificar seções/peças no documento
2. Classificar cada uma nas 12 categorias da taxonomia
3. Retornar JSON estruturado e validável

ATENÇÃO: Qualquer modificação neste prompt afeta diretamente
a qualidade da classificação. Teste extensivamente antes de alterar.
"""

from __future__ import annotations

TAXONOMY_DESCRIPTION = '''
## TAXONOMIA DE PEÇAS PROCESSUAIS BRASILEIRAS

Você DEVE classificar cada seção em EXATAMENTE UMA das seguintes 12 categorias:

### 1. PETICAO_INICIAL
**Descrição:** Documento que inicia o processo judicial. É a primeira manifestação do autor/reclamante.
**Triggers de Identificação:**
- "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ" (início típico)
- "vem, respeitosamente, à presença de Vossa Excelência"
- "propor a presente AÇÃO" ou "RECLAMAÇÃO TRABALHISTA"
- Contém qualificação das partes no início
- Geralmente é o primeiro documento substantivo do processo
**Inclui:** Petições iniciais, aditamentos à inicial, emendas à inicial

### 2. CONTESTACAO
**Descrição:** Resposta formal do réu/reclamado à inicial. Defesa processual.
**Triggers de Identificação:**
- Título "CONTESTAÇÃO" ou "DEFESA"
- "Em preliminar" ou "Preliminarmente"
- "No mérito" seguido de contraditório
- Menciona "réu", "reclamada", "improcedência"
- Pode conter exceções de incompetência, preliminares
**Inclui:** Contestações, defesas, exceções, impugnações

### 3. REPLICA
**Descrição:** Resposta do autor à contestação. Manifestação sobre defesa.
**Triggers de Identificação:**
- Título "RÉPLICA" ou "IMPUGNAÇÃO À CONTESTAÇÃO"
- "Em réplica à contestação"
- "Manifestação sobre documentos"
- Refuta argumentos da defesa
**Inclui:** Réplicas, tréplicas, manifestações sobre documentos da parte contrária

### 4. DECISAO_JUDICIAL
**Descrição:** Pronunciamentos judiciais que decidem questões (mérito ou processuais).
**Triggers de Identificação:**
- "SENTENÇA" ou "ACÓRDÃO" no início
- "Vistos, etc." ou "Vistos e examinados os autos"
- "JULGO PROCEDENTE" ou "JULGO IMPROCEDENTE"
- "Acordam os Desembargadores" (acórdãos)
- "DECISÃO" com análise de mérito
- Presença de fundamentação + dispositivo
- Assinatura de juiz/desembargador ao final
**Inclui:** Sentenças, acórdãos, decisões interlocutórias de mérito, julgamentos antecipados

### 5. DESPACHO
**Descrição:** Pronunciamentos judiciais de mero expediente, sem análise de mérito.
**Triggers de Identificação:**
- "DESPACHO" no início
- Comandos curtos: "Cite-se", "Intime-se", "Junte-se"
- "Defiro" ou "Indefiro" sem fundamentação extensa
- "Aguarde-se", "Dê-se vista"
- "Conclusos para sentença"
- Geralmente curtos (menos de meia página)
**Inclui:** Despachos de mero expediente, determinações procedimentais

### 6. RECURSO
**Descrição:** Peças recursais - impugnações a decisões.
**Triggers de Identificação:**
- "APELAÇÃO", "AGRAVO", "RECURSO ORDINÁRIO"
- "EMBARGOS DE DECLARAÇÃO"
- "RECURSO DE REVISTA"
- "RAZÕES DE RECURSO" ou "CONTRARRAZÕES"
- Menciona "reforma" de decisão
- Cita artigos do CPC sobre recursos
**Inclui:** Apelações, agravos, embargos, recursos extraordinários, contrarrazões

### 7. PARECER_MP
**Descrição:** Manifestações do Ministério Público como fiscal da lei.
**Triggers de Identificação:**
- "MINISTÉRIO PÚBLICO" no cabeçalho
- "PARECER" como título
- "Promotor de Justiça" ou "Procurador"
- "Opina" ou "Manifesta-se"
- Linguagem de custos legis
**Inclui:** Pareceres ministeriais, promoções, manifestações do MP

### 8. ATA_TERMO
**Descrição:** Registros de audiências e termos processuais.
**Triggers de Identificação:**
- "ATA DE AUDIÊNCIA" no início
- "TERMO DE" (depoimento, conciliação, etc.)
- "Audiência realizada em"
- Data, hora, local da audiência
- Descrição de procedimentos orais
- Registro de testemunhos/depoimentos
**Inclui:** Atas de audiência, termos de depoimento, atas de conciliação

### 9. CERTIDAO
**Descrição:** Atestados de atos processuais e comunicações.
**Triggers de Identificação:**
- "CERTIFICO" ou "CERTIDÃO"
- "Certidão de Intimação"
- "Certidão de Publicação"
- Estilo formal de cartório
- Assinatura de escrivão/analista
**Inclui:** Certidões de intimação, publicação, trânsito em julgado

### 10. ANEXOS
**Descrição:** Documentos probatórios anexados ao processo.
**Triggers de Identificação:**
- "PROCURAÇÃO" (documento de representação)
- "CONTRATO" (qualquer tipo)
- "Doc." ou "Documento nº"
- "ANEXO" seguido de número
- "COMPROVANTE" de qualquer tipo
- Documentos pessoais (RG, CPF, CTPS)
- Extratos bancários, contracheques
- Documentos que NÃO são peças processuais típicas
**Inclui:** Procurações, contratos, comprovantes, documentos pessoais, fotos, laudos técnicos

### 11. CAPA_DADOS
**Descrição:** Informações cadastrais e de autuação do processo.
**Triggers de Identificação:**
- "Classe:" e "Assunto:" estruturados
- "Distribuído em:"
- "Autuação"
- Dados cadastrais das partes
- Número do processo em destaque
- Metadados do sistema judicial
**Inclui:** Capas de processo, dados de distribuição, informações de autuação

### 12. INDETERMINADO
**Descrição:** Use APENAS quando for impossível classificar em outra categoria.
**Quando Usar:**
- Páginas em branco ou quase vazias
- Conteúdo corrompido/ilegível
- Documentos em idioma estrangeiro não traduzidos
- Fragmentos sem contexto suficiente
**ATENÇÃO:** Use com parcimônia. A maioria dos documentos DEVE ter classificação específica.
'''

CLASSIFICATION_PROMPT = f'''
# TAREFA: Classificação Semântica de Documento Jurídico Brasileiro

Você é um especialista em direito processual brasileiro com profundo conhecimento da estrutura de processos judiciais. Sua tarefa é analisar o documento abaixo e identificar as diferentes peças processuais, classificando cada uma de forma precisa.

{TAXONOMY_DESCRIPTION}

---

## REGRAS DE CLASSIFICAÇÃO

### 1. Identificação de Seções
- Cada MUDANÇA de peça processual marca uma nova seção
- Observe os marcadores de página: `## [[PAGE_XXX]] [TYPE: ...]`
- Uma seção pode abranger MÚLTIPLAS páginas consecutivas
- O início de uma nova peça geralmente é evidente pelo cabeçalho ou mudança de contexto

### 2. Critérios de Classificação
- Leia o INÍCIO de cada seção para identificar o tipo
- Priorize os **triggers de identificação** da taxonomia
- Se houver ambiguidade, considere o CONTEXTO do documento
- Atribua confidence baseado na clareza dos triggers:
  - 0.9-1.0: Triggers claros e inequívocos
  - 0.7-0.9: Triggers presentes mas contexto ambíguo
  - 0.5-0.7: Inferência baseada em contexto
  - 0.3-0.5: Classificação incerta
  - <0.3: Use INDETERMINADO

### 3. Regras Especiais
- Se um documento tiver múltiplas petições iniciais, classifique cada uma separadamente
- Despachos curtos (< 10 linhas) intercalados podem ser agrupados com a peça seguinte
- Documentos de identificação (RG, CPF) sempre são ANEXOS
- Na dúvida entre DECISAO_JUDICIAL e DESPACHO, verifique se há fundamentação

---

## FORMATO DE OUTPUT

Retorne APENAS JSON válido. NÃO inclua markdown code blocks (```json).
Siga EXATAMENTE este schema:

{{
  "doc_id": "identificador_do_documento",
  "total_pages": <número total de páginas>,
  "total_sections": <número de seções identificadas>,
  "sections": [
    {{
      "section_id": 1,
      "type": "TIPO_DA_PECA",
      "title": "Título descritivo curto (max 50 chars)",
      "start_page": <página inicial>,
      "end_page": <página final>,
      "confidence": <0.0 a 1.0>,
      "reasoning": "Justificativa em 1 frase (ex: 'Começa com Excelentíssimo Senhor')"
    }},
    ...
  ],
  "summary": "Resumo do processo em 1-2 frases descrevendo o tipo de ação e partes envolvidas"
}}

### Regras do JSON:
- `section_id` deve ser sequencial começando em 1
- `type` deve ser EXATAMENTE uma das 12 categorias (em MAIÚSCULAS)
- `start_page` e `end_page` são números (1-indexed)
- `confidence` é um float entre 0.0 e 1.0
- Todos os campos são OBRIGATÓRIOS

---

## DOCUMENTO PARA ANÁLISE

Analise o documento abaixo e retorne a classificação JSON:

'''


def build_classification_prompt(doc_id: str = "documento") -> str:
    """
    Constrói prompt de classificação com doc_id customizado.

    Args:
        doc_id: Identificador do documento (usado no output JSON)

    Returns:
        Prompt completo para classificação

    Example:
        >>> prompt = build_classification_prompt("processo_123")
        >>> response = gemini_client.process_file(path, prompt)
    """
    return CLASSIFICATION_PROMPT.replace(
        '"doc_id": "identificador_do_documento"',
        f'"doc_id": "{doc_id}"'
    )
