# Contexto: stj-vec -- Sessao 2 (Embedding Dense Completo + Preparacao Sparse)

**Data:** 2026-02-24
**Branch:** work/stj-vec-embedding-pipeline
**Sessao anterior:** docs/contexto/24022026-embedding-pipeline-execution.md

---

## O que foi feito

### 1. Benchmark de GPUs (tentativa)
Criado `modal/benchmark_gpu.py` pra comparar L4, A10G, A100 com batch sizes variados. Encontramos problemas com TEI (tags de compute capability, OOM, payload limits) que levaram a iterar rapidamente entre configs.

### 2. Migracao de sentence-transformers para TEI
Reescrevemos `modal/embed.py` de sentence-transformers (PyTorch vanilla) para TEI (Text Embeddings Inference) com flash attention e continuous batching. Throughput significativamente maior.

### 3. Iteracao de GPU/batch
| Config | Resultado |
|--------|-----------|
| 10x A100-40GB batch=512 (sessao 1) | 24% VRAM, desperdicio |
| 10x L4 TEI batch=256 | 16% VRAM, ETA 2h |
| 10x L4 TEI batch=1024 | 27% VRAM, ETA 16min |
| 10x L4 TEI batch=4096 | OOM |
| H200/B200 TEI | TEI nao tem kernels pra Blackwell/Hopper |
| H200 TEI hopper batch=4096 | FUNCIONA, muito rapido |

**Config final:** 10x H200 ($4.54/h) + TEI hopper-1.7 + batch=4096 + payload-limit=50MB.

### 4. Embedding dense COMPLETO
852/857 sources embeddados (5 vazios). ~13.5M embeddings. Custo estimado: ~$15-20.

### 5. Import pro SQLite
- Import Rust falhou em alguns .npz com "Invalid checksum" (crate zip mais estrita que Python zipfile)
- 203 sources importados pelo Rust antes de falhar
- Criado `scripts/import_embeddings.py` com numpy + sqlite-vec
- Import Python completou os 649 restantes
- 1 source com CRC bad (20230331) -- precisa re-download do Modal

### 6. Limpeza de disco
- Removido: .cache/uv (17GB), .cache/voice_ai (4.9GB), .cache/huggingface (4.8GB), .gradle (1.9GB), Picture-composer (746MB), /tmp/stj-vec-embeddings (40GB), /tmp/stj-vec-chunks (23GB)
- Disco: de 7.5GB livres para 47GB livres

### 7. Investigacao: TEI vs FlagEmbedding para sparse
**TEI NAO suporta sparse de BGE-M3.** `--pooling splade` exige arquitetura MaskedLM. BGE-M3 gera sparse via linear layer + ReLU, incompativel.

**Conclusao: FlagEmbedding e obrigatorio pra sparse.**

## Estado atual

| Item | Status |
|------|--------|
| Dense embedding (852 sources) | COMPLETO no Modal Volume |
| Dense import no SQLite | COMPLETO (exceto 20230331) |
| Sparse embedding | NAO INICIADO |
| embed_hybrid.py (FlagEmbedding) | CRIADO, nao testado |
| Busca dense-only | NAO TESTADA |
| Busca hibrida (dense+sparse) | NAO IMPLEMENTADA |

## Commits desta sessao

```
e78f0e6 chore(stj-vec): A100-40GB e batch_size=512 no embed.py
76be3b8 feat(stj-vec): reescreve embed.py com TEI + A100-80GB batch=1024
44f7ea9 fix(stj-vec): TEI image tag 80 para A100 (compute cap 80)
60c2894 fix(stj-vec): L4 TEI batch=2048 (4096 OOM, 1024 subutilizado)
14a20f5 feat(stj-vec): H200 TEI hopper batch=4096, embed_hybrid.py (FlagEmbedding)
9db629f chore(stj-vec): import script Python e prompt de cleanup VM
```

## Linear

- **CMR-46:** Benchmark 2x B200 para run sparse embedding (backlog, research)

## Decisoes

- **TEI > sentence-transformers** pra dense: flash attention, continuous batching, kernels CUDA otimizados
- **H200 + TEI hopper** e a melhor config disponivel (B200/Blackwell sem suporte TEI)
- **FlagEmbedding obrigatorio pra sparse**: TEI nao suporta sparse de BGE-M3
- **Python importer > Rust importer**: crate zip do Rust rejeita .npz validos

## Pendencias

1. **Re-download source 20230331** -- CRC bad no .npz, re-baixar do Modal e importar
2. **Smoke test busca dense-only** -- testar /search com embeddings reais
3. **Run sparse com embed_hybrid.py** -- testar 1 source, depois --all-pending
4. **Storage sparse no SQLite** -- tabela sparse_chunks, importer
5. **Busca hibrida** -- fusao dense+sparse no server
6. **Cleanup VM** -- prompt em docs/prompts/vm-cleanup.md
7. **Object Storage S3** -- configurar pra mover juridico-data (33GB)
