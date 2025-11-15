# Plano de Migração WSL2 - Claude Code + Automação Jurídica

Versão: 1.0
Data: 2025-01-15
Objetivo: Migração completa do ambiente de desenvolvimento para WSL2 com integração servidor corporativo

---

## Visão Geral

Migração estruturada em 6 sprints de 1 semana cada, totalizando 6 semanas de implementação.

Cada sprint é autocontido e entrega valor incremental, sem dependências críticas entre sprints.

Investimento total estimado: 32-48 horas distribuídas.

---

## SPRINT 1: Instalação e Configuração Base WSL2

Duração: 1 semana
Horas estimadas: 6-8h
Objetivo: Ambiente WSL2 funcional com Claude Code instalado

### Tarefas

**1.1 Instalação WSL2**

```powershell
# PowerShell como Administrador
wsl --install -d Ubuntu-24.04

# Reiniciar Windows
Restart-Computer

# Após reinício, configurar usuário/senha Ubuntu
# Username: [seu_usuario]
# Password: [senha_forte]
```

**1.2 Atualização Sistema Base**

```bash
# Dentro do WSL
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential curl wget git vim htop tree
```

**1.3 Instalação Node.js via nvm**

```bash
# Instalar nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Recarregar shell
source ~/.bashrc

# Instalar Node.js LTS
nvm install --lts
nvm alias default node

# Verificar
node --version
npm --version
```

**1.4 Configuração npm Global**

```bash
# Criar diretório global
mkdir -p ~/.npm-global

# Configurar npm
npm config set prefix ~/.npm-global

# Adicionar ao PATH
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verificar
npm config get prefix
```

**1.5 Instalação Claude Code**

```bash
# Instalar globalmente
npm install -g @anthropic-ai/claude-code

# Verificar instalação
claude --version

# Autenticação (primeira execução)
claude
# Seguir instruções para autenticar com API key Anthropic
```

**1.6 Configuração .wslconfig**

Windows: Criar `C:\Users\[Username]\.wslconfig`

```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
localhostForwarding=true
nestedVirtualization=false
```

```powershell
# PowerShell - reiniciar WSL
wsl --shutdown
# Aguardar 10 segundos
wsl
```

**1.7 Configuração Windows Defender**

```powershell
# PowerShell como Administrador
Add-MpPreference -ExclusionPath "$env:USERPROFILE\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu24.04LTS_79rhkp1fndgsc"

# Verificar
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
```

### Validação Sprint 1

```bash
# Executar todos os comandos sem erros
node --version        # v20.x.x
npm --version         # 10.x.x
claude --version      # Versão mais recente
which claude          # ~/.npm-global/bin/claude
```

### Entregável

Ambiente WSL2 configurado e Claude Code funcional.

---

## SPRINT 2: Migração de Código e Estrutura de Projeto

Duração: 1 semana
Horas estimadas: 6-8h
Objetivo: Código do projeto rodando em WSL2

### Tarefas

**2.1 Criação de Estrutura Base**

```bash
# Criar diretórios
mkdir -p ~/projects
mkdir -p ~/bin
mkdir -p ~/logs
mkdir -p ~/.claude
```

**2.2 Clonagem do Repositório**

```bash
cd ~/projects

# Se usar HTTPS
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git

# OU se usar SSH
git clone git@github.com:PedroGiudice/Claude-Code-Projetos.git

cd Claude-Code-Projetos
```

**2.3 Configuração Git**

```bash
git config --global user.name "Seu Nome"
git config --global user.email "seu@email.com"

# Verificar branch atual
git branch
git status
```

**2.4 Instalação Python e Dependências**

```bash
# Python já vem instalado no Ubuntu 24.04, mas garantir pip
sudo apt install -y python3-pip python3-venv python3-dev

# Verificar
python3 --version
pip3 --version
```

**2.5 Configuração de Virtual Environments por Agente**

```bash
cd ~/projects/Claude-Code-Projetos

# Para cada agente (exemplo: oab-watcher)
for agente in agentes/*/; do
    echo "Configurando $agente"
    cd "$agente"

    # Criar venv
    python3 -m venv .venv

    # Ativar
    source .venv/bin/activate

    # Atualizar pip
    pip install --upgrade pip

    # Instalar dependências
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
    fi

    # Desativar
    deactivate

    cd ../..
done
```

