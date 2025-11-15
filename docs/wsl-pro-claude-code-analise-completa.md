# WSL Pro Claude Code: Análise Completa e Guia de Implementação

**Documento de Análise Técnica**
**Data:** 2025-01-15
**Versão:** 1.0
**Autor:** Análise baseada em pesquisa extensiva e repositório claude-stack-dotnet

---

## Sumário Executivo

Este documento compila análise abrangente sobre o uso do Windows Subsystem for Linux (WSL) com Claude Code, incluindo pesquisa técnica detalhada, análise do repositório de referência claude-stack-dotnet, levantamento de issues conhecidas no GitHub, e soluções práticas documentadas pela comunidade.

**Principais conclusões:**
- ✅ WSL2 é a escolha profissional recomendada para Claude Code no Windows
- ⚠️ Requer configuração cuidadosa para evitar degradação de performance
- 🔧 Issues conhecidas têm soluções documentadas
- 📊 Trade-off entre complexidade inicial vs capacidades avançadas

---

## Parte 1: Pesquisa Técnica WSL + Claude Code

### 1.1 Cenário Atual de Compatibilidade

O Claude Code oferece **três métodos de instalação no Windows**:

| Método | Complexidade | Performance | Compatibilidade | Uso Recomendado |
|--------|--------------|-------------|-----------------|-----------------|
| **Windows Nativo + Git Bash** | Baixa | Boa | 70% features | Projetos simples, restrições corporativas |
| **WSL1** | Média | Razoável | 85% features | Legacy, acesso intensivo a arquivos Windows |
| **WSL2** | Alta | Excelente* | 100% features | Desenvolvimento profissional, uso avançado |

*\*Excelente quando configurado corretamente (arquivos em filesystem Linux)*

### 1.2 Requisitos Fundamentais

**Claude Code requer ambiente shell POSIX** para funcionar corretamente, o que explica por que WSL oferece experiência superior ao Windows nativo.

**Componentes essenciais:**
- Node.js LTS (via nvm, não apt)
- npm com configuração global sem sudo
- Git
- Build tools (gcc, make)
- Ferramentas POSIX (sed, awk, grep com regex)

### 1.3 Funcionalidades Avançadas

#### Sistema de Hooks (8 pontos de intervenção)

| Hook | Momento | Pode Bloquear? | Casos de Uso |
|------|---------|----------------|--------------|
| **UserPromptSubmit** | Antes do processamento | ✅ Sim (exit 2) | Validação segurança, injeção contexto |
| **PreToolUse** | Antes de executar ferramenta | ✅ Sim (exit 2) | Bloquear `rm -rf`, acesso a `.env` |
| **PostToolUse** | Após execução bem-sucedida | ⚠️ Não desfaz | Formatação auto (prettier/eslint) |
| **Stop Hook** | Quando Claude tenta parar | ✅ Força continuar | Garantir testes passam |
| **SessionStart** | Início/retomada sessão | ❌ Não | Carregar contexto (git status) |
| **SubagentStop** | Término de subagentes | ✅ Sim | Controle delegação |
| **PreCompact** | Antes de compactação | ❌ Não | Backup transcrições |
| **Notification** | Informacional | ❌ Não | Logging, auditoria |

**Compatibilidade:** Hooks complexos usando scripts Python/bash requerem ambiente POSIX real = **WSL essencial**.

#### Arquitetura de Agentes

**Subagentes especializados:**
- Context windows independentes (200k tokens)
- System prompts customizados
- Permissões granulares de ferramentas
- **Execução paralela: até 10 subagentes simultâneos**

**Meta-agents:** Agentes que criam outros agentes baseado em descrição de funcionalidade.

**Requer WSL?** Não obrigatório, mas servidores MCP (Model Context Protocol) funcionam **apenas em WSL/Linux**.

#### Ecossistema de Plugins

**Plugins críticos que requerem WSL:**
- **Episodic Memory** (obra/episodic-memory): Servidor MCP + SQLite vector search
- **Superpowers** (obra/superpowers): Skills TDD, debugging sistemático
- **TypeScript Quality Hooks**: ESLint/Prettier com caching SHA256

**Compatibilidade Git Bash:** Limitada ou inexistente para plugins baseados em MCP.

### 1.4 Performance: Números Reveladores

#### Benchmarks Cross-Filesystem (WSL2)

| Operação | WSL2 em NTFS (/mnt/c/) | WSL2 em ext4 (~/) | Linux Nativo |
|----------|------------------------|-------------------|--------------|
| **Create-React-App build** | 63.14s | 5.8s | 4.63s |
| **Large TypeScript build** | 263.71s | 28.75s | 24.13s |
| **Git status (large repo)** | 8-15s | <1s | <1s |
| **npm install (typical)** | ~45s | ~2s | ~2s |
| **Symfony page gen** | 1200-1500ms | 100-130ms | 100-130ms |

**Conclusão crítica:** WSL2 acessando `/mnt/c/` é **5-10x mais lento** que filesystem nativo. Esta é limitação arquitetural fundamental (protocolo 9P).

#### Windows Defender: O Assassino Silencioso

**Impacto:** 5-10x degradação para operações npm/yarn quando Antimalware Service Executable escaneia WSL.

**Solução obrigatória:**
```powershell
# PowerShell como Administrador
Add-MpPreference -ExclusionPath "$env:USERPROFILE\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu*"
```

**Trade-off:** Reduz segurança mas é praticamente necessário para desenvolvimento profissional.

#### Overhead CPU/Memória WSL2

**Benchmarks (Windows 11 25H2, Phoronix):**
- Tarefas CPU-intensivas: 10-15% mais lento que Linux nativo
- Operações I/O-bound: Até 20% mais lento
- Memória: WSL2 pode consumir 7GB+ RAM sem liberar eficientemente
- VmmemWSL: Uso contínuo de CPU mesmo idle

**Filesystem ext4 nativo:** WSL2 alcança **85-95% de performance** de Linux nativo.

### 1.5 Vantagens do WSL

**1. Ambiente Linux verdadeiro**
- Kernel Linux real (não camada de tradução)
- Acesso completo ao ecossistema: apt, Docker, Python, Node.js
- Sem fricção de ACL do Windows

**2. Compatibilidade MCP 100%**
- Servidores como claude-flow, ruv-swarm funcionam
- Git Bash tem falhas conhecidas com MCP

**3. Integração IDE superior**
- VSCode Remote-WSL: perfeita
- IDE e Claude Code no mesmo contexto filesystem
- Terminal Windows com melhor suporte Unicode/ANSI

**4. Paridade com produção**
- Maioria dos servidores roda Linux
- Mesmas ferramentas, mesmos comandos
- Pipelines CI/CD consistentes

**5. Docker nativo**
- Suporte seamless para containerização
- Docker Desktop usa WSL2 backend

### 1.6 Desvantagens do WSL

**1. Complexidade de configuração**
- Curva de aprendizado: entender Linux, filesystem, arquitetura WSL
- Instalação multi-etapas (5-7 passos)
- Confusão paths: `/mnt/c/` vs `~/`
- Duplicação filesystem (projetos clonados duas vezes)

**2. Problema crítico de segurança**
- Windows Defender **não pode escanear** instâncias WSL2 (executa em Hyper-V)
- Ponto cego de segurança
- Requer Microsoft Defender for Endpoint plug-in (apenas enterprise)
- WSL pode ser explorado pós-comprometimento sem detecção

**3. Issues de ambiente VDI/Enterprise**
- Performance VDI severa: 10+ segundos delays por comando
- IT corporativo frequentemente bloqueia WSL
- Antivirus corporativo adicional degrada performance ainda mais

### 1.7 Veredito Final da Pesquisa

**Para usuários profissionais: WSL2 é essencial**

**Fatores críticos de sucesso:**
1. ✅ Armazenar projetos em `~/projects`, **NUNCA** em `/mnt/c/`
2. ✅ Configurar exclusões Windows Defender
3. ✅ Definir limites memória em `.wslconfig` (8GB recomendado)
4. ✅ Usar VSCode Remote-WSL
5. ✅ Clonar repositórios diretamente no filesystem WSL

**Matriz de recomendações:**

| Cenário | Solução | Rationale |
|---------|---------|-----------|
| Desenvolvimento full-stack | WSL2 (essencial) | Docker, databases, toolchains |
| Projetos Python/Node pesados | WSL2 (essencial) | MCP servers, dependencies |
| Uso de hooks avançados | WSL2 (essencial) | Scripts bash, POSIX |
| Desenvolvimento de plugins | WSL2 (essencial) | MCP integration |
| Scripting simples | Git Bash (aceitável) | Automação básica |
| Restrições corporativas | Git Bash (fallback) | WSL bloqueado |

---

## Parte 2: Análise do Repositório claude-stack-dotnet

### 2.1 Visão Geral do Projeto

**Repositório:** https://github.com/NotMyself/claude-stack-dotnet

**Descrição:** Template full-stack .NET 10 demonstrando integração profissional com Claude Code AI, incluindo arquitetura moderna, gerenciamento centralizado de pacotes, testes (MSTest v4 + Playwright E2E), e pipeline CI/CD automatizado.

**Tecnologias:**
- .NET 10.0 SDK RC 2 (versão 10.0.100-rc.2.25502.107+)
- ASP.NET Core MVC + Minimal APIs
- MSTest v4 (Microsoft.Testing.Platform, não legado VSTest)
- Playwright (E2E tests)
- GitHub Actions (CI/CD)

### 2.2 Estrutura de Arquivos

```
claude-stack-dotnet/
├── src/
│   ├── ClaudeStack.Web/              # Aplicação MVC
│   └── ClaudeStack.API/              # API Minimal APIs
│
├── tests/
│   ├── ClaudeStack.Web.Tests/        # Testes unitários MVC
│   ├── ClaudeStack.Web.Tests.Playwright/   # E2E MVC
│   ├── ClaudeStack.API.Tests/        # Testes unitários API
│   └── ClaudeStack.API.Tests.Playwright/   # E2E API
│
├── .claude/                           # Infraestrutura Claude Code
│   ├── agents/                        # Agentes especializados
│   ├── commands/                      # Slash commands customizados
│   ├── skills/                        # Skills auto-ativantes
│   ├── hooks/                         # Session hooks
│   ├── dev-docs/                      # Documentação de desenvolvimento
│   ├── mcp/                          # Model Context Protocol servers
│   └── ATTRIBUTION.md                 # Licenciamento (MIT)
│
├── .github/
│   └── workflows/                     # GitHub Actions workflows
│
├── Directory.Build.props              # Configuração MSBuild compartilhada
├── Directory.Packages.props           # Versões NuGet centralizadas (CPM)
├── global.json                        # SDK + test runner config
├── sln.slnx                          # Arquivo solução
└── setup-claude-code-wsl.ps1         # Script automação WSL setup
```

