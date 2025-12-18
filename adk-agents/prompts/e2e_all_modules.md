# Teste E2E Completo - Legal Workbench All-React

## Contexto
O Legal Workbench foi migrado para All-React com React Router.
URL base: http://localhost/app

## Módulos a Testar
1. Hub Home (/)
2. Trello Command Center (/trello)
3. Doc Assembler (/doc-assembler)
4. STJ Dados Abertos (/stj)

## Roteiro de Testes

### FASE 1: Hub Home
1. Navegue para http://localhost/app
2. Tire screenshot "hub_home_inicial"
3. Capture snapshot para verificar:
   - Header "Legal Workbench"
   - Cards dos 3 módulos (Trello, Doc Assembler, STJ)
   - Grid de estatísticas
4. Clique no card do Trello
5. Verifique navegação para /app/trello
6. Registre resultado: "Hub Home - Navegação"

### FASE 2: Trello Command Center
1. Já em /app/trello, capture snapshot
2. Tire screenshot "trello_module"
3. Verifique elementos:
   - Header "Trello Command Center"
   - Seletor de board
   - Status de sincronização
   - Três painéis (NavigationPanel, DataTable, ActionsPanel)
4. Se houver boards, selecione um e capture snapshot novamente
5. Registre resultado: "Trello - Interface"

### FASE 3: Doc Assembler
1. Navegue para http://localhost/app/doc-assembler
2. Capture snapshot
3. Tire screenshot "doc_assembler_module"
4. Verifique elementos:
   - Header "Doc Assembler"
   - DropZone para upload
   - Lista de templates
   - Empty state ou DocumentViewer
   - Painel de Annotations
5. Registre resultado: "Doc Assembler - Interface"

### FASE 4: STJ Dados Abertos
1. Navegue para http://localhost/app/stj
2. Capture snapshot
3. Tire screenshot "stj_module"
4. Verifique elementos:
   - Header "STJ Dados Abertos"
   - Stats de acórdãos (se disponível)
   - SearchForm com input e filtros
   - ResultsList área
   - CaseDetail área
5. Se possível, teste uma busca (preencha termo e clique buscar)
6. Registre resultado: "STJ - Interface"

### FASE 5: Navegação via Sidebar
1. Navegue de volta para http://localhost/app
2. Verifique a sidebar:
   - 4 ícones de navegação
   - Estado ativo correto
3. Clique em cada ícone e verifique que navega corretamente
4. Registre resultado: "Sidebar - Navegação"

## Output Esperado
Para cada fase, use write_test_result com:
- test_name: Nome descritivo
- status: PASSOU, FALHOU, ou SKIP
- details: O que foi verificado e resultado

## Ao Final
Crie um resumo consolidado:
```
## Resultado Final E2E

| Módulo | Status | Observações |
|--------|--------|-------------|
| Hub Home | ? | ... |
| Trello | ? | ... |
| Doc Assembler | ? | ... |
| STJ | ? | ... |
| Sidebar | ? | ... |

Total: X/5 módulos funcionando
```
