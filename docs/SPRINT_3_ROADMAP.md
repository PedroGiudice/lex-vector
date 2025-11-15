# Sprint 3 Roadmap - Setup PC Trabalho (Windows Corporativo)

**Versão:** 1.0
**Data:** 2025-11-15
**Duração estimada:** 6-10 horas
**Objetivo:** Replicar ambiente WSL2 do PC casa + integrar servidor corporativo

---

## Contexto

**PC Casa (atual - WSL2):**
- Sprint 1 + 2 concluídos ✅
- Localização: `~/claude-work/repos/Claude-Code-Projetos`
- Processa: Dados de APIs (armazenados em `~/claude-code-data/`)
- Acesso servidor: NÃO (fora da rede corporativa)

**PC Trabalho (meta Sprint 3):**
- Localização: `C:\claude-work\repos\Claude-Code-Projetos` (Windows)
- Localização WSL: `~/claude-work/repos/Claude-Code-Projetos` (após instalação)
- Processa: Dados do servidor corporativo
- Acesso servidor: SIM (`\\SERVIDOR\documentos-juridicos`)

**Resultado esperado:** Ambos PCs "iguais" (mesma stack WSL2 + Python + Claude Code), mas PC trabalho tem acesso adicional ao servidor.

---

## Fase 1: Instalação WSL2 (2-3h)

### 1.1 Pré-requisitos (5 min)

**Validar no PC Trabalho (PowerShell como Admin):**

```powershell
# Verificar versão Windows
winver
# Requisito: Windows 10 versão 2004+ OU Windows 11

# Verificar virtualização habilitada
Get-ComputerInfo | Select-Object -Property CsProcessors
# Deve mostrar virtualização habilitada no BIOS
```

**Se virtualização desabilitada:**
- Reiniciar PC
- Entrar no BIOS (geralmente F2, Del, ou F10)
- Habilitar "Intel VT-x" ou "AMD-V"

### 1.2 Instalação WSL2 (15-30 min)

```powershell
# PowerShell como Administrador
wsl --install -d Ubuntu-24.04

# Aguardar download (pode demorar 5-15min)
# Sistema vai pedir para reiniciar
Restart-Computer
```

**Após reinício:**

1. Ubuntu vai abrir automaticamente
2. Criar usuário e senha:
   - Username: `[seu_usuario]` (sugestão: mesmo do PC casa)
   - Password: `[senha_forte]` (pode ser diferente do PC casa)

### 1.3 Configuração .wslconfig (5 min)

**Windows - Criar arquivo:** `C:\Users\[Username]\.wslconfig`

```ini
[wsl2]
memory=4GB
processors=2
swap=1GB
localhostForwarding=true
nestedVirtualization=false
```

**Reiniciar WSL:**

```powershell
# PowerShell
wsl --shutdown
# Aguardar 10 segundos
wsl
```

### 1.4 Atualização Sistema Base (10 min)

**Dentro do WSL:**

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl wget git vim htop tree
```

### 1.5 Exclusão Windows Defender (CRÍTICO - 5 min)

**PowerShell como Admin:**

```powershell
Add-MpPreference -ExclusionPath "$env:USERPROFILE\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu24.04LTS_79rhkp1fndgsc"

# Verificar
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
```

**Razão:** Sem exclusão, WSL fica 5-10x mais lento (Defender escaneia cada operação de arquivo).

### 1.6 Validação Fase 1

```bash
# WSL deve iniciar sem erros
wsl

# Verificar versão
lsb_release -a
# Esperado: Ubuntu 24.04 LTS

# Verificar recursos
free -h  # Deve mostrar ~4GB RAM
nproc    # Deve mostrar 2 cores
```

**✅ Checkpoint:** WSL2 funcional, performático, atualizado.

---

## Fase 2: Instalação Node.js + Claude Code (1-2h)

### 2.1 Instalação nvm (5 min)

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Recarregar shell
source ~/.bashrc

# Verificar
nvm --version  # Deve retornar 0.39.7
```

