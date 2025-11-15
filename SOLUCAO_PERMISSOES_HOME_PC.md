# Solução Completa: Permissões Windows - Home PC

## Resumo Executivo

Script PowerShell **unificado** que detecta e corrige **todos** os problemas de permissão no seu PC Windows doméstico, permitindo que Claude Code funcione perfeitamente.

### Problema Identificado

Seu PC de casa foi configurado pela mesma pessoa que configurou o PC do trabalho, resultando em:
- ❌ Arquivos com **ownership incorreto** (proprietário diferente do usuário atual)
- ❌ Permissões NTFS insuficientes
- ❌ PATH corrompido (contém `C:\Users\<user>` inteiro)
- ❌ EPERM ao criar lock files (`.claude.json.lock`)
- ❌ Windows Defender bloqueando operações

### Solução Criada

**3 arquivos entregues:**

1. **`fix-home-windows-permissions.ps1`** (910 linhas)
   - Script principal de correção
   - 100% genérico (zero hardcoded paths)
   - Funciona com/sem privilégios admin

2. **`PLANO_SCRIPT_PERMISSOES.md`**
   - Planejamento técnico completo
   - Análise de causa raiz
   - Arquitetura da solução

3. **`docs/GUIA_CORRECAO_PERMISSOES_HOME.md`**
   - Guia de uso passo-a-passo
   - Exemplos de output esperado
   - Troubleshooting completo

## Uso Imediato (TL;DR)

### Opção 1: Diagnóstico Rápido

```powershell
cd C:\claude-work\repos\Claude-Code-Projetos
.\fix-home-windows-permissions.ps1 -DiagnoseOnly
```

### Opção 2: Correção Completa (SEM Admin)

```powershell
.\fix-home-windows-permissions.ps1 -All
```

### Opção 3: Correção Completa (COM Admin) - **RECOMENDADO**

```powershell
# PowerShell → Right-click → Run as Administrator
cd C:\claude-work\repos\Claude-Code-Projetos
.\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion
```

## O Que o Script Faz

### Diagnóstico Automático

✅ **Ownership** - Verifica proprietário de arquivos críticos
✅ **Permissões NTFS** - Testa se usuário atual tem FullControl
✅ **PATH** - Detecta corrupção (C:\Users\<user> inteiro)
✅ **Lock Creation** - Testa criação de `.claude.json.lock`
✅ **Stale Locks** - Encontra locks de sessões antigas
✅ **Windows Defender** - Verifica exclusões

### Correção Automatizada

🔧 **Ownership** → `takeown.exe` + `icacls /setowner`
🔧 **Permissions** → `icacls /grant <user>:F` (FullControl)
🔧 **PATH** → Remove entrada errada, adiciona `.local\bin`
🔧 **Stale Locks** → Remove `.claude.json.*`
🔧 **Defender** → Adiciona exclusão (requer admin)

### Validação Pós-Correção

✅ Re-executa diagnóstico
✅ Testa criação de locks
✅ Gera relatório final

## Arquivos Verificados

```
C:\Users\<você>\.claude.json         → Configuração Claude Code
C:\Users\<você>\.claude\             → Plugins/cache
C:\Users\<você>\.local\              → Binários locais
C:\claude-work\repos\Claude-Code-Projetos\  → Projeto (se detectado)
```

## PATH Corrigido

**ANTES (Incorreto):**
```
C:\Users\pedro              ← REMOVE (causa crash do Claude Code)
C:\Windows\System32
...
```

**DEPOIS (Correto):**
```
C:\Users\pedro\.local\bin   ← ADICIONA (binários do usuário)
C:\Windows\System32
...
```

## Características Técnicas

### 100% Genérico

✅ Zero hardcoded paths
✅ Zero hardcoded usernames
✅ Usa apenas: `$env:USERPROFILE`, `$env:USERNAME`, `$env:TEMP`
✅ Detecta projeto dinamicamente
✅ Funciona em qualquer PC Windows

