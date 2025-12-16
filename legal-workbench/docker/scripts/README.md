# Legal Workbench - Deployment Scripts

Scripts de operação para deployment e gerenciamento do Legal Workbench dockerizado.

## Scripts Disponíveis

### 1. deploy.sh - Deploy Automatizado
Faz o deploy completo da aplicação com verificação de pré-requisitos e health checks.

```bash
# Deploy em modo desenvolvimento (default)
./deploy.sh

# Deploy em modo produção (build sem cache)
./deploy.sh prod
```

**Features:**
- Verifica pré-requisitos (Docker, Docker Compose)
- Valida variáveis de ambiente (.env)
- Build das imagens
- Start dos serviços
- Health check automático de todos os serviços
- Mostra URLs de acesso

### 2. health-check.sh - Verificação de Saúde
Verifica o status de todos os serviços e mostra uso de recursos.

```bash
# Health check com output completo
./health-check.sh

# Modo silencioso (apenas exit code)
./health-check.sh --quiet

# Output em JSON
./health-check.sh --json
```

**Métricas verificadas:**
- Status dos containers
- Endpoints /health de cada serviço
- Uso de CPU
- Uso de memória

**Exit codes:**
- 0 = Todos os serviços healthy
- 1 = Um ou mais serviços unhealthy

### 3. backup.sh - Backup de Volumes
Cria backups comprimidos de todos os volumes Docker.

```bash
# Backup com configurações padrão (mantém últimos 5)
./backup.sh

# Manter últimos 10 backups
./backup.sh --keep 10

# Salvar em diretório customizado
./backup.sh --output /caminho/para/backups
```

**Volumes backup:**
- stj-duckdb-data (banco de dados STJ)
- text-extractor-cache (cache do Marker)
- app-data (dados da aplicação)
- redis-data (persistência Redis)

**Formato:** `backup_YYYYMMDD_HHMMSS_<volume>.tar.gz`

**Restauração:**
```bash
docker run --rm \
  -v <volume>:/target \
  -v <backup-dir>:/backup \
  alpine sh -c 'rm -rf /target/* && tar xzf /backup/<backup-file> -C /target'
```

### 4. rollback.sh - Rollback de Versões
Permite rollback de serviços para versões anteriores das imagens.

```bash
# Modo interativo (menu)
./rollback.sh

# Rollback de serviço específico
./rollback.sh text-extractor

# Rollback de todos os serviços
./rollback.sh all
```

**Processo:**
1. Lista todas as imagens disponíveis do serviço
2. Mostra a versão atual
3. Permite seleção da versão desejada
4. Faz rollback e aguarda health check

### 5. logs.sh - Visualização de Logs
Visualiza logs dos serviços com filtros e colorização.

```bash
# Últimas 100 linhas de todos os serviços
./logs.sh

# Logs de serviço específico
./logs.sh text-extractor

# Seguir logs em tempo real
./logs.sh text-extractor --follow

# Mostrar apenas erros
./logs.sh --errors

# Últimas 50 linhas
./logs.sh --tail 50

# Logs da última hora
./logs.sh --since "1 hour ago"
```

**Filtros de erro:**
- ERROR, CRITICAL
- Exception, Traceback
- Failed

**Colorização:**
- Vermelho: Erros críticos
- Amarelo: Warnings
- Azul: Info
- Verde: Success

## Workflow Recomendado

### Deploy Inicial
```bash
# 1. Configurar variáveis de ambiente
cp ../docker/.env.example ../docker/.env
# Editar .env com suas credenciais

# 2. Deploy
./deploy.sh dev

# 3. Verificar saúde
./health-check.sh
```

### Operação Diária
```bash
# Verificar status
./health-check.sh

# Ver logs
./logs.sh --tail 50

# Seguir logs de serviço específico
./logs.sh text-extractor -f
```

### Manutenção
```bash
# Backup diário (adicionar ao cron)
./backup.sh --keep 7

# Verificar apenas erros
./logs.sh --errors --since "1 hour ago"

# Rollback em caso de problema
./rollback.sh text-extractor
```

### Deploy de Atualização
```bash
# 1. Backup antes de atualizar
./backup.sh

# 2. Deploy nova versão
./deploy.sh prod

# 3. Se houver problema, rollback
./rollback.sh all
```

## Automação com Cron

### Backup Diário
```bash
# Adicionar ao crontab
0 2 * * * /path/to/legal-workbench/docker/scripts/backup.sh --keep 7
```

### Health Check Periódico
```bash
# A cada 5 minutos
*/5 * * * * /path/to/legal-workbench/docker/scripts/health-check.sh --quiet || /path/to/alert-script.sh
```

### Limpeza de Logs
```bash
# Diário, meia-noite
0 0 * * * docker system prune -f --filter "until=24h"
```

## Troubleshooting

### Deploy Falha
```bash
# Ver logs completos
./logs.sh --errors

# Verificar serviços específicos
docker compose ps
docker compose logs <service>

# Tentar novamente
./deploy.sh
```

### Serviço Unhealthy
```bash
# Identificar problema
./health-check.sh

# Ver logs do serviço
./logs.sh <service> --tail 200

# Restart do serviço
docker compose restart <service>
```

### Rollback Necessário
```bash
# Backup do estado atual
./backup.sh

# Rollback
./rollback.sh <service>

# Verificar
./health-check.sh
```

## Integração CI/CD

### GitHub Actions Example
```yaml
- name: Deploy
  run: |
    cd legal-workbench/docker/scripts
    ./deploy.sh prod

- name: Health Check
  run: |
    cd legal-workbench/docker/scripts
    ./health-check.sh --json > health-report.json
```

### Monitoramento
```bash
# Exportar métricas para monitoramento
./health-check.sh --json | jq '.services[] | select(.status != "healthy")'
```

## Requisitos

- Docker >= 20.10
- Docker Compose >= 2.0
- bash >= 4.0
- curl (para health checks)
- jq (para output JSON)

## Notas

- Todos os scripts são **idempotentes** (podem ser executados múltiplas vezes)
- Compatíveis com **Linux/WSL**
- Saída colorizada para melhor visualização
- Exit codes apropriados para automação
- Validação de pré-requisitos antes de executar

## Suporte

Para problemas ou dúvidas:
1. Verificar logs: `./logs.sh --errors`
2. Verificar saúde: `./health-check.sh`
3. Consultar docker-compose.yml para configurações
4. Verificar .env para variáveis de ambiente

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