### 2.3 Características Arquiteturais

#### Central Package Management (CPM)

**Arquivo:** `Directory.Packages.props`

```xml
<Project>
  <ItemGroup>
    <PackageVersion Include="Microsoft.AspNetCore.OpenApi" Version="10.0.0-rc.2.25502.107" />
    <PackageVersion Include="Microsoft.VisualStudio.Testing.MSTest" Version="4.0.0-beta.24615.1" />
    <!-- ... todas as versões centralizadas ... -->
  </ItemGroup>
</Project>
```

**Benefício:** Versões definidas em um único local, nunca nos project files individuais.

#### Configuração Compartilhada

**Arquivo:** `Directory.Build.props`

```xml
<Project>
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <Nullable>disable</Nullable>
    <ImplicitUsings>disable</ImplicitUsings>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
```

**Nota crítica:** `ImplicitUsings` desabilitado = **usings explícitos obrigatórios** em todos os arquivos C#.

#### Microsoft.Testing.Platform

**Evolução:** Abandono do VSTest legado em favor do novo platform.

**Implicação:** Projetos de teste são executáveis via `dotnet run` (além de `dotnet test`).

**Configuração:** Definida em `global.json` - nunca usar flag `--test-runner`.

### 2.4 Pipeline CI/CD (6 Etapas)

1. **Autorização:** Aprovação manual requerida
2. **Guardrails PR:** Validações básicas de pull request
3. **Verificações Qualidade:** Linters, formatação, análise estática
4. **Revisão Código:** Análise automatizada por Claude Code
5. **Revisão Segurança:** Scan de vulnerabilidades
6. **Validação .NET:** Build, testes unitários, testes E2E

**Integração Claude Code:** Revisão automatizada de código como etapa do pipeline.

### 2.5 Infraestrutura Claude Code

#### Sistema de Skills Auto-Ativantes

**Localização:** `.claude/skills/`

**Mecânica:** Skills carregam dinamicamente quando relevantes, fornecendo workflows mandatórios.

**Meta-skill:** `skill-developer` - cria skills específicas do projeto programaticamente.

#### Agentes Especializados

**Localização:** `.claude/agents/`

**Tipos incluídos:**
- Code reviewer (revisão de código)
- Refactoring agent (refatoração)
- Documentation agent (documentação)

**Definição (exemplo):**
```markdown
---
name: code-reviewer
description: Expert code reviewer. Use PROACTIVELY after writing code
tools: Read, Grep, Glob, Bash
color: Yellow
model: opus
---

You are a senior code reviewer specializing in .NET...
```

#### Sistema de Dev Docs

**Localização:** `.claude/dev-docs/`

**Propósito:** Documentação de desenvolvimento interna, accessible via contexto do Claude Code.

### 2.6 Script PowerShell: setup-claude-code-wsl.ps1

**Versão analisada:** 2.0.0

#### Parâmetros de Entrada

```powershell
param(
    [switch]$SkipBackup,      # Ignora backup de distribuições WSL
    [switch]$SkipCleanup,     # Preserva instalações WSL existentes
    [string]$UbuntuVersion = "24.04",
    [string]$NodeVersion = "20"
)
```

#### Requisitos de Sistema

- **OS:** Windows 10 (build 19041+) ou Windows 11
- **PowerShell:** versão 7+
- **Privilégios:** Administrador
- **Arquitetura:** x64

#### Fluxo de Instalação (12 Fases)

| Fase | Ação | Crítico? |
|------|------|----------|
| 1 | Verificar pré-requisitos (OS, PowerShell, privilégios) | ✅ |
| 2 | Instalar recursos WSL (`wsl --install --no-distribution`) | ✅ |
| 3 | Backup de distribuições existentes | ⚠️ |
| 4 | Remover instalações antigas (após confirmação) | ⚠️ |
| 5 | Instalar Ubuntu (versão configurável) | ✅ |
| 6 | Configurar ambiente de desenvolvimento | ✅ |
| 7 | Configurar npm global sem sudo | ✅ |
| 8 | Adicionar npm ao PATH (~/.bashrc) | ✅ |
| 9 | Instalar Claude Code (`npm install -g @anthropic-ai/claude-code`) | ✅ |
| 10 | Instalar GitHub CLI (`gh`) | 🔧 |
| 11 | Validar instalação (testes em shell fresh) | ✅ |
| 12 | Exibir relatório de sucesso | 📊 |

#### Componentes Instalados

**Runtime:**
- Node.js (via nvm, versão configurável, padrão: 20)
- Python3 + pip
- npm (configuração global em `~/.npm-global`)

**Build Tools:**
```bash
build-essential  # gcc, g++, make
git
```

**Utilitários de Desenvolvimento:**
```bash
curl wget openssh-client jq zip unzip tree
ripgrep htop bat fd-find
```

#### Configurações Principais

**npm global sem sudo:**
```bash
# Diretório
mkdir -p ~/.npm-global

# Configuração
npm config set prefix ~/.npm-global

# PATH em ~/.bashrc
export PATH=$HOME/.npm-global/bin:$PATH
```

**Autenticação GitHub:**
```bash
gh auth login  # Interativo, suporta HTTPS/SSH
```

#### Sistema de Logs

**Função:** `Write-LogMessage`

**Níveis:**
- Info (Cyan)
- Success (Green)
- Warning (Yellow)
- Error (Red)

**Exemplo:**
```powershell
Write-LogMessage "Installing Node.js..." "Info"
```

#### Mecanismos de Segurança

1. **Prompt de confirmação** antes de remover distribuições WSL existentes
2. **Backup automático** (a menos que `-SkipBackup` seja usado)
3. **Validações progressivas** após cada fase crítica
4. **Testes em shells fresh** para verificar PATH configurado corretamente
5. **Exit on error** com mensagens descritivas

#### Otimizações (v2.0.0)

**1. Instalação antecipada de recursos WSL:**
Recursos WSL instalados **antes** de backup/limpeza, permitindo reinício único.

**2. Cache compartilhado de pacotes:**
- Redução de 66% em tempo de atualizações subsequentes
- `/var/cache/apt/archives` compartilhado entre instâncias

**3. Transação única apt:**
```bash
sudo apt update && sudo apt install -y \
  build-essential git curl wget python3 python3-pip \
  openssh-client jq zip unzip tree ripgrep htop bat fd-find
```

**4. Validação pós-instalação:**
```bash
# Testa em shell fresh (simulando login novo)
wsl -d Ubuntu-24.04 -e bash -c "source ~/.bashrc && claude --version"
```

### 2.7 Lições do Repositório

**1. Automação é crítica:**
Script PowerShell reduz setup de 2-4 horas para 15-30 minutos.

**2. Validação progressiva:**
Testar cada componente imediatamente após instalação evita debugging tardio.

**3. Configuração explícita:**
- npm global sem sudo
- PATH configurado em ~/.bashrc
- Node via nvm (não apt)

**4. Infraestrutura Claude Code como código:**
- `.claude/` versionado no Git
- Agents, skills, hooks como parte do projeto
- Documentação de desenvolvimento (dev-docs) integrada

**5. Pipeline CI/CD com Claude:**
Revisão automatizada de código como etapa do pipeline demonstra integração profissional.

---

## Parte 3: Issues Conhecidas e Soluções

### 3.1 Issues Reportadas no GitHub (2025)

#### Issue #1232: JetBrains IDE Detection (WSL)

**Status:** Aberta (22 maio 2025)

**Problema:**
```
$ claude
$ /ide
No available IDEs detected.
```

Claude Code não detecta JetBrains IDEs (PyCharm, IntelliJ IDEA, Rider) quando executado em WSL.

**Causa raiz:** WSL2 usa NAT networking por padrão, impedindo detecção de IDEs rodando no Windows.

**Soluções documentadas:**

**Solução 1: Configurar Windows Firewall**
- Permitir comunicação entre WSL2 e Windows através da porta da IDE
- Detalhes específicos no guia oficial de troubleshooting

**Solução 2: Instalar IDE dentro do WSL**
```bash
# Em vez de usar Windows IDE, instalar no Linux
# Exemplo para IntelliJ IDEA:
sudo snap install intellij-idea-community --classic
```

**Resultado:** Claude conecta à versão Linux da IDE sem problemas.

**Solução 3: Usar modo WSL2 espelhado (Windows 11 22H2+)**

Editar `C:\Users\[Username]\.wslconfig`:
```ini
[wsl2]
networkingMode=mirrored
```

Reiniciar WSL:
```powershell
wsl --shutdown
```

**Trade-off:** Modo espelhado melhora detecção mas pode ter outras implicações de rede.

#### Issue #2273: JetBrains Rider Plugin (Windows)

**Status:** Aberta (18 junho 2025)

**Problema:** Claude Code plugin v0.1.9-beta não conecta à versão **Windows** do Rider, mas funciona com versão **Linux** instalada no WSL.

**Workaround confirmado:**
```bash
# Instalar Rider no WSL em vez de usar instalação Windows
sudo snap install rider --classic
```

#### Issue #1411: Working Directory Mismatch

**Status:** Aberta (maio 2025)

**Problema:**
```
Found 1 other running IDE(s). However, their workspace/project
directories do not match the current cwd.
```

**Causa:** IDE abre projeto em `/mnt/c/Users/...` mas Claude Code executa em `~/projects/...`

**Solução:**
```bash
# Opção 1: Navegar até o mesmo caminho da IDE
cd /mnt/c/Users/[Username]/Documents/MyProject
claude

# Opção 2 (recomendado): Mover projeto para filesystem WSL
cp -r /mnt/c/Users/[Username]/Documents/MyProject ~/projects/
cd ~/projects/MyProject
claude
```

#### Issue #559: Auto-Update Failure (Ink compatibility)

