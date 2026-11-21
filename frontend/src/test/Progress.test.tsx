import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Progress } from "@/components/ui/Progress";

describe("Progress component", () => {
  it("renders with correct aria attributes and width", () => {
    render(<Progress value={40} max={100} />);
    const progressbar = screen.getByRole("progressbar");
    expect(progressbar).toHaveAttribute("aria-valuenow", "40");
    expect(progressbar).toHaveAttribute("aria-valuemax", "100");
  });
});
