# Análise Completa do Claude-Code-Projetos
## Base para One-Pager

---

## 1. VISÃO GERAL DO PROJETO

### Objetivo Principal
O **Claude-Code-Projetos** é uma plataforma modular de automação jurídica que combina:
- **Legal Workbench**: Dashboard web para gestão de processos jurídicos
- **Agentes Especializados**: Suite de agentes Claude para tarefas específicas (scraping, conversão, análise)
- **Comandos CLI**: Ferramentas de linha de comando para automação e consultas

### Problema que Resolve
**Desafios no trabalho jurídico:**
- Acesso fragmentado a múltiplas fontes (STJ, STF, tribunais estaduais)
- Conversão manual de formatos (LEDES, DOCX, PDF)
- Falta de integração entre ferramentas
- Processos repetitivos e time-consuming

**Solução:**
Plataforma unificada que automatiza download, conversão, extração e análise de dados jurídicos através de:
- Interface web centralizada
- Agentes especializados para cada tribunal/formato
- Comandos CLI para integração com workflows existentes

### Usuários-Alvo
1. **Escritórios de Advocacia**: Gestão de processos em massa, extração de dados, conversão de timesheet
2. **Departamentos Jurídicos**: Consulta a jurisprudência, acompanhamento processual
3. **Profissionais Jurídicos**: Advogados, paralegals, analistas que precisam de automação

---

## 2. COMPONENTES PRINCIPAIS

### A. Legal Workbench (Dashboard Web)
**Localização:** `/home/lgp/Claude-Code-Projetos/legal-workbench/`

**Descrição:**
Dashboard Flask para gestão centralizada de processos jurídicos com múltiplas ferramentas integradas.

**Funcionalidades:**
1. **STJ (Superior Tribunal de Justiça)**
   - Download massivo de processos (retroativo por data)
   - Exportação para planilha Excel
   - Interface para consulta individual

2. **LEDES Converter**
   - Conversão DOCX → LEDES 1998B
   - Validação de formato
   - Parser de timesheet estruturado

3. **Text Extractor**
   - Extração de texto de PDFs
   - Suporte a múltiplos arquivos
   - Interface drag-and-drop

4. **Autenticação e Segurança**
   - Login via credenciais
   - CSRF protection
   - Gestão de sessões

**Stack Técnico:**
- **Backend**: Flask, SQLAlchemy
- **Frontend**: Jinja2, Bootstrap, JavaScript
- **Scraping**: Selenium WebDriver (headless Chrome)
- **Processamento**: pandas, python-docx, PyPDF2

### B. Agentes Especializados
**Localização:** `/home/lgp/Claude-Code-Projetos/agentes/`

#### 1. **STJ Agent**
- **Propósito**: Automação de downloads do STJ
- **Capacidades**:
  - Download massivo de processos
  - Extração de metadados
  - Organização por data
  - Exportação para Excel

#### 2. **LEDES Agent**
- **Propósito**: Conversão de timesheet para formato LEDES
- **Capacidades**:
  - Parser de DOCX estruturado
  - Validação de formato LEDES 1998B
  - Mapeamento de colunas
  - Geração de arquivo .ledes

#### 3. **Text Extractor Agent**
- **Propósito**: Extração de texto de PDFs
- **Capacidades**:
  - Processamento batch
  - Preservação de formatação
  - Output em texto puro

#### 4. **Gemini Assistant Agent**
- **Propósito**: Context offloading e análise de grandes volumes
- **Capacidades**:
  - Resumo de arquivos > 500 linhas
  - Análise de diffs grandes
  - Filtragem de logs
  - Mapeamento de estruturas

### C. Comandos CLI
**Localização:** `/home/lgp/Claude-Code-Projetos/comandos/`

#### Lista de Comandos:

1. **cnj-scraper** - Scraping de processos do CNJ
2. **convert-ledes** - CLI para conversão DOCX → LEDES
3. **extract-text** - CLI para extração de texto de PDFs
4. **stj-downloader** - Download massivo de processos STJ
5. **merge-pdfs** - Combinação de múltiplos PDFs
6. **validate-ledes** - Validação de arquivos LEDES

### D. Shared Library
**Localização:** `/home/lgp/Claude-Code-Projetos/shared/`

**Estrutura:**
```
shared/
├── utils/
│   ├── path_utils.py      # Gestão de paths dinâmicos
│   ├── logger.py          # Sistema de logging
│   └── config.py          # Configurações globais
├── scrapers/
│   ├── stj_scraper.py     # Lógica de scraping STJ
│   └── base_scraper.py    # Classe base para scrapers
└── parsers/
    ├── ledes_parser.py    # Parser LEDES
    └── pdf_parser.py      # Parser PDF
```

