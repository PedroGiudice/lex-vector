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
