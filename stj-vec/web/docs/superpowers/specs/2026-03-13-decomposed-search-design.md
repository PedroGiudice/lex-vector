# Design: Busca Decomposta + Redesign UI

**Data:** 2026-03-13
**Status:** Aprovado para implementacao

---

## Objetivo

Integrar o agente query-decomposer ao Laravel BFF como busca assincrona com Livewire,
e redesenhar a UI para exibir resultados agrupados por angulo juridico.

## Arquitetura

### Dois modos de busca

| Modo | Mecanismo | Tempo | UI |
|------|-----------|-------|-----|
| Busca direta | POST /search sincrono | ~2s | Lista plana (existente) |
| Busca decomposta | Livewire + Process async | 130-450s | Agrupado por angulo |

### Fluxo async (busca decomposta)

1. Usuario submete query no componente Livewire `DecomposedSearch`
2. Livewire chama `Process::start()` com o CLI do agente
3. Grava metadados em `storage/app/searches/{uuid}.meta.json`
4. `wire:poll.3s` verifica se `storage/app/searches/{uuid}.result.json` existe
5. Quando existe, le JSON, renderiza resultados agrupados
6. Timeout: 10 minutos

### Comando CLI

```bash
claude --agent ~/.claude/agents/query-decomposer.md \
  -p "{query}" \
  --output-format json \
  --model sonnet \
  --dangerously-skip-permissions \
  --no-session-persistence
```

### Armazenamento

Zero migrations. Zero Eloquent models. Filesystem-only:

```
storage/app/searches/
  {uuid}.meta.json   -> {pid, query, started_at}
  {uuid}.result.json -> output JSON do agente (50-100KB)
```

Cleanup via scheduled command: remover arquivos >24h.

## Rotas

Nenhuma rota nova. Livewire se comunica internamente.

```
GET /                    -> SearchController@index (existente)
POST /search             -> SearchController@search (existente)
GET /document/{docId}    -> SearchController@document (existente)
```

## Componentes

### Livewire: DecomposedSearch

**Classe:** `App\Livewire\DecomposedSearch`

**Estado:**
- `$query` (string) -- query do usuario
- `$searchId` (string|null) -- UUID da busca em andamento
- `$status` (string) -- idle|searching|completed|error|timeout
- `$results` (array|null) -- resultados parseados
- `$decomposition` (array|null) -- info de decomposicao (angulos, rounds)
- `$startedAt` (int|null) -- timestamp para calcular elapsed
- `$elapsedSeconds` (int) -- tempo decorrido atualizado pelo poll

**Actions:**
- `startSearch()` -- valida query, gera UUID, dispara Process, muda status
- `checkResult()` -- chamado pelo wire:poll, verifica arquivo resultado
- `cancelSearch()` -- mata processo (kill PID do meta), limpa estado

**View:** `resources/views/livewire/decomposed-search.blade.php`

### Service: AgentRunner

**Classe:** `App\Services\AgentRunner`

Responsabilidade: executar o agente CLI e gerenciar ciclo de vida.

```php
interface AgentRunnerInterface {
    public function start(string $searchId, string $query): void;
    public function isComplete(string $searchId): bool;
    public function getResult(string $searchId): ?array;
    public function cancel(string $searchId): void;
    public function cleanup(int $maxAgeHours = 24): int;
}
```

Implementacao usa `Process::start()` do Laravel com redirect de stdout para arquivo resultado.

## UI Design

### Layout

```
+----------------------------------------------------------+
|  STJ-Vec  [Busca Direta | Busca Decomposta]              |
+----------------------------------------------------------+
|  [========= Campo de busca =========] [Buscar]           |
|  [chip: angulo 1] [chip: angulo 2] [chip: angulo 3]     |
+-----------+----------------------------------------------+
|           |                                               |
| FILTROS   |  Status / Resultados                         |
| (sidebar) |                                               |
|           |  -- Angulo 1: Descricao (N resultados) --    |
| Tipo      |  [Card] [Card] [Card]                        |
| Classe    |                                               |
| Ministro  |  -- Angulo 2: Descricao (N resultados) --    |
| Orgao     |  [Card] [Card]                               |
| Data      |                                               |
|           |  -- Angulo 3: Descricao (N resultados) --    |
| [Limpar]  |  [Card] [Card] [Card]                        |
+-----------+----------------------------------------------+
```

### Paleta

