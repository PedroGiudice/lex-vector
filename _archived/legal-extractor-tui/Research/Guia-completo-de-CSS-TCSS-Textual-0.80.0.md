# Guia completo de CSS/TCSS no Textual 0.80.0+

O Textual CSS (TCSS) é um dialeto CSS simplificado projetado para interfaces de terminal, usando a sintaxe `$variavel` em vez de `var(--name)` e suportando **88 propriedades específicas** para estilização de TUIs. A versão atual do framework é **6.6.0** (novembro 2025), com mudanças significativas desde a versão 0.86.0 que introduziu o novo sistema de temas. Este guia cobre todas as práticas recomendadas para aplicações modernas.

---

## Sistema de variáveis CSS nativas

O Textual fornece **11 cores base obrigatórias** que formam a fundação do sistema de temas, sendo apenas `$primary` tecnicamente requerida:

| Variável | Propósito |
|----------|-----------|
| `$primary` | Cor principal de branding, títulos e ênfase forte |
| `$secondary` | Cor alternativa para diferenciação |
| `$accent` | Contraste com primary/secondary para chamar atenção |
| `$foreground` | Cor padrão de texto |
| `$background` | Fundo de tela onde não há conteúdo |
| `$surface` | Fundo padrão de widgets |
| `$panel` | Diferencia partes da UI do conteúdo principal |
| `$boost` | Cor com alpha para criar camadas |
| `$success` | Indicador de sucesso |
| `$warning` | Indicador de aviso |
| `$error` | Indicador de erro |

Cada cor base possui **6 tons gerados automaticamente**: `-lighten-1`, `-lighten-2`, `-lighten-3` (mais claro) e `-darken-1`, `-darken-2`, `-darken-3` (mais escuro). Exemplo: `$primary-darken-2` ou `$error-lighten-1`. Também existem **variantes muted** com 70% de opacidade: `$primary-muted`, `$secondary-muted`, `$accent-muted`, `$warning-muted`, `$error-muted`, `$success-muted`.

As variáveis de texto garantem legibilidade automática sobre qualquer fundo: `$text` (auto-contraste preto/branco), `$text-muted` (importância menor), `$text-disabled` (itens desabilitados), `$text-primary`, `$text-secondary`, `$text-accent`, `$text-warning`, `$text-error`, `$text-success`.

Variáveis especializadas cobrem elementos específicos da interface:

- **Bordas**: `$border` (foco), `$border-blurred` (sem foco)
- **Cursor de bloco**: `$block-cursor-foreground`, `$block-cursor-background`, `$block-cursor-text-style`
- **Input**: `$input-cursor-background`, `$input-cursor-foreground`, `$input-selection-background`
- **Scrollbar**: `$scrollbar`, `$scrollbar-hover`, `$scrollbar-active`, `$scrollbar-background`
- **Links**: `$link-background`, `$link-color`, `$link-style`, `$link-background-hover`, `$link-color-hover`
- **Footer**: `$footer-foreground`, `$footer-background`, `$footer-key-foreground`
- **Botões**: `$button-foreground`, `$button-color-foreground`, `$button-focus-text-style`

---

## Breaking changes entre versões

### Versão 0.86.0 (novembro 2024) — mudança mais crítica

Esta versão introduziu o **novo sistema de temas** com alterações significativas. O atributo `App.dark` foi removido completamente, substituído por `App.theme`. Widgets podem aparecer visualmente diferentes após atualização devido a mudanças nas variáveis CSS padrão.

```python
# Antes (0.70.x - 0.85.x)
self.dark = True  # REMOVIDO

# Depois (0.86.0+)
self.theme = "textual-dark"  # Novo sistema
```

### Versão 2.0.0 (início 2025)

O argumento `wrap` do `OptionList` foi removido. A migração requer CSS:

```css
OptionList {
    text-wrap: nowrap;
    text-overflow: ellipsis;
}
```

O argumento `tooltip` também foi removido do OptionList — use o atributo `.tooltip` ou método `with_tooltip()`. A semântica de `Widget.anchor` mudou e agora deve ser aplicada ao container pai.

### Versão 6.0.0 (agosto 2025)

