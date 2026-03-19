# Contexto: Sidebar de Historico, Sistema de Theming TOML e Autenticacao

**Data:** 2026-03-19
**Sessao:** feature/stj-vec-sidebar-auth-theming (mergeado em main)
**Duracao:** ~3h

---

## O que foi feito

### 1. Sidebar de historico de buscas

Componente Livewire `SearchHistory` que lista as ultimas 30 buscas da tabela `search_jobs`, agrupadas por data (Hoje/Ontem/dd-mm). Cada item mostra query truncada, icone SVG de status (check/spinner/erro), contagem de resultados, duracao, e horario. Polling a cada 30s.

Clicar numa busca concluida dispara `load-history-job` via Livewire dispatch, que carrega os resultados no painel principal (DecomposedSearch escuta via `#[On('load-history-job')]`).

Layout alterado para `flex` com sidebar 240px a esquerda + conteudo principal. Sidebar escondida em telas < lg.

### 2. Redesign de cores e divisorias

Paleta migrada de navy-900 (azul marinho pesado) para slate-800 (neutro mais leve). Borders de navy-100 (quase invisiveis) para slate-200. Botoes consistentes em slate. Result cards com `border-left: 3px solid` visivel por default e `space-y-3` entre cards.

Pagina de documento (integra) recebeu section labels (Ementa, Acordao, Voto etc), separadores entre chunks, texto justificado com indentacao, tipografia dedicada `.document-prose`.

### 3. Sistema de theming TOML

Replicado do case-docs e ccui-vf. Componentes:

- **Model `Theme`**: name, toml_config (texto TOML), is_active
- **`TomlParser`**: parser minimalista sem dependencias (parse/encode)
- **`ThemeService`**: 27 tokens semanticos mapeados via VAR_MAP (surface, text, border, accent, button). Gera `:root { --c-*: valor; }` injetado via `<style>` no layout
- **`ThemeSettings`** Livewire: CRUD de temas, editor TOML, ativar/desativar, reset
- Rota `/settings/themes` + icone de engrenagem no header

Todos os blades migrados de classes Tailwind hardcoded para `var(--c-*)`. Badges de status (azul/amber/red) permaneceram com Tailwind (sao semanticos de estado, nao de tema).

**BUG CONHECIDO: o sistema de themes NAO funciona.** Tema pode ser criado e editado, mas as variaveis CSS nao sao aplicadas corretamente. Precisa debug na proxima sessao.

### 4. Autenticacao com login/senha

Auth minimalista sem Breeze/Fortify:

- **AuthController**: login/logout/change-password com `Auth::attempt()` e rate limiting (`throttle:5,1`)
- **SetupController**: primeiro acesso via token SHA-256 (`hash('sha256', $id.$email.$created_at)`). Token valido enquanto `must_change_password=true`, expira apos uso
- **EnsurePasswordChanged middleware**: forca troca de senha no primeiro login
- **Comando `users:setup-links`**: gera URLs de setup por usuario
- **UserSeeder**: 3 usuarios (PGR, ABP, BBT) com senha aleatoria

Fluxo: usuario recebe link de setup -> cria senha -> auto-login -> acesso ao app. Proximos acessos via `/login`.

### 5. Exposicao publica via Tailscale Funnel

Tailscale Funnel ativado na porta 8443. App acessivel publicamente em `https://extractlab.cormorant-alpha.ts.net:8443/`. Trust proxies configurado (`$middleware->trustProxies(at: '*')`) e `APP_URL` atualizado no `.env`.

### 6. Skill e regra criadas

- `~/.claude/skills/laravel-auth.md` -- workflow generalizado de auth minimalista replicavel
- `~/.claude/rules/laravel-apps.md` -- tabela com todos os 6 apps Laravel, portas, URLs, servicos

