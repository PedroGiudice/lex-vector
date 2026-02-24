# Retomada: stj-vec -- Pos-Embedding e Pipeline Sparse

## Contexto rapido

O stj-vec e um sistema de busca vetorial sobre ~2.1M documentos juridicos do STJ (13.5M chunks). Cargo workspace Rust em `/home/opc/lex-vector/stj-vec/` com 3 crates (core, ingest, server) + scripts Modal Python. 27 testes passando.

O embedding dense (BGE-M3, 1024d) de todos os 857 sources foi lancado no Modal com 10x A100-40GB (batch_size=512). **Verificar se terminou antes de qualquer coisa.** Os embeddings ficam no Volume `stj-vec-data` em `/embeddings/`. O flag `--all-pending` permite retomar se nao terminou.

Apos o dense, o proximo passo e implementar sparse embeddings (FlagEmbedding) e busca hibrida. Design doc aprovado em `docs/design-docs/2026-02-24-stj-vec-embedding-pipeline.md`.

## Arquivos principais

- `stj-vec/modal/embed.py` -- Modal Class A100-40GB, batch=512, sentence-transformers (dense only)
- `stj-vec/crates/core/src/storage.rs` -- schema SQLite (precisa tabela sparse_chunks)
- `stj-vec/crates/ingest/src/importer.rs` -- importa .npz (precisa adaptar pra .sparse.json)
- `stj-vec/crates/server/src/routes.rs` -- rota /search (precisa busca hibrida)
- `stj-vec/config.toml` -- dim=1024, provider=modal
- `docs/design-docs/2026-02-24-stj-vec-embedding-pipeline.md` -- design completo
- `docs/prompts/2026-02-24-embedding-pipeline-execution.md` -- plano 9 passos original
- `docs/contexto/24022026-embedding-pipeline-execution.md` -- contexto detalhado

## Proximos passos (por prioridade)

### 1. Verificar se embedding dense terminou
**O que:** Checar se todos os 857 sources foram embeddados no Modal.
**Verificar:**
```bash
modal volume ls stj-vec-data /embeddings/ | grep -c ".npz"
# Deve ser 857. Se < 857:
cd /home/opc/lex-vector/stj-vec && modal run modal/embed.py --all-pending
```

### 2. Download e import dos embeddings dense
**O que:** Baixar .npz e .json do Volume, importar no SQLite via CLI.
```bash
modal volume get stj-vec-data /embeddings/ /tmp/stj-vec-embeddings/
cd /home/opc/lex-vector/stj-vec
nohup cargo run --release -p stj-vec-ingest -- --config config.toml import-embeddings --input /tmp/stj-vec-embeddings > /tmp/import.log 2>&1 &
```
**Verificar:** `sqlite3 db/stj-vec.db "SELECT count(*) FROM vec_chunks;"` -- deve ser ~13.5M

### 3. Commit das mudancas pendentes
**Onde:** Branch `work/stj-vec-embedding-pipeline`
**O que:** gpu A100-40GB e batch_size=512 no embed.py, atualizacao design doc.
```bash
cd /home/opc/lex-vector && git add -A && git commit -m "chore(stj-vec): A100-40GB e batch_size=512 no embed.py"
```

### 4. Smoke test busca dense-only
**O que:** Testar /search do server com embeddings dense. Precisa de um embedder funcional pra queries -- o server usa NoopEmbedder agora. Implementar OllamaEmbedder (BGE-M3 local via Ollama) pra queries em tempo real, ou chamar Modal pra embed de query.
**Verificar:** `curl -X POST localhost:8421/search -d '{"query":"recurso especial provido"}'`

### 5. Implementar sparse no embed.py (FlagEmbedding)
**Onde:** `stj-vec/modal/embed.py`
**O que:** Trocar sentence-transformers por FlagEmbedding. Gerar dense + sparse numa chamada. Output adicional: `{source}.sparse.json`. Converter token_ids pra texto via tokenizer.
**Por que:** Busca por termos exatos ("art. 1.022", "provido", "deferido") precisa de sparse.
**Consideracao GPU:** Avaliar 2x B200 com batch_size=2048 (192GB VRAM). Cold start e ~5s com Volume. Custo estimado ~$28 pra todo o corpus.

### 6. Storage e importer sparse
**Onde:** `stj-vec/crates/core/src/storage.rs`, `stj-vec/crates/ingest/src/importer.rs`
**O que:** Tabela `sparse_chunks(chunk_id, token, weight)` com indices. Importer le .sparse.json. Filtro de peso minimo (descartar weight < 0.01) pra controlar tamanho.

### 7. Busca hibrida no server
**Onde:** `stj-vec/crates/server/src/routes.rs`
**O que:** Query gera dense + sparse, busca nos dois, fusao `score = w * dense + (1-w) * sparse`. Peso configuravel em config.toml.

### 8. Re-ranker (fase 2)
**O que:** Serafim 335M ou cross-encoder Legal-BERTimbau em CPU sobre top-k candidatos.

## Como verificar estado atual

```bash
cd /home/opc/lex-vector/stj-vec

# Branch e mudancas pendentes
git status

# Testes (27 passando)
cargo test --workspace

# Modal - embeddings completados
modal volume ls stj-vec-data /embeddings/ | grep -c ".npz"

# DB stats (pode ser lento com DB grande)
sqlite3 db/stj-vec.db "SELECT count(*) FROM documents; SELECT count(*) FROM chunks;"

# Disco -- /tmp pode ter 23GB de JSONL pra limpar
du -sh /tmp/stj-vec-chunks/ /tmp/stj-vec-embeddings/ 2>/dev/null

# Modal auth e creditos
modal profile current
```

## Nota sobre custos Modal

O usuario tem cartao cadastrado alem dos $30/mes free. Run dense com 10x A100-40GB batch=512 custou ~$17 (ETA 49min).

## Analise pendente: otimizacao de GPU pra run sparse

**IMPORTANTE: o run dense usou batch_size=512 numa A100 com 40GB de VRAM -- apenas 24% de utilizacao. Isso e desperdicio.** O conteudo juridico e denso e os chunks variam em tamanho/densidade, o que afeta throughput real.

Antes do run sparse, fazer uma analise matematica comparando:

**Opcao A: GPU forte, poucos containers, batch enorme**
- Ex: 2-4x B200 (192GB VRAM), batch_size=2048-4096
- Menos containers = menos overhead, GPU saturada

**Opcao B: GPU fraca, muitos containers, batch menor**
- Ex: 8-12x L4 (24GB) ou A10 (24GB), batch_size=512-1024
- Mais paralelismo, GPU mais barata

Considerar: throughput real por GPU (nao estimativas de benchmark), custo/h, overhead de modal.map(), variacao de tamanho dos chunks (sources de 41 a 372K chunks), e que o FlagEmbedding (dense+sparse) e mais pesado que sentence-transformers (dense only).

**Rodar benchmark real** de 1 source (~15K chunks) em cada config antes de lancar o run completo. Medir emb/s e VRAM real, nao estimar.

## Nota: embedding dense possivelmente incompleto

O run dense (10x A100, batch=512) tinha ETA ~49min mas pode nao ter terminado antes da sessao encerrar. Verificar primeiro (passo 1 acima). O `--all-pending` retoma de onde parou.
