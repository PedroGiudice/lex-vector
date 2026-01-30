# Issues Conhecidos

Problemas identificados aguardando resolucao.

---

## Abertos

### #2 - Modal Cold Start: Latencia inicial excessiva (PRIORIDADE ALTA)

**Modulo:** Text Extractor (Modal serverless)
**Sintoma:** Primeira extracao apos periodo de inatividade leva varios minutos extras
**Data:** 2026-01-30

O Modal precisa inicializar containers a cada cold start. Impacta experiencia do usuario.

**Solucoes a investigar:**
1. Keep-warm (cron ping periodico)
2. Provisioned concurrency (custo adicional)
3. Feedback visual diferenciando cold start de processamento

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

### #4 - UI: Checker mostra "limpeza Gemini" mas agora e script

**Modulo:** Text Extractor (frontend)
**Sintoma:** Interface ainda mostra opcao "limpeza Gemini" mas a limpeza agora e feita por script
**Data:** 2026-01-30

Atualizar label/UI para refletir que a limpeza e via script, nao mais Gemini.

---

### #5 - Download nao funciona

**Modulo:** Text Extractor (frontend)
**Sintoma:** Botao de download nao funciona apos extracao
**Data:** 2026-01-30

Investigar implementacao do download no app Tauri.

---

## Resolvidos

### #1 - Text Extractor: "Submission failed: Network Error"

**Modulo:** Text Extractor (frontend + Tauri)
**Sintoma:** Ao submeter PDF para extracao, erro "Submission failed: Network Error"
**Status:** Resolvido (DEFINITIVO)
**Data:** 2026-01-29
**Resolvido em:** 2026-01-30

**Causa Raiz (descoberta incremental):**
1. CORS invalido: `allow_origins=["*"]` + `allow_credentials=True`
2. IP hardcoded em `dynamic.yml` apontava para container antigo
3. **(DEFINITIVO)** WebKitGTK (engine Tauri Linux) tem limitacoes com fetch/CORS causando "Broken pipe"

**Solucao Definitiva:**
Usar `tauri-plugin-http` em vez do fetch nativo do WebView.

**Arquivos modificados:**
- `Cargo.toml`: `tauri-plugin-http = "2"`
- `lib.rs`: `.plugin(tauri_plugin_http::init())`
- `capabilities/default.json`: `"http:default"`
- `textExtractorApi.ts`: usa `tauriFetch` quando `isTauri()` = true

**Tech Debt:**
- Binario Tauri se chama `tauri-app` (generico) - deveria ser `legal-workbench`
