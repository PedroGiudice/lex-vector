import os
from pathlib import Path

# Configuração de Saída
OUTPUT_FILE = "CONTEXTO_COMPLETO_PROJETO.txt"

# O que incluir (Extensões e Nomes Específicos)
EXTENSIONS = {'.py', '.md', '.json', '.txt', '.ini', '.sh'}
INCLUDE_FILES = {'requirements.txt', 'Dockerfile', '.gitignore'}

# O que IGNORAR (Pastas de sistema/lixo)
IGNORE_DIRS = {
    '.git', '.venv', 'venv', 'env', '__pycache__', 
    'outputs', 'scans', 'site-packages', 'node_modules', 
    '.pytest_cache', 'dist', 'build'
}

def pack_project():
    root_path = Path('.')
    count = 0
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write("# CONTEXTO TOTAL DO PROJETO LEGAL-TEXT-EXTRACTOR\n")
        out.write(f"# Data: {os.environ.get('USER', 'User')} | WSL2 Environment\n\n")
        
        # Percorre tudo recursivamente
        for path in root_path.rglob('*'):
            # 1. Ignorar pastas proibidas
            if any(part in IGNORE_DIRS for part in path.parts):
                continue
            
            # 2. Ignorar arquivos de saída do script
            if path.name in {'pack_context.py', OUTPUT_FILE}:
                continue
                
            # 3. Verificar se é arquivo válido (Extensão ou Nome Exato)
            is_valid_ext = path.suffix in EXTENSIONS
            is_valid_name = path.name in INCLUDE_FILES
            
            if path.is_file() and (is_valid_ext or is_valid_name):
                try:
                    # Tenta ler como texto
                    content = path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Formatação clara para o LLM
                    out.write(f"\n{'='*60}\n")
                    out.write(f"FILE PATH: {path.as_posix()}\n")
                    out.write(f"{'='*60}\n")
                    out.write(content + "\n")
                    
                    print(f"✅ Adicionado: {path}")
                    count += 1
                except Exception as e:
                    print(f"❌ Erro ao ler {path}: {e}")

    print(f"\n🎉 SUCESSO! {count} arquivos compactados em: {OUTPUT_FILE}")

if __name__ == "__main__":
    pack_project()