### 2.2 Instalação Node.js (10 min)

```bash
# Instalar Node.js LTS
nvm install --lts
nvm alias default node

# Verificar
node --version  # v20.x ou v22.x
npm --version   # 10.x ou superior
```

### 2.3 Instalação Claude Code (5 min)

```bash
# Instalar globalmente
npm install -g @anthropic-ai/claude-code

# Verificar
claude --version
which claude  # Deve apontar para ~/.nvm/versions/node/...
```

### 2.4 Autenticação Claude Code (5 min)

```bash
# Primeira execução
claude

# Seguir instruções para autenticar com API key Anthropic
# (mesmo processo do PC casa)
```

### 2.5 Validação Fase 2

```bash
node --version   # v20+
npm --version    # 10+
claude --version # 2.0.42+
which claude     # ~/.nvm/versions/node/.../bin/claude
```

**✅ Checkpoint:** Node.js e Claude Code instalados e funcionais.

---

## Fase 3: Clonagem e Configuração do Projeto (30-60 min)

### 3.1 Criar Estrutura de Diretórios (2 min)

```bash
mkdir -p ~/claude-work/repos
cd ~/claude-work/repos
```

### 3.2 Clonar Repositório (5 min)

**Opção A - HTTPS:**

```bash
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos
```

**Opção B - SSH (se já tiver chave configurada):**

```bash
git clone git@github.com:PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos
```

### 3.3 Configuração Git (3 min)

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"

# Verificar
git status
git log --oneline -5
```

### 3.4 Instalação Python + Dependências (5 min)

```bash
# Python já vem no Ubuntu 24.04
python3 --version  # 3.12.3

# Instalar pip e venv
sudo apt install -y python3-pip python3-venv python3-dev

# Verificar
pip3 --version
```

### 3.5 Criar Virtual Environments (20-40 min)

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Script automatizado para todos os agentes
for agente in agentes/*/; do
    echo "Configurando $agente"
    cd "$agente"

    # Criar venv
    python3 -m venv .venv

    # Ativar
    source .venv/bin/activate

    # Atualizar pip
    pip install --upgrade pip

    # Instalar dependências (se existir requirements.txt)
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
    fi

    # Desativar
    deactivate

    cd ../..
done
```

**Agentes esperados:**
1. `agentes/djen-tracker/.venv`
2. `agentes/legal-articles-finder/.venv`
3. `agentes/legal-lens/.venv`
4. `agentes/legal-rag/.venv`
5. `agentes/oab-watcher/.venv`

### 3.6 Instalar npm Dependencies (MCP Server) (10 min)

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/mcp-servers/djen-mcp-server

# Instalar packages
npm install

# Verificar
ls node_modules/ | wc -l  # ~340 packages
```

**Nota:** Vulnerabilidades npm conhecidas (5 moderate) são esperadas. Ver CHANGELOG.md para detalhes.

### 3.7 Testar Hooks (5 min)

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Testar hook JavaScript
node .claude/hooks/session-context-hybrid.js

# Output esperado (JSON):
# {"continue":true,"systemMessage":"..."}
```

**IMPORTANTE - Teste SessionStart Hook no Ambiente Corporativo:**

```bash
# Executar Claude Code uma vez
cd ~/claude-work/repos/Claude-Code-Projetos
claude

# Se houver EPERM loop (conforme DISASTER_HISTORY.md):
# - Sessão trava
# - Arquivo .claude.json.lock fica "locked"
# - Impossível usar Claude Code

# SOLUÇÃO se EPERM ocorrer:
# Desabilitar SessionStart hooks no PC trabalho
```

**Criar:** `.claude/settings.local.json` (gitignored)

```json
{
  "hooks": {
    "sessionStart": {
      "enabled": false
    }
  }
}
```

### 3.8 Validação Fase 3

```bash
# Verificar estrutura
ls ~/claude-work/repos/Claude-Code-Projetos/

# Testar um venv
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/oab-watcher
source .venv/bin/activate
python -c "import sys; print(f'Python: {sys.version}')"
deactivate

# Verificar Git
git status  # Deve estar limpo (apenas .venv/ em .gitignore)
```

