# Roadmap - Legal Text Extractor

## Arquitetura Atual (Fase 3) - COMPLETA

Pipeline de 4 estagios algoritmicos:

```
PDF → [Cartografo] → [Saneador] → [Extrator] → [Bibliotecario] → structure.json
       step_01       step_02       step_03       step_04
```

| Estagio | Nome | Script | Funcao |
|---------|------|--------|--------|
| 1 | Cartografo | `step_01_layout.py` | Detecta sistema judicial, mapeia layout |
| 2 | Saneador | `step_02_vision.py` | Pre-processa imagens para OCR |
| 3 | Extrator | `step_03_extract.py` | Extrai texto com bbox filtering |
| 4 | Bibliotecario | `step_04_classify.py` | Classifica pecas processuais |

**Status:** ✅ Completo (4 estagios implementados e testados)

---

## Detalhes do Bibliotecario (Step 04)

Quarto estagio da pipeline:

```
PDF → [Cartógrafo] → [Saneador] → [Extrator] → [Bibliotecário] → structure.json
       step_01       step_02       step_03       step_04
```

### ESTÁGIO 4: O BIBLIOTECÁRIO (Semantic Classifier)

**Script:** `src/steps/step_04_classify.py`

**Input:** `outputs/{doc_id}/final.md` (do Estágio 3)

**Lógica:**
1. Lê o Markdown estruturado
2. Aplica biblioteca de Regex (portada do JS) para identificar cabeçalhos de peças:
   - `EXCELENTÍSSIMO SENHOR DOUTOR JUIZ...` → Petição Inicial
   - `SENTENÇA` → Sentença
   - `ACÓRDÃO` → Acórdão
   - `CONTESTAÇÃO` → Contestação
   - `RÉPLICA` → Réplica
   - `EMBARGOS DE DECLARAÇÃO` → Embargos
   - `DESPACHO` → Despacho
   - `DECISÃO INTERLOCUTÓRIA` → Decisão
   - `CERTIDÃO` → Certidão
   - `ATA DE AUDIÊNCIA` → Ata
3. Segmenta o documento logicamente por peça processual

**Output:** `outputs/{doc_id}/structure.json`

```json
{
  "doc_id": "processo_123",
  "total_sections": 5,
  "sections": [
    {
      "id": 1,
      "type": "peticao_inicial",
      "title": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO...",
      "start_line": 1,
      "end_line": 150,
      "confidence": 0.95
    },
    {
      "id": 2,
      "type": "contestacao",
      "title": "CONTESTAÇÃO",
      "start_line": 151,
      "end_line": 280,
      "confidence": 0.92
    }
  ]
}
```

---

## Backlog

### Fase 3.1: Implementacao do Bibliotecario - COMPLETO
- [x] Criar `step_04_classify.py`
- [x] Portar regex de identificacao de pecas do JS
- [x] Implementar segmentacao por cabecalhos
- [x] Gerar `semantic_structure.json` com metadados
- [x] Gerar `final_tagged.md` com tags semanticas
- [ ] Testes unitarios para cada tipo de peca

**Implementado em 2025-11-25:**
- 12 categorias de pecas processuais
- Limpeza avancada de texto (15 regras regex)
- Taxonomia JSON com sinonimos e patterns
- CLI typer com comandos `classify` e `validate-taxonomy`

### Fase 3.2: Refinamentos do ImageCleaner
- [ ] Adicionar suporte a documentos com múltiplas colunas
- [ ] Otimizar detecção de carimbos coloridos (azul, vermelho, verde)
- [ ] Melhorar threshold adaptativo para scans muito escuros

### Fase 3.3: Integração End-to-End
- [ ] CLI unificada para pipeline completo
- [ ] Relatório de qualidade por documento
- [ ] Benchmark de performance (tempo/página)

---

## Decisões Arquiteturais

| Decisão | Motivo |
|---------|--------|
| Pipeline algorítmica (sem LLM) | Custo proibitivo de API para volume alto |
| Regex para classificação | Padrões jurídicos são bem definidos |
| Output em JSON | Facilita integração com sistemas downstream |
| Grayscale output | Suficiente para OCR, menor tamanho |

---

*Última atualização: 2025-11-25*
