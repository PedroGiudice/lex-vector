# Quickstart - Legal RAG System

Guia rápido para começar a usar o sistema em 5 minutos.

## 1. Setup Inicial (2 minutos)

```bash
# Navegar para o diretório
cd agentes/legal-rag

# Criar ambiente virtual
python -m venv .venv

# Ativar (Linux/Mac)
source .venv/bin/activate

# Ativar (Windows)
.venv\Scripts\activate

# Instalar dependências essenciais
pip install anthropic sentence-transformers chromadb langchain tiktoken loguru pydantic python-dotenv

# Baixar modelo spaCy (português)
python -m spacy download pt_core_news_sm
```

## 2. Configurar API Key (30 segundos)

```bash
# Criar arquivo .env
echo "ANTHROPIC_API_KEY=sua_chave_aqui" > .env
```

## 3. Testar Configuração (30 segundos)

```python
# test_setup.py
from config.settings import get_settings
from config.embeddings_models import get_embedding_model

# Carregar settings
settings = get_settings()
print(f"✓ Settings carregadas: {settings.project_name}")

# Testar modelo de embeddings (modo rápido)
model = get_embedding_model("fast", device="cpu")
print(f"✓ Modelo embeddings carregado: {model.get_sentence_embedding_dimension()}d")

# Testar encoding
text = "Teste de embedding jurídico"
embedding = model.encode([text])
print(f"✓ Embedding gerado: shape {embedding.shape}")

print("\n✅ Setup completo!")
```

Execute:
```bash
python test_setup.py
```

## 4. Indexar Primeiro Acórdão (2 minutos)

```python
# exemplo_indexacao.py
from indexing.models import AcordaoMetadata
from datetime import datetime
from pathlib import Path

# Preparar metadata
metadata = AcordaoMetadata(
    tribunal="STF",
    processo_numero="1234567-89.2024.1.00.0000",
    classe_processual="RE",
    relator="Min. Exemplo",
    data_julgamento=datetime(2024, 1, 15),
    data_publicacao=datetime(2024, 1, 20),
    orgao_julgador="Primeira Turma",
    area_direito="Constitucional",
    assunto_principal="Direitos Fundamentais",
    ementa="Exemplo de ementa jurídica sobre direitos fundamentais..."
)

# Texto exemplo
texto = """
EMENTA: DIREITO CONSTITUCIONAL. LIBERDADE DE EXPRESSÃO.

1. A liberdade de expressão é um dos pilares fundamentais da democracia,
encontrando amparo no art. 5º, IV e IX, da Constituição Federal de 1988.

2. O exercício desse direito não é absoluto, devendo ser harmonizado
com outros direitos fundamentais, especialmente a dignidade da pessoa humana.

3. Recurso conhecido e provido.
"""

print("Metadata:")
print(f"  Tribunal: {metadata.tribunal}")
print(f"  Processo: {metadata.processo_numero}")
print(f"  Relator: {metadata.relator}")
print(f"\nTexto: {len(texto)} caracteres")
print("\n✓ Pronto para indexação!")
```

## 5. Próximos Passos

### Implementação Completa

Para usar o sistema completo, você precisa implementar os módulos restantes:

1. **Pipeline de Indexação** (`indexing/pipeline.py`)
2. **Retrieval Híbrido** (`retrieval/hybrid_retriever.py`)
3. **Gerador RAG** (`generation/rag_generator.py`)

Veja a especificação técnica completa para detalhes de implementação.

### Alternativa: Versão Simplificada

Para começar rapidamente, você pode usar uma versão simplificada:

```python
# rag_simples.py
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import anthropic
import os

# 1. Setup
client_chroma = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_db"
))

collection = client_chroma.get_or_create_collection("test")
model = SentenceTransformer('paraphrase-xlm-r-multilingual-v1')

# 2. Indexar
texto = "A liberdade de expressão é garantida pela Constituição."
embedding = model.encode([texto])[0]

collection.add(
    ids=["doc1"],
    embeddings=[embedding.tolist()],
    documents=[texto],
    metadatas=[{"tribunal": "STF"}]
)

print("✓ Documento indexado!")

# 3. Buscar
query = "direitos fundamentais constituição"
query_emb = model.encode([query])[0]

results = collection.query(
    query_embeddings=[query_emb.tolist()],
    n_results=1
)

print(f"\n✓ Resultado encontrado: {results['documents'][0][0]}")

# 4. Gerar resposta (opcional - requer API key)
if os.getenv("ANTHROPIC_API_KEY"):
    client_ai = anthropic.Anthropic()

    prompt = f"""Responda com base neste contexto:

    {results['documents'][0][0]}

    Pergunta: {query}
    """

    response = client_ai.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    print(f"\n✓ Resposta: {response.content[0].text}")
```

## Troubleshooting Rápido

### Erro: ModuleNotFoundError

```bash
# Reinstale dependências
pip install -r requirements.txt
```

### Erro: ANTHROPIC_API_KEY not found

```bash
# Verifique o .env
cat .env

# Exporte manualmente
export ANTHROPIC_API_KEY=sua_chave
```

### Erro: GPU not found (CUDA)

```python
# Force CPU mode
device = "cpu"
model = get_embedding_model("fast", device="cpu")
```

## Recursos

- **README.md**: Documentação completa
- **config.json**: Configurações detalhadas
- **Especificação técnica**: Documento de implementação completo
- **CLAUDE.md**: Regras arquiteturais do projeto

## Suporte

Para dúvidas ou problemas:
1. Verifique a documentação completa
2. Consulte a especificação técnica
3. Revise os exemplos de código
