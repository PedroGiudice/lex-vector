#!/bin/bash

# ==============================================================================
# Setup HD Externo Otimizado - STJ Dados Abertos
# ==============================================================================
# Este script configura o HD externo com detecção automática, benchmarks
# e validações completas para garantir performance otimizada.
#
# Características:
# - Auto-detecta drive com mais espaço livre
# - Executa benchmark de performance
# - Cria estrutura otimizada
# - Valida configuração
# - Gera relatório detalhado
# ==============================================================================

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configurações
MIN_SPACE_GB=50
MIN_WRITE_SPEED_MB=30  # Mínimo aceitável
GOOD_WRITE_SPEED_MB=60 # Bom desempenho
MIN_READ_SPEED_MB=60   # Mínimo aceitável
GOOD_READ_SPEED_MB=120 # Bom desempenho

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}    Setup HD Externo Otimizado - STJ Dados Abertos ${NC}"
echo -e "${BLUE}===================================================${NC}\n"

# ==============================================================================
# 1. DETECTAR HD EXTERNO COM MAIS ESPAÇO
# ==============================================================================
echo -e "${YELLOW}[1/8] Detectando HD externo...${NC}"

BEST_DRIVE=""
BEST_SPACE=0

for drive_letter in d e f g h; do
    mount_point="/mnt/${drive_letter}"
    if [ -d "$mount_point" ] && [ -w "$mount_point" ]; then
        # Obter espaço livre em GB
        SPACE_GB=$(df -BG "$mount_point" 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}')

        if [ -n "$SPACE_GB" ] && [ "$SPACE_GB" -gt "$BEST_SPACE" ]; then
            BEST_SPACE="$SPACE_GB"
            BEST_DRIVE="$mount_point"
        fi

        echo -e "  Encontrado: /mnt/${drive_letter}/ com ${GREEN}${SPACE_GB}GB${NC} livres"
    fi
done

if [ -z "$BEST_DRIVE" ] || [ "$BEST_SPACE" -lt "$MIN_SPACE_GB" ]; then
    echo -e "${RED}✗ Nenhum HD com espaço suficiente (mínimo ${MIN_SPACE_GB}GB)${NC}"
    exit 1
fi

HD_PATH="$BEST_DRIVE"
echo -e "${GREEN}✓ HD selecionado: $HD_PATH com ${BEST_SPACE}GB livres${NC}"

# Verificar filesystem
FS_TYPE=$(mount | grep "$HD_PATH" | awk '{print $5}')
echo -e "  Filesystem: ${CYAN}${FS_TYPE}${NC}"

# ==============================================================================
# 2. BENCHMARK DE PERFORMANCE
# ==============================================================================
echo -e "\n${YELLOW}[2/8] Testando performance do HD...${NC}"

BENCHMARK_DIR="${HD_PATH}/juridico-data/benchmark"
mkdir -p "$BENCHMARK_DIR"

# Teste de escrita (100MB para ser mais rápido)
echo -e "  ${CYAN}Testando escrita...${NC}"
WRITE_START=$(date +%s%N)
dd if=/dev/zero of="${BENCHMARK_DIR}/test_write.bin" bs=1M count=100 conv=fdatasync 2>&1 | grep -v records
WRITE_END=$(date +%s%N)
WRITE_TIME=$(echo "scale=3; ($WRITE_END - $WRITE_START) / 1000000000" | bc)
WRITE_SPEED=$(echo "scale=1; 100 / $WRITE_TIME" | bc)

# Teste de leitura
echo -e "  ${CYAN}Testando leitura...${NC}"
READ_START=$(date +%s%N)
dd if="${BENCHMARK_DIR}/test_write.bin" of=/dev/null bs=1M 2>&1 | grep -v records
READ_END=$(date +%s%N)
READ_TIME=$(echo "scale=3; ($READ_END - $READ_START) / 1000000000" | bc)
READ_SPEED=$(echo "scale=1; 100 / $READ_TIME" | bc)

# Limpar arquivo de teste
rm -f "${BENCHMARK_DIR}/test_write.bin"

