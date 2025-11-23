#!/bin/bash

# =============================================================================
# DIAGNÓSTICO WINDOWS C:\ - Análise Completa de Armazenamento
# =============================================================================
# Focado em encontrar o que está consumindo os 91% de espaço em C:\
# Criado: 2025-11-21
# =============================================================================

OUTPUT_FILE="diagnostico-windows-$(date +%Y%m%d-%H%M%S).txt"

exec > >(tee "$OUTPUT_FILE")
exec 2>&1

echo "=========================================="
echo "DIAGNÓSTICO WINDOWS C:\ - 91% USADO"
echo "Total: 223GB | Usado: 201GB | Livre: 22GB"
echo "=========================================="
echo ""
echo "Iniciado: $(date)"
echo "Relatório será salvo em: $OUTPUT_FILE"
echo ""

# =============================================================================
# 1. DISCO VIRTUAL WSL2
# =============================================================================
echo "=========================================="
echo "1. DISCO VIRTUAL WSL2 (ext4.vhdx)"
echo "=========================================="
echo ""
echo "Buscando ext4.vhdx..."

find /mnt/c/Users -name "ext4.vhdx" 2>/dev/null | while read vhdx; do
    size=$(ls -lh "$vhdx" | awk '{print $5}')
    echo "Encontrado: $vhdx"
    echo "Tamanho: $size"
    echo ""
    echo "⚠️  Se este arquivo estiver com muitos GB, você pode compactar:"
    echo "   1. No PowerShell: wsl --shutdown"
    echo "   2. No PowerShell (Admin): Optimize-VHD -Path '$vhdx' -Mode Full"
    echo ""
done

if [ -z "$(find /mnt/c/Users -name 'ext4.vhdx' 2>/dev/null)" ]; then
    echo "Não encontrado nos locais padrão."
    echo "Locais verificados:"
    echo "  - C:\\Users\\*\\AppData\\Local\\Packages\\CanonicalGroupLimited*\\LocalState\\"
    echo ""
fi

# =============================================================================
# 2. TOP DIRETÓRIOS EM C:\
# =============================================================================
echo "=========================================="
echo "2. TOP DIRETÓRIOS EM C:\\ (pode levar 5-10 min)"
echo "=========================================="
echo ""

echo "Analisando diretórios principais..."
du -sh /mnt/c/Users 2>/dev/null &
du -sh /mnt/c/Windows 2>/dev/null &
du -sh /mnt/c/ProgramData 2>/dev/null &
du -sh /mnt/c/'Program Files' 2>/dev/null &
du -sh /mnt/c/'Program Files (x86)' 2>/dev/null &
wait

echo ""
echo "Top 15 maiores diretórios em C:\\ (nível 1):"
du -h --max-depth=1 /mnt/c 2>/dev/null | sort -rh | head -15

# =============================================================================
# 3. C:\Users - ANÁLISE DETALHADA
# =============================================================================
echo ""
echo "=========================================="
echo "3. C:\\Users - ANÁLISE DETALHADA"
echo "=========================================="
echo ""

