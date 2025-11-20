#!/bin/bash
# Setup Completo do Sistema de Jurisprudência Collector
# Autor: Claude Code (Sonnet 4.5)
# Data: 2025-11-20

set -e  # Parar em caso de erro

echo "============================================================"
echo "SETUP COMPLETO - Sistema de Jurisprudência Collector"
echo "============================================================"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar localização
echo "${YELLOW}[1/8]${NC} Verificando localização..."
EXPECTED_DIR="/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/agentes/jurisprudencia-collector"
if [ "$PWD" != "$EXPECTED_DIR" ]; then
    echo "❌ ERRO: Execute este script do diretório correto:"
    echo "   cd $EXPECTED_DIR"
    exit 1
fi
echo "✅ Localização correta"
echo ""

# 2. Criar virtual environment
echo "${YELLOW}[2/8]${NC} Criando virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✅ Virtual environment criado"
else
    echo "✅ Virtual environment já existe"
fi
echo ""

# 3. Ativar venv
echo "${YELLOW}[3/8]${NC} Ativando virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment ativado"
echo ""

# 4. Atualizar pip
echo "${YELLOW}[4/8]${NC} Atualizando pip..."
pip install --quiet --upgrade pip
echo "✅ Pip atualizado"
echo ""

# 5. Instalar dependências
echo "${YELLOW}[5/8]${NC} Instalando dependências..."
echo "   Isso pode levar alguns minutos (download de modelos RAG ~500 MB)..."
pip install --quiet -r requirements.txt
echo "✅ Dependências instaladas"
echo ""

# 6. Criar estrutura de diretórios
echo "${YELLOW}[6/8]${NC} Criando estrutura de diretórios..."
mkdir -p data/db
mkdir -p data/downloads
mkdir -p data/cadernos
mkdir -p logs
mkdir -p cache/embeddings
echo "✅ Diretórios criados"
echo ""

# 7. Inicializar banco de dados
echo "${YELLOW}[7/8]${NC} Inicializando banco de dados SQLite..."
if [ ! -f "data/db/jurisprudencia.db" ]; then
    sqlite3 data/db/jurisprudencia.db < schema.sql
    echo "✅ Banco de dados criado e inicializado"
else
    echo "⚠️  Banco de dados já existe, pulando inicialização"
    read -p "Deseja recriar o banco? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm data/db/jurisprudencia.db
        sqlite3 data/db/jurisprudencia.db < schema.sql
        echo "✅ Banco de dados recriado"
    else
        echo "✅ Banco existente mantido"
    fi
fi
echo ""

# 8. Validar instalação
echo "${YELLOW}[8/8]${NC} Validando instalação..."

# Testar imports
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

try:
    from downloader import DJENDownloader
    from processador_texto import processar_publicacao
    from rag import Embedder, Chunker, SemanticSearch
    print("✅ Todos os módulos importados com sucesso")
except ImportError as e:
    print(f"❌ ERRO ao importar módulos: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Validação falhou"
    exit 1
fi
echo ""

# 9. Executar teste básico
echo "${YELLOW}[TESTE]${NC} Executando teste básico..."
python3 test_basic_downloader.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Teste básico passou"
else
    echo "⚠️  Teste básico falhou (opcional, pode ser ignorado)"
fi
echo ""

# 10. Exibir resumo
echo "============================================================"
echo "${GREEN}INSTALAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
echo "============================================================"
echo ""
echo "📊 Estatísticas:"
echo "   - Virtual environment: .venv ($(du -sh .venv | cut -f1))"
echo "   - Banco de dados: data/db/jurisprudencia.db"
echo "   - Cache embeddings: cache/embeddings/"
echo "   - Logs: logs/"
echo ""
echo "🚀 Próximos Passos:"
echo ""
echo "1. Executar download imediato:"
echo "   ./run_scheduler.sh --now"
echo ""
echo "2. Executar em background:"
echo "   ./run_scheduler.sh --now &"
echo "   ./run_scheduler.sh --status"
echo ""
echo "3. Configurar systemd (produção):"
echo "   sudo nano /etc/systemd/system/jurisprudencia-scheduler.service"
echo "   (Veja SCHEDULER_README.md para template)"
echo ""
echo "4. Consultar documentação:"
echo "   cat docs/INDEX.md"
echo "   cat docs/QUICK_START.md"
echo ""
echo "5. Testar busca semântica:"
echo "   python exemplo_rag.py"
echo ""
echo "============================================================"
echo ""
echo "Para reativar o ambiente futuramente:"
echo "   source .venv/bin/activate"
echo ""
