# Legal Workbench - Known Issues & Migration Notes

## Status Atual (2025-12-12)

### Infraestrutura: OPERACIONAL

Todos os 6 serviços Docker estão **online e healthy**:

| Serviço | Porta | Status |
|---------|-------|--------|
| lw-hub (Streamlit) | 8501 | Online |
| lw-text-extractor | 8001 | Online |
| lw-doc-assembler | 8002 | Online |
| lw-stj-api | 8003 | Online |
| lw-trello-mcp | 8004 | Online |
| lw-redis | 6379 | Online |

---

## PROBLEMA CRITICO: Divergencia Frontend vs Backend

### Resumo

O layout atual da aplicacao Streamlit **NAO REFLETE** a proposta real de cada modulo. Existe uma **divergencia significativa** entre:

1. O que os backends sao capazes de fazer
2. O que a UI expoe ao usuario

### Divergencias por Modulo

#### 1. Trello MCP

| Backend | Frontend Atual |
|---------|----------------|
| Extrai dados de quadros existentes | Apenas cria cartoes |
| Lista quadros do usuario | Nao expoe |
| Extrai cards com labels, checklists, etc. | Nao expoe |
| Extrai dados estruturados | Nao expoe |

**Proposta Original:** Ferramenta de **EXTRACAO** de dados do Trello para alimentar outros modulos.

#### 2. STJ Dados Abertos

| Backend | Frontend Atual |
|---------|----------------|
| Download retroativo em massa | Apenas consulta simples |
| Sincronizacao incremental | Nao expoe |
| Consulta local DuckDB | Nao expoe |
| Estatisticas do banco local | Nao expoe |
| Filtros avancados (relator, classe, periodo) | Nao expoe |

**Proposta Original:** Sistema de **COLETA E ARMAZENAMENTO LOCAL** de toda jurisprudencia do STJ.

#### 3. Legal Doc Assembler

| Backend | Frontend Atual |
|---------|----------------|
| Sistema de templates .docx | Formulario basico |
| Upload de documento base | Nao expoe |
| Definicao de placeholders/variaveis | Nao expoe |
| Conexao com fontes de dados (Trello, etc.) | Nao expoe |
| Geracao em lote | Nao expoe |

**Proposta Original:** Sistema de **TEMPLATES** onde usuario transforma .docx em template, define variaveis, e gera documentos em lote.

#### 4. Text Extractor

| Backend | Frontend Atual |
|---------|----------------|
| Extracao via Marker | Funcional |
| Jobs assincronos (Celery) | Parcialmente exposto |
| Preview de resultados | Parcialmente exposto |

**Status:** Mais alinhado que os outros, mas ainda com gaps na UX.

---

## DECISAO: Migracao de Framework UI

### Motivo

O **Streamlit** possui limitacoes esteticas e de UX que **impedem sua adocao como interface de produto final**:

1. Layout rigido baseado em colunas
2. Recarregamento completo da pagina em cada interacao
3. Customizacao CSS limitada
4. Componentes com aparencia "prototipo"
5. Sem suporte adequado a estados complexos
6. Performance degradada com muitos elementos

### Plano

A UI atual em Streamlit serve como **MVP funcional** para validar backends.

A migracao para um framework frontend adequado sera realizada apos:
1. Backends estabilizados
2. APIs documentadas
3. Definicao do novo stack (React/Next.js, Vue, ou similar)

---

## Proximos Passos

1. [ ] Manter Streamlit apenas como interface de desenvolvimento/debug
2. [ ] Documentar APIs de cada backend (OpenAPI/Swagger)
3. [ ] Definir novo framework frontend
4. [ ] Criar nova UI que exponha 100% das funcionalidades backend
5. [ ] Alinhar UX com proposta original de cada modulo

---

*Documento criado: 2025-12-12*
*Status: Aguardando decisao sobre novo framework UI*
