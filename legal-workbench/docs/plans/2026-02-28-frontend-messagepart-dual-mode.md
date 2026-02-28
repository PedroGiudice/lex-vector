# Frontend MessagePart + UI Dual-Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Substituir o TerminalPane (xterm.js / bytes brutos) por uma ChatView tipada que recebe MessagePart[] via WebSocket, com dual mode client/developer.

**Architecture:** O backend Rust (ccui-backend) vai deserializar output NDJSON do `claude -p --output-format stream-json` e emitir ChatUpdate tipado via WS. O frontend recebe esses eventos, acumula mensagens num state local (useChat hook), e renderiza via ChatView. Dois modos de visualizacao: developer (raw tools, thinking, code blocks) e client (linguagem juridica, status pills, sem detalhes tecnicos).

**Tech Stack:** React 19, TypeScript, Tailwind CSS 4, Vitest, lucide-react. Sem novas dependencias externas.

---

## Contexto: Arquivos Atuais

| Arquivo | Destino |
|---------|---------|
| `types/protocol.ts` | **Expandir** -- adicionar tipos ChatUpdate e MessagePart |
| `contexts/WebSocketContext.tsx` | **Adaptar** -- tipar mensagens ChatUpdate |
| `contexts/SessionContext.tsx` | **Manter** -- funciona como esta |
| `components/SessionView.tsx` | **Adaptar** -- trocar TerminalPane por ChatView |
| `components/TerminalPane.tsx` | **Manter** -- usado apenas em developer mode como fallback |
| `components/AppRouter.tsx` | **Manter** -- sem mudanca |
| `components/CaseSelector.tsx` | **Manter** -- sem mudanca |
| `components/ConnectionStatus.tsx` | **Manter** -- sem mudanca |
| `components/ChannelTabs.tsx` | **Remover** -- sem multi-canal no novo modelo |
| `components/ErrorBanner.tsx` | **Manter** |
| `components/Spinners.tsx` | **Manter** |
| `hooks/useCcuiApi.ts` | **Manter** |

## Contexto: Reaproveitamento ADK

| Arquivo ADK | Acao | Motivo |
|------------|------|--------|
| `types.ts` (MessagePart, MessagePartType) | **Referencia** | Nossos tipos sao diferentes (alinhados com stream-json do Claude, nao ADK) |
| `ChatWorkspace.tsx` (AgentMessageBody, getClientIntent, layout) | **Adaptar** | Layout e dual-mode sao reaproveitaveis; adaptar tool names para Claude Code |
| `MarkdownRenderer.tsx` | **Copiar e simplificar** | Parser markdown custom, sem deps. Remover slate dependency |
| `Icons.tsx` | **Ignorar** | Usamos lucide-react |
| `agentBridge.ts` | **Ignorar** | Especifico do Gemini ADK |

---

## Task 1: Tipos TypeScript -- ChatUpdate e MessagePart

**Files:**
- Modify: `ccui-app/src/types/protocol.ts`
- Create: `ccui-app/src/__tests__/protocol.test.ts`

### Tipos a Adicionar

O backend vai emitir mensagens WS no formato ChatUpdate. Estes tipos devem ser adicionados a `protocol.ts`:

```typescript
// ---- Stream-JSON Message Parts ----

export type MessagePartType =
  | "text"        // Texto do assistente
  | "thinking"    // Cadeia de raciocinio (extended thinking)
  | "tool_use"    // Invocacao de ferramenta (Read, Write, Bash, Grep, etc.)
  | "tool_result" // Resultado da ferramenta
  ;

export interface MessagePart {
  type: MessagePartType;
  content: string;
  metadata?: {
    toolName?: string;      // Nome da tool (Read, Write, Bash, Grep, Edit, Glob, etc.)
    toolId?: string;        // ID unico do tool_use (para correlacionar com tool_result)
    filePath?: string;      // Caminho de arquivo (Read, Write, Edit)
    exitCode?: number;      // Codigo de saida (Bash)
    isError?: boolean;      // Se tool_result e erro
    language?: string;      // Linguagem para syntax highlight
    isStreaming?: boolean;   // Se o conteudo ainda esta sendo recebido
  };
}

// ---- Chat Messages ----

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  parts: MessagePart[];
  timestamp: number;          // Unix ms
  isStreaming?: boolean;       // Mensagem ainda em progresso
}

// ---- Server -> Client (novos tipos) ----

/** Evento ChatUpdate emitido pelo backend quando processa output do Claude */
export type ChatUpdate =
  | { type: "chat_start"; message_id: string }
  | { type: "chat_delta"; message_id: string; part: MessagePart }
  | { type: "chat_end"; message_id: string }
  ;

// Expandir ServerMessage existente
// Adicionar ChatUpdate ao union type ServerMessage
```

