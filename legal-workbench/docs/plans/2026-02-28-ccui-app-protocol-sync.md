# ccui-app Protocol Sync: session_id + chat_input + chat_init

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Sincronizar os tipos TypeScript do ccui-app com o schema atual do ccui-backend (ProcessProxy), corrigindo tres gaps: campos `session_id` ausentes em mensagens de chat, tipo `chat_init` inexistente, e input de chat usando canal tmux em vez de ProcessProxy.

**Architecture:** O ccui-backend agora usa ProcessProxy (stream-json). O `ServerMessage` Rust emite `session_id` em `chat_start/delta/end` e um novo evento `chat_init`. O `ClientMessage` tem `chat_input` (com `session_id`) para enviar texto ao Claude via ProcessProxy -- diferente de `input` (com `channel`, legado tmux). O frontend precisa refletir esses contratos exatamente.

**Tech Stack:** TypeScript, React 19, Vitest, ccui-app (`legal-workbench/ccui-app/`). Nenhuma nova dependencia.

---

## Task 1: Atualizar tipos ServerMessage em protocol.ts

**Contexto:** O backend emite `session_id` em `chat_start`, `chat_delta` e `chat_end`. Emite tambem `chat_init` (metadados da sessao Claude). O frontend nao tem esses campos/tipo, o que causa mismatch silencioso.

**Files:**
- Modify: `legal-workbench/ccui-app/src/types/protocol.ts`
- Modify: `legal-workbench/ccui-app/src/__tests__/protocol.test.ts`

**Step 1: Escrever testes falhando**

Em `src/__tests__/protocol.test.ts`, adicionar ao describe existente:

```typescript
it("chat_start tem session_id", () => {
  const msg: ServerMessage = {
    type: "chat_start",
    message_id: "m1",
    session_id: "sess_abc",
  };
  expect(msg.session_id).toBe("sess_abc");
});

it("chat_delta tem session_id", () => {
  const msg: ServerMessage = {
    type: "chat_delta",
    message_id: "m1",
    session_id: "sess_abc",
    part: { type: "text", content: "chunk" },
  };
  expect(msg.session_id).toBe("sess_abc");
});

it("chat_end tem session_id", () => {
  const msg: ServerMessage = {
    type: "chat_end",
    message_id: "m1",
    session_id: "sess_abc",
  };
  expect(msg.session_id).toBe("sess_abc");
});

it("chat_init existe e tem campos corretos", () => {
  const msg: ServerMessage = {
    type: "chat_init",
    session_id: "sess_abc",
    model: "claude-sonnet-4-5",
    claude_session_id: "claude_xyz",
  };
  expect(msg.type).toBe("chat_init");
  expect(msg.model).toBe("claude-sonnet-4-5");
});
```

**Step 2: Rodar testes para confirmar falha**

```bash
cd legal-workbench/ccui-app && bun run test src/__tests__/protocol.test.ts
```

Esperado: erros de TypeScript (campos inexistentes no tipo).

**Step 3: Atualizar ServerMessage em protocol.ts**

Substituir as linhas de `chat_start`, `chat_delta`, `chat_end` e adicionar `chat_init`:

```typescript
export type ServerMessage =
  | { type: "output"; channel: string; data: string }
  | { type: "session_created"; session_id: string; case_id?: string }
  | { type: "session_ended"; session_id: string }
  | { type: "chat_init"; session_id: string; model: string; claude_session_id: string }
  | { type: "chat_start"; message_id: string; session_id: string }
  | { type: "chat_delta"; message_id: string; session_id: string; part: MessagePart }
  | { type: "chat_end"; message_id: string; session_id: string }
  | { type: "error"; message: string }
  | { type: "pong" };
```

**Step 4: Rodar testes para confirmar que passam**

```bash
cd legal-workbench/ccui-app && bun run test src/__tests__/protocol.test.ts
```

Esperado: todos os testes passando (incluindo os 3 existentes + 4 novos).

**Step 5: Commit**

```bash
git add legal-workbench/ccui-app/src/types/protocol.ts
git add legal-workbench/ccui-app/src/__tests__/protocol.test.ts
git commit -m "feat(ccui-app): sincronizar ServerMessage com schema ProcessProxy (session_id + chat_init)"
```

---

## Task 2: Adicionar chat_input ao ClientMessage

