import React, { useEffect, useRef } from "react";
import type { ChatMessage, MessagePart } from "../types/protocol";
import { getClientIntent } from "../utils/getClientIntent";
import { MarkdownRenderer } from "./MarkdownRenderer";

interface ChatViewProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  viewMode: "client" | "developer";
}

/* -- Sub-components -- */

const StatusPill: React.FC<{ label: string }> = ({ label }) => (
  <div
    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs"
    style={{ background: "var(--accent-dim)", color: "var(--accent)" }}
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
      className="text-xs cursor-pointer select-none"
      style={{ color: "var(--text-muted)" }}
    >
      Raciocinio
    </summary>
    <pre
      className="mt-1 p-2 rounded text-xs whitespace-pre-wrap overflow-x-auto"
      style={{ background: "var(--bg-elevated)", color: "var(--text-secondary)" }}
    >
      {content}
    </pre>
  </details>
);

const ToolUseBlock: React.FC<{ part: MessagePart }> = ({ part }) => (
  <div
    className="my-1 p-2 rounded text-xs border"
    style={{ borderColor: "var(--border)", background: "var(--bg-elevated)" }}
  >
    <div className="font-medium mb-1" style={{ color: "var(--accent)" }}>
      {part.metadata?.toolName ?? "Tool"}{" "}
      <span style={{ color: "var(--text-muted)" }}>{part.metadata?.toolId ?? ""}</span>
    </div>
    <pre className="whitespace-pre-wrap overflow-x-auto" style={{ color: "var(--text-secondary)" }}>
      {part.content}
    </pre>
  </div>
);

const ToolResultBlock: React.FC<{ part: MessagePart }> = ({ part }) => (
  <div
    className="my-1 p-2 rounded text-xs border"
    style={{
      borderColor: part.metadata?.isError ? "var(--error)" : "var(--border)",
      background: "var(--bg-elevated)",
    }}
  >
    <div className="text-[10px] mb-1" style={{ color: "var(--text-muted)" }}>
      Resultado {part.metadata?.toolId ?? ""}
      {part.metadata?.exitCode !== undefined && ` (exit: ${part.metadata.exitCode})`}
    </div>
    <pre className="whitespace-pre-wrap overflow-x-auto max-h-48" style={{ color: "var(--text-secondary)" }}>
      {part.content}
    </pre>
  </div>
);

const ClientPartRenderer: React.FC<{ part: MessagePart }> = ({ part }) => {
  const intent = getClientIntent(part);

  if (intent.hidden) return null;

  if (part.type === "text") {
    return <MarkdownRenderer content={part.content} />;
  }

  if (part.type === "tool_use" && intent.label) {
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

const MessageBubble: React.FC<{ message: ChatMessage; viewMode: "client" | "developer" }> = ({
  message,
  viewMode,
}) => {
  const isUser = message.role === "user";
  const Renderer = viewMode === "client" ? ClientPartRenderer : DevPartRenderer;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-3 text-sm ${isUser ? "rounded-br-sm" : "rounded-bl-sm"}`}
        style={{
          background: isUser ? "var(--accent-dim)" : "var(--bg-surface)",
          color: "var(--text-primary)",
        }}
      >
        {message.parts.map((part, idx) => (
          <Renderer key={`${message.id}-${idx}`} part={part} />
        ))}
      </div>
    </div>
  );
};

const StreamingIndicator: React.FC = () => (
  <div
    data-testid="streaming-indicator"
    className="flex items-center gap-2 px-4 py-2 text-xs"
    style={{ color: "var(--text-muted)" }}
  >
    <span
      className="w-1.5 h-1.5 rounded-full animate-pulse"
      style={{ background: "var(--accent)" }}
    />
    Analisando...
  </div>
);

/* -- Main component -- */

export const ChatView: React.FC<ChatViewProps> = ({ messages, isStreaming, viewMode }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isStreaming]);

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} viewMode={viewMode} />
      ))}
      {isStreaming && <StreamingIndicator />}
    </div>
  );
};
