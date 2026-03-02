/**
 * Hook para rastrear agentes via eventos WebSocket agent_joined/agent_left.
 * Mantém lista reativa de agentes ativos na sessão.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useWebSocket } from "../contexts/WebSocketContext";

export interface AgentInfo {
  name: string;
  color: string;
  model: string;
  pane_id: string;
  joinedAt: number;
}

const AGENT_COLORS: Record<string, string> = {
  main: "var(--agent-terracota)",
  researcher: "var(--agent-oliva)",
  "case-analyst": "var(--agent-teal)",
  strategist: "var(--agent-malva)",
  "code-refactorer": "var(--agent-musgo)",
};

function fallbackColor(name: string): string {
  const colors = [
    "var(--agent-terracota)",
    "var(--agent-oliva)",
    "var(--agent-teal)",
    "var(--agent-malva)",
    "var(--agent-musgo)",
  ];
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) | 0;
  return colors[Math.abs(hash) % colors.length];
}

export function useAgents() {
  const { onMessage } = useWebSocket();
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const agentsRef = useRef<AgentInfo[]>([]);

  const handleMessage = useCallback((msg: { type: string; name?: string; color?: string; model?: string; pane_id?: string }) => {
    if (msg.type === "agent_joined" && msg.name) {
      const agent: AgentInfo = {
        name: msg.name,
        color: msg.color || AGENT_COLORS[msg.name.toLowerCase()] || fallbackColor(msg.name),
        model: msg.model || "",
        pane_id: msg.pane_id || "",
        joinedAt: Date.now(),
      };
      const next = [...agentsRef.current.filter((a) => a.name !== agent.name), agent];
      agentsRef.current = next;
      setAgents(next);
    } else if ((msg.type === "agent_left" || msg.type === "agent_crashed") && msg.name) {
      const next = agentsRef.current.filter((a) => a.name !== msg.name);
      agentsRef.current = next;
      setAgents(next);
    }
  }, []);

  useEffect(() => {
    return onMessage(handleMessage as Parameters<typeof onMessage>[0]);
  }, [onMessage, handleMessage]);

  const reset = useCallback(() => {
    agentsRef.current = [];
    setAgents([]);
  }, []);

  return { agents, reset };
}