### Segurança

✅ Cria backup do PATH automaticamente
✅ Apenas modifica arquivos do usuário atual
✅ Não toca em arquivos de sistema
✅ PATH do sistema intocado (apenas PATH do usuário)
✅ Validação pós-correção obrigatória

### Compatibilidade

✅ PowerShell 5.1+ (Desktop)
✅ Windows 10, Windows 11
✅ Funciona sem admin (exceto Defender exclusion)
✅ Sintaxe 100% PowerShell (zero bashismos)

## Output Esperado (Exemplo)

### Diagnóstico com Problemas

```
[!] Owner incorreto: C:\Users\pedro\.claude.json
  [i]   Atual: DESKTOP\admin | Esperado: pedro
[✗] CRÍTICO: PATH contém C:\Users\pedro (deve ser removido!)
[✗] Lock creation test: FALHOU

Para corrigir, execute:
  .\fix-home-windows-permissions.ps1 -All
```

### Correção Bem-Sucedida

```
═══ CORREÇÃO DE OWNERSHIP
[✓] Ownership corrigido: 1/1

═══ CORREÇÃO DE PERMISSÕES
[✓] Permissões corrigidas: 1/1

═══ CORREÇÃO DO PATH
[✓] PATH atualizado com sucesso!

═══ VALIDAÇÃO PÓS-CORREÇÃO
[✓] Lock creation test: PASSOU

╔═══════════════════════════════════════════════════════════════════╗
║  ✓ CORREÇÕES APLICADAS COM SUCESSO!                               ║
║  Claude Code deve funcionar agora.                                ║
╚═══════════════════════════════════════════════════════════════════╝
```

## Comparação com Scripts Existentes

### Scripts Antigos

1. **`fix-claude-permissions.ps1`**
   - ❌ Foco apenas em EPERM de lock files
   - ❌ Não verifica ownership
   - ❌ Não corrige PATH

2. **`diagnose-corporate-env.ps1`**
   - ✅ Diagnóstico excelente
   - ❌ Sem correção automatizada
   - ❌ Foco em ambiente corporativo

### Script Novo (fix-home-windows-permissions.ps1)

✅ **Unificado** - Diagnóstico + Correção em um único script
✅ **Completo** - Ownership + Permissions + PATH + Locks + Defender
✅ **Específico** - Foco em ambiente doméstico (não corporativo)
✅ **Validado** - Pós-correção automática

## Fluxo Recomendado (Primeira Execução)

```powershell
# PASSO 1: Clone/Pull do repositório (se ainda não fez)
cd C:\claude-work\repos\Claude-Code-Projetos
git pull

# PASSO 2: Diagnóstico
.\fix-home-windows-permissions.ps1 -DiagnoseOnly

# PASSO 3: Leia o relatório (identifique problemas)

# PASSO 4: Correção Completa
# Opção A: Sem Admin
.\fix-home-windows-permissions.ps1 -All

# Opção B: Com Admin (RECOMENDADO)
# Right-click PowerShell → Run as Administrator
.\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion

# PASSO 5: Valide
.\fix-home-windows-permissions.ps1 -DiagnoseOnly

# PASSO 6: Teste Claude Code
claude
```

## Troubleshooting Rápido

### "Lock creation test ainda falha"

**Solução 1:** Execute com admin + Defender exclusion
```powershell
.\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion
```

**Solução 2:** Verifique antivírus terceiro
- Adicione `.claude.json` às exclusões manualmente

**Solução 3:** Ambiente semi-corporativo?
```powershell
.\diagnose-corporate-env.ps1 -Verbose
```
Se score ≥ 6 → Use Claude Code Web ao invés do CLI

### "PATH não mudou"

**Causa:** PATH é variável de ambiente - precisa reabrir PowerShell

**Solução:**
```powershell
# Feche e reabra PowerShell
# OU force reload:
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
```