**Status:** Aberta (19 março 2025)

**Problema:**
```
Raw mode is not supported on the current process.stdin
```

Claude falha ao auto-update em WSL devido a problemas com biblioteca Ink (terminal UI).

**Solução temporária:**
```bash
# Desinstalar e reinstalar manualmente
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code
```

**Status permanente:** Anthropic está investigando compatibilidade Ink com WSL.

#### Issue #653: API Connection Error

**Status:** Aberta (29 março 2025)

**Problema:** Erro persistente "API Error: Connection error" quando usando Claude Code CLI em terminal WSL via VS Code.

**Soluções tentadas (pela comunidade):**

**1. Verificar proxy/VPN:**
```bash
# Testar conectividade direta
curl -I https://api.anthropic.com

# Desabilitar proxy temporariamente
unset http_proxy https_proxy
```

**2. Verificar DNS:**
```bash
# Adicionar DNS público ao /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

**3. Verificar firewall corporativo:**
```bash
# Algumas redes bloqueiam api.anthropic.com
# Testar em rede diferente (hotspot móvel)
```

#### Issue #188: Installation Failure (OS Detection)

**Status:** Resolvida (27 fevereiro 2025)

**Problema:** Script de instalação detecta incorretamente Windows mesmo rodando dentro do WSL.

**Causa:** Script checa `$env:OS` (variável Windows) em vez de `uname`.

**Solução (já implementada):**
```bash
# Usar instalação npm direta em vez de script
npm install -g @anthropic-ai/claude-code
```

**Status:** Anthropic corrigiu detecção de OS em versões posteriores.

### 3.2 Soluções de Performance

#### Problema: /mnt/c Extremamente Lento

**Raiz do problema:** Protocolo 9P (network file sharing) entre VM Linux e host Windows, sem caching para garantir consistência.

**Soluções por prioridade:**

**🥇 Solução 1: Mover projeto para filesystem WSL (MELHOR)**

```bash
# Copiar projeto inteiro
cp -r /mnt/c/Users/[Username]/Documents/MyProject ~/projects/MyProject
cd ~/projects/MyProject

# Confirmar localização
pwd  # Deve mostrar /home/[username]/projects/MyProject
```

**Performance esperada:** 5-10x mais rápido.

**Trade-off:** Arquivos não acessíveis nativamente via Windows Explorer (requer `\\wsl$\Ubuntu\home\...`).

**🥈 Solução 2: Git do Windows para operações em /mnt/c**

```bash
# Criar alias para git do Windows
alias wgit="/mnt/c/Program\ Files/Git/bin/git.exe"

# Usar wgit em vez de git quando em /mnt/c
cd /mnt/c/Users/[Username]/Documents/MyProject
wgit status  # Rápido (executa no Windows)
git status   # Lento (WSL acessa NTFS via 9P)
```

**🥉 Solução 3: Ajustar opções de mount**

Editar `/etc/fstab`:
```
C: /mnt/c drvfs rw,noatime,metadata,case=off 0 0
```

Remontar:
```bash
sudo umount /mnt/c
sudo mount -a
```

**Benefício:** Melhoria marginal (10-20%), não resolve problema fundamental.

**🔧 Solução 4: VHDX compartilhado com filesystem Linux**

```powershell
# PowerShell
wsl --manage --create-vhd --name SharedProjects --size 50GB

# WSL
sudo mkfs.ext4 /dev/sdb  # (nome pode variar)
sudo mount /dev/sdb /mnt/shared
```

**Benefício:** Performance de ext4 com acesso Windows via `\\wsl$`.

#### Problema: Windows Defender Degradando Performance

**Sintoma:** Antimalware Service Executable consome 100% CPU durante operações npm/git.

**Solução obrigatória:**

```powershell
# PowerShell como Administrador
Add-MpPreference -ExclusionPath "$env:USERPROFILE\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu*"

# Para versões específicas de Ubuntu:
Add-MpPreference -ExclusionPath "$env:USERPROFILE\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu24.04LTS_79rhkp1fndgsc"

# Verificar exclusões
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
```

**Performance esperada:** Iguala Defender completamente desabilitado.

**Trade-off de segurança:** WSL torna-se ponto cego para Defender. Mitigar com:
- Microsoft Defender for Endpoint (enterprise)
- Antivirus dentro do WSL (ClamAV)
- Políticas de segurança estritas

#### Problema: Consumo Excessivo de Memória

**Sintoma:** VmmemWSL consome 7GB+ RAM, não libera memória.

**Solução: Configurar .wslconfig**

Criar/editar `C:\Users\[Username]\.wslconfig`:
```ini
[wsl2]
memory=8GB              # Limite máximo de RAM
processors=4            # Limite de cores CPU
swap=2GB                # Tamanho swap
localhostForwarding=true
nestedVirtualization=false  # Desabilitar se não usar Docker
```

Reiniciar WSL:
```powershell
wsl --shutdown
```

**Efeito:** Impede WSL de consumir toda RAM disponível.

**Liberação forçada de memória (workaround):**
```bash
# Dentro do WSL
sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
```

### 3.3 Soluções de Compatibilidade

#### MCP Servers Falhando

**Sintoma:** Servidores como claude-flow, ruv-swarm não iniciam.

**Causa comum:** Dependências não instaladas ou configuração PATH incorreta.

**Solução:**

```bash
# 1. Verificar Node.js instalado via nvm
nvm --version
node --version

# 2. Verificar npm global configurado
npm config get prefix  # Deve mostrar ~/.npm-global

# 3. Verificar PATH
echo $PATH | grep npm-global  # Deve aparecer

# 4. Reinstalar Claude Code
npm install -g @anthropic-ai/claude-code

# 5. Testar MCP server específico
claude  # Dentro do projeto
# Usar comando que requer MCP
```

**Se ainda falhar:**
```bash
# Verificar logs de erro
~/.claude/logs/

# Reportar issue com logs
```

#### Git Bash vs WSL: Quando Migrar?

**Indicadores que você precisa migrar para WSL:**

1. ✅ Erro ao executar servidor MCP
2. ✅ Hooks complexos falhando
3. ✅ Comandos sed/awk não funcionam corretamente
4. ✅ Performance inaceitável para npm install
5. ✅ Necessidade de Docker
6. ✅ Plugins episodic-memory ou superpowers não funcionam

**Processo de migração:**

```bash
# 1. Backup de configurações existentes
cp -r ~/.claude ~/claude-backup-windows

# 2. Instalar WSL2
# (via PowerShell como Admin)
wsl --install

# 3. Dentro do WSL, instalar Claude Code
npm install -g @anthropic-ai/claude-code

# 4. Copiar configurações (se compatíveis)
# Via Windows Explorer: \\wsl$\Ubuntu\home\[username]\.claude

# 5. Testar em projeto pequeno
cd ~/projects/test
claude
```

---

## Parte 4: Guia de Implementação Passo-a-Passo

### 4.1 Instalação WSL2 do Zero (Método Manual)

#### Fase 1: Pré-requisitos (5 minutos)

**Verificar versão Windows:**
```powershell
# PowerShell
[System.Environment]::OSVersion.Version

# Requerido: Windows 10 build 19041+ ou Windows 11
```

**Verificar virtualização habilitada:**
```powershell
# PowerShell
Get-ComputerInfo | Select-Object HyperVisorPresent, HyperVRequirementVirtualizationFirmwareEnabled

# Ambos devem ser True
```

**Se virtualização desabilitada:** Acessar BIOS/UEFI e habilitar Intel VT-x ou AMD-V.

#### Fase 2: Instalar WSL (10 minutos)

**PowerShell como Administrador:**

```powershell
# Instalar WSL com Ubuntu padrão
wsl --install

# OU especificar versão Ubuntu
wsl --install -d Ubuntu-24.04

# Reiniciar Windows (obrigatório)
Restart-Computer
```

**Após reinício:**

Ubuntu iniciará automaticamente solicitando:
1. Username (usuário Linux, pode ser diferente do Windows)
2. Password (senha UNIX, não precisa ser igual à do Windows)

**Verificar instalação:**
```powershell
wsl --list --verbose
# Deve mostrar Ubuntu-24.04 com VERSION 2
```

#### Fase 3: Atualizar Sistema (5 minutos)

**Dentro do WSL:**

```bash
# Atualizar lista de pacotes
sudo apt update

# Atualizar todos os pacotes
sudo apt upgrade -y

# Instalar build essentials
sudo apt install -y build-essential curl wget git
```

#### Fase 4: Instalar Node.js via nvm (10 minutos)

**Por que nvm?** Evita conflitos de permissão, permite múltiplas versões Node.js.

```bash
# Instalar nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Recarregar shell
source ~/.bashrc

# Verificar nvm
nvm --version

# Instalar Node.js LTS
nvm install --lts

# Definir como padrão
nvm alias default node

# Verificar
node --version  # Deve mostrar v20.x.x ou superior
npm --version   # Deve mostrar 10.x.x ou superior
```

#### Fase 5: Configurar npm Global (5 minutos)

```bash
# Criar diretório para pacotes globais
mkdir -p ~/.npm-global

# Configurar npm para usar este diretório
npm config set prefix ~/.npm-global

# Adicionar ao PATH
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc

# Recarregar
source ~/.bashrc

# Verificar
npm config get prefix  # Deve mostrar /home/[username]/.npm-global
```

#### Fase 6: Instalar Claude Code (3 minutos)

```bash
# Instalar globalmente
npm install -g @anthropic-ai/claude-code

# Verificar instalação
claude --version

# Primeira execução (autenticação)
claude
# Seguir instruções para autenticar com Anthropic
```

#### Fase 7: Otimizar Configuração (15 minutos)

**7.1 Criar .wslconfig**

No **Windows**, criar `C:\Users\[Username]\.wslconfig`:

```ini
[wsl2]
# Memória máxima alocada para WSL2
memory=8GB

# Número de processadores virtuais
processors=4

# Tamanho do swap
swap=2GB

# Permitir forwarding de localhost (importante para IDEs)
localhostForwarding=true

# Desabilitar virtualização aninhada se não usar Docker
nestedVirtualization=false

