# APIs para Jurisprudência Brasileira: Análise Comparativa

## DIFERENÇA CRÍTICA: METADADOS vs. CONTEÚDO JURISPRUDENCIAL

### Metadados Processuais (DataJud)
O DataJud fornece apenas a **"capa"** do processo. Informações administrativas e estruturais:
- Número do processo (CNJ único)
- Classe processual (código TPU)
- Partes (CPF/CNPJ parcialmente anonimizados, OABs)
- Órgão julgador
- Movimentações (timestamps e códigos de movimento)
- Assuntos (códigos TPU)
- Grau, nível de sigilo, sistema de origem

**Ausente**: Texto completo das decisões, ementas, votos, relatórios, fundamentos jurídicos.

### Conteúdo Jurisprudencial Completo
O que você precisa para análise de raciocínio jurídico:
- **Ementas**: Resumo oficial da decisão com tese jurídica
- **Acórdãos completos (inteiro teor)**: Relatório + voto + ementa + dispositivo
- Decisões monocráticas
- Súmulas e precedentes qualificados
- Fundamentação jurídica completa

---

## PANORAMA DAS APIs DISPONÍVEIS

### 1. API DataJud (CNJ) ⚠️ NÃO ATENDE SEU CASO

**URL**: https://api-publica.datajud.cnj.jus.br/api_publica_[tribunal]/_search  
**Autenticação**: Chave pública gratuita (sem cadastro)  
**Cobertura**: 91 tribunais nacionais  
**Atualização**: Diária (obrigatória por Res. CNJ 331/2020)

**Formato de retorno**: JSON estruturado via Elasticsearch

**Limitação crítica**: APENAS metadados processuais. Não fornece ementas nem inteiros teores de acórdãos.

**Caso de uso**: Acompanhamento processual, análise de movimentações, filtros por classe/assunto, estatísticas judiciais.

---

### 2. STJ Dados Abertos ✅ MELHOR OPÇÃO GRATUITA

**URL**: https://dadosabertos.web.stj.jus.br/  
**Autenticação**: Não requer (dados públicos)  
**Cobertura**: Superior Tribunal de Justiça  
**Atualização**: **Diária** (arquivos disponibilizados dia seguinte à publicação no DJe)

#### Datasets Disponíveis:

**A) Íntegras de Decisões Terminativas e Acórdãos do DJe**
- **Conteúdo**: Texto completo das decisões + metadados
- **Formato**: ZIP (textos) + JSON (metadados) + CSV (dicionário)
- **Estrutura**: Arquivos mensais consolidados + arquivos diários incrementais
- **Período**: Desde fevereiro/2022 até data atual
- **Nomenclatura**: AAAAMMDD.zip / metadadosAAAAMMDD.json

**B) Espelhos de Acórdãos por Órgão Julgador**
- Corte Especial, Primeira Seção, Segunda Seção, Terceira Seção
- Primeira Turma até Sexta Turma
- **Formato**: ZIP contendo arquivos JSON
- **Conteúdo**: Ementa, decisão, legislação citada, doutrina, indexação
- **Atualização**: Mensal com arquivos incrementais

#### Vantagens Técnicas:
1. **JSON estruturado**: Parsing simples, token efficiency para LLMs
2. **Metadados ricos**: Ministro relator, órgão julgador, data julgamento/publicação
3. **Dicionário de dados**: CSV com especificação de todos os campos
4. **Formato aberto**: Processável por máquina (Python/R/Node.js)
5. **Gratuito e ilimitado**: Sem API key, sem rate limits, download direto via HTTP

#### Estrutura de um JSON de metadados (exemplo):
```json
{
  "processo": "REsp 1234567/SP",
  "ministro_relator": "Nome do Ministro",
  "orgao_julgador": "Primeira Turma",
  "data_julgamento": 1234567890000,
  "data_publicacao": 1234567890000,
  "classe": "Recurso Especial",
  "assunto": "Direito Civil",
  "id_documento": "unique_id",
  "arquivo_texto": "REsp_1234567.txt"
}
```

**Limitação**: Apenas STJ. Não cobre STF, TJs, TRFs, TRTs.

---

### 3. STF - Sem API Estruturada ⚠️ APENAS PORTAIS HTML

**Portal de Pesquisa**: https://jurisprudencia.stf.jus.br/  
**Inteiro Teor**: https://portal.stf.jus.br/jurisprudencia/pesquisarInteiroTeor.asp

**Recursos**:
- Pesquisa por palavra-chave, número de processo, ministro relator
- Filtros por órgão julgador, data, repercussão geral
- Busca em inteiro teor (acórdãos de 2012+)
- Exportação de resultados em CSV

