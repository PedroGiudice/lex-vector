# Legal Lens

Sistema RAG (Retrieval-Augmented Generation) para análise de documentos jurídicos e extração de jurisprudência por tema.

## 🎯 Propósito

Processa PDFs jurídicos baixados pelo **oab-watcher**, cria embeddings semânticos, indexa em vector database e permite:

- Busca semântica avançada em milhares de documentos
- Extração automática de jurisprudência por temas jurídicos
- Análise estruturada de decisões, acórdãos e publicações
- Relatórios consolidados de jurisprudência

## 🚀 Funcionalidades

### ✅ Implementadas

- [x] **Processamento de PDFs jurídicos**
  - Extração de texto via PyPDF2 e pdfplumber
  - Chunking inteligente com overlap
  - Preservação de metadata (tribunal, data, página)

- [x] **Sistema RAG completo**
  - Vector database com ChromaDB
  - Embeddings multilíngues (Sentence-Transformers)
  - Busca semântica com filtros de metadata
  - Similaridade por cosine distance

- [x] **Extração de jurisprudência**
  - Classificação automática por temas jurídicos
  - Extração de campos estruturados:
    - Número de processo
    - Tribunal e vara
    - Tipo de decisão (sentença, acórdão, etc)
    - Partes do processo
    - Ementa e dispositivo
  - Confidence scoring

- [x] **Interface interativa (CLI)**
  - Menu completo com 10+ opções
  - Indexação batch de PDFs
  - Busca semântica livre
  - Extração por tema específico ou todos os temas
  - Estatísticas e relatórios
  - Exportação JSON

### 📋 Temas Jurídicos Suportados

1. Direito Civil
2. Direito Penal
3. Direito Trabalhista
4. Direito Tributário
5. Direito Administrativo
6. Direito Constitucional
7. Direito Processual Civil
8. Direito Processual Penal
9. Responsabilidade Civil
10. Contratos
11. Família e Sucessões
12. Consumidor
13. Propriedade Intelectual

## 📦 Instalação

### Pré-requisitos

- Python 3.10+
- HD externo montado em `E:\` (para dados)
- PDFs já baixados pelo **oab-watcher**

### Setup

```powershell
# 1. Navegar para o diretório do agente
cd C:\claude-work\repos\Claude-Code-Projetos\agentes\legal-lens

# 2. Criar ambiente virtual
python -m venv .venv

# 3. Ativar ambiente virtual
.venv\Scripts\activate

# 4. Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# 5. Criar estrutura de dados
mkdir E:\claude-code-data\agentes\legal-lens\processed
mkdir E:\claude-code-data\agentes\legal-lens\vector_db
mkdir E:\claude-code-data\agentes\legal-lens\logs
mkdir E:\claude-code-data\agentes\legal-lens\outputs
mkdir E:\claude-code-data\agentes\legal-lens\cache
```

## 🎮 Uso

### Via PowerShell Script (Recomendado)

```powershell
.\run_agent.ps1
```

### Via Linha de Comando Manual

```powershell
.venv\Scripts\activate
python main.py
```

## 📚 Workflow Completo

### 1️⃣ Baixar Cadernos com oab-watcher

```powershell
cd ..\oab-watcher
.\run_agent.ps1
# Escolher opção 3: Download massivo de cadernos
# Ex: TJSP, 2025-01-01 a 2025-01-31
```

### 2️⃣ Indexar PDFs no Legal Lens

```powershell
cd ..\legal-lens
.\run_agent.ps1
# Escolher opção 1: Indexar PDFs no vector database
```

**O que acontece:**
- Legal Lens lê PDFs de `E:\claude-code-data\agentes\oab-watcher\downloads\cadernos\`
- Extrai texto página por página
- Divide em chunks de ~1000 caracteres com overlap de 200
- Gera embeddings com modelo multilíngue
- Indexa no ChromaDB (vector database persistente)

### 3️⃣ Buscar e Extrair Jurisprudência

```powershell
# Opção 4: Busca semântica livre
# Ex: "responsabilidade civil médica erro cirúrgico"