---

## 3. STACK TECNOLÓGICA

### Linguagens
- **Python 3.11+** (linguagem principal)
- **JavaScript/HTML/CSS** (frontend Legal Workbench)
- **Shell/Bash** (scripts de automação)

### Frameworks e Bibliotecas

#### Backend
- **Flask 3.x**: Framework web
- **SQLAlchemy**: ORM para banco de dados
- **Selenium 4.x**: Automação de browser (scraping)
- **BeautifulSoup4**: Parsing de HTML
- **pandas**: Manipulação de dados

#### Processamento de Documentos
- **python-docx**: Leitura/escrita de arquivos DOCX
- **PyPDF2**: Processamento de PDFs
- **openpyxl**: Manipulação de Excel

#### Segurança e Validação
- **Flask-WTF**: Proteção CSRF
- **Werkzeug**: Hashing de senhas
- **python-dotenv**: Gestão de secrets

### Infraestrutura
- **WSL2 (Ubuntu)**: Ambiente de desenvolvimento
- **ChromeDriver**: Browser headless para Selenium
- **Git**: Controle de versão
- **venv**: Ambientes virtuais Python

---

## 4. PROPOSIÇÃO DE VALOR

### Diferenciais Técnicos

1. **Modularidade Radical** - Cada agente é independente e especializado
2. **Context Offloading via Gemini** - Processamento de grandes volumes sem overhead
3. **Scraping Robusto** - Selenium com headless Chrome para sites dinâmicos
4. **Paths Dinâmicos** - Zero hardcoding de caminhos
5. **Arquitetura Orientada a Lições** - `DISASTER_HISTORY.md` documenta erros passados

### Diferenciais de Produto

1. **Integração Multi-Tribunal**: STJ, STF, tribunais estaduais em uma única interface
2. **Conversão LEDES**: Poucos produtos oferecem LEDES 1998B nativo
3. **Automação End-to-End**: Download → Processamento → Exportação sem intervenção manual
4. **Open Source Mindset**: Código modular e extensível

---

## 5. STATUS ATUAL

### Componentes Funcionais ✅

#### Legal Workbench
- ✅ **STJ Module**: Download massivo, exportação Excel
- ✅ **LEDES Converter**: DOCX → LEDES 1998B com validação
- ✅ **Text Extractor**: PDF → texto com interface drag-and-drop
- ✅ **Autenticação**: Login, logout, proteção de rotas

#### Agentes
- ✅ **STJ Agent**: Operacional com retry e logging
- ✅ **LEDES Agent**: Parser completo e validador
- ✅ **Text Extractor Agent**: Batch processing funcional
- ✅ **Gemini Assistant**: Context offloading ativo

### Em Desenvolvimento 🚧

1. **STF Module** (planejado)
2. **Tribunais Estaduais** (planejado)
3. **OCR Module** (planejado)
4. **API REST** (planejado)

---

## 6. CASOS DE USO CONCRETOS

### Caso 1: Escritório - Extração de Timesheet
**Fluxo:** Upload DOCX → Conversão LEDES → Download validado
**Valor:** 4 horas/mês → 10 minutos

### Caso 2: Departamento Jurídico - Monitoramento de Jurisprudência
**Fluxo:** Filtro STJ → Download massivo → Exporta Excel
**Valor:** 200+ processos em 30 minutos (vs. dias manual)

### Caso 3: Advogado Solo - Análise de Contratos em PDF
**Fluxo:** Upload PDFs → Extração de texto → Busca textual
**Valor:** Texto pesquisável sem OCR pago

### Caso 4: Paralegals - Automação via CLI
**Fluxo:** Scripts automatizados via cron job
**Valor:** Pipeline automatizado, zero intervenção

### Caso 5: Analista - Pesquisa de Precedentes
**Fluxo:** Busca STJ → Lista processos → Exporta relevantes
**Valor:** Pesquisa em 15 minutos (vs. horas no site oficial)

---

## 7. EQUIPE

- **PGR (Pedro)**: Dono do projeto, decisões de produto
- **LGP (Leo)**: Contribuidor ativo, sócio, implementação técnica

---

## 8. MÉTRICAS DE SUCESSO

### Técnicas
- Redução de tempo de processamento: 90%+
- Taxa de sucesso de scraping: 95%+
- Acurácia de conversão LEDES: 100%

### Negócio
- Economia de horas/mês: 20-40 horas por usuário
- ROI: Payback em < 2 meses (vs. ferramentas pagas)

---

## CONCLUSÃO

**Proposta de Valor Única:**
"Automatize 90% do trabalho jurídico repetitivo com uma plataforma modular que integra scraping, conversão e análise em um único ecossistema."