O `ServerMessage` existente sera expandido para incluir ChatUpdate:

```typescript
export type ServerMessage =
  | { type: "output"; channel: string; data: string }          // Legado (developer mode)
  | { type: "session_created"; session_id: string; case_id?: string }
  | { type: "session_ended"; session_id: string }
  | { type: "chat_start"; message_id: string }                 // NOVO
  | { type: "chat_delta"; message_id: string; part: MessagePart } // NOVO
  | { type: "chat_end"; message_id: string }                   // NOVO
  | { type: "error"; message: string }
  | { type: "pong" };
```

**Nota:** `agent_joined`, `agent_left`, `agent_crashed` sao removidos -- o novo modelo nao tem multi-canal/multi-agente.

### Step 1: Escrever teste de tipagem

```typescript
// __tests__/protocol.test.ts
import { describe, it, expect } from "vitest";
import type { MessagePart, ChatMessage, ServerMessage } from "../types/protocol";

describe("protocol types", () => {
  it("MessagePart aceita todos os tipos validos", () => {
    const parts: MessagePart[] = [
      { type: "text", content: "Ola" },
      { type: "thinking", content: "Analisando..." },
      { type: "tool_use", content: '{"path":"/x"}', metadata: { toolName: "Read", toolId: "tu_1" } },
      { type: "tool_result", content: "conteudo do arquivo", metadata: { toolId: "tu_1" } },
    ];
    expect(parts).toHaveLength(4);
  });

  it("ChatMessage tem campos obrigatorios", () => {
    const msg: ChatMessage = {
      id: "msg_1",
      role: "assistant",
      parts: [{ type: "text", content: "Resposta" }],
      timestamp: Date.now(),
    };
    expect(msg.role).toBe("assistant");
    expect(msg.parts[0].type).toBe("text");
  });

  it("ServerMessage aceita chat_delta", () => {
    const msg: ServerMessage = {
      type: "chat_delta",
      message_id: "msg_1",
      part: { type: "text", content: "chunk" },
    };
    expect(msg.type).toBe("chat_delta");
  });
});
```

### Step 2: Rodar teste -- deve falhar (tipos nao existem)

Run: `cd legal-workbench/ccui-app && bun run test -- __tests__/protocol.test.ts`
Expected: FAIL -- tipos nao exportados

### Step 3: Implementar os tipos em protocol.ts

Adicionar os tipos acima ao final de `protocol.ts`. Remover `agent_joined`, `agent_left`, `agent_crashed` do `ServerMessage`. Manter `Channel` e `ChannelTabs` por enquanto (cleanup posterior).

### Step 4: Rodar teste -- deve passar

Run: `cd legal-workbench/ccui-app && bun run test -- __tests__/protocol.test.ts`
Expected: PASS

### Step 5: Commit

```bash
git add ccui-app/src/types/protocol.ts ccui-app/src/__tests__/protocol.test.ts
git commit -m "feat(ccui-app): tipos MessagePart e ChatUpdate para stream-json"
```

---

## Task 2: Hook useChat -- Acumulador de Mensagens

**Files:**
- Create: `ccui-app/src/hooks/useChat.ts`
- Create: `ccui-app/src/__tests__/useChat.test.ts`

### Design

Hook que escuta eventos ChatUpdate do WebSocket e acumula mensagens:

