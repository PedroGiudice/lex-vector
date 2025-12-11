# CLAUDE.md - Legal Workbench

Regras específicas para desenvolvimento no Legal Workbench.

---

## Definition of Done (DoD)

**Uma tarefa SÓ está CONCLUÍDA quando:**

1. ✅ Backend testado e funcional (testes unitários passando)
2. ✅ Integração com UI/Streamlit verificada
3. ✅ Funcionalidade testável via `lw` (alias Streamlit)
4. ✅ Alterações não quebraram outros módulos

> **"Se não funciona na UI, não está pronto."**

---

## Regras Obrigatórias

### 1. UI-First Validation

Toda alteração em `ferramentas/` DEVE ser validada em `modules/`:

```
ferramentas/legal-text-extractor/  →  modules/text_extractor.py
ferramentas/legal-doc-assembler/   →  modules/doc_assembler.py
ferramentas/stj-dados-abertos/     →  modules/stj.py
ferramentas/trello-mcp/            →  modules/trello.py
```

**Checklist pós-alteração de backend:**
- [ ] Wrapper em `modules/` importa corretamente?
- [ ] `render()` executa sem exceção?
- [ ] Resultado aparece na UI?

### 2. Teste End-to-End Obrigatório

Antes de commitar alterações que afetam módulos:

```bash
# 1. Rodar Streamlit
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench
source .venv/bin/activate
streamlit run app.py

# 2. Testar CADA módulo alterado na UI
# 3. Verificar que módulos NÃO alterados continuam funcionando
```

### 3. Teste Empírico via Streamlit

**Regra:** Testes empíricos (com dados reais) SEMPRE via Streamlit.

- Testes unitários = verificam lógica isolada
- Testes empíricos = verificam fluxo completo do usuário
- **Ambos são necessários, mas empírico via UI é obrigatório**

### 4. Isolamento de Erros

Se um módulo quebrar:
1. **NÃO** commitar até corrigir
2. Verificar se a quebra afetou outros módulos
3. Rollback se necessário

---

## Estrutura do Projeto

```
legal-workbench/
├── app.py              # Entry point Streamlit
├── config.yaml         # Configuração de módulos
├── modules/            # Wrappers UI (Streamlit)
│   ├── text_extractor.py
│   ├── doc_assembler.py
│   ├── stj.py
│   └── trello.py
└── ferramentas/        # Backends independentes
    ├── legal-text-extractor/
    ├── legal-doc-assembler/
    ├── stj-dados-abertos/
    └── trello-mcp/
```

---

## Comandos Úteis

```bash
# Iniciar Legal Workbench
lw  # alias definido em ~/.bashrc

# Ou manualmente:
cd ~/claude-work/repos/Claude-Code-Projetos/legal-workbench
source .venv/bin/activate
streamlit run app.py
```

---

## Workflow de Desenvolvimento

```
1. Alterar backend em ferramentas/
       ↓
2. Rodar testes unitários do backend
       ↓
3. Atualizar wrapper em modules/ (se necessário)
       ↓
4. Testar via `lw` (Streamlit)
       ↓
5. Verificar outros módulos não quebraram
       ↓
6. Commitar
```

---

*Última atualização: 2025-12-10*