### "Ownership ainda incorreto"

**Causa:** Precisa de admin para takeown de alguns arquivos

**Solução:**
```powershell
# PowerShell como Administrador
.\fix-home-windows-permissions.ps1 -FixOwnership
```

## Arquivos de Suporte

### Documentação

- **`PLANO_SCRIPT_PERMISSOES.md`** → Planejamento técnico completo
- **`docs/GUIA_CORRECAO_PERMISSOES_HOME.md`** → Guia de uso detalhado
- **`DISASTER_HISTORY.md`** → Contexto histórico dos problemas
- **`CLAUDE.md`** → Regras arquiteturais (Lições 1-8)

### Scripts Auxiliares

- **`diagnose-corporate-env.ps1`** → Detecta ambiente corporativo
- **`fix-claude-permissions.ps1`** → Fix específico de EPERM (antigo)

## Validação de Qualidade

### Testes de Sintaxe

✅ **PowerShell 5.1** - Sintaxe validada
✅ **Cmdlets** - Todos nativos do Windows
✅ **Variáveis de ambiente** - Uso correto
✅ **Zero bashismos** - 100% PowerShell puro
✅ **Paths** - Todos com `Join-Path` (cross-subdir)

### Cobertura de Problemas

✅ **Ownership** - takeown + icacls
✅ **Permissions** - ACLs com FullControl
✅ **PATH** - Detecção + limpeza + adição
✅ **Locks** - Detecção + remoção
✅ **Defender** - Exclusões opcionais
✅ **Validation** - Pós-correção automática

### Segurança

✅ **Backups** - PATH salvo automaticamente
✅ **Scope** - Apenas usuário atual
✅ **Reversível** - PATH pode ser restaurado
✅ **Não-destrutivo** - Não toca arquivos sistema

## Diferencial: Por Que Esta Solução é Melhor

### Problema Original
"Meu PC de casa tem problemas de ownership porque foi configurado pela mesma pessoa do trabalho"

### Soluções Antigas
- `fix-claude-permissions.ps1` → Apenas EPERM
- `diagnose-corporate-env.ps1` → Apenas diagnóstico

### Esta Solução
✅ **Detecta** ownership incorreto (NOVO!)
✅ **Corrige** ownership via takeown (NOVO!)
✅ **Limpa** PATH corrompido (NOVO!)
✅ **Unificado** - Um script faz tudo
✅ **Validado** - Testa após correção
✅ **Documentado** - 3 níveis de docs

## Próximos Passos

1. ✅ **Arquivos criados e prontos para uso**
   - `fix-home-windows-permissions.ps1`
   - `PLANO_SCRIPT_PERMISSOES.md`
   - `docs/GUIA_CORRECAO_PERMISSOES_HOME.md`
   - `SOLUCAO_PERMISSOES_HOME_PC.md` (este arquivo)

2. ⏳ **Commit para branch**
   - Branch: `claude/fix-windows-permissions-home-0122FXqA1UA4ZTRN3WgAyJ92`

3. ⏳ **Push para GitHub**

4. ⏳ **Execução no PC Windows doméstico**
   - Execute script
   - Valide correções
   - Teste Claude Code

## Conclusão

**Problema:** PC de casa com problemas de permissão (ownership, PATH, EPERM)

**Solução:** Script PowerShell unificado que detecta e corrige **todos** os problemas automaticamente

**Resultado esperado:** Claude Code funcionando perfeitamente no PC doméstico após uma única execução do script

**Próximo passo:** Execute no Windows:
```powershell
cd C:\claude-work\repos\Claude-Code-Projetos
git pull
.\fix-home-windows-permissions.ps1 -All -AddDefenderExclusion
```

---

**Criado:** 2025-11-15
**Versão:** 1.0
**Status:** ✅ PRONTO PARA USO
**Branch:** `claude/fix-windows-permissions-home-0122FXqA1UA4ZTRN3WgAyJ92`
