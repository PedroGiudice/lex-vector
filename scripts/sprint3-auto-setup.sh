#!/bin/bash
# Sprint 3 - Setup Automatizado PC Trabalho
# EXECUTAR NO PC TRABALHO (Windows + WSL2)
# Data: 2025-11-15

set -e  # Abortar em erro

echo "=========================================="
echo "SPRINT 3 - SETUP PC TRABALHO (AUTOMATIZADO)"
echo "=========================================="
echo ""

# Verificar se já está no WSL
if ! grep -q microsoft /proc/version; then
    echo "❌ ERRO: Este script deve rodar DENTRO do WSL2"
    echo "Execute: wsl"
    echo "Depois: cd ~/claude-work/repos/Claude-Code-Projetos && bash scripts/sprint3-auto-setup.sh"
    exit 1
fi

# Variáveis (AJUSTAR ANTES DE EXECUTAR)
SERVIDOR="SERVIDOR_OU_IP"  # Ex: FILESRV01 ou 192.168.1.100
SHARE="documentos-juridicos"
USUARIO_REDE=""  # Preencher: usuario da rede
DOMINIO=""       # Preencher: domínio corporativo

# Validar variáveis
if [ "$SERVIDOR" == "SERVIDOR_OU_IP" ] || [ -z "$USUARIO_REDE" ] || [ -z "$DOMINIO" ]; then
    echo "❌ ERRO: Ajuste as variáveis no topo do script antes de executar"
    echo ""
    echo "Editar:"
    echo "  nano ~/claude-work/repos/Claude-Code-Projetos/scripts/sprint3-auto-setup.sh"
    echo ""
    echo "Preencher:"
    echo "  SERVIDOR=\"[nome ou IP do servidor]"
    echo "  USUARIO_REDE=\"[seu usuario de rede]\""
    echo "  DOMINIO=\"[dominio da empresa]\""
    exit 1
fi

echo "Configuração:"
echo "  Servidor: //$SERVIDOR/$SHARE"
echo "  Usuário: $USUARIO_REDE@$DOMINIO"
echo ""
read -sp "Senha de $USUARIO_REDE: " SENHA_REDE
echo ""
echo ""

# ========== FASE 1: Validações ==========
echo "[1/7] Validando pré-requisitos..."

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não instalado. Execute primeiro:"
    echo "   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash"
    echo "   source ~/.bashrc"
    echo "   nvm install --lts"
    exit 1
fi

# Verificar Claude Code
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code não instalado. Execute:"
    echo "   npm install -g @anthropic-ai/claude-code"
    exit 1
fi

# Verificar estrutura do projeto
if [ ! -d ~/claude-work/repos/Claude-Code-Projetos ]; then
    echo "❌ Projeto não clonado. Execute:"
    echo "   mkdir -p ~/claude-work/repos"
    echo "   cd ~/claude-work/repos"
    echo "   git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git"
    exit 1
fi

cd ~/claude-work/repos/Claude-Code-Projetos

echo "✅ Pré-requisitos OK"
echo ""

# ========== FASE 2: Instalar CIFS Utils ==========
echo "[2/7] Instalando cifs-utils..."
sudo apt install -y cifs-utils > /dev/null 2>&1
echo "✅ cifs-utils instalado"
echo ""

# ========== FASE 3: Configurar Credentials ==========
echo "[3/7] Configurando credenciais SMB..."
sudo bash -c "cat > /root/.smbcredentials << EOF
username=$USUARIO_REDE
password=$SENHA_REDE
domain=$DOMINIO
EOF"
sudo chmod 600 /root/.smbcredentials
echo "✅ Credenciais configuradas (/root/.smbcredentials)"
echo ""

# ========== FASE 4: Criar Mount Point ==========
echo "[4/7] Criando mount point..."
sudo mkdir -p /mnt/servidor
echo "✅ Mount point criado (/mnt/servidor)"
echo ""

# ========== FASE 5: Testar Montagem Manual ==========
echo "[5/7] Testando montagem manual..."
echo "Montando //$SERVIDOR/$SHARE..."

if sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,noperm //$SERVIDOR/$SHARE /mnt/servidor 2>/dev/null; then
    echo "✅ Montagem bem-sucedida!"

    # Verificar conteúdo
    if [ $(ls /mnt/servidor 2>/dev/null | wc -l) -gt 0 ]; then
        echo "✅ Servidor contém arquivos:"
        ls -lh /mnt/servidor | head -5
    else
        echo "⚠️  AVISO: Servidor montado mas vazio. Verificar path do share."
    fi

    echo ""

    # Desmontar
    sudo umount /mnt/servidor
    echo "Servidor desmontado (temporário para testes)"
else
    echo "❌ FALHA na montagem"
    echo ""
    echo "Possíveis causas:"
    echo "  1. GPO corporativa bloqueia montagem CIFS"
    echo "  2. Credenciais incorretas"
    echo "  3. Servidor inacessível (ping $SERVIDOR?)"
    echo "  4. Share name incorreto (verificar \\\\$SERVIDOR\\$SHARE no Windows)"
    echo ""
    echo "Ver docs/SPRINT_3_ROADMAP.md - Seção 'Cenário Alternativo A'"
    exit 1