## Estado dos arquivos

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `app/Livewire/SearchHistory.php` | Criado | Componente sidebar, lista search_jobs |
| `app/Livewire/ThemeSettings.php` | Criado | CRUD de temas TOML |
| `app/Livewire/DecomposedSearch.php` | Modificado | +loadHistoryJob listener, +dispatch search-completed |
| `app/Models/Theme.php` | Criado | Model com activate/active |
| `app/Models/User.php` | Modificado | +must_change_password fillable/cast |
| `app/Services/Theme/ThemeService.php` | Criado | 27 tokens, VAR_MAP, cssVariables() |
| `app/Services/Theme/TomlParser.php` | Criado | parse/encode minimalista |
| `app/Http/Controllers/AuthController.php` | Criado | login/logout/change-password |
| `app/Http/Controllers/SetupController.php` | Criado | Primeiro acesso via token |
| `app/Http/Middleware/EnsurePasswordChanged.php` | Criado | Forca troca de senha |
| `app/Console/Commands/GenerateSetupLinks.php` | Criado | Gera URLs de setup |
| `bootstrap/app.php` | Modificado | +trustProxies, +password.changed alias |
| `routes/web.php` | Modificado | Rotas auth (guest/auth/password.changed) + setup |
| `resources/css/app.css` | Modificado | CSS variables --c-*, .document-prose, .section-label |
| `resources/views/layouts/app.blade.php` | Modificado | Sidebar + header com logout + ThemeService injection |
| `resources/views/livewire/decomposed-search.blade.php` | Modificado | var(--c-*) em vez de navy-* |
| `resources/views/livewire/search-history.blade.php` | Criado | Sidebar com agrupamento por data |
| `resources/views/livewire/theme-settings.blade.php` | Criado | Editor TOML |
| `resources/views/search/document.blade.php` | Modificado | Section labels, .document-prose |
| `resources/views/auth/login.blade.php` | Criado | Tela de login |
| `resources/views/auth/setup.blade.php` | Criado | Primeiro acesso |
| `resources/views/auth/change-password.blade.php` | Criado | Troca de senha |
| `resources/views/settings/themes.blade.php` | Criado | Wrapper pra ThemeSettings |
| `database/migrations/*_create_themes_table.php` | Criado | Tabela themes |
| `database/migrations/*_add_must_change_password.php` | Criado | Coluna must_change_password |
| `database/seeders/UserSeeder.php` | Criado | 3 usuarios iniciais |
| `tests/Feature/*.php` | Modificado | RefreshDatabase + actingAs em todos |

## Commits desta sessao

```
3dc6085 feat(stj-vec-web): autenticacao com login/senha e primeiro acesso via token
03a0f71 feat(stj-vec-web): sistema de theming TOML com editor no browser
5a48edf feat(stj-vec-web): sidebar de historico, redesign de cores e divisorias
```

**Nao commitado:** fix do `$fillable` no `SearchJob` (adicionado `'id'`). Commitar na proxima sessao apos validar.

## Decisoes tomadas

- **Auth manual em vez de Breeze/Fortify**: para 3 usuarios fixos sem self-registration, Breeze e Fortify trazem bloat (register, forgot-password, email verify). Auth::attempt() + middleware custom e suficiente. | Descartado: Breeze (muita UI desnecessaria), Fortify (dependencia extra)
- **Login por name em vez de email**: emails sao ficticios (`pgr@stj-vec.local`). Nome e mais intuitivo para 3 usuarios. | Descartado: email -- inutil sem verificacao
- **Primeiro acesso via token SHA-256**: evita definir senhas manualmente e compartilhar via chat. Token = hash deterministico de id+email+created_at, expira apos uso. | Descartado: senhas fixas (inseguro), magic link por email (sem SMTP)
- **Tailscale Funnel em vez de nginx+certbot**: sem dominio proprio, Let's Encrypt nao emite certificado. Funnel da HTTPS automatico. | Descartado: nginx+certbot (requer dominio)
- **Theming TOML replicado de case-docs**: padrao ja provado em 2 repos. TomlParser sem dependencia. | Descartado: config em JSON (menos legivel), YAML (precisa parser)
- **Accent quente #a16a3a**: AA pass contra branco (4.53:1). O #c8956c original falhava AA (2.63:1). | Descartado: #c8956c para texto/botoes (falha acessibilidade)

### 7. Fix: historico de buscas mostrava spinner permanente

`SearchJob` model usa `HasUuids` que auto-gera UUID. O campo `id` nao estava no `$fillable`, entao `SearchJob::create(['id' => $searchId, ...])` ignorava o UUID do Livewire e gerava outro. O `persistJobResult()` fazia `where('id', $searchId)` com o UUID original -- nunca encontrava o registro. Status ficava `running` pra sempre.

Fix: adicionado `'id'` ao `$fillable` do `SearchJob`. 4 registros orfaos corrigidos para `error`.

## Pendencias identificadas

1. **Sistema de themes nao funciona** (alta) -- Temas podem ser criados/editados mas as CSS variables nao sao aplicadas. Precisa debug: verificar se ThemeService::cssVariables() retorna o CSS correto, se o `<style>` e renderizado, e se as classes `var(--c-*)` nos blades estao corretas
2. **Historico de buscas: validar fix** (alta) -- O fix do `$fillable` foi aplicado mas nao testado no browser. Proxima sessao deve fazer uma busca e verificar se aparece com check verde no historico e se e clicavel
3. **CCUI e ELCO compartilham porta 8001** (media) -- Conflito se ambos rodarem. Resolver mudando porta de um deles
4. **Testes de auth ausentes** (media) -- AuthController e SetupController nao tem testes dedicados. Os 52 testes existentes passam mas nao cobrem fluxo de login/setup/change-password
5. **index.blade.php parcialmente migrado** (baixa) -- A tab "Busca Direta" ainda usa classes navy-* hardcoded no JS template literal (resultado renderizado via JS, nao Blade). Funciona visualmente (tokens navy existem no @theme) mas nao responde a temas