**Contexto:** O backend tem dois tipos de input:
- `input` (canal tmux, legado) -- keepalive para developer mode
- `chat_input` (ProcessProxy, novo) -- envia texto ao Claude via `session_id`

O frontend deve usar `chat_input` para o fluxo de chat tipado.

**Files:**
- Modify: `legal-workbench/ccui-app/src/types/protocol.ts`
- Modify: `legal-workbench/ccui-app/src/__tests__/protocol.test.ts`

**Step 1: Escrever teste falhando**

```typescript
it("ClientMessage aceita chat_input com session_id", () => {
  const msg: ClientMessage = {
    type: "chat_input",
    session_id: "sess_abc",
    text: "Qual o status do processo?",
  };
  expect(msg.type).toBe("chat_input");
});
```

**Step 2: Rodar para confirmar falha**

```bash
cd legal-workbench/ccui-app && bun run test src/__tests__/protocol.test.ts
```

Esperado: erro TypeScript (tipo inexistente).

**Step 3: Adicionar chat_input ao ClientMessage**

```typescript
export type ClientMessage =
  | { type: "create_session"; case_id?: string }
  | { type: "input"; channel: string; text: string }
  | { type: "chat_input"; session_id: string; text: string }
  | { type: "resize"; channel: string; cols: number; rows: number }
  | { type: "destroy_session"; session_id: string }
  | { type: "ping" };
```

**Step 4: Rodar testes**

```bash
cd legal-workbench/ccui-app && bun run test src/__tests__/protocol.test.ts
```

Esperado: todos passando.

**Step 5: Commit**

```bash
git add legal-workbench/ccui-app/src/types/protocol.ts
git add legal-workbench/ccui-app/src/__tests__/protocol.test.ts
git commit -m "feat(ccui-app): adicionar chat_input ao ClientMessage (ProcessProxy)"
```

---

## Task 3: Atualizar useChat para usar chat_input e session_id

**Contexto:** `useChat` atualmente envia `{ type: "input", channel: "main", text }` (legado tmux). Com ProcessProxy, deve enviar `{ type: "chat_input", session_id, text }`. O `session_id` vem do `SessionContext`. Tambem deve ignorar `chat_init` graciosamente.

**Files:**
- Modify: `legal-workbench/ccui-app/src/hooks/useChat.ts`
- Modify: `legal-workbench/ccui-app/src/__tests__/useChat.test.ts`

**Step 1: Escrever testes falhando**

Em `src/__tests__/useChat.test.ts`, primeiro adicionar mock do SessionContext ao bloco de mocks existente:

```typescript
// Adicionar apos o mock de WebSocketContext:
const mockSessionId = "sess_test_123";
vi.mock("../contexts/SessionContext", () => ({
  useSession: () => ({
    sessionId: mockSessionId,
    caseId: "caso-001",
    selectCase: vi.fn(),
    createSession: vi.fn(),
    reset: vi.fn(),
  }),
}));
```

Depois adicionar os testes:

```typescript
it("sendMessage envia chat_input com session_id", () => {
  const { result } = renderHook(() => useChat());
  act(() => result.current.sendMessage("Ola processProxy"));
  expect(mockSend).toHaveBeenCalledWith({
    type: "chat_input",
    session_id: "sess_test_123",
    text: "Ola processProxy",
  });
});

it("ignora chat_init sem crashar", () => {
  const { result } = renderHook(() => useChat());
  // Nao deve lancar excecao
  act(() => messageHandler?.({
    type: "chat_init",
    session_id: "sess_abc",
    model: "claude-sonnet-4-5",
    claude_session_id: "claude_xyz",
  }));
  expect(result.current.messages).toHaveLength(0);
});

it("chat_start/delta/end com session_id funcionam igual", () => {
  const { result } = renderHook(() => useChat());

  act(() => messageHandler?.({ type: "chat_start", message_id: "m1", session_id: "sess_abc" }));
  expect(result.current.isStreaming).toBe(true);

  act(() => messageHandler?.({
    type: "chat_delta",
    message_id: "m1",
    session_id: "sess_abc",
    part: { type: "text", content: "ola" },
  }));
  expect(result.current.messages[0].parts[0].content).toBe("ola");

  act(() => messageHandler?.({ type: "chat_end", message_id: "m1", session_id: "sess_abc" }));
  expect(result.current.isStreaming).toBe(false);
});
```

