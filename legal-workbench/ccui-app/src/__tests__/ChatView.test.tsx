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

  it("developer mode mostra thinking", () => {
    render(<ChatView messages={[assistantMsg]} isStreaming={false} viewMode="developer" />);
    expect(screen.getByText("Analisando prazo...")).toBeInTheDocument();
  });

  it("client mode mostra status pill para tool_use durante streaming", () => {
    render(<ChatView messages={[assistantMsg]} isStreaming={true} viewMode="client" />);
    expect(screen.getByText(/Buscando nos documentos/)).toBeInTheDocument();
  });

  it("client mode suprime status pill para tool_use apos streaming encerrado", () => {
    render(<ChatView messages={[assistantMsg]} isStreaming={false} viewMode="client" />);
    expect(screen.queryByText(/Buscando nos documentos/)).not.toBeInTheDocument();
  });

  it("mostra indicador de streaming", () => {
    render(<ChatView messages={[]} isStreaming={true} viewMode="client" />);
    expect(screen.getByTestId("streaming-indicator")).toBeInTheDocument();
  });
});
