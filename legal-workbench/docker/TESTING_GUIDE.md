# Guia de Testes - Legal Workbench Docker

> **Para**: PGR
> **De**: Claude (Technical Director)
> **Data**: 2025-12-11
> **Branch**: `claude/docker-analysis-01QbbMxQFDgBtcTGGDfX8pHz`

---

## Checklist Rápido

Quando chegar no PC, execute na ordem:

```bash
# 1. Atualizar repositório
cd ~/lex-vector
git fetch origin
git checkout claude/docker-analysis-01QbbMxQFDgBtcTGGDfX8pHz
git pull

# 2. Configurar ambiente
cd legal-workbench/docker
cp .env.example .env
nano .env  # Adicionar suas API keys

# 3. Executar smoke test
chmod +x scripts/smoke-test.sh
./scripts/smoke-test.sh
```

---

## Passo a Passo Detalhado

### 1. Pré-requisitos

Verifique se você tem:

```bash
# Docker 24+
docker --version

# Docker Compose 2.20+
docker compose version

# 14GB+ RAM no WSL
free -h
```

Se precisar ajustar memória do WSL, edite `%UserProfile%\.wslconfig`:

```ini
[wsl2]
memory=14GB
swap=4GB
processors=4
```

Depois reinicie WSL: `wsl --shutdown`

### 2. Configurar API Keys

Edite o arquivo `.env`:

```bash
cd legal-workbench/docker
nano .env
```

Preencha:

```env
# Obrigatório para text-extractor
GEMINI_API_KEY=sua_chave_aqui

# Obrigatório para trello-mcp
TRELLO_API_KEY=sua_chave_aqui
TRELLO_API_TOKEN=seu_token_aqui
```

**Onde obter:**
- Gemini: https://aistudio.google.com/apikey
- Trello: https://trello.com/power-ups/admin (criar Power-Up)

### 3. Executar Smoke Test

```bash
./scripts/smoke-test.sh
```

O script vai:
1. ✅ Verificar pré-requisitos
2. ✅ Construir todas as imagens
3. ✅ Subir containers na ordem correta
4. ✅ Testar health endpoints
5. ✅ Executar testes funcionais básicos

### 4. Testes Manuais (Opcional)

#### Testar Text Extractor:

```bash
# Upload de PDF de teste
curl -X POST http://localhost:8001/api/v1/extract \
  -F "file=@/caminho/para/teste.pdf" \
  -F "engine=pdfplumber"

# Verificar status do job
curl http://localhost:8001/api/v1/jobs/{job_id}

# Obter resultado
curl http://localhost:8001/api/v1/jobs/{job_id}/result
```

#### Testar Doc Assembler:

```bash
# Listar templates
curl http://localhost:8002/api/v1/templates

# Gerar documento (exemplo)
curl -X POST http://localhost:8002/api/v1/assemble \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "peticao_inicial",
    "data": {
      "cliente_nome": "João Silva",
      "cliente_cpf": "123.456.789-00"
    }
  }'
```

#### Testar STJ API:

```bash
# Buscar jurisprudência
curl "http://localhost:8003/api/v1/search?query=habeas+corpus&limit=5"

# Estatísticas
curl http://localhost:8003/api/v1/stats
```

### 5. Acessar Interface Web

Abra no navegador: **http://localhost:8501**

A interface tem 4 abas:
- 📄 **Text Extractor** - Upload e extração de PDFs
- 📋 **Doc Assembler** - Geração de documentos
- 🔍 **STJ Search** - Busca de jurisprudência
- 📌 **Trello** - Integração com Trello

---

## Troubleshooting

### Container não sobe

```bash
# Ver logs do container
docker compose logs text-extractor

# Reiniciar serviço específico
docker compose restart text-extractor

# Reconstruir imagem
docker compose build --no-cache text-extractor
docker compose up -d text-extractor
```

### Out of Memory (OOM)

Se o text-extractor morrer com código 137:

```bash
# Verificar memória
docker stats

# Reduzir concorrência em .env
MAX_CONCURRENT_JOBS=1
```

### Porta já em uso

```bash
# Verificar o que está usando a porta
sudo lsof -i :8501

# Matar processo ou mudar porta no docker-compose.yml
```

### Build falha

```bash
# Limpar cache e reconstruir
docker system prune -a
docker compose build --no-cache
```

---

## Comandos Úteis

```bash
# Ver status de todos os containers
docker compose ps

# Ver logs em tempo real
docker compose logs -f

# Ver logs de um serviço
docker compose logs text-extractor --tail=50

# Parar tudo
docker compose down

# Parar e remover volumes (⚠️ CUIDADO: perde dados)
docker compose down -v

# Reiniciar tudo
docker compose restart

# Ver uso de recursos
docker stats
```

---

## URLs de Acesso

| Serviço | URL | Descrição |
|---------|-----|-----------|
| Streamlit Hub | http://localhost:8501 | Interface principal |
| Text Extractor API | http://localhost:8001/docs | Swagger UI |
| Doc Assembler API | http://localhost:8002/docs | Swagger UI |
| STJ API | http://localhost:8003/docs | Swagger UI |
| Trello MCP API | http://localhost:8004/docs | Swagger UI |
| Celery Flower | http://localhost:5555 | Monitoramento de jobs |

---

## Resultado Esperado

Se tudo funcionar, você verá:

```
═══════════════════════════════════════════════════════════════
  RESULTADO DO SMOKE TEST
═══════════════════════════════════════════════════════════════

  Passed:  15
  Failed:  0
  Skipped: 1

═══════════════════════════════════════════════════════════════
  ✓ TODOS OS TESTES PASSARAM!
═══════════════════════════════════════════════════════════════
```

---

## Contato

Se tiver problemas, abra uma issue no repo ou me chame na próxima sessão do Claude Code.

**Branch testado**: `claude/docker-analysis-01QbbMxQFDgBtcTGGDfX8pHz`
