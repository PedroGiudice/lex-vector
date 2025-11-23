#!/bin/bash

# Análise rápida focada no Windows C:\
# Criado: 2025-11-21

echo "========================================="
echo "ANÁLISE RÁPIDA - WINDOWS C:\ (91% USADO)"
echo "========================================="
echo ""

echo "1. DISCO VIRTUAL WSL2 (ext4.vhdx):"
echo "-----------------------------------"
# Buscar apenas em locais conhecidos
ls -lh /mnt/c/Users/*/AppData/Local/Packages/CanonicalGroupLimited*/LocalState/ext4.vhdx 2>/dev/null || \
ls -lh /mnt/c/Users/*/AppData/Local/Packages/*/LocalState/ext4.vhdx 2>/dev/null | head -1 || \
echo "Não encontrado nos locais padrão"
echo ""

echo "2. Top Diretórios em C:\ (apenas nível 1, rápido):"
echo "---------------------------------------------------"
# Usar ls ao invés de du (muito mais rápido, mas menos preciso)
ls -lh /mnt/c/ 2>/dev/null | grep "^d" | sort -k5 -hr | head -15
echo ""

echo "3. Diretórios conhecidos por consumir muito espaço:"
echo "----------------------------------------------------"

echo "   Windows Update Cache:"
du -sh /mnt/c/Windows/SoftwareDistribution/Download 2>/dev/null || echo "   Sem acesso"

echo "   Temp do Windows:"
du -sh /mnt/c/Windows/Temp 2>/dev/null || echo "   Sem acesso"

echo "   Lixeira (Recycler/RecycleBin):"
du -sh /mnt/c/'$Recycle.Bin' 2>/dev/null || echo "   Sem acesso"

echo "   Arquivos de hibernação:"
ls -lh /mnt/c/hiberfil.sys 2>/dev/null || echo "   Não encontrado"
ls -lh /mnt/c/pagefile.sys 2>/dev/null || echo "   Não encontrado"

echo ""
echo "4. Top 20 maiores arquivos em C:\Users (>500MB):"
echo "-------------------------------------------------"
timeout 60 find /mnt/c/Users -type f -size +500M 2>/dev/null -exec ls -lh {} \; | \
    awk '{print $5 "\t" $9}' | sort -rh | head -20 || echo "Timeout ou sem acesso"

echo ""
echo "5. Downloads, Documents, Desktop (locais comuns para PDFs):"
echo "------------------------------------------------------------"
for user_dir in /mnt/c/Users/*/; do
    username=$(basename "$user_dir")
    echo "Usuário: $username"

    if [ -d "$user_dir/Downloads" ]; then
        downloads_size=$(du -sh "$user_dir/Downloads" 2>/dev/null | cut -f1)
        downloads_count=$(find "$user_dir/Downloads" -type f 2>/dev/null | wc -l)
        echo "  Downloads: $downloads_size ($downloads_count arquivos)"
    fi

    if [ -d "$user_dir/Documents" ]; then
        docs_size=$(du -sh "$user_dir/Documents" 2>/dev/null | cut -f1)
        docs_count=$(find "$user_dir/Documents" -type f 2>/dev/null | wc -l)
        echo "  Documents: $docs_size ($docs_count arquivos)"
    fi

    if [ -d "$user_dir/Desktop" ]; then
        desktop_size=$(du -sh "$user_dir/Desktop" 2>/dev/null | cut -f1)
        desktop_count=$(find "$user_dir/Desktop" -type f 2>/dev/null | wc -l)
        echo "  Desktop: $desktop_size ($desktop_count arquivos)"
    fi

    echo ""
done

echo "6. Buscar PDFs grandes (>50MB) em C:\Users:"
echo "--------------------------------------------"
timeout 60 find /mnt/c/Users -type f -name "*.pdf" -size +50M 2>/dev/null -exec ls -lh {} \; | \
    awk '{print $5 "\t" $9}' | sort -rh | head -20 || echo "Timeout ou sem acesso"

echo ""
echo "========================================="
echo "RECOMENDAÇÕES IMEDIATAS:"
echo "========================================="
echo ""
echo "1. Limpar Windows Update cache (pode liberar 5-20GB):"
echo "   No PowerShell (Admin): "
echo "   Stop-Service wuauserv"
echo "   Remove-Item C:\Windows\SoftwareDistribution\Download\* -Recurse -Force"
echo "   Start-Service wuauserv"
echo ""
echo "2. Limpar Lixeira:"
echo "   No PowerShell: Clear-RecycleBin -Force"
echo ""
echo "3. Compactar disco WSL2 (se ext4.vhdx estiver grande):"
echo "   No PowerShell:"
echo "   wsl --shutdown"
echo "   Optimize-VHD -Path '<caminho-do-ext4.vhdx>' -Mode Full"
echo ""
echo "4. Analisar com ferramenta visual no Windows:"
echo "   - WinDirStat: https://windirstat.net/"
echo "   - TreeSize Free: https://www.jam-software.com/treesize_free"
echo ""