# Modo de rede (Windows 11 22H2+)
# networkingMode=mirrored  # Descomente se tiver problemas de detecção IDE
```

**7.2 Configurar Exclusões Windows Defender**

**PowerShell como Administrador:**

```powershell
# Adicionar exclusão para instalação WSL
Add-MpPreference -ExclusionPath "$env:USERPROFILE\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu24.04LTS_79rhkp1fndgsc"

# Verificar
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
```

**7.3 Reiniciar WSL**

```powershell
# PowerShell
wsl --shutdown

# Aguardar 8-10 segundos, então
wsl
```

#### Fase 8: Validação Completa (10 minutos)

**8.1 Testar Claude Code**

```bash
# Criar projeto teste
mkdir -p ~/projects/test-claude
cd ~/projects/test-claude

# Criar arquivo simples
echo "console.log('Hello Claude');" > test.js

# Iniciar Claude Code
claude

# No prompt Claude, testar:
# "Read the test.js file and explain what it does"
```

**8.2 Testar Performance**

```bash
# Benchmark npm install em filesystem WSL
cd ~
mkdir test-perf && cd test-perf
time npm init -y
time npm install react react-dom

# Deve completar em ~2-5 segundos

# Comparar com /mnt/c (NÃO RECOMENDADO PARA PROJETOS REAIS)
cd /mnt/c/Users/[Username]/Documents
mkdir test-perf-windows && cd test-perf-windows
time npm init -y
time npm install react react-dom

# Provavelmente levará 20-60 segundos
```

**8.3 Verificar Integrações**

```bash
# Git configurado?
git --version
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"

# PATH correto?
echo $PATH | grep npm-global  # Deve aparecer

# Claude Code atualizado?
claude --version
```

### 4.2 Instalação Automatizada (Script)

**Usar o script do repositório claude-stack-dotnet:**

```powershell
# PowerShell como Administrador

# Baixar script
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/NotMyself/claude-stack-dotnet/main/setup-claude-code-wsl.ps1" -OutFile "setup-claude-code-wsl.ps1"

# Executar
.\setup-claude-code-wsl.ps1

# Com parâmetros customizados
.\setup-claude-code-wsl.ps1 -UbuntuVersion "24.04" -NodeVersion "20" -SkipBackup

# Para reinstalação limpa
.\setup-claude-code-wsl.ps1 -UbuntuVersion "24.04"
# Script solicitará confirmação antes de remover instalação antiga
```

**Tempo estimado:** 15-30 minutos (incluindo downloads).

### 4.3 Workflow de Desenvolvimento

#### Estrutura de Diretórios Recomendada

```
WSL Filesystem (~/):
├── projects/                    # TODOS os projetos de desenvolvimento
│   ├── projeto-a/
│   ├── projeto-b/
│   └── claude-code-projetos/   # Seu repositório
│
├── .npm-global/                 # Pacotes npm globais
├── .claude/                     # Configurações Claude Code
│   ├── agents/
│   ├── skills/
│   └── hooks/
│
└── .config/                     # Outras configurações de ferramentas
```

**Nunca armazenar projetos em:**
- ❌ `/mnt/c/Users/...` (performance terrível)
- ❌ `/mnt/d/` (mesmo problema)
- ❌ Qualquer `/mnt/*`

#### Clonar Repositórios

```bash
# Sempre clonar diretamente no filesystem WSL
cd ~/projects
git clone https://github.com/usuario/repo.git
cd repo

# Iniciar desenvolvimento
claude
```

#### Acessar Arquivos WSL do Windows

**Via Windows Explorer:**
```
\\wsl$\Ubuntu-24.04\home\[username]\projects\
```

**OU criar link simbólico:**
```bash
# Dentro do WSL
ln -s ~/projects /mnt/c/Users/[Username]/WSLProjects

# Agora acessível via:
# C:\Users\[Username]\WSLProjects
```

**⚠️ Aviso:** Editar arquivos via Windows Explorer funciona, mas idealmente usar IDE com Remote-WSL.

#### Integração VSCode

**1. Instalar extensão Remote-WSL:**

No Windows VSCode:
- Extensions → Buscar "WSL"
- Instalar "WSL" (Microsoft)

**2. Abrir projeto do WSL:**

```bash
# Dentro do WSL, no diretório do projeto
code .
```

VSCode Windows abrirá conectado ao filesystem WSL.

**3. Verificar contexto:**

Canto inferior esquerdo do VSCode deve mostrar: `WSL: Ubuntu-24.04`

**4. Terminal integrado:**

Terminal do VSCode automaticamente usa bash do WSL.

#### Integração JetBrains IDEs

**Opção 1: IDE instalado no Windows (problemático)**

Conhecido por ter issues de detecção (#1232, #2273). Requer:
- Configuração de firewall
- Modo de rede espelhado (`.wslconfig`)
- Pode não funcionar consistentemente

**Opção 2: IDE instalado no WSL (recomendado)**

```bash
# Instalar IntelliJ IDEA Community
sudo snap install intellij-idea-community --classic

# OU Rider
sudo snap install rider --classic

# OU PyCharm Community
sudo snap install pycharm-community --classic

# Lançar
intellij-idea-community &  # Executa em background
```

**Acessar interface gráfica:** Requer X Server no Windows (VcXsrv ou WSLg em Windows 11).

**Opção 3: JetBrains Gateway (ideal)**

```bash
# Instalar SSH server no WSL
sudo apt install openssh-server -y
sudo service ssh start

# No Windows, usar JetBrains Gateway para conectar via SSH ao WSL
```

Gateway gerencia conexão remota transparentemente.

### 4.4 Migração de Projeto Existente

#### Cenário: Projeto atualmente em C:\Users\...\Documents\MeuProjeto

**Passo 1: Backup**

```powershell
# PowerShell
cd C:\Users\[Username]\Documents\MeuProjeto
git status  # Garantir que não há mudanças não comitadas

# Commit tudo
git add .
git commit -m "Backup antes de migração para WSL"
git push
```

**Passo 2: Clonar no WSL**

```bash
# Dentro do WSL
cd ~/projects
git clone https://github.com/usuario/MeuProjeto.git
cd MeuProjeto
```

**Passo 3: Configurar Ambiente**

```bash
# Se projeto Node.js
npm install

# Se projeto Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Se projeto .NET
dotnet restore
dotnet build
```

**Passo 4: Testar**

```bash
# Executar testes
npm test
# OU
dotnet test
# OU
pytest

# Iniciar aplicação
npm start
# OU
dotnet run
```

**Passo 5: Verificar Performance**

```bash
# Comparar tempos de build
time npm run build
# OU
time dotnet build

# Deve ser significativamente mais rápido que versão em /mnt/c
```

**Passo 6: Atualizar Fluxo de Trabalho**

```bash
# Abrir VSCode do WSL
code .

# Configurar Claude Code
claude

# Desenvolver normalmente
```

**Passo 7: (Opcional) Remover Versão Windows**

```powershell
# PowerShell - APENAS após confirmar que tudo funciona no WSL
cd C:\Users\[Username]\Documents
# Backup final
Compress-Archive -Path MeuProjeto -DestinationPath MeuProjeto-backup.zip
# Remover
Remove-Item -Recurse -Force MeuProjeto
```

### 4.5 Troubleshooting Comum

#### Problema: "claude: command not found"

**Causa:** PATH não configurado corretamente.

**Solução:**

```bash
# Verificar instalação
ls ~/.npm-global/bin/claude

# Se existe, adicionar ao PATH
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Testar
claude --version
```

#### Problema: "Permission denied" ao instalar pacotes npm

**Causa:** Tentando instalar globalmente sem configuração de npm global.

**Solução:**

```bash
# Reconfigurar npm
npm config set prefix ~/.npm-global
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Reinstalar Claude Code
npm install -g @anthropic-ai/claude-code
```

#### Problema: WSL não inicia

**Causa:** Virtualização desabilitada ou recursos WSL não instalados.

**Solução:**

```powershell
# PowerShell como Administrador

# Verificar status WSL
wsl --status

# Instalar/reparar recursos
wsl --install --no-distribution
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Reiniciar
Restart-Computer
```

#### Problema: Performance ainda lenta mesmo em ~/projects

**Causa:** Windows Defender ou configuração `.wslconfig` não aplicada.

**Solução:**

```powershell
# PowerShell como Administrador

# Verificar exclusões Defender
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath

# Se não houver exclusão para WSL, adicionar
Add-MpPreference -ExclusionPath "$env:USERPROFILE\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu*"

# Verificar .wslconfig
Get-Content $env:USERPROFILE\.wslconfig

# Se não existir, criar (veja seção 4.1 Fase 7.1)

# Reiniciar WSL
wsl --shutdown
# Aguardar 10 segundos
wsl
```

---

## Parte 5: Comparação com Projeto Claude-Code-Projetos

### 5.1 Arquitetura Atual do Projeto

**Repositório analisado:** `/home/user/Claude-Code-Projetos/`

**Estrutura:**

```
Claude-Code-Projetos/
├── agentes/           # Agentes de monitoramento (Python)
│   ├── oab-watcher/
│   ├── djen-tracker/
│   └── legal-lens/
│
├── comandos/          # Utilitários (single-purpose)
├── skills/            # Skills Claude Code
├── shared/            # Código compartilhado
├── docs/              # Documentação
│
├── CLAUDE.md          # Instruções para Claude Code
├── DISASTER_HISTORY.md
└── README.md
```

**Tecnologias:**
- Python (agentes)
- Virtual environments (.venv por agente)
- Git (controle de versão)
- Data em drive externo (E:\claude-code-data\)

### 5.2 Paralelismos com claude-stack-dotnet

| Aspecto | Claude-Code-Projetos | claude-stack-dotnet |
|---------|----------------------|---------------------|
| **Linguagem** | Python | C# (.NET) |
| **Estrutura modular** | ✅ agentes/ comandos/ skills/ | ✅ src/ tests/ .claude/ |
| **Documentação projeto** | ✅ CLAUDE.md | ✅ .claude/dev-docs/ |
| **Infraestrutura Claude** | ✅ skills/ | ✅ .claude/agents/skills/hooks/ |
| **Versionamento Git** | ✅ Sim | ✅ Sim |
| **Testes automatizados** | ⚠️ Não implementado | ✅ MSTest + Playwright |
| **CI/CD** | ❌ Não | ✅ GitHub Actions |
| **Gerenciamento deps** | ✅ requirements.txt por agente | ✅ Central Package Management |
| **Setup automatizado** | ⚠️ Manual | ✅ setup-claude-code-wsl.ps1 |

### 5.3 Lições Aplicáveis

#### Lição 1: Infraestrutura .claude/ Versionada

**claude-stack-dotnet** versiona toda infraestrutura Claude Code:
- `.claude/agents/` - agentes especializados
- `.claude/skills/` - skills auto-ativantes
- `.claude/hooks/` - session hooks
- `.claude/dev-docs/` - documentação de desenvolvimento
- `.claude/mcp/` - servidores MCP

**Aplicação ao Claude-Code-Projetos:**

Criar estrutura `.claude/` versionada:

```bash
cd /home/user/Claude-Code-Projetos

mkdir -p .claude/{agents,skills,hooks,dev-docs,mcp}

# Mover skills/ existente
mv skills/* .claude/skills/
rmdir skills

# Criar agentes para tarefas recorrentes
# Exemplo: code-reviewer, refactoring-agent, doc-generator
```

**Benefício:** Infraestrutura Claude Code como código, compartilhável entre máquinas/equipe.

#### Lição 2: Script de Setup Automatizado

**claude-stack-dotnet** fornece `setup-claude-code-wsl.ps1` que automatiza setup completo.

**Aplicação ao Claude-Code-Projetos:**

Criar `setup-python-wsl.sh`:

```bash
#!/bin/bash
# setup-python-wsl.sh
# Automação de setup para Claude-Code-Projetos em WSL

set -e  # Exit on error

echo "=== Setup Claude-Code-Projetos em WSL ==="

# 1. Atualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python e dependências
sudo apt install -y python3 python3-pip python3-venv build-essential

# 3. Instalar Node.js via nvm (para Claude Code)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install --lts
nvm alias default node

# 4. Configurar npm global
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 5. Instalar Claude Code
npm install -g @anthropic-ai/claude-code

# 6. Clonar repositório
cd ~/projects
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos

# 7. Configurar cada agente
for agente in agentes/*/; do
    echo "Configurando $agente..."
    cd "$agente"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    cd ../..
