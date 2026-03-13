# Contexto: Teste End-to-End do Agente Query-Decomposer + Engenharia de Prompt

**Data:** 2026-03-13
**Sessao:** work/query-decomposer-docs (continuacao de 12032026)
**Duracao:** ~2h

---

## O que foi feito

### 1. Movido agente para diretorio global

Agente `query-decomposer.md` movido de `stj-vec/agents/` para `~/.claude/agents/`.
Regra firmada: TODOS os agentes devem ser globais.

### 2. Teste end-to-end do agente com 3 modelos

Query de teste: "inaplicabilidade CDC contrato de licenciamento de software pronto para uso"

Resultados comparativos:

| Metrica | Haiku | Sonnet | Opus |
|---------|-------|--------|------|
| Tool uses | **0** (fabricou tudo) | 6 | 8 |
| Resultados | 16 (FALSOS) | 17 | 32 |
| Angulos | 6 | 6 | 8 |
| Rounds | 2 | 2 | 2 |
| Tokens | 20k | 71k | 91k |
| Tempo | 35s | 151s | 156s |
| Dados reais | Nao | Sim | Sim |

**Haiku fabricou jurisprudencia inteira:** zero tool calls, doc_ids inventados (formato errado),
scores artificiais redondos (0.87 vs reais tipo 0.45594978), ministros inexistentes
("Ministra Gisele Fonseca"), content_preview gerado (nao copiado da base).
Isso aconteceu MESMO com prompt explicitando "NAO inventa". Haiku nao tem capacidade
de tool-use disciplinado para esta tarefa.

**Sonnet** funcionou corretamente: 6 buscas reais, 17 resultados dedupados, dados autenticos.
Leading cases corretos (REsp 1554403, AREsp 3071046).

**Opus** foi superior: 8 angulos (vs 6 do Sonnet), 32 resultados unicos, incluiu angulos extras
(Lei 9.609/98, cessao de direitos/rescisao contratual) que Sonnet nao explorou.

### 3. Adicionada secao de engenharia de queries ao prompt

Secao "Construir queries efetivas" adicionada ao agente com 4 sub-secoes:

1. **Como o STJ escreve** -- frases formulaicas reais extraidas da base (ex: "destinatario final da relacao de consumo", "teoria finalista mitigada", "diploma consumerista")
2. **Sinonimos que trazem resultados diferentes** -- pares de termos que ativam chunks diferentes (CDC/Codigo de Defesa do Consumidor/diploma consumerista/Lei 8.078)
3. **Tamanho ideal da query** -- 5-10 palavras como ponto otimo
4. **O que NAO fazer** -- anti-padroes reais observados no teste Haiku (termos em ingles, portugues de Portugal, linguagem natural)

Vocabulario extraido de buscas reais na legal-knowledge-base e na base STJ, nao inventado.

### 4. Problema do filtro tipo=ACORDAO

Filtro `tipo: "ACORDAO"` eliminou todos os 9 candidatos (pre_filter=9, post_filter=0).
O valor do campo `tipo` na base e "ACORDAO" (uppercase sem acento), mas o matching pode
ser case-sensitive. Investigar se o payload index keyword e case-sensitive no Qdrant.

### 5. Commit na branch work/query-decomposer-docs

Commit `a185489` com docs de contexto e prompt da sessao anterior (12032026).

## Estado dos arquivos

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `~/.claude/agents/query-decomposer.md` | Modificado (global) | +secao engenharia de queries, +limites ajustados |
| `stj-vec/agents/query-decomposer.md` | Deletado | Movido para global |
| `stj-vec/docs/contexto/12032026-*.md` | Commitado | a185489 |
| `stj-vec/docs/prompts/12032026-*.md` | Commitado | a185489 |
| `~/.claude/projects/.../memory/feedback_agents_global.md` | Criado | Memoria: agentes sempre globais |
| `~/.claude/projects/.../memory/MEMORY.md` | Modificado | +secao Feedback |

## Commits desta sessao

```
a185489 docs(stj-vec): contexto e prompt do agente query-decomposer
```

## Decisoes tomadas

- **Haiku descartado para query-decomposer**: fabrica resultados inteiros sem chamar tools. Problema de capacidade do modelo, nao de prompt | Descartado: ajustar prompt para Haiku (tentado, nao resolveu)
- **Sonnet como piso, Opus como teto**: Sonnet funciona, Opus e melhor (mais angulos, mais resultados). Default mantido em `model: sonnet` no frontmatter
- **Agentes sempre globais**: `~/.claude/agents/`, nunca em diretorios locais | Motivo: consistencia, acessibilidade cross-projeto
- **Vocabulario juridico assado no prompt**: em vez de consultar legal-knowledge-base em runtime (latencia), extrair termos e embuti-los no system prompt

## Metricas

| Metrica | Valor |
|---------|-------|
| Qdrant status | green, 13,442,327 pontos |
| API Rust (8421) | operacional |
| Plugin MCP stj-vec-tools | 3 tools, operacional |
| Tempo Sonnet end-to-end | ~151s |
| Tempo Opus end-to-end | ~156s |
| Tempo Haiku end-to-end | ~35s (mas fabricou tudo) |

## Pendencias identificadas

1. **Testar Haiku novamente com prompt v2 completo** (media) -- o teste Haiku v2 usou prompt atualizado mas Haiku pode ter ignorado tools por bug de MCP/subagente. Testar via `claude --agent` CLI para eliminar variavel
2. **Investigar filtro tipo=ACORDAO** (media) -- retornou 0 resultados pos-filtro. Verificar case-sensitivity do payload index keyword no Qdrant
3. **Testar com queries de outros temas** (alta) -- ate agora so testamos CDC/software. Testar com: dano moral, responsabilidade civil, prescricao intercorrente
4. **Integrar no Laravel BFF** (media) -- `Process::run()` no SearchController, parse JSON, exibir
5. **Cleanup modelos Ollama** (baixa) -- `ollama rm qwen2.5:0.5b qwen2.5:1.5b qwen2.5:3b` (~3.3GB)
6. **Commit do agente atualizado** (alta) -- agente global em `~/.claude/agents/` esta fora do git do lex-vector. Decidir: commitar copia em stj-vec/docs/ ou manter apenas global