for user_dir in /mnt/c/Users/*/; do
    username=$(basename "$user_dir")

    # Pular diretórios de sistema
    if [[ "$username" == "Public" || "$username" == "Default" || "$username" == "All Users" ]]; then
        continue
    fi

    echo "--------------------"
    echo "Usuário: $username"
    echo "--------------------"

    # Tamanho total
    total_size=$(du -sh "$user_dir" 2>/dev/null | cut -f1)
    echo "Total: $total_size"
    echo ""

    # Subdiretórios principais
    echo "Top 10 subdiretórios:"
    du -h --max-depth=1 "$user_dir" 2>/dev/null | sort -rh | head -10
    echo ""

    # Downloads
    if [ -d "$user_dir/Downloads" ]; then
        downloads_size=$(du -sh "$user_dir/Downloads" 2>/dev/null | cut -f1)
        downloads_count=$(find "$user_dir/Downloads" -type f 2>/dev/null | wc -l)
        echo "📥 Downloads: $downloads_size ($downloads_count arquivos)"
    fi

    # Documents
    if [ -d "$user_dir/Documents" ]; then
        docs_size=$(du -sh "$user_dir/Documents" 2>/dev/null | cut -f1)
        docs_count=$(find "$user_dir/Documents" -type f 2>/dev/null | wc -l)
        echo "📄 Documents: $docs_size ($docs_count arquivos)"
    fi

    # Desktop
    if [ -d "$user_dir/Desktop" ]; then
        desktop_size=$(du -sh "$user_dir/Desktop" 2>/dev/null | cut -f1)
        desktop_count=$(find "$user_dir/Desktop" -type f 2>/dev/null | wc -l)
        echo "🖥️  Desktop: $desktop_size ($desktop_count arquivos)"
    fi

    # AppData
    if [ -d "$user_dir/AppData" ]; then
        appdata_size=$(du -sh "$user_dir/AppData" 2>/dev/null | cut -f1)
        echo "📦 AppData: $appdata_size"

        # AppData subdirs
        echo "   Top 5 em AppData:"
        du -h --max-depth=2 "$user_dir/AppData" 2>/dev/null | sort -rh | head -5
    fi

    echo ""
done

# =============================================================================
# 4. ARQUIVOS GRANDES (>500MB)
# =============================================================================
echo ""
echo "=========================================="
echo "4. ARQUIVOS GRANDES EM C:\\Users (>500MB)"
echo "=========================================="
echo ""

echo "Buscando arquivos grandes (pode levar 10-15 min)..."
find /mnt/c/Users -type f -size +500M 2>/dev/null -exec ls -lh {} \; | \
    awk '{print $5 "\t" $9}' | sort -rh | head -30

# =============================================================================
# 5. PDFs GRANDES (>50MB)
# =============================================================================
echo ""
echo "=========================================="
echo "5. PDFs GRANDES (>50MB) - Faculdade, etc"
echo "=========================================="
echo ""

echo "Buscando PDFs grandes..."
find /mnt/c/Users -type f -name "*.pdf" -size +50M 2>/dev/null -exec ls -lh {} \; | \
    awk '{print $5 "\t" $9}' | sort -rh | head -30

# =============================================================================
# 6. VÍDEOS GRANDES (>100MB)
# =============================================================================
echo ""
echo "=========================================="
echo "6. VÍDEOS GRANDES (>100MB)"
echo "=========================================="
echo ""

echo "Buscando vídeos grandes (.mp4, .avi, .mkv, .mov)..."
find /mnt/c/Users -type f \( -name "*.mp4" -o -name "*.avi" -o -name "*.mkv" -o -name "*.mov" \) -size +100M 2>/dev/null -exec ls -lh {} \; | \
    awk '{print $5 "\t" $9}' | sort -rh | head -30

# =============================================================================
# 7. WINDOWS - DIRETÓRIOS DE SISTEMA
# =============================================================================
echo ""
echo "=========================================="
echo "7. WINDOWS - DIRETÓRIOS DE SISTEMA"
echo "=========================================="
echo ""

echo "Windows Update Cache:"
du -sh /mnt/c/Windows/SoftwareDistribution/Download 2>/dev/null || echo "Sem acesso"

echo ""
echo "Temp do Windows:"
du -sh /mnt/c/Windows/Temp 2>/dev/null || echo "Sem acesso"

echo ""
echo "Lixeira:"
du -sh /mnt/c/'$Recycle.Bin' 2>/dev/null || echo "Sem acesso"

echo ""
echo "WinSxS (Windows Side by Side - backups):"
du -sh /mnt/c/Windows/WinSxS 2>/dev/null || echo "Sem acesso"

echo ""
echo "Logs do Windows:"
du -sh /mnt/c/Windows/Logs 2>/dev/null || echo "Sem acesso"

echo ""
echo "Installer (pacotes MSI/MSP):"
du -sh /mnt/c/Windows/Installer 2>/dev/null || echo "Sem acesso"

# =============================================================================
# 8. PROGRAMAS INSTALADOS
# =============================================================================
echo ""
echo "=========================================="
echo "8. PROGRAMAS INSTALADOS (Top 15)"
echo "=========================================="
echo ""

echo "Program Files:"
du -h --max-depth=1 /mnt/c/'Program Files' 2>/dev/null | sort -rh | head -15

echo ""
echo "Program Files (x86):"
du -h --max-depth=1 /mnt/c/'Program Files (x86)' 2>/dev/null | sort -rh | head -15

# =============================================================================
# 9. OneDrive / Cloud Storage
# =============================================================================
echo ""
echo "=========================================="
echo "9. CLOUD STORAGE (OneDrive, Dropbox, etc)"
echo "=========================================="
echo ""

for user_dir in /mnt/c/Users/*/; do
    username=$(basename "$user_dir")

    if [[ "$username" == "Public" || "$username" == "Default" ]]; then
        continue
    fi

    if [ -d "$user_dir/OneDrive" ]; then
        onedrive_size=$(du -sh "$user_dir/OneDrive" 2>/dev/null | cut -f1)
        echo "OneDrive ($username): $onedrive_size"
    fi

    if [ -d "$user_dir/Dropbox" ]; then
        dropbox_size=$(du -sh "$user_dir/Dropbox" 2>/dev/null | cut -f1)
        echo "Dropbox ($username): $dropbox_size"
    fi

    if [ -d "$user_dir/Google Drive" ]; then
        gdrive_size=$(du -sh "$user_dir/Google Drive" 2>/dev/null | cut -f1)
        echo "Google Drive ($username): $gdrive_size"
    fi
