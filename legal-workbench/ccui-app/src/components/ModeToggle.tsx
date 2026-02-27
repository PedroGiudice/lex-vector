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
