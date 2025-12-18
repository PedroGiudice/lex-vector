# TEMPLATE: Frontend Handoff para Agentes ADK

> **Uso**: Copie este template e preencha as seções `{{PLACEHOLDER}}` para criar um prompt de handoff completo para agentes ADK continuarem desenvolvimento frontend.

---

# PROMPT: {{NOME_DO_PROJETO}} Frontend

## Contexto do Projeto

O **{{NOME_DO_PROJETO}}** é {{DESCRIÇÃO_BREVE}}. O foco principal é **{{FOCO_PRINCIPAL}}**.

### Stack Técnica
- {{FRAMEWORK}} (ex: React 18 + TypeScript + Vite)
- {{STATE_MANAGEMENT}} (ex: Zustand, Redux, Context)
- {{CSS_FRAMEWORK}} (ex: Tailwind CSS)
- API Backend: {{BACKEND_INFO}}

### Arquivos Principais
```
{{DIRETORIO_FRONTEND}}/
├── services/{{API_SERVICE}}.ts    # API client
├── store/{{STORE_FILE}}.ts        # State management
├── components/
│   ├── layout/                    # Layout components
│   └── {{FEATURE}}/               # Feature components
│       ├── {{COMPONENT_1}}.tsx
│       ├── {{COMPONENT_2}}.tsx
│       └── {{COMPONENT_3}}.tsx
```

---

## Decisões de Design

### 1. {{DECISAO_1_TITULO}}
{{DECISAO_1_DESCRICAO}}

### 2. {{DECISAO_2_TITULO}}
{{DECISAO_2_DESCRICAO}}

### 3. {{DECISAO_3_TITULO}}
{{DECISAO_3_DESCRICAO}}

---

## O Que Já Foi Implementado

### Backend ({{PERCENTUAL_BACKEND}}% funcional)
- {{ENDPOINT_1}}
- {{ENDPOINT_2}}
- {{ENDPOINT_3}}

### Frontend ({{PERCENTUAL_FRONTEND}}% implementado)

**Funcional:**
- {{FEATURE_FUNCIONAL_1}}
- {{FEATURE_FUNCIONAL_2}}
- {{FEATURE_FUNCIONAL_3}}

**Faltando:**
1. **{{FEATURE_FALTANDO_1}}** - {{DESCRICAO_1}}
2. **{{FEATURE_FALTANDO_2}}** - {{DESCRICAO_2}}
3. **{{FEATURE_FALTANDO_3}}** - {{DESCRICAO_3}}

---

## O Que Precisa Ser Feito

### Prioridade 1: {{P1_TITULO}}
```typescript
// {{P1_CONTEXTO}}
{{P1_CODIGO_EXEMPLO}}
```

### Prioridade 2: {{P2_TITULO}}
```typescript
// {{P2_CONTEXTO}}
{{P2_CODIGO_EXEMPLO}}
```

### Prioridade 3: {{P3_TITULO}}
```typescript
// {{P3_CONTEXTO}}
{{P3_CODIGO_EXEMPLO}}
```

---

## Endpoints Backend Disponíveis

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `{{ENDPOINT_PATH_1}}` | {{METHOD_1}} | {{DESC_1}} |
| `{{ENDPOINT_PATH_2}}` | {{METHOD_2}} | {{DESC_2}} |
| `{{ENDPOINT_PATH_3}}` | {{METHOD_3}} | {{DESC_3}} |

---

## Paleta de Cores (Tailwind)

```css
/* Definido em tailwind.config.js */
bg-main: {{COR_BG_MAIN}}        /* Fundo principal */
bg-panel: {{COR_BG_PANEL}}      /* Painéis */
bg-input: {{COR_BG_INPUT}}      /* Inputs */
text-primary: {{COR_TEXT_PRIMARY}}   /* Texto principal */
text-secondary: {{COR_TEXT_SECONDARY}} /* Texto secundário */
accent-{{COR_ACCENT_NAME}}: {{COR_ACCENT}}    /* Accent */
success-green: {{COR_SUCCESS}}  /* Sucesso */
danger-red: {{COR_DANGER}}      /* Perigo */
```

---

## Como Rodar

```bash
cd {{DIRETORIO_PROJETO}}

# Start all services
{{COMANDO_START}}

# Frontend em {{URL_FRONTEND}}
# API em {{URL_API}}
```

---

## Referência Visual

```
{{ASCII_WIREFRAME}}
```

---

## Critérios de Aceite

