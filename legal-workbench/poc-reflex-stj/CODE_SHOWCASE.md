# Code Showcase - Reflex Reactive Patterns

This document highlights the key code patterns that demonstrate Reflex's capabilities.

---

## 1. Reactive SQL Preview (The Star Feature)

**Location:** `poc_reflex_stj/poc_reflex_stj.py` (Lines 84-120)

```python
class STJState(rx.State):
    legal_domain: str = ""
    trigger_words: List[str] = []
    only_acordaos: bool = False

    @rx.var
    def sql_preview(self) -> str:
        """Computed property: Live SQL preview that updates reactively."""
        if not self.legal_domain and not self.trigger_words:
            return "-- Selecione domínio ou palavras-gatilho para gerar SQL"

        sql_parts = ["SELECT"]
        sql_parts.append("  acor.id,")
        sql_parts.append("  acor.numero_processo,")
        sql_parts.append("  acor.ementa,")
        # ... more fields

        where_clauses = []

        if self.legal_domain:
            where_clauses.append(f"  acor.dominio = '{self.legal_domain}'")

        if self.trigger_words:
            trigger_conditions = " OR ".join([
                f"acor.ementa LIKE '%{word}%'" for word in self.trigger_words
            ])
            where_clauses.append(f"  ({trigger_conditions})")

        if self.only_acordaos:
            where_clauses.append("  acor.tipo_documento = 'ACORDAO'")

        if where_clauses:
            sql_parts.append("WHERE")
            sql_parts.append(" AND\n".join(where_clauses))

        sql_parts.append("ORDER BY acor.data_julgamento DESC")
        sql_parts.append("LIMIT 100;")

        return "\n".join(sql_parts)
```

**Why This Is Powerful:**
- ✅ **Zero manual wiring** - No `useEffect` or dependency tracking
- ✅ **Automatic updates** - Changes to `legal_domain`, `trigger_words`, or `only_acordaos` trigger recalculation
- ✅ **Type safe** - Return type is enforced
- ✅ **Pure function** - No side effects, just computation

**React Equivalent (for comparison):**
```javascript
const [sqlPreview, setSqlPreview] = useState("");
const [legalDomain, setLegalDomain] = useState("");
const [triggerWords, setTriggerWords] = useState([]);
const [onlyAcordaos, setOnlyAcordaos] = useState(false);

useEffect(() => {
    // Manual dependency tracking
    const sql = buildSqlQuery(legalDomain, triggerWords, onlyAcordaos);
    setSqlPreview(sql);
}, [legalDomain, triggerWords, onlyAcordaos]);
```

---

## 2. Two-Way Data Binding

**Location:** `poc_reflex_stj/poc_reflex_stj.py` (Lines 281-288)

```python
rx.select(
    STJState.domains,                      # Options from state
    placeholder="Selecione um domínio...", # UI hint
    value=STJState.legal_domain,           # Current value (read)
    on_change=STJState.set_legal_domain,   # Setter (write)
    size="3",
    color_scheme="orange",
)
```

**What Happens:**
1. User selects "Direito Civil"
2. `STJState.set_legal_domain("Direito Civil")` is called
3. `STJState.legal_domain` updates to `"Direito Civil"`
4. All UI components using `STJState.legal_domain` re-render
5. `sql_preview` computed var recalculates automatically
6. SQL code block updates

**All in 1 frame - no flicker, no manual sync**

---

## 3. Multi-Select with Toggle State

**Location:** `poc_reflex_stj/poc_reflex_stj.py` (Lines 304-319)

```python
# UI Layer
rx.foreach(
    STJState.available_triggers,  # ["Dano Moral", "Lucros Cessantes", ...]
    lambda word: rx.button(
        word,
        on_click=lambda w=word: STJState.toggle_trigger_word(w),
        variant=rx.cond(
            STJState.trigger_words.contains(word),  # If word is selected
            "solid",                                 # Use solid variant
            "outline"                                # Else use outline
        ),
        color_scheme="orange",
        size="2",
    ),
)

# State Layer
def toggle_trigger_word(self, word: str):
    """Toggle trigger word selection."""
    if word in self.trigger_words:
        self.trigger_words = [w for w in self.trigger_words if w != word]
    else:
        self.trigger_words = self.trigger_words + [word]
```

**Pattern:**
- Foreach generates button for each trigger word
- Click handler toggles word in/out of `trigger_words` list
- UI variant (solid vs outline) updates based on presence in list
- SQL preview updates automatically

---

## 4. Conditional Rendering

**Location:** `poc_reflex_stj/poc_reflex_stj.py` (Lines 470-525)

