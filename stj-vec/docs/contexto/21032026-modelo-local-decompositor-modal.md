# Contexto: Modelo Local (Decompositor) no Modal

**Data:** 2026-03-21
**Sessao:** main (sem branch dedicado)
**Duracao:** ~4 horas

---

## O que foi feito

### 1. Pesquisa e decisao: modelo local pra substituir Sonnet no decompositor

Sessao iniciou com pesquisa do usuario sobre fine-tuning de modelos 70B pra tool calling. Conclusao: o decompositor e uma tarefa simples (query expansion, nao raciocinio complexo), viavel com modelo local. Fine-tune foi adiado -- testar modelo base primeiro.

### 2. Scripts Modal criados: serve_decomposer.py e test_decomposer.py

Dois scripts seguindo padrao do Chandra (extractor-lab):

- **`modal/serve_decomposer.py`**: App deployed no Modal com vLLM HTTP server, GPU snapshot (sleep/wake), `is_generator=True` pra manter container vivo durante agentic loop. Server executa buscas diretamente contra API Rust via IP publico (`217.76.48.35:8421`).
- **`modal/test_decomposer.py`**: Client Python puro via `Cls.from_name()` + `remote_gen()`. Consome generator do server e mostra progresso.

### 3. Teste com Qwen3-32B-FP8 na H100 -- FUNCIONOU

Primeiro modelo testado. Resultados promissores:

- 12 tool calls no round 1, boa alternancia formulaica/semantica
- Modelo usou vocabulario juridico do prompt (diploma consumerista, cessao de direitos, etc.)
- Thinking em ingles mas queries em portugues correto
- Inferencia: ~55s pra 1465 tokens output
- Tool calling formato Hermes funcional

### 4. Multi-turno com resultados reais -- FUNCIONAL MAS COM PROBLEMAS

Pipeline completo rodou: modelo gera queries -> server executa buscas na API Rust -> resultados retornados ao modelo -> proximo round.

**Problema critico identificado:** rounds 2-4 geram queries duplicatas verbatim do round 2. O modelo nao usa os tool results pra avaliar cobertura -- reinicia a decomposicao do zero a cada turno. Com MAX_ROUNDS=2, round 1 (12 queries) + round 2 (8 queries novas) = 20 queries unicas. Rounds 3-4 sao lixo identico ao 2.

### 5. Tentativas com modelos 72B -- TODAS FALHARAM

| Modelo | GPU | Problema |
|--------|-----|----------|
| `Qwen/Qwen3-72B-FP8` | H100 | NAO EXISTE no HuggingFace |
| `Qwen/Qwen3-72B-Instruct` | H200 | NAO EXISTE -- Qwen3 nao tem 72B |
| `Groq/Llama-3-Groq-70B-Tool-Use` | H200 | max_position_embeddings=8192 (Llama 3.0 base, nao 3.1) |
| `mesolitica/Qwen2.5-72B-Instruct-FP8` | H200 | Crash: `pure virtual method called`, `compressed-tensors` incompativel com vLLM 0.13.0 na H200 |
| `Qwen/Qwen2.5-72B-Instruct-GPTQ-Int8` | H200 | Crash: `XID 31 MMU Fault`, `CUDA illegal memory access` apos carregar 71.8GB. Tentado com gpu-memory-utilization 0.90 e 0.80, max-model-len 32768 e 16384. Mesmo erro. |

**NOTA IMPORTANTE:** Os crashes do Qwen2.5-72B na H200 NAO foram diagnosticados. Presumi "bug do vLLM" ou "OOM" sem confirmar. A causa real pode ser:
- Incompatibilidade vLLM 0.13.0 + H200 (Hopper vs novo hardware)
- GPTQ-Int8 Marlin kernel incompativel com H200
- Algo mais fundamental

**Acao necessaria na proxima sessao:** PESQUISAR E CONFIRMAR a causa antes de tentar de novo. Verificar issues do vLLM no GitHub pra H200 + GPTQ. Verificar se versao mais recente do vLLM resolve.

