# Contexto: MCP Bridge em Release, HTTP Plugin, Build Windows

**Data:** 2026-02-18
**Sessao:** main (commits 2b97f60, 86baef3)
**Projeto:** lex-vector/legal-workbench

---

## O que foi feito

### 1. Batch de testes E2E do LEDES Converter via API

Executados 6 passos de teste end-to-end na API (porta 8003):
- Health check: OK
- List matters: 4 matters retornados
- Text-to-LEDES: conversao OK, classificacao UTBMS correta (L510, L210)
- Validate: detectou 4 erros esperados em input incompleto
- Structured conversion: output LEDES completo com dados do matter
- CRUD matters: create/get/delete funcionando

### 2. Habilitacao do MCP Bridge em release builds

Problema: o plugin `tauri-plugin-mcp-bridge` estava restrito a debug builds via
`#[cfg(all(feature = "mcp-bridge", debug_assertions))]`. Isso impedia testes via
MCP Tauri no AppImage/exe.

Solucao: removida a condicao `debug_assertions`, mantendo apenas `#[cfg(feature = "mcp-bridge")]`.
O plugin so e incluido quando `--features mcp-bridge` e passado no build.

Arquivos: `build.rs`, `lib.rs`

### 3. Renomeacao do binario de tauri-app para legal-workbench

Problema: todos os apps Tauri saiam com o mesmo nome de processo `tauri-app`,
impossibilitando o MCP Bridge de distinguir entre Legal Workbench e Pro ATT Machine.

Solucao: renomeado o `[package] name` no Cargo.toml de `tauri-app` para `legal-workbench`,
e a lib de `tauri_app_lib` para `legal_workbench_lib`.

Arquivos: `Cargo.toml`, `main.rs`

### 4. Migracao de axios para tauri-plugin-http

Problema: no webview de producao (scheme `tauri://`), o `XMLHttpRequest` (usado pelo axios)
e bloqueado para URLs externas. O `fetch` nativo tambem. Apenas o `tauri-plugin-http`
consegue fazer requests HTTP para fora do webview.

Solucao:
- Importar `fetch` do `@tauri-apps/plugin-http`
- Criar `httpFetch` que usa `tauriFetch` em Tauri e `globalThis.fetch` em browser
- Substituir todas as chamadas axios por `httpFetch`
- Configurar scope HTTP na capability `default.json` com URLs permitidas

Arquivo: `ledesConverterApi.ts`, `capabilities/default.json`

### 5. Configuracao da scope HTTP

A capability `http:default` do Tauri v2 exige scope explicita com URLs permitidas.
Formato correto:
```json
{
  "identifier": "http:default",
  "allow": [
    { "url": "http://localhost:*" },
    { "url": "http://127.0.0.1:*" },
    { "url": "http://100.98.38.32:*" },
    { "url": "http://100.114.203.28:*" },
    { "url": "https://*.lexvector.com.br/*" }
  ]
}
```

### 6. URL da API apontando para Tailscale

Problema: o default `localhost:8003` exige tunnel SSH em cada maquina cliente.
Solucao: mudado para `100.98.38.32:8003` (IP Tailscale da VM GCP), eliminando
necessidade de tunnel.

### 7. Build Windows (cmr-002)

Build concluido com sucesso no PC Windows:
- Toolchain: Rust + Node + MSVC Build Tools + Bun
- Comando: `bun run tauri build -- --features mcp-bridge`
- Requer PowerShell como Admin + `$env:CARGO_HTTP_CHECK_REVOKE = "false"`
- Artefatos: MSI e NSIS `.exe` gerados
- App instalado via NSIS installer

### 8. Testes MCP Tauri no PC Linux (cmr-auto)

Conexao MCP Bridge via Tailscale (100.102.249.9:9223) funcionou.
Testes realizados com sucesso:
- Navegacao Dashboard -> LEDES Converter
- Carregamento de 4 matters via tauri-plugin-http
- Selecao de matter + dados no sidebar (ID, client, firm, timekeeper, rate)
- Conversao text-to-LEDES via colar texto
- Validacao com 9 issues detectados (esperados para input parcial)

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `frontend/src-tauri/build.rs` | Modificado - removido debug_assertions do MCP Bridge |
| `frontend/src-tauri/src/lib.rs` | Modificado - idem |
| `frontend/src-tauri/Cargo.toml` | Modificado - name: legal-workbench |
| `frontend/src-tauri/src/main.rs` | Modificado - legal_workbench_lib |
| `frontend/src-tauri/capabilities/default.json` | Modificado - scope HTTP com IPs Tailscale |
| `frontend/src/services/ledesConverterApi.ts` | Modificado - axios -> tauri-plugin-http fetch |
| `scripts/build-windows.ps1` | Criado - script de build Windows (nao commitado) |

## Commits desta sessao

```
86baef3 fix(tauri): apontar LEDES API para IP Tailscale da VM GCP
2b97f60 feat(tauri): habilitar MCP Bridge em release, renomear binario e migrar HTTP para plugin
```

## Pendencias identificadas

1. **SSH Windows (cmr-002) nao acessivel da VM GCP** -- OpenSSH Server instalado e rodando,
   firewall rule criada, mas conexao timeout via Tailscale. Precisa debug.
2. **Teste MCP Tauri no Windows** -- app instalado mas nao testado via MCP Bridge
   (depende de resolver SSH/Tailscale)
3. **Matters nao carregam no Windows** -- o commit 86baef3 corrige (aponta para IP Tailscale),
   mas precisa rebuild no Windows com `git pull && bun run tauri build -- --features mcp-bridge`
4. **Tunnel SSH no PC Linux (cmr-auto)** -- existe tunnel reverso ativo na porta 8003,
   mas com a mudanca para IP Tailscale direto, pode ser removido

## Decisoes tomadas

- **MCP Bridge em release:** habilitado via feature flag, nao mais restrito a debug.
  Justificativa: necessario para testes E2E remotos via MCP Tauri
- **axios removido do LEDES API client:** substituido por tauri-plugin-http fetch.
  Justificativa: axios usa XHR que e bloqueado no webview de producao
- **API URL default = IP Tailscale:** em vez de localhost.
  Justificativa: elimina necessidade de tunnel SSH em cada maquina
- **Binario renomeado:** legal-workbench em vez de tauri-app.
  Justificativa: distinguir de outros apps Tauri (Pro ATT Machine)
- **Build Windows requer Admin:** documentado no CLAUDE.md.
  Justificativa: SSL/certificados corporativos no escritorio