```typescript
// hooks/useChat.ts
import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "../contexts/WebSocketContext";
import type { ChatMessage, MessagePart, ServerMessage } from "../types/protocol";

interface UseChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  sendMessage: (text: string) => void;
  clearMessages: () => void;
}

export function useChat(): UseChatReturn {
  const { send, onMessage } = useWebSocket();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const currentMsgRef = useRef<string | null>(null);

  useEffect(() => {
    return onMessage((msg: ServerMessage) => {
      switch (msg.type) {
        case "chat_start":
          currentMsgRef.current = msg.message_id;
          setIsStreaming(true);
          setMessages((prev) => [
            ...prev,
            {
              id: msg.message_id,
              role: "assistant",
              parts: [],
              timestamp: Date.now(),
              isStreaming: true,
            },
          ]);
          break;

        case "chat_delta":
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== msg.message_id) return m;
              // Se ultimo part tem mesmo tipo e esta em streaming, append ao content
              const lastPart = m.parts[m.parts.length - 1];
              if (
                lastPart &&
                lastPart.type === msg.part.type &&
                lastPart.type === "text" &&
                lastPart.metadata?.isStreaming
              ) {
                return {
                  ...m,
                  parts: [
                    ...m.parts.slice(0, -1),
                    { ...lastPart, content: lastPart.content + msg.part.content },
                  ],
                };
              }
              // Novo part
              return {
                ...m,
                parts: [...m.parts, { ...msg.part, metadata: { ...msg.part.metadata, isStreaming: true } }],
              };
            })
          );
          break;

        case "chat_end":
          currentMsgRef.current = null;
          setIsStreaming(false);
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== msg.message_id) return m;
              return {
                ...m,
                isStreaming: false,
                parts: m.parts.map((p) => ({
                  ...p,
                  metadata: { ...p.metadata, isStreaming: false },
                })),
              };
            })
          );
          break;
      }
    });
  }, [onMessage]);

  const sendMessage = useCallback(
    (text: string) => {
      const userMsg: ChatMessage = {
        id: `user_${Date.now()}`,
        role: "user",
        parts: [{ type: "text", content: text }],
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMsg]);
      send({ type: "input", channel: "main", text });
    },
    [send]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setIsStreaming(false);
    currentMsgRef.current = null;
  }, []);

  return { messages, isStreaming, sendMessage, clearMessages };
}
```

### Step 1: Escrever testes

```typescript
// __tests__/useChat.test.ts
import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import React from "react";

// Mock do WebSocketContext
const mockSend = vi.fn();
let messageHandler: ((msg: any) => void) | null = null;
const mockOnMessage = vi.fn((handler: any) => {
  messageHandler = handler;
  return () => { messageHandler = null; };
});

vi.mock("../contexts/WebSocketContext", () => ({
  useWebSocket: () => ({
    send: mockSend,
    onMessage: mockOnMessage,
  }),
}));

import { useChat } from "../hooks/useChat";

describe("useChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    messageHandler = null;
  });

  it("acumula mensagens do usuario via sendMessage", () => {
    const { result } = renderHook(() => useChat());
    act(() => result.current.sendMessage("Ola"));
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].parts[0].content).toBe("Ola");
    expect(mockSend).toHaveBeenCalledWith({ type: "input", channel: "main", text: "Ola" });
  });

  it("processa chat_start + chat_delta + chat_end", () => {
    const { result } = renderHook(() => useChat());

    act(() => messageHandler?.({ type: "chat_start", message_id: "m1" }));
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.isStreaming).toBe(true);

    act(() => messageHandler?.({
      type: "chat_delta",
      message_id: "m1",
      part: { type: "text", content: "Resposta" },
    }));
    expect(result.current.messages[0].parts).toHaveLength(1);
    expect(result.current.messages[0].parts[0].content).toBe("Resposta");

    act(() => messageHandler?.({ type: "chat_end", message_id: "m1" }));
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.messages[0].isStreaming).toBe(false);
  });

  it("clearMessages limpa tudo", () => {
    const { result } = renderHook(() => useChat());
    act(() => result.current.sendMessage("msg"));
    act(() => result.current.clearMessages());
    expect(result.current.messages).toHaveLength(0);
  });
});
```

### Step 2: Rodar teste -- deve falhar

Run: `cd legal-workbench/ccui-app && bun run test -- __tests__/useChat.test.ts`
Expected: FAIL -- modulo nao existe

### Step 3: Implementar useChat.ts

Copiar implementacao acima.

