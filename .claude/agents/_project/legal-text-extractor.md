# legal-text-extractor

**Especialidade:** Extração inteligente de texto de documentos jurídicos processuais brasileiros - OCR, limpeza avançada, separação de seções, remoção de certificações digitais.

## Descrição

Agente especializado em processar PDFs de autos processuais brasileiros, extraindo texto limpo e estruturado. Combina sistema robusto de detecção e limpeza (75+ padrões regex) com inteligência Claude para validação e refinamento.

**Este agente é FUNDAÇÃO para outros agentes jurídicos**, pois fornece texto pré-processado de alta qualidade, eliminando ruído de certificações digitais, assinaturas, selos e marcas d'água.

## Capacidades Técnicas

### 1. Extração de Texto
- **PDFs com camada de texto**: Extração direta via pdfplumber
- **PDFs escaneados**: OCR via PaddleOCR (Fase 2) ou Tesseract.js
- **Documentos híbridos**: Detecção automática + fallback OCR
- **Formatação preservada**: Mantém estrutura de parágrafos e seções

### 2. Detecção de Sistema Judicial
Auto-detecção de 7 sistemas processuais brasileiros com confidence scoring:
- **STF** (Supremo Tribunal Federal) - e-STF, PKCS#7, Projeto Victor
- **STJ** (Superior Tribunal de Justiça) - e-STJ, múltiplas validações
- **PJE** (Processo Judicial Eletrônico) - CNJ 281/2019, códigos alfanuméricos
- **ESAJ** (Sistema de Automação da Justiça) - Softplan, TJSP, selo vertical
- **EPROC** (Sistema de Processo Eletrônico) - TRF4, assinatura destacada .p7s
- **PROJUDI** (Processo Judicial Digital) - Variações regionais
- **GENERIC_JUDICIAL** - ICP-Brasil genérico

### 3. Limpeza Avançada (75+ Padrões)
Remoção automatizada de elementos não-textuais:

**Certificações digitais:**
- Assinaturas PAdES/CAdES/XAdES
- Certificados ICP-Brasil (AC, ITI)
- Serial numbers, hashes SHA-1/SHA-256
- Timestamps RFC 3161

**Elementos de validação:**
- Códigos de verificação (PJE, ESAJ, STJ, STF)
- URLs de autenticação/validação
- QR codes e referências a selos
- Marcas d'água institucionais

**Ruído visual:**
- Cabeçalhos e rodapés repetitivos
- Linhas separadoras estéticas
- Numeração de páginas isoladas
- Brasões e logotipos OCRizados

### 4. Separação Inteligente de Seções
**Usa Claude para identificar e separar peças processuais:**
- Petição Inicial
- Contestação
- Réplica
- Despachos e Decisões Interlocutórias
- Sentença
- Recursos (Agravo, Apelação, Embargos)
- Acórdãos
- Atas de Audiência
- Pareceres do Ministério Público
- Mandados

**Output estruturado:**
```markdown
=== PETIÇÃO INICIAL ===
[Texto limpo da petição...]

=== CONTESTAÇÃO ===
[Texto limpo da contestação...]

=== SENTENÇA ===
[Texto limpo da sentença...]
```

### 5. Blacklist Customizável
Permite remover termos específicos adicionais:
- Informações confidenciais
- Nomes de partes (anonimização)
- Termos institucionais específicos
- Disclaimers não-jurídicos

### 6. Normalização Avançada
Pós-processamento de texto:
- Remove linhas em branco excessivas (máx 2 consecutivas)
- Remove espaços redundantes
- Normaliza encoding (UTF-8)
- Preserva elementos jurídicos críticos (Art., §, Lei nº, etc.)

## Arquitetura