Propriedades renomeadas: `Static.renderable` → `Static.content` e `Label.renderable` → `Label.content`. Estilos de background não são mais automaticamente aplicados a conteúdo de widgets — Segments em branco não recebem cor de fundo automaticamente.

### Novos recursos adicionados

A versão **0.80.0+** adicionou pseudo-classes `:first-child` e `:last-child`. A versão **6.3.0** introduziu a propriedade `scrollbar-visibility`. O suporte a CSS nesting com seletor `&` está disponível em versões recentes.

---

## Propriedades CSS suportadas e não suportadas

### Layout e posicionamento

```css
layout: horizontal | vertical | grid;
dock: top | right | bottom | left;
position: relative | absolute;
offset: <x> <y>;
align: <horizontal> <vertical>;
content-align: <horizontal> <vertical>;
text-align: left | center | right | justify | start | end;
```

### Dimensões (unidades suportadas)

O Textual suporta **7 tipos de unidades**: células/caracteres (sem unidade), `%` (porcentagem do pai), `fr` (unidade fracional), `w` (% largura container), `h` (% altura container), `vw` (% largura viewport), `vh` (% altura viewport), e `auto`.

```css
width: 20;        /* 20 células */
width: 50%;       /* 50% do pai */
width: 1fr;       /* unidade fracional */
height: 25vh;     /* 25% da viewport */
min-width: 10;
max-height: auto;
box-sizing: border-box | content-box;
```

### Espaçamento (margin e padding)

Usa valores inteiros representando células. Aceita 1-4 valores no padrão CSS:

```css
padding: 1;           /* todos os lados */
padding: 1 2;         /* vertical horizontal */
padding: 1 2 3 4;     /* top right bottom left */
margin-top: 2;
```

### Cores e aparência

```css
color: $primary;
color: #ff5500;
color: rgb(255, 0, 0);
color: hsl(0, 100%, 50%);
color: auto;          /* auto-contraste */
background: red 20%;  /* com opacidade */
background-tint: $boost;
opacity: 50%;
text-opacity: 70%;
visibility: visible | hidden;
display: block | none;
```

### Bordas (16 tipos específicos de terminal)

Tipos disponíveis: `ascii`, `blank`, `dashed`, `double`, `heavy`, `hidden/none`, `hkey`, `inner`, `outer`, `panel`, `round`, `solid`, `tall`, `thick`, `vkey`, `wide`.

```css
border: heavy $primary;
border-top: double green;
border-title-align: center;
border-title-color: $accent;
outline: solid red;
```

### Grid layout

```css
grid-size: 4;                    /* 4 colunas */
grid-size: 4 6;                  /* 4 colunas, 6 linhas */
grid-columns: 1fr 2fr 1fr;
grid-rows: 2fr 1fr 1fr;
grid-gutter: 1 2;                /* vertical horizontal */
column-span: 2;
row-span: 3;
```

### Texto

```css
text-style: bold italic;         /* combinável */
text-style: reverse strike underline;
text-wrap: wrap | nowrap;
text-overflow: clip | fold | ellipsis;
```

### Scrollbar

```css
overflow: auto | hidden | scroll;
overflow-x: hidden;
scrollbar-size: 1 1;
scrollbar-gutter: stable;
scrollbar-color: $panel;
scrollbar-background: $background-darken-1;
scrollbar-visibility: visible | hidden;  /* novo em 6.3.0 */
```

### Layers (substitui z-index)

```css
layers: base overlay popup;
layer: overlay;
```

### Propriedades NÃO suportadas

O Textual **não suporta** as seguintes propriedades web CSS:

- **Animações**: `animation`, `@keyframes`, `transition`
- **Transforms**: `transform`, `rotate`, `scale`, `translate`
- **Bordas arredondadas**: `border-radius` (terminais usam caracteres)
- **Sombras**: `box-shadow`, `text-shadow`
- **Flexbox**: `flex`, `flex-direction`, `justify-content`
- **Posicionamento web**: `z-index`, `top`, `left`, `right`, `bottom`
- **Fontes**: `font-family`, `font-size`, `font-weight`, `line-height`
- **Seletores avançados**: `:nth-child()`, `:first-of-type`
- **Media queries**: `@media`
- **Funções CSS**: `calc()`, `min()`, `max()`, `clamp()`
- **Variáveis web**: `var(--name)` — use `$name`

