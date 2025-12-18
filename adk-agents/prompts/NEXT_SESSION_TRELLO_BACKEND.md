# Próxima Sessão: Implementar Backend Completo do Trello

## Contexto

Fizemos pesquisa completa da API do Trello e criamos spec de layout para o "Trello Command Center".
Arquivos relevantes:
- `adk-agents/research/trello_api_full_capabilities.md` - Pesquisa da API
- `adk-agents/layout_specs/trello_command_center.md` - Spec do layout

## Problema

O backend atual (`ferramentas/trello-mcp/` e `docker/services/trello-mcp/`) tem implementação PARCIAL.

### O que TEMOS:
- `get_board_structure()` - extração de boards
- `get_board_cards_with_custom_fields()` - cards com custom fields
- `search_cards()` - busca básica
- `batch_get_cards()` - batch de até 10 cards
- `create_card()` - criar card
- `update_card()` - atualizar card
- `move_card()` - mover entre listas
- `add_comment()` - adicionar comentário

### O que FALTA (baseado na pesquisa):

**CREATE:**
- [ ] `create_list()` - criar lista
- [ ] `create_checklist()` - criar checklist
- [ ] `add_checklist_item()` - adicionar item ao checklist
- [ ] `add_attachment()` - adicionar anexo (URL ou arquivo)
- [ ] `create_label()` - criar label

**UPDATE:**
- [ ] `archive_card()` / `unarchive_card()` - arquivar/desarquivar
- [ ] `update_checklist_item()` - marcar complete/incomplete
- [ ] `set_custom_field_value()` - definir valor de custom field
- [ ] `update_list()` - atualizar lista
- [ ] `move_all_cards()` - mover todos cards de uma lista
- [ ] `archive_all_cards()` - arquivar todos cards de uma lista
- [ ] `update_comment()` - editar comentário

**DELETE:**
- [ ] `delete_card()` - deletar card (permanente)
- [ ] `delete_attachment()` - remover anexo
- [ ] `delete_comment()` - deletar comentário
- [ ] `remove_member_from_card()` - remover membro do card
- [ ] `delete_checklist()` - deletar checklist
- [ ] `delete_checklist_item()` - deletar item do checklist

**READ (extras):**
- [ ] `get_card_attachments()` - listar anexos
- [ ] `get_card_actions()` - histórico de atividades
- [ ] `get_card_checklists()` - checklists do card
- [ ] Busca avançada com operadores (@member, #label, due:week, has:attachments)

**WEBHOOKS:**
- [ ] `create_webhook()` - criar webhook
- [ ] `delete_webhook()` - deletar webhook
- [ ] `list_webhooks()` - listar webhooks ativos

## Tarefa

1. **Analisar** a estrutura atual do backend (MCP Server + FastAPI wrapper)
2. **Decidir** onde implementar cada função (MCP, FastAPI, ou ambos)
3. **Implementar** as funções faltantes seguindo o padrão existente
4. **Testar** cada endpoint
5. **Documentar** a API completa

## Arquivos Principais

```
legal-workbench/
├── ferramentas/trello-mcp/
│   └── src/
│       ├── trello_client.py    ← Cliente da API (adicionar métodos aqui)
│       ├── models.py           ← Modelos Pydantic
│       └── server.py           ← MCP Server tools
│
└── docker/services/trello-mcp/
    └── api/
        └── routes.py           ← Endpoints REST (adicionar rotas aqui)
```

## Prompt para Iniciar

```
Preciso implementar o backend completo do Trello para suportar todas as operações da API.

CONTEXTO:
- Pesquisa completa: adk-agents/research/trello_api_full_capabilities.md
- Spec do frontend: adk-agents/layout_specs/trello_command_center.md
- Backend atual: ferramentas/trello-mcp/ e docker/services/trello-mcp/

TAREFA:
1. Primeiro, leia os arquivos de pesquisa e spec para entender o escopo
2. Analise o backend atual para entender o padrão de código
3. Liste TODAS as funções que precisam ser implementadas
4. Implemente cada função seguindo o padrão existente
5. Adicione os endpoints REST correspondentes

PRIORIDADE:
1. CRUD completo de cards (incluindo archive/unarchive)
2. Checklists (criar, adicionar items, marcar complete)
3. Attachments (adicionar, remover, listar)
4. Comments (adicionar, editar, deletar)
5. Custom fields (set value)
6. Busca avançada com operadores

Comece analisando e planejando antes de implementar.
```

---

*Criado em: 2024-12-17*