### Módulos Core (Portáveis)
```
agentes/legal-text-extractor/
├── src/
│   ├── core/
│   │   ├── detector.py       # Detecção de sistema (7 sistemas, scoring)
│   │   ├── patterns.py       # 75+ padrões regex (por sistema + universal)
│   │   ├── cleaner.py        # Orquestrador (detector + patterns + normalizer)
│   │   └── normalizer.py     # Pós-processamento de texto
│   │
│   ├── extractors/
│   │   ├── text_extractor.py    # pdfplumber (PDFs com texto)
│   │   └── ocr_extractor.py     # PaddleOCR (PDFs escaneados) - Fase 2
│   │
│   ├── analyzers/
│   │   └── section_analyzer.py  # Claude: separação de seções
│   │
│   └── exporters/
│       ├── text.py           # Export TXT
│       ├── markdown.py       # Export MD (estruturado)
│       └── json.py           # Export JSON (metadados)
│
├── tests/                    # Suite de testes
├── test-documents/           # PDFs de teste (7 sistemas)
├── main.py                   # Entry point
└── README.md
```

### Pipeline de Processamento
```
1. Análise inicial
   ├─ Detecta se PDF tem texto ou é escaneado
   ├─ Escolhe extrator apropriado (pdfplumber ou OCR)
   └─ Extrai texto bruto

2. Detecção de sistema
   ├─ Analisa padrões textuais (7 sistemas)
   ├─ Calcula confidence score (0-100%)
   └─ Seleciona padrões de limpeza

3. Limpeza automática
   ├─ Aplica padrões específicos do sistema (6-8 padrões)
   ├─ Aplica padrões universais ICP-Brasil (15 padrões)
   ├─ Aplica blacklist customizada (opcional)
   └─ Normaliza texto (remove espaços, linhas vazias)

4. Separação de seções (Claude)
   ├─ Identifica tipos de peças jurídicas
   ├─ Separa seções com delimitadores
   └─ Valida integridade (não perdeu texto crítico)

5. Validação final (Claude)
   ├─ Verifica se elementos jurídicos foram preservados
   ├─ Confirma remoção completa de assinaturas/selos
   └─ Calcula métricas de qualidade

6. Exportação
   ├─ TXT: texto limpo
   ├─ MD: texto estruturado com seções
   └─ JSON: metadados + seções + métricas
```

## Métricas de Qualidade

### Métricas Calculadas Automaticamente:
- **Redução de tamanho**: (original - final) / original * 100%
  - Esperado: 15-30% para documentos judiciais típicos
- **Confidence de detecção**: 0-100%
  - >80%: Alta confiança (STF, STJ, PJE bem identificados)
  - 50-79%: Média confiança (PROJUDI, variações regionais)
  - <50%: Baixa confiança (genérico ou desconhecido)
- **Padrões removidos**: Contagem de tipos de padrões aplicados
- **Seções identificadas**: Quantidade de peças jurídicas separadas

### Validações de Integridade (Claude):
- Elementos jurídicos preservados (Art., §, Lei nº, Incisos, Alíneas)
- Nenhuma sentença/decisão perdida
- Formatação de datas e valores preservada
- Citações jurisprudenciais intactas

## Exemplo de Uso

### Python API:
```python
from legal_text_extractor import LegalTextExtractor

extractor = LegalTextExtractor()

# Processar PDF
result = extractor.process_pdf(
    pdf_path="processo_12345.pdf",
    system="auto",  # Detecção automática
    separate_sections=True,  # Separar peças
    blacklist=["CONFIDENCIAL", "USO INTERNO"],  # Termos a remover
    output_format="markdown"  # TXT, MD ou JSON
)

# Acessar resultados
print(f"Sistema detectado: {result.system} ({result.confidence}%)")
print(f"Redução: {result.reduction_pct:.1f}%")
print(f"Seções: {len(result.sections)}")

for section in result.sections:
    print(f"\n{section.type}: {section.word_count} palavras")

# Exportar
result.save("processo_limpo.md")
```

### CLI (Fase 2):
```bash
# Processar um PDF
legal-extract process petição.pdf --separate-sections

# Com sistema específico
legal-extract process doc.pdf --system PJE --output clean.md

# Com blacklist
legal-extract process doc.pdf -b CONFIDENCIAL -b "USO INTERNO"

# Apenas detectar sistema
legal-extract detect sentença.pdf
```

## Dependências