**✅ Checkpoint:** Código sincronizado, venvs criados, hooks testados.

---

## Fase 4: Integração Servidor Corporativo (2-3h)

### 4.1 Instalação CIFS Utils (1 min)

```bash
sudo apt install -y cifs-utils
```

### 4.2 Teste de Acesso ao Servidor (Windows) (5 min)

**ANTES de configurar WSL, validar acesso Windows:**

```powershell
# PowerShell (Windows)
Test-Path \\SERVIDOR\documentos-juridicos

# Se FALSE: Servidor inacessível
# Possíveis causas:
# - Nome servidor incorreto
# - Sem permissão de acesso
# - VPN desconectada (se trabalho remoto)
```

**Se acesso OK, anotar:**
- Servidor: `\\SERVIDOR` (ou IP: `\\192.168.1.100`)
- Share: `documentos-juridicos`
- Estrutura: `\\SERVIDOR\documentos-juridicos\processos\2024\`

### 4.3 Criar Credentials File (WSL) (3 min)

```bash
# WSL
sudo nano /root/.smbcredentials
```

**Conteúdo:**

```
username=[seu_usuario_rede]
password=[sua_senha_rede]
domain=[DOMINIO_EMPRESA]
```

**Substituir:**
- `[seu_usuario_rede]`: Usuário da rede corporativa (sem domínio)
- `[sua_senha_rede]`: Senha atual
- `[DOMINIO_EMPRESA]`: Domínio (ex: EMPRESA, CORP) - verificar com `echo $USERDOMAIN` no PowerShell

**Proteger arquivo:**

```bash
sudo chmod 600 /root/.smbcredentials

# Verificar
ls -l /root/.smbcredentials
# Deve mostrar: -rw------- 1 root root
```

### 4.4 Criar Mount Point (1 min)

```bash
sudo mkdir -p /mnt/servidor
```

### 4.5 Teste de Montagem Manual (10 min)

**ANTES de configurar fstab, testar montagem manual:**

```bash
# Substituir SERVIDOR pelo nome real ou IP
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,noperm //SERVIDOR/documentos-juridicos /mnt/servidor

# Verificar
mount | grep servidor
ls /mnt/servidor

# Se funcionar:
echo "Montagem OK"

# Se FALHAR com erro (13) Permission denied:
# - GPO corporativa pode estar bloqueando
# - Ver seção "Cenário Alternativo A" abaixo

# Desmontar (após teste)
sudo umount /mnt/servidor
```

**Cenários de Erro:**

| Erro | Causa Provável | Solução |
|------|----------------|---------|
| `mount error(13): Permission denied` | GPO bloqueia CIFS OU credenciais inválidas | Validar credenciais, escalar para TI |
| `mount error(5): Input/output error` | Servidor offline ou inacessível | Verificar ping, VPN |
| `mount error(112): Host is down` | Nome/IP servidor incorreto | Validar `\\SERVIDOR` no Windows |
| `mount error(2): No such file or directory` | Share name incorreto | Validar path exato do share |

### 4.6 Configuração fstab (Montagem Persistente) (5 min)

**Se montagem manual funcionou:**

```bash
sudo nano /etc/fstab
```

**Adicionar linha (ajustar SERVIDOR):**

```
//SERVIDOR/documentos-juridicos /mnt/servidor cifs credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,file_mode=0644,dir_mode=0755,iocharset=utf8,noperm,_netdev 0 0
```

**Flags explicadas:**
- `vers=3.0`: Força SMB 3.0 (melhor performance)
- `uid=1000,gid=1000`: Arquivos aparecem como seu usuário WSL
- `file_mode=0644`: Read-only para usuário (write bloqueado por segurança)
- `noperm`: Ignora conflitos de permissões Windows vs Linux
- `_netdev`: Aguarda rede antes de montar (essencial)

**Testar fstab:**

```bash
sudo mount -a

