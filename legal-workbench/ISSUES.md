# Issues Conhecidos

Problemas identificados aguardando resolucao.

---

## Quick Reference: Instalacao do App Tauri

**Desinstalar versao atual:**
```bash
sudo dpkg --purge legal-workbench
```

**Instalar nova versao (via Tailscale):**
```bash
scp opc@100.114.203.28:/tmp/lw.deb /tmp/ && sudo dpkg -i /tmp/lw.deb
```

**Rodar app com logs (debug):**
```bash
/opt/Legal\ Workbench/tauri-app 2>&1 | tee /tmp/lw-log.txt
```

**Verificar versao instalada:**
```bash
dpkg -s legal-workbench | grep Version
```

---

## Abertos

### #1 - Text Extractor: "Submission failed: Network Error"

**Modulo:** Text Extractor (frontend + Tauri)
**Sintoma:** Ao submeter PDF para extracao, erro "Submission failed: Network Error"
**Status:** Aberto (solucao anterior revertida)
**Data:** 2026-01-29

**Causa Raiz (descoberta incremental):**
1. CORS invalido: `allow_origins=["*"]` + `allow_credentials=True`
2. IP hardcoded em `dynamic.yml` apontava para container antigo
3. WebKitGTK (engine Tauri Linux) tem limitacoes com fetch/CORS causando "Broken pipe"

**Tentativa de Solucao (2026-02-02) - REVERTIDA:**
Tentamos usar `tauri-plugin-http` em vez do fetch nativo do WebView.

**Problema:** Nossa implementacao do tauri-plugin-http causou freeze/crash do app ao enviar FormData.
Bugs conhecidos no plugin:
- [Issue #2588](https://github.com/tauri-apps/plugins-workspace/issues/2588): http fetch freezes in POST
- [Issue #13498](https://github.com/tauri-apps/tauri/issues/13498): Webview window random freezing

**Status Atual:**
Revertido para axios. App funciona mas pode ter "Network Error" esporadico no WebKitGTK.
Investigar alternativas ou aguardar fix upstream do tauri-plugin-http.

**Tech Debt:**
- Binario Tauri se chama `tauri-app` (generico) - deveria ser `legal-workbench`

---

### #3 - UX: Feedback de progresso inadequado (PRIORIDADE MEDIA)

**Modulo:** Text Extractor (frontend)
**Sintoma:** Barra de progresso para em 10% e pula direto para 100%
**Data:** 2026-01-30

Usuario nao sabe se job travou ou esta processando. Sem nocao de tempo restante.

**Melhorias sugeridas:**
1. Progresso granular por pagina/fase
2. Fases visiveis ("Inicializando...", "Processando pagina X de Y")
3. Tempo estimado baseado em tamanho do PDF

---

## Resolvidos

### #4 - UI: Checker mostra "limpeza Gemini" mas agora e script

**Modulo:** Text Extractor (frontend)
**Sintoma:** Interface ainda mostra opcao "limpeza Gemini" mas a limpeza agora e feita por script
**Status:** Resolvido
**Data:** 2026-01-30
**Resolvido em:** 2026-02-02

**Solucao:**
UI agora tem duas opcoes separadas:
- "Use Gemini enhancement" - para limpeza via Gemini (opcional)
- "Limpeza final (script)" - para limpeza via script local

**Arquivos modificados:**
- `frontend/src/components/text-extractor/UploadPanel.tsx`: Adicionado toggle `useScript`
- `frontend/src/store/textExtractorStore.ts`: Estado `useScript`
- `frontend/src/types/textExtractor.ts`: Tipo `useScript` em ExtractOptions
- `docker/services/text-extractor/core/`: Modulo de limpeza por script (cleaner, detector, normalizer, patterns)

---

### #2 - Modal Cold Start: Latencia inicial excessiva

**Modulo:** Text Extractor (Modal serverless)
**Sintoma:** Primeira extracao apos periodo de inatividade leva varios minutos extras
**Status:** Resolvido
**Data:** 2026-01-30
**Resolvido em:** 2026-01-30

**Causa Raiz:**
- Cada container T4 precisava carregar modelos Marker (~1.35GB) do zero
- Com multi-T4 parallel (7+ containers), todos sofriam cold start simultaneamente
- Tempo total de cold start: ~2 minutos por container

**Solucao:**
Implementar GPU Memory Snapshot (Modal alpha feature):
- Classe `T4Extractor` com `@app.cls(enable_memory_snapshot=True, experimental_options={"enable_gpu_snapshot": True})`
- Metodo `@modal.enter(snap=True)` carrega modelos e captura na VRAM
- Novos containers restauram snapshot em ~10s em vez de carregar modelos

**Arquivos modificados:**
- `ferramentas/legal-text-extractor/modal_worker.py`
  - Adicionada classe `T4Extractor` com GPU snapshot
  - Atualizada `extract_pdf_parallel()` para usar `T4Extractor`
  - Adicionada funcao `warmup_t4_snapshot()` e CLI `--warmup-t4`

**Comando para criar snapshot apos deploy:**
```bash
modal run modal_worker.py --warmup-t4
```

---

### #5 - Download nao funciona

**Modulo:** Text Extractor (frontend Tauri)
**Sintoma:** Botao de download nao funciona apos extracao
**Status:** Resolvido
**Data:** 2026-01-30
**Resolvido em:** 2026-01-30

**Causa Raiz:**
- Implementacao usava `document.createElement('a').click()` que nao funciona no WebKitGTK do Tauri Linux
- WebKitGTK tem restricoes de seguranca que bloqueiam downloads via DOM manipulation

**Solucao:**
Usar APIs nativas do Tauri para salvar arquivo:
- `@tauri-apps/plugin-dialog` para dialog de salvar
- `@tauri-apps/plugin-fs` para escrever arquivo
- Fallback para browser download quando nao esta no Tauri

**Arquivos modificados:**
- `frontend/src/lib/tauri.ts`: Adicionada funcao `saveFileNative()`
- `frontend/src/components/text-extractor/OutputPanel.tsx`: `handleDownload` usa nativo no Tauri
- `frontend/src-tauri/capabilities/default.json`: Adicionadas permissoes `dialog:default` e `fs:default`

