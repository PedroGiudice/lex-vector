# Documentação - Jurisprudência Collector

Índice completo da documentação do sistema de coleta e processamento de jurisprudência.

## Mapa de Documentação

### Comece Aqui

1. **[QUICK_START.md](QUICK_START.md)** ⚡ *5 minutos*
   - Instalação rápida
   - Primeiro processamento
   - Referência rápida

### Guias Completos

2. **[INSTALACAO.md](INSTALACAO.md)** 🔧 *20 minutos*
   - Verificar requisitos
   - Criar virtual environment
   - Instalar dependências
   - Validar instalação
   - Criar banco de dados
   - Troubleshooting de instalação

3. **[USO_BASICO.md](USO_BASICO.md)** 📚 *30 minutos*
   - Processamento de publicações
   - Baixar dados da API DJEN
   - Processar lotes
   - Inserir no banco
   - Consultas básicas
   - Busca textual (FTS5)
   - Exemplos completos

4. **[CONFIGURACAO.md](CONFIGURACAO.md)** ⚙️ *30 minutos*
   - Variáveis de ambiente
   - Logging avançado
   - Otimização de API
   - Otimização de banco
   - Padrões customizados
   - Backup e manutenção

5. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** 🔍 *Sob demanda*
   - Problemas de instalação
   - Problemas de processamento
   - Problemas de banco
   - Problemas de configuração
   - FAQ e casos especiais

### Referências Técnicas

6. **[../../docs/ARQUITETURA_JURISPRUDENCIA.md](../../docs/ARQUITETURA_JURISPRUDENCIA.md)** 🏗️
   - Visão geral de arquitetura
   - Schema do banco de dados
   - Pipeline de ingestão
   - Estratégia de atualização
   - Estimativa de armazenamento

7. **[../../docs/API_TESTING_REPRODUCIBLE.md](../../docs/API_TESTING_REPRODUCIBLE.md)** 🧪
   - Testes da API DJEN
   - Testes da API DataJud
   - Comandos curl replicáveis
   - Schemas e respostas reais

---

## Roteiros de Aprendizado

### Para Iniciante

```
1. Ler QUICK_START.md (5 min)
   ↓
2. Seguir INSTALACAO.md (20 min)
   ↓
3. Executar exemplo em USO_BASICO.md (10 min)
   ↓
✅ Sistema funcionando!
```

**Tempo total:** ~35 minutos

### Para Desenvolvedor

```
1. Ler QUICK_START.md (5 min)
   ↓
2. Ler ARQUITETURA_JURISPRUDENCIA.md (15 min)
   ↓
3. Executar INSTALACAO.md (20 min)
   ↓
4. Estudar USO_BASICO.md (30 min)
   ↓
5. Explorar CONFIGURACAO.md (20 min)
   ↓
✅ Pronto para customizar!
```

**Tempo total:** ~90 minutos

### Para Admin/Ops

```
1. Ler ARQUITETURA_JURISPRUDENCIA.md (15 min)
   ↓
2. Seguir INSTALACAO.md (20 min)
   ↓
3. Ler CONFIGURACAO.md seção de backup (10 min)
   ↓
4. Ler TROUBLESHOOTING.md (15 min)
   ↓
✅ Pronto para manutenção!
```

**Tempo total:** ~60 minutos

---

## Estrutura de Diretórios

```
jurisprudencia-collector/
├── docs/                              # VOCÊ ESTÁ AQUI
│   ├── INDEX.md                       # Este arquivo
│   ├── QUICK_START.md                 # Comece aqui
│   ├── INSTALACAO.md                  # Instalação passo-a-passo
│   ├── USO_BASICO.md                  # Exemplos práticos
│   ├── CONFIGURACAO.md                # Customizações
│   └── TROUBLESHOOTING.md             # Solução de problemas
│
├── src/
│   ├── __init__.py
│   ├── processador_texto.py           # Módulo principal
│   └── downloader.py                  # Downloader (futuro)
│
├── .venv/                             # Virtual environment (git ignore)
├── schema.sql                         # Schema do banco SQLite
├── requirements.txt                   # Dependências Python
├── README.md                          # Overview do projeto
├── main.py                            # Script principal (futuro)
└── test_processador_stj.py            # Testes com dados reais
```

---

## Tópicos Principais

### Processamento de Publicações