```python
rx.cond(
    STJState.show_results,  # Condition
    rx.box(                 # If True: Show results section
        rx.vstack(
            rx.hstack(
                rx.text("> RESULTADOS", ...),
                rx.badge(STJState.results_count, ...),  # Dynamic count
            ),
            rx.vstack(
                rx.foreach(
                    STJState.results_data,  # Loop through results
                    result_card,            # Render each with result_card()
                ),
            ),
        ),
    ),
    rx.fragment(),  # If False: Render nothing
)
```

**Flow:**
1. Initial state: `show_results = False` → No results section
2. User clicks "EXECUTAR QUERY"
3. `execute_query()` sets `show_results = True`
4. Results section appears
5. `results_data` is populated
6. `foreach` renders each result card

---

## 5. Dynamic Badges with Color Logic

**Location:** `poc_reflex_stj/poc_reflex_stj.py` (Lines 189-208)

```python
def outcome_badge(outcome: str) -> rx.Component:
    """Create outcome badge with appropriate color."""
    colors = {
        "Provido": {"bg": "#22c55e", "text": "#ffffff"},     # Green
        "Desprovido": {"bg": "#dc2626", "text": "#ffffff"},  # Red
        "Parcial": {"bg": "#f59e0b", "text": "#000000"},     # Amber/Yellow
    }

    style = colors.get(outcome, {"bg": "#6b7280", "text": "#ffffff"})

    return rx.box(
        rx.text(outcome.upper(), size="1", weight="bold"),
        padding="4px 12px",
        border_radius="12px",
        background=style["bg"],
        color=style["text"],
        display="inline-block",
        font_family="monospace",
    )
```

**Usage in Result Card:**
```python
rx.hstack(
    rx.text(result["id"], ...),     # "REsp 1.234.567"
    rx.spacer(),                     # Push badge to right
    outcome_badge(result["outcome"]), # "PROVIDO" (green pill)
    width="100%",
)
```

**Result:**
- `outcome_badge("Provido")` → Green pill with "PROVIDO"
- `outcome_badge("Desprovido")` → Red pill with "DESPROVIDO"
- `outcome_badge("Parcial")` → Yellow pill with "PARCIAL"

---

## 6. Template Quick-Fill Pattern

**Location:** `poc_reflex_stj/poc_reflex_stj.py` (Lines 147-156)

```python
def apply_template_divergencia(self):
    """Apply 'Divergência entre Turmas' template."""
    self.legal_domain = "Direito Civil"
    self.trigger_words = ["Jurisprudência Dominante", "Súmula"]
    self.only_acordaos = True
```

**UI Binding:**
```python
rx.button(
    "Divergência Turmas",
    on_click=STJState.apply_template_divergencia,
    variant="outline",
    color_scheme="gray",
)
```

**What Happens on Click:**
1. `apply_template_divergencia()` updates 3 state variables
2. All UI components using those variables re-render:
   - Dropdown shows "Direito Civil"
   - "Jurisprudência Dominante" button becomes solid
   - "Súmula" button becomes solid
   - Toggle switches to ON
   - SQL preview updates with all filters
3. **All in one atomic update** - no intermediate states visible

---

## 7. Result Card Composition

**Location:** `poc_reflex_stj/poc_reflex_stj.py` (Lines 211-249)

```python
def result_card(result: Dict) -> rx.Component:
    """Render a single result card."""
    return rx.box(
        rx.vstack(
            # Header: ID + Outcome badge
            rx.hstack(
                rx.text(
                    result["id"],  # "REsp 1.234.567"
                    size="3",
                    weight="bold",
                    color="#f59e0b",  # Amber
                    font_family="monospace",
                ),
                rx.spacer(),
                outcome_badge(result["outcome"]),
                width="100%",
                align="center",
            ),

            # Ementa (body text)
            rx.text(
                result["ementa"],
                size="2",
                color="#e2e8f0",  # Light gray
                margin_top="8px",
            ),

            # Footer: Date + Relator
            rx.hstack(
                rx.text(f"Data: {result['date']}", ...),
                rx.text("|", color="#475569"),  # Separator
                rx.text(result["relator"], ...),
                margin_top="8px",
            ),

            align_items="start",
            spacing="1",
        ),

        # Card styling
        padding="16px",
        border_radius="4px",
        border="1px solid #334155",
        background="#0f172a",  # Dark card background
        width="100%",
        _hover={"border_color": "#f59e0b"},  # Amber on hover
    )
```

**Usage:**
```python
rx.foreach(
    STJState.results_data,  # List of result dicts
    result_card,            # Function to render each
)
```

