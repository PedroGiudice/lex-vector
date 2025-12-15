# STJ Module - Quick Start Guide

## Installation

```bash
cd /home/user/Claude-Code-Projetos/legal-workbench

# Create/activate venv (if not exists)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install streamlit pandas duckdb rich httpx pydantic typer python-dateutil python-dotenv tenacity
```

## Test Integration

```bash
# Run integration tests
python test_stj_integration.py

# Expected output: 5/5 tests passing
```

## Start Streamlit

```bash
# From legal-workbench directory
source .venv/bin/activate
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Test Download Feature

1. Navigate to "STJ Dados Abertos" in the sidebar
2. Go to "Download Center" tab
3. Configure download:
   - **Start Date:** 2023-01-01
   - **End Date:** 2023-01-07 (1 week for testing)
   - **Organs:** Corte Especial
4. Click "Iniciar Download"
5. Watch the progress:
   - Phase 1: Download JSON files (0-40%)
   - Phase 2: Process data (40-70%)
   - Phase 3: Insert to database (70-100%)
6. Verify success message and balloons

## Test Search

1. Go to "Busca" tab
2. Enter search term: "responsabilidade civil"
3. Select search type: "Ementa"
4. Click "Buscar"
5. Verify results display
6. Download CSV if needed

## Test Statistics

1. Go to "Estatisticas" tab
2. Verify metrics display:
   - Total acordaos
   - Database size
   - Distribution charts
3. Expand "Ver detalhes" for breakdown

## Test Maintenance

1. Go to "Manutencao" tab
2. Check sync status
3. View coverage by organ
4. Test "Reindexar Banco" (optional)

## Troubleshooting

### Module not found error
```bash
# Make sure you're in venv
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database error
The database file is created automatically on first download. If you see errors:
- Make sure the download completed successfully
- Check `ferramentas/stj-dados-abertos/data/database/` directory exists
- Try a smaller date range first

### Import errors
Run the integration test to diagnose:
```bash
python test_stj_integration.py
```

## Architecture

```
User Interface (Streamlit)
    ↓
modules/stj.py (UI wrapper)
    ↓
ferramentas/stj-dados-abertos/ (backend)
    ├── src/downloader.py     → Downloads JSON from STJ API
    ├── src/processor.py      → Processes JSON into records
    ├── src/database.py       → DuckDB operations
    └── config.py             → URL generation & settings
```

## File Locations

- **Main UI:** `/home/user/Claude-Code-Projetos/legal-workbench/modules/stj.py`
- **Backend:** `/home/user/Claude-Code-Projetos/legal-workbench/ferramentas/stj-dados-abertos/`
- **Database:** `ferramentas/stj-dados-abertos/data/database/stj.duckdb`
- **Downloaded JSONs:** `ferramentas/stj-dados-abertos/data/json/`

## Success Criteria

- Download completes without errors
- Progress bar reaches 100%
- Database file is created
- Search returns results
- Statistics display correctly
- No Python exceptions in terminal

## Next Steps After Testing

1. Try retroactive download (2022-present) with "Download Completo"
2. Test with multiple organs selected
3. Build custom searches
4. Export data for analysis
5. Monitor database size growth

---

**Status:** Ready for Production
**Last Updated:** 2025-12-15