# Verificar
mount | grep servidor
ls /mnt/servidor/processos/
```

### 4.7 Benchmark de Performance (15-30 min)

**Criar script de benchmark:**

```bash
mkdir -p ~/bin
cat > ~/bin/benchmark-servidor.sh << 'EOF'
#!/bin/bash

echo "=== Benchmark Servidor Corporativo ==="
echo ""

# Encontrar PDFs de tamanhos diferentes
SMALL_PDF=$(find /mnt/servidor/processos -name "*.pdf" -type f -size -1M 2>/dev/null | head -1)
MEDIUM_PDF=$(find /mnt/servidor/processos -name "*.pdf" -type f -size +1M -size -5M 2>/dev/null | head -1)
LARGE_PDF=$(find /mnt/servidor/processos -name "*.pdf" -type f -size +5M 2>/dev/null | head -1)

test_read() {
    local file=$1
    local label=$2

    if [ -z "$file" ]; then
        echo "[$label] SKIP - nenhum arquivo encontrado"
        return
    fi

    local size=$(du -h "$file" | cut -f1)
    echo "[$label] Arquivo: $(basename "$file") ($size)"

    # Executar 3 vezes (primeira pode ser cache miss)
    local total=0
    for i in 1 2 3; do
        local start=$(date +%s%N)
        cat "$file" > /dev/null 2>&1
        local end=$(date +%s%N)
        local duration=$(( (end - start) / 1000000 ))  # ms
        total=$((total + duration))
    done

    local avg=$((total / 3))
    echo "[$label] Tempo médio leitura: ${avg}ms"

    # Threshold validation
    if [ $avg -gt 500 ]; then
        echo "[$label] ❌ PROBLEMATICO: Cache obrigatório (>500ms)"
    elif [ $avg -gt 200 ]; then
        echo "[$label] ⚠️  ACEITAVEL: Cache recomendado (>200ms)"
    elif [ $avg -gt 100 ]; then
        echo "[$label] ✅ BOM: Cache opcional (100-200ms)"
    else
        echo "[$label] ✅ EXCELENTE: Processar direto (<100ms)"
    fi
    echo ""
}

# Executar testes
test_read "$SMALL_PDF" "PDF PEQUENO (<1MB)"
test_read "$MEDIUM_PDF" "PDF MEDIO (1-5MB)"
test_read "$LARGE_PDF" "PDF GRANDE (>5MB)"

echo "=== Benchmark Completo ==="
EOF

chmod +x ~/bin/benchmark-servidor.sh

# Executar
mkdir -p ~/logs
~/bin/benchmark-servidor.sh | tee ~/logs/sprint3-benchmark.log
```

**Interpretar resultados:**

- **< 100ms:** Performance excelente - Sprint 4 (cache) é OPCIONAL
- **100-200ms:** Performance boa - Sprint 4 recomendado para batch jobs
- **200-500ms:** Performance aceitável - Sprint 4 OBRIGATÓRIO
- **> 500ms:** Performance problemática - Escalar para TI (Defender? Rede?)

### 4.8 Criar Estrutura de Cache Local (5 min)

**Mesmo que servidor seja rápido, criar estrutura para uso futuro:**

```bash
mkdir -p ~/documentos-juridicos-cache/processos-ativos
mkdir -p ~/documentos-juridicos-cache/temp-processing
mkdir -p ~/claude-code-data/{inbox,processing,outputs,cache}
```

### 4.9 Validação Fase 4

```bash
# Servidor montado
mount | grep servidor
# Esperado: //SERVIDOR/documentos-juridicos on /mnt/servidor type cifs

# Arquivos acessíveis
ls /mnt/servidor/processos/ | head -5

# Leitura funcional
TEST_PDF=$(find /mnt/servidor -name "*.pdf" 2>/dev/null | head -1)
if [ -n "$TEST_PDF" ]; then
    cat "$TEST_PDF" > /dev/null && echo "✅ Leitura OK"
fi

# Performance aceitável
cat ~/logs/sprint3-benchmark.log | grep "Tempo médio"

