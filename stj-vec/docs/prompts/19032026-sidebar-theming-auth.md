# Retomada: Debug do Theming TOML + Testes de Auth

## Contexto rapido

Sessao anterior implementou 3 features no stj-vec/web (Laravel 12, PHP 8.3): sidebar de historico de buscas, sistema de theming TOML, e autenticacao com login/senha. Auth funciona (testado no browser, PGR logou com sucesso). Sidebar funciona. **O sistema de themes NAO funciona** -- temas podem ser criados/editados via `/settings/themes` mas as CSS variables nao sao aplicadas corretamente. Esse e o principal item pendente.

App publico em `https://extractlab.cormorant-alpha.ts.net:8443/` via Tailscale Funnel. 52 testes passando.

<session_metadata>
branch: main
last_commit: 3dc6085
tests_passing: 52
service: stj-search-web (porta 8082)
public_url: https://extractlab.cormorant-alpha.ts.net:8443/
</session_metadata>

## Arquivos principais

- `stj-vec/web/app/Services/Theme/ThemeService.php` -- gera CSS variables a partir do TOML
- `stj-vec/web/app/Services/Theme/TomlParser.php` -- parser TOML minimalista
- `stj-vec/web/app/Livewire/ThemeSettings.php` -- CRUD de temas
- `stj-vec/web/resources/views/layouts/app.blade.php` -- onde `<style>{!! ThemeService::cssVariables() !!}</style>` e injetado
- `stj-vec/web/resources/css/app.css` -- referencias `var(--c-*)` no CSS
- `docs/contexto/19032026-sidebar-theming-auth.md` -- contexto detalhado

## Proximos passos (por prioridade)

### 0. Validar fix do historico de buscas + commitar
**Onde:** `app/Models/SearchJob.php` (ja modificado, nao commitado)
**O que:** `id` foi adicionado ao `$fillable`. Fazer uma busca no browser e verificar se aparece com check verde no historico e se clicar carrega os resultados
**Por que:** Fix aplicado mas nao validado no browser
**Verificar:** Fazer busca -> sidebar mostra check verde -> clicar carrega resultados. Se OK, commitar: `git add stj-vec/web/app/Models/SearchJob.php && git commit -m "fix(stj-vec-web): adiciona id ao fillable do SearchJob"`

### 1. Debug do sistema de theming TOML
**Onde:** `app/Services/Theme/ThemeService.php`, `resources/views/layouts/app.blade.php`
**O que:** Diagnosticar por que as CSS variables nao sao aplicadas. Hipoteses: (a) ThemeService::cssVariables() nao encontra tema ativo no DB, (b) TomlParser nao parseia corretamente o TOML gerado pelo encode(), (c) o `<style>` e renderizado mas com valores errados, (d) as classes `var(--c-*)` nos blades tem typo
**Por que:** Sem theming funcionando, as cores voltam a ser hardcoded
**Verificar:** Criar tema via `/settings/themes`, ativar, verificar `view-source:` no browser se as CSS variables aparecem no `<style>` do `<head>`

### 2. Testes para auth (AuthController e SetupController)
**Onde:** `tests/Feature/` (criar `AuthTest.php`)
**O que:** Testar: login com credenciais validas/invalidas, redirect pra change-password quando must_change_password=true, setup via token valido/invalido/expirado, logout, rate limiting
**Por que:** Auth e critica -- precisa de cobertura
**Verificar:** `php artisan test --filter Auth`

### 3. Migrar JS template literals da busca direta para theme variables
**Onde:** `resources/views/search/index.blade.php`, bloco `<script>` (linhas 230-260 aprox.)
**O que:** Os resultados da busca direta sao renderizados via JS (`template literal`), usando classes `navy-*` hardcoded. Trocar para `var(--c-*)` inline ou classes CSS que usem as variables
**Por que:** Sem isso, a tab "Busca Direta" nao responde a mudancas de tema
**Verificar:** Mudar tema e verificar se os resultados da busca direta mudam de cor

### 4. Resolver conflito de porta CCUI vs ELCO (8001)
**Onde:** Servicos systemd `ccui.service` e `elco-machina.service`
**O que:** Mudar a porta de um dos dois (sugestao: ELCO para 8004)
**Por que:** Ambos nao podem rodar simultaneamente na 8001
**Verificar:** `systemctl --user start ccui elco-machina` sem erro

## Como verificar

```bash
cd /home/opc/lex-vector/stj-vec/web
php artisan test --compact                    # 52+ testes passando
systemctl --user status stj-search-web        # active (running)
curl -s -o /dev/null -w "%{http_code}" https://extractlab.cormorant-alpha.ts.net:8443/login  # 200
php artisan tinker --execute="echo App\Models\Theme::count().' temas, '.App\Models\User::count().' usuarios';"
```
