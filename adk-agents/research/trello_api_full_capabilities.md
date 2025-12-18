# Trello REST API - Pesquisa Completa

> Pesquisa realizada em 2024-12-17
> Fonte: developer.atlassian.com/cloud/trello/

## Resumo Executivo

A API REST do Trello oferece acesso completo via HTTP (GET, POST, PUT, DELETE).
Rate limits: 300 req/10s por API key, 100 req/10s por token.

---

## 1. DATA EXTRACTION (READ)

### Boards
```
GET /1/boards/{id}                    - Board único
GET /1/boards/{id}/cards              - Todos cards do board
GET /1/boards/{id}/lists              - Todas listas
GET /1/boards/{id}/members            - Membros
GET /1/boards/{id}/labels             - Labels
GET /1/boards/{id}/customFields       - Custom fields
GET /1/boards/{id}/checklists         - Checklists
GET /1/boards/{id}/actions            - Histórico de atividades
GET /1/members/me/boards              - Boards do usuário atual
```

### Cards
```
GET /1/cards/{id}                     - Card único
GET /1/cards/{id}/actions             - Histórico do card
GET /1/cards/{id}/attachments         - Anexos
GET /1/cards/{id}/checklists          - Checklists do card
GET /1/cards/{id}/members             - Membros atribuídos
GET /1/cards/{id}/customFieldItems    - Valores dos custom fields
GET /1/cards/{id}/pluginData          - Dados de Power-Ups
```

### Lists
```
GET /1/lists/{id}                     - Lista única
GET /1/lists/{id}/cards               - Cards da lista
```

### Checklists
```
GET /1/checklists/{id}                - Checklist único
GET /1/checklists/{id}/checkItems     - Items do checklist
```

### Search
```
GET /1/search?query={q}&modelTypes=cards

Operadores de busca:
- @member ou member:name    - Cards do membro (@me = usuário atual)
- board:name               - Cards em board específico
- list:name                - Cards em lista específica
- #label ou label:name     - Cards com label
- due:day|week|month       - Cards por prazo
- created:N                - Cards criados nos últimos N dias
- has:attachments|members  - Cards com feature específica
- is:open|archived         - Status do card
- -operador                - Negação
```

### Batch Requests
```
GET /1/batch?urls={urls}              - Até 10 GETs em uma request
```

---

## 2. DATA CREATION (CREATE)

### Boards
```
POST /1/boards/
  - name (obrigatório)
  - desc, idOrganization, prefs_permissionLevel
```

### Cards
```
POST /1/cards
  - name (obrigatório)
  - idList (obrigatório)
  - desc, pos, due, dueComplete, idMembers, idLabels
  - urlSource, fileSource (para attachments)
```

### Lists
```
POST /1/lists
  - name (obrigatório)
  - idBoard (obrigatório)
  - pos
```

### Checklists
```
POST /1/checklists
  - idCard (obrigatório)
  - name (obrigatório)
  - pos

POST /1/checklists/{id}/checkItems
  - name (obrigatório)
  - pos, checked
```

### Comments
```
POST /1/cards/{id}/actions/comments
  - text (obrigatório)
```

### Labels
```
POST /1/boards/{id}/labels
  - name, color (obrigatórios)
```

### Attachments
```
POST /1/cards/{id}/attachments
  - url OU file
  - name, setCover
```

### Custom Fields
```
POST /1/customFields
  - idModel (board ID), type, name (obrigatórios)
  - Requer Power-Up habilitado!
```

### Webhooks
```
POST /1/webhooks
  - callbackURL (obrigatório)
  - idModel (obrigatório) - board/card/list ID
  - description, active
```

---

## 3. DATA MODIFICATION (UPDATE)

### Cards
```
PUT /1/cards/{id}
  - name, desc, closed, idList, idMembers, idLabels
  - pos, due, dueComplete, cover

PUT /1/cards/{id}/idList              - Mover para outra lista
PUT /1/cards/{id}/pos                 - Mudar posição (top/bottom/número)
PUT /1/cards/{id}/closed              - Arquivar (true) / Desarquivar (false)
```

### Checklist Items
```
PUT /1/cards/{id}/checkItem/{itemId}
  - name, state (complete/incomplete), pos
```

### Custom Field Values
```
PUT /1/cards/{idCard}/customField/{idField}/item
  - value: { text: "..." } ou { number: "42" } ou { checked: "true" } ou { date: "..." }
  - idValue (para dropdowns)
```

### Lists
```
PUT /1/lists/{id}
  - name, closed, pos

POST /1/lists/{id}/moveAllCards       - Mover todos cards
POST /1/lists/{id}/archiveAllCards    - Arquivar todos cards
```

### Comments
```
PUT /1/actions/{id}                   - Editar comentário
  - text
```

---

## 4. DATA DELETION (DELETE)

```
DELETE /1/cards/{id}                  - Deletar card (PERMANENTE!)
DELETE /1/lists/{id}                  - Deletar lista
DELETE /1/checklists/{id}             - Deletar checklist
DELETE /1/checklists/{id}/checkItems/{itemId} - Deletar item
DELETE /1/labels/{id}                 - Deletar label
DELETE /1/cards/{id}/attachments/{attachmentId} - Remover anexo
DELETE /1/cards/{id}/actions/{actionId}/comments - Deletar comentário
DELETE /1/boards/{id}/members/{memberId} - Remover membro do board
DELETE /1/webhooks/{id}               - Deletar webhook
```

⚠️ **IMPORTANTE**: DELETE é permanente! Use `PUT closed=true` para arquivar.

---

## 5. WEBHOOKS & AUTOMAÇÃO

### Criação
```
POST /1/webhooks
  - callbackURL: URL que receberá POST quando model mudar
  - idModel: ID do board/card/list a monitorar
```

### Características
- Notificações em tempo real
- Requests assinadas com HMAC-SHA1 (header X-Trello-Webhook)
- IPs de origem: 104.192.142.240/28
- Auto-desativam após 30 dias de falhas
- Auto-deletam se token expirar

---

## 6. RATE LIMITS

| Limite | Valor |
|--------|-------|
| Por API Key | 300 req / 10 segundos |
| Por Token | 100 req / 10 segundos |
| Endpoint /members | 100 req / 15 minutos |

Headers de resposta:
```
x-rate-limit-api-key-remaining
x-rate-limit-api-token-remaining
```

---

## 7. NESTED RESOURCES

Reduzir requests combinando dados:
```
GET /1/boards/{id}?cards=all&lists=all&members=all&customFields=true
GET /1/cards/{id}?actions=all&actions_limit=1000
```

---

## 8. CUSTOM FIELDS

### Tipos
- **text**: `{ "value": { "text": "Hello" } }`
- **number**: `{ "value": { "number": "42" } }`
- **date**: `{ "value": { "date": "2024-12-15T00:00:00.000Z" } }`
- **checkbox**: `{ "value": { "checked": "true" } }`
- **dropdown**: usa `idValue` para referenciar opção

### Requer Power-Up habilitado no board!

---

## Fontes

- https://developer.atlassian.com/cloud/trello/rest/
- https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/
- https://developer.atlassian.com/cloud/trello/guides/rest-api/webhooks/
- https://developer.atlassian.com/cloud/trello/guides/rest-api/getting-started-with-custom-fields/