# Avaliar performance
echo -e "\n  ${CYAN}Resultados:${NC}"
echo -e "  Velocidade de escrita: ${GREEN}${WRITE_SPEED} MB/s${NC}"
echo -e "  Velocidade de leitura: ${GREEN}${READ_SPEED} MB/s${NC}"

# Verificar se performance é aceitável
WRITE_OK=$(echo "$WRITE_SPEED >= $MIN_WRITE_SPEED_MB" | bc)
READ_OK=$(echo "$READ_SPEED >= $MIN_READ_SPEED_MB" | bc)

if [ "$WRITE_OK" -eq 0 ] || [ "$READ_OK" -eq 0 ]; then
    echo -e "${YELLOW}⚠ Performance abaixo do ideal, mas continuando...${NC}"
fi

# ==============================================================================
# 3. CRIAR ESTRUTURA DE DIRETÓRIOS
# ==============================================================================
echo -e "\n${YELLOW}[3/8] Criando estrutura de diretórios...${NC}"

BASE_DIR="${HD_PATH}/juridico-data"

# Estrutura principal
DIRS=(
    "$BASE_DIR/stj/raw"
    "$BASE_DIR/stj/staging"
    "$BASE_DIR/stj/archive/2022"
    "$BASE_DIR/stj/archive/2023"
    "$BASE_DIR/stj/archive/2024"
    "$BASE_DIR/stj/archive/2025"
    "$BASE_DIR/stj/database"
    "$BASE_DIR/stj/processed"
    "$BASE_DIR/stj/logs"
    "$BASE_DIR/shared/embeddings"
    "$BASE_DIR/shared/models"
    "$BASE_DIR/shared/cache"
    "$BASE_DIR/shared/temp"
    "$BASE_DIR/backups"
    "$BASE_DIR/exports"
)

for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
    echo -e "  ✓ ${dir#$BASE_DIR/}"
done

echo -e "${GREEN}✓ Estrutura criada com sucesso${NC}"

# ==============================================================================
# 4. CRIAR ARQUIVO DE CONFIGURAÇÃO
# ==============================================================================
echo -e "\n${YELLOW}[4/8] Criando arquivo de configuração...${NC}"

CONFIG_FILE="${BASE_DIR}/config.json"
HOME_CONFIG="${HOME}/.juridico-data-config.json"

cat > "$CONFIG_FILE" << EOF
{
  "version": "2.0.0",
  "created_at": "$(date -Iseconds)",
  "base_path": "$BASE_DIR",
  "hd_path": "$HD_PATH",
  "space_available_gb": $BEST_SPACE,
  "filesystem": "$FS_TYPE",
  "performance": {
    "write_speed_mb_s": $WRITE_SPEED,
    "read_speed_mb_s": $READ_SPEED,
    "tested_at": "$(date -Iseconds)"
  },
  "projects": {
    "stj": {
      "name": "STJ Dados Abertos",
      "path": "$BASE_DIR/stj",
      "database": "$BASE_DIR/stj/database/stj.duckdb",
      "staging": "$BASE_DIR/stj/staging",
      "archive": "$BASE_DIR/stj/archive",
      "raw": "$BASE_DIR/stj/raw",
      "active": true,
      "estimated_size_gb": 50
    }
  },
  "shared": {
    "embeddings": "$BASE_DIR/shared/embeddings",
    "models": "$BASE_DIR/shared/models",
    "cache": "$BASE_DIR/shared/cache",
    "temp": "$BASE_DIR/shared/temp"
  },
  "settings": {
    "max_staging_days": 7,
    "backup_retention_days": 30,
    "log_level": "INFO",
    "auto_cleanup": true,
    "min_free_space_gb": 10
  }
}
EOF

# Copiar config para home do usuário (cache)
cp "$CONFIG_FILE" "$HOME_CONFIG"

echo -e "${GREEN}✓ Configuração salva em:${NC}"
echo -e "  - $CONFIG_FILE"
echo -e "  - $HOME_CONFIG (cache)"

# ==============================================================================
# 5. CRIAR ARQUIVO .ENV
# ==============================================================================
echo -e "\n${YELLOW}[5/8] Criando arquivo .env...${NC}"

ENV_FILE="$(dirname "$0")/.env"

