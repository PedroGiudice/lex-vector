# Sessão 2026-03-06 — LTE Pipeline: Descobertas e Decisões

## Contexto

Sessão de revisão arquitetural do Legal Text Extractor (LTE) a partir de testes no Datalab Playground e análise crítica do `modal_worker.py` atual.

---

## 1. Problemas Identificados no modal_worker.py Atual

### 1.1 Arquitetura Multi-GPU Está Errada

A implementação atual (`extract_pdf_parallel` + `T4Extractor`) divide o PDF em chunks e envia cada um para um container T4 separado. Problemas concretos:

- **PDF serializado N vezes**: `[pdf_bytes] * len(chunks)` envia o arquivo completo para cada container. Um PDF de 50MB com 5 chunks = 250MB de transferência desnecessária.
- **Cold starts simultâneos**: múltiplos containers T4 sobem ao mesmo tempo, sem garantia de que os snapshots estão prontos.
- **Premissa errada**: o gargalo do Marker não é VRAM — é overhead de coordenação. A documentação do Marker recomenda exatamente o oposto: **um GPU maior com múltiplos workers paralelos** (`NUM_WORKERS` dentro do mesmo container), não múltiplos GPUs cada um com um processo.

### 1.2 Threshold de Decisão Arbitrário

```python
PARALLEL_THRESHOLD = 300  # acima disso usa multi-T4
DEFAULT_CHUNK_SIZE = 100
MAX_PARALLEL_WORKERS = 8
```

Sem medição real. Um auto de 350 páginas todo digital vai para multi-T4 por causa de um número arbitrário, quando um único L40S com múltiplos workers resolveria mais barato e mais rápido.

**Status**: arquitetura multi-GPU identificada como lixo. Reescrever.

---

## 2. Configurações do Marker — O Que Funciona

Descobertas a partir de testes no Datalab Playground com autos do TJSP:

### 2.1 bbox — DESABILITAR

`bbox` aumenta muito o tempo de parse sem melhorar a qualidade do output. Não usar.

### 2.2 image captions — DESABILITAR

Para autos judiciais, image captions são ruído puro. O modelo tenta descrever carimbos, assinaturas digitais, logotipos de tribunal. Zero valor semântico.

### 2.3 paginate — HABILITAR

Preserva referência de página no output. Necessário para citação em RAG.

### 2.4 skip cache — DESABILITAR

Manter cache de modelos. Cold start sem cache é inaceitável em produção.

### 2.5 Modelo "faster"

Para documentos nativos digitais do TJSP, o modelo "faster" é suficiente. Reduz tempo de parse significativamente. Validado em testes no playground.

### 2.6 auto-segment — Ideal

Segmentação automática funciona bem para autos. Usar como padrão.

### 2.7 Output Formats Disponíveis

| Format | Uso |
|---|---|
| `markdown` | Legibilidade humana, RAG padrão |
| `json` | Pós-processamento programático — inclui `polygon`, `section_hierarchy`, `block_type` por bloco |
| `html` | Renderização web |
| **`chunks`** | **Pré-segmentado para vector databases — output pronto para embedding, omite imagens** |

O formato `chunks` é o mais relevante para o pipeline do LTE: entrega o material já fatiado e pronto para ingestão no vector store, sem precisar de um pós-processador de chunking manual.

**Limitação**: o `chunks` é formato genérico — não respeita taxonomia jurídica. Para chunking com semântica de autos (Petição → Contestação → Decisão), ainda é necessário o `json` + pós-processador determinístico baseado em `section_hierarchy`. Os dois formatos têm casos de uso distintos.

### 2.8 Configuração Recomendada (próxima iteração)

```python
config = {
    "output_format": "json",          # Para consumo programático com section_hierarchy
    "paginate_output": True,           # Preserva referência de página
    "disable_image_extraction": True,  # Sem imagens base64
    "disable_image_captions": True,   # Sem captions (ruído)
    # bbox: não usar
    # force_ocr: apenas quando necessário
}
```

---

## 3. page_schema / Extração Estruturada

### O que é

Feature do Marker que, combinada com um LLM configurado (`--use_llm`), extrai campos estruturados segundo um schema JSON definido pelo usuário. O Marker faz o parse do PDF; o LLM lê o texto extraído e popula os campos do schema.

**Importante**: é o LLM que faz a extração estruturada, não o Marker sozinho. Sem LLM configurado, `page_schema` não funciona.

### Relevância para o LTE

Substitui o `step_04_classify.py` (Bibliotecário) com qualidade superior. Os campos extraídos ficam como frontmatter do documento — dados estruturados anexados ao chunk antes de ir para o embedding.

Exemplo de schema para autos TJSP:
```json
{
  "numero_processo": "string",
  "vara": "string",
  "juiz": "string",
  "requerente": "string",
  "requerido": "string",
  "valor_causa": "number",
  "data_distribuicao": "string"
}
```

### Status

- Via API e Marker local: schema definido manualmente.
- No playground do Datalab: existe inferência automática de schema (beta, não exposta via API).
- Custo no Modal: apenas GPU time, sem custo adicional de API se LLM for local (Ollama).

**Decisão**: deixar para próxima iteração. Prioridade atual é corrigir a arquitetura multi-GPU.

---

## 4. Por Que o Output é Monstruosamente Grande

Insight fundamental desta sessão:

> O Marker é o primeiro responsável pela qualidade do embedding. Não adianta transcrever perfeitamente se o output é um markdown de 300KB que o modelo de embedding não consegue processar adequadamente.

O que vai para o embedding não é o markdown bruto — é texto limpo extraído dos chunks, com metadados anexados. O `page_schema` + LLM resolve isso: gera um frontmatter estruturado com os dados essenciais do processo, reduzindo drasticamente o ruído semântico para o embedding.