**2.6 Teste de Execução**

```bash
# Testar um agente
cd ~/projects/Claude-Code-Projetos/agentes/oab-watcher
source .venv/bin/activate

# Executar (não processar, apenas testar imports)
python -c "import sys; print(f'Python: {sys.version}'); import main; print('Imports OK')"

deactivate
```

**2.7 Atualização de Paths no Código**

Editar `shared/utils/path_utils.py`:

```python
import os
from pathlib import Path

def get_data_dir(agent_name: str, subdir: str = "") -> Path:
    """
    Retorna path para diretório de dados do agente.
    WSL-first, fallback para E:\ se necessário.
    """
    # Prioridade 1: WSL filesystem
    data_root_wsl = Path.home() / 'claude-code-data'

    if data_root_wsl.exists():
        agent_data = data_root_wsl / 'agentes' / agent_name
        return agent_data / subdir if subdir else agent_data

    # Fallback: E:\ via /mnt/e/
    data_root_e = Path('/mnt/e/claude-code-data')
    agent_data = data_root_e / 'agentes' / agent_name
    return agent_data / subdir if subdir else agent_data
```

### Validação Sprint 2

```bash
# Todos os agentes devem ter venv configurado
cd ~/projects/Claude-Code-Projetos/agentes/oab-watcher
ls -la .venv  # Deve existir

# Código deve executar sem erros de import
source .venv/bin/activate
python -c "from shared.utils.path_utils import get_data_dir; print(get_data_dir('oab-watcher'))"
deactivate
```

### Entregável

Código do projeto funcionando em WSL2 com todos os venvs configurados.

---

## SPRINT 3: Integração com Servidor Corporativo

Duração: 1 semana
Horas estimadas: 8-10h
Objetivo: Servidor montado e acessível via WSL2

### Tarefas

**3.1 Instalação CIFS Utils**

```bash
sudo apt install -y cifs-utils
```

**3.2 Criação de Credentials File**

```bash
# Criar arquivo de credenciais (seguro)
sudo nano /root/.smbcredentials

# Conteúdo (ajustar conforme necessário):
username=[seu_usuario_rede]
password=[sua_senha_rede]
domain=[DOMINIO_ESCRITORIO]

# Proteger arquivo
sudo chmod 600 /root/.smbcredentials
```

**3.3 Criação de Mount Point**

```bash
sudo mkdir -p /mnt/servidor
```

**3.4 Configuração fstab**

```bash
sudo nano /etc/fstab

# Adicionar linha (ajustar [servidor] e [caminho]):
//[servidor]/documentos-juridicos /mnt/servidor cifs credentials=/root/.smbcredentials,uid=1000,gid=1000,file_mode=0644,dir_mode=0755,iocharset=utf8,_netdev 0 0
```

Nota: Substituir `[servidor]` pelo nome/IP do servidor e ajustar caminho conforme estrutura real.

**3.5 Montagem Inicial**

```bash
# Montar
sudo mount -a

# Verificar
ls /mnt/servidor
df -h | grep servidor
```

**3.6 Teste de Acesso**

```bash
# Listar conteúdo
ls -lah /mnt/servidor/processos/

# Testar leitura de arquivo
if [ -f /mnt/servidor/processos/*.pdf ]; then
    head -c 1024 /mnt/servidor/processos/*.pdf | wc -c
    echo "Leitura OK"
fi
```

**3.7 Benchmark de Performance**

```bash
# Criar script de benchmark
cat > ~/bin/benchmark-servidor.sh << 'EOF'
#!/bin/bash

echo "Benchmark de leitura - Servidor"

# Encontrar PDF de teste
TEST_PDF=$(find /mnt/servidor -name "*.pdf" -type f | head -1)

if [ -z "$TEST_PDF" ]; then
    echo "Nenhum PDF encontrado para teste"
    exit 1
fi

echo "Arquivo de teste: $TEST_PDF"
echo "Tamanho: $(du -h "$TEST_PDF" | cut -f1)"

# Benchmark leitura
echo "Testando leitura..."
time cat "$TEST_PDF" > /dev/null

echo "Teste completo"
EOF

chmod +x ~/bin/benchmark-servidor.sh

# Executar
~/bin/benchmark-servidor.sh
```