### Step 4: Rodar teste -- deve passar

Run: `cd legal-workbench/ccui-app && bun run test -- __tests__/useChat.test.ts`
Expected: PASS

### Step 5: Commit

```bash
git add ccui-app/src/hooks/useChat.ts ccui-app/src/__tests__/useChat.test.ts
git commit -m "feat(ccui-app): hook useChat para acumular ChatUpdate do WS"
```

---

## Task 3: MarkdownRenderer -- Copiar e Adaptar do ADK

**Files:**
- Create: `ccui-app/src/components/MarkdownRenderer.tsx`
- Create: `ccui-app/src/__tests__/MarkdownRenderer.test.tsx`

### Design

Copiar `ADK-sandboxed-legal/src/components/MarkdownRenderer.tsx` com ajustes:
- Remover export default (usar named export apenas)
- Remover classes com tema ADK (`surface-elevated`, `accent`) -- usar CSS variables do ccui-app (`var(--bg-surface)`, `var(--accent)`)
- Manter a funcao `renderMarkdown()` como export principal

### Step 1: Escrever teste

```typescript
// __tests__/MarkdownRenderer.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { MarkdownRenderer } from "../components/MarkdownRenderer";

describe("MarkdownRenderer", () => {
  it("renderiza texto simples como paragrafo", () => {
    render(<MarkdownRenderer content="Texto simples" />);
    expect(screen.getByText("Texto simples")).toBeInTheDocument();
  });

  it("renderiza bold com **", () => {
    render(<MarkdownRenderer content="Texto **negrito** aqui" />);
    const bold = screen.getByText("negrito");
    expect(bold.tagName).toBe("STRONG");
  });

  it("renderiza heading h2", () => {
    render(<MarkdownRenderer content="## Titulo" />);
    expect(screen.getByText("Titulo").tagName).toBe("H2");
  });

  it("renderiza lista", () => {
    render(<MarkdownRenderer content="- Item 1\n- Item 2" />);
    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
  });

  it("retorna null para conteudo vazio", () => {
    const { container } = render(<MarkdownRenderer content="" />);
    expect(container.firstChild).toBeNull();
  });
});
```

### Step 2-5: TDD cycle padrao

Copiar MarkdownRenderer do ADK, adaptar classes CSS (trocar Tailwind theme classes por CSS variables do ccui-app), rodar testes, commit.

```bash
git add ccui-app/src/components/MarkdownRenderer.tsx ccui-app/src/__tests__/MarkdownRenderer.test.tsx
git commit -m "feat(ccui-app): MarkdownRenderer adaptado do ADK"
```

---

## Task 4: getClientIntent -- Traducao Tecnica -> Juridica

**Files:**
- Create: `ccui-app/src/utils/getClientIntent.ts`
- Create: `ccui-app/src/__tests__/getClientIntent.test.ts`

### Design

Funcao pura que mapeia um MessagePart para texto em linguagem juridica. Adaptada do ADK mas com tool names do Claude Code:

```typescript
// utils/getClientIntent.ts
import type { MessagePart } from "../types/protocol";

export interface ClientIntent {
  label: string;     // Texto curto para o usuario (ex: "Analisando documentos do caso...")
  icon: string;      // Nome do icone lucide (ex: "file-search", "terminal", "pencil")
  hidden: boolean;   // Se deve ser oculto no client mode
}

const TOOL_INTENTS: Record<string, ClientIntent> = {
  // Leitura de arquivos
  Read:     { label: "Consultando documento...",           icon: "file-text",   hidden: false },
  Glob:     { label: "Localizando arquivos relevantes...", icon: "folder-search", hidden: false },
  Grep:     { label: "Buscando nos documentos...",         icon: "search",      hidden: false },

  // Escrita
  Write:    { label: "Redigindo documento...",             icon: "pencil",      hidden: false },
  Edit:     { label: "Revisando documento...",             icon: "pencil-line", hidden: false },

  // Execucao
  Bash:     { label: "Processando dados...",               icon: "terminal",    hidden: false },

  // Web
  WebSearch:  { label: "Pesquisando jurisprudencia...",    icon: "globe",       hidden: false },
  WebFetch:   { label: "Consultando fonte externa...",     icon: "globe",       hidden: false },

  // Task/subagente
  Task:       { label: "Consultando especialista...",      icon: "users",       hidden: false },
};

export function getClientIntent(part: MessagePart): ClientIntent {
  // Thinking -- ocultar no client mode
  if (part.type === "thinking") {
    return { label: "Analisando...", icon: "brain", hidden: true };
  }

  // Texto -- mostrar como esta
  if (part.type === "text") {
    return { label: "", icon: "", hidden: false };
  }

  // Tool use -- mapear por nome
  if (part.type === "tool_use" && part.metadata?.toolName) {
    const intent = TOOL_INTENTS[part.metadata.toolName];
    if (intent) return intent;
    // Fallback para tools desconhecidas
    return { label: "Executando verificacao...", icon: "cog", hidden: false };
  }

  // Tool result -- ocultar no client mode (resultado tecnico)
  if (part.type === "tool_result") {
    return { label: "Resultado processado", icon: "check", hidden: true };
  }

  return { label: "", icon: "", hidden: false };
}
```