---

## 5. Interface de Inspeção Visual — Conceito

### Motivação

O Datalab Playground tem uma feature crítica: split-pane mostrando o PDF original ao lado dos blocos classificados pelo Marker (SECTIONHEADER, TEXT, PageHeader, Table), com color coding por tipo. É impossível debugar o pipeline sem visibilidade de quais blocos o Marker está classificando e por quê.

Hoje: processar o auto, receber markdown de 300KB, sem visibilidade nenhuma.

### Conceito: "Penpot do Datalab Playground"

Mesma experiência de inspeção visual de blocos, mas:
- Rodando contra o Marker local/Modal (não a API do Datalab)
- Com os autos judiciais (documentos que não podem ir para nuvem de terceiros)
- Com features adicionais relevantes para o caso de uso jurídico

O dado já existe — o JSON do Marker tem `block_type`, `polygon`, `section_hierarchy`, `html` para cada bloco. É só a camada de visualização que falta.

### Features Essenciais

1. Split-pane: PDF original (esquerda) + blocos classificados (direita), sincronizados
2. Color coding por `block_type`
3. Filtros por tipo (esconder PageHeader = remove ruído de cabeçalho repetido)
4. Inspetor de bloco: tipo, página, hierarquia, conteúdo raw
5. Tabs: Blocks / JSON / Markdown / **Chunks** (preview do que vai para o embedding)
6. Painel de configuração: alterar params do Marker e reprocessar com diff de blocos
7. Upload → Modal → JSON de volta

### Features Adicionais (vs Playground do Datalab)

- Tab de Chunks com preview do embedding
- Comparação de configs (mesmo doc, dois configs, diff de blocos)
- `page_schema` com campos jurídicos pré-configurados para TJSP
- Funciona offline / sem enviar documentos para terceiros

### Stack e Roadmap Tecnológico

**Fase 1 — Laravel Web App**

Laravel + Livewire como frontend reativo. Backend cobre o que o front-end não pode fazer sozinho: upload do PDF, chamada ao endpoint do Modal, gerenciamento do job em background, broadcasting de progresso em tempo real via WebSocket. PDF renderer via `pdf.js` no browser, SVG overlay dos bounding boxes.

Vantagem imediata: sem builds, sem compilações, ciclo de iteração mais rápido. Claude Code tem cobertura excelente de Laravel — convenções claras, estrutura previsível, menos correção necessária.

**Fase 2 — NativePHP/Tauri Desktop (quando fizer sentido)**

NativePHP empacota o Laravel existente como app desktop via Tauri — sem reescrever nada, sem mudar stack. A codebase é a mesma. A decisão de empacotar como desktop fica para quando o produto estiver estável e validado.

Argumento adicional para desktop: autos judiciais são documentos sensíveis. Um app local que só faz chamadas ao Modal para OCR é proposta mais limpa do que aplicação web em servidor de terceiro.

```
Laravel web (fase 1, agora)
    ↓
NativePHP/Tauri desktop (fase 2, produto estável)
```

Esta é a direção tecnológica definida para o projeto.

---

## 6. Modelos do Datalab — Distinção Crítica

### Marker vs. Chandra — São Coisas Diferentes

| | Marker | Chandra |
|---|---|---|
| Tipo | Pipeline multi-modelo (orquestrador) | VLM end-to-end (Qwen-3-VL fine-tune, 9B params) |
| Licença | GPL-3.0 (código), OpenRAIL-M (pesos) | Apache 2.0 (código), OpenRAIL-M (pesos) |
| OCR interno | Surya | Próprio (VLM) |
| Benchmark olmOCR | 76.5 | 83.1 |
| Segmentação hierárquica | Não nativa | **Sim — necessário para isso** |

### Por que Chandra é necessário para segmentação hierárquica

A tab **Segment** do playground — que detecta hierarquia de seções entre páginas — usa Chandra, não Marker. O Marker extrai texto com qualidade, mas não tem capacidade nativa de entender estrutura hierárquica de seções ao longo de um documento inteiro.

Para o LTE, isso significa: **a separação hierárquica dos autos (Petição Inicial → Contestação → Decisão etc.) requer Chandra**, não Marker.

### Tiers do Datalab API

| Tier | Modelo | Uso recomendado |
|---|---|---|
| **Fast** | Chandra Small | Parse simples, documentos digitais limpos |
| **Balanced** | Chandra | Padrão — maioria dos casos |
| **Accurate** | Chandra + LLM correction + Agni | Máxima qualidade, hierarquia multi-página |

O modelo "faster" testado no playground e validado para autos do TJSP é o **Fast (Chandra Small)**.

### Implicação para o Pipeline Local (Modal)

Rodando Marker localmente via Modal: **sem segmentação hierárquica**. Para ter essa feature no pipeline próprio, é necessário:

- Usar a API do Datalab (paga), ou
- Rodar Chandra localmente (9B params, ~18GB VRAM FP16, ~10GB quantizado) via vLLM no Modal

Decisão pendente: qual das duas abordagens adotar para o LTE.

---

## 7. Notas sobre CCUI

CCUI é projeto separado — Tauri + Rust + React. Não confundir com o LTE. A interface de inspeção do LTE é um produto independente, não um canal do CCUI.

---

## Próximos Passos

1. **Imediato**: reescrever `modal_worker.py` — abandonar arquitetura multi-T4, adotar single GPU + múltiplos workers
2. **Próximo**: atualizar configuração do Marker com os parâmetros validados (sem bbox, sem image captions, paginate on)
3. **Futuro**: interface de inspeção visual
4. **Futuro**: `page_schema` com LLM local para frontmatter jurídico
