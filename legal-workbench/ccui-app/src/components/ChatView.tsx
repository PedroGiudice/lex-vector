import React, { useEffect, useRef } from "react";
import type { ChatMessage, MessagePart } from "../types/protocol";
import { getClientIntent } from "../utils/getClientIntent";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { ApertureSpinnerMini } from "./ApertureSpinner";

interface ChatViewProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  viewMode: "client" | "developer";
}

/* -- Sub-components -- */

const StatusPill: React.FC<{ label: string }> = ({ label }) => (
  <div
    className="inline-flex items-center gap-1.5 px-2.5 py-1 text-[11px]"
    style={{
      fontFamily: "var(--font-mono)",
      background: "var(--accent-dim)",
      color: "var(--accent)",
      borderRadius: "var(--radius-sm)",
    }}
  >
    <span
      className="w-1.5 h-1.5 rounded-full animate-pulse"
      style={{ background: "var(--accent)" }}
    />
    {label}
  </div>
);

const ThinkingBlock: React.FC<{ content: string }> = ({ content }) => (
  <details className="my-1">
    <summary
      className="text-[11px] cursor-pointer select-none"
      style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}
    >
      Raciocinio
    </summary>
    <pre
      className="mt-1 p-3 text-[12px] whitespace-pre-wrap overflow-x-auto"
      style={{
        fontFamily: "var(--font-mono)",
        background: "var(--bg-header)",
        border: "1px solid var(--bg-borders)",
        borderRadius: "var(--radius-md)",
        color: "var(--text-secondary)",
      }}
    >
      {content}
    </pre>
  </details>
);

const ToolUseBlock: React.FC<{ part: MessagePart }> = ({ part }) => (
  <div
    className="inline-flex items-center gap-1.5 my-1 px-2.5 py-1 text-[11px]"
    style={{
      fontFamily: "var(--font-mono)",
      background: "var(--accent-dim)",
      border: "1px solid rgba(200,120,74,0.15)",
      borderRadius: "var(--radius-sm)",
    }}
  >
    <span
      className="w-1.5 h-1.5 rounded-full"
      style={{ background: "var(--accent)" }}
    />
    <span style={{ color: "var(--accent)" }}>
      {part.metadata?.toolName ?? "Tool"}
    </span>
    <span style={{ color: "var(--text-muted)" }}>
      {part.metadata?.toolId ?? ""}
    </span>
  </div>
);

const ToolResultBlock: React.FC<{ part: MessagePart }> = ({ part }) => (
  <div
    className="my-1 p-3 text-[12px]"
    style={{
      fontFamily: "var(--font-mono)",
      borderRadius: "var(--radius-md)",
      background: "var(--bg-header)",
      border: part.metadata?.isError
        ? "1px solid #8a3028"
        : "1px solid var(--bg-borders)",
    }}
  >
    <div className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>
      Resultado {part.metadata?.toolId ?? ""}
      {part.metadata?.exitCode !== undefined && ` (exit: ${part.metadata.exitCode})`}
    </div>
    <pre
      className="whitespace-pre-wrap overflow-x-auto max-h-48"
      style={{ color: "var(--text-secondary)" }}
    >
      {part.content}
    </pre>
  </div>
);

const ClientPartRenderer: React.FC<{
  part: MessagePart;
  isStreaming: boolean;
}> = ({ part, isStreaming }) => {
  const intent = getClientIntent(part);
  if (intent.hidden) return null;
  if (part.type === "text") return <MarkdownRenderer content={part.content} />;
  if (part.type === "tool_use" && intent.label && isStreaming) {
    return <StatusPill label={intent.label} />;
  }
  return null;
};

const DevPartRenderer: React.FC<{ part: MessagePart }> = ({ part }) => {
  switch (part.type) {
    case "thinking":
      return <ThinkingBlock content={part.content} />;
    case "tool_use":
      return <ToolUseBlock part={part} />;
    case "tool_result":
      return <ToolResultBlock part={part} />;
    case "text":
      return <MarkdownRenderer content={part.content} />;
    default:
      return null;
  }
};

/* -- Message bubble -- */

const MessageBubble: React.FC<{
  message: ChatMessage;
  viewMode: "client" | "developer";
  isStreaming: boolean;
}> = ({ message, viewMode, isStreaming }) => {
  const isUser = message.role === "user";

  if (isUser) {
    // User: accent bar left, bg panels, radius 0 8 8 0
    return (
      <div className="mb-6">
        <div
          className="px-4 py-3 text-sm"
          style={{
            background: "var(--bg-panels)",
            borderLeft: "3px solid var(--accent)",
            borderRadius: "0 8px 8px 0",
            color: "var(--text-primary)",
            lineHeight: "var(--lh-body)",
          }}
        >
          {message.parts.map((part, idx) =>
            viewMode === "client" ? (
              <ClientPartRenderer key={`${message.id}-${idx}`} part={part} isStreaming={isStreaming} />
            ) : (
              <DevPartRenderer key={`${message.id}-${idx}`} part={part} />
            )
          )}
        </div>
      </div>
    );
  }

  // Assistant: no bubble, text on base bg, icon + label above
  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 mb-1.5">
        <span
          className="w-2 h-2 rounded-full"
          style={{ background: "var(--accent)" }}
        />
        <span
          className="text-[11px]"
          style={{ fontFamily: "var(--font-mono)", color: "var(--accent)" }}
        >
          assistant
        </span>
      </div>
      <div
        className="text-sm"
        style={{
          color: "var(--text-primary)",
          lineHeight: "var(--lh-body)",
        }}
      >
        {message.parts.map((part, idx) =>
          viewMode === "client" ? (
            <ClientPartRenderer key={`${message.id}-${idx}`} part={part} isStreaming={isStreaming} />
          ) : (
            <DevPartRenderer key={`${message.id}-${idx}`} part={part} />
          )
        )}
      </div>
    </div>
  );
};

/* -- Streaming indicator -- */

const StreamingIndicator: React.FC = () => (
  <div
    data-testid="streaming-indicator"
    className="flex items-center gap-2.5 py-3 text-[12px]"
    style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}
  >
    <ApertureSpinnerMini size={20} />
    <span>Pensando...</span>
  </div>
);

/* -- Main -- */

export const ChatView: React.FC<ChatViewProps> = ({
  messages,
  isStreaming,
  viewMode,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto py-6">
      <div className="max-w-[var(--chat-max-width)] mx-auto px-4">
        {messages.length === 0 && !isStreaming && (
          <div className="flex flex-col items-center justify-center py-20">
            <p
              className="text-[20px] mb-2"
              style={{ fontFamily: "var(--font-display)", fontStyle: "italic", color: "var(--text-secondary)" }}
            >
              Chat do agente ativo
            </p>
            <p className="text-[12px]" style={{ fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
              Envie uma instrucao para comecar
            </p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            viewMode={viewMode}
            isStreaming={isStreaming}
          />
        ))}
        {isStreaming && <StreamingIndicator />}
      </div>
    </div>
  );
};