# Montagem persiste após reinício WSL
# (testar em PowerShell: wsl --shutdown, aguardar 10s, wsl, mount | grep servidor)
```

**✅ Checkpoint:** Servidor montado, performance quantificada, cache estruturado.

---

## Cenário Alternativo A: GPO Bloqueia Montagem CIFS

**Se Fase 4.5 falhar com `mount error(13): Permission denied`:**

### Workaround: Robocopy (Windows) + /mnt/c/ (WSL)

**1. Criar cache Windows (PowerShell como Admin):**

```powershell
# Criar diretório
New-Item -Path "C:\servidor-cache" -ItemType Directory

# Testar robocopy manual
robocopy \\SERVIDOR\documentos-juridicos C:\servidor-cache /E /MT:8 /R:3 /W:5 /LOG:C:\logs\robocopy-test.log

# Verificar
dir C:\servidor-cache\processos\
```

**2. Configurar Task Scheduler (sincronização automática 2x/dia):**

```powershell
# Criar script
$scriptPath = "C:\scripts\sync-servidor.ps1"
New-Item -Path "C:\scripts" -ItemType Directory -Force

@"
`$Source = "\\SERVIDOR\documentos-juridicos"
`$Dest = "C:\servidor-cache"
`$Log = "C:\logs\robocopy-`$(Get-Date -Format 'yyyyMMdd-HHmm').log"

robocopy `$Source `$Dest /MIR /MT:16 /R:3 /W:5 /LOG:`$Log

# Criar flag para WSL
wsl touch ~/sync-trigger.flag
"@ | Out-File -FilePath $scriptPath -Encoding UTF8

# Criar tarefa agendada (8h e 14h, dias úteis)
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File `"$scriptPath`""
$trigger1 = New-ScheduledTaskTrigger -Daily -At 8:00AM -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday
$trigger2 = New-ScheduledTaskTrigger -Daily -At 2:00PM -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName "Sync-Servidor-WSL" -Action $action -Trigger $trigger1,$trigger2 -Principal $principal -Settings $settings
```

**3. WSL acessa via /mnt/c/ (performance degradada, mas funcional):**

```bash
# Criar symlink para facilitar
ln -s /mnt/c/servidor-cache ~/documentos-juridicos-cache

# Verificar
ls ~/documentos-juridicos-cache/processos/
```

**IMPORTANTE:** Performance via /mnt/c/ será 5-10x mais lenta. Sprint 4 (cache WSL nativo) torna-se OBRIGATÓRIO.

---

## Fase 5: Validação Final e Documentação (30 min)

### 5.1 Checklist Sprint 3

```bash
# ✅ Estrutura padronizada
pwd  # ~/claude-work/repos/Claude-Code-Projetos

# ✅ WSL2 funcional
lsb_release -a  # Ubuntu 24.04 LTS

# ✅ Node.js + Claude Code
node --version && claude --version

