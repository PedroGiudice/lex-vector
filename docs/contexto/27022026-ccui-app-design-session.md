# Contexto: ccui-app Design Session

**Data:** 2026-02-27
**Sessao:** branch `wrapper-legal-agents-front`
**Duracao:** ~30min

---

## O que foi feito

Brainstorming e design completo do ccui-app (app Tauri standalone para advogados).
Nenhum codigo escrito -- apenas documentacao de design.

### Decisoes tomadas com o usuario

1. **Escopo:** Fluxo completo (seletor de caso -> sessao -> multi-canal)
2. **Arquitetura:** App Tauri standalone no PC do advogado, conectando remotamente ao ccui-backend na VM
3. **Localizacao:** `legal-workbench/ccui-app/` no monorepo (Abordagem A)
4. **Visual:** Evoluir ccui-v2 -- menos IDE, mais chatbox profissional. Funcionalidade primeiro
5. **Execucao:** Agent team na proxima sessao
6. **Backend:** Nao muda. ccui-backend na VM ja tem todos os endpoints necessarios

### Documento produzido

`legal-workbench/docs/plans/2026-02-27-ccui-app-standalone-design.md` -- design completo com:
- Estrutura do projeto
- Fluxo do usuario
- Protocolo WS (match com backend)
- Endpoints REST
- Componentes a reutilizar
- 6 tasks decompostas para agent team

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `docs/plans/2026-02-27-ccui-app-standalone-design.md` | Criado |
| `docs/contexto/27022026-ccui-app-design-session.md` | Criado (este arquivo) |

## Pendencias

1. Commitar os CLAUDE.md da Phase 2 (ficaram pendentes da sessao anterior)
2. Remover rota `/ccui-assistant` do LW principal (apos ccui-app funcionar)

## Para a proxima sessao

O design esta pronto. A proxima sessao deve:

1. Ler `legal-workbench/docs/plans/2026-02-27-ccui-app-standalone-design.md`
2. Invocar skill `superpowers:writing-plans` para criar plano de implementacao detalhado
3. Lancar agent team com as 6 tasks do design
4. Modelo recomendado para teammates: sonnet (custo-beneficio para frontend)