| Elemento | Cor | Hex |
|----------|-----|-----|
| Header / accents | Navy | #1B365D |
| Fundo pagina | Gray 50 | #F9FAFB |
| Cards | White | #FFFFFF |
| Links / CTAs | Blue 600 | #2563EB |
| Texto principal | Gray 800 | #1F2937 |
| Texto secundario | Gray 500 | #6B7280 |
| Badge ACORDAO | Blue 100/700 | #DBEAFE/#1D4ED8 |
| Badge DECISAO | Amber 100/700 | #FEF3C7/#B45309 |
| Score alto (>0.7) | Green 600 | #16A34A |
| Score medio (0.4-0.7) | Yellow 600 | #CA8A04 |
| Erro | Red 600 | #DC2626 |

### Card de resultado

```
+--------------------------------------------------+
| [ACORDAO]  [REsp]  Processo: 1234567-89.2024     |
|                                          RRF 0.82|
|                                                    |
| Ementa com termos destacados em amarelo,          |
| mostrando 2-3 linhas do content_preview...        |
|                                                    |
| Min. Fulano . 2a Turma . 2024-03-15              |
| dense: 0.89  sparse: 0.74  via: "angulo 1"       |
+--------------------------------------------------+
```

### Estados da UI

1. **Idle:** campo de busca vazio, sem resultados
2. **Searching:** spinner + barra de progresso (elapsed time), mensagem "Analisando..."
3. **Completed:** chips de angulos + resultados agrupados
4. **Error:** mensagem de erro com botao retry
5. **Timeout:** mensagem especifica + sugestao de tentar busca direta

### Tabs de modo

Toggle no topo: "Busca Direta" (busca simples existente) | "Busca Decomposta" (Livewire async).
Busca direta mantem o comportamento vanilla JS existente.

### Responsividade

- Desktop: sidebar 250px + conteudo flex
- Tablet: sidebar colapsa em drawer
- Mobile: cards full-width, filtros em bottom sheet

## Testes

### Feature tests (Livewire)

1. `test_can_start_decomposed_search` -- submete query, verifica status=searching
2. `test_poll_returns_results_when_complete` -- simula arquivo resultado, verifica renderizacao
3. `test_timeout_after_10_minutes` -- simula elapsed > 600s, verifica status=timeout
4. `test_cancel_search` -- inicia busca, cancela, verifica cleanup
5. `test_validation_rejects_short_query` -- query < 3 chars rejeitada

### Unit tests

1. `AgentRunner::start()` -- verifica que Process e lancado e meta gravado
2. `AgentRunner::isComplete()` -- verifica deteccao de arquivo resultado
3. `AgentRunner::getResult()` -- verifica parsing de JSON real
4. `AgentRunner::cleanup()` -- verifica remocao de arquivos antigos

### Fixtures

Arquivo fixture com output real do agente (de uma das 5 validacoes anteriores).

## Quality Gates

- `./vendor/bin/pint` (zero violations)
- `php artisan test` (todos passando)
- Teste manual end-to-end com agente real

## Dependencias novas

- `livewire/livewire` (composer require)
- Nenhuma outra

## Arquivos a criar/modificar

### Criar

| Arquivo | Tipo |
|---------|------|
| `app/Livewire/DecomposedSearch.php` | Livewire component |
| `app/Services/AgentRunner.php` | Service |
| `app/Services/AgentRunnerInterface.php` | Interface |
| `app/Providers/AppServiceProvider.php` | Binding (modificar) |
| `resources/views/livewire/decomposed-search.blade.php` | View |
| `tests/Feature/DecomposedSearchTest.php` | Feature test |
| `tests/Unit/AgentRunnerTest.php` | Unit test |
| `tests/fixtures/agent-output-sample.json` | Fixture |

### Modificar

| Arquivo | Mudanca |
|---------|---------|
| `resources/views/search/index.blade.php` | Adicionar tabs + mount Livewire |
| `resources/views/layouts/app.blade.php` | Livewire scripts/styles, paleta navy |
| `composer.json` | Adicionar livewire/livewire |
| `config/services.php` | Adicionar agent_path config |

## Decisoes

- **Filesystem sobre cache:** JSON de 50-100KB, mais facil de debugar, nao polui cache
- **Process::start() sobre Jobs:** nao precisa de queue worker, o processo e fire-and-forget com resultado em arquivo
- **Livewire sobre vanilla JS:** polling nativo, estado no servidor, menos JS manual
- **Sem rotas novas:** Livewire se comunica internamente, sem API publica para decomposicao
- **Manter busca direta intacta:** zero risco de regressao, dois modos coexistem