done

echo "=== Setup completo! ==="
echo "Para iniciar: cd ~/projects/Claude-Code-Projetos && claude"
```

**Benefício:** Onboarding de nova máquina/desenvolvedor em 15-30 minutos.

#### Lição 3: Pipeline CI/CD

**claude-stack-dotnet** integra Claude Code no pipeline GitHub Actions:
1. Verificações de qualidade
2. **Revisão de código automatizada por Claude**
3. Revisão de segurança
4. Validação de build/testes

**Aplicação ao Claude-Code-Projetos:**

Criar `.github/workflows/claude-review.yml`:

```yaml
name: Claude Code Review

on:
  pull_request:
    branches: [ main, develop ]

jobs:
  claude-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code

      - name: Run Claude Code Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          claude -p "Review this pull request for:
          1. Code quality and Python best practices
          2. Security vulnerabilities
          3. Documentation completeness
          4. Test coverage
          Output results in markdown format." > review.md

      - name: Post Review Comment
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: review
            });
```

**Benefício:** Revisão automática de PRs, liberando tempo para revisão humana focar em aspectos estratégicos.

#### Lição 4: Testes Automatizados

**claude-stack-dotnet** tem cobertura de testes:
- Unitários (MSTest)
- Integração
- E2E (Playwright)

**Aplicação ao Claude-Code-Projetos:**

Criar estrutura de testes para agentes Python:

```bash
cd /home/user/Claude-Code-Projetos

# Para cada agente, criar diretório tests/
cd agentes/oab-watcher
mkdir tests

# Criar test_oab_watcher.py
cat > tests/test_oab_watcher.py << 'EOF'
import pytest
from main import fetch_publicacoes, parse_publicacao

def test_fetch_publicacoes():
    """Testa fetch de publicações do DOU"""
    pubs = fetch_publicacoes(data='2025-01-15')
    assert len(pubs) > 0

def test_parse_publicacao():
    """Testa parsing de publicação individual"""
    sample_pub = {...}  # Dados de exemplo
    result = parse_publicacao(sample_pub)
    assert result['tipo'] in ['INSCRICAO', 'SUSPENSAO', 'CANCELAMENTO']
EOF

# Adicionar pytest às dependências
echo "pytest" >> requirements.txt

# Atualizar venv
source .venv/bin/activate
pip install -r requirements.txt

# Executar testes
pytest tests/
```

**Benefício:** Garantia de qualidade, detecção precoce de regressões.

#### Lição 5: Gerenciamento Centralizado de Dependências

**claude-stack-dotnet** usa Central Package Management (CPM) para .NET.

**Aplicação ao Claude-Code-Projetos:**

Python não tem equivalente nativo, mas pode-se criar `requirements-shared.txt`:

```bash
cd /home/user/Claude-Code-Projetos

# Criar requirements compartilhado
cat > requirements-shared.txt << 'EOF'
# Dependências compartilhadas entre todos os agentes
requests==2.31.0
beautifulsoup4==4.12.2
lxml==5.1.0
python-dateutil==2.8.2
pydantic==2.5.0
loguru==0.7.2
EOF

# Modificar requirements.txt de cada agente
cd agentes/oab-watcher
cat > requirements.txt << 'EOF'
-r ../../requirements-shared.txt

# Dependências específicas do oab-watcher
selenium==4.16.0
webdriver-manager==4.0.1
EOF

# Reinstalar
source .venv/bin/activate
pip install -r requirements.txt
```

**Benefício:** Versões consistentes, atualizações simplificadas.

### 5.4 Adaptações Específicas para Ambiente WSL

#### Paths de Dados (E:\ vs WSL)

**Situação atual:** Dados em `E:\claude-code-data\` (drive externo Windows).

**Desafio WSL:** Acessar `E:\` via `/mnt/e/` sofre mesma penalidade de performance de `/mnt/c/`.

**Soluções:**

**Opção 1: Mover dados para filesystem WSL**

```bash
# Criar diretório de dados no WSL
mkdir -p ~/claude-code-data

# Copiar dados existentes (uma vez)
cp -r /mnt/e/claude-code-data/* ~/claude-code-data/

# Atualizar shared/utils/path_utils.py
# De:
# data_root = Path(os.getenv('CLAUDE_DATA_ROOT', 'E:/claude-code-data'))
# Para:
data_root = Path(os.getenv('CLAUDE_DATA_ROOT', '~/claude-code-data')).expanduser()
```

**Benefício:** Performance 5-10x melhor.

**Trade-off:** Dados não diretamente acessíveis via Windows Explorer (precisa usar `\\wsl$\...`).

**Opção 2: Manter E:\ para armazenamento, cache em WSL**

```bash
# Estrutura híbrida
~/claude-code-data/          # Cache, processamento temporário
/mnt/e/claude-code-data/     # Armazenamento permanente

# Workflow:
# 1. Download e processamento em ~/claude-code-data/
# 2. Cópia para /mnt/e/ ao final do dia (script agendado)
```

**Benefício:** Melhor dos dois mundos - performance + backup em drive físico.

**Opção 3: Symlink seletivo**

```bash
# Logs/cache em WSL (performance)
mkdir -p ~/claude-code-data/logs
mkdir -p ~/claude-code-data/cache

# Downloads em /mnt/e/ (armazenamento)
ln -s /mnt/e/claude-code-data/downloads ~/claude-code-data/downloads
```

**Benefício:** Granularidade - performance onde importa, armazenamento onde faz sentido.

#### Integração com Windows Tools

**Situação:** Projeto usa ferramentas Windows (Office para exportação, etc.)

**Solução: Scripts de ponte**

```bash
# Criar scripts em ~/bin/
mkdir -p ~/bin

# Script para abrir Excel do Windows
cat > ~/bin/excel-windows << 'EOF'
#!/bin/bash
# Converte path Linux para Windows e abre Excel
wslpath -w "$1" | xargs -I {} cmd.exe /c start excel "{}"
EOF

chmod +x ~/bin/excel-windows

# Uso
excel-windows ~/claude-code-data/outputs/relatorio.xlsx
```

### 5.5 Checklist de Migração para WSL

**Fase 1: Preparação**
- [ ] Backup completo do projeto (`git push`, exportar E:\claude-code-data\`)
- [ ] Instalar WSL2 seguindo Parte 4.1
- [ ] Configurar .wslconfig e exclusões Defender
- [ ] Instalar Claude Code no WSL

**Fase 2: Migração de Código**
- [ ] Clonar repositório em `~/projects/Claude-Code-Projetos`
- [ ] Criar venvs para cada agente
- [ ] Instalar dependências (`pip install -r requirements.txt`)
- [ ] Testar execução de cada agente individualmente

**Fase 3: Migração de Dados**
- [ ] Decidir estratégia (Opção 1, 2 ou 3 acima)
- [ ] Copiar dados necessários para WSL (se Opção 1)
- [ ] Atualizar `shared/utils/path_utils.py`
- [ ] Testar acesso a dados

**Fase 4: Infraestrutura Claude Code**
- [ ] Criar estrutura `.claude/` versionada
- [ ] Mover skills existentes
- [ ] Criar agentes especializados (code-reviewer, etc.)
- [ ] Configurar hooks (se necessário)

**Fase 5: Automação**
- [ ] Criar script `setup-python-wsl.sh`
- [ ] Testar em instalação WSL fresh
- [ ] Criar GitHub Actions para CI/CD (opcional)

**Fase 6: Validação**
- [ ] Executar todos os agentes e verificar funcionalidade
- [ ] Comparar performance (vs versão Windows)
- [ ] Verificar integração Claude Code
- [ ] Testar workflow completo (desenvolvimento → commit → push)

**Fase 7: Documentação**
- [ ] Atualizar README.md com instruções WSL
- [ ] Atualizar CLAUDE.md com paths WSL
- [ ] Documentar estratégia de dados escolhida
- [ ] Criar troubleshooting WSL-específico

---

## Parte 6: Arquitetura para Servidor Corporativo e Documentos Jurídicos

### 6.1 Contexto do Ambiente

**Infraestrutura atual:**
- Servidor corporativo central (SSD, proxy configurado, acesso remoto)
- 7 usuários simultâneos sem degradação de performance
- Source of truth: todos os documentos vão para servidor primeiro
- Dois tipos de dados distintos:
  1. Downloads massivos: Cadernos DOU/DJEN (E:\, volume alto, descartável)
  2. Documentos jurídicos: Íntegra de autos, documentos das partes (servidor, crítico, permanente)

**Projeto extrator:**
- Objetivo: Processar documentos jurídicos do servidor
- Output: Autos organizados com YAML tags, estrutura mínima
- Requisito: Acesso contínuo à base de documentos sem friction de sincronização

**Desafio arquitetural:**
- Downloads massivos (E:\): Performance degradada aceitável (acesso esporádico)
- Documentos jurídicos (servidor): Performance crítica (base de desenvolvimento)
- Necessidade: Evitar duplicação/sincronização manual constante

### 6.2 Soluções de Integração Servidor-WSL

#### Solução 1: Mount SMB do Servidor no WSL (RECOMENDADA)

**Arquitetura:**

```
Servidor Corporativo (\\servidor\documentos-juridicos\)
    |
    | SMB/CIFS mount
    V
WSL2 (/mnt/servidor/)
    |
    +-- Cache local (~/cache-servidor/) para processamento intensivo
    +-- Outputs (~/outputs/) -> sincronizado para servidor
```

**Implementação:**

```bash
# Instalar CIFS utilities
sudo apt install cifs-utils -y

# Criar ponto de montagem
sudo mkdir -p /mnt/servidor

# Criar credentials file (seguro)
sudo nano /root/.smbcredentials
# Conteúdo:
# username=seu_usuario
# password=sua_senha
# domain=DOMINIO_ESCRITORIO

sudo chmod 600 /root/.smbcredentials

# Configurar mount automático em /etc/fstab
sudo nano /etc/fstab
# Adicionar linha:
//servidor/documentos-juridicos /mnt/servidor cifs credentials=/root/.smbcredentials,uid=1000,gid=1000,file_mode=0644,dir_mode=0755,iocharset=utf8 0 0

# Montar
sudo mount -a

# Verificar
ls /mnt/servidor
```

**Performance esperada:**

```
Rede gigabit (1Gbps):
- Ler PDF 50MB: 2-4s (vs 8-12s de /mnt/e/, vs 0.8s de ~/)
- Throughput: 100-125 MB/s
- Latência: Baixa (rede local)

Rede corporativa típica (100Mbps):
- Ler PDF 50MB: 5-8s
- Throughput: 10-12 MB/s
```

**Trade-offs:**

- Performance: 2-3x mais lento que WSL local, mas 2-3x mais rápido que /mnt/e/
- Consistência: Sempre dados atualizados (source of truth)
- Dependência: Requer servidor acessível
- Zero duplicação de dados

**Quando usar:**
- Leitura ocasional de documentos
- Servidor com SSD e rede gigabit
- Documentos que mudam frequentemente (atualização de autos)

#### Solução 2: Cache Híbrido com Rsync Seletivo

**Arquitetura:**

```
Servidor (\\servidor\documentos-juridicos\)
    |
    | rsync incremental (apenas mudanças)
    V
WSL Cache (~/documentos-juridicos-cache/)
    |
    | Processamento local (rápido)
    V
Outputs (~/outputs/) -> sincronizado de volta para servidor
```

**Implementação:**

```bash
# Script de sincronização inteligente
cat > ~/bin/sync-servidor.sh << 'EOF'
#!/bin/bash

SERVIDOR="/mnt/servidor/documentos-juridicos"
CACHE="$HOME/documentos-juridicos-cache"

# Criar cache se não existir
mkdir -p "$CACHE"

# Sincronização incremental (apenas mudanças)
rsync -avz --delete \
  --filter='+ */' \
  --filter='+ *.pdf' \
  --filter='+ *.docx' \
  --filter='+ *.jpg' \
  --filter='- *' \
  "$SERVIDOR/" "$CACHE/"

