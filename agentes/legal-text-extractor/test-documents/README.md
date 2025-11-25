# Test Documents

## PDFs Sintéticos (Fixtures)

### fixture_test.pdf

PDF de teste gerado automaticamente com 3 páginas para validar a pipeline:

- **Página 1 (NATIVE)**: Texto normal extraível - fim de petição inicial
  - 1593 caracteres
  - Testa: Step 01 (Analisador) - classificação NATIVE
  - Testa: Extração direta via pdfplumber

- **Página 2 (RASTER_NEEDED)**: Imagem de texto (contrato escaneado)
  - 0 caracteres extraíveis (texto embedded como imagem)
  - Testa: Step 01 (Analisador) - classificação RASTER_NEEDED
  - Testa: Step 02 (Saneador) - processamento de imagem
  - Testa: Step 03 (Extrator) - OCR (quando implementado)

- **Página 3 (TARJA_DETECTED)**: Texto com tarja lateral de assinatura digital
  - 1539 caracteres
  - Tarja lateral nos últimos 20% da largura (simula PJe/e-SAJ)
  - Testa: Step 01 (Analisador) - detecção de tarja
  - Testa: Step 02 (Saneador) - remoção de tarja (quando implementado)

**Gerar novamente:**
```bash
cd agentes/legal-text-extractor
source .venv/bin/activate
python scripts/generate_fixtures.py
```

## PDFs Reais (Para Testes Manuais)

Coloque aqui PDFs de teste dos 7 sistemas:

- [ ] STF - Supremo Tribunal Federal
- [ ] STJ - Superior Tribunal de Justiça
- [ ] PJE - Processo Judicial Eletrônico
- [ ] ESAJ - Sistema de Automação da Justiça
- [ ] EPROC - Sistema de Processo Eletrônico
- [ ] PROJUDI - Processo Judicial Digital
- [ ] GENERIC - Judicial genérico

**IMPORTANTE:** Não commite PDFs! Eles estão no .gitignore.
