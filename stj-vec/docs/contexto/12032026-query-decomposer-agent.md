# Contexto: Agente de Decomposicao de Query + Plugin MCP stj-vec-tools

**Data:** 2026-03-12/13
**Sessao:** main (continuacao de 11032026)
**Duracao:** ~4h

---

## O que foi feito

### 1. Enrich Qdrant -- payload de metadados propagados

O script `enrich_qdrant_payload.py` (da sessao anterior) completou:
- 13,485,051 pontos processados em 19,202s (702 pts/s)
- Todos os 7 payload indexes criados com sucesso (timeouts HTTP normais, criacao assincrona)

Estado final dos indexes:

| Index | Tipo | Pontos |
|-------|------|--------|
| doc_id | keyword | 13,442,327 |
| chunk_index | integer | 13,442,327 |
| secao | keyword | 13,440,118 |
| classe | keyword | 13,257,844 |
| tipo | keyword | 13,436,968 |
| orgao_julgador | keyword | 4,312,896 |
| data_julgamento | keyword | 3,315,397 |

Collection status: green, queue: 0. Pre-filtering operacional.

### 2. Testes de modelos locais para decomposicao de query

Testamos modelos Ollama (CPU, 16 vCPUs EPYC) para verificar se um modelo pequeno
consegue fazer decomposicao juridica autonomamente.

Query teste: "inaplicabilidade CDC contrato de licenciamento de software pronto para uso"

| Modelo | Params | Tempo | Resultado |
|--------|--------|-------|-----------|
| qwen2.5:0.5b | 500M | 29s | Lixo -- quebrou query em tokens isolados |
| qwen2.5:1.5b | 1.5B | 23s | Repetiu query com labels diferentes. Interpretou "angle" como graus |
| qwen2.5:3b (zero-shot) | 3.1B | 27s | 3 sub-queries superficiais, confundiu CDC com "Consolidacao do Direito Civil" |
| qwen2.5:3b (few-shot) | 3.1B | ~15s | 3 sub-queries melhores mas angulos fracos |
| qwen2.5:3b (angulos dados) | 3.1B | ~15s | 5 sub-queries boas MAS so preencheu template fornecido |

**Conclusao:** nenhum modelo ate 3B consegue decomposicao juridica autonoma.
O 3B e "template filler" -- segue angulos que voce da, nao identifica quais sao relevantes.
Nao entende o dominio (confunde CDC, nao identifica perspectivas juridicas).

**Decisao:** Claude Code headless (`claude --agent`) e o caminho.

### 3. Debate sobre runtime do agente

Opcoes avaliadas:

| Opcao | Custo | Latencia | Embutivel | Decisao |
|-------|-------|----------|-----------|---------|
| Claude Code CLI (`--agent`) | $0 (plano Max) | 3-8s | Nao (subprocess VM) | **Adotado para V1** |
| API Anthropic (SDK) | ~$3/mes Haiku | 0.5-2s | Sim (HTTP direto) | Milestone futuro (CMR) |
| Modal (modelo dedicado) | $0.10-0.50/h GPU | 1-3s | Sim (endpoint HTTP) | Descartado |
| Modelo local (Ollama) | $0 | 15-30s CPU | Sim | **Descartado** (qualidade insuficiente) |

**Milestone Linear registrado:** "SDK Agent (Anthropic API) para query decomposition"
-- migrar de CC headless para SDK quando validado.

### 4. Plugin MCP stj-vec-tools

Criado plugin no marketplace opc-plugins com 3 tools MCP:

- **search** -- busca vetorial hibrida (proxy para Rust API localhost:8421/api/search)
- **document** -- busca documento por doc_id (proxy para /api/document/{doc_id})
- **filters** -- lista filtros disponiveis (proxy para /api/filters)

Server MCP testado end-to-end (tools/list + tool call search com resultados reais).

Plugin instalado no projeto lex-vector (scope: project).

### 5. Agente query-decomposer

Criado `stj-vec/agents/query-decomposer.md` com:

- Tools restritas: apenas as 3 MCP tools do stj-vec-tools (sem Bash, sem filesystem)
- Processo: analisar query -> gerar 3-6 sub-queries por angulo juridico -> buscar -> avaliar -> refinar
- Limites: max 3 rounds, min 10 resultados, max 30, dedup por doc_id
- Output: JSON estruturado com decomposicao + resultados
- Restricoes: proibido citar artigos de lei, fundamentar, opinar

**NAO TESTADO AINDA** -- o agente foi criado e o plugin instalado, mas nao houve teste
end-to-end do `claude --agent` com as MCP tools.

## Estado dos arquivos

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `stj-vec/agents/query-decomposer.md` | Criado | Agente com MCP tools |
| `~/.claude/plugins/.../stj-vec-tools/server.mjs` | Criado | MCP server Node.js (3 tools) |
| `~/.claude/plugins/.../stj-vec-tools/.mcp.json` | Criado | Config stdio |
| `~/.claude/plugins/.../stj-vec-tools/package.json` | Criado | Deps: @modelcontextprotocol/sdk, zod |
| `~/.claude/plugins/.../opc-plugins/marketplace.json` | Modificado | +stj-vec-tools entry |
| `~/.claude/plugins/installed_plugins.json` | Modificado | Plugin instalado scope=project |

## Decisoes tomadas

- **Modelos locais descartados para decomposicao**: qualidade insuficiente ate 3B. Nao identificam angulos juridicos autonomamente. Nao entendem dominio (confundem CDC)
- **Claude Code headless como V1**: custo zero (plano Max), qualidade garantida, subprocess via Laravel `Process::run()`
- **SDK Agent como evolucao futura**: custo aceitavel (~$3/mes Haiku), latencia melhor, embutivel. Mas prematura antes de validar o agente
- **Plugin MCP em vez de Bash**: sandboxing -- agente so tem acesso as 3 tools de busca, nao ao filesystem
- **Agente NAO cita direito**: restricao estrutural. So retorna resultados da API. Previne alucinacao juridica
- **3 rounds max com min 10 resultados**: pragmatismo entre qualidade e tempo
- **Step 0 (engenharia pura) confirmado como insuficiente**: expansao por dicionario dilui sinal raro, stopwords estaticas perigosas, nao identifica angulos

## Metricas

| Metrica | Valor |
|---------|-------|
| Qdrant collection size | 13,442,327 pontos |
| Payload indexes | 7/7 completos (green) |
| Enrich duration | 19,202s (~5.3h) |
| Enrich rate | 702 pts/s |
| Modelos Ollama testados | 3 (0.5b, 1.5b, 3b) |
| Melhor tok/s CPU | 14.4 (0.5b) |
| Plugin MCP tools | 3 (search, document, filters) |

## Pendencias identificadas

1. **Testar agente query-decomposer end-to-end** (alta) -- `claude --agent stj-vec/agents/query-decomposer.md -p "query"` com MCP tools ativas
2. **Validar output JSON do agente** (alta) -- confirmar que Sonnet segue o schema de output
3. **Integrar no Laravel BFF** (media) -- `Process::run()` no SearchController, parse JSON, exibir
4. **Cleanup modelos Ollama** (baixa) -- qwen2.5 0.5b/1.5b/3b consomem ~3.3GB em disco, nao serao usados
5. **Commit dos arquivos da sessao** (alta) -- agente e documentos nao commitados