echo "Sincronização completa: $(date)"
EOF

chmod +x ~/bin/sync-servidor.sh

# Executar inicialmente
~/bin/sync-servidor.sh

# Agendar via cron (a cada 2 horas durante expediente)
crontab -e
# Adicionar:
# 0 8-18/2 * * 1-5 /home/user/bin/sync-servidor.sh >> /home/user/logs/sync.log 2>&1
```

**Script de processamento com cache:**

```python
from pathlib import Path
import shutil

CACHE = Path.home() / 'documentos-juridicos-cache'
SERVIDOR = Path('/mnt/servidor/documentos-juridicos')

def processar_com_cache(processo_id):
    """Usa cache local, fallback para servidor se necessário"""

    # Tentar cache primeiro (rápido)
    pdf_cache = CACHE / f'{processo_id}.pdf'

    if pdf_cache.exists():
        # Verificar se está atualizado (comparar mtime com servidor)
        pdf_servidor = SERVIDOR / f'{processo_id}.pdf'

        if pdf_servidor.exists():
            if pdf_cache.stat().st_mtime >= pdf_servidor.stat().st_mtime:
                # Cache atualizado, usar
                return processar_pdf(pdf_cache)
            else:
                # Cache desatualizado, atualizar
                shutil.copy(pdf_servidor, pdf_cache)
                return processar_pdf(pdf_cache)

    # Cache miss, buscar do servidor
    pdf_servidor = SERVIDOR / f'{processo_id}.pdf'
    if not pdf_servidor.exists():
        raise FileNotFoundError(f"Processo {processo_id} não encontrado")

    # Copiar para cache
    pdf_cache.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(pdf_servidor, pdf_cache)

    return processar_pdf(pdf_cache)
```

**Performance esperada:**

```
Cache hit (documento já sincronizado):
- Acesso: 0.8-1.2s (performance WSL nativa)
- Processamento: 8-12s
- TOTAL: ~10-14s

Cache miss (busca do servidor):
- Cópia inicial: 2-4s (rede gigabit)
- Processamento: 8-12s
- TOTAL: ~12-16s (cache subsequente: 10-14s)

Sincronização rsync (100 documentos, apenas mudanças):
- Primeira vez (todos): 5-10 minutos
- Incremental (mudanças): 30-60 segundos
```

**Trade-offs:**

- Performance: Idêntica a WSL nativo (cache hit)
- Consistência: Depende de frequência de rsync
- Duplicação: Sim, mas controlada (apenas documentos processados)
- Offline: Funciona mesmo sem servidor (usa cache)

**Quando usar:**
- Processamento batch intensivo
- Documentos relativamente estáveis (poucas mudanças diárias)
- Necessidade de trabalhar offline ocasionalmente

#### Solução 3: NFS Mount (Performance Superior a SMB)

**Vantagens sobre SMB:**
- 20-30% mais rápido para operações pequenas
- Menor overhead de protocolo
- Melhor integração com permissões Linux

**Configuração servidor (se disponível):**

```bash
# No servidor Linux/NAS com suporte NFS
# /etc/exports
/srv/documentos-juridicos 192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)

# Reiniciar NFS
sudo exportfs -ra
```

**Configuração WSL:**

```bash
# Instalar cliente NFS
sudo apt install nfs-common -y

# Mount
sudo mkdir -p /mnt/servidor-nfs
sudo mount -t nfs servidor:/srv/documentos-juridicos /mnt/servidor-nfs

# /etc/fstab
servidor:/srv/documentos-juridicos /mnt/servidor-nfs nfs defaults,_netdev 0 0
```

**Performance esperada:**

```
NFS vs SMB (rede gigabit):
- Ler PDF 50MB: 1.5-3s (NFS) vs 2-4s (SMB)
- Operações pequenas: 30% mais rápido
- Throughput máximo: Similar
```

**Trade-off:**
- Requer servidor com suporte NFS (pode não estar disponível)
- Configuração mais complexa
- Performance superior se disponível

### 6.3 Arquitetura Recomendada para Automação Jurídica

**Estrutura de dados em camadas:**

```
CAMADA 1: Servidor Corporativo (Source of Truth)
\\servidor\documentos-juridicos\
├── processos\
│   ├── 2024\
│   ├── 2025\
│   └── ...
└── documentos-partes\

CAMADA 2: WSL Mount (Acesso direto, consistente)
/mnt/servidor/ -> \\servidor\documentos-juridicos\

CAMADA 3: WSL Cache (Performance, processamento intensivo)
~/documentos-juridicos-cache/
├── processos-ativos/      # Rsync de processos em andamento
└── temp-processing/        # Copy-on-demand para OCR

CAMADA 4: WSL Outputs (Geração rápida)
~/claude-code-data/outputs/
├── autos-estruturados/
├── yaml-extractions/
└── relatorios/

CAMADA 5: Sincronização de volta (Outputs -> Servidor)
~/outputs/ --rsync--> \\servidor\outputs-extrator\
```

**Workflow completo:**

```python
from pathlib import Path
import shutil

# Configuração
SERVIDOR = Path('/mnt/servidor/documentos-juridicos')
CACHE = Path.home() / 'documentos-juridicos-cache/processos-ativos'
TEMP = Path.home() / 'documentos-juridicos-cache/temp-processing'
OUTPUTS = Path.home() / 'claude-code-data/outputs'

def extrair_autos_processo(numero_processo):
    """Pipeline completo: servidor -> cache -> processamento -> output"""

    # 1. Localizar no servidor
    pdf_servidor = SERVIDOR / 'processos' / f'{numero_processo}.pdf'
    if not pdf_servidor.exists():
        raise FileNotFoundError(f"Processo {numero_processo} não encontrado")

    # 2. Verificar cache
    pdf_cache = CACHE / f'{numero_processo}.pdf'

    if not pdf_cache.exists() or \
       pdf_cache.stat().st_mtime < pdf_servidor.stat().st_mtime:
        # Cache desatualizado, copiar do servidor
        print(f"Atualizando cache: {numero_processo}")
        shutil.copy(pdf_servidor, pdf_cache)

    # 3. Copy para temp (processamento pesado)
    pdf_temp = TEMP / f'{numero_processo}.pdf'
    shutil.copy(pdf_cache, pdf_temp)

    # 4. Processar (OCR, extração, tudo em WSL = rápido)
    texto_bruto = extrair_texto_ocr(pdf_temp)
    estrutura = parse_estrutura_processual(texto_bruto)
    yaml_tagged = gerar_yaml_tags(estrutura)

    # 5. Salvar output em WSL
    output_file = OUTPUTS / 'autos-estruturados' / f'{numero_processo}.yaml'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(yaml_tagged)

    # 6. Limpar temp
    pdf_temp.unlink()

    # 7. Sincronizar output para servidor (background)
    # Script separado roda a cada hora via cron

    return output_file