### Step 1: Escrever teste

```typescript
// __tests__/getClientIntent.test.ts
import { describe, it, expect } from "vitest";
import { getClientIntent } from "../utils/getClientIntent";
import type { MessagePart } from "../types/protocol";

describe("getClientIntent", () => {
  it("oculta thinking no client mode", () => {
    const part: MessagePart = { type: "thinking", content: "hmm" };
    expect(getClientIntent(part).hidden).toBe(true);
  });

  it("mapeia Read para linguagem juridica", () => {
    const part: MessagePart = { type: "tool_use", content: "{}", metadata: { toolName: "Read" } };
    const intent = getClientIntent(part);
    expect(intent.label).toContain("documento");
    expect(intent.hidden).toBe(false);
  });

  it("mapeia Grep para busca", () => {
    const part: MessagePart = { type: "tool_use", content: "{}", metadata: { toolName: "Grep" } };
    expect(getClientIntent(part).label).toContain("Buscando");
  });

  it("texto nao tem intent especial", () => {
    const part: MessagePart = { type: "text", content: "Ola" };
    expect(getClientIntent(part).hidden).toBe(false);
    expect(getClientIntent(part).label).toBe("");
  });

  it("tool desconhecida tem fallback", () => {
    const part: MessagePart = { type: "tool_use", content: "{}", metadata: { toolName: "CustomTool" } };
    expect(getClientIntent(part).label).toBeTruthy();
  });

  it("tool_result e oculto no client mode", () => {
    const part: MessagePart = { type: "tool_result", content: "ok" };
    expect(getClientIntent(part).hidden).toBe(true);
  });
});
```

### Step 2-5: TDD cycle padrao, commit:

```bash
git add ccui-app/src/utils/getClientIntent.ts ccui-app/src/__tests__/getClientIntent.test.ts
git commit -m "feat(ccui-app): getClientIntent para traducao tecnica -> juridica"
```

---

## Task 5: Componente ChatView -- Renderizacao de Mensagens

**Files:**
- Create: `ccui-app/src/components/ChatView.tsx`
- Create: `ccui-app/src/__tests__/ChatView.test.tsx`

### Design

Componente principal que substitui TerminalPane. Adaptado do AgentMessageBody do ADK:

```
ChatView
  +-- MessageList (scroll area)
  |     +-- MessageBubble (por ChatMessage)
  |           +-- UserBubble (role === "user")
  |           +-- AssistantBubble (role === "assistant")
  |                 +-- [client mode] ClientPartRenderer
  |                 |     +-- StatusPill (tool_use -> intent label)
  |                 |     +-- MarkdownRenderer (text parts)
  |                 +-- [developer mode] DevPartRenderer
  |                       +-- ThinkingBlock (collapsible)
  |                       +-- ToolUseBlock (tool name + input JSON)
  |                       +-- ToolResultBlock (output, exit code)
  |                       +-- MarkdownRenderer (text parts)
  +-- StreamingIndicator (quando isStreaming)
```

**Props:**

```typescript
interface ChatViewProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  viewMode: "client" | "developer";
}
```

### Step 1: Escrever testes basicos

