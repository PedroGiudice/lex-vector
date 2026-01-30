# Issues Conhecidos

Problemas identificados aguardando resolucao.

---

## Abertos

### #2 - Modal Cold Start: Latencia inicial excessiva (PRIORIDADE)

**Modulo:** Text Extractor (Modal serverless)
**Sintoma:** Primeira extracao apos periodo de inatividade leva varios minutos extras devido ao cold start do Modal
**Status:** Aberto
**Data:** 2026-01-30
**Prioridade:** ALTA

**Descricao:**
O Modal precisa inicializar containers a cada cold start, o que adiciona latencia significativa (minutos) na primeira requisicao. Isso acontece SEMPRE apos periodo de inatividade e prejudica a experiencia do usuario.

**Impacto:**
- Usuario espera muito tempo na primeira extracao do dia
- Timeout pode ocorrer se cold start + processamento exceder limite
- Experiencia ruim para usuarios ocasionais

**Possiveis solucoes a investigar:**
1. **Keep-warm**: Cron job que faz ping periodico para manter container quente
2. **Provisioned concurrency**: Modal permite reservar containers (custo adicional)
3. **Feedback visual**: Mostrar ao usuario que esta em cold start vs processamento
4. **Cache agressivo**: Reduzir necessidade de chamadas ao Modal

---

### #3 - UX: Feedback de progresso inadequado

**Modulo:** Text Extractor (frontend)
**Sintoma:** Barra de progresso para em 10% e pula direto para 100% quando job finaliza
**Status:** Aberto
**Data:** 2026-01-30
**Prioridade:** MEDIA

**Descricao:**
O usuario ve apenas uma barra de porcentagem que nao reflete o progresso real:
- Para em 10% durante todo o processamento
- Pula para 100% apenas quando job completa
- Nenhuma informacao adicional (paginas processadas, tempo estimado, fase atual)

**Impacto:**
- Usuario nao sabe se job travou ou esta processando
- Sem nocao de tempo restante
- Experiencia frustrante em jobs longos (10-20 min)

**Melhorias sugeridas:**
1. **Progresso granular**: Backend reportar progresso real por pagina/fase
2. **Fases visiveis**: "Inicializando Modal...", "Processando pagina X de Y", "Limpando texto..."
3. **Tempo estimado**: Baseado em tamanho do PDF e historico
4. **Logs em tempo real**: Stream de logs do backend para o frontend
5. **Indicador de cold start**: Diferenciar "aguardando servidor" de "processando"

---

## Resolvidos

### #1 - Text Extractor: "Submission failed: Network Error"

**Modulo:** Text Extractor (frontend + Tauri)
**Sintoma:** Ao submeter PDF para extracao, erro "Submission failed: Network Error"
**Status:** Resolvido (DEFINITIVO)
**Data:** 2026-01-29
**Resolvido em:** 2026-01-30

**Causa Raiz (descoberta incremental):**

1. **(Parcial)** CORS invalido: `allow_origins=["*"]` + `allow_credentials=True` viola spec HTTP
2. **(Parcial)** IP hardcoded em `dynamic.yml` apontava para container antigo
3. **(DEFINITIVO)** **WebKitGTK (engine do Tauri no Linux) tem limitacoes com fetch/CORS** que causavam "Broken pipe" antes mesmo da requisicao chegar ao backend

**Solucao Definitiva:**

Usar `tauri-plugin-http` em vez do fetch nativo do WebView. O plugin faz requisicoes HTTP via Rust nativo, contornando limitacoes do WebKitGTK.

**Arquivos modificados:**
- `frontend/src-tauri/Cargo.toml`: adicionado `tauri-plugin-http = "2"`
- `frontend/src-tauri/src/lib.rs`: inicializado `.plugin(tauri_plugin_http::init())`
- `frontend/src-tauri/capabilities/default.json`: adicionado `"http:default"`
- `frontend/src/services/textExtractorApi.ts`: usa `tauriFetch` quando `isTauri()` retorna true

**Outras correcoes aplicadas na sessao:**
- CSP atualizado para incluir `ipc://localhost`
- Permissoes ACL para plugins: dialog, fs, notification, store, updater, process, http
- DevTools habilitado para debugging (feature `devtools` no Cargo.toml)

**Tech Debt Identificado (baixa prioridade):**
- `main.py`: IP Tailscale hardcoded (considerar env var)
- Binario Tauri se chama `tauri-app` (generico) - deveria ser `legal-workbench`