fi

echo ""

# ========== FASE 6: Configurar fstab (Montagem Persistente) ==========
echo "[6/7] Configurando fstab para auto-mount..."

FSTAB_LINE="//$SERVIDOR/$SHARE /mnt/servidor cifs credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,file_mode=0644,dir_mode=0755,iocharset=utf8,noperm,_netdev 0 0"

if ! grep -q "/mnt/servidor" /etc/fstab; then
    echo "$FSTAB_LINE" | sudo tee -a /etc/fstab > /dev/null
    echo "✅ fstab atualizado"
else
    echo "✅ fstab já configurado (pulando)"
fi

# Montar via fstab
sudo mount -a

if mount | grep -q "/mnt/servidor"; then
    echo "✅ Servidor montado via fstab"
else
    echo "⚠️  AVISO: fstab configurado mas montagem falhou"
    echo "Tentar manualmente: sudo mount -a"
fi

echo ""

# ========== FASE 7: Benchmark de Performance ==========
echo "[7/7] Executando benchmark de performance..."

mkdir -p ~/bin
mkdir -p ~/logs

cat > ~/bin/benchmark-servidor.sh << 'EOFSCRIPT'
#!/bin/bash

echo "=== Benchmark Servidor Corporativo ==="
echo ""

# Encontrar PDF médio para teste
MEDIUM_PDF=$(find /mnt/servidor -name "*.pdf" -type f -size +1M -size -5M 2>/dev/null | head -1)

if [ -z "$MEDIUM_PDF" ]; then
    echo "⚠️  SKIP: Nenhum PDF médio (1-5MB) encontrado para benchmark"
    echo "Servidor pode estar vazio ou sem PDFs neste range de tamanho"
    exit 0
fi

SIZE=$(du -h "$MEDIUM_PDF" | cut -f1)
echo "Arquivo de teste: $(basename "$MEDIUM_PDF") ($SIZE)"
echo ""

# Executar 3 leituras
TOTAL=0
for i in 1 2 3; do
    echo -n "  Leitura $i/3... "
    START=$(date +%s%N)
    cat "$MEDIUM_PDF" > /dev/null 2>&1
    END=$(date +%s%N)
    DURATION=$(( (END - START) / 1000000 ))  # ms
    TOTAL=$((TOTAL + DURATION))
    echo "${DURATION}ms"
done

AVG=$((TOTAL / 3))
echo ""
echo "Tempo médio de leitura: ${AVG}ms"
echo ""

# Threshold validation
if [ $AVG -gt 500 ]; then
    echo "❌ PROBLEMATICO: Performance ruim (>500ms)"
    echo "   → Sprint 4 (cache híbrido) é OBRIGATÓRIO"
elif [ $AVG -gt 200 ]; then
    echo "⚠️  ACEITAVEL: Performance OK mas cache recomendado (>200ms)"
    echo "   → Sprint 4 (cache híbrido) é RECOMENDADO"
elif [ $AVG -gt 100 ]; then
    echo "✅ BOM: Performance boa (100-200ms)"
    echo "   → Sprint 4 (cache) é opcional"
else
    echo "✅ EXCELENTE: Performance nativa (<100ms)"
    echo "   → Pode processar direto do servidor (Sprint 4 opcional)"
fi

echo ""
echo "=== Benchmark Completo ==="
EOFSCRIPT

chmod +x ~/bin/benchmark-servidor.sh

echo "Executando benchmark..."
~/bin/benchmark-servidor.sh | tee ~/logs/sprint3-benchmark-$(date +%Y%m%d).log

echo ""

# ========== FASE 8: Criar Estruturas de Cache ==========
echo "[BONUS] Criando estrutura de cache local..."
mkdir -p ~/documentos-juridicos-cache/processos-ativos
mkdir -p ~/documentos-juridicos-cache/temp-processing
mkdir -p ~/claude-code-data/{inbox,processing,outputs,cache}
echo "✅ Estrutura de diretórios criada"
echo ""

# ========== CONCLUSAO ==========
echo "=========================================="
echo "SPRINT 3 - CONCLUIDO"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo ""
echo "1. Validar auto-mount após reinício WSL:"
echo "   PowerShell: wsl --shutdown"
echo "   Aguardar 10s"
echo "   PowerShell: wsl"
echo "   WSL: mount | grep servidor"
echo ""
echo "2. Revisar benchmark:"
echo "   cat ~/logs/sprint3-benchmark-$(date +%Y%m%d).log"
echo ""
echo "3. Testar hooks (verificar se EPERM ocorre):"
echo "   cd ~/claude-work/repos/Claude-Code-Projetos"
echo "   claude"
echo "   (Se travar: Ctrl+C e desabilitar SessionStart hooks)"
echo ""
echo "4. Commitar mudanças:"
echo "   git add ."
echo "   git commit -m \"docs: Sprint 3 completo - PC trabalho\""
echo "   git push"
echo ""
echo "Ver documentação completa: docs/SPRINT_3_ROADMAP.md"
echo ""
