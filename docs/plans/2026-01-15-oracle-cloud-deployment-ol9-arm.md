# Legal Workbench - Oracle Cloud Deployment (OL9 ARM)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy completo do Legal Workbench na VM Oracle Linux 9 ARM em sa-saopaulo-1.

**Architecture:** Docker Compose com Traefik como reverse proxy, servicos Python (FastAPI) e frontend React (Nginx).

**Tech Stack:** Docker, Docker Compose, Oracle Linux 9, ARM64/aarch64, Traefik, FastAPI, React

**VM:** 64.181.162.38 | **SSH:** `ssh -i ~/.ssh/oci_lw opc@64.181.162.38`

---

## Task 1: Instalar Docker e Docker Compose

**Objetivo:** Instalar Docker CE no Oracle Linux 9 ARM.

**Step 1: Atualizar sistema e instalar dependencias**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo dnf update -y && sudo dnf install -y dnf-utils git"
```

Expected: Pacotes atualizados sem erros.

**Step 2: Adicionar repositorio Docker**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo"
```

Expected: Repositorio adicionado.

**Step 3: Instalar Docker**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin"
```

Expected: Docker instalado.

**Step 4: Iniciar e habilitar Docker**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo systemctl start docker && sudo systemctl enable docker"
```

Expected: Docker rodando.

**Step 5: Adicionar usuario ao grupo docker**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo usermod -aG docker opc"
```

Expected: Usuario adicionado (requer novo login para efetivar).

**Step 6: Verificar instalacao**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo docker --version && sudo docker compose version"
```

Expected: Versoes do Docker e Compose exibidas.

---

## Task 2: Configurar Firewall

**Objetivo:** Abrir portas 80 e 443 no firewall do OS.

**Step 1: Abrir portas HTTP/HTTPS**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo firewall-cmd --permanent --add-service=http && sudo firewall-cmd --permanent --add-service=https && sudo firewall-cmd --reload"
```

Expected: success (3x).

**Step 2: Verificar**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo firewall-cmd --list-all"
```

Expected: services inclui http e https.

---

## Task 3: Clonar Repositorio

**Objetivo:** Clonar o repositorio lex-vector na VM.

**Step 1: Clonar**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "cd ~ && git clone https://github.com/PedroGiudice/lex-vector.git"
```

Expected: Repositorio clonado em ~/lex-vector.

**Step 2: Verificar estrutura**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "ls ~/lex-vector/legal-workbench/"
```

Expected: docker, frontend, ferramentas, etc.

---

## Task 4: Configurar .env

**Objetivo:** Criar arquivo .env com credenciais.

**Step 1: Criar .env**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "cat > ~/lex-vector/legal-workbench/.env << 'EOF'
# Trello API
TRELLO_API_KEY=270ff9a4fe79bdc7ecbe6e5f76aed1c0
TRELLO_API_TOKEN=ATTA2a2be1f51e8ed1985a4186357f537ce6fb6e25c61c4c3d65826dfa4951c8a1f375D041BD

# Gemini API
GEMINI_API_KEY=AIzaSyAQQrf_RnR_gFh9KDRIsaIav00gsoEfkHc

# Text Extractor Config
MAX_CONCURRENT_JOBS=2
JOB_TIMEOUT_SECONDS=600

# Logging
LOG_LEVEL=INFO
EOF"
```

Expected: Arquivo criado.

**Step 2: Verificar**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "cat ~/lex-vector/legal-workbench/.env | head -5"
```

Expected: Conteudo do .env exibido.

---

## Task 5: Build dos Containers (ARM)

**Objetivo:** Fazer build das imagens Docker para ARM64.

**Step 1: Build completo via docker compose**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "cd ~/lex-vector/legal-workbench && sudo docker compose build --progress=plain 2>&1" | tee /tmp/docker-build.log
```

Expected: Todas as imagens construidas. NOTA: text-extractor pode demorar (~10-15min) devido a PyTorch ARM.

**Step 2: Verificar imagens criadas**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo docker images | grep legal-workbench"
```

Expected: 6+ imagens listadas (frontend-react, api-stj, api-text-extractor, etc).

---

## Task 6: Deploy com Docker Compose

**Objetivo:** Subir todos os containers.

**Step 1: Iniciar containers**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "cd ~/lex-vector/legal-workbench && sudo docker compose up -d"
```

Expected: Containers criados e iniciados.

**Step 2: Verificar status**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo docker compose ps"
```

Expected: Todos containers com status "Up" ou "healthy".

**Step 3: Verificar logs (se houver erro)**

```bash
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo docker compose logs --tail=50"
```

Expected: Sem erros criticos.

---

## Task 7: Testar Endpoints

**Objetivo:** Validar que a aplicacao esta acessivel.

**Step 1: Testar frontend**

```bash
curl -s -o /dev/null -w "%{http_code}" http://64.181.162.38/
```

Expected: 200

**Step 2: Testar health do Traefik**

```bash
curl -s http://64.181.162.38:8080/api/overview | head -c 100
```

Expected: JSON do Traefik.

**Step 3: Testar API STJ**

```bash
curl -s http://64.181.162.38/api/stj/health
```

Expected: {"status":"healthy"} ou similar.

**Step 4: Testar API Trello**

```bash
curl -s http://64.181.162.38/api/trello/health
```

Expected: {"status":"healthy"} ou similar.

---

## Task 8: Validacao Final

**Objetivo:** Confirmar Definition of Done.

**Checklist:**
- [ ] VM OL9 ARM rodando
- [ ] Docker instalado e funcionando
- [ ] Todos containers up
- [ ] Frontend acessivel em http://64.181.162.38/
- [ ] APIs respondendo health checks
- [ ] Nenhum erro critico nos logs

**Comando de verificacao completa:**

```bash
echo "=== Docker ===" && ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo docker compose ps" && echo "=== Frontend ===" && curl -s -o /dev/null -w "%{http_code}\n" http://64.181.162.38/ && echo "=== APIs ===" && curl -s http://64.181.162.38/api/stj/health 2>/dev/null || echo "STJ: N/A"
```

---

## Rollback (se necessario)

```bash
# Parar tudo
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "cd ~/lex-vector/legal-workbench && sudo docker compose down"

# Limpar imagens
ssh -i ~/.ssh/oci_lw opc@64.181.162.38 "sudo docker system prune -af"

# Recomecar do Task 5
```
