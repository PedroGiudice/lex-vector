# Guia de Correção de Permissões - Windows Home PC

## Visão Geral

Script unificado que detecta e corrige **todos** os problemas de permissão no seu PC Windows doméstico, permitindo que Claude Code funcione perfeitamente.

**Arquivo:** `fix-home-windows-permissions.ps1`

## Problemas que Este Script Resolve

### ✅ Ownership Incorreto
- **Sintoma:** "Access Denied" mesmo com permissões aparentes
- **Causa:** Arquivos criados por outro usuário (ex: setup corporativo)
- **Solução:** `takeown` + `icacls /setowner`

### ✅ Permissões NTFS Inadequadas
- **Sintoma:** EPERM, "Permission Denied"
- **Causa:** ACLs restritivas, sem FullControl
- **Solução:** `icacls /grant <user>:F`

### ✅ PATH Corrompido
- **Sintoma:** Claude Code trava, VSCode abre plugins automaticamente
- **Causa:** PATH contém `C:\Users\<user>` inteiro ao invés de `.local\bin`
- **Solução:** Remove entrada errada, adiciona `.local\bin`

### ✅ EPERM em Lock Files
- **Sintoma:** Claude Code CLI congela ao iniciar
- **Causa:** Não consegue criar `.claude.json.lock`
- **Solução:** Ownership + Permissions + Defender exclusion

### ✅ Stale Locks
- **Sintoma:** Claude Code não inicia (falha silenciosa)
- **Causa:** Locks de sessões crashed anteriores
- **Solução:** Remove `.claude.json.*` antigos

### ✅ Windows Defender Bloqueios
- **Sintoma:** Delays, EPERM intermitente
- **Causa:** Real-time protection escaneia durante writes
- **Solução:** Adiciona exclusão (requer Admin)

## Uso Rápido

### 1. Diagnóstico Inicial (Recomendado)

```powershell
cd C:\claude-work\repos\Claude-Code-Projetos
.\fix-home-windows-permissions.ps1 -DiagnoseOnly
```

**O que faz:**
- ✅ Detecta problemas **sem fazer alterações**
- ✅ Mostra relatório completo
- ✅ Recomenda próximos passos

**Quando usar:**
- Primeira execução (para entender o estado)
- Antes de aplicar correções
- Para validar após correções

### 2. Correção Completa (Sem Admin)

```powershell
.\fix-home-windows-permissions.ps1 -All
```

**O que faz:**
- ✅ Corrige ownership de arquivos críticos
- ✅ Ajusta permissões NTFS (FullControl)
- ✅ Limpa PATH corrompido
- ✅ Remove stale locks
- ⚠️ **Pula** Defender exclusion (requer admin)

**Quando usar:**
- Problemas de ownership/permissões detectados
- PATH corrompido
- Não tem privilégios admin

### 3. Correção Completa (Com Admin) - RECOMENDADO

```powershell
# PowerShell → Right-click → Run as Administrator
cd C:\claude-work\repos\Claude-Code-Projetos
.\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion
```

**O que faz:**
- ✅ Tudo do item 2 acima
- ✅ **PLUS:** Adiciona exclusão Windows Defender

**Quando usar:**
- **Ideal para primeira correção completa**
- EPERM detectado
- Quer prevenir problemas futuros

### 4. Correções Específicas

#### Apenas Ownership

```powershell
.\fix-home-windows-permissions.ps1 -FixOwnership
```

**Útil quando:**
- Diagnóstico mostra apenas problemas de ownership
- Não quer alterar PATH ou permissões

#### Apenas Permissões

```powershell
.\fix-home-windows-permissions.ps1 -FixPermissions
```

**Útil quando:**
- ACLs precisam ajuste, mas ownership está correto

#### Apenas PATH

```powershell
.\fix-home-windows-permissions.ps1 -FixPATH
```

**Útil quando:**
- Claude Code trava com sintomas de PATH corrompido
- PATH contém `C:\Users\<user>` inteiro

## Output Esperado

### Diagnóstico Bem-Sucedido (Sem Problemas)

