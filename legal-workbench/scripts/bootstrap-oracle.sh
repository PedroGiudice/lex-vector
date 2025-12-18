#!/bin/bash
# =============================================================================
# Legal Workbench - Oracle Cloud Bootstrap Script
# =============================================================================
# Execute apos criar a VM Oracle Cloud A1.Flex:
#   curl -fsSL https://raw.githubusercontent.com/PedroGiudice/Claude-Code-Projetos/main/legal-workbench/scripts/bootstrap-oracle.sh | bash
# =============================================================================

set -e  # Exit on error

echo "=========================================="
echo " Legal Workbench - Oracle Cloud Bootstrap"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# 1. Verificar ambiente
# =============================================================================
log_info "Verificando ambiente..."

# Check if ARM64
ARCH=$(uname -m)
if [ "$ARCH" != "aarch64" ]; then
    log_warn "Arquitetura: $ARCH (esperado: aarch64/ARM64)"
    log_warn "Este script foi otimizado para Oracle Cloud A1.Flex (ARM)"
    read -p "Continuar mesmo assim? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check memory
MEM_GB=$(free -g | awk '/^Mem:/{print $2}')
log_info "Memoria disponivel: ${MEM_GB}GB"
if [ "$MEM_GB" -lt 8 ]; then
    log_warn "Recomendado: 24GB RAM para todos os servicos"
fi

# =============================================================================
# 2. Instalar Docker
# =============================================================================
log_info "Instalando Docker..."

if command -v docker &> /dev/null; then
    log_info "Docker ja instalado: $(docker --version)"
else
    # Detectar OS
    if [ -f /etc/oracle-release ]; then
        # Oracle Linux
        sudo dnf install -y dnf-utils device-mapper-persistent-data lvm2
        sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    elif [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y ca-certificates curl gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    else
        log_error "OS nao suportado. Instale Docker manualmente."
        exit 1
    fi

    sudo systemctl enable --now docker
    sudo usermod -aG docker $USER
    log_info "Docker instalado. Pode precisar relogar para grupo docker."
fi

# =============================================================================
# 3. Configurar Firewall
# =============================================================================
log_info "Configurando firewall..."

if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    sudo firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
    log_info "Portas 80 e 443 abertas no firewalld"
elif command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    log_info "Portas 80 e 443 abertas no ufw"
fi

# =============================================================================
# 4. Clonar repositorio
# =============================================================================
log_info "Clonando repositorio..."

REPO_DIR="$HOME/Claude-Code-Projetos"
if [ -d "$REPO_DIR" ]; then
    log_info "Repositorio ja existe. Atualizando..."
    cd "$REPO_DIR"
    git pull origin main
else
    cd "$HOME"
    git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
    cd "$REPO_DIR"
fi

cd "$REPO_DIR/legal-workbench"

# =============================================================================
# 5. Configurar variaveis de ambiente
# =============================================================================
log_info "Configurando variaveis de ambiente..."

if [ ! -f .env ]; then
    log_warn "Arquivo .env nao encontrado. Criando template..."
    cat > .env << 'ENVEOF'
# Trello API (obrigatorio para modulo Trello)
TRELLO_API_KEY=sua_api_key_aqui
TRELLO_API_TOKEN=seu_token_aqui

# Gemini API (obrigatorio para text-extractor)
GEMINI_API_KEY=sua_gemini_key_aqui

# Text Extractor Config
MAX_CONCURRENT_JOBS=2
JOB_TIMEOUT_SECONDS=600
ENVEOF

    log_warn "IMPORTANTE: Edite o arquivo .env com suas credenciais!"
    log_warn "   nano $REPO_DIR/legal-workbench/.env"
    echo ""
    read -p "Pressione ENTER apos editar o .env, ou Ctrl+C para sair..."
fi

# =============================================================================
# 6. Build e Deploy
# =============================================================================
log_info "Fazendo build das imagens Docker (pode demorar 10-15 min)..."

# Usar newgrp para aplicar grupo docker sem relogar
if ! groups | grep -q docker; then
    log_warn "Executando com sudo pois usuario nao esta no grupo docker ainda"
    sudo docker compose build
    sudo docker compose up -d
else
    docker compose build
    docker compose up -d
fi

# =============================================================================
# 7. Verificar deployment
# =============================================================================
log_info "Verificando deployment..."

sleep 10  # Aguardar containers iniciarem

echo ""
echo "=========================================="
echo " Status dos Containers"
echo "=========================================="
docker compose ps 2>/dev/null || sudo docker compose ps

echo ""
echo "=========================================="
echo " Testando endpoints"
echo "=========================================="

# Testar frontend
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200\|304"; then
    log_info "Frontend: OK"
else
    log_warn "Frontend: Verificar logs com 'docker compose logs frontend-react'"
fi

# Testar APIs
for api in trello stj doc text; do
    if curl -s http://localhost/api/$api/health 2>/dev/null | grep -qi "ok\|healthy"; then
        log_info "API $api: OK"
    else
        log_warn "API $api: Verificar logs"
    fi
done

# =============================================================================
# 8. Instrucoes finais
# =============================================================================
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || echo "<seu-ip-publico>")

echo ""
echo "=========================================="
echo " Deployment Concluido!"
echo "=========================================="
echo ""
echo "Acesse a aplicacao:"
echo "  http://$PUBLIC_IP/"
echo ""
echo "Comandos uteis:"
echo "  docker compose ps          # Ver status"
echo "  docker compose logs -f     # Ver logs"
echo "  docker compose restart     # Reiniciar tudo"
echo "  docker compose down        # Parar tudo"
echo ""
echo "Proximos passos:"
echo "  1. Configurar dominio no Cloudflare (opcional)"
echo "  2. Testar todos os modulos"
echo "  3. Compartilhar URL com a Bia!"
echo ""
log_info "Bootstrap concluido com sucesso!"
