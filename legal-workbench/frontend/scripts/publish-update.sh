#!/usr/bin/env bash
#
# publish-update.sh - Publica AppImage do Legal Workbench para auto-update
#
# Uso: ./scripts/publish-update.sh [notas-da-release]
#
# Fluxo:
#   1. Le versao do tauri.conf.json
#   2. Encontra o AppImage gerado pelo build
#   3. Reempacota com libgpg-error.so.0 (fix cross-distro OL10 -> Ubuntu)
#   4. Re-assina com chave do projeto
#   5. Copia para /var/www/updates/
#   6. Gera latest.json
#   7. Corrige SELinux
#   8. Verifica servidor
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TAURI_CONF="$PROJECT_DIR/src-tauri/tauri.conf.json"

# Configuracao
SIGNING_KEY="$HOME/.tauri/lex-vector.key"
SIGNING_KEY_PASSWORD="x"
UPDATE_DIR="/var/www/updates"
UPDATE_SERVER="http://100.114.203.28:8090"
TAILSCALE_IP="100.114.203.28"

# Cores (sem emojis)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[publish]${NC} $1"; }
warn() { echo -e "${YELLOW}[publish]${NC} $1"; }
error() { echo -e "${RED}[publish]${NC} $1" >&2; exit 1; }

# 1. Ler versao
VERSION=$(grep '"version"' "$TAURI_CONF" | head -1 | sed 's/.*"\([0-9.]*\)".*/\1/')
[ -z "$VERSION" ] && error "Nao conseguiu ler versao de $TAURI_CONF"
log "Versao: $VERSION"

# Notas da release
NOTES="${1:-Legal Workbench v${VERSION}}"
log "Notas: $NOTES"

# 2. Encontrar AppImage do build
BUNDLE_DIR="$PROJECT_DIR/src-tauri/target/release/bundle/appimage"
PRODUCT_NAME=$(grep '"productName"' "$TAURI_CONF" | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
APPIMAGE=$(find "$BUNDLE_DIR" -name "*.AppImage" -not -name "*.sig" 2>/dev/null | head -1)
[ -z "$APPIMAGE" ] && error "AppImage nao encontrado em $BUNDLE_DIR. Rode 'bun run tauri build' primeiro."
log "AppImage encontrado: $(basename "$APPIMAGE")"

# 3. Reempacotar com libgpg-error.so.0 (fix cross-distro)
log "Reempacotando AppImage com libgpg-error.so.0..."
WORK_DIR=$(mktemp -d)
cd "$WORK_DIR"

# Extrair AppImage
APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGE" --appimage-extract > /dev/null 2>&1
[ ! -d "squashfs-root" ] && error "Falha ao extrair AppImage"

# Adicionar lib faltante
if [ -f "/lib64/libgpg-error.so.0" ]; then
    cp /lib64/libgpg-error.so.0 squashfs-root/usr/lib/
    log "libgpg-error.so.0 adicionada"
else
    warn "libgpg-error.so.0 nao encontrada em /lib64/ - pulando"
fi

# Encontrar appimagetool
APPIMAGETOOL_APPIMAGE=$(find "$HOME/.cache/tauri" -name "linuxdeploy-plugin-appimage*" 2>/dev/null | head -1)
if [ -z "$APPIMAGETOOL_APPIMAGE" ]; then
    error "linuxdeploy-plugin-appimage nao encontrado em ~/.cache/tauri/"
fi

TOOL_DIR=$(mktemp -d)
cd "$TOOL_DIR"
APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL_APPIMAGE" --appimage-extract > /dev/null 2>&1

OUTPUT_APPIMAGE="$WORK_DIR/${PRODUCT_NAME}_${VERSION}_amd64.AppImage"
cd "$WORK_DIR"
ARCH=x86_64 NO_STRIP=true "$TOOL_DIR/squashfs-root/usr/bin/appimagetool" squashfs-root "$OUTPUT_APPIMAGE" > /dev/null 2>&1
log "AppImage reempacotado: $(basename "$OUTPUT_APPIMAGE")"

# 4. Re-assinar
log "Assinando AppImage..."
export TAURI_SIGNING_PRIVATE_KEY=$(cat "$SIGNING_KEY")
export TAURI_SIGNING_PRIVATE_KEY_PASSWORD="$SIGNING_KEY_PASSWORD"

cd "$PROJECT_DIR"
bun run tauri signer sign "$OUTPUT_APPIMAGE" \
    -k "$TAURI_SIGNING_PRIVATE_KEY" \
    -p "$TAURI_SIGNING_PRIVATE_KEY_PASSWORD" > /dev/null 2>&1

SIG_FILE="${OUTPUT_APPIMAGE}.sig"
[ ! -f "$SIG_FILE" ] && error "Arquivo .sig nao gerado"
log "Assinatura gerada"

# 5. Copiar para /var/www/updates/
log "Copiando para $UPDATE_DIR..."
cp "$OUTPUT_APPIMAGE" "$UPDATE_DIR/"
cp "$SIG_FILE" "$UPDATE_DIR/"

# 6. Gerar latest.json
SIGNATURE=$(cat "$SIG_FILE")
PUB_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
ENCODED_NAME=$(echo "${PRODUCT_NAME}_${VERSION}_amd64.AppImage" | sed 's/ /%20/g')

cat > "$UPDATE_DIR/latest.json" << EOF
{
  "version": "$VERSION",
  "notes": "$NOTES",
  "pub_date": "$PUB_DATE",
  "platforms": {
    "linux-x86_64": {
      "signature": "$SIGNATURE",
      "url": "${UPDATE_SERVER}/${ENCODED_NAME}"
    }
  }
}
EOF
log "latest.json gerado"

# 7. Corrigir SELinux
if command -v chcon &> /dev/null; then
    chcon -R -t httpd_sys_content_t "$UPDATE_DIR/" 2>/dev/null || true
    log "SELinux corrigido"
fi

# 8. Verificar servidor
log "Verificando servidor..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8090/latest.json" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    log "Servidor OK (HTTP 200)"
    SERVED_VERSION=$(curl -s "http://localhost:8090/latest.json" | grep '"version"' | sed 's/.*"\([0-9.]*\)".*/\1/')
    log "Versao publicada: $SERVED_VERSION"
else
    warn "Servidor retornou HTTP $HTTP_CODE - verificar nginx"
fi

# Cleanup
rm -rf "$WORK_DIR" "$TOOL_DIR"

log "Publicacao concluida!"
log "  AppImage: ${PRODUCT_NAME}_${VERSION}_amd64.AppImage"
log "  URL: ${UPDATE_SERVER}/${ENCODED_NAME}"
log "  latest.json: ${UPDATE_SERVER}/latest.json"