**Problema**: Não há API REST para download em massa. Acesso apenas via:
- Interface web HTML
- Consulta individual por processo
- Exportação limitada de resultados de busca

**Workaround**: Web scraping (complexo, sujeito a CAPTCHAs, mudanças no HTML).

---

### 4. Tribunais Estaduais - Fragmentado

**TJSP, TJRJ, TJMG, TJRS, etc.**:
- Maioria não possui API pública para jurisprudência
- Dados Abertos (quando existem): Focam em metadados administrativos, não jurisprudência
- Portais de consulta: HTML, sem estruturação para download em massa

**Exceção**: Alguns tribunais (TJAM, TJPE) aderem ao DataJud mas este continua sem fornecer inteiros teores.

---

### 5. APIs Comerciais

#### Jusbrasil API
- **Cobertura**: Todos os tribunais (STF, STJ, TJs, TRFs, TRTs)
- **Conteúdo**: Ementas + inteiros teores quando disponíveis
- **Formato**: JSON via REST
- **Pricing**: Pay-per-use ou contratos enterprise
- **Vantagem**: Agregador único, normalização de dados, enriquecimento

#### Escavador API
- Similar ao Jusbrasil
- R$ 9,90/mês (plano básico) ou API comercial
- Ementas + inteiros teores + análise jurisprudencial

#### JUDIT / Turivius / Codilo
- Soluções comerciais especializadas
- Jurimetria integrada, IA para análise
- Pricing mais alto (R$ 169/mês+)

**Trade-off**: Custo vs. cobertura completa e conveniência.

---

## RECOMENDAÇÃO PARA SEU CASO DE USO

### Para Base de Dados de Ementas e Acórdãos Completos:

#### Opção 1: STJ Dados Abertos (Gratuita - Melhor para começar)

**Implementação**:
```python
import requests
import zipfile
import json
from datetime import datetime

# 1. Baixar arquivo diário de íntegras + metadados
base_url = "https://dadosabertos.web.stj.jus.br/dataset/integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica/resource/"

# Exemplo: dados de 15/03/2024
data = "20240315"
zip_url = f"{base_url}{resource_id}/download/{data}.zip"
json_url = f"{base_url}{resource_id}/download/metadados{data}.json"

# 2. Download e extração
zip_response = requests.get(zip_url)
with open(f"{data}.zip", 'wb') as f:
    f.write(zip_response.content)

# 3. Extração de textos
with zipfile.ZipFile(f"{data}.zip", 'r') as zip_ref:
    zip_ref.extractall(f"textos_{data}/")

# 4. Carregar metadados
metadados = requests.get(json_url).json()

# 5. Processar para base de dados
for doc in metadados:
    processo = doc['processo']
    arquivo_texto = doc['arquivo_texto']
    ementa = doc.get('ementa', '')
    
    # Ler inteiro teor
    with open(f"textos_{data}/{arquivo_texto}", 'r') as f:
        inteiro_teor = f.read()
    
    # Inserir no banco de dados / indexar no Elasticsearch
    # ...
```

**Estratégia de Coleta**:
1. **Carga inicial**: Baixar arquivos mensais consolidados (fev/2022 - presente)
2. **Atualização**: Script diário para baixar arquivo do dia anterior
3. **Armazenamento**: PostgreSQL + Elasticsearch ou MongoDB
4. **Volume estimado**: ~50-100 MB/dia compactado

**Processamento para LLM**:
1. Expandir códigos TPU para descrições legíveis
2. Normalizar datas para ISO 8601
3. Extrair seções estruturadas: ementa / relatório / voto / decisão
4. Chunking inteligente (máx 8k tokens por chunk)
5. Metadados + texto completo em JSON

#### Opção 2: STJ Dados Abertos + Web Scraping STF (Híbrida)

**Para cobrir ambos tribunais superiores**:
- STJ: API estruturada (conforme acima)
- STF: Scraping do portal de pesquisa + inteiro teor

**Complexidade adicional**:
- Selenium/Playwright para navegação automatizada
- Bypass de CAPTCHAs (se implementados)
- Rate limiting ético (10-20s entre requests)
- Manutenção contínua (20-30% do tempo de dev inicial)

#### Opção 3: API Comercial (Escalável - Para produção)

**Quando justifica**:
- Necessidade de cobertura nacional completa (todos os TJs + TRFs + TRTs)
- SLA garantido para aplicação crítica
- Volume > 10.000 consultas/mês
- Equipe pequena sem recursos para manutenção de scrapers

**Recomendação**: Jusbrasil API ou Escavador API
- Formato JSON padronizado
- Cobertura completa
- Atualização diária
- Sem overhead de manutenção

---

## COMPARATIVO TÉCNICO

