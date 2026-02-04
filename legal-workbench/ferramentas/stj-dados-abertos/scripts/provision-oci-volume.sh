#!/bin/bash
# =============================================================================
# Provisionamento de Volume de Bloco OCI para STJ Dados Abertos
# =============================================================================
#
# Este script configura um volume de bloco OCI anexado para armazenar dados do STJ.
#
# PRE-REQUISITOS (no OCI Console):
# 1. Criar Block Volume de 100GB na mesma availability domain da VM
# 2. Anexar o volume a esta instancia (paravirtualized attachment)
# 3. Obter o device path (ex: /dev/sdb)
#
# EXECUCAO:
#   sudo ./provision-oci-volume.sh /dev/sdb
#
# =============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuracoes
MOUNT_POINT="/mnt/juridico-data"
STJ_DATA_DIR="$MOUNT_POINT/stj"
FS_TYPE="xfs"
OWNER="opc:opc"

# Verificar se rodando como root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ERRO] Execute como root: sudo $0 <device>${NC}"
    exit 1
fi

# Verificar argumento
if [ -z "$1" ]; then
    echo "Uso: sudo $0 <device>"
    echo ""
    echo "Exemplo: sudo $0 /dev/sdb"
    echo ""
    echo "Devices disponiveis:"
    lsblk -d -o NAME,SIZE,TYPE | grep disk
    exit 1
fi

DEVICE="$1"

# Verificar se device existe
if [ ! -b "$DEVICE" ]; then
    echo -e "${RED}[ERRO] Device nao encontrado: $DEVICE${NC}"
    echo ""
    echo "Devices disponiveis:"
    lsblk -d -o NAME,SIZE,TYPE | grep disk
    exit 1
fi

# Verificar se ja esta montado
if mount | grep -q "$DEVICE"; then
    echo -e "${YELLOW}[AVISO] Device ja esta montado:${NC}"
    mount | grep "$DEVICE"
    exit 1
fi

echo "=========================================="
echo "Provisionamento de Volume OCI"
echo "=========================================="
echo ""
echo "Device: $DEVICE"
echo "Mount Point: $MOUNT_POINT"
echo "Filesystem: $FS_TYPE"
echo ""

# Confirmar
read -p "Continuar? TODOS OS DADOS NO DEVICE SERAO PERDIDOS! (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelado."
    exit 1
fi

echo ""
echo "1. Formatando device..."
mkfs.$FS_TYPE "$DEVICE"
echo -e "${GREEN}[OK] Device formatado${NC}"

echo ""
echo "2. Criando mount point..."
mkdir -p "$MOUNT_POINT"
echo -e "${GREEN}[OK] Mount point criado: $MOUNT_POINT${NC}"

echo ""
echo "3. Montando volume..."
mount "$DEVICE" "$MOUNT_POINT"
echo -e "${GREEN}[OK] Volume montado${NC}"

echo ""
echo "4. Criando estrutura de diretorios..."
mkdir -p "$STJ_DATA_DIR"/{staging,archive,raw,database,logs,metadata,backups}
chown -R $OWNER "$MOUNT_POINT"
chmod -R 755 "$MOUNT_POINT"
echo -e "${GREEN}[OK] Diretorios criados${NC}"

echo ""
echo "5. Adicionando ao fstab para mount automatico..."
# Obter UUID do device
UUID=$(blkid -s UUID -o value "$DEVICE")
FSTAB_ENTRY="UUID=$UUID $MOUNT_POINT $FS_TYPE defaults,noatime,_netdev 0 0"

# Verificar se ja existe no fstab
if grep -q "$UUID" /etc/fstab; then
    echo -e "${YELLOW}[AVISO] Ja existe entrada no fstab${NC}"
else
    echo "$FSTAB_ENTRY" >> /etc/fstab
    echo -e "${GREEN}[OK] Adicionado ao fstab${NC}"
fi

echo ""
echo "6. Verificando mount..."
df -h "$MOUNT_POINT"

echo ""
echo "=========================================="
echo -e "${GREEN}[OK] Provisionamento concluido!${NC}"
echo "=========================================="
echo ""
echo "Proximos passos:"
echo ""
echo "1. Configurar variavel de ambiente:"
echo "   export DATA_PATH=$STJ_DATA_DIR"
echo "   export DB_PATH=$STJ_DATA_DIR/database/stj.duckdb"
echo ""
echo "2. Adicionar ao ~/.bashrc:"
echo "   echo 'export DATA_PATH=$STJ_DATA_DIR' >> ~/.bashrc"
echo "   echo 'export DB_PATH=$STJ_DATA_DIR/database/stj.duckdb' >> ~/.bashrc"
echo ""
echo "3. Testar CLI:"
echo "   cd /home/opc/lex-vector/legal-workbench/ferramentas/stj-dados-abertos"
echo "   source .venv/bin/activate"
echo "   python cli.py stj-init"
echo ""
echo "4. Iniciar download massivo (apos validacao):"
echo "   python cli.py stj-download-periodo 2022-05-01 $(date +%Y-%m-%d) --orgao corte_especial"
echo ""
