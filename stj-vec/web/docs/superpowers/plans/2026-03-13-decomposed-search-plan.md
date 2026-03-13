# Plano: Busca Decomposta + Redesign UI

**Spec:** `docs/superpowers/specs/2026-03-13-decomposed-search-design.md`
**Runner:** Host (PHP 8.3, Laravel 12, sem Sail)
**Branch:** `work/query-decomposer-docs` (atual)

---

## Batch 1: Scaffolding

1. Instalar Livewire (`composer require livewire/livewire`)
2. Adicionar config `agent_path` em `config/services.php`
3. Atualizar layout `app.blade.php` com @livewireStyles/@livewireScripts e nova paleta navy
4. Verificar: `php artisan livewire:list` funciona

## Batch 2: Service AgentRunner

5. Criar `app/Services/AgentRunnerInterface.php` (interface)
6. Criar `app/Services/AgentRunner.php` (implementacao com Process::start)
7. Registrar binding no `AppServiceProvider`
8. Criar fixture `tests/fixtures/agent-output-sample.json` (output real do agente)
9. Escrever `tests/Unit/AgentRunnerTest.php`:
   - test_start_creates_meta_file
   - test_is_complete_detects_result_file
   - test_get_result_parses_json
   - test_cleanup_removes_old_files
10. Rodar testes -- devem falhar (RED)
11. Implementar AgentRunner ate testes passarem (GREEN)

## Batch 3: Livewire Component

12. Criar componente: `php artisan make:livewire DecomposedSearch`
13. Escrever `tests/Feature/DecomposedSearchTest.php`:
    - test_can_render_component
    - test_start_search_changes_status
    - test_poll_returns_results_when_complete
    - test_timeout_after_limit
    - test_validation_rejects_short_query
14. Rodar testes -- devem falhar (RED)
15. Implementar `DecomposedSearch.php` (estado, actions, poll)
16. Rodar testes ate passarem (GREEN)

## Batch 4: UI -- Layout e Busca Direta

17. Redesenhar `layouts/app.blade.php`:
    - Header navy com logo
    - Tabs "Busca Direta" | "Busca Decomposta"
    - Paleta: navy #1B365D, gray-50 fundo, white cards
18. Refatorar `search/index.blade.php`:
    - Tab "Busca Direta" com o conteudo existente
    - Tab "Busca Decomposta" monta `<livewire:decomposed-search />`
    - Sidebar de filtros (tipo, classe, ministro, orgao, data)
19. Verificar: busca direta continua funcionando identica

## Batch 5: UI -- Componente Decomposed

20. Implementar `livewire/decomposed-search.blade.php`:
    - Campo de busca com botao
    - Estado searching: spinner + elapsed timer
    - Estado completed: chips de angulos + resultados agrupados
    - Cards: badges tipo/classe, processo, preview, scores, ministro, data
    - Estado error/timeout: mensagem + retry
21. Estilos Tailwind: responsivo (sidebar drawer em mobile)

## Batch 6: Quality Gates

22. `./vendor/bin/pint` -- zero violations
23. `php artisan test` -- todos passando
24. Teste manual end-to-end: busca decomposta com agente real
25. Commit e verificacao final

## Batch 7: Cleanup

26. Criar artisan command `search:cleanup` para remover resultados >24h
27. Registrar no scheduler (se usar)

---

## Verificacao por batch

| Batch | Gate |
|-------|------|
| 1 | `php artisan livewire:list` funciona |
| 2 | `php artisan test --filter=AgentRunner` GREEN |
| 3 | `php artisan test --filter=DecomposedSearch` GREEN |
| 4 | Busca direta funciona identica no browser |
| 5 | Busca decomposta renderiza estados no browser |
| 6 | Pint + tests + manual OK |
| 7 | Comando cleanup funciona |
