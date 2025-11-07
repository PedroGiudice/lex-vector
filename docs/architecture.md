# Arquitetura do Sistema

## Visão Geral

Sistema de automação jurídica baseado em agentes Python para monitoramento e processamento de publicações.

## Separação em 3 Camadas

### CAMADA 1: CÓDIGO
- **Localização:** C:\claude-work\repos\Claude-Code-Projetos\
- **Conteúdo:** Código-fonte Python, configurações
- **Versionamento:** Git obrigatório
- **Sincronização:** git push/pull entre máquinas

### CAMADA 2: AMBIENTE
- **Localização:** .venv/ dentro de cada projeto
- **Conteúdo:** Interpretador Python, pacotes instalados
- **Versionamento:** NUNCA (em .gitignore)
- **Recriação:** Via requirements.txt

### CAMADA 3: DADOS
- **Localização:** E:\claude-code-data\
- **Conteúdo:** Downloads, logs, outputs
- **Versionamento:** NUNCA
- **Portabilidade:** HD externo físico apenas

## Fluxo de Dados

```
API DJEN → oab-watcher → Downloads (E:\)
                       ↓
                   legal-lens → Análise
                       ↓
                   Outputs (E:\) → Relatórios
```

## Status

🟡 **Em desenvolvimento** - Documentação será expandida conforme implementação
