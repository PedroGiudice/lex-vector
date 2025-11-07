# OAB Watcher

Monitor de publicações do Diário de Justiça Eletrônico (DJEN) por número de OAB.

## Funcionalidades

1. **Busca por OAB**: Consulta publicações associadas a um número de OAB específico
2. **Download Massivo**: Baixa cadernos de tribunais para períodos determinados
3. **Relatórios**: Gera estatísticas dos dados coletados

## Estrutura de Dados

**Código (versionado no Git):**
- `C:\claude-work\repos\Claude-Code-Projetos\agentes\oab-watcher\`

**Dados (HD externo E:\):**
- `E:\claude-code-data\agentes\oab-watcher\downloads\` - PDFs e JSONs baixados
- `E:\claude-code-data\agentes\oab-watcher\logs\` - Logs de execução
- `E:\claude-code-data\agentes\oab-watcher\outputs\` - Relatórios gerados

## Setup

```powershell
# Navegar até diretório
cd agentes\oab-watcher

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

## Execução

```powershell
# Via PowerShell script
.\run_agent.ps1

# Via Python direto
.venv\Scripts\activate
python main.py
```

## API DJEN - Descobertas e Problemas

### ⚠️ PROBLEMA IDENTIFICADO (2025-11-07)

**A API não filtra corretamente por número de OAB.**

#### Sintomas:
- Endpoint: `GET /api/v1/comunicacao?numero_oab=129021&uf_oab=SP`
- Retorna: 10.000 publicações de diversos tribunais (TJSP, TJRJ, TRF1, etc.)
- **Nenhuma contém o número de OAB solicitado (129021/SP)**
- Campo `numeroOAB` nos destinatários retorna `N/A` em todos os casos

#### Teste Realizado:
```bash
# Busca: OAB 129021/SP
# Resultado: 100 items retornados (paginados de 10.000 total)
# Items contendo "129021": 0 (zero)
```

#### Análise:
A API `comunicaapi.pje.jus.br` é primariamente para **tribunais enviarem comunicações**, não para advogados/sistemas consultarem. Os parâmetros `numero_oab` e `uf_oab` podem:
- Não estar implementados no backend
- Estar sendo ignorados silenciosamente
- Requerer autenticação/permissões específicas

### Arquitetura da API - Dois Sistemas

1. **`comunicaapi.pje.jus.br`** (API de Tribunais)
   - Propósito: Envio de comunicações processuais PELOS tribunais
   - Autenticação: Requer credenciais CNJ Corporativo
   - Acesso: Restrito a tribunais cadastrados
   - Documentação: https://app.swaggerhub.com/apis-docs/cnj/pcp/1.0.0

2. **`comunica.pje.jus.br`** (Portal Público)
   - Propósito: Consulta de publicações PELOS advogados/público
   - Autenticação: Acesso público (sem login)
   - Interface: Web (requer JavaScript)
   - Filtros: Nome, OAB, processo, data, tribunal

### Soluções Propostas

#### Opção 1: Busca do Dia + Filtro Manual (RECOMENDADA)
```python
# 1. Buscar todas as publicações do dia (sem filtro OAB)
GET /api/v1/comunicacao?data_inicio=2025-11-07&data_fim=2025-11-07

# 2. Filtrar manualmente buscando OAB no texto/destinatários
items_filtrados = [
    item for item in items
    if '129021' in json.dumps(item) or
       any(d.get('numeroOAB') == '129021' for d in item.get('destinatarios', []))
]
```

**Prós:**
- Usa API existente
- Não requer scraping
- Controle total sobre filtros

**Contras:**
- Pode retornar muitos resultados (10k+ publicações/dia)
- Requer processamento local
- Possível rate limiting

#### Opção 2: Scraping do Portal Público
Automatizar busca em `comunica.pje.jus.br/consulta` usando Selenium/Playwright

**Prós:**
- Filtros funcionam corretamente
- Dados validados pela interface oficial

**Contras:**
- Requer navegador/automação
- Mais lento
- Sujeito a mudanças na interface

#### Opção 3: Download de Cadernos + Parsing Local
Baixar PDFs completos dos cadernos e fazer OCR/parsing

**Prós:**
- Dados completos e confiáveis
- Independente de filtros da API

**Contras:**
- Muito mais custoso (armazenamento, processamento)
- OCR pode ter erros
- Processamento demorado

### Endpoints Conhecidos

Base URL: `https://comunicaapi.pje.jus.br`

| Endpoint | Método | Propósito | Status |
|----------|--------|-----------|--------|
| `/api/v1/comunicacao` | GET | Busca publicações | ⚠️ Filtro OAB não funciona |
| `/api/v1/comunicacao` | POST | Envia comunicação (tribunais) | 🔒 Requer auth |
| `/api/v1/cadernos` | GET | Lista cadernos disponíveis | ✅ Funcional |

### Próximos Passos

1. **Implementar Opção 1**: Busca do dia + filtro manual
2. **Testar com OAB 129021/SP** em data conhecida
3. **Validar resultados** manualmente no portal `comunica.pje.jus.br`
4. **Documentar performance**: Quantas publicações por dia? Tempo de processamento?

### Recursos Úteis

- **Portal de Consulta**: https://comunica.pje.jus.br/consulta
- **Swagger API**: https://app.swaggerhub.com/apis-docs/cnj/pcp/1.0.0
- **DataJud (CNJ)**: https://www.cnj.jus.br/sistemas/datajud/api-publica/
- **Recorte Digital OAB**: Portal da OAB (serviço automático de notificações)

## Configuração

Edite `config.json` para ajustar:
- Timeout de requisições
- Tribunais monitorados
- Caminhos de dados

## Status

🔴 **Refatoração necessária** - API atual não filtra por OAB corretamente (ver seção "API DJEN - Descobertas e Problemas")