cat > "$ENV_FILE" << EOF
# Configuração HD Externo - Gerado em $(date)
# Performance: ${WRITE_SPEED} MB/s write, ${READ_SPEED} MB/s read
JURIDICO_DATA_BASE=$BASE_DIR
JURIDICO_HD_PATH=$HD_PATH
STJ_DATA_PATH=$BASE_DIR/stj
STJ_RAW_PATH=$BASE_DIR/stj/raw
STJ_STAGING_PATH=$BASE_DIR/stj/staging
STJ_DATABASE=$BASE_DIR/stj/database/stj.duckdb
STJ_ARCHIVE=$BASE_DIR/stj/archive
STJ_LOGS=$BASE_DIR/stj/logs
SHARED_EMBEDDINGS=$BASE_DIR/shared/embeddings
SHARED_CACHE=$BASE_DIR/shared/cache
SHARED_TEMP=$BASE_DIR/shared/temp
EOF

echo -e "${GREEN}✓ Arquivo .env criado${NC}"

# ==============================================================================
# 6. CRIAR SCRIPTS DE VALIDAÇÃO
# ==============================================================================
echo -e "\n${YELLOW}[6/8] Criando scripts auxiliares...${NC}"

# Script de validação
cat > "${BASE_DIR}/validate_setup.sh" << 'VALIDATE_EOF'
#!/bin/bash
# Validar configuração do HD

CONFIG_FILE="$HOME/.juridico-data-config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Configuração não encontrada. Execute setup_hd_optimized.sh primeiro."
    exit 1
fi

HD_PATH=$(jq -r '.hd_path' "$CONFIG_FILE")
MIN_SPACE=10

# Verificar se HD está acessível
if [ ! -d "$HD_PATH" ]; then
    echo "❌ HD não está acessível em $HD_PATH"
    exit 1
fi

# Verificar espaço livre
SPACE_GB=$(df -BG "$HD_PATH" | awk 'NR==2 {gsub(/G/,"",$4); print $4}')
if [ "$SPACE_GB" -lt "$MIN_SPACE" ]; then
    echo "⚠️  Espaço baixo: ${SPACE_GB}GB (mínimo: ${MIN_SPACE}GB)"
else
    echo "✅ HD OK: ${SPACE_GB}GB livres em $HD_PATH"
fi
VALIDATE_EOF

chmod +x "${BASE_DIR}/validate_setup.sh"

# Script de limpeza
cat > "${BASE_DIR}/cleanup_staging.sh" << 'CLEANUP_EOF'
#!/bin/bash
# Limpar arquivos staging antigos (> 7 dias)

STAGING_DIR="$(jq -r '.projects.stj.staging' ~/.juridico-data-config.json)"
DAYS_OLD=7

if [ -d "$STAGING_DIR" ]; then
    find "$STAGING_DIR" -type f -mtime +$DAYS_OLD -delete
    echo "✅ Arquivos staging > ${DAYS_OLD} dias removidos"
fi
CLEANUP_EOF

chmod +x "${BASE_DIR}/cleanup_staging.sh"

echo -e "${GREEN}✓ Scripts criados:${NC}"
echo -e "  - validate_setup.sh"
echo -e "  - cleanup_staging.sh"

# ==============================================================================
# 7. TESTE FINAL DE VALIDAÇÃO
# ==============================================================================
echo -e "\n${YELLOW}[7/8] Validando configuração...${NC}"

# Testar escrita em cada diretório principal
for test_dir in "$BASE_DIR/stj/raw" "$BASE_DIR/stj/staging" "$BASE_DIR/stj/database"; do
    test_file="${test_dir}/test_$(date +%s).tmp"
    echo "test" > "$test_file" 2>/dev/null
    if [ -f "$test_file" ]; then
        rm "$test_file"
        echo -e "  ✓ Escrita OK em ${test_dir#$BASE_DIR/}"
    else
        echo -e "  ${RED}✗ Falha de escrita em ${test_dir#$BASE_DIR/}${NC}"
    fi
done

# ==============================================================================
# 8. GERAR RELATÓRIO FINAL
# ==============================================================================
echo -e "\n${YELLOW}[8/8] Gerando relatório...${NC}"

REPORT_FILE="${BASE_DIR}/setup_report_$(date +%Y%m%d_%H%M%S).txt"

