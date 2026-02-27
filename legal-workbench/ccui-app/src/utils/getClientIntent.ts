import type { MessagePart } from "../types/protocol";

export interface ClientIntent {
  label: string;
  icon: string;
  hidden: boolean;
}

const TOOL_INTENTS: Record<string, ClientIntent> = {
  Read:       { label: "Consultando documento...",           icon: "file-text",     hidden: false },
  Glob:       { label: "Localizando arquivos relevantes...", icon: "folder-search", hidden: false },
  Grep:       { label: "Buscando nos documentos...",         icon: "search",        hidden: false },
  Write:      { label: "Redigindo documento...",             icon: "pencil",        hidden: false },
  Edit:       { label: "Revisando documento...",             icon: "pencil-line",   hidden: false },
  Bash:       { label: "Processando dados...",               icon: "terminal",      hidden: false },
  WebSearch:  { label: "Pesquisando jurisprudencia...",      icon: "globe",         hidden: false },
  WebFetch:   { label: "Consultando fonte externa...",       icon: "globe",         hidden: false },
  Task:       { label: "Consultando especialista...",        icon: "users",         hidden: false },
};

export function getClientIntent(part: MessagePart): ClientIntent {
  if (part.type === "thinking") {
    return { label: "Analisando...", icon: "brain", hidden: true };
  }

  if (part.type === "text") {
    return { label: "", icon: "", hidden: false };
  }

  if (part.type === "tool_use" && part.metadata?.toolName) {
    const intent = TOOL_INTENTS[part.metadata.toolName];
    if (intent) return intent;
    return { label: "Executando verificacao...", icon: "cog", hidden: false };
  }

  if (part.type === "tool_result") {
    return { label: "Resultado processado", icon: "check", hidden: true };
  }

  return { label: "", icon: "", hidden: false };
}