---

## Sintaxe e boas práticas

### Definição e uso de variáveis

Variáveis usam prefixo `$` e são definidas no topo do arquivo CSS:

```css
$my-border: wide green;
$accent-color: #ff5500;
$spacing: 2;

Button {
    border: $my-border;
    color: $accent-color;
    padding: $spacing;
}
```

Variáveis podem referenciar outras variáveis: `$composite: heavy $primary;`

**Não há suporte nativo para fallbacks** como `var(--name, fallback)`. Para valores condicionais, use pseudo-classes `:dark` e `:light`.

### CSS nesting (suportado)

```css
#container {
    border: heavy $primary;
    
    .button {
        width: 1fr;
        
        &.active {
            background: $success;
        }
        
        &:hover {
            background: $primary-lighten-1;
        }
    }
}
```

### Pseudo-classes suportadas

```css
Button:hover { background: $primary; }
Button:focus { border: heavy $accent; }
Button:focus-within { background: $boost; }
Button:disabled { opacity: 50%; }
Button:enabled { color: $text; }

/* Tema */
MyWidget:dark { background: #333; }
MyWidget:light { background: #fff; }

/* Posição (novo em 0.80.0+) */
ListItem:first-child { border-top: none; }
ListItem:last-child { border-bottom: none; }
```

### Formatos de cor aceitos

```css
color: red;                    /* nomes */
color: #f00;                   /* hex 3 dígitos */
color: #ff0000;                /* hex 6 dígitos */
color: rgb(255, 0, 0);         /* RGB */
color: rgba(255, 0, 0, 0.5);   /* RGBA */
color: hsl(0, 100%, 50%);      /* HSL */
color: $primary;               /* variável */
color: $primary 80%;           /* variável + opacidade */
color: auto;                   /* auto-contraste */
```

### Organização recomendada de arquivos

```python
# Opção 1: Arquivo externo (recomendado)
class MyApp(App):
    CSS_PATH = "styles.tcss"
    
# Opção 2: Múltiplos arquivos
class MyApp(App):
    CSS_PATH = ["base.tcss", "components.tcss", "themes.tcss"]

# Opção 3: CSS inline (para componentes simples)
class MyApp(App):
    CSS = """
    Screen { align: center middle; }
    """

# Opção 4: DEFAULT_CSS em widgets customizados
class MyWidget(Static):
    DEFAULT_CSS = """
    MyWidget {
        background: $surface;
        padding: 1 2;
    }
    """
```

---

## Temas e customização

### Criando temas customizados

```python
from textual.theme import Theme
from textual.app import App

arctic_theme = Theme(
    name="arctic",
    primary="#88C0D0",
    secondary="#81A1C1",
    accent="#B48EAD",
    foreground="#D8DEE9",
    background="#2E3440",
    success="#A3BE8C",
    warning="#EBCB8B",
    error="#BF616A",
    surface="#3B4252",
    panel="#434C5E",
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#88C0D0",
        "input-selection-background": "#81a1c1 35%",
    },
)

class MyApp(App):
    def on_mount(self) -> None:
        self.register_theme(arctic_theme)
        self.theme = "arctic"
```

### Temas built-in

O Textual inclui temas pré-definidos: `textual-dark` (padrão), `textual-light`, `nord`, `gruvbox`. Usuários podem alternar temas via Command Palette (Ctrl+P).

### Alternância de tema em runtime

```python
def action_toggle_theme(self) -> None:
    self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"
```

### Sobrescrevendo variáveis específicas

```python
def get_theme_variable_defaults(self) -> dict[str, str]:
    return {
        "my-custom-color": "#ff0000",
        "custom-border-width": "2",
    }
```

### Estilos dinâmicos via classes CSS

```python
# Adicionar classes
widget.add_class("highlighted", "active")

# Remover classes
widget.remove_class("highlighted")

# Alternar classes
widget.toggle_class("selected")

# CSS correspondente
.highlighted { background: $warning; }
.active { border: heavy $success; }
```

---

## Debugging e troubleshooting

### Console de desenvolvimento

O `textual-dev` fornece ferramentas essenciais de debugging:

```bash
# Terminal 1: Iniciar console
textual console

# Terminal 2: Executar app com hot-reload de CSS
textual run my_app.py --dev
```