| Critério | DataJud | STJ Dados Abertos | STF Portal | APIs Comerciais |
|----------|---------|-------------------|------------|-----------------|
| **Ementas completas** | ❌ | ✅ | ✅ (via scraping) | ✅ |
| **Inteiros teores** | ❌ | ✅ | ✅ (via scraping) | ✅ |
| **Formato estruturado** | ✅ JSON | ✅ JSON | ❌ HTML | ✅ JSON |
| **Cobertura** | 91 tribunais | STJ | STF | Nacional |
| **Custo** | Gratuito | Gratuito | Gratuito | R$ 10-500/mês |
| **API REST** | ✅ | ✅ (download) | ❌ | ✅ |
| **Atualização** | Diária | Diária | Diária | Diária |
| **Manutenção requerida** | Baixa | Mínima | Alta | Mínima |
| **Rate limits** | 10k/req | Nenhum | N/A | Variável |
| **Ideal para LLM** | ❌ | ✅ | ⚠️ | ✅ |

---

## ARQUITETURA RECOMENDADA PARA SEU SISTEMA LEGAL-BRANIAC

### Pipeline de Ingestão de Jurisprudência

```
┌─────────────────────────┐
│  STJ Dados Abertos      │
│  (Íntegras + Ementas)   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  ETL Processor          │
│  - Descompactação       │
│  - Parsing JSON         │
│  - Normalização         │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Document Processor     │
│  - Expansão códigos TPU │
│  - Extração seções      │
│  - Chunking p/ LLM      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Vector Database        │
│  (Elasticsearch/Pinecone)│
│  - Embeddings           │
│  - Metadados            │
│  - Full-text search     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Legal-Braniac Agents   │
│  - Jurisprudence        │
│    Cartographer         │
│  - Hermeneutic          │
│    Interpreter          │
└─────────────────────────┘
```

### Stack Técnica Sugerida

**Coleta**:
- Python 3.11+ com `requests`, `zipfile`, `json`
- Schedule diário via cron/Airflow

**Armazenamento**:
- PostgreSQL: Metadados estruturados
- Elasticsearch 8+: Full-text search + embeddings vetoriais
- Alternativa: Weaviate, Pinecone, Qdrant

**Processamento**:
- Pandas para manipulação de dados
- SpaCy + BERTimbau para NER jurídico
- LangChain para chunking e embeddings
- Claude API para análise semântica

**Estimativa de Volume**:
- STJ desde 2022: ~50 GB descompactado
- Taxa de crescimento: ~1-2 GB/mês
- Recomendado: 100 GB storage + 50 GB working space

---

## CONCLUSÃO

### Resposta Direta à Sua Pergunta

**Melhor API para angariar larga base de ementas e íntegras de acórdãos:**

1. **Curto prazo / Proof of Concept**: **STJ Dados Abertos**
   - Gratuita
   - Estruturada (JSON)
   - Ementas + inteiros teores completos
   - Atualização diária
   - Zero configuração (download direto via HTTP)

2. **Médio prazo / Produção com orçamento**: **API Comercial** (Jusbrasil ou Escavador)
   - Cobertura nacional completa
   - SLA garantido
   - Normalização de dados
   - Custo-benefício superior ao desenvolvimento in-house

3. **Longo prazo / Solução customizada**: **Híbrido**
   - STJ Dados Abertos (base sólida gratuita)
   - Scraping complementar para STF e TJs prioritários
   - API comercial para gaps críticos

### Ação Imediata

Comece implementando ETL para STJ Dados Abertos:
- Baixe dataset inicial (consolidados mensais desde 2022)
- Configure pipeline de atualização diária
- Estruture base de dados com campos para expansão futura
- Teste integração com agentes do Legal-Braniac

Isso lhe dará:
- Base sólida de >100k acórdãos do STJ
- Zero custo operacional
- Formato ideal para processamento por LLMs
- Fundação para expansão posterior

---

## Recursos Técnicos

**STJ Dados Abertos**:
- Portal: https://dadosabertos.web.stj.jus.br/
- Dataset de Íntegras: https://dadosabertos.web.stj.jus.br/dataset/integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica
- Espelhos de Acórdãos: https://dadosabertos.web.stj.jus.br/group/jurisprudencia
- Documentação: https://dadosabertos.web.stj.jus.br/dataset/api-publica-datajud

**DataJud (para referência de metadados)**:
- Wiki: https://datajud-wiki.cnj.jus.br/api-publica/
- Endpoints: https://api-publica.datajud.cnj.jus.br/

**APIs Comerciais**:
- Jusbrasil: https://api.jusbrasil.com.br/
- Escavador: https://api.escavador.com/v2/docs/