```typescript
// __tests__/ChatView.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { ChatView } from "../components/ChatView";
import type { ChatMessage } from "../types/protocol";

const userMsg: ChatMessage = {
  id: "u1",
  role: "user",
  parts: [{ type: "text", content: "Qual o prazo prescricional?" }],
  timestamp: Date.now(),
};

const assistantMsg: ChatMessage = {
  id: "a1",
  role: "assistant",
  parts: [
    { type: "thinking", content: "Analisando prazo..." },
    { type: "tool_use", content: '{"pattern":"prescricao"}', metadata: { toolName: "Grep", toolId: "t1" } },
    { type: "tool_result", content: "art. 206 CC", metadata: { toolId: "t1" } },
    { type: "text", content: "O prazo prescricional e de 3 anos conforme art. 206 do CC." },
  ],
  timestamp: Date.now(),
};

describe("ChatView", () => {
  it("renderiza mensagem do usuario", () => {
    render(<ChatView messages={[userMsg]} isStreaming={false} viewMode="client" />);
    expect(screen.getByText("Qual o prazo prescricional?")).toBeInTheDocument();
  });

  it("client mode oculta thinking e tool_result", () => {
    render(<ChatView messages={[assistantMsg]} isStreaming={false} viewMode="client" />);
    expect(screen.queryByText("Analisando prazo...")).not.toBeInTheDocument();
    expect(screen.getByText(/prazo prescricional/)).toBeInTheDocument();
  });

  it("developer mode mostra thinking em details", () => {
    render(<ChatView messages={[assistantMsg]} isStreaming={false} viewMode="developer" />);
    expect(screen.getByText("Analisando prazo...")).toBeInTheDocument();
  });

  it("client mode mostra status pill para tool_use", () => {
    render(<ChatView messages={[assistantMsg]} isStreaming={false} viewMode="client" />);
    expect(screen.getByText(/Buscando nos documentos/)).toBeInTheDocument();
  });

  it("mostra indicador de streaming", () => {
    render(<ChatView messages={[assistantMsg]} isStreaming={true} viewMode="client" />);
    expect(screen.getByText(/Analisando/i)).toBeInTheDocument();
  });
});
```

### Step 2-5: Implementar ChatView, DevPartRenderer, ClientPartRenderer como subcomponentes no mesmo arquivo. TDD cycle, commit:

```bash
git add ccui-app/src/components/ChatView.tsx ccui-app/src/__tests__/ChatView.test.tsx
git commit -m "feat(ccui-app): ChatView com dual-mode client/developer"
```

---

## Task 6: Componente ModeToggle + SessionView Refatorado

**Files:**
- Create: `ccui-app/src/components/ModeToggle.tsx`
- Modify: `ccui-app/src/components/SessionView.tsx`
- Create: `ccui-app/src/__tests__/ModeToggle.test.tsx`

### Design

ModeToggle: toggle simples client/developer (adaptado do ADK ChatWorkspace). Guarda estado em localStorage.

SessionView refatorado:
- Remover import de ChannelTabs e TerminalPane
- Adicionar import de ChatView, ModeToggle, useChat
- Layout: header (caso + mode toggle + connection) -> ChatView -> input area

```typescript
// ModeToggle.tsx
import React from "react";
import { Code, Briefcase } from "lucide-react";

export type ViewMode = "client" | "developer";

interface ModeToggleProps {
  mode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

export const ModeToggle: React.FC<ModeToggleProps> = ({ mode, onChange }) => (
  <div
    className="flex items-center p-0.5 rounded-lg border"
    style={{ borderColor: "var(--border)", background: "var(--bg-elevated)" }}
  >
    <button
      onClick={() => onChange("client")}
      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all"
      style={{
        background: mode === "client" ? "var(--accent)" : "transparent",
        color: mode === "client" ? "var(--bg-base)" : "var(--text-secondary)",
      }}
    >
      <Briefcase className="w-3 h-3" />
      Cliente
    </button>
    <button
      onClick={() => onChange("developer")}
      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all"
      style={{
        background: mode === "developer" ? "var(--bg-surface)" : "transparent",
        color: mode === "developer" ? "var(--text-primary)" : "var(--text-secondary)",
      }}
    >
      <Code className="w-3 h-3" />
      Desenvolvedor
    </button>
  </div>
);
```

