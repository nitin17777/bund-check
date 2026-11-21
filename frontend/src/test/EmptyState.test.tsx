import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { EmptyState } from "@/components/ui/EmptyState";
import { FileQuestion } from "lucide-react";

describe("EmptyState component", () => {
  it("renders title, description, and action button", () => {
    render(
      <EmptyState
        icon={<FileQuestion data-testid="icon" />}
        title="Nothing Found"
        description="Try searching for something else."
        action={<button>Create New</button>}
      />
    );

    expect(screen.getByText("Nothing Found")).toBeInTheDocument();
    expect(screen.getByText("Try searching for something else.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create New" })).toBeInTheDocument();
    expect(screen.getByTestId("icon")).toBeInTheDocument();
  });
});
