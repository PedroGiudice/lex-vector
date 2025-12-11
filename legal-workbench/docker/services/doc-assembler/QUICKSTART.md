# Doc Assembler API - Quick Start Guide

## 🚀 Start in 3 Steps

### 1. Start the Service

#### Using Docker (Recommended)
```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/docker
docker-compose up doc-assembler
```

#### Using Python Directly
```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/docker/services/doc-assembler
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload
```

### 2. Verify Service

```bash
curl http://localhost:8002/health | jq '.'
```

Expected output:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "engine_version": "2.0.0",
  "timestamp": "2025-12-11T..."
}
```

### 3. Test API

#### Option A: Using Python Test Suite
```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/docker/services/doc-assembler
python test_api.py
```

#### Option B: Using curl
```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/docker/services/doc-assembler
./examples/simple_curl_tests.sh
```

#### Option C: Using Python Client
```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/docker/services/doc-assembler
python examples/python_client_example.py
```

---

## 📋 Basic Usage Examples

### List Available Templates

```bash
curl http://localhost:8002/api/v1/templates | jq '.'
```

### Assemble a Document

```bash
curl -X POST http://localhost:8002/api/v1/assemble \
  -H "Content-Type: application/json" \
  -d '{
    "template_path": "your_template.docx",
    "data": {
      "nome": "João da Silva",
      "cpf": "123.456.789-01",
      "endereco": "Rua das Flores, 123"
    },
    "output_filename": "output.docx",
    "field_types": {
      "nome": "name",
      "cpf": "cpf",
      "endereco": "address"
    }
  }' | jq '.'
```

### Preview Document (No File Created)

```bash
curl -X POST http://localhost:8002/api/v1/preview \
  -H "Content-Type: application/json" \
  -d '{
    "template_path": "your_template.docx",
    "data": {
      "nome": "João da Silva",
      "cpf": "123.456.789-01"
    }
  }' | jq '.full_text'
```

---

## 🔍 Interactive Documentation

Open in browser after starting service:

- **Swagger UI:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc

---

## 🐛 Troubleshooting

### Service won't start?

```bash
# Check if port 8002 is already in use
lsof -i :8002

# Check Docker logs
docker logs lw-doc-assembler

# Rebuild if needed
docker-compose build --no-cache doc-assembler
```

### Can't find templates?

Templates should be in:
```
/home/user/Claude-Code-Projetos/legal-workbench/ferramentas/legal-doc-assembler/templates/
```

Check they're mounted correctly:
```bash
docker exec lw-doc-assembler ls -la /app/templates
```

### Import errors?

The API automatically adds the backend source to Python path. Verify:
```bash
docker exec lw-doc-assembler python -c "import sys; print('\n'.join(sys.path))"
```

---

## 📚 Next Steps

1. Read full documentation: `README.md`
2. Check API endpoints: http://localhost:8002/docs
3. See Python client example: `examples/python_client_example.py`
4. Review backend code: `/home/user/Claude-Code-Projetos/legal-workbench/ferramentas/legal-doc-assembler/src/`

---

## 🔗 Related Services

Part of Legal Workbench (all services):
```bash
docker-compose up  # Start all services
```

- **Streamlit Hub:** http://localhost:8501
- **Text Extractor:** http://localhost:8001
- **Doc Assembler:** http://localhost:8002 ← YOU ARE HERE
- **STJ API:** http://localhost:8003
- **Trello MCP:** http://localhost:8004