### Step 1-5: TDD cycle para ModeToggle (teste de toggle, persistencia), depois refatorar SessionView. Commit:

```bash
git add ccui-app/src/components/ModeToggle.tsx ccui-app/src/__tests__/ModeToggle.test.tsx ccui-app/src/components/SessionView.tsx
git commit -m "feat(ccui-app): ModeToggle + SessionView com ChatView"
```

---

## Task 7: Cleanup -- Remover ChannelTabs, Simplificar Contextos

**Files:**
- Delete: `ccui-app/src/components/ChannelTabs.tsx`
- Delete: `ccui-app/src/__tests__/ChannelTabs.test.tsx`
- Modify: `ccui-app/src/contexts/SessionContext.tsx` -- remover logica de channels multi-agente
- Modify: `ccui-app/src/App.tsx` -- sem mudanca (ja funciona)

### Design

SessionContext simplificado: manter caseId, sessionId. Remover channels array (substituido por useChat).

### Step 1-3: Remover, adaptar, rodar todos os testes:

Run: `cd legal-workbench/ccui-app && bun run test`
Expected: ALL PASS

### Step 4: Commit

```bash
git add -A ccui-app/src/
git commit -m "refactor(ccui-app): remover ChannelTabs e simplificar SessionContext"
```

---

## Task 8: Testes de Integracao

**Files:**
- Create: `ccui-app/src/__tests__/integration/chat-flow.test.tsx`

### Design

Teste end-to-end do fluxo: mount App -> selecionar caso -> receber chat_start/delta/end -> verificar renderizacao.

```typescript
describe("chat flow integration", () => {
  it("fluxo completo: case select -> session -> chat message", async () => {
    // Mock API + WS
    // 1. Render App
    // 2. Selecionar caso (click no CaseCard)
    // 3. Simular session_created via WS
    // 4. Verificar SessionView renderizado
    // 5. Enviar mensagem (input + enter)
    // 6. Simular chat_start + chat_delta(text) + chat_end
    // 7. Verificar mensagem renderizada no ChatView
  });
});
```

### Step 1-5: TDD cycle, commit:

```bash
git add ccui-app/src/__tests__/integration/
git commit -m "test(ccui-app): testes de integracao do fluxo de chat"
```

---

## Ordem de Implementacao (Resumo)

| # | Task | Deps | Estimativa |
|---|------|------|-----------|
| 1 | Tipos TypeScript | Nenhuma | Pequena |
| 2 | Hook useChat | Task 1 | Media |
| 3 | MarkdownRenderer | Nenhuma | Pequena |
| 4 | getClientIntent | Task 1 | Pequena |
| 5 | ChatView | Tasks 1, 3, 4 | Grande |
| 6 | ModeToggle + SessionView | Tasks 2, 5 | Media |
| 7 | Cleanup | Task 6 | Pequena |
| 8 | Testes Integracao | Task 7 | Media |

**Paralelizavel:** Tasks 1, 3, 4 podem ser feitas em paralelo. Task 2 depende apenas de Task 1. Task 5 e o caminho critico.

---

## Notas de Design

### Sobre xterm.js / TerminalPane
TerminalPane NAO e deletado. Permanece no codebase como componente disponivel para developer mode avancado (futuro: toggle para ver raw terminal). Mas nao e renderizado por default -- ChatView o substitui.

### Sobre @xterm/xterm no package.json
Manter por enquanto. Remover apenas quando TerminalPane for definitivamente descartado (decisao futura).

### Sobre Slate Editor (ADK)
NAO copiar o Slate editor do ADK. O input do ccui-app e um `<textarea>` simples. Advogado nao precisa de rich text editor para instruir o Claude.

### Sobre CSS
O ccui-app usa CSS variables (--bg-base, --accent, etc.) definidas no CSS global. Os componentes novos devem usar essas variables, nao classes Tailwind de tema. Classes Tailwind sao usadas apenas para layout (flex, p-4, etc.).

### Sobre dependencias
Nenhuma dependencia nova. Tudo usa React 19 + lucide-react + Tailwind que ja estao no projeto.