```
╔═══════════════════════════════════════════════════════════════════╗
║        CORREÇÃO DE PERMISSÕES WINDOWS - CLAUDE CODE               ║
║        Ambiente Doméstico (Home PC)                               ║
╚═══════════════════════════════════════════════════════════════════╝

═══ DETECÇÃO DE AMBIENTE
═══════════════════════════════
[i] Usuário: pedro
[i] Profile: C:\Users\pedro
[i] Admin: ✗
[i] Projeto Claude: ✓
  [i] Local: C:\claude-work\repos\Claude-Code-Projetos

═══ DIAGNÓSTICO COMPLETO
═══════════════════════════════
[i] Verificando ownership de arquivos críticos...
[✓] Owner correto: C:\Users\pedro\.claude.json (DESKTOP\pedro)
[✓] Owner correto: C:\Users\pedro\.claude (DESKTOP\pedro)
[✓] Owner correto: C:\Users\pedro\.local (DESKTOP\pedro)

[i] Verificando permissões NTFS...
[✓] Permissões corretas: C:\Users\pedro\.claude.json
[✓] Permissões corretas: C:\Users\pedro\.claude
[✓] Permissões corretas: C:\Users\pedro\.local

[i] Analisando variável PATH...
[✓] .local\bin está no PATH

[i] Testando criação de lock files...
[✓] Lock creation test: PASSOU

[i] Procurando stale locks...
[✓] Nenhum stale lock encontrado

╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║  ✓ NENHUM PROBLEMA DETECTADO - SISTEMA OK!                        ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

### Diagnóstico com Problemas

```
[!] Owner incorreto: C:\Users\pedro\.claude.json
  [i]   Atual: DESKTOP\admin | Esperado: pedro
[!] Permissões insuficientes: C:\Users\pedro\.claude.json
[✗] CRÍTICO: PATH contém C:\Users\pedro (deve ser removido!)
[!] .local\bin não está no PATH (será adicionado)
[✗] Lock creation test: FALHOU
  [✗]   Erro: Access is denied

╔═══════════════════════════════════════════════════════════════════╗
║                      RESULTADO DO DIAGNÓSTICO                     ║
╚═══════════════════════════════════════════════════════════════════╝

[Ownership]
  TotalChecked: 3
  IssuesFound: 1
  AllCorrect: ✗

[Permissions]
  TotalChecked: 3
  IssuesFound: 1
  AllCorrect: ✗

[PATH]
  TotalEntries: 15
  HasUserProfileRoot: True
  HasLocalBin: False
  IsCorrupted: True
  IssuesFound: 2

[LockCreation]
  CanCreateLock: ✗
  HasEPERMIssue: True
  TestPassed: ✗

Modo diagnóstico - nenhuma correção aplicada

Para corrigir, execute:
  .\fix-home-windows-permissions.ps1 -All

Ou com Admin (para Defender):
  .\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion
```

### Correção Bem-Sucedida

```
╔═══════════════════════════════════════════════════════════════════╗
║                      INICIANDO CORREÇÕES                          ║
╚═══════════════════════════════════════════════════════════════════╝

═══ CORREÇÃO DE OWNERSHIP
═══════════════════════════════
[i] Corrigindo ownership: C:\Users\pedro\.claude.json
[✓]   takeown.exe: Sucesso
[✓] Ownership corrigido: 1/1

═══ CORREÇÃO DE PERMISSÕES
═══════════════════════════════
[i] Corrigindo permissões: C:\Users\pedro\.claude.json
[✓]   icacls: Sucesso
[✓] Permissões corrigidas: 1/1

═══ CORREÇÃO DO PATH
═══════════════════════════════
[i] Backup do PATH: C:\Users\pedro\AppData\Local\Temp\PATH_backup_20251115_143022.txt
[!] Removido: C:\Users\pedro
[✓] Adicionado ao PATH: C:\Users\pedro\.local\bin
[✓] PATH atualizado com sucesso!
  [i]   Entradas removidas: 1
  [i]   Backup salvo em: C:\Users\pedro\AppData\Local\Temp\PATH_backup_20251115_143022.txt

═══ LIMPEZA DE STALE LOCKS
═══════════════════════════════
[✓] Removido: .claude.json.lock
[✓] Locks removidos: 1/1

═══ VALIDAÇÃO PÓS-CORREÇÃO
═══════════════════════════════
[i] Testando criação de lock files...
[✓] Lock creation test: PASSOU

╔═══════════════════════════════════════════════════════════════════╗
║                      RELATÓRIO FINAL                              ║
╚═══════════════════════════════════════════════════════════════════╝

[Ownership]
  Attempted: 1
  Fixed: 1
  Failed: 0

[Permissions]
  Attempted: 1
  Fixed: 1
  Failed: 0

[PATH]
  BackupLocation: C:\Users\pedro\AppData\Local\Temp\PATH_backup_20251115_143022.txt
  EntriesRemoved: 1
  LocalBinAdded: True

[StaleLocks]
  Attempted: 1
  Removed: 1
  Failed: 0

╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║  ✓ CORREÇÕES APLICADAS COM SUCESSO!                               ║
║                                                                   ║
║  Claude Code deve funcionar agora.                                ║
║  Execute: claude                                                  ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

## Arquivos Verificados/Corrigidos

### Arquivos Críticos Claude Code

```
C:\Users\<você>\.claude.json         → Configuração principal
C:\Users\<você>\.claude\             → Diretório de plugins/cache
C:\Users\<você>\.local\              → Binários locais
```

### Projeto Claude Code (se detectado)

```
C:\claude-work\repos\Claude-Code-Projetos\   → Raiz do projeto
```

### PATH Específico