1. **{{CRITERIO_1}}** - {{CRITERIO_1_DESC}}
2. **{{CRITERIO_2}}** - {{CRITERIO_2_DESC}}
3. **{{CRITERIO_3}}** - {{CRITERIO_3_DESC}}
4. **{{CRITERIO_4}}** - {{CRITERIO_4_DESC}}
5. **Build passa** - `npm run build` sem erros TypeScript

---

## FASE FINAL: Testes Visuais com Playwright

**IMPORTANTE**: Após implementação, usar agente `test-writer-fixer` ou Playwright MCP para validação visual completa.

### Checklist de Testes E2E

```gherkin
Feature: {{NOME_DO_PROJETO}} - {{FEATURE_PRINCIPAL}}

  Background:
    Given I navigate to {{URL_FRONTEND}}
    And I wait for {{ELEMENTO_INICIAL}} to load

  # ============================================
  # TESTE 1: Carregamento Inicial
  # ============================================
  Scenario: Page loads correctly
    Then I should see "{{TITULO_PAGINA}}" header
    And {{ELEMENTO_PRINCIPAL_1}} should be visible
    And {{ELEMENTO_PRINCIPAL_2}} should be visible

  # ============================================
  # TESTE 2: {{TESTE_2_TITULO}}
  # ============================================
  Scenario: {{TESTE_2_TITULO}}
    When {{TESTE_2_ACAO}}
    Then {{TESTE_2_RESULTADO}}

  # ============================================
  # TESTE 3: {{TESTE_3_TITULO}}
  # ============================================
  Scenario: {{TESTE_3_TITULO}}
    When {{TESTE_3_ACAO}}
    Then {{TESTE_3_RESULTADO}}

  # ============================================
  # TESTE 4: {{TESTE_4_TITULO}}
  # ============================================
  Scenario: {{TESTE_4_TITULO}}
    When {{TESTE_4_ACAO}}
    Then {{TESTE_4_RESULTADO}}

  # ============================================
  # TESTE 5: {{TESTE_5_TITULO}}
  # ============================================
  Scenario: {{TESTE_5_TITULO}}
    When {{TESTE_5_ACAO}}
    Then {{TESTE_5_RESULTADO}}
```

### Comandos Playwright para Testes

```typescript
// Usar com MCP Playwright ou test-writer-fixer agent

// 1. Navegar e aguardar carregamento
await page.goto('{{URL_FRONTEND}}');
await page.waitForSelector('{{SELETOR_CARREGAMENTO}}');

// 2. {{ACAO_TESTE_1}}
await page.{{COMANDO_1}};

// 3. {{ACAO_TESTE_2}}
await page.{{COMANDO_2}};

// 4. Screenshot para validação visual
await page.screenshot({ path: '{{NOME_SCREENSHOT}}.png' });
```

### Matriz de Testes por Funcionalidade

| Funcionalidade | {{MODO_1}} | {{MODO_2}} | Esperado |
|----------------|------------|------------|----------|
| {{FUNC_1}} | {{F1_M1}} | {{F1_M2}} | {{F1_ESPERADO}} |
| {{FUNC_2}} | {{F2_M1}} | {{F2_M2}} | {{F2_ESPERADO}} |
| {{FUNC_3}} | {{F3_M1}} | {{F3_M2}} | {{F3_ESPERADO}} |
| {{FUNC_4}} | {{F4_M1}} | {{F4_M2}} | {{F4_ESPERADO}} |

### Screenshots de Referência

Após cada teste, capturar screenshot para validação:

```bash
# Diretório para screenshots
{{DIRETORIO_PROJETO}}/test-screenshots/
├── 01-initial-load.png
├── 02-{{SCREENSHOT_2}}.png
├── 03-{{SCREENSHOT_3}}.png
├── 04-{{SCREENSHOT_4}}.png
└── 05-{{SCREENSHOT_5}}.png
```

### Critérios de Sucesso dos Testes

- [ ] Todos os cenários E2E passam
- [ ] Nenhum erro no console do browser
- [ ] Tempo de carregamento < {{TEMPO_MAX}}s
- [ ] {{CRITERIO_TESTE_1}}
- [ ] UI mantém consistência visual

---

## Instruções para o Agente

1. **Leia todo este documento** antes de começar
2. **Verifique o estado atual** - rode o projeto e veja o que funciona
3. **Priorize as tarefas** - P1 > P2 > P3
4. **Teste cada mudança** - não acumule mudanças sem testar
5. **Documente decisões** - se mudar algo do plano, documente o porquê
6. **Rode os testes E2E** - use test-writer-fixer ou Playwright MCP ao final
