# ADR-001: Arquitetura Marker-Only para Extração de PDF

**Status:** Aceito
**Data:** 2025-12-09
**Decisores:** PGR (Product Design Director), Claude (Technical Director)

## Contexto

O sistema legal-text-extractor precisa processar PDFs jurídicos de grande volume (processos com centenas de páginas) e extrair texto de forma confiável, preservando a estrutura do documento.

### Problemas Identificados

1. **Output de 80MB**: Extrações geravam arquivos massivos, inutilizáveis para LLMs
2. **Complexidade da Pipeline Híbrida**: Lógica de fallback entre engines adicionava complexidade sem benefício claro
3. **Incerteza sobre OCR**: Não estava claro quando o Marker usava OCR vs extração nativa

### Descobertas da Pesquisa

Após análise detalhada da documentação e código-fonte do Marker:

1. **80MB é causado por imagens base64**, não por OCR excessivo
2. **Marker é "text-first"**: Usa `pdftext` para texto nativo, OCR (Surya) apenas quando necessário
3. **Configuração `--disable_image_extraction`** reduz output em ~98%
4. **`--use_llm` do Marker** só ajuda com tabelas/formulários, NÃO substitui classificação semântica

## Decisão

Adotar arquitetura **Marker-only** com configuração otimizada:

### Pipeline Simplificada

```
PDF → MarkerEngine (configurado) → DocumentCleaner → Output
                                           ↓
                              (Futuro) Step 04: Bibliotecário
```

### Configuração MarkerConfig

```python
@dataclass
class MarkerConfig:
    output_format: str = "markdown"
    paginate_output: bool = True           # Preserva referências de página
    disable_image_extraction: bool = True  # CRÍTICO: resolve problema 80MB
    disable_links: bool = True             # Remove hyperlinks (ruído)
    drop_repeated_text: bool = True        # Remove headers/footers repetidos
    keep_pageheader_in_output: bool = False  # Cabeçalhos são ruído (logos, "Poder Judiciário")
    keep_pagefooter_in_output: bool = False  # Rodapés são ruído (paginação, timestamps)
    force_ocr: bool = False                # Deixar Marker decidir automaticamente
    strip_existing_ocr: bool = False       # Preservar OCR existente
    use_llm: bool = False                  # Desabilitado - Step 04 fará classificação
```

### Justificativas

| Configuração | Valor | Razão |
|--------------|-------|-------|
| `disable_image_extraction` | True | Imagens base64 causam 98% do bloat |
| `paginate_output` | True | Essencial para citações jurídicas ("fl. 42") |
| `keep_pageheader_in_output` | False | Cabeçalhos judiciais são ruído puro (logos, números de processo repetidos) |
| `keep_pagefooter_in_output` | False | Rodapés contêm apenas paginação e timestamps |
| `force_ocr` | False | Marker detecta automaticamente páginas que precisam OCR |
| `use_llm` | False | LLM do Marker é para tabelas; Step 04 fará classificação semântica |

## Alternativas Consideradas

### 1. Pipeline Híbrida (Marker + PDFPlumber fallback)

**Rejeitada porque:**
- Adiciona complexidade sem benefício mensurável
- PDFPlumber não oferece vantagem sobre Marker para casos de uso identificados
- Marker já tem fallback interno para páginas problemáticas

### 2. Usar `--use_llm` do Marker para classificação

**Rejeitada porque:**
- Funcionalidade do Marker é específica para tabelas/formulários
- Não faz classificação semântica de peças processuais
- Step 04 com Gemini 2.5 Flash/Pro será desenvolvido especificamente para isso

## Consequências

### Positivas

- **Simplicidade**: Uma engine, configuração clara
- **Performance**: Output leve (~1MB vs 80MB)
- **Manutenibilidade**: Menos código, menos pontos de falha
- **Transparência**: Metadados mostram quantas páginas usaram OCR vs nativo

### Negativas

- **Dependência única**: Se Marker falhar, não há fallback automático
  - Mitigação: PDFPlumber pode ser adicionado posteriormente se necessário
- **RAM**: Requer ~10GB RAM (aceitável para ambiente de desenvolvimento)

### Neutras

- **Step 04 pendente**: Classificação semântica será implementada separadamente
- **Testes necessários**: Validar com PDFs reais no legal-workbench antes do merge

## Próximos Passos

1. ✅ Implementar MarkerEngine com configuração otimizada
2. ✅ Simplificar main.py para usar apenas Marker
3. ⏳ Testar no legal-workbench com PDFs reais
4. ⏳ Fazer merge para main após validação
5. ⏳ Implementar Step 04 (Bibliotecário) com Gemini

## Taxonomia de Peças (para Step 04)

Categorias definidas para classificação futura:

1. `PETICAO_INICIAL` - Petição inicial, aditamentos
2. `CONTESTACAO_DEFESA` - Contestação, defesa, exceções
3. `REPLICA` - Réplica, tréplica, manifestações
4. `DECISAO_JUDICIAL` - Sentenças, acórdãos, decisões interlocutórias
5. `DESPACHO` - Despachos, determinações procedimentais
6. `RECURSO` - Apelações, agravos, embargos
7. `PARECER_MP` - Pareceres do Ministério Público
8. `ATA_TERMO` - Atas de audiência, termos de depoimento
9. `CERTIDAO` - Certidões, intimações, citações
10. `ANEXOS_DOCUMENTOS` - Documentos probatórios anexados
11. `CAPA_DADOS_PROCESSO` - Capa, dados de autuação
12. `INDETERMINADO` - Peças não classificáveis

## Referências

- [Marker PDF Documentation](https://github.com/VikParuchuri/marker)
- Research/Marker PDF Converter Optimization Guide.txt
- Research/marker_integration_analysis.md
- Research/Deep-Research-Marker.md
