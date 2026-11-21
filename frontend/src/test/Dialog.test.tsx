import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Dialog } from "@/components/ui/Dialog";

describe("Dialog component", () => {
  it("renders when open and handles escape key", () => {
    const handleClose = vi.fn();
    const { rerender } = render(
      <Dialog isOpen={true} onClose={handleClose} title="Test Modal" description="Modal details">
        <div>Modal inner content</div>
      </Dialog>
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Test Modal")).toBeInTheDocument();
    expect(screen.getByText("Modal details")).toBeInTheDocument();
    expect(screen.getByText("Modal inner content")).toBeInTheDocument();

    fireEvent.keyDown(window, { key: "Escape" });
    expect(handleClose).toHaveBeenCalledTimes(1);

    rerender(
      <Dialog isOpen={false} onClose={handleClose} title="Test Modal">
        <div>Modal inner content</div>
      </Dialog>
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