# ✅ Python venvs (5 agentes)
for venv in agentes/*/.venv; do
    if [ -d "$venv" ]; then
        echo "✅ $venv"
    fi
done

# ✅ Git sincronizado
git status

# ✅ Hooks testados (se não EPERM)
node .claude/hooks/session-context-hybrid.js

# ✅ Servidor acessível
ls /mnt/servidor/ || ls /mnt/c/servidor-cache/

# ✅ Benchmark documentado
cat ~/logs/sprint3-benchmark.log
```

### 5.2 Commit Documentação

**No PC TRABALHO (após Sprint 3):**

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Se criou settings.local.json (hooks desabilitados):
git add .claude/settings.local.json

# NÃO commitar (já está em .gitignore):
# - .venv/
# - node_modules/
# - logs/

git status  # Verificar apenas arquivos relevantes

# Commit (se houver mudanças)
git commit -m "docs: adiciona configuração PC trabalho (Sprint 3)

- WSL2 instalado e configurado
- Servidor corporativo montado em /mnt/servidor
- Benchmark performance: [COLAR RESULTADOS]
- SessionStart hooks: [HABILITADO/DESABILITADO - razão]
"

# Push
git push
```

### 5.3 Atualizar CHANGELOG.md

```bash
nano CHANGELOG.md
```

**Adicionar entrada:**

```markdown
## [Sprint 3] - 2025-11-15

### Added

- **PC Trabalho (Windows Corporativo):**
  - WSL2 Ubuntu 24.04 LTS instalado
  - Node.js v24.11.1 + Claude Code 2.0.42
  - Python 3.12.3 + 5 virtual environments
  - Servidor corporativo montado: /mnt/servidor
  - Benchmark performance servidor: [RESULTADOS]

### Changed

- Estrutura cross-machine: PC casa (APIs) + PC trabalho (servidor)
- Hooks SessionStart: [HABILITADO/DESABILITADO] no PC trabalho

### Infrastructure

- Windows Defender exclusion: WSL filesystem
- .wslconfig: 4GB RAM, 2 cores
- fstab: Auto-mount servidor corporativo (SMB 3.0)
- [SE APLICAVEL] Task Scheduler: Robocopy 2x/dia
```

### 5.4 Sincronizar com PC Casa

**PC Casa (quando voltar):**

```bash
cd ~/claude-work/repos/Claude-Code-Projetos
git pull

# Revisar mudanças do PC trabalho
git log --oneline -5
```

---

## Troubleshooting Comum

### Problema: WSL não inicia após instalação

**Solução:**

```powershell
# PowerShell como Admin
wsl --status

# Se mostrar erro, reinstalar:
wsl --unregister Ubuntu-24.04
wsl --install -d Ubuntu-24.04
```

### Problema: `mount error(13)` ao montar servidor

**Diagnóstico:**

```bash
# Testar autenticação SMB
smbclient -L //SERVIDOR -U usuario%senha

# Se smbclient funciona mas mount não:
# → GPO bloqueia montagem, usar Workaround Alternativo A
```

### Problema: Hooks causam EPERM loop

**Sintoma:** Claude Code trava ao iniciar, arquivo `.claude.json.lock` fica locked.

**Solução:**

```bash
# Desabilitar SessionStart hooks
cat > .claude/settings.local.json << 'EOF'
{
  "hooks": {
    "sessionStart": {
      "enabled": false
    }
  }
}
EOF

# Remover lock se existir
rm -f .claude/.claude.json.lock

# Reiniciar Claude Code
claude
```

### Problema: Performance WSL muito lenta

**Diagnóstico:**

```bash
# Benchmark simples
time ls -R ~/claude-work/repos/Claude-Code-Projetos > /dev/null

# Se > 5 segundos:
# 1. Verificar Windows Defender exclusion
# 2. Verificar .wslconfig (RAM suficiente?)
# 3. Reiniciar WSL: wsl --shutdown (PowerShell)
```

---

## Próximos Passos

Após Sprint 3:

- **Sprint 4:** Sistema de cache híbrido (se benchmark > 200ms)
- **Sprint 5:** Adaptação de código para usar servidor/cache
- **Sprint 6:** Infraestrutura .claude/ e documentação final

---

## Estimativas de Tempo

**Otimista (sem problemas):**
- Fase 1: 1h
- Fase 2: 30min
- Fase 3: 45min
- Fase 4: 1h
- **Total: 3h15min**

**Provável (troubleshooting moderado):**
- Fase 1: 2h (virtualização, defender)
- Fase 2: 1h (autenticação Claude)
- Fase 3: 1h (venvs, npm)
- Fase 4: 2h (credenciais, montagem)
- **Total: 6h**

**Pessimista (GPO bloqueia, EPERM hooks):**
- Fase 1: 3h (permissões Admin, escalação TI)
- Fase 2: 1h30min
- Fase 3: 1h30min
- Fase 4: 4h (GPO troubleshooting, Workaround A)
- **Total: 10h**

---

**Última atualização:** 2025-11-15
**Responsável:** Sprint 3 - Setup PC Trabalho
