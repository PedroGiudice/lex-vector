#!/bin/bash

# ==============================================================================
# Setup HD Externo para Base de Dados Jurídica
# ==============================================================================
# Este script configura o HD externo (E:\ no Windows = /mnt/e/ no WSL2)
# para servir como base de dados central para múltiplos projetos jurídicos.
#
# Estrutura criada:
# - STJ Dados Abertos
# - TJSP (futuro)
# - STF (futuro)
# - Shared databases
# ==============================================================================

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}    Setup HD Externo - Base de Dados Jurídica     ${NC}"
echo -e "${BLUE}===================================================${NC}\n"

# 1. VERIFICAR SE HD EXTERNO ESTÁ ACESSÍVEL
# ==============================================================================
echo -e "${YELLOW}[1/7] Verificando HD externo...${NC}"

# Tentar múltiplos pontos de montagem comuns
HD_PATH=""
for mount_point in "/mnt/e" "/mnt/d" "/mnt/f" "/mnt/g"; do
    if [ -d "$mount_point" ] && [ -w "$mount_point" ]; then
        HD_PATH="$mount_point"
        echo -e "${GREEN}✓ HD externo encontrado em: $HD_PATH${NC}"

        # Verificar espaço disponível
        SPACE_AVAILABLE=$(df -h "$HD_PATH" | awk 'NR==2 {print $4}')
        SPACE_GB=$(df -BG "$HD_PATH" | awk 'NR==2 {gsub(/G/,"",$4); print $4}')

        echo -e "  Espaço disponível: ${GREEN}${SPACE_AVAILABLE}${NC}"

        if [ "$SPACE_GB" -lt 100 ]; then
            echo -e "${YELLOW}⚠ Aviso: Recomendado ter pelo menos 100GB livres${NC}"
            echo -e "  Continuar mesmo assim? (s/n)"
            read -r resposta
            if [[ ! "$resposta" =~ ^[Ss]$ ]]; then
                echo -e "${RED}Setup cancelado.${NC}"
                exit 1
            fi
        fi
        break
    fi
done

if [ -z "$HD_PATH" ]; then
    echo -e "${RED}✗ HD externo não encontrado ou sem permissão de escrita${NC}"
    echo -e "${YELLOW}Por favor, verifique se o HD está montado corretamente.${NC}"
    echo -e "Tente: ls /mnt/"
    exit 1
fi

# 2. CRIAR ESTRUTURA PRINCIPAL
# ==============================================================================
echo -e "\n${YELLOW}[2/7] Criando estrutura de diretórios...${NC}"

BASE_DIR="$HD_PATH/juridico-data"

# Estrutura principal
mkdir -p "$BASE_DIR"/{databases,downloads,staging,exports,logs,backups,shared}

# Sub-estruturas por projeto
# STJ Dados Abertos
mkdir -p "$BASE_DIR/stj"/{archive,staging,processed,database}
mkdir -p "$BASE_DIR/stj/archive"/{2022,2023,2024,2025}

# TJSP (futuro)
mkdir -p "$BASE_DIR/tjsp"/{archive,staging,processed,database}

# STF (futuro)
mkdir -p "$BASE_DIR/stf"/{archive,staging,processed,database}

# Shared resources
mkdir -p "$BASE_DIR/shared"/{embeddings,models,cache,temp}

echo -e "${GREEN}✓ Estrutura de diretórios criada${NC}"

# 3. CONFIGURAR PERMISSÕES
# ==============================================================================
echo -e "\n${YELLOW}[3/7] Configurando permissões...${NC}"

# Dar permissões adequadas (leitura/escrita para usuário)
chmod -R 755 "$BASE_DIR"

echo -e "${GREEN}✓ Permissões configuradas${NC}"

# 4. CRIAR ARQUIVO DE CONFIGURAÇÃO
# ==============================================================================
echo -e "\n${YELLOW}[4/7] Criando arquivo de configuração...${NC}"

CONFIG_FILE="$BASE_DIR/config.json"

