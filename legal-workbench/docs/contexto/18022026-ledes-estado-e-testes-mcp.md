# Contexto: Estado do LEDES Converter e Preparacao para Testes MCP

**Data:** 2026-02-18
**Sessao:** Revisao de estado + build AppImage
**Branch:** work/session-20260212-083652 (mergeado no main, sem diff pendente)

---

## O que foi feito

### 1. Levantamento completo do estado via cogmem + Gemini Bridge

Revisao da memoria cognitiva e exploracao do codebase via Gemini para mapear
o estado atual do modulo LEDES Converter apos ~2 semanas sem tocar no projeto.

### 2. Verificacao de dados persistidos (matters)

Confirmado que o SQLite (`ferramentas/ledes-converter/data/matters.db`) contem
4 matters ativos:

| Matter | ID |
|--------|----|
| BRA/STLandATDIL/CRM/Governance | LS-2025-23274 |
| CMR General Litigation Matters | LS-2020-05805 |
| FY26 - General Employment Advice (Brazil) | LS-2025-22672 |
| [WA-27] Brazil - Employment Advice | LS-2026-24216 |

### 3. Build AppImage

Build Tauri concluido com sucesso (~60s, cache quente):
```
Legal Workbench_0.1.4_amd64.AppImage
```
Enviado via SCP para `cmr-auto@100.102.249.9:~/`.

### 4. Issues Linear -- todos LEDES fechados

Issues CMR-23 a CMR-29 todos em status Done. Abertos no projeto sao apenas:
- CMR-22 (timeout frontend, text-extractor) -- In Progress
- CMR-21 (Modal cold start) -- Backlog

## Arquitetura atual do LEDES Converter

```
Frontend (React/Zustand/Tailwind, Tauri native APIs)
    |
    | HTTP via axios (porta 8003 ou proxy /api/ledes)
    v
Backend (FastAPI, porta 8003)
    |-- POST /convert/docx-to-ledes    (upload DOCX)
    |-- POST /convert/structured       (JSON estruturado)
    |-- POST /convert/text-to-ledes    (texto puro)
    |-- POST /convert/batch            (multiplos arquivos)
    |-- POST /validate                 (validacao LEDES 1998B)
    |-- GET/POST/PUT/DELETE /matters   (CRUD matters SQLite)
    |-- GET /health
    |
    v
Modules: ledes_generator.py, ledes_validator.py, matter_store.py, task_codes.py
Tests: 128 cases em 5 arquivos (test_api, test_generator, test_matter_store, test_task_codes, test_validator)
```

## API rodando

Health check OK em `localhost:8003/health`.
Container Docker ativo via docker-compose (Traefik em /api/ledes).

## Pendencias identificadas

1. **Branch morto** -- `work/session-20260212-083652` pode ser deletado (100% mergeado)
2. **Testes frontend inexistentes** -- nao ha testes de renderizacao/integracao React
3. **Deletions no git status** -- arquivos removidos (ISSUES.md, DISASTER_HISTORY.md, infra/oracle/*) nao commitados

## Decisoes tomadas

- Regex fragil e aceitavel por ora (uso pessoal, template CMR unico)
- Foco em manter dados e ter LEDES funcional, nao em robustez generica
