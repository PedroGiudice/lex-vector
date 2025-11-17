# Roteiro de Migração WSL - PC Trabalho
**Guia Passo-a-Passo Completo para Iniciantes**

---

## 📋 Visão Geral

### O que vamos fazer?

Este guia vai te ensinar a configurar o **Windows Subsystem for Linux (WSL)** no seu PC do trabalho, criando um ambiente de desenvolvimento idêntico ao que já funciona no PC de casa.

**Resultado final:** Você terá Ubuntu 24.04 rodando dentro do Windows, com Node.js, Claude Code, Python e todo o projeto configurado e funcionando.

### Por que WSL?

- ✅ **Portabilidade:** Mesmo ambiente em ambas as máquinas
- ✅ **Performance:** Mais rápido que máquinas virtuais
- ✅ **Integração:** Acessa arquivos Windows normalmente
- ✅ **Ferramentas Linux:** bash, git, python nativos

### Tempo total estimado

⏱️ **1 hora e 40 minutos** divididos em:

- Fase 1: Preparação (Windows) - 15min
- Fase 2: Instalação WSL (Windows + Ubuntu) - 20min
- Fase 3: Node.js e Claude Code (Ubuntu) - 15min
- Fase 4: Python e Projeto (Ubuntu) - 30min
- Fase 5: Configurações Finais - 20min

### O que você precisa ter

- Windows 10 build 19041+ ou Windows 11
- 8GB RAM mínimo (16GB recomendado)
- 20GB espaço livre no disco C:\
- Conexão internet estável (vai baixar ~2-3GB)
- Conta GitHub configurada
- **PowerShell com privilégios de Administrador**

---

## Fase 1: Preparação (Windows) ⏱️ 15min

### 1.1 Verificar Pré-Requisitos

Antes de começar, vamos garantir que seu PC atende aos requisitos mínimos.

#### Passo 1: Verificar versão do Windows

**O que vamos fazer:**
Vamos checar se sua versão do Windows suporta WSL2.

**Por que é importante:**
WSL2 só funciona em versões específicas do Windows. Se o build for muito antigo, você precisará atualizar o Windows primeiro.

```powershell
# Abra PowerShell (não precisa ser Administrador ainda)
# Copie e cole este comando:

[System.Environment]::OSVersion.Version
```

**O que esperar:**
Você verá algo assim:
```
Major  Minor  Build  Revision
-----  -----  -----  --------
10     0      22631  0
```

**✅ Validação:**
- O número em **Build** deve ser **19041 ou maior**
- Se for menor, você precisa atualizar o Windows (Settings > Update & Security > Windows Update)

**❌ Se der errado:**
- Build < 19041: Atualize o Windows antes de continuar
- Erro "comando não encontrado": Você está no CMD ao invés do PowerShell. Feche e abra PowerShell.

---

#### Passo 2: Verificar espaço em disco

**O que vamos fazer:**
Vamos conferir quanto espaço livre você tem no drive C:\

**Por que é importante:**
O WSL vai ocupar cerca de 10-15GB após instalação completa. Precisamos garantir espaço suficiente.

```powershell
# Copie e cole este comando:

$disk = Get-PSDrive C
$freeGB = [math]::Round($disk.Free / 1GB, 2)
Write-Host "Espaço livre em C:\: $freeGB GB" -ForegroundColor Cyan

if ($freeGB -lt 20) {
    Write-Host "⚠️  ATENÇÃO: Espaço insuficiente!" -ForegroundColor Red
    Write-Host "   Mínimo necessário: 20GB" -ForegroundColor Red
} else {
    Write-Host "✅ Espaço suficiente para continuar" -ForegroundColor Green
}
```

**O que esperar:**
```
Espaço livre em C:\: 45.32 GB
✅ Espaço suficiente para continuar
```

**✅ Validação:**
- Você tem pelo menos 20GB livres? Se sim, continue.

**❌ Se der errado:**
- Espaço insuficiente: Libere espaço em C:\ antes de continuar
  - Desinstale programas não usados
  - Limpe arquivos temporários (Windows Disk Cleanup)
  - Mova arquivos grandes para outro drive

---

#### Passo 3: Verificar PowerShell 7+

**O que vamos fazer:**
Vamos confirmar que você tem PowerShell versão 7 ou superior.

**Por que é importante:**
Alguns comandos usados neste guia funcionam melhor no PowerShell 7+.

```powershell
# Verificar versão do PowerShell
$PSVersionTable.PSVersion
```

**O que esperar:**
```
Major  Minor  Patch  PreReleaseLabel BuildLabel
-----  -----  -----  --------------- ----------
7      4      1
```

**✅ Validação:**
- Major >= 7? Você está pronto!
- Major = 5? Ainda funciona, mas considere atualizar depois

