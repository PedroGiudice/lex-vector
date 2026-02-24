# Retomada: stj-vec -- Embedding em Massa via Modal

## Contexto rapido

O stj-vec e um sistema de busca vetorial sobre ~2M documentos juridicos do STJ. Cargo workspace Rust em `/home/opc/lex-vector/stj-vec/` com 3 crates (core, ingest, server) + scripts Modal Python. O core e ingest estao completos (27 testes passando). O server compila mas o /search depende de embeddings.

O modelo de embedding e o **BGE-M3** (1024 dims), rodando no **Modal com T4 GPU**. Ja foi testado com 3 chunks reais e funcionou perfeitamente (shape (3,1024), float32, normalizado). O modelo esta no Volume `stj-vec-models`, os scripts Modal em `stj-vec/modal/`.

A missao desta sessao: **embeddar todos os dados** (~857 sources, estimativa ~7M chunks). O processo e demorado e custoso -- minimizar interacao Claude Code, scriptar o maximo possivel.

## Arquivos principais

- `stj-vec/modal/embed.py` -- Modal Class com T4, `embed_source()` + `modal.map()` para escalar
- `stj-vec/modal/download_model.py` -- modelo ja baixado no Volume
- `stj-vec/crates/ingest/src/main.rs` -- CLI com export-chunks e import-embeddings
- `stj-vec/crates/ingest/src/exporter.rs` -- exporta chunks SQLite -> JSONL
- `stj-vec/crates/ingest/src/importer.rs` -- importa .npz -> SQLite vec_chunks
- `stj-vec/config.toml` -- dim=1024, provider=modal
- `docs/plans/2026-02-24-modal-embedding-service.md` -- plano (tasks 1-4 completas, task 5 pendente)
- `docs/contexto/24022026-stj-vec-modal-embedding.md` -- contexto detalhado

## Proximos passos (por prioridade)

### 1. Brainstorming rapido: multi-T4 vs GPU mais cara
**O que:** Sem gastar creditos -- apenas raciocinar com dados conhecidos. T4 (~60 emb/s, $0.59/h), A10G (~150 emb/s, $1.10/h), A100 (~400 emb/s, $2.50/h). Modal permite ate 8x T4 via modal.map(). Decidir configuracao final antes de rodar.
**Por que:** Evitar desperdicio de creditos com benchmark quando os numeros publicos ja sao suficientes para decidir.
**Resultado esperado:** Escolha definitiva de GPU e quantidade de containers para o run completo.

### 2. Scan + chunk de todos os sources
**Onde:** `stj-vec-ingest` na VM
**O que:**
```bash
cd /home/opc/lex-vector/stj-vec
cargo run --release -p stj-vec-ingest -- --config config.toml scan
cargo run --release -p stj-vec-ingest -- --config config.toml chunk
```
**Por que:** Precisa popular SQLite com todos os documents e chunks antes de exportar.
**Verificar:** `cargo run --release -p stj-vec-ingest -- --config config.toml stats` -- chunk_count deve ser >> 0

### 3. Export chunks para Modal Volume
**Onde:** VM + Modal
**O que:**
```bash
cargo run --release -p stj-vec-ingest -- --config config.toml export-chunks --output /tmp/stj-vec-chunks
modal volume put stj-vec-data /tmp/stj-vec-chunks/ /chunks/ --force
```
**Por que:** Chunks precisam estar no Volume para o Modal processar.
**Verificar:** `modal volume ls stj-vec-data /chunks/ | wc -l` -- deve ser ~857

### 4. Criar script shell de automacao
**Onde:** `stj-vec/scripts/run-embedding.sh`
**O que:** Script que encapsula: scan, chunk, export, upload, `modal run embed.py --all-pending`, download, import. Com logging, checkpoints, e tratamento de erros. Objetivo: usuario roda 1 comando e vai dormir.
**Por que:** Minimizar interacao Claude Code durante processo longo e custoso ($15-20 de credito Modal).
**Verificar:** Execucao do script com `--dry-run` (sem executar Modal)

### 5. Rodar embedding em massa
**Onde:** Modal (multi-T4 via modal.map)
**O que:** `modal run modal/embed.py --all-pending`
**Por que:** Gerar todos os embeddings de uma vez.
**Verificar:** `modal volume ls stj-vec-data /embeddings/ | wc -l` == numero de sources

### 6. Import embeddings
**Onde:** VM
**O que:**
```bash
modal volume get stj-vec-data /embeddings/ /tmp/stj-vec-embeddings/
cargo run --release -p stj-vec-ingest -- --config config.toml import-embeddings --input /tmp/stj-vec-embeddings
```
**Verificar:** `cargo run --release -p stj-vec-ingest -- --config config.toml stats` -- embedding_count >> 0, ingest_done >> 0

## Como verificar estado atual

```bash
cd /home/opc/lex-vector/stj-vec

# Branch
git branch --show-current  # work/stj-vec-design

# Testes (27 passando)
cargo test --workspace

# Modal Volumes
modal volume ls stj-vec-models  # bge-m3/ (modelo)
modal volume ls stj-vec-data    # chunks/test.jsonl, embeddings/test.npz (teste)

# Modal auth
modal profile current  # pedrogiudice
```

## Nota sobre custo e eficiencia

O usuario tem $30/mes de credito Modal. Multi-T4 (ate 8x) via `modal.map()` e a estrategia escolhida. Fazer um brainstorming rapido com numeros publicos para decidir GPU sem gastar creditos em benchmark. O embed.py ja suporta `--all-pending` que distribui automaticamente. O foco e scriptar para minimizar custo de contexto Claude Code.
