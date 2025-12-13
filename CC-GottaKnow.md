# CC-GottaKnow

**Arquivo de comunicação inter-sessões para Claude Code.**

Este arquivo contém breaking changes e alterações importantes que DEVEM ser avaliadas antes de qualquer trabalho. Claude Code deve ler este arquivo no início de cada sessão e comunicar itens pendentes ao usuário.

---

<gotta-know>

<breaking-change id="BUN-001" status="action-required" severity="high" date="2025-12-13">
  <title>Bun adicionado à stack como runtime JS padrão</title>
  <description>
    Todos os hooks JavaScript agora usam `bun run` em vez de `node`.
    Bun 1.3.4 é ~25% mais rápido para execução de scripts.
    Referência: ARCHITECTURE.md (ADR-005)
  </description>
  <required-actions>
    <action step="1">Verificar se Bun está instalado: `bun --version`</action>
    <action step="2">Se não instalado: `curl -fsSL https://bun.sh/install | bash`</action>
    <action step="3">(Opcional) Reinstalar Claude Code via Bun: `npm uninstall -g @anthropic-ai/claude-code && bun install -g @anthropic-ai/claude-code`</action>
  </required-actions>
  <affected-files>
    <file>.claude/settings.json</file>
    <file>.claude/hooks/*.js</file>
    <file>.claude/statusline/*.js</file>
  </affected-files>
  <verification>
    <command>bun run .claude/hooks/hook-wrapper.js .claude/hooks/prompt-enhancer.js &lt;&lt;&lt; '{"prompts":[{"content":"test"}]}'</command>
    <expected>Execução silenciosa (sem erro)</expected>
  </verification>
  <docs>docs/BUN_SETUP_GUIDE.md</docs>
</breaking-change>

</gotta-know>

---

## Formato de Entrada

```xml
<breaking-change id="ID-ÚNICO" status="action-required|acknowledged|resolved" severity="high|medium|low" date="YYYY-MM-DD">
  <title>Título curto</title>
  <description>Descrição detalhada</description>
  <required-actions>
    <action step="N">Ação a tomar</action>
  </required-actions>
  <affected-files>
    <file>caminho/do/arquivo</file>
  </affected-files>
  <verification>
    <command>Comando para verificar</command>
    <expected>Resultado esperado</expected>
  </verification>
  <docs>Link para documentação</docs>
</breaking-change>
```

## Status

| Status | Significado |
|--------|-------------|
| `action-required` | Requer ação do usuário antes de continuar |
| `acknowledged` | Usuário ciente, pode prosseguir |
| `resolved` | Completamente resolvido, manter para histórico |

## Instruções para Claude Code

Ao iniciar uma sessão:

1. **Ler este arquivo** se existir
2. **Filtrar** itens com `status="action-required"`
3. **Comunicar** ao usuário os itens pendentes
4. **Oferecer** executar as ações necessárias
5. **Atualizar** status após resolução