**💡 Dica:**
Se você tiver PowerShell 5, não se preocupe - os comandos deste guia ainda vão funcionar. Você pode atualizar depois se quiser (download: https://github.com/PowerShell/PowerShell/releases)

---

### 1.2 Habilitar Recursos WSL

#### Passo 1: Abrir PowerShell como Administrador

**O que vamos fazer:**
A partir de agora, você vai precisar de privilégios de Administrador.

**Como fazer:**

1. Pressione **Windows + X**
2. Selecione **"Windows PowerShell (Admin)"** ou **"Terminal (Admin)"**
3. Clique **"Sim"** quando pedir confirmação

**✅ Validação:**
O título da janela deve mostrar "Administrador: Windows PowerShell" ou similar.

---

#### Passo 2: Habilitar recursos do Windows

**O que vamos fazer:**
Vamos ativar os componentes do Windows necessários para o WSL funcionar.

**Por que é importante:**
WSL depende de dois recursos específicos do Windows que vêm desabilitados por padrão.

```powershell
# Este comando habilita o Windows Subsystem for Linux
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Este comando habilita a Plataforma de Máquina Virtual
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

**O que esperar:**
Você verá várias linhas de progresso, e depois:
```
A operação foi concluída com êxito.
```

**⏱️ Tempo:** ~1-2 minutos

**✅ Validação:**
Ambos os comandos terminaram com "A operação foi concluída com êxito"?

**❌ Se der errado:**
- Erro "Acesso negado": Você precisa executar como Administrador (veja Passo 1)
- Erro "Recurso não encontrado": Sua versão do Windows pode ser antiga demais (veja seção 1.1)

**⚠️ IMPORTANTE:**
NÃO reinicie o computador ainda! Vamos fazer mais configurações antes.

---

### 1.3 Configurar .wslconfig

**O que vamos fazer:**
Vamos criar um arquivo de configuração que limita quanto de RAM e CPU o WSL pode usar.

**Por que é importante:**
Sem este arquivo, o WSL pode consumir TODA a memória disponível do Windows, deixando o PC lento. Vamos configurar limites seguros.

#### Passo 1: Criar o arquivo .wslconfig

```powershell
# Este comando abre o Bloco de Notas para criar o arquivo
notepad $env:USERPROFILE\.wslconfig
```

**O que esperar:**
O Bloco de Notas vai abrir e perguntar: **"Deseja criar um novo arquivo?"**
- Clique **"Sim"**

---

#### Passo 2: Adicionar configurações

**O que fazer:**
Copie este texto e cole no Bloco de Notas:

```ini
[wsl2]
memory=4GB
processors=2
swap=1GB
localhostForwarding=true
nestedVirtualization=false
```

**Explicação de cada linha:**
- `memory=4GB` - WSL pode usar no máximo 4GB de RAM
- `processors=2` - WSL pode usar no máximo 2 núcleos de CPU
- `swap=1GB` - WSL pode usar 1GB de memória virtual (swap)
- `localhostForwarding=true` - Permite acessar servidores WSL via localhost
- `nestedVirtualization=false` - Desabilita virtualização aninhada (não precisamos)

**💡 Dica:**
Se seu PC tiver 16GB+ de RAM, você pode aumentar para `memory=6GB` ou `memory=8GB`.

---

#### Passo 3: Salvar e fechar

**Como fazer:**
1. No Bloco de Notas, clique **Arquivo > Salvar**
2. Feche o Bloco de Notas

**✅ Validação:**
```powershell
# Verificar que o arquivo foi criado
Test-Path $env:USERPROFILE\.wslconfig

# Deve mostrar: True
```

**❌ Se mostrar False:**
Repita os passos 1-3. Certifique-se de clicar "Salvar" antes de fechar.

---

### 1.4 Configurar Windows Defender

**O que vamos fazer:**
Vamos adicionar uma exclusão no Windows Defender para que ele não escaneie os arquivos do WSL.

**Por que é importante:**
O Windows Defender escaneando arquivos WSL pode deixar o sistema **até 10x mais lento**. Esta exclusão melhora drasticamente a performance.

#### Passo 1: Encontrar o caminho do Ubuntu

**⚠️ ATENÇÃO:**
Se você **AINDA NÃO instalou o Ubuntu**, PULE esta seção por enquanto. Você vai voltar aqui depois da Fase 2.

Se você **JÁ TEM Ubuntu instalado** (improvável, mas possível):

```powershell
# PowerShell como Administrador
# Este comando encontra automaticamente onde o Ubuntu está instalado

$ubuntuPath = Get-ChildItem "$env:USERPROFILE\AppData\Local\Packages\" -Directory |
    Where-Object { $_.Name -like "CanonicalGroupLimited.Ubuntu24.04LTS_*" } |
    Select-Object -First 1 -ExpandProperty FullName

if ($ubuntuPath) {
    Write-Host "✅ Ubuntu encontrado em:" -ForegroundColor Green
    Write-Host "   $ubuntuPath" -ForegroundColor Cyan
} else {
    Write-Host "ℹ️  Ubuntu ainda não está instalado" -ForegroundColor Yellow
    Write-Host "   (Isso é normal se você ainda não fez a Fase 2)" -ForegroundColor Yellow
}
```

---

#### Passo 2: Adicionar exclusão

**Só execute este comando se o Passo 1 encontrou o Ubuntu:**

```powershell
# Este comando adiciona a exclusão no Windows Defender
Add-MpPreference -ExclusionPath $ubuntuPath

Write-Host "✅ Exclusão adicionada com sucesso!" -ForegroundColor Green
```

**O que esperar:**
Nenhuma mensagem de erro. Silêncio é sucesso!

---

#### Passo 3: Verificar exclusões

```powershell
# Este comando lista todas as exclusões do Defender
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath | Where-Object { $_ -like "*Ubuntu*" }
```

**O que esperar:**
```
C:\Users\SeuNome\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu24.04LTS_79rhkp1fndgsc
```

**✅ Validação:**
Você vê um caminho com "Ubuntu24.04LTS"? Perfeito!

**📝 Nota:**
Se você pulou esta seção porque ainda não tem Ubuntu, **marque para voltar aqui depois da Fase 2, Passo 2.2**.

---

### ✅ Checkpoint Fase 1

Antes de continuar para a Fase 2, confirme:

- [ ] Versão do Windows é build 19041+
- [ ] Você tem pelo menos 20GB livres
- [ ] PowerShell está aberto como Administrador
- [ ] Recursos WSL foram habilitados (2 comandos dism.exe)
- [ ] Arquivo .wslconfig foi criado e salvo
- [ ] (Opcional) Windows Defender configurado

**Pronto para continuar?**
Vamos para a Fase 2!

---

## Fase 2: Instalação WSL (Windows + Ubuntu) ⏱️ 20min

### 2.1 Instalar Ubuntu 24.04

**O que vamos fazer:**
Vamos instalar o Ubuntu 24.04 LTS (Long Term Support), que é a mesma versão usada no PC de casa.

**Por que Ubuntu 24.04:**
- Versão estável e suportada até 2029
- Mesma versão do PC casa = compatibilidade garantida
- Já vem com Python 3.12+ pré-instalado

---

#### Passo 1: Executar instalação

```powershell
# PowerShell como Administrador
# Este comando baixa e instala o Ubuntu 24.04

wsl --install -d Ubuntu-24.04
```

**O que esperar:**
```
Instalando: Ubuntu 24.04 LTS
Ubuntu 24.04 LTS foi instalado.
Iniciando Ubuntu 24.04 LTS...
```

**⏱️ Tempo:**
- Download: 2-5 minutos (dependendo da internet)
- Instalação: 2-3 minutos

**💡 Dica:**
Durante o download, você vai ver barras de progresso. É normal demorar alguns minutos.

---

#### Passo 2: Reiniciar o Windows

**Por que é necessário:**
As mudanças nos recursos do Windows (Fase 1.2) só são ativadas após reinício.

```powershell
# Este comando reinicia o Windows
Restart-Computer
```

**⚠️ ATENÇÃO:**
- Salve todos os arquivos abertos antes!
- Feche todos os programas
- O computador vai reiniciar em 10 segundos

**❌ Se não quiser reiniciar agora:**
Você pode reiniciar manualmente mais tarde. Mas **não pule** o reinício!

---

### 2.2 Configurar Usuário Ubuntu

**O que vai acontecer:**
Após o Windows reiniciar, o Ubuntu vai abrir automaticamente pela primeira vez.

**Se não abrir sozinho:**
1. Pressione **Windows + R**
2. Digite: `ubuntu2404`
3. Pressione **Enter**

---

#### Passo 1: Aguardar instalação final

**O que você vai ver:**
```
Installing, this may take a few minutes...
```

**⏱️ Tempo:** 1-2 minutos

**O que está acontecendo:**
O Ubuntu está configurando o sistema de arquivos e preparando o ambiente.

---

#### Passo 2: Criar username

**O que você vai ver:**
```
Enter new UNIX username:
```

**O que fazer:**
Digite um nome de usuário (só letras minúsculas, sem espaços).

**Exemplos:**
- ✅ Bom: `pedro`, `cmr`, `joao`
- ❌ Ruim: `Pedro` (maiúsculas), `cmr auto` (espaços)

**💡 Dica:**
Use o mesmo username em ambos os PCs para facilitar sincronização.

---

#### Passo 3: Criar senha

**O que você vai ver:**
```
New password:
```

**⚠️ IMPORTANTE:**
- **A senha NÃO vai aparecer na tela** enquanto você digita (é assim mesmo!)
- Digite a senha e pressione Enter
- Você vai precisar digitar novamente para confirmar

**Recomendações de segurança:**
- Mínimo 8 caracteres
- Misture letras, números e símbolos
- **ANOTE A SENHA** em algum lugar seguro!

**✅ Validação:**
Você vai ver:
```
passwd: password updated successfully
Installation successful!
```

---

#### Passo 4: Primeiro login

**O que você vai ver:**
Um prompt parecido com isso:
```bash
username@hostname:~$
```

**Exemplo:**
```bash
pedro@DESKTOP-ABC123:~$
```

**🎉 Parabéns!**
Você está agora dentro do Ubuntu Linux rodando no Windows!

---

#### Passo 5: Voltar e configurar Windows Defender

**Lembra da Fase 1.4?**
Se você pulou, **AGORA é a hora de voltar lá** e adicionar a exclusão do Windows Defender.

**Como fazer:**
1. Minimize a janela do Ubuntu (deixe aberta)
2. Abra PowerShell como Administrador (Windows)
3. Volte para Fase 1.4 e execute os comandos
4. Volte aqui e continue

---

### 2.3 Atualizar Sistema Base

**O que vamos fazer:**
Vamos atualizar todos os pacotes do Ubuntu para as versões mais recentes.

**Por que é importante:**
- Correções de segurança
- Bug fixes
- Melhor compatibilidade

---

#### Passo 1: Atualizar lista de pacotes

**O que vamos fazer:**
Baixar a lista mais recente de pacotes disponíveis.

```bash
# Copie e cole este comando no Ubuntu
sudo apt update
```

**O que esperar:**
```
[sudo] password for pedro:
```

**O que fazer:**
Digite a senha que você criou no Passo 2.2.3 (a senha NÃO vai aparecer, é normal).

Depois você vai ver:
```
Hit:1 http://archive.ubuntu.com/ubuntu noble InRelease
Get:2 http://archive.ubuntu.com/ubuntu noble-updates InRelease [126 kB]
...
Reading package lists... Done
Building dependency tree... Done
```

**⏱️ Tempo:** 30-60 segundos

---

#### Passo 2: Instalar atualizações

**O que vamos fazer:**
Instalar todas as atualizações disponíveis.

```bash
# Este comando atualiza os pacotes instalados
sudo apt upgrade -y
```

**Explicação:**
- `sudo` = executar como administrador
- `apt` = gerenciador de pacotes do Ubuntu
- `upgrade` = atualizar pacotes
- `-y` = responder "sim" automaticamente

**O que esperar:**
```
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
Calculating upgrade... Done
...
```

**⏱️ Tempo:** 2-5 minutos (dependendo de quantas atualizações)

**💡 Dica:**
Você pode ver mensagens como "Setting up..." e barras de progresso. É normal!

**✅ Validação:**
Última linha deve ser:
```
Reading package lists... Done
```

---

### 2.4 Instalar Ferramentas Essenciais

**O que vamos fazer:**
Vamos instalar as ferramentas necessárias para desenvolvimento.

**Lista de ferramentas:**
- **build-essential** - Compiladores C/C++ (necessário para alguns pacotes Python)
- **curl/wget** - Download de arquivos
- **git** - Controle de versão
- **vim** - Editor de texto
- **htop** - Monitor de processos
- **tree** - Visualizar estrutura de diretórios
- **ripgrep** - Busca rápida em arquivos (usado pelo Claude Code)
- **jq** - Processar JSON no terminal
- **zip** - Compactar/descompactar arquivos
- **python3/python3-pip** - Python e gerenciador de pacotes
- **python3-venv** - Criar ambientes virtuais Python
- **python3-dev** - Headers Python (necessário para alguns pacotes)

---

#### Passo único: Instalar tudo de uma vez

```bash
# Este comando instala todas as ferramentas necessárias
sudo apt install -y build-essential curl wget git vim htop tree ripgrep jq zip python3 python3-pip python3-venv python3-dev
```

**O que esperar:**
```
Reading package lists... Done
Building dependency tree... Done
...
The following NEW packages will be installed:
  build-essential curl wget git vim htop tree ripgrep jq zip python3-pip python3-venv python3-dev ...
...
Unpacking ...
Setting up ...
Processing triggers for ...
```

**⏱️ Tempo:** 3-5 minutos

**✅ Validação:**
Vamos testar algumas ferramentas:

```bash
# Testar Git
git --version
# Deve mostrar: git version 2.x.x

# Testar Python
python3 --version
# Deve mostrar: Python 3.12.x

# Testar ripgrep
rg --version
# Deve mostrar: ripgrep 13.x.x ou superior

# Testar jq
jq --version
# Deve mostrar: jq-1.x
```

**❌ Se algum comando não funcionar:**
```bash
# Ver quais pacotes foram instalados
dpkg -l | grep -E "git|python3|ripgrep|jq"

# Reinstalar pacote específico (exemplo: git)
sudo apt install --reinstall git
```

---

### ✅ Checkpoint Fase 2

Antes de continuar para a Fase 3, confirme:

- [ ] Ubuntu 24.04 instalado
- [ ] Usuário criado e você está logado
- [ ] Windows Defender configurado (exclusão adicionada)
- [ ] Sistema atualizado (`apt update && apt upgrade`)
- [ ] Ferramentas essenciais instaladas
- [ ] Git, Python, ripgrep funcionando

**Comandos de validação rápida:**
```bash
# Executar todos de uma vez
echo "Git: $(git --version)"
echo "Python: $(python3 --version)"
echo "ripgrep: $(rg --version | head -1)"
echo "jq: $(jq --version)"
```

**Você deve ver 4 linhas sem erros.**

**Pronto para continuar?**
Vamos para a Fase 3!

---

## Fase 3: Node.js e Claude Code (Ubuntu) ⏱️ 15min

### 3.1 Instalar nvm (Node Version Manager)

**O que vamos fazer:**
Vamos instalar o **nvm**, uma ferramenta que permite instalar e gerenciar múltiplas versões do Node.js.

**Por que usar nvm:**
- ✅ Permite trocar de versão facilmente
- ✅ Não requer sudo para instalar pacotes
- ✅ Isola versões por projeto
- ✅ Mesma ferramenta usada no PC casa

**Por que NÃO instalar Node.js direto via apt:**
- ❌ Versão antiga (Ubuntu 24.04 vem com Node.js 18, precisamos da 24)
- ❌ Difícil de atualizar
- ❌ Requer sudo para npm install -g

---

#### Passo 1: Baixar e instalar nvm

**O que vamos fazer:**
Executar o script de instalação oficial do nvm.

```bash
# Este comando baixa e instala o nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
```

**Explicação:**
- `curl -o-` = baixar arquivo e enviar para saída
- `| bash` = executar o script baixado

**O que esperar:**
```
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 16555  100 16555    0     0  xxxxx      0 --:--:-- --:--:-- --:--:-- xxxxx
=> Downloading nvm from git to '/home/username/.nvm'
...
=> Appending nvm source string to /home/username/.bashrc
...
=> Close and reopen your terminal to start using nvm or run the following to use it now:

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
```

**⏱️ Tempo:** 30-60 segundos

---

#### Passo 2: Recarregar configurações do shell

**O que vamos fazer:**
Aplicar as mudanças no arquivo `.bashrc` sem precisar fechar/abrir o terminal.

**Por que é importante:**
O nvm adiciona configurações ao `.bashrc`. Precisamos "recarregar" estas configurações.

```bash
# Este comando recarrega o .bashrc
source ~/.bashrc
```

**O que esperar:**
Nenhuma mensagem (silêncio é sucesso).

---

#### Passo 3: Verificar instalação do nvm

```bash
# Verificar se nvm está disponível
nvm --version
```

**O que esperar:**
```
0.40.1
```

**✅ Validação:**
Você vê um número de versão (0.40.1 ou similar)? Perfeito!

**❌ Se mostrar "nvm: command not found":**

**Diagnóstico:**
```bash
# Verificar se o nvm foi instalado
ls -la ~/.nvm

# Você deve ver um diretório com arquivos
```

**Solução:**
```bash
# Adicionar manualmente ao .bashrc
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc
echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc
source ~/.bashrc

# Testar novamente
nvm --version
```

---

### 3.2 Instalar Node.js v24

**O que vamos fazer:**
Vamos instalar a versão 24 do Node.js, que é a mesma usada no PC de casa.

**Por que versão 24:**
- Mesma versão = compatibilidade garantida
- Versão LTS (Long Term Support) = estável
- Claude Code funciona melhor com versões recentes

---

#### Passo 1: Instalar Node.js

```bash
# Este comando baixa e instala o Node.js versão 24
nvm install 24
```

**O que esperar:**
```
Downloading and installing node v24.11.1...
Downloading https://nodejs.org/dist/v24.11.1/node-v24.11.1-linux-x64.tar.xz...
######################################################################### 100.0%
Computing checksum with sha256sum
Checksums matched!
Now using node v24.11.1 (npm v11.6.2)
Creating default alias: default -> 24 (-> v24.11.1)
```

**⏱️ Tempo:** 1-2 minutos (download + instalação)

**💡 Dica:**
Você pode ver barras de progresso durante o download. É normal demorar!

---

#### Passo 2: Definir como versão padrão

**O que vamos fazer:**
Configurar a v24 para ser usada automaticamente sempre que você abrir um terminal.

```bash
# Este comando define v24 como padrão
nvm alias default 24
```

**O que esperar:**
```
default -> 24 (-> v24.11.1)
```

**Explicação:**
Agora sempre que você abrir um novo terminal, a versão 24 será ativada automaticamente.

---

#### Passo 3: Ativar a versão (sessão atual)

```bash
# Este comando ativa v24 agora (nesta sessão)
nvm use 24
```

**O que esperar:**
```
Now using node v24.11.1
```

---

#### Passo 4: Verificar instalação

```bash
# Verificar versão do Node.js
node --version

# Verificar versão do npm
npm --version
```

**O que esperar:**
```
v24.11.1
11.6.2
```

(Números exatos podem variar: v24.x.x e npm 11.x.x)

**✅ Validação:**
- Node.js começa com **v24**?
- npm começa com **11** ou **10**?

Se sim, perfeito!

**❌ Se mostrar versões diferentes:**
```bash
# Listar versões instaladas
nvm list

# Deve mostrar:
#        v24.11.1
# default -> 24 (-> v24.11.1)

# Se não mostrar v24, instale novamente:
nvm install 24
nvm use 24
```

---

### 3.3 Instalar Claude Code

**O que vamos fazer:**
Vamos instalar a ferramenta de linha de comando **Claude Code**, que é uma interface CLI para o Claude AI da Anthropic.

**O que é Claude Code:**
Uma ferramenta que permite interagir com o Claude AI diretamente do terminal, com suporte a hooks, agents, skills e muito mais.

---

#### Passo 1: Instalar globalmente via npm

```bash
# Este comando instala Claude Code globalmente (disponível em todo o sistema)
npm install -g @anthropic-ai/claude-code
```

**Explicação:**
- `npm install` = instalar pacote
- `-g` = global (disponível em qualquer diretório)
- `@anthropic-ai/claude-code` = nome do pacote

**O que esperar:**
```
added 150 packages in 45s

25 packages are looking for funding
  run `npm fund` for details
```

**⏱️ Tempo:** 30-60 segundos

**💡 Dica:**
Você pode ver avisos (warnings) sobre pacotes opcionais. Pode ignorar.

---

#### Passo 2: Verificar instalação

```bash
# Verificar que Claude Code foi instalado
claude --version
```

**O que esperar:**
```
2.0.42
```

(Ou versão superior)

**✅ Validação:**
Você vê um número de versão? Perfeito!

**❌ Se mostrar "claude: command not found":**

**Diagnóstico:**
```bash
# Verificar onde npm instala pacotes globais
npm list -g --depth=0 | grep claude-code
```

**Solução:**
```bash
# Reinstalar
npm uninstall -g @anthropic-ai/claude-code
npm install -g @anthropic-ai/claude-code

# Se ainda não funcionar, verificar PATH do npm
echo $PATH | grep npm

# Adicionar ao PATH se necessário
echo 'export PATH="$PATH:$HOME/.nvm/versions/node/v24.11.1/bin"' >> ~/.bashrc
source ~/.bashrc
```

---

#### Passo 3: Autenticar (primeira execução)

**O que vamos fazer:**
Executar Claude Code pela primeira vez para configurar a API key.

**⚠️ IMPORTANTE:**
Você vai precisar de uma **API key da Anthropic**. Se não tiver:
- Acesse: https://console.anthropic.com/settings/keys
- Crie uma nova API key
- Copie e guarde em local seguro

```bash
# Executar Claude Code pela primeira vez
claude
```

**O que vai acontecer:**

1. Claude vai pedir a API key:
```
Welcome to Claude Code!

Please enter your Anthropic API key:
```

2. Cole sua API key e pressione Enter

**💡 Dica:**
A API key não vai aparecer na tela (segurança). É normal!

3. Claude vai perguntar onde salvar a configuração:
```
Where would you like to save the API key?
  [1] Local config (~/.config/claude-code/)
  [2] Environment variable
```

4. Digite `1` e pressione Enter (Local config é mais fácil)

**O que esperar:**
```
✓ API key saved successfully
```

**🎉 Pronto!**
Claude Code está instalado e autenticado.

---

### 3.4 Validar Instalação Completa

**Vamos fazer um teste completo de tudo que instalamos:**

```bash
# Executar todos os testes de uma vez
echo "=== Validação Completa - Fase 3 ==="
echo ""
echo "1. nvm:"
nvm --version

echo ""
echo "2. Node.js:"
node --version

echo ""
echo "3. npm:"
npm --version

echo ""
echo "4. Claude Code:"
claude --version

echo ""
echo "=== Tudo instalado! ==="
```

**Output esperado:**
```
=== Validação Completa - Fase 3 ===

1. nvm:
0.40.1

2. Node.js:
v24.11.1

3. npm:
11.6.2

4. Claude Code:
2.0.42

=== Tudo instalado! ===
```

**✅ Validação:**
Todos os 4 comandos mostraram versões sem erros? Excelente!

---

### ✅ Checkpoint Fase 3

Antes de continuar para a Fase 4, confirme:

- [ ] nvm instalado (versão 0.40.1)
- [ ] Node.js v24 instalado e ativo
- [ ] npm v11+ disponível
- [ ] Claude Code instalado e autenticado
- [ ] Todos os comandos `--version` funcionam

**Comandos de validação rápida:**
```bash
nvm --version && node --version && npm --version && claude --version
```

**Você deve ver 4 números de versão, um em cada linha.**

**Pronto para continuar?**
Vamos para a Fase 4 - A parte mais importante!

---

## Fase 4: Python e Projeto (Ubuntu) ⏱️ 30min

### 4.1 Criar Estrutura de Diretórios

**O que vamos fazer:**
Vamos criar a estrutura de diretórios padrão usada no projeto.

**Estrutura completa:**
```
~/claude-work/
└── repos/
    └── Claude-Code-Projetos/  ← vai ser criado pelo git clone
```

**Por que esta estrutura:**
- **~/claude-work/** = Diretório raiz para todos os projetos Claude
- **repos/** = Repositórios Git
- **Claude-Code-Projetos/** = Este projeto específico

---

#### Passo 1: Criar diretórios

```bash
# Este comando cria a estrutura completa
mkdir -p ~/claude-work/repos
```

**Explicação:**
- `mkdir` = make directory (criar diretório)
- `-p` = criar diretórios pai se não existirem
- `~` = seu diretório home (/home/username)

**O que esperar:**
Nenhuma mensagem (silêncio é sucesso).

---

#### Passo 2: Navegar para o diretório

```bash
# Ir para o diretório repos
cd ~/claude-work/repos
```

---

#### Passo 3: Confirmar localização

```bash
# Verificar onde você está
pwd
```

**O que esperar:**
```
/home/username/claude-work/repos
```

(Substitua "username" pelo seu username real)

**✅ Validação:**
O caminho termina com `/claude-work/repos`? Perfeito!

---

### 4.2 Configurar Git

**O que vamos fazer:**
Vamos configurar o Git com seu nome e email, e configurar autenticação.

**Por que é importante:**
Git precisa saber quem você é para os commits. Além disso, vamos configurar autenticação para não ter que digitar senha toda vez.

---

#### Passo 1: Configurar nome e email

```bash
# Configurar seu nome (use seu nome real)
git config --global user.name "Seu Nome Completo"

# Configurar seu email (use o mesmo email do GitHub)
git config --global user.email "seu.email@exemplo.com"
```

**⚠️ ATENÇÃO:**
- Use **ASPAS DUPLAS** ao redor do nome
- Email deve ser o mesmo da sua conta GitHub
- Exemplo real:
  ```bash
  git config --global user.name "Pedro Giudice"
  git config --global user.email "pedro@exemplo.com"
  ```

---

#### Passo 2: Verificar configuração

```bash
# Ver configuração atual
git config --global --list
```

**O que esperar:**
```
user.name=Seu Nome Completo
user.email=seu.email@exemplo.com
```

**✅ Validação:**
Nome e email estão corretos? Continue!

---

#### Passo 3: Configurar autenticação

**Você tem duas opções:**
1. **SSH Keys** (recomendado - mais seguro)
2. **Credential Helper** (mais simples, menos seguro)

Vamos fazer **SSH Keys** (opção recomendada).

---

#### Passo 3A: Gerar chave SSH

**O que vamos fazer:**
Criar um par de chaves (pública/privada) para autenticação.

```bash
# Gerar chave SSH
ssh-keygen -t ed25519 -C "seu.email@exemplo.com" -f ~/.ssh/id_ed25519 -N ""
```

**Explicação:**
- `-t ed25519` = tipo de criptografia (moderno e seguro)
- `-C "email"` = comentário (seu email)
- `-f ~/.ssh/id_ed25519` = arquivo de saída
- `-N ""` = sem senha (facilita uso, mas menos seguro)

**💡 Segurança:**
Se preferir senha na chave (mais seguro), remova `-N ""` e o comando vai perguntar a senha.

**O que esperar:**
```
Generating public/private ed25519 key pair.
Your identification has been saved in /home/username/.ssh/id_ed25519
Your public key has been saved in /home/username/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx seu.email@exemplo.com
```

---

#### Passo 3B: Iniciar ssh-agent

**O que vamos fazer:**
Iniciar o agente SSH que gerencia suas chaves.

```bash
# Iniciar ssh-agent
eval "$(ssh-agent -s)"
```

**O que esperar:**
```
Agent pid 12345
```

(Número pode variar)

---

#### Passo 3C: Adicionar chave ao ssh-agent

```bash
# Adicionar chave privada ao agent
ssh-add ~/.ssh/id_ed25519
```

**O que esperar:**
```
Identity added: /home/username/.ssh/id_ed25519 (seu.email@exemplo.com)
```

---

#### Passo 3D: Copiar chave pública

**O que vamos fazer:**
Exibir a chave pública para você copiar.

```bash
# Mostrar chave pública
cat ~/.ssh/id_ed25519.pub
```

**O que esperar:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx seu.email@exemplo.com
```

**📋 IMPORTANTE:**
1. **Selecione TODO o texto** (começa com `ssh-ed25519` e termina com seu email)
2. **Copie** (Ctrl+Shift+C no Ubuntu terminal)
3. **Guarde** na área de transferência

---

#### Passo 3E: Adicionar chave no GitHub

**O que fazer:**

1. Abra navegador e vá para: https://github.com/settings/keys
2. Clique em **"New SSH key"**
3. Em **Title**, digite algo como: `PC Trabalho - WSL Ubuntu`
4. Em **Key**, **cole** a chave que você copiou
5. Clique em **"Add SSH key"**
6. GitHub pode pedir sua senha - digite e confirme

**💡 Dica:**
Deixe a janela do terminal aberta. Vamos testar a chave agora!

---

#### Passo 3F: Testar conexão SSH

**O que vamos fazer:**
Verificar se o GitHub reconhece sua chave SSH.

```bash
# Testar conexão com GitHub
ssh -T git@github.com
```

**⚠️ Na primeira vez, você vai ver:**
```
The authenticity of host 'github.com (140.82.113.4)' can't be established.
ED25519 key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

**O que fazer:**
Digite `yes` e pressione Enter.

**O que esperar depois:**
```
Hi SeuUsername! You've successfully authenticated, but GitHub does not provide shell access.
```

**✅ Validação:**
Você viu a mensagem "successfully authenticated"? Perfeito!

**❌ Se der erro "Permission denied":**

**Diagnóstico:**
```bash
# Verificar se chave foi criada
ls -la ~/.ssh/id_ed25519*

# Você deve ver:
# id_ed25519 (chave privada)
# id_ed25519.pub (chave pública)
```

**Solução:**
```bash
# Verificar se chave está no agent
ssh-add -l

# Se não mostrar sua chave:
ssh-add ~/.ssh/id_ed25519

# Testar novamente
ssh -T git@github.com
```

---

### 4.3 Clonar Repositório

**O que vamos fazer:**
Baixar o código do projeto do GitHub para sua máquina.

**Certifique-se de estar no diretório correto:**
```bash
# Verificar onde você está
pwd

# Deve mostrar: /home/username/claude-work/repos
# Se não estiver, execute:
cd ~/claude-work/repos
```

---

#### Passo 1: Clonar via SSH

```bash
# Clonar repositório
git clone git@github.com:PedroGiudice/Claude-Code-Projetos.git
```

**O que esperar:**
```
Cloning into 'Claude-Code-Projetos'...
remote: Enumerating objects: 1234, done.
remote: Counting objects: 100% (1234/1234), done.
remote: Compressing objects: 100% (567/567), done.
remote: Total 1234 (delta 890), reused 1123 (delta 801), pack-reused 0
Receiving objects: 100% (1234/1234), 2.45 MiB | 3.12 MiB/s, done.
Resolving deltas: 100% (890/890), done.
```

**⏱️ Tempo:** 30-60 segundos (dependendo da internet)

**❌ Se der erro "Permission denied":**
Sua chave SSH não está configurada corretamente. Volte ao Passo 4.2.3F.

**❌ Se der erro "Repository not found":**
Verifique se o username/repositório está correto. Se for um repositório privado, certifique-se de ter acesso.

---

#### Passo 2: Entrar no diretório do projeto

```bash
# Navegar para o projeto
cd Claude-Code-Projetos
```

---

#### Passo 3: Verificar conteúdo

```bash
# Listar arquivos/diretórios
ls -la
```

**O que esperar:**
```
total 123
drwxr-xr-x 10 username username  4096 Nov 17 10:30 .
drwxr-xr-x  3 username username  4096 Nov 17 10:29 ..
drwxr-xr-x  8 username username  4096 Nov 17 10:30 .git
drwxr-xr-x  4 username username  4096 Nov 17 10:30 .claude
-rw-r--r--  1 username username  1234 Nov 17 10:30 .gitignore
-rw-r--r--  1 username username  5678 Nov 17 10:30 README.md
drwxr-xr-x  7 username username  4096 Nov 17 10:30 agentes
drwxr-xr-x  3 username username  4096 Nov 17 10:30 comandos
drwxr-xr-x  5 username username  4096 Nov 17 10:30 docs
drwxr-xr-x  3 username username  4096 Nov 17 10:30 mcp-servers
drwxr-xr-x  3 username username  4096 Nov 17 10:30 shared
drwxr-xr-x 40 username username  4096 Nov 17 10:30 skills
```

**✅ Validação:**
Você vê as pastas `agentes`, `comandos`, `docs`, `skills`? Perfeito!

---

#### Passo 4: Verificar status Git

```bash
# Verificar status do repositório
git status
```

**O que esperar:**
```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

**✅ Validação:**
Mensagem "working tree clean"? Excelente!

---

### 4.4 Criar Virtual Environments (Python)

**O que vamos fazer:**
Vamos criar ambientes virtuais Python isolados para cada um dos 5 agentes do projeto.

**O que são virtual environments (venvs):**
Ambientes Python isolados que permitem instalar pacotes específicos sem afetar o sistema global.

**Por que um venv por agente:**
Cada agente pode ter dependências diferentes. Isolamento evita conflitos.

**Os 5 agentes:**
1. **djen-tracker** - Monitora Diário Eletrônico de Justiça
2. **legal-articles-finder** - Encontra artigos legais
3. **legal-lens** - Analisa publicações legais
4. **legal-rag** - RAG (Retrieval Augmented Generation) legal
5. **oab-watcher** - Monitora diário da OAB

---

#### Preparação: Verificar diretório

```bash
# Garantir que você está no diretório do projeto
pwd

# Deve mostrar: /home/username/claude-work/repos/Claude-Code-Projetos
```

---

#### Agente 1: djen-tracker

**Passo 1: Navegar para o agente**
```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/djen-tracker
```

**Passo 2: Criar venv**
```bash
python3 -m venv .venv
```

**O que está acontecendo:**
Python está criando um ambiente virtual na pasta `.venv`

**⏱️ Tempo:** 10-20 segundos

**Passo 3: Ativar venv**
```bash
source .venv/bin/activate
```

**O que esperar:**
Seu prompt vai mudar para:
```bash
(.venv) username@hostname:~/claude-work/repos/Claude-Code-Projetos/agentes/djen-tracker$
```

**💡 Nota:** O `(.venv)` no início indica que o ambiente virtual está ativo!

**Passo 4: Atualizar pip**
```bash
pip install --upgrade pip --quiet
```

**⏱️ Tempo:** 5-10 segundos

**Passo 5: Instalar dependências**
```bash
# Verificar se requirements.txt existe
if [ -f requirements.txt ]; then
    pip install -r requirements.txt --quiet
    echo "✅ Dependências instaladas"
else
    echo "⚠️  requirements.txt não encontrado (pode ser normal)"
fi
```

**⏱️ Tempo:** 30-60 segundos (dependendo das dependências)

**Passo 6: Desativar venv**
```bash
deactivate
```

**O que esperar:**
O `(.venv)` desaparece do prompt.

**Passo 7: Voltar ao diretório raiz**
```bash
cd ~/claude-work/repos/Claude-Code-Projetos
```

---

#### Agente 2: legal-articles-finder

```bash
# Navegar
cd agentes/legal-articles-finder

# Criar venv
python3 -m venv .venv

# Ativar
source .venv/bin/activate

# Atualizar pip
pip install --upgrade pip --quiet

# Instalar dependências (se existir requirements.txt)
[ -f requirements.txt ] && pip install -r requirements.txt --quiet && echo "✅ Dependências instaladas"

# Desativar
deactivate

# Voltar
cd ~/claude-work/repos/Claude-Code-Projetos
```

---

#### Agente 3: legal-lens

```bash
cd agentes/legal-lens
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --quiet
[ -f requirements.txt ] && pip install -r requirements.txt --quiet && echo "✅ Dependências instaladas"
deactivate
cd ~/claude-work/repos/Claude-Code-Projetos
```

---

#### Agente 4: legal-rag

```bash
cd agentes/legal-rag
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --quiet
[ -f requirements.txt ] && pip install -r requirements.txt --quiet && echo "✅ Dependências instaladas"
deactivate
cd ~/claude-work/repos/Claude-Code-Projetos
```

---

#### Agente 5: oab-watcher

```bash
cd agentes/oab-watcher
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --quiet
[ -f requirements.txt ] && pip install -r requirements.txt --quiet && echo "✅ Dependências instaladas"
deactivate
cd ~/claude-work/repos/Claude-Code-Projetos
```

---

#### Validação: Verificar todos os venvs

```bash
# Listar todos os .venv criados
ls agentes/*/.venv -d
```

**O que esperar:**
```
agentes/djen-tracker/.venv
agentes/legal-articles-finder/.venv
agentes/legal-lens/.venv
agentes/legal-rag/.venv
agentes/oab-watcher/.venv
```

**✅ Validação:**
Você vê 5 linhas (5 venvs)? Perfeito!

**❌ Se algum estiver faltando:**
Volte e repita os passos para o agente específico.

---

**🎉 Parabéns!**
Você criou 5 ambientes virtuais Python isolados!

**💡 Como usar os venvs no dia a dia:**
```bash
# Para trabalhar em um agente específico:
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/oab-watcher
source .venv/bin/activate

# Agora você pode executar scripts Python:
python main.py

# Quando terminar:
deactivate
```

---

### 4.5 Instalar npm Packages (MCP Server)

**O que vamos fazer:**
Vamos instalar as dependências npm para o **MCP Server** (Model Context Protocol Server), que é usado pelo agente djen-tracker.

**O que é MCP Server:**
Um servidor que fornece contexto adicional para o Claude AI, permitindo acesso a dados externos e funcionalidades especializadas.

---

#### Passo 1: Navegar para o diretório

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/mcp-servers/djen-mcp-server
```

---

#### Passo 2: Verificar package.json

```bash
# Verificar se package.json existe
ls -la package.json
```

**O que esperar:**
```
-rw-r--r-- 1 username username 1234 Nov 17 10:30 package.json
```

**✅ Validação:**
Arquivo existe? Continue!

---

#### Passo 3: Instalar dependências

```bash
# Instalar todos os pacotes listados em package.json
npm install
```

**O que esperar:**
```
npm WARN deprecated package1@1.0.0: This package is deprecated...
npm WARN deprecated package2@2.0.0: This package is deprecated...

added 340 packages, and audited 341 packages in 45s

25 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
```

**⏱️ Tempo:** 1-3 minutos (dependendo da internet)

**💡 Nota:**
- Avisos (WARN) sobre pacotes deprecados são normais - pode ignorar
- Se aparecer vulnerabilidades, não se preocupe por enquanto

---

#### Passo 4: Verificar instalação

```bash
# Contar pacotes instalados
ls node_modules/ | wc -l
```

**O que esperar:**
```
340
```

(Ou número próximo - pode variar entre 330-350)

**✅ Validação:**
Número próximo de 340? Excelente!

---

#### Passo 5: Testar se servidor funciona

```bash
# Tentar executar o servidor (vai mostrar help/erro esperado)
node index.js || echo "✅ Arquivo index.js encontrado"
```

**💡 Nota:**
É esperado que dê erro ou mostre ajuda - só estamos verificando que o arquivo existe.

---

#### Passo 6: Voltar ao diretório raiz

```bash
cd ~/claude-work/repos/Claude-Code-Projetos
```

---

### ✅ Checkpoint Fase 4

Antes de continuar para a Fase 5, confirme:

- [ ] Estrutura `~/claude-work/repos/Claude-Code-Projetos` criada
- [ ] Git configurado (nome, email, SSH)
- [ ] Repositório clonado com sucesso
- [ ] 5 venvs Python criados e funcionando
- [ ] npm packages instalados (340 em djen-mcp-server)

**Comandos de validação completa:**

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

echo "=== Validação Completa - Fase 4 ==="
echo ""

echo "1. Localização:"
pwd

echo ""
echo "2. Git:"
git status | head -3

echo ""
echo "3. Venvs Python:"
ls agentes/*/.venv -d | wc -l
echo "   (Deve mostrar: 5)"

echo ""
echo "4. npm packages:"
ls mcp-servers/djen-mcp-server/node_modules/ | wc -l
echo "   (Deve mostrar: ~340)"

echo ""
echo "=== Fase 4 Completa! ==="
```

**Output esperado:**
- Localização correta
- Git: working tree clean
- 5 venvs
- ~340 npm packages

**Tudo OK?**
Vamos para a Fase 5 - última etapa!

---

## Fase 5: Configurações Finais ⏱️ 20min

### 5.1 Validar Hooks JavaScript

**O que vamos fazer:**
Vamos testar os hooks JavaScript do projeto para garantir que estão funcionando corretamente.

**O que são hooks:**
Scripts que são executados automaticamente em certos eventos do Claude Code (como início de sessão, submissão de prompt, etc.).

**Por que testar:**
Hooks quebrados podem causar erros silenciosos ou comportamento inesperado no Claude Code.

---

#### Passo 1: Verificar localização

```bash
# Garantir que você está no diretório correto
cd ~/claude-work/repos/Claude-Code-Projetos
pwd
```

**Deve mostrar:**
```
/home/username/claude-work/repos/Claude-Code-Projetos
```

---

#### Passo 2: Listar hooks disponíveis

```bash
# Ver todos os hooks JavaScript
ls .claude/hooks/*.js
```

**O que esperar:**
```
.claude/hooks/invoke-legal-braniac-hybrid.js
.claude/hooks/session-context-hybrid.js
... (outros hooks)
```

---

#### Passo 3: Testar hook principal #1

**Hook: invoke-legal-braniac-hybrid.js**

```bash
# Executar hook manualmente
node .claude/hooks/invoke-legal-braniac-hybrid.js
```

**O que esperar:**
Um JSON com estrutura similar a:
```json
{
  "continue": true,
  "context": "...",
  "timestamp": "2025-11-17T..."
}
```

**✅ Validação:**
- Saída é JSON válido?
- Tem campo `"continue": true`?
- Sem erros?

Se sim, perfeito!

**❌ Se der erro:**

**Erro comum: "Cannot find module"**
```bash
# Diagnóstico: verificar se node_modules existe
ls -la .claude/hooks/node_modules/

# Se não existir, instalar dependências:
cd .claude/hooks
npm install
cd ~/claude-work/repos/Claude-Code-Projetos
```

---

#### Passo 4: Testar hook principal #2

**Hook: session-context-hybrid.js**

```bash
# Executar hook manualmente
node .claude/hooks/session-context-hybrid.js
```

**O que esperar:**
JSON similar ao hook anterior:
```json
{
  "continue": true,
  "sessionContext": "...",
  "timestamp": "..."
}
```

**✅ Validação:**
JSON válido sem erros? Excelente!

---

#### Passo 5: Validação com jq (opcional mas recomendado)

**O que vamos fazer:**
Usar `jq` para validar que o JSON é válido e extrair campo específico.

```bash
# Testar hook e extrair campo "continue"
node .claude/hooks/invoke-legal-braniac-hybrid.js | jq -r '.continue'
```

**O que esperar:**
```
true
```

**✅ Validação:**
Mostra `true`? Perfeito! O hook está retornando JSON válido.

---

### 5.2 PowerShell Profile (Opcional, mas Muito Útil!)

**O que vamos fazer:**
Instalar um PowerShell profile customizado que adiciona comandos rápidos para trabalhar com WSL.

**⚠️ ATENÇÃO:**
Esta etapa é executada no **WINDOWS** (PowerShell), não no Ubuntu!

**Benefícios:**
- `scc` - Start Claude Code (abre Claude Code no projeto)
- `gcp` - Go to Claude Project (abre bash WSL no projeto)
- `gsync` - Git sync (pull + status)
- `cstatus` - Check Claude Code status
- `claude <args>` - Executar Claude Code sem prefixo `wsl`

---

#### Passo 1: Abrir PowerShell no Windows

**Como fazer:**
1. Pressione **Windows + X**
2. Selecione **"Windows PowerShell"** (não precisa ser Admin)

---

#### Passo 2: Baixar o profile

**Opção A: Se você já tem o repositório clonado no Windows**
```powershell
# Navegar para o repositório (ajuste o caminho se necessário)
cd C:\Users\SeuNome\Downloads\Claude-Code-Projetos

# ou onde quer que você tenha baixado
```

**Opção B: Baixar apenas o profile**
```powershell
# Baixar profile direto do GitHub
$profileUrl = "https://raw.githubusercontent.com/PedroGiudice/Claude-Code-Projetos/main/powershell-profile.ps1"
$tempPath = "$env:TEMP\powershell-profile.ps1"
Invoke-WebRequest -Uri $profileUrl -OutFile $tempPath

# Usar o arquivo baixado
$sourceFile = $tempPath
```

---

#### Passo 3: Backup do profile existente (se houver)

```powershell
# Verificar se já existe profile
if (Test-Path $PROFILE) {
    $backupName = "$PROFILE.backup.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Copy-Item $PROFILE $backupName
    Write-Host "✅ Backup criado: $backupName" -ForegroundColor Green
} else {
    Write-Host "ℹ️  Nenhum profile anterior encontrado" -ForegroundColor Cyan
}
```

---

#### Passo 4: Criar diretório do profile (se não existir)

```powershell
# Criar diretório
$profileDir = Split-Path $PROFILE
New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
Write-Host "✅ Diretório do profile pronto" -ForegroundColor Green
```

---

#### Passo 5: Copiar profile

**Se usou Opção A:**
```powershell
Copy-Item .\powershell-profile.ps1 $PROFILE -Force
```

**Se usou Opção B:**
```powershell
Copy-Item $tempPath $PROFILE -Force
```

**Verificar:**
```powershell
Write-Host "✅ Profile copiado para: $PROFILE" -ForegroundColor Green
```

---

#### Passo 6: IMPORTANTE - Editar username WSL

**O que fazer:**
```powershell
# Abrir profile no Bloco de Notas
notepad $PROFILE
```

**O que procurar:**
Encontre a linha (por volta da linha 39):
```powershell
$wslUser = "cmr-auto"  # ← TROCAR ESTE VALOR!
```

**O que mudar:**
1. No WSL Ubuntu, execute:
   ```bash
   whoami
   ```
   Exemplo de output: `pedro`

2. No Bloco de Notas, troque `"cmr-auto"` pelo seu username:
   ```powershell
   $wslUser = "pedro"  # ← Seu username aqui
   ```

3. Salve (Ctrl+S) e feche o Bloco de Notas

---

#### Passo 7: Configurar ExecutionPolicy

**O que vamos fazer:**
Permitir que o PowerShell execute scripts locais.

```powershell
# Configurar política de execução
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**O que esperar:**
```
Execution Policy Change
The execution policy helps protect you from scripts that you do not trust...
Do you want to change the execution policy?
[Y] Yes  [A] Yes to All  [N] No  [L] No to All  [S] Suspend  [?] Help (default is "N"):
```

**O que fazer:**
Digite `Y` e pressione Enter.

---

#### Passo 8: Recarregar profile

```powershell
# Recarregar profile (aplicar mudanças)
. $PROFILE
```

**O que esperar:**
Mensagens de inicialização do profile (se houver).

---

#### Passo 9: Testar comandos

```powershell
# Verificar se aliases foram criados
Get-Alias scc
Get-Alias gcp
Get-Alias gsync
```

**O que esperar:**
```
CommandType     Name                                               Version    Source
-----------     ----                                               -------    ------
Alias           scc -> Start-Claude
Alias           gcp -> Enter-ClaudeProject
Alias           gsync -> Sync-Git
```

**✅ Validação:**
Todos os 3 aliases aparecem? Perfeito!

---

#### Passo 10: Testar funcionalidade

```powershell
# Testar comando cstatus
cstatus
```

**O que esperar:**
Informações sobre Claude Code, Node.js, Git, etc.

**✅ Validação:**
Comando executa sem erros? Excelente!

**💡 Como usar os comandos:**

```powershell
# Iniciar Claude Code no projeto
scc

# Abrir bash WSL no projeto
gcp

# Sincronizar Git (pull + status)
gsync

# Verificar status do ambiente
cstatus

# Executar Claude Code com argumentos
claude --help
```

---

### 5.3 Validação Completa do Sistema

**Vamos fazer uma validação completa de TUDO que instalamos:**

#### Checklist Completo (execute no Ubuntu)

```bash
cd ~/claude-work/repos/Claude-Code-Projetos

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  VALIDAÇÃO COMPLETA - SETUP WSL PC TRABALHO              ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. Estrutura
echo "1️⃣  Estrutura de Diretórios:"
pwd
echo "   ✅ Localização correta"
echo ""

# 2. Git
echo "2️⃣  Git:"
git --version
git config --global user.name
git config --global user.email
git status | head -1
echo "   ✅ Git configurado"
echo ""

# 3. Node.js
echo "3️⃣  Node.js:"
node --version
npm --version
echo "   ✅ Node.js instalado"
echo ""

# 4. Claude Code
echo "4️⃣  Claude Code:"
claude --version
echo "   ✅ Claude Code instalado"
echo ""

# 5. Python
echo "5️⃣  Python:"
python3 --version
echo "   ✅ Python instalado"
echo ""

# 6. Venvs
echo "6️⃣  Virtual Environments:"
venv_count=$(ls agentes/*/.venv -d 2>/dev/null | wc -l)
echo "   Encontrados: $venv_count venvs"
if [ $venv_count -eq 5 ]; then
    echo "   ✅ Todos os 5 venvs criados"
else
    echo "   ⚠️  Esperado: 5, Encontrado: $venv_count"
fi
echo ""

# 7. npm packages
echo "7️⃣  npm packages (MCP Server):"
npm_count=$(ls mcp-servers/djen-mcp-server/node_modules/ 2>/dev/null | wc -l)
echo "   Instalados: $npm_count packages"
if [ $npm_count -gt 300 ]; then
    echo "   ✅ npm packages instalados (~340)"
else
    echo "   ⚠️  Esperado: ~340, Encontrado: $npm_count"
fi
echo ""

# 8. Hooks
echo "8️⃣  Hooks JavaScript:"
if node .claude/hooks/invoke-legal-braniac-hybrid.js > /dev/null 2>&1; then
    echo "   ✅ invoke-legal-braniac-hybrid.js: OK"
else
    echo "   ❌ invoke-legal-braniac-hybrid.js: ERRO"
fi

if node .claude/hooks/session-context-hybrid.js > /dev/null 2>&1; then
    echo "   ✅ session-context-hybrid.js: OK"
else
    echo "   ❌ session-context-hybrid.js: ERRO"
fi
echo ""

# 9. Ferramentas essenciais
echo "9️⃣  Ferramentas Essenciais:"
command -v git > /dev/null && echo "   ✅ git"
command -v vim > /dev/null && echo "   ✅ vim"
command -v htop > /dev/null && echo "   ✅ htop"
command -v tree > /dev/null && echo "   ✅ tree"
command -v rg > /dev/null && echo "   ✅ ripgrep"
command -v jq > /dev/null && echo "   ✅ jq"
echo ""

# 10. SSH GitHub
echo "🔟 Conexão SSH GitHub:"
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    echo "   ✅ Autenticado com sucesso"
else
    echo "   ⚠️  Não autenticado (configure SSH se necessário)"
fi
echo ""

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  VALIDAÇÃO CONCLUÍDA                                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
```

**✅ Validação Final:**
Todos os itens marcados com ✅? **PARABÉNS! Setup completo!**

---

### 5.4 Primeiros Passos

**Agora que tudo está configurado, veja como usar no dia a dia:**

---

#### Como iniciar Claude Code

**Opção 1: Via PowerShell (Windows) - se instalou profile**
```powershell
# PowerShell
scc
```

**Opção 2: Via WSL Ubuntu**
```bash
# Abrir WSL
wsl

# Navegar para projeto
cd ~/claude-work/repos/Claude-Code-Projetos

# Iniciar Claude Code
claude
```

---

#### Workflow básico de desenvolvimento

**Cenário: Trabalhar no agente oab-watcher**

```bash
# 1. Abrir WSL
wsl

# 2. Navegar para o agente
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/oab-watcher

# 3. Ativar venv
source .venv/bin/activate

# 4. Trabalhar no código
# ... editar arquivos, executar scripts, etc ...

# 5. Executar script
python main.py

# 6. Quando terminar, desativar venv
deactivate
```

---

#### Git Sync entre PC Trabalho e PC Casa

**Fim do dia no PC Trabalho:**
```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Ver mudanças
git status

# Adicionar tudo
git add .

# Commit
git commit -m "feat: implementa funcionalidade X"

# Enviar para GitHub
git push
```

**Manhã seguinte no PC Casa:**
```bash
cd ~/claude-work/repos/Claude-Code-Projetos

# Baixar mudanças
git pull

# Continuar trabalhando...
```

**⚠️ IMPORTANTE:**
- ✅ **Sincroniza:** Código (.py), configs (.json), docs (.md), requirements.txt, package.json
- ❌ **NÃO sincroniza:** .venv/, node_modules/, logs, outputs, cache

**Regra de ouro:**
Se você mudou `requirements.txt` ou `package.json`, **recrie os ambientes na outra máquina**:

```bash
# Para Python venv:
cd agentes/nome-do-agente
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Para npm packages:
cd mcp-servers/djen-mcp-server
rm -rf node_modules
npm install
```

---

#### Comandos úteis para o dia a dia

```bash
# Verificar qual branch você está
git branch

# Ver diferenças não commitadas
git diff

# Ver histórico de commits
git log --oneline -10

# Listar todos os venvs
ls agentes/*/.venv -d

# Verificar espaço usado pelo WSL
du -sh ~/claude-work

# Listar processos Python rodando
ps aux | grep python

# Verificar uso de memória
free -h

# Ver estrutura do projeto
tree -L 2 ~/claude-work/repos/Claude-Code-Projetos
```

---

## 🔧 Troubleshooting Detalhado

### Problema 1: WSL não inicia após instalação

**Sintomas:**
- Comando `wsl` trava
- Erro "O subsistema do Windows para Linux não foi iniciado"
- Tela preta ao abrir Ubuntu

**Diagnóstico passo a passo:**

```powershell
# PowerShell como Admin

# Passo 1: Verificar status
wsl --status

# Passo 2: Verificar distribuições instaladas
wsl --list --verbose

# Passo 3: Verificar se WSL2 é padrão
wsl --set-default-version 2
```

**Soluções:**

**Solução 1: Reiniciar WSL**
```powershell
wsl --shutdown
Start-Sleep -Seconds 10
wsl
```

**Solução 2: Atualizar WSL**
```powershell
wsl --update
wsl --shutdown
wsl
```

**Solução 3: Reparar Ubuntu**
```powershell
# Desregistrar (⚠️ APAGA TUDO!)
wsl --unregister Ubuntu-24.04

# Reinstalar
wsl --install -d Ubuntu-24.04
```

---

### Problema 2: Hooks JavaScript não executam

**Sintomas:**
- Erro "node: command not found"
- Erro "Cannot find module"
- JSON inválido ou vazio

**Diagnóstico:**

```bash
# Verificar Node.js
which node
node --version

# Verificar permissões dos hooks
ls -la .claude/hooks/*.js

# Testar hook manualmente
node .claude/hooks/invoke-legal-braniac-hybrid.js
```

**Soluções:**

**Solução 1: Node.js não encontrado**
```bash
# Verificar se nvm está ativo
nvm --version

# Se não estiver, adicionar ao .bashrc
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc
echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc
source ~/.bashrc

# Ativar Node.js
nvm use 24
```

**Solução 2: Dependências faltando**
```bash
cd .claude/hooks

# Verificar se package.json existe
ls -la package.json

# Se existir, instalar dependências
npm install

# Testar novamente
cd ~/claude-work/repos/Claude-Code-Projetos
node .claude/hooks/invoke-legal-braniac-hybrid.js
```

---

### Problema 3: venv não ativa

**Sintomas:**
- Comando `source .venv/bin/activate` não muda o prompt
- `pip install` instala no sistema global
- Erro "No module named..."

**Diagnóstico:**

```bash
# Verificar se venv existe
ls -la .venv/

# Verificar se venv está corrompido
file .venv/bin/activate

# Verificar Python usado
which python3
```

**Soluções:**

**Solução 1: Recriar venv**
```bash
# Remover venv corrompido
cd agentes/nome-do-agente
rm -rf .venv

# Recriar
python3 -m venv .venv

# Ativar
source .venv/bin/activate

# Verificar se ativou (deve mostrar (.venv) no prompt)
# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt
```

**Solução 2: Verificar Python**
```bash
# Ver versão do Python
python3 --version

# Se não tiver python3-venv:
sudo apt install python3-venv
```

---

### Problema 4: Git pede senha constantemente

**Sintomas:**
- `git push` pede senha sempre
- "Permission denied (publickey)"
- SSH não funciona

**Diagnóstico:**

```bash
# Verificar se chave SSH existe
ls -la ~/.ssh/id_ed25519*

# Testar conexão SSH
ssh -T git@github.com

# Ver chaves no ssh-agent
ssh-add -l
```

**Soluções:**

**Solução 1: Reconfigurar SSH**
```bash
# Gerar nova chave (se não existir)
ssh-keygen -t ed25519 -C "seu.email@exemplo.com" -f ~/.ssh/id_ed25519

# Iniciar ssh-agent
eval "$(ssh-agent -s)"

# Adicionar chave
ssh-add ~/.ssh/id_ed25519

# Copiar chave pública
cat ~/.ssh/id_ed25519.pub

# Adicionar no GitHub: https://github.com/settings/keys
```

**Solução 2: Usar credential helper (menos seguro)**
```bash
# Configurar Git para armazenar credenciais
git config --global credential.helper store

# No próximo push, digite username/password
# Git vai salvar e não pedir mais
```

---

### Problema 5: WSL extremamente lento

**Sintomas:**
- Comandos demoram muito
- Windows Defender consumindo CPU
- Uso de memória alto

**Diagnóstico:**

```powershell
# PowerShell

# Verificar .wslconfig
notepad $env:USERPROFILE\.wslconfig

# Verificar exclusões do Defender
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath | Where-Object { $_ -like "*Ubuntu*" }

# Ver uso de recursos do WSL
wsl bash -c "free -h"
wsl bash -c "top -bn1 | head -20"
```

**Soluções:**

**Solução 1: Configurar .wslconfig**
```powershell
# Editar .wslconfig
notepad $env:USERPROFILE\.wslconfig

# Adicionar/ajustar:
# [wsl2]
# memory=4GB
# processors=2

# Reiniciar WSL
wsl --shutdown
Start-Sleep -Seconds 10
wsl
```

**Solução 2: Adicionar exclusão Defender**
```powershell
# PowerShell como Admin

# Encontrar path Ubuntu
$ubuntuPath = Get-ChildItem "$env:USERPROFILE\AppData\Local\Packages\" -Directory |
    Where-Object { $_.Name -like "CanonicalGroupLimited.Ubuntu24.04LTS_*" } |
    Select-Object -First 1 -ExpandProperty FullName

# Adicionar exclusão
Add-MpPreference -ExclusionPath $ubuntuPath

# Verificar
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
```

---

### Problema 6: npm install falha com EACCES

**Sintomas:**
- Erro "EACCES: permission denied"
- npm install requer sudo (NÃO DEVE!)
- Pacotes globais não funcionam

**Causa:**
Node.js instalado via apt (sistema), não via nvm.

**Solução:**

```bash
# Remover Node.js do sistema
sudo apt remove nodejs npm

# Instalar via nvm (correto)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 24
nvm use 24

# Reinstalar Claude Code
npm install -g @anthropic-ai/claude-code

# Testar
claude --version
```

---

### Problema 7: "nul" files aparecem no Git

**Sintomas:**
- Arquivos chamados `nul` em diretórios
- `git status` mostra `nul` como untracked

**Causa:**
Confusão entre comandos Linux (`/dev/null`) e Windows (`nul`).

**Solução:**

```bash
# Encontrar todos os arquivos "nul"
find . -name "nul" -type f

# Remover todos
find . -name "nul" -type f -delete

# OU remover manualmente
rm agentes/*/nul

# Verificar git status
git status
```

**Prevenção:**
Use redirecionamentos corretos no Linux:
```bash
# ✅ Correto (Linux)
comando > /dev/null 2>&1

# ❌ Errado (cria arquivo "nul")
comando > nul 2>&1
```

---

## 📚 Referências

### Documentos do Projeto

- **README.md** - Visão geral do projeto e instruções básicas
- **CLAUDE.md** - Regras arquiteturais e decisões críticas
- **WSL_SETUP.md** - Guia completo de setup WSL (validado no PC casa)
- **DISASTER_HISTORY.md** - Histórico de erros arquiteturais (lições aprendidas)
- **CHANGELOG.md** - Histórico de mudanças (Sprint 1-2)
- **docs/plano-migracao-wsl2.md** - Plano detalhado 6 sprints

### Links Externos

- **WSL Documentação:** https://docs.microsoft.com/windows/wsl/
- **Ubuntu 24.04 Release Notes:** https://releases.ubuntu.com/24.04/
- **nvm GitHub:** https://github.com/nvm-sh/nvm
- **Claude Code:** https://docs.anthropic.com/claude-code
- **GitHub SSH Keys:** https://docs.github.com/authentication/connecting-to-github-with-ssh

---

## ✅ Checklist Final de Validação

**Use este checklist para confirmar que TODO o setup está correto:**

### Infraestrutura Base
- [ ] Windows 10 build 19041+ ou Windows 11
- [ ] WSL2 instalado e funcionando
- [ ] Ubuntu 24.04 LTS instalado
- [ ] Arquivo `.wslconfig` configurado (4GB RAM, 2 CPUs)
- [ ] Windows Defender com exclusão para Ubuntu

### Ferramentas de Desenvolvimento
- [ ] Git instalado e configurado (nome, email)
- [ ] SSH keys configuradas e funcionando no GitHub
- [ ] Node.js v24+ instalado via nvm
- [ ] npm v11+ disponível
- [ ] Claude Code 2.0.42+ instalado e autenticado
- [ ] Python 3.12+ disponível
- [ ] Ferramentas essenciais instaladas (vim, htop, ripgrep, jq, etc)

### Projeto
- [ ] Estrutura `~/claude-work/repos/Claude-Code-Projetos` criada
- [ ] Repositório clonado via Git
- [ ] Git status limpo (working tree clean)
- [ ] 5 virtual environments Python criados:
  - [ ] agentes/djen-tracker/.venv
  - [ ] agentes/legal-articles-finder/.venv
  - [ ] agentes/legal-lens/.venv
  - [ ] agentes/legal-rag/.venv
  - [ ] agentes/oab-watcher/.venv
- [ ] Dependências npm instaladas (~340 packages em djen-mcp-server)

### Hooks e Configurações
- [ ] Hook `invoke-legal-braniac-hybrid.js` funciona
- [ ] Hook `session-context-hybrid.js` funciona
- [ ] Hooks retornam JSON válido
- [ ] PowerShell profile instalado (opcional)

### Testes Funcionais
- [ ] `wsl` abre Ubuntu sem erros
- [ ] `claude --version` funciona
- [ ] `git push/pull` funciona sem pedir senha
- [ ] `source .venv/bin/activate` muda prompt
- [ ] `node .claude/hooks/*.js` retorna JSON válido

---

## 🎉 Parabéns!

**Se todos os itens do checklist estão marcados, você concluiu com sucesso a migração para WSL no PC do trabalho!**

### Próximos Passos

1. **Familiarize-se com o ambiente:**
   - Explore os diretórios do projeto
   - Leia o README.md
   - Execute alguns comandos básicos

2. **Teste o workflow:**
   - Faça uma pequena mudança em um arquivo
   - Commit e push para GitHub
   - Pull no PC de casa para validar sincronização

3. **Configure ferramentas adicionais (opcional):**
   - Editor de código favorito (VS Code, vim, etc)
   - Aliases personalizados no `.bashrc`
   - Temas de terminal

4. **Explore Claude Code:**
   - Execute `claude` e explore os comandos
   - Teste os agents configurados
   - Experimente com skills

### Suporte

**Se encontrar problemas:**
1. Consulte a seção **Troubleshooting** deste guia
2. Verifique **CLAUDE.md** para regras arquiteturais
3. Leia **DISASTER_HISTORY.md** para evitar erros conhecidos
4. Abra uma issue no GitHub se necessário

---

**Última atualização:** 2025-11-17
**Baseado em:** Setup validado PC casa (Sprint 1-2 completo)
**Tempo total de execução:** ~1h40min (seguindo este guia)
**Versão do guia:** 2.0 (Didático e Passo-a-Passo)

---

**Bom trabalho! 🚀**
