# Retomada: Pipeline Rust Unificado + Busca Decomposta STJ-Vec

<session_metadata>
branch: main
last_commit: a4bd8b8 (fix: timer Alpine.js)
commits_ahead_origin: 22
pending_uncommitted: isProcessDead (4 arquivos PHP)
failing_test: DecomposedSearchTest::poll (mock falta isProcessDead)
</session_metadata>

## Contexto rapido

Sessao de 2026-03-16 com foco em infraestrutura de dados e qualidade da busca do stj-vec (busca vetorial de jurisprudencia STJ).

O que foi feito: pipeline Rust unificado para download/ingest de dados do CKAN (Portal de Dados Abertos do STJ), chunker section-aware que respeita fronteiras EMENTA/VOTO/DECISAO, indice `processo_digits` para enrich O(log n), base atualizada ate 2026-03-13 com 13.47M pontos no Qdrant, pagina de inteiro teor no Laravel, correcao dos thresholds RRF na UI, prompt dual dense/sparse reforcado no agente decomposer, e remocao do crate server legado (sqlite-vec).

Ha 4 arquivos PHP modificados nao commitados (deteccao de processo morto no Livewire) com 1 teste falhando. 22 commits locais na main nao pushados para origin.

## Arquivos principais

- `stj-vec/docs/contexto/16032026-pipeline-unificado-e-busca-decomposta.md` -- contexto detalhado
- `stj-vec/docs/plans/rust-unified-pipeline.md` -- plano das 3 fases (completo)
- `stj-vec/crates/ingest/src/download.rs` -- cliente CKAN (manifest, retry, streaming)
- `stj-vec/crates/ingest/src/unzip.rs` -- extracao de ZIPs
- `stj-vec/crates/core/src/chunker.rs` -- chunker section-aware
- `stj-vec/crates/core/src/storage.rs` -- query processo_digits indexada
- `stj-vec/web/app/Livewire/DecomposedSearch.php` -- componente busca decomposta
- `stj-vec/web/app/Services/AgentRunnerInterface.php` -- interface com isProcessDead()
- `stj-vec/agent/prompts/decomposer.md` -- prompt SDK agent (dual dense/sparse)
- `~/.claude/agents/query-decomposer.md` -- prompt CLI agent (atualizado, fora do repo)

## Proximos passos (por prioridade)

### 1. Corrigir teste isProcessDead e commitar

**Onde:** `stj-vec/web/tests/Feature/DecomposedSearchTest.php`, metodo `mockRunner()`
**O que:** Adicionar `$mock->shouldReceive('isProcessDead')->andReturn(false)` ao mock helper. O mock nao inclui o novo metodo da interface.
**Por que:** 4 arquivos PHP modificados nao commitados, teste falha, bloqueia merge.
**Verificar:**
```bash
cd stj-vec/web && php artisan test --compact --filter=Decomposed
```

### 2. Push para origin

**Onde:** branch `main`
**O que:** `git push origin main` -- 22 commits locais
**Por que:** Trabalho significativo nao backupado no remote
**Verificar:**
```bash
git log --oneline origin/main..main | wc -l  # deve ser 0 apos push
```

### 3. Conectar Laravel BFF ao Tailscale Serve (HTTPS)

**Onde:** VM extractlab, Tailscale Serve config
**O que:** Expor porta 8082 via Tailscale Serve para acesso HTTPS. Porta 8000 esta reservada (extractor lab).
**Por que:** Acesso externo ao BFF sem HTTPS nao e pratico para uso real.
**Verificar:**
```bash
tailscale serve status
curl -s https://extractlab.cormorant-alpha.ts.net:<porta>/
```

### 4. Timer systemd para atualizacao automatica

**Onde:** `~/.config/systemd/user/stj-ingest-update.timer` + `.service`
**O que:** `stj-vec-ingest update --source espelhos` semanal + `stj-vec-ingest download --source integras` diario (so baixa novos via manifest)
**Por que:** Base precisa se manter atualizada sem intervenção manual
**Verificar:**
```bash
systemctl --user status stj-ingest-update.timer
journalctl --user -u stj-ingest-update.service --since today
```

### 5. Integrar TallStackUI no Laravel BFF

**Onde:** `stj-vec/web/`
**O que:** `composer require tallstackui/tallstackui` + configurar provider + substituir componentes manuais por componentes TallStackUI (tabelas, badges, loading, modais)
**Por que:** UI atual e funcional mas crua. TallStackUI integra com Livewire 4 nativamente.
**Verificar:**
```bash
cd stj-vec/web && php artisan test --compact
```

### 6. Gerar embeddings dos 5 sources pendentes

**Onde:** Modal (GPU)
**O que:**
```bash
modal run stj-vec/modal/embed_hybrid.py --source 20220810 --source 20230629 --source 20241001 --source 20241002 --source 20241014
```
Depois baixar e importar no Qdrant.
**Por que:** 5 sources sem embeddings desde sessoes anteriores. ~150k chunks faltando no Qdrant.
**Verificar:** Comparar `SELECT COUNT(*) FROM chunks` com pontos no Qdrant (devem convergir).

## Como verificar

```bash
# Ambiente funcional
cd /home/opc/lex-vector/stj-vec

# Rust compila
cargo check 2>&1 | tail -1
# "Finished `dev` profile"

# Testes Rust
cargo test -p stj-vec-core -p stj-vec-ingest 2>&1 | grep "test result"
# ok. 23 passed; ok. 27 passed

# Laravel testes (1 falha esperada -- isProcessDead mock)
cd web && php artisan test --compact
# 42 passed, 1 failed

# Server de busca rodando
curl -s http://localhost:8421/api/health | head -1

# Qdrant operacional
curl -s http://localhost:6333/collections/stj | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Points: {d[\"result\"][\"points_count\"]:,}, Status: {d[\"result\"][\"status\"]}')"
# Points: 13,470,848, Status: green

# Laravel BFF
curl -s http://localhost:8082/ | head -5

# Pipeline Rust disponivel
./target/release/stj-vec-ingest --help
```
