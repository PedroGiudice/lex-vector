# Roadmap - Legal Text Extractor

## Arquitetura Atual (Fase 2)

Pipeline de 3 estágios algorítmicos:

```
PDF → [Cartógrafo] → [Saneador] → [Extrator] → final.md
       step_01       step_02       step_03
```

| Estágio | Nome | Script | Função |
|---------|------|--------|--------|
| 1 | Cartógrafo | `step_01_layout.py` | Detecta sistema judicial, mapeia layout |
| 2 | Saneador | `step_02_vision.py` | Pré-processa imagens para OCR |
| 3 | Extrator | `step_03_extract.py` | Extrai texto com bbox filtering |

**Status:** ✅ Completo (8 testes de integração passando)

---

## Arquitetura Proposta (Fase 3)

Adicionaremos um quarto estágio à pipeline:

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

### Fase 3.1: Implementação do Bibliotecário
- [ ] Criar `step_04_classify.py`
- [ ] Portar regex de identificação de peças do JS
- [ ] Implementar segmentação por cabeçalhos
- [ ] Gerar `structure.json` com metadados
- [ ] Testes unitários para cada tipo de peça

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