### Validação Sprint 3

```bash
# Servidor deve estar montado
mount | grep servidor

# Deve listar arquivos
ls /mnt/servidor

# Leitura deve funcionar (tempo depende da rede)
time cat /mnt/servidor/processos/[algum_arquivo].pdf > /dev/null
```

### Entregável

Servidor corporativo montado e acessível via /mnt/servidor com performance quantificada.

---

## SPRINT 4: Estrutura de Cache e Sincronização

Duração: 1 semana
Horas estimadas: 6-8h
Objetivo: Sistema de cache híbrido funcional

### Tarefas

**4.1 Criação de Estrutura de Dados WSL**

```bash
# Criar diretórios
mkdir -p ~/claude-code-data/{inbox,processing,outputs,cache}
mkdir -p ~/documentos-juridicos-cache/{processos-ativos,temp-processing}
```

**4.2 Script de Sincronização Servidor -> Cache**

```bash
cat > ~/bin/sync-servidor.sh << 'EOF'
#!/bin/bash

SERVIDOR="/mnt/servidor/documentos-juridicos"
CACHE="$HOME/documentos-juridicos-cache/processos-ativos"
LOG="$HOME/logs/sync-servidor.log"

# Criar diretórios se não existirem
mkdir -p "$CACHE"
mkdir -p "$(dirname "$LOG")"

# Log início
echo "[$(date)] Iniciando sincronização servidor -> cache" >> "$LOG"

# Sincronização incremental (apenas anos recentes)
rsync -avz --delete \
  --include='processos/2024/***' \
  --include='processos/2025/***' \
  --include='processos/2026/***' \
  --exclude='processos/*' \
  --exclude='*.tmp' \
  --exclude='*.bak' \
  "$SERVIDOR/" "$CACHE/" >> "$LOG" 2>&1

# Log resultado
if [ $? -eq 0 ]; then
    echo "[$(date)] Sincronização completa - Sucesso" >> "$LOG"
else
    echo "[$(date)] Sincronização completa - Erro $?" >> "$LOG"
fi
EOF

chmod +x ~/bin/sync-servidor.sh
```

**4.3 Script de Sincronização Cache -> Servidor (Outputs)**

```bash
cat > ~/bin/sync-outputs.sh << 'EOF'
#!/bin/bash

OUTPUTS_WSL="$HOME/claude-code-data/outputs"
OUTPUTS_SERVIDOR="/mnt/servidor/outputs-extrator"
LOG="$HOME/logs/sync-outputs.log"

# Criar diretórios
mkdir -p "$OUTPUTS_SERVIDOR"
mkdir -p "$(dirname "$LOG")"

# Log início
echo "[$(date)] Iniciando sincronização outputs -> servidor" >> "$LOG"

# Sincronização unidirecional (WSL -> Servidor)
rsync -avz \
  --exclude='*.tmp' \
  --exclude='.git/' \
  "$OUTPUTS_WSL/" "$OUTPUTS_SERVIDOR/" >> "$LOG" 2>&1

# Log resultado
if [ $? -eq 0 ]; then
    echo "[$(date)] Sincronização outputs completa - Sucesso" >> "$LOG"
else
    echo "[$(date)] Sincronização outputs completa - Erro $?" >> "$LOG"
fi
EOF

chmod +x ~/bin/sync-outputs.sh
```

**4.4 Script Bidirectional (Combinado)**

```bash
cat > ~/bin/sync-bidirectional.sh << 'EOF'
#!/bin/bash

echo "Sincronização bidirectional iniciando..."

# Servidor -> Cache
echo "1/2: Sincronizando servidor -> cache..."
~/bin/sync-servidor.sh

# Outputs -> Servidor
echo "2/2: Sincronizando outputs -> servidor..."
~/bin/sync-outputs.sh

echo "Sincronização bidirectional completa"
EOF

chmod +x ~/bin/sync-bidirectional.sh
```

**4.5 Execução Inicial**

```bash
# Primeira sincronização (pode demorar)
~/bin/sync-bidirectional.sh

# Verificar logs
tail -n 50 ~/logs/sync-servidor.log
tail -n 50 ~/logs/sync-outputs.log
```

