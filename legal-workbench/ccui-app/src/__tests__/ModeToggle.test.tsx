import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { ModeToggle } from "../components/ModeToggle";
import type { ViewMode } from "../components/ModeToggle";

describe("ModeToggle", () => {
  it("renderiza botoes cliente e desenvolvedor", () => {
    render(<ModeToggle mode="client" onChange={() => {}} />);
    expect(screen.getByText("Cliente")).toBeInTheDocument();
    expect(screen.getByText("Desenvolvedor")).toBeInTheDocument();
  });

  it("chama onChange ao clicar", () => {
    const onChange = vi.fn();
    render(<ModeToggle mode="client" onChange={onChange} />);
    fireEvent.click(screen.getByText("Desenvolvedor"));
    expect(onChange).toHaveBeenCalledWith("developer");
  });

  it("chama onChange para client", () => {
    const onChange = vi.fn();
    render(<ModeToggle mode="developer" onChange={onChange} />);
    fireEvent.click(screen.getByText("Cliente"));
    expect(onChange).toHaveBeenCalledWith("client");
  });
});
