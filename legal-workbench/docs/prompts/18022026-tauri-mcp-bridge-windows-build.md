# Retomada: Testar LEDES Converter no Windows via MCP Tauri

## Contexto rapido

O Legal Workbench foi adaptado para funcionar em release builds com MCP Bridge
habilitado, HTTP via tauri-plugin-http (nao mais axios), e API apontando para o
IP Tailscale da VM GCP (100.98.38.32:8003). Build Windows (.exe) foi gerado
com sucesso no PC cmr-002, mas precisa de rebuild com o ultimo commit (86baef3)
que aponta a API para o IP Tailscale. Alem disso, o SSH entre VM GCP e PC Windows
via Tailscale esta com timeout -- precisa debug.

Testes no PC Linux (cmr-auto) via MCP Tauri foram bem-sucedidos: matters carregam,
conversao funciona, validacao detecta issues corretamente.

## Arquivos principais

- `frontend/src/services/ledesConverterApi.ts` -- API client LEDES (usa tauri-plugin-http)
- `frontend/src-tauri/capabilities/default.json` -- scope HTTP com IPs permitidos
- `frontend/src-tauri/build.rs` -- MCP Bridge condicional via feature flag
- `frontend/src-tauri/Cargo.toml` -- binario: legal-workbench
- `docs/contexto/18022026-tauri-mcp-bridge-windows-build.md` -- contexto desta sessao

## Proximos passos (por prioridade)

### 1. Rebuild no Windows com ultimo commit
**Onde:** PC Windows (cmr-002), PowerShell como Admin
**O que:** git pull e rebuild para pegar o commit que aponta API para IP Tailscale
**Por que:** sem isso, o app tenta localhost:8003 que nao existe no Windows
**Verificar:**
```powershell
cd C:\Lex-Vector\lex-vector
git pull origin main
cd legal-workbench\frontend
$env:CARGO_HTTP_CHECK_REVOKE = "false"
bun run tauri build -- --features mcp-bridge
# Reinstalar
& "src-tauri\target\release\bundle\nsis\Legal Workbench_0.1.4_x64-setup.exe"
```

### 2. Corrigir SSH/Tailscale entre VM GCP e PC Windows
**Onde:** PC Windows (cmr-002)
**O que:** debugar por que SSH timeout na porta 22 via Tailscale (100.112.239.110)
**Por que:** sem SSH, nao da pra conectar via MCP Tauri remotamente
**Verificar:**
```powershell
# No Windows, verificar:
Get-Service sshd                          # deve estar Running
netstat -an | findstr ":22 "              # deve mostrar LISTENING
ping 100.98.38.32                         # deve responder (VM GCP)
Test-NetConnection 100.98.38.32 -Port 22  # deve dar TcpTestSucceeded: True
```
```bash
# Na VM GCP, testar:
ssh -o ConnectTimeout=10 cmr-002@100.112.239.110 'hostname'
```

### 3. Conectar via MCP Tauri ao app Windows
**Onde:** VM GCP -> MCP Tauri -> cmr-002:9223
**O que:** iniciar driver_session apontando para IP Tailscale do Windows
**Por que:** validar que MCP Bridge funciona no build Windows
**Verificar:**
```
mcp__tauri__driver_session(action: "start", host: "100.112.239.110", port: 9223)
mcp__tauri__webview_execute_js("document.querySelector('h1').textContent")
# Deve retornar "Legal Workbench"
```

### 4. Testar LEDES Converter E2E no Windows
**Onde:** app Legal Workbench no Windows, via MCP Tauri
**O que:** navegar para LEDES, verificar matters carregam, testar conversao
**Por que:** validar que tauri-plugin-http funciona no Windows com IP Tailscale
**Verificar:**
```javascript
// Via mcp__tauri__webview_execute_js:
// 1. Navegar para LEDES
// 2. Verificar select de matters (deve ter 5 opcoes: default + 4 matters)
// 3. Selecionar matter, colar texto, compilar
// 4. Verificar output LEDES e validacao
```

### 5. (Opcional) Remover tunnel SSH no PC Linux
**Onde:** PC Linux (cmr-auto)
**O que:** matar o tunnel reverso na porta 8003 (ja desnecessario com IP Tailscale)
**Por que:** limpeza -- o tunnel foi criado antes da mudanca para IP direto
**Verificar:**
```bash
ssh cmr-auto@100.102.249.9 'ss -tlnp | grep 8003'
# Se mostrar tunnel ssh, matar o processo
```

## Como verificar (smoke test rapido)

```bash
# Na VM GCP: API esta rodando?
curl -s http://localhost:8003/health

# API acessivel via Tailscale?
curl -s http://100.98.38.32:8003/matters | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} matters')"
```