O modo `--dev` habilita **live CSS editing** — alterações em arquivos `.tcss` são refletidas instantaneamente sem reiniciar a aplicação.

### Logging para debugging

```python
from textual import log

def on_mount(self) -> None:
    log("Variáveis locais:", locals())
    log(children=self.children, theme=self.theme)
    
    # Visualizar árvore DOM com anotações CSS
    self.log(self.tree)
```

### Controle de verbosidade

```bash
# Modo verbose
textual console -v

# Excluir grupos de mensagens
textual console -x SYSTEM -x EVENT -x DEBUG
```

### Inspeção de estilos computados

```python
widget.css_identifier    # Identificador CSS do widget
widget.css_path_nodes    # Caminho do App até este nó
widget.styles            # Estilos computados atuais
widget.display           # Estado de display
widget.visible           # Estado de visibilidade
```

### Preview de cores do tema

```bash
textual colors
```

### Problemas comuns e soluções

| Problema | Solução |
|----------|---------|
| CSS não atualiza | Executar com `textual run --dev` |
| Tema não aplica | Definir em `on_mount()`, não em `__init__()` |
| print() não aparece | Usar `textual console` + `--dev` ou `self.log()` |
| Variáveis não funcionam | Verificar sintaxe `$name` (não `var(--name)`) |

---

## Projetos de referência (2024-2025)

### Projetos flagship bem implementados

**Posting** (~9.100 stars) é um cliente HTTP moderno para terminal com sistema de temas customizáveis via YAML, suporte a navegação Vim e syntax highlighting. Demonstra excelente separação entre lógica e estilo.

**Harlequin** é uma IDE SQL completa com suporte a 20+ adaptadores de banco de dados. Usa Textual 0.89.1 com `textual-fastdatatable` e `textual-textarea`, demonstrando componentização avançada e integração do sistema de temas.

**Toolong** (~3.600 stars), desenvolvido pela própria Textualize, é um visualizador de logs que demonstra uso eficiente do sistema de temas built-in com CSS mínimo customizado.

**Elia** (~2.200 stars), de Darren Burns (contribuidor core do Textual), é um cliente LLM para terminal demonstrando interface keyboard-centric bem estilizada.

### Padrões CSS observados em projetos maduros

```css
/* Grid layout para UIs complexas */
Screen {
    layout: grid;
    grid-size: 2;
    grid-gutter: 2;
    padding: 2;
}

/* Unidades fracionais para responsividade */
.panel { height: 1fr; }

/* Classes para estado */
.started #start { display: none; }
.started #stop { display: block; }

/* Uso consistente de variáveis de tema */
TimeDisplay {
    background: $panel;
    color: $text;
    border: $secondary tall;
}
```

### Recursos e listas curadas

- **awesome-textualize-projects**: github.com/oleksis/awesome-textualize-projects
- **written-in-textual**: github.com/matan-h/written-in-textual
- **Galeria oficial**: textualize.io/textual/gallery
- **Exemplos oficiais**: github.com/Textualize/textual/tree/main/examples

---

## Conclusão

O ecossistema CSS do Textual evoluiu significativamente desde a versão 0.80.0. A mudança mais impactante foi a **introdução do sistema de temas na versão 0.86.0**, que substituiu o antigo `App.dark` por uma arquitetura baseada na classe `Theme` com variáveis semânticas. 

As boas práticas modernas incluem: usar arquivos `.tcss` externos com `CSS_PATH`, aproveitar variáveis de tema `$primary/$surface/$text` para manutenibilidade, utilizar grid layout com unidades `fr` para responsividade, gerenciar estados via classes CSS em vez de estilos inline, e debuggar com `textual console` + `--dev` para hot-reload.

Diferentemente do CSS web, o TCSS não suporta `border-radius`, animações, transforms ou funções como `calc()`. O sistema usa `$variavel` em vez de `var(--name)` e oferece 16 tipos de borda específicos para terminal. A propriedade `layers` substitui `z-index` para controle de empilhamento.

Projetos como Posting e Harlequin demonstram que aplicações complexas e visualmente ricas são viáveis com TCSS quando se adota componentização, separação de concerns, e uso consistente do sistema de temas.