**Step 2: Rodar testes para confirmar falha**

```bash
cd legal-workbench/ccui-app && bun run test src/__tests__/useChat.test.ts
```

Esperado: "sendMessage envia chat_input" FAIL (envia `input` em vez de `chat_input`).

**Step 3: Atualizar useChat.ts**

Mudancas necessarias no `src/hooks/useChat.ts`:

1. Importar `useSession`:
```typescript
import { useSession } from "../contexts/SessionContext";
```

2. Dentro de `useChat()`, adicionar:
```typescript
const { sessionId } = useSession();
```

3. Atualizar `sendMessage`:
```typescript
const sendMessage = useCallback(
  (text: string) => {
    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      parts: [{ type: "text", content: text }],
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    if (sessionId) {
      send({ type: "chat_input", session_id: sessionId, text });
    }
  },
  [send, sessionId]
);
```

4. Adicionar case `chat_init` no switch (noop):
```typescript
case "chat_init":
  // Metadados da sessao Claude -- ignorado pelo hook de chat
  break;
```

**Step 4: Rodar testes**

```bash
cd legal-workbench/ccui-app && bun run test src/__tests__/useChat.test.ts
```

Esperado: todos passando.

**Step 5: Commit**

```bash
git add legal-workbench/ccui-app/src/hooks/useChat.ts
git add legal-workbench/ccui-app/src/__tests__/useChat.test.ts
git commit -m "feat(ccui-app): useChat usa chat_input (ProcessProxy) + suporte a chat_init"
```

---

## Task 4: Atualizar teste de integracao do fluxo de chat

**Contexto:** O teste de integracao `chat-flow.test.tsx` usa os tipos antigos (sem `session_id`). Deve ser atualizado para refletir o novo protocolo.

**Files:**
- Modify: `legal-workbench/ccui-app/src/__tests__/integration/chat-flow.test.tsx`

**Step 1: Rodar o teste existente para ver quais falham**

```bash
cd legal-workbench/ccui-app && bun run test src/__tests__/integration/chat-flow.test.tsx
```

Observar quais testes falham por tipo incompativel.

**Step 2: Atualizar os eventos no teste**

Para cada ocorrencia de `chat_start`, adicionar `session_id`:
```typescript
// Antes:
{ type: "chat_start", message_id: "m1" }
// Depois:
{ type: "chat_start", message_id: "m1", session_id: "sess_test" }
```

Para cada ocorrencia de `chat_delta`, adicionar `session_id`:
```typescript
// Antes:
{ type: "chat_delta", message_id: "m1", part: ... }
// Depois:
{ type: "chat_delta", message_id: "m1", session_id: "sess_test", part: ... }
```

Para cada ocorrencia de `chat_end`, adicionar `session_id`:
```typescript
// Antes:
{ type: "chat_end", message_id: "m1" }
// Depois:
{ type: "chat_end", message_id: "m1", session_id: "sess_test" }
```

**Step 3: Rodar testes**

```bash
cd legal-workbench/ccui-app && bun run test src/__tests__/integration/chat-flow.test.tsx
```

Esperado: todos passando.

**Step 4: Rodar suite completa**

```bash
cd legal-workbench/ccui-app && bun run test
```

Esperado: todos os testes passando, sem erros TypeScript.

**Step 5: Commit**

```bash
git add legal-workbench/ccui-app/src/__tests__/integration/chat-flow.test.tsx
git commit -m "test(ccui-app): atualizar chat-flow integration test para protocolo ProcessProxy"
```

---

## Task 5: Verificacao final

**Step 1: Rodar suite completa de testes**

```bash
cd legal-workbench/ccui-app && bun run test
```

Esperado: todos passando.

**Step 2: Type-check sem erros**

```bash
cd legal-workbench/ccui-app && bun run tsc --noEmit
```

Esperado: sem erros de tipo.

**Step 3: Verificar que backend compila**

```bash
cd legal-workbench/ccui-backend && cargo check
```

Esperado: `Finished`.

**Step 4: Commit de encerramento (se nada ficou para tras)**

```bash
git log --oneline -5
```

Verificar que os 4 commits das tasks anteriores estao presentes.