## Estado dos arquivos

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `modal/serve_decomposer.py` | Criado | Deploy Modal, vLLM HTTP + GPU snapshot + agentic loop + busca API Rust. **ESTADO ATUAL QUEBRADO**: configurado pra Qwen2.5-72B-Instruct-GPTQ-Int8 na H200 que nao funciona |
| `modal/test_decomposer.py` | Criado | Client Python puro, `Cls.from_name()` + `remote_gen()` |
| `agent/prompts/decomposer.md` | Pre-existente | System prompt do decompositor (12656 chars). Escrito pra Sonnet single-turn, funciona com Qwen3-32B mas nao pra multi-turno |

## Commits desta sessao

Nenhum commit feito. Tudo sao arquivos uncommitted/untracked.

## Decisoes tomadas

- **Modelo local em vez de API Anthropic pra decompositor**: custo zero por token, thinking ilimitado, controle total. Trade-off: qualidade inferior ao Sonnet mas aceitavel.
- **Fine-tune adiado**: testar modelo base primeiro, coletar dados organicamente, fine-tunar so se necessario. Custo estimado: ~$15-25 pra QLoRA num 72B com 1k exemplos.
- **vLLM HTTP (nao offline)**: necessario pra `--enable-auto-tool-choice` e `--tool-call-parser`. API offline nao suporta tool calling.
- **Server executa buscas diretamente (nao client)**: API Rust acessivel via IP publico `217.76.48.35:8421`. Elimina necessidade de Queue/generator bidirecional. Simplifica arquitetura.
- **Generator pattern (`is_generator=True`)**: mantém container vivo durante agentic loop. Sem isso, `scaledown_window=2` derruba container entre rounds.
- **MAX_ROUNDS=2**: rounds 3+ geram queries duplicatas. Round 1 (12 queries) + round 2 (8 novas) = 20 queries unicas e suficiente.
- **Qwen3 nao tem 72B**: lineup dense para em 32B. Qwen3-32B = equivalente ao Qwen2.5-72B em benchmarks (segundo Alibaba).

## Metricas (Qwen3-32B-FP8 na H100 -- unico teste completo)

| Metrica | Valor |
|---------|-------|
| Modelo | Qwen/Qwen3-32B-FP8 |
| GPU | H100 (80GB) |
| Cold start (primeiro, sem snapshot) | ~478s |
| Cold start (com snapshot) | nao testado nesta sessao |
| Inferencia round 1 | 55.26s |
| Inferencia round 2 | 45.64s |
| Tokens round 1 | 3842 in / 1465 out |
| Tokens round 2 | 14475 in / 924 out |
| Tool calls round 1 | 12 (todos unicos, boa qualidade) |
| Tool calls round 2 | 8 (novos, boa qualidade) |
| Tool calls rounds 3-4 | 8+8 (duplicatas verbatim do round 2) |
| Buscas executadas (API Rust) | ~6s pra 12 buscas paralelas |
| Custo H100 Modal | ~$3.50/h |
| Custo H200 Modal | ~$4.54/h |

## Pendencias identificadas

1. **PESQUISAR causa do crash Qwen2.5-72B na H200** (alta) -- nao presumir. Verificar issues vLLM GitHub, testar vLLM versao mais recente, verificar compatibilidade H200 + GPTQ Marlin.
2. **Resolver multi-turno: modelo nao itera com base nos resultados** (alta) -- 3 abordagens propostas: (a) user message de coaching entre rounds, (b) resumo programatico dos resultados, (c) ambos. Nenhuma implementada.
3. **Voltar serve_decomposer.py pro Qwen3-32B-FP8/H100 funcional** (alta) -- estado atual esta configurado pra modelo que nao roda.
4. **Adicionar web endpoint alem do modal.method** (media) -- usuario pediu. vLLM ja serve OpenAI-compatible, so precisa expor a porta.
5. **Consolidacao de resultados no output final** (media) -- codigo de dedup por doc_id e ranking por RRF ja esta implementado no server mas nao foi testado end-to-end.
6. **Explorar Llama 4 Maverick (MoE) como alternativa** (baixa) -- suporte nativo tool calling, mas precisa de `--tool-call-parser pythonic` e template customizado.
7. **Registrar milestone no Linear** (baixa) -- "Modelo local pra decompositor" como milestone no projeto stj-vec.
