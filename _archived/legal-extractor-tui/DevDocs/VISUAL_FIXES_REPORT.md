# Legal Extractor TUI - Visual Fixes Report

**Data:** 2025-11-28
**Problema:** Fundo azul "estética 2008" em vez do tema vibe-neon (Dracula/Cyberpunk)

---

## Diagnóstico

### Causa Raiz: Cores Hardcoded nos Widgets Powerline

Os widgets Powerline estavam usando cores **hardcoded** ("blue", "dark_blue", "white", "green") em vez de variáveis do tema vibe-neon.

#### Arquivos Afetados

1. **powerline_status.py** (3 ocorrências)
   - Linha 150: `PowerlineSegment(self.app_name, "white", "blue", icon="🚀")`
   - Linha 151: `PowerlineSegment(self.version, "white", "dark_blue")`
   - Linha 159: `PowerlineSegment(time_str, "white", "green", icon="🕒")`
   - Linhas 245-247: Exemplo de footer com cores hardcoded

2. **powerline_breadcrumb.py** (2 ocorrências)
   - Linha 75: `bg_color: str = "blue"` (valor padrão)
   - Linha 76: `separator_color: str = "dark_blue"` (valor padrão)

3. **widgets/__init__.py** (1 ocorrência)
   - Linha 51: `PowerlineSegment("Status", "white", "blue")`

4. **models/log_entry.py** (1 ocorrência)
   - Linha 25: `self.INFO: "blue"` (cor de log INFO)

#### Impacto Visual