cat > "$CONFIG_FILE" << EOF
{
  "version": "1.0.0",
  "created_at": "$(date -Iseconds)",
  "base_path": "$BASE_DIR",
  "projects": {
    "stj": {
      "name": "STJ Dados Abertos",
      "path": "$BASE_DIR/stj",
      "database": "$BASE_DIR/stj/database/stj.duckdb",
      "staging": "$BASE_DIR/stj/staging",
      "archive": "$BASE_DIR/stj/archive",
      "active": true
    },
    "tjsp": {
      "name": "TJSP Jurisprudência",
      "path": "$BASE_DIR/tjsp",
      "database": "$BASE_DIR/tjsp/database/tjsp.duckdb",
      "staging": "$BASE_DIR/tjsp/staging",
      "archive": "$BASE_DIR/tjsp/archive",
      "active": false
    },
    "stf": {
      "name": "STF Jurisprudência",
      "path": "$BASE_DIR/stf",
      "database": "$BASE_DIR/stf/database/stf.duckdb",
      "staging": "$BASE_DIR/stf/staging",
      "archive": "$BASE_DIR/stf/archive",
      "active": false
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
    "log_level": "INFO"
  }
}
EOF

echo -e "${GREEN}✓ Arquivo de configuração criado${NC}"

# 5. CRIAR SYMLINK PARA FACILITAR ACESSO
# ==============================================================================
echo -e "\n${YELLOW}[5/7] Criando link simbólico...${NC}"

SYMLINK_PATH="$HOME/juridico-data"

if [ -L "$SYMLINK_PATH" ]; then
    echo -e "  Link simbólico já existe, removendo..."
    rm "$SYMLINK_PATH"
fi

ln -s "$BASE_DIR" "$SYMLINK_PATH"
echo -e "${GREEN}✓ Link criado: ~/juridico-data → $BASE_DIR${NC}"

# 6. TESTE DE PERFORMANCE
# ==============================================================================
echo -e "\n${YELLOW}[6/7] Testando performance do HD...${NC}"

TEST_FILE="$BASE_DIR/shared/temp/test_performance_$(date +%s).dat"

# Teste de escrita (100MB)
echo -e "  Testando velocidade de escrita..."
dd if=/dev/zero of="$TEST_FILE" bs=1M count=100 conv=fdatasync 2>&1 | grep -E 'copied|copiados' | tail -1

# Teste de leitura
echo -e "  Testando velocidade de leitura..."
dd if="$TEST_FILE" of=/dev/null bs=1M 2>&1 | grep -E 'copied|copiados' | tail -1

# Limpar arquivo de teste
rm -f "$TEST_FILE"

echo -e "${GREEN}✓ Testes de performance concluídos${NC}"

# 7. CRIAR ARQUIVO .env PARA O PROJETO
# ==============================================================================
echo -e "\n${YELLOW}[7/7] Configurando variáveis de ambiente...${NC}"

ENV_FILE="$(dirname "$0")/.env"

cat > "$ENV_FILE" << EOF
# Configuração HD Externo - Gerado em $(date)
JURIDICO_DATA_BASE=$BASE_DIR
STJ_DATA_PATH=$BASE_DIR/stj
STJ_DATABASE=$BASE_DIR/stj/database/stj.duckdb
STJ_STAGING=$BASE_DIR/stj/staging
STJ_ARCHIVE=$BASE_DIR/stj/archive
SHARED_EMBEDDINGS=$BASE_DIR/shared/embeddings
SHARED_CACHE=$BASE_DIR/shared/cache
EOF

echo -e "${GREEN}✓ Arquivo .env criado${NC}"

# SUMÁRIO FINAL
# ==============================================================================
echo -e "\n${GREEN}===================================================${NC}"
echo -e "${GREEN}         Setup Concluído com Sucesso!              ${NC}"
echo -e "${GREEN}===================================================${NC}\n"

echo -e "${BLUE}Estrutura criada em:${NC} $BASE_DIR"
echo -e "${BLUE}Link simbólico:${NC} ~/juridico-data"
echo -e "${BLUE}Configuração:${NC} $CONFIG_FILE"
echo -e "${BLUE}Variáveis:${NC} .env"

echo -e "\n${YELLOW}Estrutura de diretórios:${NC}"
tree -L 2 "$BASE_DIR" 2>/dev/null || ls -la "$BASE_DIR"

echo -e "\n${YELLOW}Próximos passos:${NC}"
echo -e "1. Atualizar config.py para usar os novos paths:"
echo -e "   ${BLUE}DATA_ROOT = Path('$BASE_DIR/stj')${NC}"
echo -e "2. Testar download inicial:"
echo -e "   ${BLUE}python cli.py stj-download-mvp${NC}"
echo -e "3. Para outros projetos, usar:"
echo -e "   ${BLUE}$BASE_DIR/tjsp${NC} ou ${BLUE}$BASE_DIR/stf${NC}"

echo -e "\n${GREEN}HD externo configurado e pronto para uso!${NC}"