**4.6 Agendamento via Cron**

```bash
# Editar crontab
crontab -e

# Adicionar linhas:
# Sincronização a cada 2 horas durante expediente (8h-18h, segunda a sexta)
0 8-18/2 * * 1-5 /home/user/bin/sync-bidirectional.sh >> /home/user/logs/cron-sync.log 2>&1

# Sincronização outputs a cada hora (mais frequente)
0 * * * * /home/user/bin/sync-outputs.sh >> /home/user/logs/cron-outputs.log 2>&1
```

**4.7 Teste de Sincronização**

```bash
# Criar arquivo de teste em outputs
echo "Teste de sincronização" > ~/claude-code-data/outputs/teste.txt

# Executar sincronização
~/bin/sync-outputs.sh

# Verificar no servidor
ls -lah /mnt/servidor/outputs-extrator/teste.txt

# Limpar
rm ~/claude-code-data/outputs/teste.txt
rm /mnt/servidor/outputs-extrator/teste.txt
```

### Validação Sprint 4

```bash
# Cache deve ter sido populado
ls ~/documentos-juridicos-cache/processos-ativos/processos/

# Cron deve estar configurado
crontab -l | grep sync

# Logs devem existir e mostrar sucesso
tail ~/logs/sync-servidor.log
```

### Entregável

Sistema de cache híbrido com sincronização automática bidirecional.

---

## SPRINT 5: Adaptação de Código e Workflows

Duração: 1 semana
Horas estimadas: 8-10h
Objetivo: Código adaptado para usar cache híbrido

### Tarefas

**5.1 Atualização path_utils.py**

Editar `shared/utils/path_utils.py`:

```python
import os
from pathlib import Path
import shutil

# Configuração global
SERVIDOR = Path('/mnt/servidor/documentos-juridicos')
CACHE = Path.home() / 'documentos-juridicos-cache/processos-ativos'
TEMP = Path.home() / 'documentos-juridicos-cache/temp-processing'
OUTPUTS = Path.home() / 'claude-code-data/outputs'

def get_documento_juridico(filename: str, use_cache: bool = True) -> Path:
    """
    Busca documento jurídico com estratégia cache-first.

    Args:
        filename: Nome do arquivo (ex: '12345.pdf')
        use_cache: Se True, tenta cache primeiro

    Returns:
        Path para arquivo (em cache ou temp)
    """
    if use_cache:
        # Tentar cache primeiro
        pdf_cache = CACHE / 'processos' / filename

        if pdf_cache.exists():
            # Verificar se está atualizado
            pdf_servidor = SERVIDOR / 'processos' / filename

            if pdf_servidor.exists():
                if pdf_cache.stat().st_mtime >= pdf_servidor.stat().st_mtime:
                    # Cache atualizado
                    return pdf_cache
                else:
                    # Atualizar cache
                    shutil.copy(pdf_servidor, pdf_cache)
                    return pdf_cache
            else:
                # Arquivo só existe em cache (ok)
                return pdf_cache

    # Cache miss ou use_cache=False: buscar do servidor
    pdf_servidor = SERVIDOR / 'processos' / filename

    if not pdf_servidor.exists():
        raise FileNotFoundError(f"Documento {filename} não encontrado")

    # Copiar para temp
    TEMP.mkdir(parents=True, exist_ok=True)
    pdf_temp = TEMP / filename
    shutil.copy(pdf_servidor, pdf_temp)

    return pdf_temp

def get_output_path(agent_name: str, subdir: str = "") -> Path:
    """Retorna path para outputs (sempre em WSL)"""
    agent_output = OUTPUTS / agent_name
    return agent_output / subdir if subdir else agent_output

def cleanup_temp():
    """Limpa arquivos temporários"""
    if TEMP.exists():
        for f in TEMP.glob('*'):
            f.unlink()
```

**5.2 Adaptação de Agente (exemplo: oab-watcher)**

Editar `agentes/oab-watcher/main.py`:

