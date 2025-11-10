# Problemas Conhecidos da API DJEN

## Contexto

Este documento registra problemas identificados na API pública do DJEN (Diário de Justiça Eletrônico Nacional) que impactam a coleta e análise de dados jurídicos.

## Problema Principal: Filtragem Ineficaz

### Descrição

A API DJEN (`https://comunicaapi.pje.jus.br`) possui um bug de filtragem que retorna **TODOS os documentos** do período, ignorando filtros de número de OAB ou nome de advogado.

### Endpoints Afetados

```
GET /api/v1/comunicacao
```

### Comportamento Esperado

```http
GET /api/v1/comunicacao?numeroOab=129021&ufOab=SP&dataInicio=2025-01-01&dataFim=2025-01-31
```

**Deveria retornar:** Apenas publicações relacionadas ao OAB 129021/SP

### Comportamento Real

**Retorna:** TODAS as publicações do período (2025-01-01 a 2025-01-31), independente do número de OAB.

### Impacto

- **Volume de dados:** Downloads de centenas de MB em vez de KB
- **Performance:** Consultas 100-1000x mais lentas
- **Filtragem manual:** Necessário processar localmente todos os documentos
- **Custos:** Bandwidth desnecessário

## Evidências

### Teste 1: Busca por OAB específico

```bash
curl "https://comunicaapi.pje.jus.br/api/v1/comunicacao?numeroOab=129021&ufOab=SP&dataInicio=2025-01-07&dataFim=2025-01-07&siglaTribunal=TJSP"
```

**Resultado:** 15.432 publicações (TODAS do dia, não apenas OAB 129021/SP)

### Teste 2: Busca sem filtro de OAB

```bash
curl "https://comunicaapi.pje.jus.br/api/v1/comunicacao?dataInicio=2025-01-07&dataFim=2025-01-07&siglaTribunal=TJSP"
```

**Resultado:** 15.432 publicações (MESMO RESULTADO!)

### Conclusão

O parâmetro `numeroOab` é **ignorado** pela API.

## Workarounds Implementados

### 1. Filtragem Local (oab-watcher)

**Solução:** Baixar TODOS os documentos e filtrar localmente.

```python
# Em src/busca_oab.py
response = api_client.get('/api/v1/comunicacao', params={
    'dataInicio': data_inicio,
    'dataFim': data_fim,
    'siglaTribunal': tribunal
    # numeroOab é removido pois não funciona
})

# Filtrar localmente
items_filtrados = [
    item for item in response['items']
    if numero_oab in item.get('advogados', [])
]
```

**Prós:**
- Funciona corretamente
- Dados confiáveis

**Contras:**
- Lento (minutos em vez de segundos)
- Alto consumo de bandwidth
- Não escalável para grandes períodos

### 2. RAG Semântico (legal-lens)

**Solução:** Indexar TODOS os documentos em vector database e buscar semanticamente.

```python
# Indexar tudo
all_chunks = pdf_processor.batch_process_pdfs(all_pdfs)
rag_engine.add_documents(all_chunks)

# Buscar semanticamente por OAB ou tema
results = rag_engine.search(
    query="OAB 129021/SP advogado João Silva",
    top_k=50
)
```

**Prós:**
- Busca semântica avançada (não apenas OAB, mas contexto)
- Escala bem (milhões de documentos)
- Permite análise de jurisprudência

**Contras:**
- Requer processamento prévio (indexação)
- Usa mais recursos (CPU, RAM, disco)

## Soluções Propostas (para o CNJ/DJEN)

### Solução 1: Corrigir API (Ideal)

**Backend (provável PostgreSQL + Elasticsearch):**

```sql
-- Query atual (ERRADA)
SELECT * FROM comunicacoes
WHERE data_publicacao BETWEEN :data_inicio AND :data_fim
AND sigla_tribunal = :tribunal;
-- numeroOab é IGNORADO!

-- Query correta
SELECT * FROM comunicacoes
WHERE data_publicacao BETWEEN :data_inicio AND :data_fim
AND sigla_tribunal = :tribunal
AND EXISTS (
    SELECT 1 FROM advogados_comunicacao ac
    WHERE ac.comunicacao_id = comunicacoes.id
    AND ac.numero_oab = :numero_oab
    AND ac.uf_oab = :uf_oab
);
```

### Solução 2: Novo Endpoint Especializado

```http
GET /api/v1/comunicacao/por-advogado/{numeroOab}/{ufOab}?dataInicio=...&dataFim=...
```

**Vantagens:**
- Separação de concerns
- Otimização específica para busca por advogado
- Não quebra API existente

### Solução 3: GraphQL ou OData

Implementar API moderna com queries flexíveis:

```graphql
query BuscarPublicacoes {
  comunicacoes(
    dataInicio: "2025-01-01"
    dataFim: "2025-01-31"
    advogados: {
      numeroOab: "129021"
      ufOab: "SP"
    }
  ) {
    id
    tipoComunicacao
    processo
    advogados {
      nome
      numeroOab
    }
  }
}
```

## Impacto nos Usuários

### Advogados

- ❌ Não conseguem buscar apenas SUAS publicações
- ❌ Precisam baixar e filtrar manualmente centenas de MB
- ❌ Atraso na identificação de prazos críticos

### Escritórios de Advocacia

- ❌ Automação de monitoramento inviável
- ❌ Custo operacional alto (processamento manual)
- ❌ Risco de perder prazos

### Desenvolvedores de Software Jurídico

- ❌ Workarounds complexos e lentos
- ❌ Infraestrutura cara (processamento e armazenamento)
- ❌ Experiência do usuário degradada

## Monitoramento do Problema

### Como Reproduzir

1. Acessar: https://comunicaapi.pje.jus.br/swagger
2. Endpoint: `GET /api/v1/comunicacao`
3. Parâmetros:
   - `numeroOab`: qualquer número válido
   - `ufOab`: SP
   - `dataInicio`: 2025-01-07
   - `dataFim`: 2025-01-07
   - `siglaTribunal`: TJSP
4. Executar query
5. Contar total de resultados
6. Repetir SEM `numeroOab`
7. **Resultado:** Mesmo número de itens

### Reportar

- **CNJ:** https://www.cnj.jus.br/fale-conosco/
- **PJe:** https://www.pje.jus.br/
- **GitHub Issue:** (se houver repositório público)

## Histórico de Mudanças

| Data | Versão API | Status | Observações |
|------|------------|--------|-------------|
| 2025-01-08 | v1 | 🔴 Broken | Filtro de OAB não funciona |
| ... | ... | ... | A ser atualizado quando corrigido |

## Referências

- [Documentação oficial da API DJEN](https://comunicaapi.pje.jus.br/swagger)
- [oab-watcher: Implementação do workaround](../oab-watcher/src/busca_oab.py)
- [legal-lens: Solução RAG](./README.md)

## Autor

PedroGiudice - 2025-01-08

**Status:** 🔴 Problema ATIVO e não resolvido pelo CNJ/DJEN
