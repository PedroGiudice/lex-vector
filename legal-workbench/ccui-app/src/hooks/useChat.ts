import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "../contexts/WebSocketContext";
import { useSession } from "../contexts/SessionContext";
import type { ChatMessage, MessagePart, ServerMessage } from "../types/protocol";

interface UseChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  sendMessage: (text: string) => void;
  clearMessages: () => void;
}

export function useChat(): UseChatReturn {
  const { send, onMessage } = useWebSocket();
  const { sessionId } = useSession();
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
              return {
                ...m,
                parts: [...m.parts, { ...msg.part, metadata: { ...msg.part.metadata, isStreaming: true } }],
              };
            })
          );
          break;

        case "chat_init":
          // Metadados da sessao Claude -- ignorado pelo hook de chat
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
      if (sessionId) {
        send({ type: "chat_input", session_id: sessionId, text });
      }
    },
    [send, sessionId]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setIsStreaming(false);
    currentMsgRef.current = null;
  }, []);

  return { messages, isStreaming, sendMessage, clearMessages };
}