```python
from shared.utils.path_utils import get_documento_juridico, get_output_path, cleanup_temp
from pathlib import Path

def processar_processo(numero_processo):
    """Pipeline adaptado para cache híbrido"""

    # 1. Obter documento (cache-first)
    pdf_path = get_documento_juridico(f'{numero_processo}.pdf')
    print(f"Processando: {pdf_path}")

    # 2. Processar (OCR, extração - tudo local, rápido)
    texto = extrair_texto_ocr(pdf_path)
    estrutura = parse_estrutura(texto)
    yaml_output = gerar_yaml_tags(estrutura)

    # 3. Salvar output (WSL)
    output_path = get_output_path('oab-watcher', 'autos-estruturados')
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / f'{numero_processo}.yaml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(yaml_output)

    print(f"Output salvo: {output_file}")

    # 4. Limpeza (se era temp)
    if pdf_path.parent.name == 'temp-processing':
        pdf_path.unlink()

    return output_file

# Processar lote
if __name__ == '__main__':
    processos = ['12345', '12346', '12347']

    for proc in processos:
        try:
            processar_processo(proc)
        except Exception as e:
            print(f"Erro ao processar {proc}: {e}")

    # Limpeza final
    cleanup_temp()
```

**5.3 Teste de Workflow Completo**

```bash
cd ~/projects/Claude-Code-Projetos/agentes/oab-watcher
source .venv/bin/activate

# Executar teste (usar processo real do servidor)
python main.py

# Verificar output
ls ~/claude-code-data/outputs/oab-watcher/autos-estruturados/

# Aguardar sync automático (ou forçar)
~/bin/sync-outputs.sh

# Verificar no servidor
ls /mnt/servidor/outputs-extrator/oab-watcher/autos-estruturados/

deactivate
```

**5.4 Adaptação de Outros Agentes**

Repetir processo de adaptação para:
- agentes/djen-tracker/
- agentes/legal-lens/
- Outros agentes existentes

**5.5 Benchmark de Performance**

```bash
cat > ~/bin/benchmark-pipeline.sh << 'EOF'
#!/bin/bash

cd ~/projects/Claude-Code-Projetos/agentes/oab-watcher
source .venv/bin/activate

echo "Benchmark: Pipeline completo"
echo "Processando 10 documentos de teste..."

time python -c "
from main import processar_processo
import sys

processos = ['12345', '12346', '12347', '12348', '12349', '12350', '12351', '12352', '12353', '12354']

for proc in processos:
    try:
        processar_processo(proc)
        print(f'[OK] {proc}')
    except Exception as e:
        print(f'[ERRO] {proc}: {e}', file=sys.stderr)
"

deactivate
EOF

chmod +x ~/bin/benchmark-pipeline.sh

# Executar
~/bin/benchmark-pipeline.sh
```

### Validação Sprint 5

```bash
# Código deve executar sem erros
cd ~/projects/Claude-Code-Projetos/agentes/oab-watcher
source .venv/bin/activate
python main.py
deactivate

# Outputs devem ser gerados em WSL
ls ~/claude-code-data/outputs/

# Outputs devem ser sincronizados para servidor
ls /mnt/servidor/outputs-extrator/
```

### Entregável

Código de todos os agentes adaptado e funcionando com cache híbrido.

---

## SPRINT 6: Infraestrutura Claude Code e Finalização

Duração: 1 semana
Horas estimadas: 6-8h
Objetivo: Infraestrutura .claude/ versionada e documentação atualizada

### Tarefas