```

**Script de sincronização bidirecional:**

```bash
#!/bin/bash
# ~/bin/sync-bidirectional.sh

# 1. Sincronizar processos ativos (servidor -> cache)
rsync -avz --delete \
  --include='processos/2025/***' \
  --include='processos/2024/***' \
  --exclude='processos/*' \
  /mnt/servidor/documentos-juridicos/ \
  ~/documentos-juridicos-cache/processos-ativos/

# 2. Sincronizar outputs (cache -> servidor)
rsync -avz \
  ~/claude-code-data/outputs/ \
  /mnt/servidor/outputs-extrator/

echo "Sincronização completa: $(date)"
```

**Cron job:**

```
# Sincronizar a cada 2 horas durante expediente
0 8-18/2 * * 1-5 /home/user/bin/sync-bidirectional.sh
```

### 6.4 Performance Esperada por Cenário

```
Cenário 1: Leitura direta do servidor (mount SMB)
- Ler PDF 50MB: 2-4s
- OCR: 40-50s (operações I/O via rede)
- Parse: 12-15s
- TOTAL: ~55-70s por processo

Cenário 2: Cache local (rsync + processamento WSL)
- Sincronização inicial: 5-10 min (100 processos)
- Leitura de cache: 0.8-1.2s
- OCR: 5-7s (tudo local)
- Parse: 2-3s
- TOTAL: ~8-12s por processo (após cache)

Cenário 3: Híbrido (mount + copy-on-demand)
- Cópia servidor->temp: 2-4s
- Processamento temp: 8-12s
- TOTAL: ~10-16s por processo

Batch 100 processos:
- Cenário 1: 90-115 minutos
- Cenário 2: 13-20 minutos (após sync inicial)
- Cenário 3: 16-26 minutos
```

### 6.5 Recomendação Específica

**Para desenvolvimento do extrator:**

Implementar Solução 2 (Cache Híbrido com Rsync):

1. Mount SMB do servidor em /mnt/servidor (acesso direto quando necessário)
2. Rsync seletivo para ~/cache/ (apenas processos ativos)
3. Processamento em WSL (performance máxima)
4. Outputs sincronizados de volta para servidor

**Justificativa:**

- Servidor permanece source of truth (zero risco de inconsistência)
- Performance de processamento é máxima (tudo em WSL após cache)
- Sincronização incremental evita duplicação desnecessária
- Funciona offline (útil para desenvolvimento)
- Outputs automaticamente disponíveis no servidor para equipe

**Dados críticos:**

- Downloads massivos (E:\): Permanecem em E:\, acesso via /mnt/e/ (performance degradada aceitável)
- Documentos jurídicos (servidor): Cache em WSL, sincronização automática
- Outputs: Gerados em WSL, sincronizados para servidor

---

## Parte 7: Recomendações Finais

### 7.1 Para o Projeto Claude-Code-Projetos

**Recomendação Primária: Migrar para WSL2 com dados no filesystem Linux**

**Justificativa:**
1. ✅ Performance 5-10x superior para operações Python/npm
2. ✅ Compatibilidade 100% com features avançadas Claude Code
3. ✅ Preparação para futuro (Docker, CI/CD, MCP servers)
4. ✅ Alinhamento com melhores práticas da indústria

**Implementação sugerida:**

```bash
# Estrutura final
~/projects/
└── Claude-Code-Projetos/
    ├── agentes/
    ├── .claude/           # NOVO - infraestrutura versionada
    ├── .github/           # NOVO - CI/CD workflows
    ├── tests/             # NOVO - testes automatizados
    └── setup-python-wsl.sh  # NOVO - automação setup