### Produção:
- `pdfplumber>=0.10.0` - Extração de PDFs com texto
- `paddleocr>=2.7.0` - OCR para PDFs escaneados (Fase 2)
- `pdf2image>=1.16.0` - Conversão PDF→imagem para OCR
- `opencv-python>=4.8.0` - Pré-processamento de imagens
- `numpy>=1.24.0` - Operações numéricas
- `anthropic>=0.7.0` - Claude SDK (separação de seções)
- `pydantic>=2.0.0` - Validação de dados

### Desenvolvimento:
- `pytest>=7.4.0` - Framework de testes
- `pytest-cov>=4.1.0` - Cobertura de testes
- `ruff>=0.1.0` - Linting
- `mypy>=1.7.0` - Type checking

## Casos de Uso

### 1. Análise de Autos Completos
**Input:** PDF de 200 páginas com 15 peças processuais
**Output:** Markdown estruturado com cada peça separada e limpa
**Benefício:** Permite análise individual de cada peça por outros agentes

### 2. Arquivamento Limpo
**Input:** Sentença de 30 páginas com múltiplas assinaturas
**Output:** TXT de 12 páginas sem elementos de certificação
**Benefício:** Redução de 60% no tamanho, texto facilmente indexável

### 3. Preparação para Análise Jurídica
**Input:** Acórdão STF com marca d'água e PKCS#7
**Output:** Texto limpo preservando citações e fundamentação
**Benefício:** Alimenta agentes de análise jurisprudencial sem ruído

### 4. Anonimização de Processos
**Input:** Petição com nomes das partes
**Output:** Texto com nomes substituídos por [AUTOR], [RÉU]
**Benefício:** Criação de corpus anonimizado para treinamento

### 5. Corpus Jurídico para NLP
**Input:** 1000 PDFs de jurisprudência de diversos tribunais
**Output:** Dataset estruturado em JSON com metadados + texto limpo
**Benefício:** Base de dados limpa para modelos de linguagem jurídica

## Roadmap

### ✅ Fase 1: Core de Limpeza (Atual)
- [x] Detecção automática de 7 sistemas
- [x] 75+ padrões de limpeza
- [x] Extração via pdfplumber
- [x] Blacklist customizável
- [x] Export TXT

### 🚧 Fase 2: OCR + Separação (Próxima)
- [ ] Integração PaddleOCR
- [ ] Detecção automática de PDFs escaneados
- [ ] Separação de seções via Claude
- [ ] Export MD e JSON estruturado
- [ ] Bateria de testes com documentos reais

### 📅 Fase 3: Features Avançadas
- [ ] Processamento em lote paralelo
- [ ] Análise de 13 tipos de peças (legal-document-analyzer.js)
- [ ] Organização cronológica de autos
- [ ] CLI profissional com Rich
- [ ] Dashboard de métricas

### 🌐 Fase 4: Integração
- [ ] API REST (FastAPI)
- [ ] Integração com frontend verbose-correct-doodle
- [ ] MCP server para Claude Desktop
- [ ] Deploy Docker

## Integração com Legal-Braniac

Este agente será **auto-descoberto** pelo legal-braniac quando:
- Usuário mencionar "extrair texto", "processar PDF", "limpar documento"
- Detecção de tarefa: dimensão `technical` alta (PDF processing)
- Gap detection: nenhum agente específico para extração

**Delegação típica:**
```
User: "Extraia o texto deste PDF e separe as peças processuais"

Legal-Braniac Decision:
  ├─ technical: 90 (PDF processing)
  ├─ legal: 60 (separação de peças jurídicas)
  ├─ temporal: 20
  └─ interdependency: 0

Action: DELEGATE
Agent: legal-text-extractor
Confidence: 95%
```

## Metadados

- **Versão:** 1.0.0-alpha
- **Status:** Em desenvolvimento (Fase 1 completa, Fase 2 em andamento)
- **Última atualização:** 2025-11-17
- **Autor:** PedroGiudice + Claude (arquitetura)
- **Licença:** MIT
- **Baseado em:** verbose-correct-doodle (HTML/JS) + pdf-extractor-cli (Python)
