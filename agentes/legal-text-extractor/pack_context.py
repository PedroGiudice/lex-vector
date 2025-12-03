import os
from pathlib import Path
import sys

# Configuração de Saída
OUTPUT_FILE = "CONTEXTO_COMPLETO_PROJETO.txt"

# Extensões e Arquivos
EXTENSIONS = {'.py', '.md', '.json', '.txt', '.ini', '.sh', '.yml'}
INCLUDE_FILES = {'requirements.txt', 'Dockerfile', '.gitignore'}
IGNORE_DIRS = {
    '.git', '.venv', 'venv', 'env', '__pycache__', 
    'outputs', 'scans', 'site-packages', 'node_modules', 
    '.pytest_cache', 'dist', 'build', '.vscode', '.idea'
}

def safe_print(msg):
    """Imprime ignorando erros de encoding do terminal"""
    try:
        print(msg)
    except Exception:
        pass

def pack_project():
    root_path = Path('.')
    count = 0
    errors = 0
    
    # Abre o arquivo de saída em modo UTF-8 forçado
    with open(OUTPUT_FILE, 'w', encoding='utf-8', errors='replace') as out:
        out.write(f"# CONTEXTO TOTAL DO PROJETO LEGAL-TEXT-EXTRACTOR\n")
        
        for path in root_path.rglob('*'):
            try:
                # 1. Filtros básicos
                if any(part in IGNORE_DIRS for part in path.parts):
                    continue
                if path.name in {'pack_context.py', 'pack_safe.py', OUTPUT_FILE}:
                    continue
                if not path.is_file():
                    continue

                # 2. Verifica extensão
                is_valid = (path.suffix in EXTENSIONS) or (path.name in INCLUDE_FILES)
                
                if is_valid:
                    # Lê conteúdo forçando ignorar erros de decode
                    content = path.read_text(encoding='utf-8', errors='replace')
                    
                    # Escreve no arquivo final
                    out.write(f"\n{'='*60}\n")
                    out.write(f"FILE PATH: {path.as_posix()}\n")
                    out.write(f"{'='*60}\n")
                    out.write(content + "\n")
                    
                    count += 1
                    safe_print(f"[OK] {path.name}")
                    
            except Exception as e:
                errors += 1
                safe_print(f"[ERRO] Falha ao ler {path.name}: {e}")

    safe_print(f"\n--- CONCLUIDO ---")
    safe_print(f"Arquivos processados: {count}")
    safe_print(f"Erros ignorados: {errors}")
    safe_print(f"Arquivo gerado: {OUTPUT_FILE}")

if __name__ == "__main__":
    pack_project()