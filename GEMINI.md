# Lex-Vector (Legal Workbench) - Contexto para Gemini

Este arquivo define o contexto operacional, ambiente e convenções para o agente Gemini neste projeto, estendendo a configuração global de ~/.claude/GEMINI.md.

## 1. Ambiente e Infraestrutura

- Sistema Operacional: Oracle Linux (VM lw-pro).
- Container Runtime: PODMAN (Rootless).
- NUNCA use o comando docker. Use sempre podman ou podman-compose.
- Socket do Podman: /run/user/1000/podman/podman.sock.
- Diretório de Trabalho: /home/opc/lex-vector.

### Comandos de Container
- Subir serviços: podman-compose up -d
- Ver logs: podman logs -f <container_name>
- Listar containers: podman ps

## 2. Visão Geral do Projeto

Lex-Vector é uma plataforma de automação jurídica focada em extração de documentos (PDF), análise com LLM e aplicativo Desktop.

- Produto Principal: Aplicativo Desktop Multiplataforma (Tauri v2).
- Idioma: Português Brasileiro (pt-BR). Acentuação obrigatória.
- Emojis: PROIBIDO o uso de emojis em qualquer interação ou código gerado.

## 3. Skills e Extensões

O Gemini utiliza seu próprio conjunto de skills nativas e extensões.

### Skills Principais
- tauri-expert: Para desenvolvimento do Core em Rust e Integração.
- frontend-developer: Para React 18, Vite e TypeScript.
- backend-architect: Para design de APIs e serviços Python.
- oci-gha: Para automação em Oracle Cloud e GitHub Actions.

### Extensão Nano Banana
- Geração de imagens, ícones e diagramas técnicos.
- Edição e restauração de ativos visuais.

## 4. Regras Invioláveis

1. Podman: Toda interação com containers deve usar Podman.
2. Sem Emojis: Comunicação e documentação devem ser limpas e profissionais, sem emojis.
3. Ambientes Virtuais: Python deve rodar sempre dentro de .venv.
4. Dados: Dados sensíveis ficam fora do repositório (~/claude-code-data/).

## 5. Stack Tecnológico

- Desktop: Tauri v2 (Rust).
- Frontend: React 18 (TypeScript, Zustand, TanStack Query, Tailwind).
- Backend: Python 3.12+ (FastAPI).
- Infra: Podman em Oracle VM.
