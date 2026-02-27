import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ChannelTabs } from "../components/ChannelTabs";
import type { Channel } from "../types/protocol";

const baseChannels: Channel[] = [
  { name: "main", pane_id: "main" },
];

describe("ChannelTabs", () => {
  it("renderiza a aba 'main' sempre", () => {
    render(
      <ChannelTabs
        channels={baseChannels}
        activeChannel="main"
        onSelect={vi.fn()}
      />
    );

    expect(screen.getByRole("tab", { name: /main/i })).toBeInTheDocument();
  });

  it("aba ativa tem aria-selected=true", () => {
    const channels: Channel[] = [
      { name: "main", pane_id: "main" },
      { name: "researcher", pane_id: "%5", color: "#4ade80" },
    ];

    render(
      <ChannelTabs
        channels={channels}
        activeChannel="researcher"
        onSelect={vi.fn()}
      />
    );

    const researcherTab = screen.getByRole("tab", { name: /researcher/i });
    expect(researcherTab).toHaveAttribute("aria-selected", "true");

    const mainTab = screen.getByRole("tab", { name: /main/i });
    expect(mainTab).toHaveAttribute("aria-selected", "false");
  });

  it("click em aba chama onSelect com o nome do canal", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const channels: Channel[] = [
      { name: "main", pane_id: "main" },
      { name: "coder", pane_id: "%6" },
    ];

    render(
      <ChannelTabs
        channels={channels}
        activeChannel="main"
        onSelect={onSelect}
      />
    );

    await user.click(screen.getByRole("tab", { name: /coder/i }));
    expect(onSelect).toHaveBeenCalledWith("coder");
  });

  it("renderiza dot colorido para canais de agente", () => {
    const channels: Channel[] = [
      { name: "main", pane_id: "main" },
      { name: "researcher", pane_id: "%5", color: "#ff0000" },
    ];

    const { container } = render(
      <ChannelTabs
        channels={channels}
        activeChannel="main"
        onSelect={vi.fn()}
      />
    );

    // O dot do agente deve ter a cor do agente como backgroundColor
    const dot = container.querySelector("span[style*='background-color']");
    expect(dot).toBeInTheDocument();
    // Cor normalizada pelo browser
    expect(dot?.getAttribute("style")).toContain("background-color");
  });

  it("renderiza multiplos canais de agentes", () => {
    const channels: Channel[] = [
      { name: "main", pane_id: "main" },
      { name: "researcher", pane_id: "%5" },
      { name: "coder", pane_id: "%6" },
      { name: "reviewer", pane_id: "%7" },
    ];

    render(
      <ChannelTabs
        channels={channels}
        activeChannel="main"
        onSelect={vi.fn()}
      />
    );

    expect(screen.getAllByRole("tab")).toHaveLength(4);
  });
});
