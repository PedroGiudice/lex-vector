#!/bin/bash
# Script de teste da API STJ Dados Abertos
# Requer: curl, jq (opcional para formatação JSON)

API_URL="http://localhost:8000"

echo "=== STJ Dados Abertos API - Testes ==="
echo ""

# 1. Health Check
echo "1. Health Check"
echo "GET ${API_URL}/health"
curl -s "${API_URL}/health" | jq . || curl -s "${API_URL}/health"
echo ""
echo ""

# 2. Root endpoint
echo "2. Root Endpoint"
echo "GET ${API_URL}/"
curl -s "${API_URL}/" | jq . || curl -s "${API_URL}/"
echo ""
echo ""

# 3. Estatísticas
echo "3. Estatísticas do Banco"
echo "GET ${API_URL}/api/v1/stats"
curl -s "${API_URL}/api/v1/stats" | jq . || curl -s "${API_URL}/api/v1/stats"
echo ""
echo ""

# 4. Busca simples (ementa)
echo "4. Busca Simples (ementa)"
echo "GET ${API_URL}/api/v1/search?termo=responsabilidade&limit=5"
curl -s "${API_URL}/api/v1/search?termo=responsabilidade&limit=5" | jq . || \
    curl -s "${API_URL}/api/v1/search?termo=responsabilidade&limit=5"
echo ""
echo ""

# 5. Busca com filtro de órgão
echo "5. Busca com Filtro de Órgão"
echo "GET ${API_URL}/api/v1/search?termo=civil&orgao=Terceira%20Turma&limit=3"
curl -s "${API_URL}/api/v1/search?termo=civil&orgao=Terceira%20Turma&limit=3" | jq . || \
    curl -s "${API_URL}/api/v1/search?termo=civil&orgao=Terceira%20Turma&limit=3"
echo ""
echo ""

# 6. Busca em texto integral (pode ser lenta)
echo "6. Busca em Texto Integral (últimos 30 dias)"
echo "GET ${API_URL}/api/v1/search?termo=dano&campo=texto_integral&dias=30&limit=2"
curl -s "${API_URL}/api/v1/search?termo=dano&campo=texto_integral&dias=30&limit=2" | jq . || \
    curl -s "${API_URL}/api/v1/search?termo=dano&campo=texto_integral&dias=30&limit=2"
echo ""
echo ""

# 7. Status de sincronização
echo "7. Status de Sincronização"
echo "GET ${API_URL}/api/v1/sync/status"
curl -s "${API_URL}/api/v1/sync/status" | jq . || curl -s "${API_URL}/api/v1/sync/status"
echo ""
echo ""

# 8. Documentação interativa
echo "8. Documentação Interativa"
echo "Acesse: ${API_URL}/docs"
echo ""

echo "=== Testes Concluídos ==="
