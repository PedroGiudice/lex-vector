# DJEN Tracker - Quickstart Guide

Guia de **5 minutos** para começar a usar o DJEN Tracker.

---

## Pré-requisitos

- Python 3.12+ instalado
- 500MB espaço em disco
- Conexão com internet

---

## Instalação (2 minutos)

### 1. Navegar até o projeto

```bash
cd ~/claude-work/repos/Claude-Code-Projetos/agentes/djen-tracker
```

### 2. Criar virtual environment

```bash
python -m venv .venv
```

### 3. Ativar venv

```bash
# Linux/WSL2/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 4. Instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Verificar instalação

```bash
python -c "from src import OABFilter, ContinuousDownloader; print('✅ OK!')"
```

Se aparecer `✅ OK!`, está pronto!

---

## Uso Básico (3 minutos)

### Cenário 1: Download de Cadernos

Baixar cadernos de hoje (27 tribunais principais):

```bash
python main.py
```

**Menu:**
```
1. Download contínuo (loop infinito)
2. Download de hoje (execução única)    ← ESCOLHA ESTA
3. Download de data específica
0. Sair
```

Digite `2` e pressione Enter.

**Resultado:**
```
[STF] ✓ STF_2025-11-17_1_abc123.pdf (12.3MB em 8.2s)
[STJ] ✓ STJ_2025-11-17_1_def456.pdf (8.9MB em 6.3s)
...
✅ Download concluído!
```

PDFs salvos em: `~/claude-code-data/djen-tracker/cadernos/`

---

### Cenário 2: Filtrar por OAB

Criar arquivo `meu_filtro.py`:

```python
from pathlib import Path
from src import OABFilter, ResultExporter

# Configurar filtro
oab_filter = OABFilter(
    cache_dir=Path("~/claude-code-data/djen-tracker/cache").expanduser(),
    enable_ocr=False
)

# OABs de interesse (EDITAR AQUI!)
target_oabs = [
    ('123456', 'SP'),  # Sua OAB
    ('789012', 'RJ'),  # Outra OAB
]

# Buscar PDFs
cadernos_dir = Path("~/claude-code-data/djen-tracker/cadernos").expanduser()
pdf_paths = list(cadernos_dir.rglob("*.pdf"))

# Executar filtro
matches = oab_filter.filter_by_oabs(
    pdf_paths=pdf_paths,
    target_oabs=target_oabs,
    min_score=0.5
)

# Exportar resultados
exporter = ResultExporter()
exporter.export_json(matches, Path("results.json"))
exporter.export_markdown(matches, Path("results.md"))

print(f"✅ {len(matches)} publicações encontradas!")
print("📄 Resultados salvos em: results.json e results.md")
```

**Executar:**
```bash
python meu_filtro.py
```

**Resultado:**
```
Processando 54 PDFs...
████████████████████████ 100% | 54/54 PDFs | 12s

✅ 8 publicações encontradas!
📄 Resultados salvos em: results.json e results.md
```

---

## Visualizar Resultados

### JSON (para automação)
```bash
cat results.json | jq
```

### Markdown (para leitura)
```bash
cat results.md
```

### Excel (para análise)
Se instalou `openpyxl`:
```python
exporter.export_excel(matches, Path("results.xlsx"))
```

Abra `results.xlsx` no Excel/LibreOffice.

---

## Próximos Passos

1. **Personalizar OABs**: Editar `target_oabs` em `meu_filtro.py`
2. **Ajustar tribunais**: Editar `config.json` → `tribunais.prioritarios`
3. **Download contínuo**: `python main.py` → Opção `1` (monitora 24/7)
4. **Explorar API**: Ver [API_REFERENCE.md](API_REFERENCE.md)
5. **Exemplos avançados**: Ver [EXAMPLES.md](EXAMPLES.md)

---

## Troubleshooting Rápido

### Erro: ModuleNotFoundError
```bash
# Verificar venv ativo
which python  # Deve apontar para .venv/bin/python

# Reativar se necessário
source .venv/bin/activate
```

### Nenhuma OAB encontrada
- Reduzir `min_score` para `0.3`
- Verificar se PDFs foram baixados: `ls ~/claude-code-data/djen-tracker/cadernos/`
- Verificar extração de texto (pode precisar de OCR)

### Download falha (HTTP 429)
- Aguardar 1 minuto e tentar novamente
- Rate limit automático já está ativo

---

## Ajuda

- **Documentação completa**: [README.md](../README.md)
- **Troubleshooting detalhado**: [README.md#troubleshooting](../README.md#troubleshooting)
- **Reportar bugs**: GitHub Issues

---

**Tempo total:** ~5 minutos
**Pronto para produção!** ✅