**6.1 Criação de Estrutura .claude/**

```bash
cd ~/projects/Claude-Code-Projetos

mkdir -p .claude/{agents,skills,hooks,dev-docs,mcp}
```

**6.2 Movimentação de Skills Existentes**

```bash
# Se houver skills/ na raiz
if [ -d skills ]; then
    mv skills/* .claude/skills/
    rmdir skills
fi

# Criar .gitignore dentro de .claude/
cat > .claude/.gitignore << 'EOF'
# Logs e caches locais
*.log
.cache/
temp/

# Não versionar dados sensíveis
.env
credentials.*
EOF
```

**6.3 Criação de Agentes Especializados**

```bash
# Agent: code-reviewer
cat > .claude/agents/code-reviewer.md << 'EOF'
---
name: code-reviewer
description: Expert code reviewer for Python projects. Use PROACTIVELY after writing code.
tools: Read, Grep, Glob, Bash
color: Yellow
model: opus
---

You are a senior code reviewer specializing in Python for legal automation.

Review code for:
1. Python best practices (PEP 8, type hints)
2. Security vulnerabilities (injection, path traversal)
3. Performance issues (I/O bottlenecks, memory leaks)
4. Documentation completeness (docstrings, comments)
5. Error handling (try/except, logging)

Focus on:
- Legal document processing pipelines
- OCR and text extraction reliability
- YAML generation correctness
- Cache consistency

Provide actionable feedback with specific line references.
EOF

# Agent: refactoring-agent
cat > .claude/agents/refactoring-agent.md << 'EOF'
---
name: refactoring-agent
description: Refactoring specialist. Use when code needs restructuring.
tools: Read, Edit, Grep, Glob
color: Blue
model: sonnet
---

You are a refactoring specialist for Python legal automation projects.

Refactor code to:
1. Improve modularity (single responsibility)
2. Reduce duplication (DRY principle)
3. Enhance readability (clear naming, structure)
4. Optimize performance (cache usage, I/O reduction)

Maintain:
- Backward compatibility
- Existing tests (or update them)
- Documentation (update docstrings)

Always explain why refactoring improves the code.
EOF
```

**6.4 Criação de Skills**

```bash
# Skill: legal-document-processing
cat > .claude/skills/legal-document-processing.md << 'EOF'
---
name: legal-document-processing
description: Best practices for processing legal documents (PDFs, DOC)
activates_when:
  - Processing PDF files
  - Extracting text from legal documents
  - OCR operations
  - YAML tagging of legal content
---

When processing legal documents, follow this workflow:

1. Document Acquisition
   - Use cache-first strategy (get_documento_juridico)
   - Verify file integrity (check file size, magic bytes)
   - Log source (servidor vs cache vs temp)

2. Text Extraction
   - Try native text extraction first (pdfplumber)
   - Fallback to OCR if native fails (Tesseract, high DPI)
   - Validate encoding (UTF-8, handle errors)
   - Preserve structure (pages, sections, metadata)

3. Structure Parsing
   - Identify document type (petição, sentença, despacho)
   - Extract entities (processo number, partes, data)
   - Parse sections (relatório, fundamentação, dispositivo)
   - Validate completeness (no missing sections)

4. YAML Generation
   - Use consistent schema (documented)
   - Include metadata (source, timestamp, version)
   - Tag sections with semantic labels
   - Validate YAML syntax before saving

5. Error Handling
   - Log all errors with context (file, line, operation)
   - Partial results are acceptable (mark as incomplete)
   - Retry transient failures (network, temporary files)
   - Never fail silently

6. Output Management
   - Save to WSL outputs (get_output_path)
   - Use descriptive filenames (processo_numero.yaml)
   - Clean temporary files after processing
   - Trigger sync to servidor (automatic via cron)

Performance considerations:
- Batch operations when possible
- Use temp directory for heavy I/O (OCR)
- Monitor memory usage (large PDFs)
- Cache intermediate results (parsed structures)
EOF
```

**6.5 Atualização CLAUDE.md**

Adicionar ao `CLAUDE.md`:

```markdown
## Arquitetura de Dados WSL2

### Estrutura de Camadas

CAMADA 1: Servidor Corporativo (Source of Truth)
- Mount point: /mnt/servidor/documentos-juridicos/
- Acesso: Leitura direta quando necessário
- Uso: Validação, fallback, documentos não cacheados

CAMADA 2: Cache WSL (Processos Ativos)
- Localização: ~/documentos-juridicos-cache/processos-ativos/
- Sincronização: Rsync a cada 2h (cron)
- Conteúdo: Processos 2024-2026

CAMADA 3: Temp Processing (Operações Pesadas)
- Localização: ~/documentos-juridicos-cache/temp-processing/
- Uso: Copy-on-demand para OCR, parsing intensivo
- Limpeza: Automática após processamento

CAMADA 4: Outputs (Resultados Estruturados)
- Localização: ~/claude-code-data/outputs/
- Sincronização: Para /mnt/servidor/outputs-extrator/ a cada 1h
- Formato: YAML, JSON, relatórios

### Scripts de Sincronização

- sync-servidor.sh: Servidor -> Cache (documentos jurídicos)
- sync-outputs.sh: Outputs -> Servidor (resultados)
- sync-bidirectional.sh: Ambos (wrapper)

Agendamento via cron:
- Bidirectional: 8h, 10h, 12h, 14h, 16h, 18h (dias úteis)
- Outputs only: A cada hora

### Desenvolvimento

Sempre usar helper functions de shared/utils/path_utils.py:
- get_documento_juridico(filename): Cache-first com fallback
- get_output_path(agent_name, subdir): Outputs em WSL
- cleanup_temp(): Limpeza de arquivos temporários

NUNCA:
- Acessar /mnt/e/ diretamente (apenas para downloads DOU/DJEN)
- Duplicar lógica de cache (usar path_utils)
- Salvar outputs fora de ~/claude-code-data/outputs/
```

**6.6 Atualização README.md**

Adicionar seção sobre setup WSL:

```markdown
## Setup WSL2 (Recomendado)

Para desenvolvimento profissional com Claude Code, WSL2 é essencial.

### Instalação Rápida

```bash
# PowerShell como Admin
wsl --install -d Ubuntu-24.04

# Após configuração, executar:
cd ~/projects
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos

# Executar script de setup (se disponível)
./setup-python-wsl.sh
```

### Sincronização de Dados

Dados jurídicos sincronizam automaticamente:
- Servidor -> Cache: A cada 2h
- Outputs -> Servidor: A cada 1h

Para sincronização manual:
```bash
~/bin/sync-bidirectional.sh
```

### Performance

Processamento em WSL vs Windows:
- OCR: 8x mais rápido
- Parsing: 6x mais rápido
- Batch 100 docs: 2h30min -> 20min

Detalhes: `docs/wsl-pro-claude-code-analise-completa.md`
```

**6.7 Commit e Push de Mudanças**

```bash
cd ~/projects/Claude-Code-Projetos

# Adicionar mudanças
git add .claude/
git add shared/utils/path_utils.py
git add agentes/*/main.py
git add CLAUDE.md
git add README.md

# Commit
git commit -m "feat: adiciona infraestrutura WSL2 com cache híbrido

- Cria estrutura .claude/ (agents, skills, hooks)
- Implementa cache híbrido servidor-WSL
- Adapta path_utils para estratégia cache-first
- Atualiza agentes para usar cache
- Adiciona documentação WSL2

Performance: 6-8x melhoria em processamento batch"

# Push
git push origin [branch]
```

**6.8 Validação Completa**

```bash
# 1. Estrutura .claude/ versionada
ls -R .claude/

# 2. Código adaptado
cd agentes/oab-watcher
source .venv/bin/activate
python main.py
deactivate

# 3. Sincronização funcionando
~/bin/sync-bidirectional.sh
tail ~/logs/sync-servidor.log

# 4. Outputs no servidor
ls /mnt/servidor/outputs-extrator/

# 5. Claude Code reconhece infraestrutura
cd ~/projects/Claude-Code-Projetos
claude
# Comando: /agents
# Deve listar: code-reviewer, refactoring-agent
```

### Validação Sprint 6

Checklist final:

- [ ] Estrutura .claude/ criada e versionada
- [ ] Agentes especializados funcionando
- [ ] Skills carregando automaticamente
- [ ] CLAUDE.md atualizado com arquitetura WSL
- [ ] README.md atualizado com setup WSL
- [ ] Código commitado e pushed
- [ ] Documentação completa (wsl-pro-claude-code-analise-completa.md)

### Entregável

Projeto completamente migrado para WSL2 com infraestrutura Claude Code profissional.

---

## Pós-Migração: Monitoramento e Otimização

### Métricas a Acompanhar

**Performance:**
```bash
# Executar semanalmente
~/bin/benchmark-pipeline.sh >> ~/logs/performance-metrics.log
```

**Sincronização:**
```bash
# Verificar logs de sync
tail -n 100 ~/logs/sync-servidor.log | grep -E '(Erro|completa)'
```

**Uso de Espaço:**
```bash
# Verificar uso de disco
du -sh ~/documentos-juridicos-cache/
du -sh ~/claude-code-data/
df -h ~
```

### Otimizações Opcionais

**1. Compressão de Cache**

```bash
# Se cache crescer muito (>50GB), habilitar compressão rsync
# Editar ~/bin/sync-servidor.sh
# Adicionar flag --compress-level=6 ao rsync
```

**2. Limpeza Automática de Cache Antigo**

```bash
cat > ~/bin/cleanup-old-cache.sh << 'EOF'
#!/bin/bash
# Remove arquivos do cache não acessados em 30 dias
find ~/documentos-juridicos-cache/processos-ativos -type f -atime +30 -delete
EOF

