/**
 * Hook para capturar metadados da sessao Claude via evento chat_init.
 */

import { useEffect, useState } from "react";
import { useWebSocket } from "../contexts/WebSocketContext";

interface SessionMeta {
  model: string | null;
  claudeSessionId: string | null;
}

export function useSessionMeta(): SessionMeta {
  const { onMessage } = useWebSocket();
  const [meta, setMeta] = useState<SessionMeta>({
    model: null,
    claudeSessionId: null,
  });

  useEffect(() => {
    return onMessage((msg) => {
      if (msg.type === "chat_init") {
        setMeta({
          model: msg.model,
          claudeSessionId: msg.claude_session_id,
        });
      }
    });
  }, [onMessage]);

  return meta;
}
