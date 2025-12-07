# Guia de Instalacao WSL2 - Portatil

Este guia permite instalar WSL2 em **qualquer PC Windows** para trabalhar com o projeto Claude-Code-Projetos.

---

## Pre-requisitos

| Requisito | Minimo | Como verificar |
|-----------|--------|----------------|
| Windows | 10 build 19041+ ou 11 | `winver` |
| PowerShell | 5.1+ (ja vem no Windows) | `$PSVersionTable` |
| Admin | Necessario para habilitar WSL | - |
| Virtualizacao | Habilitada no BIOS | - |

---

## Instalacao Rapida (4 comandos)

Abra **PowerShell como Administrador** e execute:

```powershell
# 1. Baixar o script (ou copie do pendrive/repositorio)
# Se ja tem o arquivo, pule para o passo 2

# 2. Verificar pre-requisitos
.\install-wsl2-portable.ps1 -Phase Check

# 3. Habilitar recursos WSL (REQUER RESTART)
.\install-wsl2-portable.ps1 -Phase Enable

# === REINICIE O COMPUTADOR ===

# 4. Apos reiniciar, instalar Ubuntu
.\install-wsl2-portable.ps1 -Phase Install

# 5. Validar instalacao
.\install-wsl2-portable.ps1 -Phase Validate
```

---

## Instalacao Passo a Passo

### Fase 1: Verificar Pre-requisitos

```powershell
.\install-wsl2-portable.ps1 -Phase Check
```

Este comando verifica:
- Privilegios de administrador
- Versao do Windows
- Suporte a virtualizacao
- Estado atual do WSL

**Erros comuns:**
- "NAO esta executando como Administrador" → Clique direito no PowerShell → "Executar como administrador"
- "Windows Build INCOMPATIVEL" → Atualize o Windows

### Fase 2: Habilitar Recursos WSL

```powershell
.\install-wsl2-portable.ps1 -Phase Enable
```

Este comando:
1. Habilita o subsistema Linux do Windows
2. Habilita a plataforma de maquina virtual
3. Define WSL2 como padrao

**IMPORTANTE:** Sera necessario reiniciar o computador apos esta fase!

### Fase 3: Instalar Ubuntu

Apos reiniciar, abra PowerShell como Admin novamente:

```powershell
.\install-wsl2-portable.ps1 -Phase Install
```

Quando a janela do Ubuntu abrir:
1. Crie um **nome de usuario** (ex: `pedro`, `joao`)
2. Crie uma **senha** (pode ser simples, mas memorize!)
3. Confirme a senha
4. Apos "Installation successful", digite `exit`

### Fase 4: Validar Instalacao

```powershell
.\install-wsl2-portable.ps1 -Phase Validate
```

Verifica se tudo esta funcionando corretamente.

---

## Apos WSL2 Instalado

### Configurar Ambiente de Desenvolvimento

```powershell
.\setup-dev-environment.ps1
```

Este script instala:
- Node.js 22 via nvm
- Python 3 (verifica/atualiza)
- Claude Code CLI
- Configura Git

### Clonar o Repositorio

```bash
# Dentro do Ubuntu (wsl)
mkdir -p ~/projetos
cd ~/projetos
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos
```

### Iniciar Claude Code

```bash
claude
```

---

## Troubleshooting

### Erro: "Virtualizacao nao habilitada"

**Solucao:** Habilitar no BIOS
1. Reinicie o PC
2. Entre no BIOS (geralmente F2, F12, DEL durante boot)
3. Procure por "Intel VT-x" ou "AMD-V" ou "Virtualization"
4. Habilite
5. Salve e reinicie

### Erro: "0x80370102" ou falha de VM

**Causas possiveis:**
- Virtualizacao nao habilitada no BIOS
- Hyper-V conflitando

**Solucao:**
```powershell
# Verificar se Hyper-V esta habilitado
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V

# Se necessario, habilitar
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

### Erro: "wsl: comando nao encontrado"

**Solucao:**
```powershell
# Reinstalar WSL
wsl --install

# Ou via DISM
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all
```

### Erro: Ubuntu fica em loop de instalacao

**Solucao:**
```powershell
# Remover e reinstalar
wsl --unregister Ubuntu-24.04
wsl --install -d Ubuntu-24.04
```

### Lentidao extrema

**Causas:**
- Antivirus verificando arquivos WSL
- Disco cheio

**Solucao para antivirus:**
```powershell
# Adicionar exclusao (precisa Admin)
Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\Packages\CanonicalGroupLimited*"
```

---

## Comandos Uteis

| Comando | Descricao |
|---------|-----------|
| `wsl` | Entrar no Ubuntu |
| `wsl --shutdown` | Desligar WSL completamente |
| `wsl --list --verbose` | Ver distros instaladas |
| `wsl --status` | Ver status do WSL |
| `wsl --update` | Atualizar kernel WSL |

---

## Arquivos do Projeto

| Arquivo | Descricao |
|---------|-----------|
| `install-wsl2-portable.ps1` | Instalador WSL2 (PowerShell 5.1+) |
| `setup-dev-environment.ps1` | Config ambiente dev (Node, Python, Claude) |
| `powershell-profile.ps1` | Profile PS com aliases uteis |
| `setup-claude-code-wsl.ps1` | Script original (requer PS 7+) |

---

## FAQ

**P: Preciso instalar PowerShell 7?**
R: Nao! O script `install-wsl2-portable.ps1` funciona com PowerShell 5.1 (padrao do Windows).

**P: Posso usar outro Ubuntu?**
R: Sim, mude a variavel `$UBUNTU_DISTRO` no script para `Ubuntu-22.04` ou `Ubuntu`.

**P: Posso usar Debian/Fedora?**
R: Sim, mas precisara ajustar os scripts bash internos.

**P: O que fazer se falhar no DISM?**
R: Tente via Windows Settings → Apps → Optional Features → More Windows Features → Windows Subsystem for Linux

---

## Contato

Se encontrar problemas nao cobertos aqui:
1. Anote a mensagem de erro exata
2. Anote o comando que causou o erro
3. Entre em contato com o time

---

*Ultima atualizacao: 2025-12-07*
*Compativel com: Windows 10 (19041+), Windows 11, PowerShell 5.1+*
