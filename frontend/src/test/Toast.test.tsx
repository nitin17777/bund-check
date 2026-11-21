import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ToastProvider, useToast } from "@/components/ui/Toast";

function TestConsumer() {
  const { toast } = useToast();
  return (
    <button
      onClick={() =>
        toast({
          type: "success",
          title: "Verification Complete",
          description: "All protected spans intact.",
        })
      }
    >
      Trigger Toast
    </button>
  );
}

describe("Toast component", () => {
  it("displays toast when triggered and allows dismissal", () => {
    render(
      <ToastProvider>
        <TestConsumer />
      </ToastProvider>
    );

    fireEvent.click(screen.getByRole("button", { name: "Trigger Toast" }));

    expect(screen.getByText("Verification Complete")).toBeInTheDocument();
    expect(screen.getByText("All protected spans intact.")).toBeInTheDocument();

    const dismissButton = screen.getByRole("button", { name: "Dismiss toast" });
    fireEvent.click(dismissButton);

    expect(screen.queryByText("Verification Complete")).not.toBeInTheDocument();
  });
});
