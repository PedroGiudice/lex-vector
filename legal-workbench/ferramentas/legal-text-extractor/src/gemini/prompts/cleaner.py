"""
Prompt de Limpeza Contextual de Texto Jurídico.

Este prompt instrui o Gemini a LIMPAR o texto removendo ruído técnico,
mas PRESERVANDO 100% do conteúdo jurídico substantivo.

REGRA CRÍTICA: O Gemini NÃO deve resumir ou condensar. Apenas remover ruído.
"""

from __future__ import annotations


CLEANING_PROMPT = '''
# TAREFA: Limpeza Contextual de Documento Jurídico

Você é um assistente especializado em limpeza de documentos jurídicos. Sua tarefa é **LIMPAR** o texto, removendo ruído técnico, mas **PRESERVANDO 100%** do conteúdo jurídico substantivo.

---

## O QUE VOCÊ DEVE REMOVER (RUÍDO)

### 1. Assinaturas Digitais e Certificações
- Blocos de certificação ICP-Brasil
- Hashes e códigos de verificação (ex: "Código: XXXX-XXXX-XXXX")
- Timestamps de assinatura digital
- "Documento assinado digitalmente por..."
- "Assinado com certificado digital..."
- Informações de cadeia de certificação

### 2. Headers/Footers Repetidos
- Logos de tribunais descritos textualmente
- Número do processo repetido em cada página
- "Poder Judiciário" repetido
- "Tribunal Regional do Trabalho da X Região" repetido
- Paginação ("Página X de Y", "fl. X")
- Timestamps de geração do PDF

### 3. Metadados Técnicos de Sistema
- URLs de validação de documento
- QR Codes descritos como texto
- Marcas d'água textuais (ex: "CÓPIA", "DIGITALIZADO")
- Códigos de barras descritos
- Identificadores de sistema (PJe, e-SAJ, etc.)

### 4. Artefatos de OCR
- Caracteres isolados sem sentido (|, /, \\, etc. soltos)
- Sequências de pontuação sem texto
- Linhas com apenas números aleatórios
- Texto fragmentado óbvio de OCR falho

### 5. Ruído Visual Descrito
- "[Brasão]", "[Logo]", "[Imagem]"
- Descrições de elementos visuais sem valor textual
- Linhas de separação (====, ----, etc.)

---

## O QUE VOCÊ DEVE PRESERVAR (NUNCA REMOVER)

### 1. Todo Conteúdo Jurídico
- Petições, contestações, recursos INTEGRALMENTE
- Argumentos, fundamentação, dispositivos
- Citações de leis, doutrinas, jurisprudência
- Transcrições de depoimentos
- Pareceres e manifestações

### 2. Informações de Identificação
- Nomes de partes, advogados, juízes
- Números de documentos mencionados no texto
- Datas processuais relevantes
- Valores monetários
- Prazos e deadlines

### 3. Estrutura do Documento
- Divisão em seções/peças
- Numeração de itens e parágrafos
- Cabeçalhos de seção (SENTENÇA, CONTESTAÇÃO, etc.)
- Formatação que indica hierarquia

### 4. Assinaturas Nominais
- Nome do juiz/advogado que assina
- OAB e qualificação profissional
- (remover apenas o bloco de certificado digital, não o nome)

---

## REGRAS CRÍTICAS

1. **NÃO RESUMA** - Preserve o texto integral, apenas limpo
2. **NÃO REESCREVA** - Mantenha a redação original do autor
3. **NÃO REORGANIZE** - Mantenha a ordem exata do documento
4. **NÃO INTERPRETE** - Não adicione explicações ou notas
5. **NA DÚVIDA, PRESERVE** - Se não tem certeza se é ruído, deixe

---

## FORMATO DE OUTPUT

Retorne APENAS JSON válido. NÃO inclua markdown code blocks.

{{
  "doc_id": "identificador_do_documento",
  "sections": [
    {{
      "section_id": <número da seção>,
      "type": "TIPO_DA_PECA",
      "content": "TEXTO COMPLETO E LIMPO DA SEÇÃO (preservar quebras de linha)",
      "noise_removed": ["exemplo1 de ruído removido", "exemplo2", "exemplo3"]
    }},
    ...
  ],
  "total_chars_original": <total de caracteres antes da limpeza>,
  "total_chars_cleaned": <total de caracteres após limpeza>,
  "reduction_percent": <percentual de redução (0-100)>
}}

### Regras do JSON:
- `section_id` corresponde aos IDs da classificação prévia
- `type` deve corresponder à classificação prévia
- `content` é o texto INTEGRAL da seção, apenas com ruído removido
- `noise_removed` são exemplos do que foi removido (máximo 5 por seção)
- `content` deve preservar quebras de parágrafo (\\n\\n)

---

## CONTEXTO DA CLASSIFICAÇÃO PRÉVIA

O documento foi classificado nas seguintes seções:

'''


def build_cleaning_prompt(classification_summary: str) -> str:
    """
    Constrói prompt de limpeza com contexto da classificação prévia.

    Args:
        classification_summary: Resumo da classificação em formato texto/JSON
            Exemplo: "Seção 1: PETICAO_INICIAL (págs 1-10)\\nSeção 2: CONTESTACAO (págs 11-20)"

    Returns:
        Prompt completo para limpeza

    Example:
        >>> summary = "Seção 1: PETICAO_INICIAL (págs 1-10)"
        >>> prompt = build_cleaning_prompt(summary)
        >>> response = gemini_client.process_file(path, prompt)
    """
    return CLEANING_PROMPT + classification_summary + """

---

## DOCUMENTO PARA LIMPEZA

Limpe o documento abaixo, preservando todo conteúdo jurídico:

"""