done

# =============================================================================
# 10. ANÁLISE DE EXTENSÕES (Quais tipos de arquivo dominam)
# =============================================================================
echo ""
echo "=========================================="
echo "10. TIPOS DE ARQUIVO MAIS COMUNS (Top 20)"
echo "=========================================="
echo ""

echo "Analisando extensões em C:\\Users..."
find /mnt/c/Users -type f 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20

# =============================================================================
# RESUMO E RECOMENDAÇÕES
# =============================================================================
echo ""
echo "=========================================="
echo "RESUMO E RECOMENDAÇÕES"
echo "=========================================="
echo ""

echo "✅ COMANDOS PARA LIBERAR ESPAÇO (WINDOWS):"
echo ""
echo "1. Limpar Windows Update:"
echo "   PowerShell (Admin):"
echo "   Stop-Service wuauserv"
echo "   Remove-Item C:\\Windows\\SoftwareDistribution\\Download\\* -Recurse -Force"
echo "   Start-Service wuauserv"
echo ""
echo "2. Limpar Lixeira:"
echo "   PowerShell: Clear-RecycleBin -Force"
echo ""
echo "3. Limpar arquivos temporários:"
echo "   PowerShell: Remove-Item C:\\Windows\\Temp\\* -Recurse -Force"
echo ""
echo "4. Disk Cleanup (Limpeza de Disco):"
echo "   cleanmgr /sageset:1"
echo "   cleanmgr /sagerun:1"
echo ""
echo "5. Compactar disco WSL2 (se ext4.vhdx grande):"
echo "   wsl --shutdown"
echo "   Optimize-VHD -Path <caminho-do-vhdx> -Mode Full"
echo ""
echo "6. Ferramentas visuais (recomendado):"
echo "   - WinDirStat: https://windirstat.net/"
echo "   - TreeSize Free: https://www.jam-software.com/treesize_free"
echo ""

echo "=========================================="
echo "DIAGNÓSTICO COMPLETO!"
echo "=========================================="
echo ""
echo "Finalizado: $(date)"
echo "Relatório salvo em: $OUTPUT_FILE"
echo ""
echo "📊 Próximos passos:"
echo "1. Leia o arquivo $OUTPUT_FILE"
echo "2. Identifique os maiores culpados"
echo "3. Execute os comandos de limpeza recomendados"
echo "4. Considere mover arquivos grandes para D:\\ (931GB, apenas 13% usado!)"
echo ""
