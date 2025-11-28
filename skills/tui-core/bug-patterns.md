# Bug Patterns - Bugs Criticos e Solucoes

**Documentacao de bugs encontrados em projetos reais e suas solucoes.**

---

## BUG 1: CSS Variable $text-muted Nao Definida

### Sintoma
```
CSS parsing error ou styling nao aplicado
```

### Causa
TCSS usa `$text-muted` mas a variavel nao esta definida no tema.

### Solucao
Definir a variavel ou usar alternativa:

```tcss
/* Opcao 1: Usar variavel de tema existente */
.muted { color: $foreground-muted; }

/* Opcao 2: Definir variavel customizada */
$text-muted: #6272a4;
.muted { color: $text-muted; }
```

### Verificacao
```bash
grep -r "\$text-muted" src/
# Garantir que todas as ocorrencias tem definicao
```

---

## BUG 2: Timer Leak em Widgets

### Sintoma
- App fica lenta com o tempo
- Memoria aumenta continuamente
- Multiplos timers executando apos navegacao

### Causa
Timer criado em `__init__` ou `on_mount` nunca e parado.

### Codigo Problematico
```python
class MyWidget(Widget):
    def __init__(self):
        super().__init__()
        # ERRADO: Timer criado mas nunca parado
        self.timer = self.set_interval(1, self._update)
```

### Solucao
```python
class MyWidget(Widget):
    def __init__(self):
        super().__init__()
        self.timer = None  # Nao criar aqui

    def on_mount(self) -> None:
        self.timer = self.set_interval(1, self._update)

    def on_unmount(self) -> None:
        # CRITICO: Sempre parar timer
        if self.timer:
            self.timer.stop()
```

### Verificacao
```bash
grep -r "set_interval\|set_timer" src/
# Para cada ocorrencia, verificar se existe on_unmount correspondente
```

---

## BUG 3: CSS transform Nao Suportado

### Sintoma
```
CSS warning ou elemento nao posicionado corretamente
```

### Causa
Textual NAO suporta `transform`, `translate`, `rotate`, `scale`.

### Codigo Problematico
```tcss
.centered {
    transform: translate(-50%, -50%);  /* NAO FUNCIONA */
}
```

### Solucao
```tcss
.centered {
    align: center middle;
    text-align: center;
}
```

### Verificacao
```bash
grep -r "transform:" src/styles/
# Deve retornar vazio
```

---

## BUG 4: rgba() com Suporte Limitado

### Sintoma
Background nao aparece ou cor incorreta.

### Causa
`rgba()` tem suporte limitado no Textual.

### Codigo Problematico
```tcss
.overlay {
    background: rgba(0, 0, 0, 0.7);  /* Pode falhar */
}
```

### Solucao
```tcss
/* Opcao 1: Usar variavel com opacidade */
.overlay {
    background: $background 70%;
}

/* Opcao 2: Usar hex com alpha */
.overlay {
    background: #000000b3;  /* 70% opacity */
}

/* Opcao 3: Usar variavel de tema */
.overlay {
    background: $panel;
}
```

---

## BUG 5: Message Attributes Mismatch

### Sintoma
```
AttributeError: 'StepStarted' object has no attribute 'step_index'
```

### Causa
Mensagem definida com um nome de atributo, mas usada com outro.

### Exemplo do Problema
```python
# messages.py
@dataclass
class StepStarted(Message):
    step: int      # Definido como 'step'
    name: str

# worker.py
self.post_message(StepStarted(step_index=1, step_name="Parse"))
                             # ERRADO: usando step_index em vez de step

# screen.py
def on_step_started(self, event):
    print(event.step_index)  # ERRADO: AttributeError
```

### Solucao
Manter consistencia entre definicao e uso:

```python
# messages.py - DEFINICAO
@dataclass
class StepStarted(Message):
    step: int
    name: str

# worker.py - EMISSAO
self.post_message(StepStarted(step=1, name="Parse"))

# screen.py - CONSUMO
def on_step_started(self, event):
    print(event.step)
    print(event.name)
```

### Verificacao
```bash
# Listar todas as mensagens e seus atributos
grep -A5 "class.*Message" src/messages/*.py
```

---

## BUG 6: TUIApp Constructor Sem Parametros

### Sintoma
```
TypeError: __init__() got unexpected keyword arguments
```

### Causa
`__main__.py` passa argumentos mas `App` nao aceita.

### Codigo Problematico
```python
# __main__.py
app = TUIApp(theme_name=args.theme, dev_mode=args.dev)

# app.py
class TUIApp(App):
    pass  # Sem __init__ para aceitar parametros
```

### Solucao
```python
class TUIApp(App):
    def __init__(self, theme_name: str = "default", dev_mode: bool = False):
        super().__init__()
        self._initial_theme = theme_name
        self._dev_mode = dev_mode

    def on_mount(self) -> None:
        self.theme = self._initial_theme
```

---

## BUG 7: var(--name) vs $name

### Sintoma
Variaveis CSS nao funcionam, cores nao aplicam.