**Documentos relevantes:**
- USO_BASICO.md - Seção 1 (Processamento Simples)
- USO_BASICO.md - Seção 2 (Baixar e Processar)
- ARQUITETURA_JURISPRUDENCIA.md - Seção "Pipeline de Ingestão"

**Funções principais:**
```python
processar_publicacao()      # Processa dados brutos
extrair_ementa()            # Extrai ementa
extrair_relator()           # Extrai relator
classificar_tipo()          # Classifica tipo
gerar_hash_sha256()         # Gera hash
validar_publicacao_processada()  # Valida
```

### Banco de Dados

**Documentos relevantes:**
- INSTALACAO.md - Seção 7 (Criar Banco)
- USO_BASICO.md - Seção 3-5 (Inserir e Consultar)
- ARQUITETURA_JURISPRUDENCIA.md - Schema completo

**Tabelas principais:**
```
publicacoes         # Publicações jurídicas
embeddings          # Vetores de embedding
chunks              # Chunking para textos longos
downloads_historico # Histórico de downloads
temas               # Categorias temáticas
```

### API DJEN

**Documentos relevantes:**
- USO_BASICO.md - Seção 2 (Baixar da API)
- CONFIGURACAO.md - Seção "Configuração de API DJEN"
- API_TESTING_REPRODUCIBLE.md - Testes completos

**Endpoints:**
```
GET https://comunicaapi.pje.jus.br/api/v1/comunicacao
Parâmetros: dataInicio, dataFim, siglaTribunal, limit, offset
```

### Busca e Consultas

**Documentos relevantes:**
- USO_BASICO.md - Seção 5 (Busca FTS5)
- CONFIGURACAO.md - Seção "Configuração de Filtros"

**Modos de busca:**
- Full-text search (FTS5) - busca por termo
- Busca estruturada - filtros por tribunal, tipo, data
- Busca semântica - embeddings (futuro)

---

## Recursos

### Integrações

| Recurso | Documentação |
|---------|--------------|
| API DJEN | API_TESTING_REPRODUCIBLE.md |
| SQLite 3 | ARQUITETURA_JURISPRUDENCIA.md - Schema |
| Beautiful Soup | USO_BASICO.md - Processamento |
| Requests | CONFIGURACAO.md - API DJEN |

### Padrões Testados

| Padrão | Referência | Sucesso |
|--------|-----------|---------|
| Extração de ementa | USO_BASICO.md 1.2 | ~100% STJ |
| Extração de relator | USO_BASICO.md 1.2 | ~6% (em desenvolvimento) |
| Classificação de tipo | USO_BASICO.md 1.2 | ~95% |
| Processamento completo | test_processador_stj.py | ~100% |

---

## FAQ Rápido

**P: Quero começar a usar agora.**
R: → QUICK_START.md

**P: Preciso instalar desde zero.**
R: → INSTALACAO.md

**P: Quero entender a arquitetura.**
R: → ../../docs/ARQUITETURA_JURISPRUDENCIA.md

**P: Tenho um erro específico.**
R: → TROUBLESHOOTING.md

**P: Quero customizar o comportamento.**
R: → CONFIGURACAO.md

**P: Quero ver exemplos de código.**
R: → USO_BASICO.md

---

## Versionamento

**Documentação versão:** 1.0
**Data de atualização:** 2025-11-20
**Compatibilidade:**
- Python 3.12+
- WSL2/Linux (Ubuntu 24.04 LTS)
- SQLite 3.x
- beautifulsoup4 4.12.2
- lxml 4.9.3
- requests 2.31.0

---

## Manutenção da Documentação

Ao atualizar o código, mantenha esta documentação sincronizada:

1. **Adicionar novo módulo?** → Criar seção em USO_BASICO.md
2. **Mudar comportamento?** → Atualizar exemplo em USO_BASICO.md
3. **Novo erro?** → Adicionar em TROUBLESHOOTING.md
4. **Nova config?** → Atualizar CONFIGURACAO.md
5. **Mudança arquitetural?** → Atualizar ARQUITETURA_JURISPRUDENCIA.md

---

## Contribuir

Para sugerir melhorias na documentação:

1. Consulte o documento relevante
2. Identifique o problema (informação faltante, imprecisão, etc)
3. Abra issue ou PR com sugestão

---

**Última atualização:** 2025-11-20
**Mantido por:** Claude Code (Sonnet 4.5)
