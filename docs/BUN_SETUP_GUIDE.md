# Guia de Setup do Bun para lex-vector

**Criado**: 2025-12-10
**Versão**: Bun 1.3.x
**Referência**: ARCHITECTURE.md (ADR-005)

---

## TL;DR - Setup Rápido

```bash
# 1. Instalar Bun
curl -fsSL https://bun.sh/install | bash

# 2. Adicionar ao PATH (já feito pelo installer)
source ~/.bashrc  # ou reiniciar terminal

# 3. Verificar instalação
bun --version

# 4. Testar hooks (no diretório do projeto)
cd ~/claude-work/repos/lex-vector
bun run .claude/hooks/prompt-enhancer.js <<< '{"prompts":[{"content":"test"}]}'
```

---

## 1. Instalação do Bun

### Pré-requisitos

```bash
# Ubuntu/Debian WSL2
sudo apt update && sudo apt install -y unzip
```

### Instalação Oficial

```bash
curl -fsSL https://bun.sh/install | bash
```

**Saída esperada**:
```
bun was installed successfully to ~/.bun/bin/bun

To get started, run:
  source /home/user/.bashrc
```

### Verificação

```bash
source ~/.bashrc
bun --version  # Deve mostrar 1.3.x
which bun      # Deve mostrar ~/.bun/bin/bun
```

---

## 2. Estrutura de Arquivos Afetados

```
lex-vector/
├── .claude/
│   ├── settings.json          # Hooks configurados com "bun run"
│   ├── hooks/
│   │   ├── hook-wrapper.js    # Executado via "bun run"
│   │   ├── prompt-enhancer.js # Executado via "bun run"
│   │   ├── context-collector.js
│   │   └── vibe-analyze-prompt.js
│   └── statusline/
│       ├── professional-statusline.js  # Executado via "bun run"
│       └── hybrid-powerline-statusline.js
├── Word-Templates/
│   ├── package.json           # Deps: docx
│   └── convert-md-to-docx.js  # Executável com "bun run"
└── ARCHITECTURE.md            # ADR-005: Bun para Hooks JS
```

---

## 3. Testes de Validação

### Hooks JavaScript

```bash
cd ~/claude-work/repos/lex-vector

# Hook wrapper
bun run .claude/hooks/hook-wrapper.js .claude/hooks/prompt-enhancer.js <<< '{"prompts":[{"content":"test"}]}'
# Saída esperada: vazia (silent success) ou JSON

# Statusline
bun run .claude/statusline/professional-statusline.js
# Saída esperada: statusline formatada

# Word converter (após bun/npm install)
cd Word-Templates
bun run convert-md-to-docx.js CONTESTACAO_REDEBRASIL_x_SALESFORCE.md test.docx
# Saída esperada: "Conversão concluída com sucesso!"
```

### Benchmark Node vs Bun

```bash
cd ~/claude-work/repos/lex-vector

# Node.js
time for i in {1..5}; do node .claude/hooks/hook-wrapper.js .claude/hooks/prompt-enhancer.js <<< '{"prompts":[{"content":"test"}]}' 2>/dev/null; done

# Bun
time for i in {1..5}; do bun run .claude/hooks/hook-wrapper.js .claude/hooks/prompt-enhancer.js <<< '{"prompts":[{"content":"test"}]}' 2>/dev/null; done

# Bun deve ser ~25% mais rápido
```

---

## 4. Claude Code + Bun

### Instalação do Claude Code

Claude Code e Bun são **independentes**. Instale separadamente:

```bash
# Claude Code (via npm/yarn - não requer Bun)
npm install -g @anthropic-ai/claude-code

# OU se preferir instalar via Bun:
bun install -g @anthropic-ai/claude-code
```

**Nota**: A instalação via npm ou bun funciona igualmente. O importante é que os **hooks JS** do projeto usem `bun run`.

### Verificar settings.json

O arquivo `.claude/settings.json` já deve estar configurado com `bun run`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "command": "bun run .claude/hooks/hook-wrapper.js .claude/hooks/prompt-enhancer.js"
      }
    ]
  }
}
```

---

## 5. Troubleshooting

### Bun não encontrado

```bash
# Adicionar ao PATH manualmente
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# Persistir no .bashrc
echo 'export BUN_INSTALL="$HOME/.bun"' >> ~/.bashrc
echo 'export PATH="$BUN_INSTALL/bin:$PATH"' >> ~/.bashrc
```

### 401 no bun install

Se `bun install` retornar 401, use npm como fallback:

```bash
npm install  # Instala em node_modules
bun run script.js  # Bun usa node_modules normalmente
```

### Hooks falhando

```bash
# Verificar logs
tail -50 ~/.vibe-log/hooks.log

# Testar hook isolado
bun run .claude/hooks/prompt-enhancer.js <<< '{"prompts":[{"content":"test"}]}'
```

---

## 6. Decisões Arquiteturais

### Por que Bun?

| Métrica | Node.js | Bun | Diferença |
|---------|---------|-----|-----------|
| Startup | ~42ms | ~8ms | **5x mais rápido** |
| npm install | ~30s | ~1.2s | **25x mais rápido** |
| Hook execution | ~226ms | ~173ms | **~25% mais rápido** |

### Compatibilidade

- ✅ Bun é drop-in replacement para Node.js
- ✅ Usa mesmos `node_modules`
- ✅ Suporta CommonJS e ESM
- ✅ API compatível com Node.js

### Fallback

Se Bun não estiver disponível, Node.js funciona normalmente:

```bash
# Verificar disponibilidade
command -v bun && bun run script.js || node script.js
```

---

## 7. Checklist de Setup Completo

- [ ] Bun instalado (`bun --version` funciona)
- [ ] Claude Code instalado (`claude --version` funciona)
- [ ] `.claude/settings.json` usa `bun run` nos hooks
- [ ] Hooks executam sem erro
- [ ] Statusline funciona
- [ ] Word-Templates tem dependências instaladas

---

## Prompt para Claude Code CLI

Copie e cole este prompt para configurar um novo ambiente:

```
Preciso configurar o ambiente de desenvolvimento para lex-vector.

Tarefas:
1. Verificar se Bun está instalado (`bun --version`)
   - Se não: `curl -fsSL https://bun.sh/install | bash` (pode precisar de `unzip`)
2. Verificar se Claude Code está instalado (`claude --version`)
3. Navegar até o projeto e verificar hooks:
   - `bun run .claude/hooks/hook-wrapper.js .claude/hooks/prompt-enhancer.js <<< '{"prompts":[{"content":"test"}]}'`
4. Instalar deps do Word-Templates:
   - `cd Word-Templates && bun install` (ou npm se bun falhar)
5. Confirmar que ARCHITECTURE.md menciona ADR-005 (Bun para Hooks JS)

Reporte o status de cada item.
```

---

**Última atualização**: 2025-12-10
