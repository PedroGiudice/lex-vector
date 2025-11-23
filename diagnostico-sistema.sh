#!/bin/bash

# =============================================================================
# DIAGNÓSTICO COMPLETO DO SISTEMA - WSL2 + Windows
# =============================================================================
# Analisa uso de armazenamento, performance e identifica causas de lentidão
# Criado: 2025-11-21
# =============================================================================

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configurações
LARGE_FILE_SIZE="500M"  # Arquivos maiores que isso serão reportados
TOP_DIRS=20             # Top N diretórios por tamanho
OUTPUT_FILE="diagnostico-$(date +%Y%m%d-%H%M%S).txt"

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

print_header() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}\n"
}

print_section() {
    echo -e "\n${BOLD}${BLUE}>>> $1${NC}\n"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

human_readable() {
    numfmt --to=iec-i --suffix=B "$1" 2>/dev/null || echo "$1"
}

# =============================================================================
# INFORMAÇÕES DO SISTEMA
# =============================================================================

system_info() {
    print_header "1. INFORMAÇÕES DO SISTEMA"

    echo "Hostname: $(hostname)"
    echo "Kernel: $(uname -r)"
    echo "OS: $(lsb_release -d | cut -f2)"
    echo "Arquitetura: $(uname -m)"
    echo "Uptime: $(uptime -p)"
    echo ""

    # WSL Version
    if [ -f /proc/sys/fs/binfmt_misc/WSLInterop ]; then
        print_success "Rodando em WSL2"
        echo "WSL Version: $(cat /proc/version | grep -oP 'WSL\d+')"
    fi
}

# =============================================================================
# USO DE MEMÓRIA RAM
# =============================================================================

memory_usage() {
    print_header "2. USO DE MEMÓRIA RAM"

    free -h
    echo ""

    # Top 10 processos por memória
    print_section "Top 10 Processos (Memória)"
    ps aux --sort=-%mem | head -11 | awk '{printf "%-20s %6s %6s %s\n", $1, $3, $4, $11}'
}

# =============================================================================
# USO DE DISCO - VISÃO GERAL
# =============================================================================

disk_overview() {
    print_header "3. USO DE DISCO - VISÃO GERAL"

    print_section "Sistemas de Arquivos Montados"
    df -h --output=source,fstype,size,used,avail,pcent,target | grep -v "tmpfs\|udev"

    echo ""
    print_section "Inodes (Arquivos)"
    df -i | grep -v "tmpfs\|udev"

    # Análise crítica
    echo ""
    local usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$usage" -gt 90 ]; then
        print_error "CRÍTICO: Disco raiz em ${usage}% de uso!"
    elif [ "$usage" -gt 80 ]; then
        print_warning "ATENÇÃO: Disco raiz em ${usage}% de uso"
    else
        print_success "Disco raiz em ${usage}% de uso (OK)"
    fi
}

# =============================================================================
# TOP DIRETÓRIOS POR TAMANHO - WSL
# =============================================================================

top_directories_wsl() {
    print_header "4. TOP ${TOP_DIRS} DIRETÓRIOS (WSL)"

    print_section "Analisando /home (pode levar alguns minutos)..."
    sudo du -h --max-depth=2 /home 2>/dev/null | sort -rh | head -n "$TOP_DIRS"

    echo ""
    print_section "Analisando /var (logs, cache, apt)..."
    sudo du -h --max-depth=2 /var 2>/dev/null | sort -rh | head -n "$TOP_DIRS"

    echo ""
    print_section "Analisando /usr (binários, libs)..."
    sudo du -h --max-depth=2 /usr 2>/dev/null | sort -rh | head -n "$TOP_DIRS"

    echo ""
    print_section "Analisando /tmp (temporários)..."
    sudo du -h --max-depth=2 /tmp 2>/dev/null | sort -rh | head -n 10
}

# =============================================================================
# ANÁLISE ESPECÍFICA - NODE_MODULES
# =============================================================================

analyze_node_modules() {
    print_header "5. ANÁLISE: node_modules (Comum Acumular GB)"

    local home_dir="/home/$(whoami)"
    local total_size=0
    local count=0

    print_section "Buscando todos os node_modules em $home_dir..."

    while IFS= read -r -d '' dir; do
        local size=$(du -sb "$dir" 2>/dev/null | cut -f1)
        local size_human=$(human_readable "$size")
        echo "$size_human - $dir"
        total_size=$((total_size + size))
        count=$((count + 1))
    done < <(find "$home_dir" -type d -name "node_modules" -print0 2>/dev/null)

    echo ""
    if [ "$count" -gt 0 ]; then
        print_warning "Total de $count diretórios node_modules: $(human_readable $total_size)"
        echo "Sugestão: Considere remover node_modules de projetos antigos"
        echo "Comando: find ~/claude-work -type d -name 'node_modules' -exec rm -rf {} +"
    else
        print_success "Nenhum node_modules encontrado"
    fi
}

# =============================================================================
# ANÁLISE ESPECÍFICA - PYTHON VENV
# =============================================================================

analyze_python_venv() {
    print_header "6. ANÁLISE: Python venv (Virtual Environments)"

    local home_dir="/home/$(whoami)"
    local total_size=0
    local count=0

    print_section "Buscando todos os .venv em $home_dir..."

    while IFS= read -r -d '' dir; do
        local size=$(du -sb "$dir" 2>/dev/null | cut -f1)
        local size_human=$(human_readable "$size")
        echo "$size_human - $dir"
        total_size=$((total_size + size))
        count=$((count + 1))
    done < <(find "$home_dir" -type d -name ".venv" -o -name "venv" -print0 2>/dev/null | head -20)

    echo ""
    if [ "$count" -gt 0 ]; then
        echo "Total de ~$count virtual envs: $(human_readable $total_size)"
        echo "Sugestão: Remova venvs de projetos antigos"
    else
        print_success "Nenhum venv detectado (ou muito poucos)"
    fi
}

# =============================================================================
# ANÁLISE ESPECÍFICA - DOCKER/CONTAINERS
# =============================================================================

analyze_docker() {
    print_header "7. ANÁLISE: Docker (Pode Consumir Dezenas de GB)"

    if command -v docker &> /dev/null; then
        print_section "Imagens Docker"
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>/dev/null || echo "Docker não acessível"

        echo ""
        print_section "Containers Docker"
        docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Size}}" 2>/dev/null || echo "Docker não acessível"

        echo ""
        print_section "Volumes Docker"
        docker volume ls 2>/dev/null || echo "Docker não acessível"

        echo ""
        print_warning "Sugestão: Limpar imagens/containers não usados"
        echo "Comandos:"
        echo "  docker system prune -a       # Remove tudo não usado"
        echo "  docker image prune -a        # Remove apenas imagens"
        echo "  docker volume prune          # Remove apenas volumes"
    else
        print_success "Docker não instalado (não consome espaço)"
    fi
}

