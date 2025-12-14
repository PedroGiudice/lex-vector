# Test Fixtures - Legal Text Extractor

Arsenal de documentos de teste extraídos de PDFs reais de diferentes sistemas judiciais brasileiros.

## Estrutura

### Por Sistema Judicial

| Fixture | Sistema | Páginas | Tamanho | Uso |
|---------|---------|---------|---------|-----|
| `fixture_esaj.pdf` | ESAJ (TJ-SP) | 5 | 285K | Início do processo |
| `fixture_esaj_meio.pdf` | ESAJ | 6 | 133K | Páginas do meio |
| `fixture_esaj_final.pdf` | ESAJ | 5 | 810K | Final do processo |
| `fixture_pje.pdf` | PJE | 5 | 372K | Início do processo |
| `fixture_pje_meio.pdf` | PJE | 6 | 778K | Páginas do meio |
| `fixture_pje_final.pdf` | PJE | 5 | 321K | Final do processo |
| `fixture_eproc.pdf` | EPROC | 5 | 35M | Início (scanned/OCR) |
| `fixture_eproc_meio.pdf` | EPROC | 6 | 35M | Meio (scanned/OCR) |
| `fixture_projudi.pdf` | PROJUDI (TJ-GO) | 5 | 1.1M | Início do processo |
| `fixture_projudi_meio.pdf` | PROJUDI | 6 | 2.3M | Páginas do meio |
| `fixture_projudi_final.pdf` | PROJUDI | 5 | 1.4M | Final do processo |

### Por Cenário de Teste

| Fixture | Descrição | Tamanho | Cenário |
|---------|-----------|---------|---------|
| `fixture_clean.pdf` | Documento limpo sem marcas | 178K | Baseline - texto limpo |
| `fixture_dirty.pdf` | Documento com marcas d'água/carimbos | 31K | Teste de limpeza |
| `fixture_single.pdf` | Uma única página | 21K | Caso mínimo |
| `fixture_multi_15pages.pdf` | 15 páginas | 362K | Multi-página |
| `fixture_doc_generic.pdf` | Documento genérico | 124K | Formato alternativo |

## Casos de Uso

### 1. Testar Detecção de Sistema
```python
# Deve detectar sistema ESAJ
result = detect_system("fixtures/fixture_esaj.pdf")
assert result == "ESAJ"
```

### 2. Testar OCR (EPROC)
```python
# EPROC geralmente tem páginas escaneadas
# Ótimo para testar pipeline OCR
result = extract_text("fixtures/fixture_eproc.pdf")
# Esperar texto extraído via OCR
```

### 3. Testar Limpeza de Imagem
```python
# fixture_dirty tem marcas d'água e carimbos
cleaned = clean_image("fixtures/fixture_dirty.pdf")
# Verificar remoção de artefatos
```

### 4. Testar Extração de Sentenças
```python
# Páginas finais geralmente contêm sentenças/decisões
sections = extract_sections("fixtures/fixture_esaj_final.pdf")
assert any(s.tipo == "SENTENCA" for s in sections)
```

### 5. Testar Performance
```python
# fixture_multi_15pages para benchmark
import time
start = time.time()
process("fixtures/fixture_multi_15pages.pdf")
elapsed = time.time() - start
assert elapsed < 30  # deve processar em menos de 30s
```

## Origem dos Fixtures

Extraídos usando PDFtk dos arquivos em `../padrao_docs/`:

- `padrao-ESAJ.pdf` (69 páginas) → ESAJ fixtures
- `padrao-PJE.pdf` (102 páginas) → PJE fixtures
- `padrao-EPROC.pdf` (415 páginas) → EPROC fixtures
- `padrao-PROJUDI-TJGO.pdf` (80 páginas) → PROJUDI fixtures

## Comandos PDFtk Usados

```bash
# Extrair páginas específicas
pdftk input.pdf cat 1-5 output fixture_inicio.pdf

# Extrair páginas do meio
pdftk input.pdf cat 30-35 output fixture_meio.pdf

# Extrair páginas finais
pdftk input.pdf cat 65-69 output fixture_final.pdf

# Página única
pdftk input.pdf cat 1 output fixture_single.pdf
```

## Notas

- **EPROC fixtures são grandes (~35MB)**: Contêm imagens escaneadas, ideais para testar OCR
- **fixture_dirty**: Tem marcas d'água visíveis, ideal para testar engine de limpeza
- **Páginas do meio/final**: Geralmente contêm decisões, sentenças, despachos
- **Páginas iniciais**: Geralmente contêm petição inicial, procuração

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota
