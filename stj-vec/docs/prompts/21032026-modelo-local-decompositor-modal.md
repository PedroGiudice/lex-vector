# Retomada: Modelo Local (Decompositor) no Modal

## Contexto rapido

Estamos construindo um decompositor de queries juridicas que roda num modelo local (open source) no Modal, substituindo o Claude Sonnet no pipeline de busca do stj-vec. O objetivo: zero custo de API, thinking ilimitado, controle total.

O pipeline funciona end-to-end com Qwen3-32B-FP8 na H100: modelo gera tool calls, server Modal executa buscas na API Rust (via IP publico), resultados retornados ao modelo. Problema: multi-turno nao funciona -- o modelo repete queries em vez de avaliar resultados e refinar.

Tentamos escalar pra 72B (Qwen2.5-72B-Instruct-GPTQ-Int8) na H200 mas falhou com crashes CUDA. A causa NAO foi diagnosticada -- **pesquisar antes de tentar de novo**.

## Arquivos principais

- `stj-vec/modal/serve_decomposer.py` -- app Modal deployed. **ATENCAO: estado atual configurado pra Qwen2.5-72B que NAO funciona. Reverter pra Qwen3-32B-FP8 + H100 antes de rodar.**
- `stj-vec/modal/test_decomposer.py` -- client Python, `Cls.from_name()` + `remote_gen()`
- `stj-vec/agent/prompts/decomposer.md` -- system prompt (funciona com Qwen3-32B mas nao pra multi-turno)
- `stj-vec/agent/src/decompose.ts` -- decompositor atual com Sonnet (referencia de como o agentic loop funciona)
- `docs/contexto/21032026-modelo-local-decompositor-modal.md` -- contexto detalhado desta sessao

## Proximos passos (por prioridade)

### 1. Reverter serve_decomposer.py pro config funcional
**Onde:** `stj-vec/modal/serve_decomposer.py`, linhas de config no topo
**O que:** Trocar MODEL_NAME pra `Qwen/Qwen3-32B-FP8`, GPU_TYPE pra `h100`, remover `--quantization`, restaurar `--max-model-len 32768`, `--gpu-memory-utilization 0.90`
**Por que:** Estado atual esta configurado pra modelo que crasha
**Verificar:** `modal deploy modal/serve_decomposer.py && python3 modal/test_decomposer.py "dano moral bancario"`

### 2. PESQUISAR causa dos crashes do 72B na H200
**Onde:** GitHub issues do vLLM, documentacao Modal sobre H200
**O que:** Buscar `vLLM H200 GPTQ`, `vLLM 0.13.0 H200 XID 31`, `CUDA illegal memory access H200 vLLM`. Verificar se vLLM 0.14+ ou 0.17+ resolve. Verificar se H200 precisa de CUDA 12.9+. Verificar se o problema e especifico de GPTQ-Int8 ou se FP8 pre-quantizado tambem falha.
**Por que:** Presumimos "bug" sem confirmar. Pode ser config errada, versao de CUDA, ou limitacao real.
**Verificar:** Encontrar issue confirmando o problema ou solucao

### 3. Resolver multi-turno: modelo nao itera com resultados
**Onde:** `stj-vec/modal/serve_decomposer.py`, metodo `decompose()`, entre rounds
**O que:** Implementar opcao 3 discutida na sessao: (a) gerar sumario programatico dos resultados entre rounds ("8/12 queries retornaram 5+ resultados, angulos cobertos: X, Y, Z, gaps: A, B"), (b) injetar como user message de coaching antes do round 2 ("Analise os resultados acima. Quais angulos NAO foram cobertos? NAO repita queries.")
**Por que:** Modelo 32B nao consegue processar tool results longos em JSON e reinicia decomposicao do zero
**Verificar:** Round 2 gera queries DIFERENTES do round 1 e complementares

### 4. Pesquisar e testar Qwen2.5-72B-Instruct na H200 (apos resolver passo 2)
**Onde:** `stj-vec/modal/serve_decomposer.py`
**O que:** Baseado na pesquisa do passo 2, tentar novamente com a solucao correta (versao vLLM diferente, FP8 em vez de GPTQ, ou outro checkpoint)
**Por que:** 72B deve ter instruction following melhor que 32B, especialmente pra multi-turno
**Verificar:** Modelo carrega, warmup funciona, tool calling gera queries

### 5. Adicionar web endpoint OpenAI-compatible
**Onde:** `stj-vec/modal/serve_decomposer.py`, classe DecomposerService
**O que:** Adicionar `@modal.web_server(port=VLLM_PORT)` pra expor o vLLM HTTP diretamente. Qualquer client pode chamar `/v1/chat/completions`.
**Por que:** Usuario pediu. Permite uso generico do modelo alem do decompositor.
**Verificar:** `curl https://<url>/v1/models` retorna o modelo

## Dados uteis pra proxima sessao

### Config funcional comprovada (Qwen3-32B-FP8 + H100)

```python
GPU_TYPE = "h100"
MODEL_NAME = "Qwen/Qwen3-32B-FP8"
# vLLM args:
"--dtype", "auto",
"--gpu-memory-utilization", "0.90",
"--enable-auto-tool-choice",
"--tool-call-parser", "hermes",
"--max-num-seqs", "16",
"--max-model-len", "32768",  # Qwen3 suporta nativamente
"--enforce-eager",  # troca throughput por boot rapido
"--enable-sleep-mode",
```

### API Rust acessivel externamente

```
http://217.76.48.35:8421/api/search  (IP publico da VM Contabo)
http://217.76.48.35:8421/api/filters
```

### Modelos descartados e motivos

| Modelo | Motivo |
|--------|--------|
| Qwen3-72B (qualquer) | NAO EXISTE. Qwen3 max dense = 32B |
| Groq/Llama-3-Groq-70B-Tool-Use | Contexto 8192 tokens (Llama 3.0, nao 3.1) |
| mesolitica/Qwen2.5-72B-Instruct-FP8 | Crash C++ no vLLM 0.13.0 (compressed-tensors + H200) |
| Qwen2.5-72B-Instruct-GPTQ-Int8 | XID 31 MMU Fault + CUDA illegal memory access na H200 |

### Precos GPU Modal (referencia)

| GPU | Preco/hora |
|-----|-----------|
| H100 | ~$3.50 |
| H200 | ~$4.54 |
| B200 | ~$6.25 |

## Como verificar

```bash
# 1. API Rust funcionando
curl -s http://localhost:8421/api/filters | head -c 100

# 2. Reverter config e deploy
# (editar serve_decomposer.py primeiro -- ver passo 1)
modal deploy stj-vec/modal/serve_decomposer.py

# 3. Testar decompositor
python3 stj-vec/modal/test_decomposer.py "inaplicabilidade CDC contrato licenciamento software"
```

<session_metadata>
branch: main
last_commit: 41916a7 (pre-existente, nenhum commit nesta sessao)
pending_files: modal/serve_decomposer.py, modal/test_decomposer.py (uncommitted)
blocker: serve_decomposer.py configurado pra modelo que crasha -- reverter antes de usar
</session_metadata>