cat > "$REPORT_FILE" << EOF
================================================================================
RELATÓRIO DE CONFIGURAÇÃO - HD EXTERNO STJ DADOS ABERTOS
================================================================================
Data: $(date)
--------------------------------------------------------------------------------

CONFIGURAÇÃO DO HD:
- Caminho: $HD_PATH
- Espaço livre: ${BEST_SPACE}GB
- Filesystem: $FS_TYPE
- Base de dados: $BASE_DIR

PERFORMANCE MEDIDA:
- Velocidade de escrita: ${WRITE_SPEED} MB/s
- Velocidade de leitura: ${READ_SPEED} MB/s
- Avaliação: $([ "$WRITE_OK" -eq 1 ] && [ "$READ_OK" -eq 1 ] && echo "✅ ADEQUADA" || echo "⚠️  ABAIXO DO IDEAL")

ESTRUTURA CRIADA:
$(tree -L 2 "$BASE_DIR" 2>/dev/null || ls -la "$BASE_DIR")

COMPARAÇÃO DE PERFORMANCE:
- HD Externo (escrita): ${WRITE_SPEED} MB/s
- HD Externo (leitura): ${READ_SPEED} MB/s
- SSD Local (escrita): ~500 MB/s (típico)
- SSD Local (leitura): ~3000 MB/s (típico)

RECOMENDAÇÕES:
$(if [ "$WRITE_OK" -eq 0 ]; then
    echo "⚠️  Velocidade de escrita abaixo do ideal. Considere:"
    echo "   - Usar USB 3.0+ se estiver em USB 2.0"
    echo "   - Desfragmentar o HD se for NTFS"
    echo "   - Considerar SSD externo para melhor performance"
fi)

$(if [ "$BEST_SPACE" -lt 100 ]; then
    echo "⚠️  Espaço disponível menor que 100GB. Monitore regularmente."
fi)

PRÓXIMOS PASSOS:
1. Testar download inicial:
   cd ~/claude-work/repos/Claude-Code-Projetos/ferramentas/stj-dados-abertos
   python cli.py stj-download-periodo --inicio 2024-11-20 --fim 2024-11-22

2. Verificar configuração:
   ${BASE_DIR}/validate_setup.sh

3. Configurar cron para limpeza automática:
   crontab -e
   0 3 * * * ${BASE_DIR}/cleanup_staging.sh

================================================================================
EOF

echo -e "${GREEN}✓ Relatório salvo em: $REPORT_FILE${NC}"

# ==============================================================================
# SUMÁRIO FINAL
# ==============================================================================
echo -e "\n${GREEN}===================================================${NC}"
echo -e "${GREEN}         Setup Concluído com Sucesso!              ${NC}"
echo -e "${GREEN}===================================================${NC}\n"

echo -e "${CYAN}📊 Resumo da Performance:${NC}"
echo -e "  Escrita: ${GREEN}${WRITE_SPEED} MB/s${NC} $([ "$WRITE_OK" -eq 1 ] && echo "(✅ OK)" || echo "(⚠️  Lento)")"
echo -e "  Leitura: ${GREEN}${READ_SPEED} MB/s${NC} $([ "$READ_OK" -eq 1 ] && echo "(✅ OK)" || echo "(⚠️  Lento)")"

echo -e "\n${CYAN}📁 HD Configurado:${NC}"
echo -e "  Local: ${GREEN}${HD_PATH}${NC}"
echo -e "  Espaço: ${GREEN}${BEST_SPACE}GB${NC} livres"
echo -e "  Base: ${GREEN}${BASE_DIR}${NC}"

echo -e "\n${CYAN}✅ Validações:${NC}"
echo -e "  [✓] HD detectado automaticamente"
echo -e "  [✓] Estrutura de diretórios criada"
echo -e "  [✓] Performance testada e documentada"
echo -e "  [✓] Configuração salva"
echo -e "  [✓] Scripts de validação criados"

echo -e "\n${YELLOW}⚡ Próximo comando:${NC}"
echo -e "  ${BLUE}python cli.py stj-download-periodo --inicio 2024-11-20 --fim 2024-11-22${NC}"

echo -e "\n${GREEN}HD externo configurado e otimizado com sucesso!${NC}"