**Each result dict becomes a styled card with:**
- Header (ID + outcome badge)
- Body (ementa text)
- Footer (date + relator)
- Hover effect (border color change)

---

## 8. Styling Pattern (Terminal Aesthetic)

**Inline Styling:**
```python
rx.box(
    # Content...
    padding="24px",
    border_radius="4px",
    border="1px solid #334155",      # Slate border
    background="#0f172a",            # Dark blue background
    width="100%",
    _hover={"border_color": "#f59e0b"},  # Amber on hover
)
```

**Color Palette:**
```python
COLORS = {
    "bg_dark": "#0a0f1a",       # Main background
    "bg_card": "#0f172a",       # Card background
    "text_primary": "#e2e8f0",  # Light gray text
    "accent_amber": "#f59e0b",  # Actions, highlights
    "accent_red": "#dc2626",    # Warnings, Desprovido
    "accent_green": "#22c55e",  # Success, Provido
    "border": "#334155",        # Card borders
}
```

**Font Stack:**
```python
# In app.py
app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap",
    ],
)

# Usage
rx.text(
    "SELECT * FROM ...",
    font_family="monospace",  # Uses JetBrains Mono
)
```

---

## 9. State Management Pattern

**Full State Class:**
```python
class STJState(rx.State):
    # Input state
    legal_domain: str = ""
    trigger_words: List[str] = []
    only_acordaos: bool = False
    show_results: bool = False

    # Data state
    results_data: List[Dict[str, str]] = []

    # Options (constant)
    domains: List[str] = ["", "Direito Civil", ...]
    available_triggers: List[str] = ["Dano Moral", ...]

    # Computed properties (@rx.var)
    @rx.var
    def sql_preview(self) -> str: ...

    @rx.var
    def selected_trigger_count(self) -> int: ...

    @rx.var
    def results_count(self) -> int: ...

    # Event handlers
    def set_legal_domain(self, value: str): ...
    def set_only_acordaos(self, value: bool): ...
    def toggle_trigger_word(self, word: str): ...
    def execute_query(self): ...
    def clear_query(self): ...
    def apply_template_divergencia(self): ...
    def apply_template_repetitivos(self): ...
    def apply_template_sumulas(self): ...
```

**Pattern:**
1. **State variables** - Data that can change
2. **Computed vars** - Derived data (auto-update)
3. **Event handlers** - Methods that modify state

**React Comparison:**
- State variables → `useState`
- Computed vars → `useMemo` or `useEffect`
- Event handlers → Regular functions that call `setState`

---

## 10. Code Block with Syntax Highlighting

**Location:** `poc_reflex_stj/poc_reflex_stj.py` (Lines 418-427)

```python
rx.code_block(
    STJState.sql_preview,  # Content (reactive)
    language="sql",        # Syntax highlighting
    show_line_numbers=True,
    theme="dark",
    width="100%",
)
```

**Features:**
- Auto syntax highlighting for SQL
- Line numbers
- Dark theme (matches terminal aesthetic)
- Updates reactively as `sql_preview` changes

---

## Summary: Why These Patterns Matter

### 1. Less Boilerplate
**Reflex:**
```python
@rx.var
def sql_preview(self) -> str:
    return build_sql()
```

**React:**
```javascript
const [sql, setSql] = useState("");
useEffect(() => {
    setSql(buildSql());
}, [domain, triggers, acordaos]);
```

**Saved: 3 lines per computed value**

### 2. Type Safety
**Reflex:**
```python
def set_legal_domain(self, value: str):  # Type checked
    self.legal_domain = value
```

**React (JavaScript):**
```javascript
function setLegalDomain(value) {  // No type checking
    setLegalDomain(value);
}
```

**React (TypeScript):**
```typescript
function setLegalDomain(value: string) {  // Type checked
    setLegalDomain(value);
}
```

**Reflex uses Python's native type system**

### 3. Single Language
**Reflex:** Python for UI + Backend
**React:** JavaScript/TypeScript for UI, Python for Backend

**No context switching = faster development**

---

## Code Metrics

| Metric | Value |
|--------|-------|
| Total lines | 549 |
| State class | ~140 lines |
| UI components | ~300 lines |
| Mock data | ~40 lines |
| Imports + config | ~70 lines |
| **Lines of boilerplate** | **~30 lines** |

**Compare to equivalent React app:**
- React: ~800-1000 lines (with hooks, effects, state management)
- Reflex: ~550 lines (30-40% less code)

---

**Conclusion:** Reflex patterns are more concise, type-safe, and easier to reason about for Python developers.