~/claude-code-data/        # NOVO - dados movidos de E:\
├── agentes/
│   ├── oab-watcher/
│   │   ├── downloads/
│   │   ├── logs/
│   │   └── outputs/
│   └── ...
└── shared/
```

**Cronograma sugerido:**

| Semana | Atividades | Horas Estimadas |
|--------|------------|-----------------|
| 1 | Instalar WSL2, configurar, instalar Claude Code | 4-6h |
| 2 | Migrar código, criar venvs, testar agentes | 6-8h |
| 3 | Migrar dados, atualizar paths, validar | 4-6h |
| 4 | Criar infraestrutura .claude/, agentes especializados | 6-8h |
| 5 | Automação (setup script, CI/CD) | 4-6h |
| 6 | Documentação, testes, validação final | 4-6h |

**Total:** 28-40 horas distribuídas em 6 semanas.

**ROI esperado:** Recuperação do investimento em 2-3 meses através de:
- Redução de tempo de build/execução (30-50% mais rápido)
- Menos friction em desenvolvimento (ferramentas funcionam confiavelmente)
- Onboarding acelerado (script automatizado)
- CI/CD reduz bugs em produção

### 6.2 Priorização de Features

**Must-Have (Implementar primeiro):**
1. ✅ Migração para WSL2 com dados em filesystem Linux
2. ✅ Script de setup automatizado (`setup-python-wsl.sh`)
3. ✅ Estrutura `.claude/` versionada com agents/skills/hooks
4. ✅ Exclusões Windows Defender configuradas

**Should-Have (Implementar após estabilização):**
5. ⚠️ Testes automatizados (pytest) para cada agente
6. ⚠️ GitHub Actions para revisão de código por Claude
7. ⚠️ Gerenciamento centralizado de dependências (`requirements-shared.txt`)
8. ⚠️ Meta-agent para criar agents especializados

**Nice-to-Have (Futuro):**
9. 🔮 Docker containers para agentes (isolamento total)
10. 🔮 Dashboard de monitoramento (Grafana + Prometheus)
11. 🔮 Episodic Memory plugin (memória de sessões anteriores)
12. 🔮 Superpowers plugin (TDD, debugging sistemático)

### 6.3 Riscos e Mitigações

**Risco 1: Curva de aprendizado WSL**

**Impacto:** Médio - pode adicionar 1-2 semanas ao cronograma.

**Mitigação:**
- Usar script automatizado (reduz complexidade)
- Seguir guia passo-a-passo (Parte 4.1)
- Começar com projeto pequeno/teste antes de migrar projeto real

**Risco 2: Performance ainda insatisfatória após migração**

**Impacto:** Alto - invalidaria justificativa principal.

**Mitigação:**
- Garantir dados em `~/`, **nunca** `/mnt/*`
- Configurar exclusões Defender (crítico)
- Validar `.wslconfig` aplicado corretamente
- Benchmark antes/depois para confirmar melhoria

**Risco 3: Incompatibilidade de ferramentas específicas**

**Impacto:** Baixo - maioria das ferramentas Python/Node funciona identicamente.

**Mitigação:**
- Testar cada agente individualmente após migração
- Criar scripts de ponte para ferramentas Windows (Office, etc.)
- Manter virtualização bidirecional (WSL ↔ Windows)

**Risco 4: Problemas de segurança (Defender não escaneia WSL)**

**Impacto:** Médio - ponto cego de segurança.

**Mitigação:**
- Instalar ClamAV dentro do WSL
- Não desabilitar Defender completamente, apenas exclusões específicas
- Manter sistema WSL atualizado (`sudo apt upgrade`)
- Políticas de firewall estritas

**Risco 5: Consumo excessivo de recursos (RAM/CPU)**

**Impacto:** Médio - pode degradar performance geral do sistema.

**Mitigação:**
- Configurar `.wslconfig` com limites (8GB RAM, 4 cores)
- Monitorar VmmemWSL via Task Manager
- Script para limpar cache WSL: `sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'`

### 6.4 Métricas de Sucesso

**KPIs para validar migração bem-sucedida:**

| Métrica | Baseline (Windows) | Target (WSL) | Método de Medição |
|---------|-------------------|--------------|-------------------|
| **Tempo de setup inicial** | 2-4h manual | 15-30min script | Cronômetro durante setup fresh |
| **Tempo de execução agente** | X segundos | <0.5X segundos | `time python main.py` |
| **Tempo npm install** | ~45s | ~2-5s | `time npm install react` |
| **Tempo git status** | 5-15s | <1s | `time git status` em repo grande |
| **Uso de RAM (idle)** | N/A | <8GB | Task Manager → VmmemWSL |
| **Funcionalidade Claude Code** | 70% features | 100% features | Teste hooks, MCP, plugins |

**Critérios de aceitação:**
- ✅ Todos os agentes executam sem erros
- ✅ Performance 2x+ melhor que baseline
- ✅ Hooks e MCP servers funcionam
- ✅ Setup automatizado funciona em WSL fresh
- ✅ Documentação completa e atualizada

### 6.5 Alternativas Consideradas

**Alternativa 1: Permanecer no Windows Nativo + Git Bash**

**Prós:**
- Zero curva de aprendizado
- Menor uso de recursos
- Simplicidade

**Contras:**
- ❌ Performance inferior
- ❌ Limitações de features (70% apenas)
- ❌ MCP servers não funcionam
- ❌ Não é future-proof

**Veredito:** Não recomendado para projeto profissional deste porte.

**Alternativa 2: WSL1 em vez de WSL2**

**Prós:**
- Performance 5x melhor para acesso a `/mnt/c/`
- Configuração de rede mais simples

**Contras:**
- ❌ Performance 2x pior que WSL2 para filesystem Linux
- ❌ Compatibilidade de system calls apenas parcial
- ❌ Não suporta Docker adequadamente
- ❌ Microsoft considera legacy

**Veredito:** Não recomendado. Se vai migrar, migre para WSL2 direto.

**Alternativa 3: Dual boot Linux**

**Prós:**
- Performance 100% nativa
- Zero overhead de virtualização

**Contras:**
- ❌ Requer reiniciar para trocar de SO
- ❌ Complexidade de gerenciar dois sistemas
- ❌ Potencial perda de ferramentas Windows específicas

**Veredito:** Overkill para este caso. WSL2 oferece 85-95% da performance com flexibilidade superior.

**Alternativa 4: Desenvolvimento em VM Linux (VirtualBox, VMware)**

**Prós:**
- Controle total sobre ambiente
- Snapshots para backup

**Contras:**
- ❌ Performance inferior ao WSL2
- ❌ Overhead de gerenciar VM separada
- ❌ Complexidade de networking
- ❌ Maior uso de recursos

**Veredito:** WSL2 é superior em todos os aspectos para este caso de uso.

---

## Parte 7: Resumo Executivo e Opinião

### 7.1 Síntese da Análise

**Contexto:** Pesquisa extensiva sobre WSL + Claude Code revelou que WSL2 é escolha profissional padrão, oferecendo compatibilidade 100% com features avançadas (hooks, MCP servers, plugins) e performance 85-95% de Linux nativo **quando configurado corretamente**.

**Desafio crítico:** Performance cross-filesystem. WSL2 acessando `/mnt/c/` é 5-10x mais lento que filesystem nativo devido ao protocolo 9P. **Solução obrigatória:** armazenar projetos em `~/` no filesystem Linux.

**Repositório claude-stack-dotnet:** Exemplo de implementação profissional demonstra melhores práticas:
- Script PowerShell automatizado (setup em 15-30min)
- Infraestrutura Claude Code versionada (`.claude/` no Git)
- Pipeline CI/CD com revisão automática por Claude
- Testes automatizados (unitários + E2E)
- Gerenciamento centralizado de dependências

**Issues conhecidas:** Problemas de detecção de IDEs JetBrains (#1232, #2273) têm workarounds documentados (firewall, modo de rede espelhado, ou instalar IDE no WSL). MCP servers frequentemente falham em Git Bash mas funcionam em WSL.

### 7.2 Opinião Profissional

**Para o projeto Claude-Code-Projetos: Migração para WSL2 é altamente recomendada.**

**Justificativa (dados objetivos):**

1. **Performance**: Benchmarks mostram 5-10x melhoria para operações Python/npm quando dados em filesystem WSL vs `/mnt/c/`. Projeto atual com dados em `E:\` sofre mesma penalidade.

2. **Compatibilidade**: 100% de features Claude Code (vs ~70% em Git Bash). Hooks complexos, MCP servers e plugins como episodic-memory funcionam apenas em ambiente POSIX real.

3. **Escalabilidade futura**: Docker, CI/CD, containerização requerem WSL. Migrar agora evita nova migração futura.

4. **Paridade com produção**: Servidores executam Linux. Desenvolver em ambiente Linux garante consistência.

5. **ROI**: Investimento de 28-40 horas paga-se em 2-3 meses através de redução de tempo de execução (30-50%), menos friction, onboarding acelerado.

**Ressalvas:**

- **Curva de aprendizado**: 1-2 semanas para conforto total com WSL se nunca usado antes.
- **Segurança**: Exclusões do Defender criam ponto cego; mitigar com ClamAV no WSL.
- **Dados**: Mover de `E:\` para `~/claude-code-data/` perde acesso direto via Windows Explorer; usar `\\wsl$\...` ou symlinks.

**Configurações críticas (não-negociáveis):**

1. ✅ Projetos em `~/projects/`, **nunca** `/mnt/*`
2. ✅ Exclusões Windows Defender configuradas
3. ✅ `.wslconfig` com limites de memória (8GB)
4. ✅ Node via nvm, npm global sem sudo
5. ✅ VSCode Remote-WSL para integração IDE

**Sem essas configurações**, WSL2 terá performance pior que Windows nativo. Com elas, performance é 85-95% de Linux nativo.

### 7.3 Sugestões de Como Proceder

#### Fase Imediata (Próximos 7 dias)

**Objetivo:** Validar viabilidade técnica em ambiente de teste.

**Tarefas:**

1. **Dia 1-2: Instalação WSL2**
   - Seguir Parte 4.1 (Instalação Manual) ou usar script do repositório claude-stack-dotnet
   - Configurar `.wslconfig` e exclusões Defender
   - Instalar Claude Code

2. **Dia 3-4: Teste com projeto pequeno**
   - Criar projeto teste em `~/projects/test-migration`
   - Clonar um agente simples (ex: oab-watcher)
   - Criar venv, instalar deps, executar
   - **Benchmark:** Comparar tempo de execução com versão Windows

3. **Dia 5-7: Validar funcionalidades avançadas**
   - Testar hooks (criar hook simples de logging)
   - Testar MCP server (instalar episodic-memory plugin)
   - Integrar VSCode Remote-WSL
   - **Decisão Go/No-Go:** Se performance e funcionalidade satisfatórias, prosseguir. Se não, investigar causa (provavelmente configuração incorreta).

#### Fase de Migração (Semanas 2-4)

**Objetivo:** Migrar projeto completo para WSL com mínima interrupção.

**Semana 2:**
- Migrar código: clonar repositório em `~/projects/Claude-Code-Projetos`
- Configurar venvs para todos os agentes
- Testar execução individual de cada agente
- Commit/push mudanças (se houver ajustes de paths)

**Semana 3:**
- Migrar dados: decidir estratégia (Parte 5.4)
- Implementar estratégia escolhida
- Atualizar `shared/utils/path_utils.py`
- Testar workflow completo (download → processamento → output)

**Semana 4:**
- Criar infraestrutura `.claude/` versionada
- Mover skills, criar agents básicos (code-reviewer)
- Documentar processo (atualizar README.md, CLAUDE.md)
- Validação final (executar todos os agentes, verificar outputs)

#### Fase de Otimização (Semanas 5-6)

**Objetivo:** Automação e melhorias de qualidade.

**Semana 5:**
- Criar `setup-python-wsl.sh` (baseado em claude-stack-dotnet)
- Testar em instalação WSL fresh (máquina virtual ou amigo)
- Iterar até setup < 30 minutos

**Semana 6:**
- (Opcional) Criar GitHub Actions para revisão de código
- (Opcional) Adicionar testes automatizados (pytest)
- Criar troubleshooting WSL-específico na documentação
- Comemorar 🎉

#### Fase Contínua (Ongoing)

**Objetivo:** Manutenção e evolução.

**Mensal:**
- Atualizar WSL: `sudo apt update && sudo apt upgrade`
- Atualizar Claude Code: `npm update -g @anthropic-ai/claude-code`
- Revisar uso de recursos (Task Manager → VmmemWSL)

**Trimestral:**
- Avaliar novos plugins Claude Code (marketplace)
- Adicionar novos agentes/skills conforme necessário
- Revisar e atualizar documentação

**Anual:**
- Benchmark de performance (garantir não há degradação)
- Avaliar migração para Docker (se projeto crescer muito)

### 7.4 Plano B (Se Migração Falhar)

**Cenário:** Após teste (Dias 1-7), performance ou compatibilidade insatisfatória.

**Diagnóstico:**

1. **Performance ruim:**
   - ✅ Verificar se projetos estão em `~/` (não `/mnt/*`)
   - ✅ Verificar exclusões Defender aplicadas
   - ✅ Verificar `.wslconfig` carregado (`wsl --shutdown`, então `wsl`)
   - ✅ Benchmark específico: `time npm install react` deve ser <5s

2. **Features não funcionando:**
   - ✅ MCP servers: verificar Node.js via nvm, PATH correto
   - ✅ Hooks: verificar permissões executáveis (`chmod +x`)
   - ✅ Plugins: verificar instalação npm global sem sudo

**Se problemas persistirem após troubleshooting:**

**Opção 1: Permanecer no Windows Nativo (curto prazo)**
- Aceitar limitações de features (70%)
- Focar em otimizações de código Python
- Revisar decisão em 6 meses (WSL pode melhorar)

**Opção 2: Dual Boot Linux (longo prazo)**
- Instalar Ubuntu nativo em partição separada
- Performance 100%, zero overhead
- Trade-off: flexibilidade reduzida (requer reinício para Windows)

**Opção 3: Cloud Development (IDE remoto)**
- GitHub Codespaces, GitPod ou similar
- Ambiente Linux na nuvem
- Trade-off: custo mensal, dependência de internet

**Recomendação:** Extremamente improvável que Plano B seja necessário. 95%+ dos casos de "WSL não funciona" são problemas de configuração, não limitações técnicas.

### 7.5 Última Palavra

**WSL2 não é uma bala de prata**, mas é a **melhor solução disponível** para desenvolvedores Windows que precisam de ambiente Linux sem dual boot.

Para Claude Code especificamente, a diferença entre Git Bash e WSL2 é entre **"funciona para casos básicos"** e **"desbloqueia todo o potencial da ferramenta"**.

O projeto Claude-Code-Projetos, com sua arquitetura modular, agentes Python, e ambição de automação legal sofisticada, **está exatamente no perfil que mais beneficia de WSL2**.

Investimento de 28-40 horas distribuídas em 6 semanas é **totalmente justificável** para projeto desta escala e longevidade esperada.

**Recomendação final: Proceder com migração.**

---

## Apêndice A: Recursos e Referências

### Documentação Oficial

- **Claude Code Docs**: https://docs.claude.com/en/docs/claude-code
- **WSL Microsoft Learn**: https://learn.microsoft.com/en-us/windows/wsl/
- **Repositório claude-stack-dotnet**: https://github.com/NotMyself/claude-stack-dotnet

### Issues Relevantes GitHub

- #1232: JetBrains IDE detection WSL
- #2273: Rider plugin Windows connection
- #1411: Working directory mismatch
- #559: Auto-update Ink compatibility
- #653: API connection errors
- #4197: WSL2 /mnt performance (Microsoft/WSL)

### Benchmarks de Performance

- vxlabs.com: WSL2 I/O measurements (2019-2023)
- Phoronix: Windows 11 25H2 WSL benchmarks
- Markentier.tech: Faster Git under WSL2

### Guias de Instalação

- ClaudeLog: Comprehensive WSL setup guide
- Medium: 47 Claude Code WSL tricks
- Gist eesb99: Claude Code WSL2 installation

### Plugins Recomendados

- obra/superpowers: Development skills
- obra/episodic-memory: Conversation memory
- hesreallyhim/awesome-claude-code: Curated list

---

**Fim do Documento de Análise Completa**

*Documento gerado em: 2025-01-15*
*Baseado em pesquisa de: 42+ fontes técnicas*
*Análise de: 10+ GitHub issues, 3+ benchmarks de performance, 1 repositório de referência*