```
REMOVE: C:\Users\<você>              → Raiz do perfil (NUNCA deve estar no PATH)
ADICIONA: C:\Users\<você>\.local\bin → Binários locais (DEVE estar no PATH)
```

## Troubleshooting

### "Permissões insuficientes" mesmo após correção

**Possível causa:** Executou sem privilégios admin e precisa de ownership fix mais agressivo

**Solução:**
```powershell
# PowerShell como Administrador
.\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion
```

### "PATH não mudou após script"

**Possível causa:** PATH é variável de ambiente - precisa reabrir PowerShell

**Solução:**
```powershell
# Feche e reabra PowerShell
# Ou forçar reload:
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
```

### "Lock creation test ainda falha"

**Possíveis causas:**
1. Windows Defender sem exclusão
2. Antivírus terceiro bloqueando
3. GPOs corporativas (se PC foi parte de domínio antes)

**Diagnóstico:**
```powershell
# Execute diagnóstico corporativo
.\diagnose-corporate-env.ps1 -Verbose
```

**Soluções:**
1. Execute com `-AddDefenderExclusion` (requer admin)
2. Adicione `.claude.json` às exclusões do antivírus manualmente
3. Se GPOs detectadas, pode ser ambiente semi-corporativo → use Claude Code Web

### "Arquivo X não existe"

**Comportamento esperado:** Script cria arquivos se não existirem

**Se persist ir:**
```powershell
# Criar manualmente
New-Item -ItemType File -Path "$env:USERPROFILE\.claude.json" -Force
```

## Fluxo Recomendado (Primeira Vez)

```powershell
# PASSO 1: Diagnóstico
cd C:\claude-work\repos\Claude-Code-Projetos
.\fix-home-windows-permissions.ps1 -DiagnoseOnly

# PASSO 2: Leia o relatório

# PASSO 3: Se houver problemas, corrija (com Admin se possível)
# PowerShell → Right-click → Run as Administrator
cd C:\claude-work\repos\Claude-Code-Projetos
.\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion

# PASSO 4: Valide
.\fix-home-windows-permissions.ps1 -DiagnoseOnly

# PASSO 5: Teste Claude Code
claude
```

## Segurança

### O que o Script Modifica?

✅ **Seguro:**
- Ownership de arquivos do usuário atual
- Permissões NTFS (concede FullControl ao próprio usuário)
- PATH do usuário (não sistema)
- Exclusões Defender (apenas `.claude.json`)

❌ **NÃO modifica:**
- Arquivos de sistema
- PATH do sistema (apenas usuário)
- Configurações globais
- Outros usuários

### Backups Criados

O script **automaticamente** faz backup de:
- **PATH:** `C:\Users\<você>\AppData\Local\Temp\PATH_backup_YYYYMMDD_HHMMSS.txt`

Para restaurar PATH:
```powershell
$backupPath = "C:\Users\<você>\AppData\Local\Temp\PATH_backup_YYYYMMDD_HHMMSS.txt"
$originalPATH = Get-Content $backupPath
[System.Environment]::SetEnvironmentVariable("Path", $originalPATH, "User")
```

## Compatibilidade

- ✅ **PowerShell:** 5.1+ (Windows PowerShell Desktop)
- ✅ **OS:** Windows 10, Windows 11
- ✅ **Privilégios:** Funciona sem admin (Defender exclusion requer admin)
- ✅ **Genericidade:** Zero hardcoded paths - 100% portável

## Quando NÃO Usar Este Script

❌ **Ambiente Corporativo Gerenciado (GPOs ativas)**
- Use `.\diagnose-corporate-env.ps1` para detectar
- Se score corporativo ≥ 6, use **Claude Code Web** ao invés do CLI
- GPOs podem bloquear correções

❌ **Múltiplos Usuários no Mesmo PC**
- Script apenas corrige arquivos do usuário atual
- Se precisar corrigir para outro usuário, execute como esse usuário

❌ **Problemas Não Relacionados a Permissões**
- Ex: Problemas de rede, sintaxe de código, etc.
- Veja outros troubleshooting guides

## Referências

- **DISASTER_HISTORY.md** - Contexto histórico dos problemas
- **CLAUDE.md** - Regras arquiteturais (Lições 1-8)
- **WINDOWS_PERMISSION_FIX.md** - Fix específico de EPERM
- **PLANO_SCRIPT_PERMISSOES.md** - Planejamento deste script

## Suporte

Se este script não resolver seu problema:

1. Execute diagnóstico corporativo:
   ```powershell
   .\diagnose-corporate-env.ps1 -Verbose -ExportReport
   ```

2. Verifique documentação adicional em `docs/`

3. Se for ambiente corporativo (score ≥ 6), use Claude Code Web

4. Verifique antivírus terceiros (não apenas Defender)

---

**Criado:** 2025-11-15
**Versão:** 1.0
**Testado em:** Windows 10, Windows 11
**PowerShell:** 5.1+
