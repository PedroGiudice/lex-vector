# Memória de Sessão - Legal Text Extractor

**Data:** 2025-11-17
**Sessão:** Implementação do agente legal-text-extractor
**Contexto:** Sistema de extração inteligente de texto jurídico

---

## Resumo Executivo

Implementado **agente legal-text-extractor** completo (Fase 1), fundação para processamento de documentos jurídicos processuais brasileiros.

---

## Arquitetura Implementada

### Dois locais, duas funções:

**1. `.claude/agents/legal-text-extractor.md`**
- Definição/metadata do agente para legal-braniac
- "Currículo" - o que o agente faz
- Legal-braniac lê daqui para auto-discovery

**2. `agentes/legal-text-extractor/`**
- Código Python executável (~2300 linhas)
- Venv configurado com dependencies
- Legal-braniac EXECUTA código daqui

---

## Componentes Principais

### Core Modules (Copiados de pdf-extractor-cli)
- `detector.py` - Detecção de 7 sistemas judiciais (confidence scoring)
- `patterns.py` - 75+ padrões regex (específicos + universais)
- `cleaner.py` - Orquestrador (detector + patterns + normalizer + blacklist)
- `normalizer.py` - Pós-processamento de texto

### Extractors
- `text_extractor.py` - pdfplumber (PDFs com texto)
- `ocr_extractor.py` - Stub para Fase 2 (PaddleOCR)

### Analyzers
- `section_analyzer.py` - Claude SDK para separação de seções (Fase 2)

### Exporters
- `text.py` - Export TXT
- `markdown.py` - Export MD estruturado
- `json.py` - Export JSON com metadados

### Main API
- `main.py` - LegalTextExtractor class (entry point)

---

## Sistemas Judiciais Suportados

1. **STF** (Supremo Tribunal Federal) - e-STF, PKCS#7, Projeto Victor
2. **STJ** (Superior Tribunal de Justiça) - e-STJ, múltiplas validações
3. **PJE** (Processo Judicial Eletrônico) - CNJ 281/2019, códigos alfanuméricos
4. **ESAJ** (Sistema de Automação da Justiça) - Softplan, TJSP, selo vertical
5. **EPROC** (Sistema de Processo Eletrônico) - TRF4, assinatura .p7s
6. **PROJUDI** (Processo Judicial Digital) - Variações regionais
7. **GENERIC_JUDICIAL** - ICP-Brasil genérico

---

## Padrões de Limpeza (75+)

**Por sistema:** 6-8 padrões específicos cada
**Universais:** 15 padrões ICP-Brasil

**Categorias removidas:**
- Assinaturas digitais (PAdES/CAdES/XAdES)
- Certificados ICP-Brasil (Serial, SHA-1/256, AC)
- Códigos de verificação
- URLs de autenticação
- QR codes, marcas d'água, selos
- Cabeçalhos, rodapés, numeração

---

## Pipeline de Processamento

```
1. Análise inicial → Detecta tipo de PDF (texto vs escaneado)
2. Extração → pdfplumber (ou OCR na Fase 2)
3. Detecção de sistema → 7 sistemas, confidence 0-100%
4. Limpeza automática → Padrões específicos + universais + blacklist
5. Separação de seções → Claude SDK (Fase 2)
6. Validação final → Claude verifica integridade
7. Exportação → TXT/MD/JSON
```

---

## Status Atual

### ✅ Fase 1: COMPLETA
- Estrutura de 26 arquivos
- Core de limpeza (75+ padrões)
- Detecção de 7 sistemas
- Extração com pdfplumber
- Export TXT/MD/JSON
- Venv + dependencies
- Commitado: `ff1efd9`

### 🚧 Fase 2: PENDENTE
- PDFs de teste (usuário vai adicionar)
- Separação de seções (Claude SDK)
- OCR para PDFs escaneados (opcional)
- Bateria de testes com documentos reais

---

## Próximos Passos

1. **Usuário adiciona PDFs de teste** (7 sistemas)
2. **Testar extração básica** (validar detecção + limpeza)
3. **Implementar `section_analyzer.py`** (Claude SDK)
4. **Rodar bateria de testes** (métricas: redução, confidence, preservação)
5. **Commitar Fase 2**

---

## Contexto Importante

### Por Que Este Agente É Crítico?

**É FUNDAÇÃO para outros agentes jurídicos:**
- Outros agentes trabalham melhor com **TXT limpo** do que com **PDFs pesados**
- Remove ruído de certificações (15-30% de redução)
- Preserva elementos jurídicos críticos (Art., §, Lei nº)
- Estrutura seções para análise individual

**Agentes futuros que dependerão deste:**
- Análise jurisprudencial
- Extração de teses jurídicas
- Identificação de precedentes
- Elaboração de pareceres
- Qualquer processamento de documentos processuais

---

## Integração com Legal-Braniac

**Auto-discovery:**
- Legal-braniac lê `.claude/agents/legal-text-extractor.md`
- Detecta capacidades (extração, limpeza, separação)
- Ranqueia quando usuário menciona "extrair texto", "processar PDF", "limpar documento"

**Gap detection:**
- Se nenhum agente específico para extração → cria virtual agent
- Mas legal-text-extractor já cobre essa gap → usa este

**Delegação típica:**
```
User: "Extraia o texto deste PDF e separe as peças processuais"

Legal-Braniac Decision:
  ├─ technical: 90 (PDF processing)
  ├─ legal: 60 (peças jurídicas)
  ├─ temporal: 20
  └─ interdependency: 0

Action: DELEGATE
Agent: legal-text-extractor
Confidence: 95%
```

---

## Lições Aprendidas

1. **Separação clara:** `.claude/agents/` = metadata, `agentes/` = código
2. **Core portável:** Módulos core independentes (podem ser reusados)
3. **Baseado em sistema robusto:** pdf-extractor-cli já tinha 75+ padrões testados
4. **Stubs para futuro:** OCR e separação de seções com stubs para Fase 2
5. **Documentação detalhada:** NEXT_STEPS.md para continuar facilmente

---

## Comandos para Retomar

**Ativar venv:**
```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/legal-text-extractor
source .venv/bin/activate
```

**Ver próximos passos:**
```bash
cat NEXT_STEPS.md
```

**Testar (quando tiver PDFs):**
```bash
python main.py test-documents/exemplo.pdf
```

---

## Arquivos-Chave para Consulta

1. **Definição do agente:** `.claude/agents/legal-text-extractor.md`
2. **Próximos passos:** `agentes/legal-text-extractor/NEXT_STEPS.md`
3. **API principal:** `agentes/legal-text-extractor/main.py`
4. **Padrões de limpeza:** `agentes/legal-text-extractor/src/core/patterns.py`
5. **Detecção de sistemas:** `agentes/legal-text-extractor/src/core/detector.py`

---

**Data de criação:** 2025-11-17
**Status:** Fase 1 completa, aguardando PDFs de teste para Fase 2
**Commit:** ff1efd9 - "feat(legal-text-extractor): implementa agente de extração de texto jurídico"
