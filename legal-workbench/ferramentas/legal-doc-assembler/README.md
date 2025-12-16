# Legal Document Assembler

Deterministic Python engine for generating Brazilian legal documents from JSON data.

## Features

- **Fault-tolerant**: Undefined template variables remain visible in output (e.g., `{{ rg }}`)
- **Encoding-safe**: Full UTF-8 support for Brazilian Portuguese characters
- **Format-tolerant**: Normalizes names, addresses, and documents with inconsistent formatting

## Installation

```bash
uv pip install -e .
```

## Usage

```python
from src.engine import DocumentEngine

engine = DocumentEngine()
engine.render(
    template_path="template.docx",
    data={"nome": "João da Silva", "cpf": "12345678901"},
    output_path="output.docx"
)
```

## Normalization Features

- **Names**: Title case with Brazilian connectives (da, de, do, das, dos)
- **Addresses**: Expands abbreviations (R. → Rua, AV. → Avenida)
- **Documents**: Formats CPF, CNPJ, CEP, OAB

## Testing

```bash
uv run pytest -v
```

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