### Causa
Usar sintaxe web CSS em vez de TCSS.

### Codigo Problematico
```tcss
:root {
    --my-color: #ff0000;  /* ERRADO: sintaxe web */
}
Button {
    color: var(--my-color);  /* ERRADO: sintaxe web */
}
```

### Solucao
```tcss
$my-color: #ff0000;
Button {
    color: $my-color;
}
```

### Verificacao
```bash
grep -r "var(--" src/styles/
# Deve retornar vazio
```

---

## BUG 8: DEFAULT_CSS Sobrescrevendo Tema

### Sintoma
Estilos do tema nao aplicam em widgets customizados.

### Causa
`DEFAULT_CSS` tem precedencia sobre arquivos .tcss externos.

### Codigo Problematico
```python
class MyWidget(Static):
    DEFAULT_CSS = """
    MyWidget {
        background: #1a1a2e;  /* Hardcoded - ignora tema */
        color: #f8f8f2;
    }
    """
```

### Solucao
```python
class MyWidget(Static):
    # Opcao 1: Remover DEFAULT_CSS, usar .tcss externo
    pass

    # Opcao 2: Usar variaveis de tema no DEFAULT_CSS
    DEFAULT_CSS = """
    MyWidget {
        background: $surface;
        color: $foreground;
    }
    """
```

---

## BUG 9: DuplicateIds ao Atualizar Widget Dinamicamente

### Sintoma
```
DuplicateIds: Tried to insert a widget with ID 'preview-text', but a widget already exists
```

### Causa
Ao atualizar conteudo de um widget, o codigo remove e monta um novo widget com mesmo ID, mas o `mount()` e chamado antes do `remove()` ser processado completamente.

### Codigo Problematico
```python
def _update_pane(self) -> None:
    try:
        old_widget = self.query_one("#my-widget")
        old_widget.remove()  # Async - nao e imediato!
    except:
        pass

    parent.mount(Static("New content", id="my-widget"))  # ERRADO: ID duplicado!
```

### Solucao Correta
```python
def _update_pane(self) -> None:
    try:
        widget = self.query_one("#my-widget", Static)
        widget.update("New content")  # CORRETO: Atualizar em vez de remover/montar
        widget.set_classes("new-class")
    except:
        pass  # Widget nao existe ainda
```

### Alternativa (se precisar trocar tipo de widget)
```python
async def _update_pane(self) -> None:
    try:
        old_widget = self.query_one("#my-widget")
        await old_widget.remove()  # AWAIT para garantir remocao completa
    except:
        pass

    await self.mount(Static("New content", id="my-widget"))
```

### CRITICAL: Cache de .pyc
**Este bug pode reaparecer mesmo apos corrigir o codigo!**

O Python cacheia bytecode em `__pycache__/*.pyc`. Se o cache nao for limpo, o codigo antigo continua executando.

**SEMPRE limpar cache apos modificar arquivos:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

**OU adicionar ao script de execucao:**
```bash
# No run.sh, antes de executar:
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

### Verificacao
```bash
# Procurar por padroes de remove() seguido de mount() com mesmo ID
grep -B5 -A5 "\.remove()" src/**/*.py | grep -A10 "mount.*id="
```

---

## BUG 10: Cache de Bytecode (.pyc) Desatualizado

### Sintoma
Erro persiste mesmo apos corrigir codigo. Traceback mostra linhas que nao existem mais no arquivo.

### Causa
Python cacheia bytecode compilado em `__pycache__/`. Modificacoes no .py nao invalidam cache automaticamente em todos os casos.

### Solucao
```bash
# Limpar TODOS os caches antes de executar
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Alternativa: usar PYTHONDONTWRITEBYTECODE
PYTHONDONTWRITEBYTECODE=1 python -m my_app
```

### Verificacao
Se o traceback mostra codigo diferente do arquivo, e cache desatualizado.

---

## Checklist Pre-Commit

Antes de commitar codigo TUI:

- [ ] Nenhum `transform:` em arquivos .tcss
- [ ] Nenhum `var(--` em arquivos .tcss
- [ ] Todos timers tem `on_unmount()` correspondente
- [ ] Message attributes consistentes (definicao = uso)
- [ ] DEFAULT_CSS usa variaveis de tema (nao hardcoded)
- [ ] App.__init__ aceita todos parametros de __main__.py
- [ ] Variaveis customizadas estao definidas antes do uso

---

## Script de Verificacao

```bash
#!/bin/bash
# verify_tui_bugs.sh

echo "=== TUI Bug Check ==="

echo "Checking for transform..."
grep -r "transform:" src/styles/ && echo "FAIL: transform not supported" || echo "OK"

echo "Checking for var(--)..."
grep -r "var(--" src/styles/ && echo "FAIL: use \$name syntax" || echo "OK"

echo "Checking for timer leaks..."
TIMERS=$(grep -l "set_interval\|set_timer" src/**/*.py)
for f in $TIMERS; do
    grep -q "on_unmount" $f || echo "WARN: $f has timer but no on_unmount"
done

echo "=== Check Complete ==="
```
