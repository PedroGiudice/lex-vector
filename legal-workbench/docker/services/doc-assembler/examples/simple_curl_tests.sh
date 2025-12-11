#!/bin/bash
# Simple curl tests for Doc Assembler API

BASE_URL="http://localhost:8002"
API_V1="${BASE_URL}/api/v1"

echo "=================================="
echo "Doc Assembler API - Curl Tests"
echo "=================================="

# Test 1: Health Check
echo -e "\n1️⃣  Testing /health..."
curl -s "${BASE_URL}/health" | jq '.'

# Test 2: List Templates
echo -e "\n2️⃣  Testing GET /api/v1/templates..."
curl -s "${API_V1}/templates" | jq '.'

# Test 3: Validate Data
echo -e "\n3️⃣  Testing POST /api/v1/validate..."
curl -s -X POST "${API_V1}/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "template_path": "example.docx",
    "data": {
      "nome": "João da Silva",
      "cpf": "12345678901"
    }
  }' | jq '.'

# Test 4: Preview Document
echo -e "\n4️⃣  Testing POST /api/v1/preview..."
curl -s -X POST "${API_V1}/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "template_path": "example.docx",
    "data": {
      "nome": "João da Silva",
      "cpf": "123.456.789-01",
      "endereco": "Rua das Flores, 123"
    },
    "auto_normalize": true
  }' | jq '.'

# Test 5: Assemble Document
echo -e "\n5️⃣  Testing POST /api/v1/assemble..."
curl -s -X POST "${API_V1}/assemble" \
  -H "Content-Type: application/json" \
  -d '{
    "template_path": "example.docx",
    "data": {
      "nome": "João da Silva",
      "cpf": "123.456.789-01",
      "endereco": "Rua das Flores, 123, São Paulo - SP"
    },
    "output_filename": "test_output.docx",
    "field_types": {
      "nome": "name",
      "cpf": "cpf",
      "endereco": "address"
    },
    "auto_normalize": true
  }' | jq '.'

echo -e "\n=================================="
echo "✅ All tests completed!"
echo "=================================="
