import React from "react";
import { Terminal } from "lucide-react";
import type { Channel } from "../types/protocol";

interface ChannelTabsProps {
  channels: Channel[];
  activeChannel: string;
  onSelect: (name: string) => void;
}

export const ChannelTabs: React.FC<ChannelTabsProps> = ({
  channels,
  activeChannel,
  onSelect,
}) => {
  return (
    <div
      role="tablist"
      aria-label="Canais da sessao"
      className="flex items-end gap-0.5 px-4 overflow-x-auto shrink-0"
      style={{ background: "var(--bg-surface)", borderBottom: "1px solid var(--border)" }}
    >
      {channels.map((ch) => {
        const isMain = ch.name === "main";
        const isActive = ch.name === activeChannel;

        return (
          <button
            key={ch.name}
            role="tab"
            aria-selected={isActive}
            onClick={() => onSelect(ch.name)}
            className="relative flex items-center gap-2 px-3.5 py-2.5 text-xs whitespace-nowrap
                       transition-colors duration-150 outline-none"
            style={{
              color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
              borderBottom: isActive
                ? "2px solid var(--accent)"
                : "2px solid transparent",
              marginBottom: "-1px",
            }}
            onMouseEnter={(e) => {
              if (!isActive)
                (e.currentTarget as HTMLButtonElement).style.color = "var(--text-primary)";
            }}
            onMouseLeave={(e) => {
              if (!isActive)
                (e.currentTarget as HTMLButtonElement).style.color = "var(--text-secondary)";
            }}
          >
            {isMain ? (
              <Terminal className="w-3 h-3 shrink-0" />
            ) : (
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: ch.color ?? "var(--accent)" }}
              />
            )}
            <span className="font-medium">{ch.name}</span>
            {ch.model && !isMain && (
              <span
                className="text-[10px] px-1.5 py-px rounded-full font-mono"
                style={{
                  color: "var(--text-secondary)",
                  background: "var(--bg-elevated)",
                  border: "1px solid var(--border)",
                }}
              >
                {ch.model.split("-")[0]}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};

export default ChannelTabs;
