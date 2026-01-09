# CLAUDE.md - Legal Text Extractor

Pipeline de extracao de texto de documentos juridicos.

---

## Arquitetura
Pipeline 4 etapas: Cartografo -> Saneador -> Extrator -> Bibliotecario

## Dependencias Especificas
- opencv-python-headless
- numpy
- pdfplumber
- pytesseract (opcional)

## CLI
```bash
lte process <arquivo.pdf>
lte stats
lte batch <diretorio>
```

## Testes
```bash
cd legal-workbench/ferramentas/legal-text-extractor
source .venv/bin/activate
pytest tests/ -v
```

## NUNCA
- Modificar `src/context/store.py` sem testes
- Alterar schema do SQLite sem migration plan

---

*Herdado de: ferramentas/CLAUDE.md*