# =============================================================================
# ANÁLISE ESPECÍFICA - APT CACHE
# =============================================================================

analyze_apt_cache() {
    print_header "8. ANÁLISE: APT Cache (Pacotes .deb Baixados)"

    local cache_size=$(du -sh /var/cache/apt/archives 2>/dev/null | cut -f1)
    local cache_count=$(ls /var/cache/apt/archives/*.deb 2>/dev/null | wc -l)

    echo "Tamanho do cache APT: $cache_size"
    echo "Número de pacotes .deb: $cache_count"

    if [ "$cache_count" -gt 100 ]; then
        print_warning "Cache APT grande. Considere limpar:"
        echo "sudo apt-get clean     # Remove todos os .deb"
        echo "sudo apt-get autoclean # Remove apenas .deb antigos"
    else
        print_success "Cache APT em tamanho normal"
    fi
}

# =============================================================================
# ARQUIVOS GRANDES (>500MB)
# =============================================================================

find_large_files() {
    print_header "9. ARQUIVOS GRANDES (>${LARGE_FILE_SIZE})"

    print_section "Buscando em /home (pode levar alguns minutos)..."

    find /home/$(whoami) -type f -size +"$LARGE_FILE_SIZE" -exec ls -lh {} \; 2>/dev/null | \
        awk '{print $5 "\t" $9}' | sort -rh | head -20 || echo "Nenhum arquivo grande encontrado"

    echo ""
    print_section "Buscando em /var/log..."

    find /var/log -type f -size +"$LARGE_FILE_SIZE" -exec ls -lh {} \; 2>/dev/null | \
        awk '{print $5 "\t" $9}' | sort -rh | head -10 || echo "Nenhum log grande encontrado"
}

# =============================================================================
# ANÁLISE WINDOWS (via /mnt/c)
# =============================================================================

analyze_windows_drives() {
    print_header "10. ANÁLISE: DRIVES WINDOWS (via WSL)"

    if [ -d "/mnt/c" ]; then
        print_section "Uso de Disco Windows (C:)"
        df -h /mnt/c | tail -1

        echo ""
        print_section "Top 15 Diretórios em C:\\ (limitado a 2 níveis)"
        sudo du -h --max-depth=2 /mnt/c 2>/dev/null | sort -rh | head -15 || \
            print_warning "Sem permissão para analisar C:\\"

        # Verificar disco virtual do WSL
        echo ""
        print_section "Disco Virtual WSL (ext4.vhdx)"
        local wsl_vhdx_path="/mnt/c/Users/*/AppData/Local/Packages/CanonicalGroupLimited*/LocalState/ext4.vhdx"
        if ls $wsl_vhdx_path 2>/dev/null; then
            ls -lh $wsl_vhdx_path | awk '{print "Tamanho: " $5}'
            print_warning "Este é o disco virtual do WSL2. Se muito grande:"
            echo "1. Libere espaço dentro do WSL (este script ajuda)"
            echo "2. Compacte o VHDX no PowerShell (Windows):"
            echo "   wsl --shutdown"
            echo "   Optimize-VHD -Path <caminho-do-vhdx> -Mode Full"
        fi
    else
        print_warning "Drive C:\\ não montado em /mnt/c"
    fi
}

# =============================================================================
# LOGS DO SISTEMA
# =============================================================================

analyze_logs() {
    print_header "11. ANÁLISE: LOGS DO SISTEMA"

    print_section "Top 10 Maiores Logs em /var/log"
    sudo du -ah /var/log 2>/dev/null | sort -rh | head -10

    echo ""
    print_section "Journal do systemd (journalctl)"
    local journal_size=$(sudo journalctl --disk-usage 2>/dev/null | grep -oP '\d+\.\d+[KMGT]')
    echo "Tamanho do journal: $journal_size"

    if [[ "$journal_size" == *G ]]; then
        print_warning "Journal grande. Considere limpar:"
        echo "sudo journalctl --vacuum-time=7d    # Manter apenas últimos 7 dias"
        echo "sudo journalctl --vacuum-size=500M  # Limitar a 500MB"
    fi
}

# =============================================================================
# PROCESSOS CONSUMINDO CPU
# =============================================================================

cpu_usage() {
    print_header "12. USO DE CPU"

    print_section "Top 10 Processos (CPU)"
    ps aux --sort=-%cpu | head -11 | awk '{printf "%-20s %6s %6s %s\n", $1, $3, $4, $11}'
}

# =============================================================================
# RESUMO E RECOMENDAÇÕES
# =============================================================================

generate_recommendations() {
    print_header "13. RESUMO E RECOMENDAÇÕES"

    echo -e "${BOLD}Comandos Úteis para Liberar Espaço:${NC}"
    echo ""
    echo "1. Limpar APT cache:"
    echo "   sudo apt-get clean && sudo apt-get autoclean"
    echo ""
    echo "2. Remover pacotes órfãos:"
    echo "   sudo apt-get autoremove --purge"
    echo ""
    echo "3. Limpar node_modules antigos:"
    echo "   find ~/claude-work -type d -name 'node_modules' -mtime +90 -exec rm -rf {} +"
    echo ""
    echo "4. Limpar logs systemd:"
    echo "   sudo journalctl --vacuum-time=7d"
    echo ""
    echo "5. Limpar Docker (se instalado):"
    echo "   docker system prune -a --volumes"
    echo ""
    echo "6. Compactar VHDX do WSL (no PowerShell Windows):"
    echo "   wsl --shutdown"
    echo "   Optimize-VHD -Path '<caminho-vhdx>' -Mode Full"
    echo ""
    echo -e "${BOLD}Análise de Performance WSL2:${NC}"
    echo ""
    echo "1. Verifique configuração do .wslconfig (C:\\Users\\<user>\\.wslconfig):"
    echo "   [wsl2]"
    echo "   memory=8GB"
    echo "   processors=4"
    echo ""
    echo "2. Reinicie WSL após mudanças:"
    echo "   wsl --shutdown"
    echo ""
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    clear
    echo -e "${BOLD}${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║         DIAGNÓSTICO COMPLETO DO SISTEMA - WSL2               ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "Iniciando análise completa..."
    echo "Salvando output em: $OUTPUT_FILE"
    echo ""

    # Executar todas as análises
    system_info
    memory_usage
    disk_overview
    top_directories_wsl
    analyze_node_modules
    analyze_python_venv
    analyze_docker
    analyze_apt_cache
    find_large_files
    analyze_windows_drives
    analyze_logs
    cpu_usage
    generate_recommendations

    echo ""
    print_header "DIAGNÓSTICO COMPLETO!"
    echo "Relatório salvo em: $OUTPUT_FILE"
    echo ""
    echo "Para executar novamente: bash $0"
}

# Executar com output para arquivo E tela
main 2>&1 | tee "$OUTPUT_FILE"
