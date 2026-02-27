import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { MarkdownRenderer } from "../components/MarkdownRenderer";

describe("MarkdownRenderer", () => {
  it("renderiza texto simples como paragrafo", () => {
    render(<MarkdownRenderer content="Texto simples" />);
    expect(screen.getByText("Texto simples")).toBeInTheDocument();
  });

  it("renderiza bold com **", () => {
    render(<MarkdownRenderer content="Texto **negrito** aqui" />);
    const bold = screen.getByText("negrito");
    expect(bold.tagName).toBe("STRONG");
  });

  it("renderiza heading h2", () => {
    render(<MarkdownRenderer content="## Titulo" />);
    expect(screen.getByText("Titulo").tagName).toBe("H2");
  });

  it("renderiza lista", () => {
    render(<MarkdownRenderer content={"- Item 1\n- Item 2"} />);
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0].textContent).toBe("Item 1");
    expect(items[1].textContent).toBe("Item 2");
  });

  it("retorna null para conteudo vazio", () => {
    const { container } = render(<MarkdownRenderer content="" />);
    expect(container.firstChild).toBeNull();
  });
});