Essas cores hardcoded criavam:
- Fundo azul forte (#0000FF ou similar) em vez do tema escuro (#0d0d0d, #1a1a2e)
- Contraste excessivo (estilo Windows XP/2008)
- Ignoravam completamente o tema vibe-neon registrado

---

## Correções Aplicadas

### 1. powerline_status.py

**ANTES:**
```python
left_segments = [
    PowerlineSegment(self.app_name, "white", "blue", icon="🚀"),
    PowerlineSegment(self.version, "white", "dark_blue"),
]

right_segments = [
    PowerlineSegment(time_str, "white", "green", icon="🕒"),
]
```

**DEPOIS:**
```python
left_segments = [
    PowerlineSegment(self.app_name, "$foreground", "$primary", icon="🚀"),
    PowerlineSegment(self.version, "$foreground", "$primary-darken-1"),
]

right_segments = [
    PowerlineSegment(time_str, "$foreground", "$success", icon="🕒"),
]
```

### 2. powerline_breadcrumb.py

**ANTES:**
```python
def __init__(
    self,
    fg_color: str = "white",
    bg_color: str = "blue",
    separator_color: str = "dark_blue",
):
```

**DEPOIS:**
```python
def __init__(
    self,
    fg_color: str = "$foreground",
    bg_color: str = "$primary",
    separator_color: str = "$primary-darken-1",
):
```

### 3. widgets/__init__.py

**ANTES:**
```python
powerline = PowerlineBar([
    PowerlineSegment("Status", "white", "blue"),
    PowerlineSegment("Ready", "white", "green")
])
```

**DEPOIS:**
```python
powerline = PowerlineBar([
    PowerlineSegment("Status", "$foreground", "$primary"),
    PowerlineSegment("Ready", "$foreground", "$success")
])
```

### 4. models/log_entry.py

**ANTES:**
```python
return {
    self.INFO: "blue",
    ...
}
```

**DEPOIS:**
```python
return {
    self.INFO: "cyan",  # Cyan é mais neutro que blue
    ...
}
```

---

## Integração tui_safety (Mouse Tracking Protection)

### Problema

TUIs Textual podem deixar mouse tracking ativo após crash/exit, fazendo o terminal ficar com comportamento estranho.

### Solução

1. **app.py** - Import automático de tui_safety:
   ```python
   import os
   import sys

   _tui_safety_path = os.path.expanduser("~/.local/lib/python")
   if os.path.exists(_tui_safety_path) and _tui_safety_path not in sys.path:
       sys.path.insert(0, _tui_safety_path)

   try:
       import tui_safety
       tui_safety.install()
   except ImportError:
       pass  # Continue sem proteção se tui_safety não disponível
   ```

2. **run.sh** - Trap para cleanup:
   ```bash
   cleanup() {
       printf '\x1b[?9l\x1b[?1000l\x1b[?1001l...'
   }
   trap cleanup EXIT INT TERM
   ```

---

## Script run.sh Melhorado

### Funcionalidades Adicionadas

```bash
./run.sh                    # Execução normal
./run.sh --dev              # Modo dev com Textual DevTools
./run.sh --theme matrix     # Tema alternativo
```

### Proteções

- Cleanup automático de mouse tracking (trap EXIT/INT/TERM)
- Criação automática de venv se não existir
- Suporte a argumentos --theme

---

## Mapeamento de Cores: Hardcoded → Tema

| Cor Hardcoded | Variável Tema | Valor vibe-neon |
|---------------|---------------|-----------------|
| `"white"` | `$foreground` | `#f8f8f2` |
| `"blue"` | `$primary` | `#8be9fd` (cyan) |
| `"dark_blue"` | `$primary-darken-1` | `#6ec8db` |
| `"green"` | `$success` | `#50fa7b` |
| `"orange"` | `$warning` | `#ffb86c` |
| `"black"` | `$background` | `#0d0d0d` |

---

## Resultado Esperado

Após as correções, o tema vibe-neon deve exibir:

- **Background:** `#0d0d0d` (preto profundo) ou `#1a1a2e` (azul escuro sutilíssimo)
- **Primary (Powerline):** `#8be9fd` (cyan brilhante)
- **Accent:** `#ff79c6` (rosa neon)
- **Success:** `#50fa7b` (verde neon)
- **Foreground:** `#f8f8f2` (branco quase puro)

**NÃO deve aparecer:** Fundo azul royal (#0000FF) ou azul céu (#00BFFF)

---

## Validação

### Antes de testar:

```bash
cd legal-extractor-tui
source .venv/bin/activate
```

### Testes:

```bash
# 1. Teste normal
./run.sh

# 2. Teste dev mode (com hot-reload CSS)
./run.sh --dev

# 3. Teste de tema
python -m legal_extractor_tui --theme neon
```

### Checklist Visual:

- [ ] Fundo escuro (#0d0d0d ou #1a1a2e)
- [ ] Powerline com cores cyan/rosa/verde (não azul royal)
- [ ] Bordas heavy com cor do tema ($primary)
- [ ] Mouse tracking desativado ao sair (Ctrl+C)

---

## Arquivos Modificados

1. `src/legal_extractor_tui/app.py` - Integração tui_safety
2. `src/legal_extractor_tui/widgets/powerline_status.py` - Cores tema
3. `src/legal_extractor_tui/widgets/powerline_breadcrumb.py` - Cores tema
4. `src/legal_extractor_tui/widgets/__init__.py` - Exemplo atualizado
5. `src/legal_extractor_tui/models/log_entry.py` - INFO blue → cyan
6. `run.sh` - Mouse tracking cleanup + argumentos

---

## Próximos Passos (Se Necessário)

### Se o problema persistir:

1. **Verificar DEFAULT_CSS em widgets:**
   ```bash
   grep -r "DEFAULT_CSS" src/legal_extractor_tui/widgets/
   ```
   Se algum widget tem DEFAULT_CSS com cores hardcoded, remover/mover para widgets.tcss

2. **Verificar ordem de CSS:**
   ```python
   # Em app.py, deve ser:
   CSS_PATH = [
       "animations.tcss",  # Primeiro
       "base.tcss",        # Variáveis
       "layout.tcss",      # Estrutura
       "widgets.tcss",     # Visual (último = maior precedência)
   ]
   ```

3. **Forçar tema no on_mount:**
   ```python
   def on_mount(self) -> None:
       self.theme = "vibe-neon"
       self.dark = True
   ```

---

## Referências

- Textual Theme System: https://textual.textualize.io/guide/design/
- CSS Precedence: `.claude/agents/tui-master.md` (linha 120-140)
- tui_safety: `~/.local/lib/python/tui_safety.py`