# Opção 5: Extrair jurisprudência por tema
# Ex: Tema 9 (Responsabilidade Civil), top 20 resultados

# Opção 6: Extrair todos os temas
# Gera relatório completo com estatísticas
```

**Resultado:**
- Entradas de jurisprudência estruturadas
- Confidence scores
- Exportação JSON
- Relatórios consolidados por tema

## 🔧 Configuração

Edite `config.json` para customizar:

```json
{
  "rag": {
    "embedding_model": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "top_k_results": 5,
    "similarity_threshold": 0.7
  },
  "extraction": {
    "temas_interesse": [...],
    "min_confidence": 0.6,
    "extract_fields": [...]
  }
}
```

## 📊 Estrutura de Dados

### Vector Database

```
E:\claude-code-data\agentes\legal-lens\vector_db\
└── chroma.sqlite3  # ChromaDB persistente
```

### Outputs

```
E:\claude-code-data\agentes\legal-lens\outputs\
├── jurisprudencia_responsabilidade_civil_20250108_143022.json
├── jurisprudencia_direito_penal_20250108_143022.json
└── relatorio_completo_20250108_143022.json
```

### Formato JSON de Jurisprudência

```json
{
  "numero_processo": "1234567-89.2024.1.00.0001",
  "tribunal": "TJSP",
  "vara": "3ª Vara Cível",
  "data_publicacao": "2025-01-08",
  "tipo_decisao": "sentença",
  "tema": "responsabilidade civil",
  "ementa": "...",
  "dispositivo": "...",
  "partes": ["João da Silva", "Maria Santos"],
  "texto_completo": "...",
  "source_file": "TJSP_2025-01-08_caderno.pdf",
  "page_number": 42,
  "confidence": 0.87
}
```

## 🧪 Testes

```powershell
.venv\Scripts\activate
pytest tests/
```

## 📈 Performance

- **Indexação:** ~50-100 PDFs/hora (depende do hardware)
- **Busca semântica:** <1 segundo para 10k documentos
- **Extração de jurisprudência:** ~2-5 segundos por tema

## 🛠️ Tecnologias

- **PDF Processing:** PyPDF2, pdfplumber
- **Vector Database:** ChromaDB (SQLite + HNSW)
- **Embeddings:** Sentence-Transformers (multilingual)
- **RAG Framework:** LangChain (opcional)
- **Data Models:** Pydantic

## 🔗 Integração com Outros Agentes

### oab-watcher
- **Input:** PDFs em `E:\claude-code-data\agentes\oab-watcher\downloads\cadernos\`
- **Metadata:** Tribunal, data (extraídos do filename)

### djen-tracker (futuro)
- **Input:** Monitoramento contínuo de novas publicações
- **Output:** Auto-indexação incremental

## 📝 Logs

```
E:\claude-code-data\agentes\legal-lens\logs\
└── legal_lens_20250108_143022.log
```

## 🚨 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'chromadb'"

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

### Erro: "Nenhum PDF encontrado"

Certifique-se de que o **oab-watcher** já baixou cadernos:

```powershell
dir E:\claude-code-data\agentes\oab-watcher\downloads\cadernos\
```

### Erro: "Out of memory" durante indexação

Reduza `batch_size` em `config.json`:

```json
{
  "processing": {
    "batch_size": 5,  // Reduzir de 10 para 5
    "max_concurrent": 2  // Reduzir paralelismo
  }
}
```

### Vector Database corrompido

```powershell
# Resetar database (ATENÇÃO: apaga tudo!)
# No menu do Legal Lens, escolher opção 10
```

## 📄 Licença

MIT License

## 👤 Autor

PedroGiudice - 2025

## 🔄 Status

🟢 **Implementado e funcional** - Pronto para uso em produção
