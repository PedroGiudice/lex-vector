# Retomada: Analise de Qualidade -- CLI vs SDK, Queries e Resultados

## Contexto rapido

CLI e SDK drivers funcionam end-to-end. CLI usa `--strict-mcp-config` com 1 MCP server, JSONL extraction para dados estruturados, e instrucao de JSON no `-p`. SDK usa API direta via Bun. Ambos retornam resultados da base vetorial STJ (13.47M pontos Qdrant).

Proxima sessao: comparar qualidade dos resultados entre os dois metodos, iterar prompts do agente decompositor, melhorar organizacao das respostas.

<session_metadata>
branch: main
last_commit: 41916a7
tests_passing: 55
services: stj-search-rust (8421) + stj-search-web (8082)
public_url: https://extractlab.cormorant-alpha.ts.net:8443/
</session_metadata>

## Arquivos principais

- `stj-vec/web/app/Services/AgentRunner.php` -- CLI driver com JSONL extraction
- `stj-vec/web/app/Services/SdkAgentRunner.php` -- SDK driver (Bun + decompose.ts)
- `stj-vec/agent/src/decompose.ts` -- SDK agent TypeScript
- `~/.claude/agents/query-decomposer.md` -- CLI agent prompt (Opus)
- `~/.claude/plugins/marketplaces/opc-plugins/plugins/stj-vec-tools/server.mjs` -- MCP plugin com retry
- `stj-vec/web/app/Livewire/DecomposedSearch.php` -- Livewire component
- `stj-vec/web/resources/views/livewire/decomposed-search.blade.php` -- UI template
- `docs/contexto/19032026-cli-mcp-fix-e-jsonl-extraction.md` -- contexto detalhado

## Proximos passos

### 1. Comparar resultados CLI vs SDK

**O que:** Rodar a mesma query em ambos os drivers e comparar:
- Quantidade de resultados unicos
- Cobertura de angulos/perspectivas
- Relevancia dos top-10 resultados
- Tempo de execucao
- Custo (CLI = subscription, SDK = API billing)

**Queries de teste sugeridas:**
- "inaplicabilidade CDC contrato de licenciamento de software"
- "dano moral banco negativacao indevida"
- "responsabilidade objetiva concessionaria servico publico"

**Verificar:**
```bash
cd ~/lex-vector/stj-vec/web
# CLI test
php artisan tinker --execute="
config(['services.agent.model' => 'opus']);
\$r = new \App\Services\AgentRunner;
\$r->start('compare-cli-'.time(), 'dano moral banco');
"
# SDK test
php artisan tinker --execute="
\$r = new \App\Services\SdkAgentRunner;
\$r->start('compare-sdk-'.time(), 'dano moral banco');
"
```

### 2. Iterar prompt do decompositor

**Onde:** `~/.claude/agents/query-decomposer.md` e `stj-vec/agent/prompts/decomposer.md`
**O que:** Com base na comparacao, ajustar:
- Numero minimo de buscas (atualmente 3)
- Estrategia de variacao de queries (formulaico vs semantico)
- Tratamento de resultados duplicados
- Formato de output (JSON schema)

### 3. Melhorar organizacao visual dos resultados

**Onde:** `decomposed-search.blade.php`
**O que:** Os resultados agrupados por angulo precisam de:
- Melhor label de angulo (atualmente mostra a query crua)
- Score visual (barra de relevancia)
- Link para inteiro teor
- Metadados (ministro, turma, data)

### 4. Resolver theming TOML (pendente)

**Onde:** `app/Services/Theme/ThemeService.php`
**O que:** CSS variables nao sao aplicadas. Debug: verificar se `cssVariables()` gera output correto.

## Como verificar

```bash
cd ~/lex-vector/stj-vec/web
php artisan test --compact           # 55 testes
systemctl --user status stj-search-web stj-search-rust
curl -s http://localhost:8421/api/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'])"
```
