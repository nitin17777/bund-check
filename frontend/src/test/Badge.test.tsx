import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Badge } from "@/components/ui/Badge";

describe("Badge component", () => {
  it("renders text and correct variant styles", () => {
    const { rerender } = render(<Badge variant="info">Information</Badge>);
    const badge = screen.getByText("Information");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass("text-semantic-info");

    rerender(<Badge variant="critical">Critical Issue</Badge>);
    expect(screen.getByText("Critical Issue")).toHaveClass("text-semantic-critical");

    rerender(<Badge variant="success">Passed</Badge>);
    expect(screen.getByText("Passed")).toHaveClass("text-semantic-success");
  });
});
