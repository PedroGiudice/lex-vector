# Arquitetura do Sistema

## Visao Geral

Sistema de automacao juridica baseado em agentes Python para monitoramento e processamento de publicacoes.

## Separacao em 3 Camadas

### CAMADA 1: CODIGO
- Localizacao: ~/claude-work/repos/Claude-Code-Projetos/
- Conteudo: Codigo-fonte Python, configuracoes
- Versionamento: Git obrigatorio
- Sincronizacao: git push/pull entre maquinas

### CAMADA 2: AMBIENTE
- Localizacao: .venv/ dentro de cada projeto
- Conteudo: Interpretador Python, pacotes instalados
- Versionamento: NUNCA (em .gitignore)
- Recriacao: Via requirements.txt

### CAMADA 3: DADOS
- Localizacao: ~/claude-code-data/ (configuravel)
- Conteudo: Downloads, logs, outputs
- Versionamento: NUNCA
- Portabilidade: Backup/restore apenas

## Fluxo de Dados

```
API DJEN → oab-watcher → Downloads (~/claude-code-data)
                       ↓
                   legal-lens → Analise
                       ↓
                   Outputs (~/claude-code-data) → Relatorios
```

## Status

Em desenvolvimento - Documentacao sera expandida conforme implementacao
