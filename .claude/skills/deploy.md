---
name: deploy
description: Deploy Legal Workbench to Oracle Cloud. Use this skill when the user says "/deploy", "deploy to OCI", "deploy frontend", "deploy api-*", "deploy to production", or "push to server".
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebSearch
---

# Deploy - Legal Workbench to Oracle Cloud

Deploy servicos do Legal Workbench para a VM Oracle Cloud Infrastructure.

## Quando Usar

- `/deploy` - Deploy completo
- `/deploy frontend` - Apenas frontend-react
- `/deploy api-text-extractor` - Servico especifico
- `/deploy --build` - Rebuild antes de deploy

## Infraestrutura

**Servidor:** `opc@137.131.201.119`
**SSH Key:** `~/.ssh/oci_lw`
**Diretorio remoto:** `/opt/legal-workbench`
**Regiao OCI:** `sa-saopaulo-1`

## Servicos Disponiveis

| Servico | Rota | Porta |
|---------|------|-------|
| frontend-react | `/` | 3000 |
| api-stj | `/api/stj` | 8000 |
| api-text-extractor | `/api/text` | 8001 |
| api-doc-assembler | `/api/doc` | 8002 |
| api-ledes-converter | `/api/ledes` | 8003 |
| api-trello | `/api/trello` | 8004 |
| api-ccui-ws | `/ws`, `/api/chat` | 8005 |

## Workflow de Deploy

### 1. Pre-Deploy (Local)

```bash
# Verificar branch e status
git status
git log --oneline -3

# Build local (se necessario)
cd legal-workbench
docker compose build <servico>
```

### 2. Sync para Servidor

```bash
# Rsync do projeto
rsync -avz --delete \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.venv' \
  --exclude='__pycache__' \
  -e "ssh -i ~/.ssh/oci_lw" \
  legal-workbench/ \
  opc@137.131.201.119:/opt/legal-workbench/
```

### 3. Deploy (Remoto via SSH)

```bash
ssh -i ~/.ssh/oci_lw opc@137.131.201.119 << 'EOF'
  cd /opt/legal-workbench

  # Build e restart
  docker compose build <servico>
  docker compose up -d <servico>

  # Verificar logs
  docker compose logs --tail=50 <servico>
EOF
```

### 4. Health Check

```bash
# Frontend
curl -s http://137.131.201.119/ | head -20

# APIs
curl -s http://137.131.201.119/api/text/health
curl -s http://137.131.201.119/api/stj/health
```

## Comandos Uteis no Servidor

```bash
# Status de todos os containers
docker compose ps

# Logs em tempo real
docker compose logs -f <servico>

# Restart de servico
docker compose restart <servico>

# Ver uso de recursos
docker stats --no-stream
```

## Troubleshooting

| Problema | Acao |
|----------|------|
| Container nao inicia | `docker compose logs <servico>` |
| Porta ocupada | `docker compose down && docker compose up -d` |
| Build falha | Verificar Dockerfile e deps |
| SSH timeout | Verificar Security List no OCI |

## Checklist

```
[ ] Branch correta (main para prod)
[ ] Testes passando
[ ] Build local OK
[ ] Rsync completo
[ ] Build remoto OK
[ ] Health check OK
[ ] Logs sem erros
```

## NUNCA

- Deploy direto de branch feature sem merge
- Modificar .env em producao sem backup
- Fazer `docker compose down` sem necessidade
- Ignorar falhas de health check
