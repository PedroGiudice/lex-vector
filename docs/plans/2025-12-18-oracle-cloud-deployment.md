# Legal Workbench - Oracle Cloud Free Tier Deployment Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy Legal Workbench (React + 5 FastAPI services + Redis) on Oracle Cloud Always Free Tier for $0/month.

**Architecture:** Single ARM64 VM running docker-compose with Traefik reverse proxy. All services communicate via internal Docker network. Cloudflare provides DNS + SSL (free tier).

**Tech Stack:**
- Oracle Cloud A1.Flex (4 OCPU ARM, 24GB RAM, 200GB storage) - Always Free
- Docker + Docker Compose on Oracle Linux 8
- Cloudflare DNS + SSL (free)
- GitHub Actions for CI/CD (optional)

---

## Pre-Requisitos

**Antes de iniciar, voce precisa ter:**
- Conta Oracle Cloud (criar em https://www.oracle.com/cloud/free/)
- Dominio proprio (opcional, pode usar IP direto)
- Conta Cloudflare (opcional, para SSL gratis)
- Variaveis de ambiente: `TRELLO_API_KEY`, `TRELLO_API_TOKEN`, `GEMINI_API_KEY`

---

## FASE 1: Criar Conta Oracle Cloud (15 min)

### Task 1.1: Registro na Oracle Cloud

**Passo 1:** Acesse https://www.oracle.com/cloud/free/

**Passo 2:** Clique em "Start for free"

**Passo 3:** Preencha o formulario:
- Email valido
- Pais: Brasil
- Tipo de conta: Individual ou Company

**Passo 4:** Verificacao de cartao de credito
- Oracle pede cartao para verificacao (NAO cobra)
- Pode usar cartao virtual (Nubank, Inter, etc)
- Cobranca de $1 que e estornada

**Passo 5:** Selecione a regiao "Brazil East (Sao Paulo)"
- IMPORTANTE: Sao Paulo tem melhor latencia para usuarios BR
- Se nao disponivel, use "Brazil Southeast (Vinhedo)"

**Verificacao:**
- Acesse https://cloud.oracle.com
- Deve ver o dashboard sem erros
- Regiao deve mostrar "Brazil East" ou similar

---

## FASE 2: Criar VM ARM (20 min)

### Task 2.1: Criar Instancia A1.Flex

**Passo 1:** No dashboard Oracle Cloud, va para:
- Menu hamburger (canto superior esquerdo)
- Compute > Instances
- "Create instance"

**Passo 2:** Configure a instancia:
```
Name: legal-workbench-prod
Compartment: (root)
Availability domain: AD-1 (ou qualquer disponivel)
```

**Passo 3:** Selecione imagem e shape:
```
Image: Oracle Linux 8 (ARM compatible)
Shape: VM.Standard.A1.Flex
  - OCPUs: 4 (maximo free)
  - Memory: 24 GB (maximo free)
```

**Passo 4:** Configure rede:
```
Virtual cloud network: Criar novo VCN
  - Name: legal-workbench-vcn
  - Create in compartment: (root)
Subnet: Criar nova subnet publica
  - Name: public-subnet
Assign public IPv4 address: YES
```

**Passo 5:** Adicione SSH key:
```bash
# No seu terminal local, gere uma chave se nao tiver:
ssh-keygen -t ed25519 -C "legal-workbench" -f ~/.ssh/oracle_legal

# Copie a chave publica:
cat ~/.ssh/oracle_legal.pub
```
- Cole a chave publica no campo "SSH keys"
- Selecione "Paste public keys"

**Passo 6:** Configure boot volume:
```
Boot volume size: 100 GB (pode usar ate 200GB no free tier)
```

**Passo 7:** Clique "Create"

**Verificacao:**
- Aguarde status mudar para "RUNNING" (~3-5 min)
- Anote o "Public IP address" (ex: 150.230.xxx.xxx)

---

### Task 2.2: Configurar Security List (Firewall)

**Passo 1:** Va para:
- Networking > Virtual cloud networks
- Clique no VCN criado (legal-workbench-vcn)
- Security Lists > Default Security List

**Passo 2:** Adicione regras de ingresso (Add Ingress Rules):

```
Regra 1 - HTTP:
  Source CIDR: 0.0.0.0/0
  IP Protocol: TCP
  Destination Port Range: 80
  Description: HTTP

Regra 2 - HTTPS:
  Source CIDR: 0.0.0.0/0
  IP Protocol: TCP
  Destination Port Range: 443
  Description: HTTPS

Regra 3 - SSH (ja deve existir):
  Source CIDR: 0.0.0.0/0
  IP Protocol: TCP
  Destination Port Range: 22
  Description: SSH
```

**Verificacao:**
- Deve ter 3 regras de ingresso (SSH, HTTP, HTTPS)

---

## FASE 3: Setup Inicial do Servidor (30 min)

### Task 3.1: Conectar via SSH

**Passo 1:** Conecte ao servidor:
```bash
ssh -i ~/.ssh/oracle_legal opc@<IP_PUBLICO>
```

**Passo 2:** Verifique o sistema:
```bash
# Verificar arquitetura (deve ser aarch64)
uname -m

# Verificar memoria (deve ser ~24GB)
free -h

# Verificar disco
df -h
```

**Verificacao esperada:**
```
$ uname -m
aarch64

$ free -h
              total        used        free
Mem:           23Gi       500Mi        22Gi
```

---

### Task 3.2: Instalar Docker

**Passo 1:** Instale Docker no Oracle Linux 8:
```bash
# Atualizar sistema
sudo dnf update -y

# Instalar dependencias
sudo dnf install -y dnf-utils device-mapper-persistent-data lvm2

# Adicionar repositorio Docker
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Instalar Docker (ARM64)
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Iniciar e habilitar Docker
sudo systemctl enable --now docker

# Adicionar usuario ao grupo docker
sudo usermod -aG docker opc
```

**Passo 2:** Relogar para aplicar grupo:
```bash
exit
# Reconectar
ssh -i ~/.ssh/oracle_legal opc@<IP_PUBLICO>
```

**Passo 3:** Verificar instalacao:
```bash
docker --version
docker compose version
docker run hello-world
```

**Verificacao esperada:**
```
$ docker --version
Docker version 24.x.x, build xxx

$ docker compose version
Docker Compose version v2.x.x
```

---

### Task 3.3: Configurar Firewall do OS

**Passo 1:** Oracle Linux tem firewalld alem da Security List. Abra as portas:
```bash
# Abrir portas HTTP e HTTPS
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp

# Recarregar firewall
sudo firewall-cmd --reload

# Verificar
sudo firewall-cmd --list-ports
```

**Verificacao esperada:**
```
80/tcp 443/tcp
```

---

## FASE 4: Deploy da Aplicacao (20 min)

### Task 4.1: Clonar Repositorio

**Passo 1:** Instale git e clone o repo:
```bash
sudo dnf install -y git

# Clone o repositorio
cd ~
git clone https://github.com/PedroGiudice/Claude-Code-Projetos.git
cd Claude-Code-Projetos/legal-workbench
```

**Verificacao:**
```bash
ls -la
# Deve ver: docker-compose.yml, frontend/, docker/, etc
```

---

### Task 4.2: Configurar Variaveis de Ambiente

**Passo 1:** Crie o arquivo .env:
```bash
cat > .env << 'EOF'
# Trello API
TRELLO_API_KEY=sua_api_key_aqui
TRELLO_API_TOKEN=seu_token_aqui

# Gemini API (para text-extractor)
GEMINI_API_KEY=sua_gemini_key_aqui

# Text Extractor Config
MAX_CONCURRENT_JOBS=2
JOB_TIMEOUT_SECONDS=600
EOF

# Edite com suas credenciais reais
nano .env
```

**Verificacao:**
```bash
cat .env
# Deve mostrar suas variaveis (NAO compartilhe!)
```

---

### Task 4.3: Build e Deploy

**Passo 1:** Build das imagens Docker (ARM64):
```bash
# Build de todas as imagens
docker compose build

# Isso pode levar 10-15 minutos na primeira vez
# O text-extractor com MARKER demora mais (baixa modelos)
```

**Passo 2:** Inicie os servicos:
```bash
docker compose up -d
```

**Passo 3:** Verifique os containers:
```bash
docker compose ps
```

**Verificacao esperada:**
```
NAME                    STATUS
reverse-proxy           running
frontend-react          running
api-stj                 running
api-text-extractor      running
api-doc-assembler       running
api-trello              running
redis                   running
```

**Passo 4:** Verifique logs se algo falhar:
```bash
# Logs de um servico especifico
docker compose logs api-text-extractor

# Logs de todos
docker compose logs -f
```

---

### Task 4.4: Testar Aplicacao

**Passo 1:** Teste via curl no servidor:
```bash
# Testar frontend
curl -I http://localhost/

# Testar API Trello
curl http://localhost/api/trello/health

# Testar API STJ
curl http://localhost/api/stj/health
```

**Passo 2:** Acesse via navegador:
```
http://<IP_PUBLICO>/
```

**Verificacao:**
- Deve ver a interface do Legal Workbench
- Navegacao entre modulos deve funcionar

---

## FASE 5: Configurar Dominio + SSL (15 min)

### Task 5.1: Configurar Cloudflare DNS (Opcional)

**Se voce tem um dominio:**

**Passo 1:** Acesse https://dash.cloudflare.com

**Passo 2:** Adicione seu dominio ou use um existente

**Passo 3:** Crie um registro DNS:
```
Type: A
Name: legal (ou @ para raiz)
IPv4 address: <IP_PUBLICO_DA_VM>
Proxy status: Proxied (nuvem laranja)
TTL: Auto
```

**Passo 4:** Configure SSL no Cloudflare:
- SSL/TLS > Overview
- Selecione "Full" ou "Full (strict)"

**Verificacao:**
```bash
# Aguarde propagacao DNS (~5 min)
dig legal.seudominio.com

# Teste acesso HTTPS
curl -I https://legal.seudominio.com/
```

---

### Task 5.2: Configurar HTTPS com Let's Encrypt (Alternativa sem Cloudflare)

**Se preferir SSL direto no servidor:**

**Passo 1:** Modifique o docker-compose.yml para Traefik com ACME:
```yaml
# Adicione ao servico reverse-proxy:
command:
  - "--api.insecure=true"
  - "--providers.docker=true"
  - "--providers.docker.exposedbydefault=false"
  - "--entrypoints.web.address=:80"
  - "--entrypoints.websecure.address=:443"
  - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
  - "--certificatesresolvers.letsencrypt.acme.email=seu@email.com"
  - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
ports:
  - "80:80"
  - "443:443"
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
  - letsencrypt:/letsencrypt
```

**Passo 2:** Adicione volume para certificados:
```yaml
volumes:
  letsencrypt:
```

**Passo 3:** Recrie o Traefik:
```bash
docker compose up -d reverse-proxy
```

---

## FASE 6: Configurar Auto-Deploy (Opcional, 15 min)

### Task 6.1: GitHub Actions para CI/CD

**Passo 1:** Crie o arquivo `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Oracle Cloud

on:
  push:
    branches: [main]
    paths:
      - 'legal-workbench/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.ORACLE_HOST }}
          username: opc
          key: ${{ secrets.ORACLE_SSH_KEY }}
          script: |
            cd ~/Claude-Code-Projetos/legal-workbench
            git pull origin main
            docker compose build
            docker compose up -d
```

**Passo 2:** Configure secrets no GitHub:
- Settings > Secrets and variables > Actions
- Adicione:
  - `ORACLE_HOST`: IP publico da VM
  - `ORACLE_SSH_KEY`: Conteudo da chave privada (~/.ssh/oracle_legal)

---

## FASE 7: Monitoramento e Manutencao

### Task 7.1: Configurar Healthchecks

**Comandos uteis para monitoramento:**

```bash
# Ver uso de recursos
docker stats

# Ver logs em tempo real
docker compose logs -f

# Reiniciar um servico
docker compose restart api-text-extractor

# Atualizar aplicacao
cd ~/Claude-Code-Projetos/legal-workbench
git pull
docker compose build
docker compose up -d

# Limpar imagens antigas
docker system prune -af
```

---

### Task 7.2: Backup Automatico (Cron)

**Passo 1:** Crie script de backup:
```bash
cat > ~/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR=~/backups/$DATE

mkdir -p $BACKUP_DIR

# Backup dos volumes Docker
docker run --rm \
  -v legal-workbench_shared-data:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/shared-data.tar.gz /data

docker run --rm \
  -v legal-workbench_stj-db:/data \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/stj-db.tar.gz /data

# Manter apenas ultimos 7 dias
find ~/backups -type d -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x ~/backup.sh
```

**Passo 2:** Adicione ao crontab:
```bash
crontab -e
# Adicione:
0 3 * * * ~/backup.sh >> ~/backup.log 2>&1
```

---

## Resumo de Custos

| Item | Custo Mensal |
|------|--------------|
| Oracle Cloud VM (A1.Flex 4 OCPU, 24GB) | $0 (Always Free) |
| Oracle Cloud Storage (100GB) | $0 (Always Free) |
| Cloudflare DNS + SSL | $0 (Free tier) |
| **TOTAL** | **$0/mes** |

---

## Troubleshooting

### Problema: Imagens Docker nao fazem build

**Causa:** Imagens base nao tem versao ARM64

**Solucao:** Verifique se todas as imagens base suportam ARM:
```bash
docker manifest inspect python:3.11-slim | grep arm64
docker manifest inspect redis:7-alpine | grep arm64
docker manifest inspect traefik:v3.6.5 | grep arm64
```

### Problema: MARKER nao processa PDFs

**Causa:** Falta de memoria ou modelos nao baixados

**Solucao:**
```bash
# Verificar memoria do container
docker stats api-text-extractor

# Ver logs detalhados
docker compose logs api-text-extractor | grep -i error

# Reiniciar com mais memoria (se necessario)
docker compose down api-text-extractor
docker compose up -d api-text-extractor
```

### Problema: Nao consigo criar VM A1.Flex

**Causa:** Capacidade da regiao esgotada

**Solucao:**
1. Tente outra Availability Domain (AD-2, AD-3)
2. Tente em horario diferente (madrugada BR)
3. Tente regiao alternativa (Vinhedo em vez de Sao Paulo)
4. Use script de retry automatico:
```bash
# Script que tenta criar a cada 5 minutos
while true; do
  oci compute instance launch --config-file ... && break
  sleep 300
done
```

---

## Proximos Passos

1. [ ] Criar conta Oracle Cloud
2. [ ] Criar VM A1.Flex
3. [ ] Instalar Docker
4. [ ] Deploy da aplicacao
5. [ ] Configurar dominio (opcional)
6. [ ] Testar com a Bia

---

**Autor:** Technical Director (Claude)
**Data:** 2025-12-18
**Versao:** 1.0