chmod +x ~/bin/cleanup-old-cache.sh

# Agendar mensalmente
crontab -e
# Adicionar: 0 3 1 * * /home/user/bin/cleanup-old-cache.sh
```

**3. Monitoramento de Sincronização**

```bash
cat > ~/bin/monitor-sync.sh << 'EOF'
#!/bin/bash
# Alerta se sincronização não rodou nas últimas 3 horas

LAST_SYNC=$(stat -c %Y ~/logs/sync-servidor.log)
NOW=$(date +%s)
DIFF=$((NOW - LAST_SYNC))

if [ $DIFF -gt 10800 ]; then
    echo "ALERTA: Última sincronização há $((DIFF/3600))h" | mail -s "Sync WSL atrasado" seu@email.com
fi
EOF

chmod +x ~/bin/monitor-sync.sh

# Executar a cada hora
crontab -e
# Adicionar: 0 * * * * /home/user/bin/monitor-sync.sh
```

---

## Troubleshooting

### Problema: Servidor não monta no boot

Solução:
```bash
# Verificar mount
sudo mount -a

# Se falhar, verificar credenciais
sudo cat /root/.smbcredentials

# Verificar conectividade
ping [servidor]
smbclient -L //[servidor] -U [usuario]

# Remontar manualmente
sudo umount /mnt/servidor
sudo mount -a
```

### Problema: Rsync lento

Solução:
```bash
# Verificar rede
iperf3 -c [servidor]  # Se servidor suporta

# Reduzir verbosidade
# Editar ~/bin/sync-servidor.sh
# Trocar -avz por -az (remove verbose)

# Habilitar compressão
# Adicionar --compress-level=6
```

### Problema: Cache desatualizado

Solução:
```bash
# Forçar sincronização completa
~/bin/sync-servidor.sh

# Verificar cron está rodando
systemctl status cron
crontab -l

# Verificar logs
tail -n 50 ~/logs/sync-servidor.log
```

### Problema: Performance pior que esperado

Diagnóstico:
```bash
# Benchmark WSL vs /mnt/e/
time cat ~/documentos-juridicos-cache/processos-ativos/processos/[arquivo].pdf > /dev/null
time cat /mnt/e/claude-code-data/[arquivo].pdf > /dev/null

# Verificar exclusões Defender
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath  # PowerShell

# Verificar .wslconfig
cat /mnt/c/Users/[Username]/.wslconfig

# Reiniciar WSL
wsl --shutdown  # PowerShell
# Aguardar 10s
wsl
```

---

## Rollback (Se Necessário)

Se migração falhar ou houver problemas críticos:

```bash
# 1. Desmontar servidor
sudo umount /mnt/servidor

# 2. Desabilitar cron
crontab -e
# Comentar todas as linhas de sync

# 3. Reverter código
cd ~/projects/Claude-Code-Projetos
git log --oneline  # Identificar commit antes da migração
git reset --hard [commit_hash]

# 4. Continuar usando versão Windows (E:\)
# Código antigo acessa E:\ via path_utils original
```

Nota: Outputs gerados em WSL podem ser copiados manualmente para E:\ se necessário.

---

## Resumo de Entregáveis

Sprint 1: WSL2 + Claude Code instalado e configurado
Sprint 2: Código do projeto rodando em WSL
Sprint 3: Servidor corporativo integrado via SMB
Sprint 4: Sistema de cache com sincronização automática
Sprint 5: Código adaptado para cache híbrido
Sprint 6: Infraestrutura .claude/ e documentação completa

Total: Ambiente WSL2 profissional com performance 6-8x superior e infraestrutura Claude Code avançada.

---

Fim do Plano de Migração
